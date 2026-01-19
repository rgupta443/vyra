"""
Background job tasks for content generation and processing.

This module contains the actual task functions that are executed by RQ workers.
All tasks include proper error handling, logging, and status tracking as required
by requirements 16.1, 16.2, 16.3, and 16.4.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import traceback

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class TaskError(Exception):
    """Custom exception for task-specific errors."""
    pass


class RetryableTaskError(TaskError):
    """Exception for errors that should trigger a retry."""
    pass


class NonRetryableTaskError(TaskError):
    """Exception for errors that should not trigger a retry."""
    pass


def _handle_task_error(task_name: str, error: Exception, **context) -> Dict[str, Any]:
    """
    Centralized error handling for all tasks.
    
    Args:
        task_name: Name of the task that failed
        error: The exception that occurred
        **context: Additional context for logging
        
    Returns:
        Error result dictionary
    """
    error_info = {
        "task_name": task_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
        "context": context,
        "traceback": traceback.format_exc()
    }
    
    logger.error(f"Task {task_name} failed: {error_info}")
    
    # Determine if error should trigger retry
    if isinstance(error, NonRetryableTaskError):
        error_info["retryable"] = False
    elif isinstance(error, RetryableTaskError):
        error_info["retryable"] = True
    else:
        # Default: most errors are retryable
        error_info["retryable"] = True
    
    return {
        "status": "failed",
        "error": error_info
    }


def generate_image_task(generation_id: str, user_id: str, face_id: str, 
                       preset_type: str, format_type: str) -> Dict[str, Any]:
    """
    Background task for generating Instagram images.
    
    This task handles the complete image generation workflow including:
    - Face identity consistency validation
    - Nano Banana API integration
    - Format compliance checking
    - Error handling with retry logic
    - Status tracking and updates
    
    Validates Requirements 5.5, 12.3
    
    Args:
        generation_id: UUID of the generation record
        user_id: UUID of the user
        face_id: UUID of the face to use
        preset_type: Type of preset (luxury, lifestyle, beauty)
        format_type: Instagram format (reel_9_16, feed_4_5, square_1_1)
    
    Returns:
        Dict with generation results or error information
        
    Raises:
        RetryableTaskError: For temporary failures that should be retried
        NonRetryableTaskError: For permanent failures that should not be retried
    """
    # Import services at module level to avoid UnboundLocalError
    from app.services.nano_banana_service import (
        NanoBananaService,
        IdentityConsistencyError,
        FormatComplianceError,
        APIConnectionError
    )
    from app.services.preset_service import PresetService
    from app.services.format_compliance_service import FormatComplianceService
    from app.services.generation_service import GenerationService
    from app.core.database import SessionLocal
    from app.models.face import Face
    from app.models.generation import PresetType, GenerationStatus, Generation
    import asyncio
    
    task_context = {
        "generation_id": generation_id,
        "user_id": user_id,
        "face_id": face_id,
        "preset_type": preset_type,
        "format_type": format_type
    }
    
    db = SessionLocal()
    
    try:
        logger.info(f"Starting image generation task for generation {generation_id}")
        
        # Validate input parameters
        if not all([generation_id, user_id, face_id, preset_type, format_type]):
            raise NonRetryableTaskError("Missing required parameters for image generation")
        
        # Update status to PROCESSING (Requirement 12.3)
        GenerationService.update_generation_status(
            db, generation_id, GenerationStatus.PROCESSING
        )
        
        # Load face embedding from database
        face = db.query(Face).filter(Face.id == face_id).first()
        if not face:
            raise NonRetryableTaskError(f"Face {face_id} not found")
        
        if not face.is_active:
            raise NonRetryableTaskError(f"Face {face_id} is not active")
        
        # Get preset configuration
        preset_enum = PresetType(preset_type)
        preset = PresetService.get_preset_by_type(db, preset_enum)
        if not preset:
            raise NonRetryableTaskError(f"Preset {preset_type} not found")
        
        # Get format parameters
        format_params = FormatComplianceService.get_format_parameters_for_generation(
            format_type
        )
        
        # Initialize Nano Banana service
        nano_service = NanoBananaService()
        
        # Define async wrapper to handle all async operations in one event loop
        async def run_generation():
            try:
                # Generate image with identity consistency (Requirement 5.5)
                image_url, identity_strength, metadata = await nano_service.generate_image(
                    prompt=preset.prompt_template,
                    face_embedding=face.embedding_data,
                    face_id=face_id,
                    style_parameters=preset.style_parameters,
                    format_config=format_params
                )
                return image_url, identity_strength, metadata
            finally:
                # Close the async client in the same event loop
                await nano_service.close()
        
        try:
            # Run all async operations in a single event loop
            image_url, identity_strength, metadata = asyncio.run(run_generation())
            
            logger.info(
                f"Image generation successful for generation {generation_id}. "
                f"Identity strength: {identity_strength:.3f}"
            )
            
            # Validate generation output
            if not image_url:
                raise NonRetryableTaskError("Image generation returned no URL")
            
            if identity_strength < 0.95:
                raise IdentityConsistencyError(
                    f"Identity strength {identity_strength:.3f} below threshold 0.95"
                )
            
            # Update generation with image URL (partial completion)
            generation = db.query(Generation).filter(Generation.id == generation_id).first()
            if generation:
                generation.image_url = image_url
                generation.metadata = metadata
                db.commit()
            
            # Queue caption generation task
            from app.core.queue import enqueue_caption_generation
            try:
                caption_job = enqueue_caption_generation(
                    generation_id=generation_id,
                    image_url=image_url,
                    preset_type=preset_type
                )
                logger.info(
                    f"Queued caption generation job {caption_job.id} for generation {generation_id}"
                )
            except Exception as e:
                logger.error(f"Failed to queue caption generation: {e}")
                # Don't fail the image generation if caption queueing fails
            
            result = {
                "generation_id": generation_id,
                "status": "completed",
                "image_url": image_url,
                "identity_strength": identity_strength,
                "format_validated": True,
                "metadata": metadata
            }
            
            logger.info(f"Image generation task completed for generation {generation_id}")
            return result
            
        except Exception:
            # Re-raise to be handled by outer exception handlers
            raise
        
    except IdentityConsistencyError as e:
        # Identity consistency failure - not retryable
        logger.error(f"Identity consistency failure for generation {generation_id}: {e}")
        GenerationService.fail_generation(
            db, generation_id, 
            f"Identity consistency failure: {str(e)}",
            refund_credit=True
        )
        raise NonRetryableTaskError(f"Identity consistency failure: {str(e)}")
    
    except FormatComplianceError as e:
        # Format compliance failure - not retryable
        logger.error(f"Format compliance failure for generation {generation_id}: {e}")
        GenerationService.fail_generation(
            db, generation_id,
            f"Format compliance failure: {str(e)}",
            refund_credit=True
        )
        raise NonRetryableTaskError(f"Format compliance failure: {str(e)}")
    
    except APIConnectionError as e:
        # API connection error - retryable
        logger.warning(f"API connection error for generation {generation_id}: {e}")
        # Don't update status yet - let retry mechanism handle it
        raise RetryableTaskError(f"API connection error: {str(e)}")
    
    except (RetryableTaskError, NonRetryableTaskError):
        # Re-raise custom task errors
        raise
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in image generation for {generation_id}: {e}")
        GenerationService.fail_generation(
            db, generation_id,
            f"Unexpected error: {str(e)}",
            refund_credit=True
        )
        error_result = _handle_task_error("generate_image_task", e, **task_context)
        # Convert to retryable error to trigger retry mechanism
        raise RetryableTaskError(f"Unexpected error in image generation: {str(e)}")
    
    finally:
        db.close()


def process_face_embedding_task(face_id: str, image_path: str) -> Dict[str, Any]:
    """
    Background task for processing face embeddings.
    
    This task handles:
    - Face detection and validation
    - Embedding generation and encryption
    - Identity strength calculation
    - Secure storage of embeddings
    
    Args:
        face_id: UUID of the face record
        image_path: Path to the uploaded face image
    
    Returns:
        Dict with processing results or error information
        
    Raises:
        RetryableTaskError: For temporary failures that should be retried
        NonRetryableTaskError: For permanent failures that should not be retried
    """
    task_context = {
        "face_id": face_id,
        "image_path": image_path
    }
    
    try:
        logger.info(f"Starting face embedding processing for face {face_id}")
        
        # Validate input parameters
        if not face_id or not image_path:
            raise NonRetryableTaskError("Missing required parameters for face processing")
        
        # TODO: Implement actual face embedding logic
        # This will include:
        # 1. Load and validate image file
        # 2. Detect face and check quality
        # 3. Generate face embedding
        # 4. Encrypt embedding data
        # 5. Store in database with identity strength
        # 6. Update face record status
        
        # For now, return a placeholder response
        result = {
            "face_id": face_id,
            "status": "completed",
            "message": "Face embedding task placeholder - to be implemented",
            "embedding_generated": False,
            "identity_strength": None,
            "face_detected": False,
            "processing_time_seconds": 0
        }
        
        logger.info(f"Completed face embedding processing for face {face_id}")
        return result
        
    except (RetryableTaskError, NonRetryableTaskError):
        # Re-raise custom task errors
        raise
    except Exception as e:
        # Handle unexpected errors
        error_result = _handle_task_error("process_face_embedding_task", e, **task_context)
        # Convert to retryable error to trigger retry mechanism
        raise RetryableTaskError(f"Unexpected error in face processing: {str(e)}")


def generate_caption_task(generation_id: str, image_url: str, preset_type: str) -> Dict[str, Any]:
    """
    Background task for generating captions, hashtags, and locations.
    
    This task handles:
    - OpenAI GPT-4 integration for caption generation
    - Hashtag optimization (8-12 hashtags)
    - Location suggestion generation
    - Brand safety validation
    
    Validates Requirements 9.1, 9.2, 9.5, 10.1, 10.3, 10.5, 11.2, 11.4, 11.5
    
    Args:
        generation_id: UUID of the generation record
        image_url: URL of the generated image
        preset_type: Type of preset used
    
    Returns:
        Dict with caption and hashtag results or error information
        
    Raises:
        RetryableTaskError: For temporary failures that should be retried
        NonRetryableTaskError: For permanent failures that should not be retried
    """
    from app.services.caption_service import CaptionService
    from app.services.hashtag_service import HashtagService
    from app.services.location_service import LocationService
    from app.services.generation_service import GenerationService
    from app.core.database import SessionLocal
    import asyncio
    
    task_context = {
        "generation_id": generation_id,
        "image_url": image_url,
        "preset_type": preset_type
    }
    
    db = SessionLocal()
    
    try:
        logger.info(f"Starting caption generation for generation {generation_id}")
        
        # Validate input parameters
        if not all([generation_id, image_url, preset_type]):
            raise NonRetryableTaskError("Missing required parameters for caption generation")
        
        # Initialize services
        caption_service = CaptionService()
        hashtag_service = HashtagService()
        location_service = LocationService()
        
        # Define async wrapper to handle all async operations in one event loop
        async def run_caption_generation():
            try:
                # Generate caption (Requirements 9.1, 9.2, 9.5)
                caption, is_fallback = await caption_service.generate_caption(
                    preset_type=preset_type,
                    image_url=image_url
                )
                
                logger.info(
                    f"Caption generated for {generation_id}: "
                    f"{'(fallback)' if is_fallback else '(AI)'}"
                )
                
                # Generate hashtags (Requirements 10.1, 10.3, 10.5)
                hashtags = await hashtag_service.generate_hashtags(
                    preset_type=preset_type,
                    caption=caption
                )
                
                logger.info(f"Generated {len(hashtags)} hashtags for {generation_id}")
                
                # Generate location suggestion (Requirements 11.2, 11.4, 11.5)
                location = await location_service.suggest_location(
                    preset_type=preset_type,
                    caption=caption
                )
                
                if location:
                    logger.info(f"Location suggested for {generation_id}: {location}")
                else:
                    logger.info(f"No location suggested for {generation_id}")
                
                return caption, is_fallback, hashtags, location
            finally:
                # Close all async clients in the same event loop
                await caption_service.close()
                await hashtag_service.close()
                await location_service.close()
        
        try:
            # Run all async operations in a single event loop
            caption, is_fallback, hashtags, location = asyncio.run(run_caption_generation())
            
            # Update generation record with all metadata
            GenerationService.complete_generation(
                db=db,
                generation_id=generation_id,
                image_url=image_url,
                caption=caption,
                hashtags=hashtags,
                location=location
            )
            
            result = {
                "generation_id": generation_id,
                "status": "completed",
                "caption": caption,
                "caption_is_fallback": is_fallback,
                "hashtags": hashtags,
                "hashtag_count": len(hashtags),
                "location": location,
                "brand_safe": True
            }
            
            logger.info(f"Caption generation task completed for generation {generation_id}")
            return result
            
        except Exception:
            # Re-raise to be handled by outer exception handlers
            raise
        
    except (RetryableTaskError, NonRetryableTaskError):
        # Re-raise custom task errors
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in caption generation for {generation_id}: {e}")
        error_result = _handle_task_error("generate_caption_task", e, **task_context)
        # Convert to retryable error to trigger retry mechanism
        raise RetryableTaskError(f"Unexpected error in caption generation: {str(e)}")
    
    finally:
        db.close()


def analytics_tracking_task(event_type: str, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background task for analytics tracking.
    
    This task handles:
    - Usage metrics tracking
    - Conversion rate monitoring
    - Error rate tracking
    - Performance metrics collection
    
    Args:
        event_type: Type of event to track
        user_id: UUID of the user
        data: Event data to track
    
    Returns:
        Dict with tracking results or error information
    """
    task_context = {
        "event_type": event_type,
        "user_id": user_id,
        "data": data
    }
    
    try:
        logger.info(f"Starting analytics tracking for event {event_type}")
        
        # Validate input parameters
        if not event_type or not user_id:
            raise NonRetryableTaskError("Missing required parameters for analytics tracking")
        
        # TODO: Implement actual analytics tracking logic
        # This will include:
        # 1. Validate event data
        # 2. Store metrics in database
        # 3. Update aggregated statistics
        # 4. Trigger alerts if needed
        
        # For now, return a placeholder response
        result = {
            "event_type": event_type,
            "user_id": user_id,
            "status": "completed",
            "message": "Analytics tracking task placeholder - to be implemented",
            "tracked": False,
            "processing_time_seconds": 0
        }
        
        logger.info(f"Completed analytics tracking for event {event_type}")
        return result
        
    except (RetryableTaskError, NonRetryableTaskError):
        # Re-raise custom task errors
        raise
    except Exception as e:
        # Handle unexpected errors
        error_result = _handle_task_error("analytics_tracking_task", e, **task_context)
        # Most analytics errors should not be retried to avoid spam
        raise NonRetryableTaskError(f"Error in analytics tracking: {str(e)}")


def payment_processing_task(payment_id: str, user_id: str, plan_type: str) -> Dict[str, Any]:
    """
    Background task for payment processing.
    
    This task handles:
    - Stripe webhook processing
    - Plan upgrades/downgrades
    - Credit allocation
    - Payment failure handling
    
    Args:
        payment_id: Stripe payment ID
        user_id: UUID of the user
        plan_type: New plan type
    
    Returns:
        Dict with payment processing results or error information
    """
    task_context = {
        "payment_id": payment_id,
        "user_id": user_id,
        "plan_type": plan_type
    }
    
    try:
        logger.info(f"Starting payment processing for payment {payment_id}")
        
        # Validate input parameters
        if not all([payment_id, user_id, plan_type]):
            raise NonRetryableTaskError("Missing required parameters for payment processing")
        
        # TODO: Implement actual payment processing logic
        # This will include:
        # 1. Validate Stripe payment
        # 2. Update user plan
        # 3. Allocate credits
        # 4. Send confirmation email
        # 5. Track conversion metrics
        
        # For now, return a placeholder response
        result = {
            "payment_id": payment_id,
            "user_id": user_id,
            "plan_type": plan_type,
            "status": "completed",
            "message": "Payment processing task placeholder - to be implemented",
            "plan_updated": False,
            "credits_allocated": 0,
            "processing_time_seconds": 0
        }
        
        logger.info(f"Completed payment processing for payment {payment_id}")
        return result
        
    except (RetryableTaskError, NonRetryableTaskError):
        # Re-raise custom task errors
        raise
    except Exception as e:
        # Handle unexpected errors
        error_result = _handle_task_error("payment_processing_task", e, **task_context)
        # Payment errors are usually retryable
        raise RetryableTaskError(f"Error in payment processing: {str(e)}")