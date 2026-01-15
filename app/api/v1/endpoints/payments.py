"""
Payment processing endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.dependencies import get_db, get_current_user
from app.models.user import User, PlanType
from app.schemas.payment import CheckoutRequest, CheckoutResponse, PlanInfo
from app.services.payment_service import (
    PaymentService,
    CheckoutCreationError,
    WebhookVerificationError,
    PaymentProcessingError
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create Stripe checkout session for plan upgrade.
    
    Implements retry logic for transient failures and provides clear error messages.
    
    Requirements: 14.1, 14.2, 14.4
    """
    try:
        # Validate plan type
        if request.plan_type == PlanType.FREE:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_plan",
                    "message": "Cannot create checkout for free plan. Free plan is already active.",
                    "user_message": "The free plan is already available to you. Please select a paid plan to upgrade."
                }
            )
        
        # Create checkout session (with automatic retry for transient failures)
        session_data = await PaymentService.create_checkout_session(
            user=current_user,
            plan_type=request.plan_type,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        
        return CheckoutResponse(
            session_id=session_data["session_id"],
            url=session_data["url"]
        )
    
    except CheckoutCreationError as e:
        # Payment-specific error with clear message
        logger.error(f"Checkout creation failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "checkout_failed",
                "message": str(e),
                "user_message": "We couldn't process your payment request. Please try again or contact support if the issue persists."
            }
        )
    
    except ValueError as e:
        # Validation error
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_error",
                "message": str(e),
                "user_message": "Invalid payment information provided. Please check your details and try again."
            }
        )
    
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error creating checkout for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred",
                "user_message": "We're experiencing technical difficulties. Please try again in a few moments or contact support."
            }
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhooks for payment events.
    
    Verifies webhook signatures and processes payment events with error handling.
    
    Requirements: 14.3, 14.4, 14.5
    """
    if not stripe_signature:
        logger.warning("Webhook received without stripe-signature header")
        raise HTTPException(
            status_code=400,
            detail="Missing stripe-signature header"
        )
    
    # Get raw request body
    payload = await request.body()
    
    # Verify webhook signature
    event = PaymentService.verify_webhook_signature(payload, stripe_signature)
    
    if not event:
        logger.warning("Webhook signature verification failed")
        raise HTTPException(
            status_code=400,
            detail="Invalid signature"
        )
    
    # Process webhook event
    try:
        result = await PaymentService.handle_webhook_event(
            event_type=event["type"],
            event_data=event["data"],
            db=db
        )
        
        # Log result
        if result.get("processed"):
            logger.info(f"Webhook processed: {event['type']} - {result.get('message')}")
        else:
            logger.warning(f"Webhook not processed: {event['type']} - {result.get('message')}")
        
        # Always return 200 to prevent Stripe retries for non-critical errors
        return {
            "status": "success" if result.get("processed") else "acknowledged",
            "processed": result.get("processed", False),
            "message": result.get("message", "Event received")
        }
    
    except Exception as e:
        # Log error but return 200 to prevent Stripe retries
        logger.error(f"Error processing webhook {event['type']}: {str(e)}")
        return {
            "status": "error",
            "message": f"Error processing webhook: {str(e)}"
        }


@router.get("/plans", response_model=list[PlanInfo])
async def get_plans():
    """
    Get available subscription plans.
    
    Returns list of all available plans with pricing and features.
    """
    try:
        plans = PaymentService.get_all_plans()
        return [
            PlanInfo(
                plan_type=PlanType(plan["plan_type"]),
                name=plan["name"],
                price=plan["price"],
                credits=plan["credits"],
                description=plan["description"],
                stripe_price_id=plan.get("stripe_price_id")
            )
            for plan in plans
        ]
    except Exception as e:
        logger.error(f"Error fetching plans: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to fetch plans",
                "user_message": "We couldn't load the available plans. Please try again later."
            }
        )

