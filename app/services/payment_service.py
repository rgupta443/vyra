"""
Payment processing service using Stripe.
"""
import stripe
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.models.user import User, PlanType
from app.services.user_service import UserService

# Initialize Stripe with secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentError(Exception):
    """Base exception for payment-related errors."""
    pass


class CheckoutCreationError(PaymentError):
    """Exception raised when checkout session creation fails."""
    pass


class WebhookVerificationError(PaymentError):
    """Exception raised when webhook verification fails."""
    pass


class PaymentProcessingError(PaymentError):
    """Exception raised when payment processing fails."""
    pass


class PaymentService:
    """Service for handling Stripe payment operations."""
    
    # Plan configuration with pricing
    PLAN_CONFIG = {
        PlanType.FREE: {
            "name": "Free",
            "price": 0,
            "credits": 5,
            "description": "5 generations to get started",
            "stripe_price_id": None
        },
        PlanType.BASIC: {
            "name": "Basic",
            "price": 1999,  # $19.99 in cents
            "credits": 50,
            "description": "50 generations per month",
            "stripe_price_id": settings.STRIPE_BASIC_PRICE_ID if hasattr(settings, 'STRIPE_BASIC_PRICE_ID') else None
        },
        PlanType.PRO: {
            "name": "Pro",
            "price": 4999,  # $49.99 in cents
            "credits": 200,
            "description": "200 generations per month",
            "stripe_price_id": settings.STRIPE_PRO_PRICE_ID if hasattr(settings, 'STRIPE_PRO_PRICE_ID') else None
        }
    }
    
    @classmethod
    def get_plan_info(cls, plan_type: PlanType) -> Dict[str, Any]:
        """Get plan information."""
        return cls.PLAN_CONFIG.get(plan_type, cls.PLAN_CONFIG[PlanType.FREE])
    
    @classmethod
    def get_all_plans(cls) -> list[Dict[str, Any]]:
        """Get all available plans."""
        plans = []
        for plan_type in [PlanType.FREE, PlanType.BASIC, PlanType.PRO]:
            plan_info = cls.PLAN_CONFIG[plan_type].copy()
            plan_info["plan_type"] = plan_type.value
            plans.append(plan_info)
        return plans
    
    @classmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((stripe.error.APIConnectionError, stripe.error.RateLimitError))
    )
    async def create_checkout_session(
        cls,
        user: User,
        plan_type: PlanType,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, str]:
        """
        Create a Stripe checkout session for plan upgrade with retry logic.
        
        Args:
            user: User requesting the checkout
            plan_type: Plan type to subscribe to
            success_url: URL to redirect on successful payment
            cancel_url: URL to redirect on cancelled payment
            
        Returns:
            Dictionary with session_id and checkout URL
            
        Raises:
            CheckoutCreationError: If checkout creation fails after retries
            ValueError: If plan is invalid or Stripe price ID not configured
        """
        if plan_type == PlanType.FREE:
            raise ValueError("Cannot create checkout for free plan")
        
        plan_info = cls.get_plan_info(plan_type)
        
        try:
            # For development, create a one-time payment if price_id not configured
            if not plan_info["stripe_price_id"]:
                # Create one-time payment session
                session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[{
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"{plan_info['name']} Plan",
                                "description": plan_info["description"],
                            },
                            "unit_amount": plan_info["price"],
                        },
                        "quantity": 1,
                    }],
                    mode="payment",
                    success_url=success_url,
                    cancel_url=cancel_url,
                    client_reference_id=str(user.id),
                    metadata={
                        "user_id": str(user.id),
                        "plan_type": plan_type.value,
                        "credits": plan_info["credits"]
                    }
                )
            else:
                # Create subscription session with configured price ID
                session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[{
                        "price": plan_info["stripe_price_id"],
                        "quantity": 1,
                    }],
                    mode="subscription",
                    success_url=success_url,
                    cancel_url=cancel_url,
                    client_reference_id=str(user.id),
                    metadata={
                        "user_id": str(user.id),
                        "plan_type": plan_type.value,
                        "credits": plan_info["credits"]
                    }
                )
            
            return {
                "session_id": session.id,
                "url": session.url
            }
        
        except stripe.error.CardError as e:
            # Card was declined
            raise CheckoutCreationError(f"Card declined: {e.user_message}")
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters
            raise CheckoutCreationError(f"Invalid request: {str(e)}")
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe failed
            raise CheckoutCreationError("Payment system authentication failed. Please contact support.")
        except stripe.error.APIConnectionError as e:
            # Network communication failed - will be retried
            raise
        except stripe.error.RateLimitError as e:
            # Too many requests - will be retried
            raise
        except stripe.error.StripeError as e:
            # Generic Stripe error
            raise CheckoutCreationError(f"Payment processing error: {str(e)}")
        except Exception as e:
            # Unexpected error
            raise CheckoutCreationError(f"Unexpected error creating checkout: {str(e)}")
    
    @classmethod
    async def handle_webhook_event(
        cls,
        event_type: str,
        event_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Handle Stripe webhook events with error handling.
        
        Args:
            event_type: Type of webhook event
            event_data: Event data from Stripe
            db: Database session
            
        Returns:
            Dictionary with processing result
            
        Raises:
            PaymentProcessingError: If event processing fails critically
        """
        result = {"processed": False, "message": "Unknown event type"}
        
        try:
            if event_type == "checkout.session.completed":
                result = await cls._handle_checkout_completed(event_data, db)
            elif event_type == "customer.subscription.updated":
                result = await cls._handle_subscription_updated(event_data, db)
            elif event_type == "customer.subscription.deleted":
                result = await cls._handle_subscription_deleted(event_data, db)
            elif event_type == "invoice.payment_succeeded":
                result = await cls._handle_payment_succeeded(event_data, db)
            elif event_type == "invoice.payment_failed":
                result = await cls._handle_payment_failed(event_data, db)
            else:
                # Unknown event type - not an error, just log and continue
                result = {
                    "processed": True,
                    "message": f"Event type {event_type} not handled (ignored)"
                }
        
        except Exception as e:
            # Log error but don't raise - we want to return 200 to Stripe
            result = {
                "processed": False,
                "message": f"Error processing {event_type}: {str(e)}",
                "error": str(e)
            }
        
        return result
    
    @classmethod
    async def _handle_checkout_completed(
        cls,
        event_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Handle successful checkout completion with error handling.
        
        Requirements: 14.2, 14.3
        """
        session = event_data.get("object", {})
        user_id = session.get("metadata", {}).get("user_id")
        plan_type_str = session.get("metadata", {}).get("plan_type")
        credits = int(session.get("metadata", {}).get("credits", 0))
        
        if not user_id or not plan_type_str:
            return {"processed": False, "message": "Missing user_id or plan_type in metadata"}
        
        try:
            plan_type = PlanType(plan_type_str)
        except ValueError:
            return {"processed": False, "message": f"Invalid plan_type: {plan_type_str}"}
        
        try:
            # Update user plan and credits
            user = UserService.get_user_by_id(db, user_id)
            
            if not user:
                return {"processed": False, "message": f"User not found: {user_id}"}
            
            # Update plan and allocate credits
            user.plan_type = plan_type.value
            user.credits = credits
            db.commit()
            
            return {
                "processed": True,
                "message": f"User {user_id} upgraded to {plan_type.value} with {credits} credits"
            }
        
        except Exception as e:
            # Rollback on any error
            db.rollback()
            return {
                "processed": False,
                "message": f"Failed to update user: {str(e)}",
                "error": str(e)
            }
    
    @classmethod
    async def _handle_subscription_updated(
        cls,
        event_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Handle subscription update events."""
        subscription = event_data.get("object", {})
        customer_id = subscription.get("customer")
        
        # In a production system, you would look up the user by Stripe customer ID
        # For now, we'll return a success message
        return {
            "processed": True,
            "message": f"Subscription updated for customer {customer_id}"
        }
    
    @classmethod
    async def _handle_subscription_deleted(
        cls,
        event_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Handle subscription cancellation."""
        subscription = event_data.get("object", {})
        customer_id = subscription.get("customer")
        
        # In a production system, downgrade user to free plan
        return {
            "processed": True,
            "message": f"Subscription cancelled for customer {customer_id}"
        }
    
    @classmethod
    async def _handle_payment_succeeded(
        cls,
        event_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Handle successful recurring payment."""
        invoice = event_data.get("object", {})
        customer_id = invoice.get("customer")
        
        # In a production system, refresh user credits for the billing period
        return {
            "processed": True,
            "message": f"Payment succeeded for customer {customer_id}"
        }
    
    @classmethod
    async def _handle_payment_failed(
        cls,
        event_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Handle failed payment."""
        invoice = event_data.get("object", {})
        customer_id = invoice.get("customer")
        
        # In a production system, notify user and potentially suspend service
        return {
            "processed": True,
            "message": f"Payment failed for customer {customer_id}",
            "action_required": "notify_user"
        }
    
    @classmethod
    def verify_webhook_signature(cls, payload: bytes, signature: str) -> Optional[Dict[str, Any]]:
        """
        Verify Stripe webhook signature and construct event.
        
        Args:
            payload: Raw request body
            signature: Stripe signature header
            
        Returns:
            Constructed event dict or None if verification fails
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError:
            # Invalid payload
            return None
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return None
