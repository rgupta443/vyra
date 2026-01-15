"""
Tests for payment processing functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.payment_service import PaymentService, CheckoutCreationError
from app.models.user import User, PlanType
import stripe


class TestPaymentService:
    """Test suite for PaymentService."""
    
    def test_get_plan_info_free(self):
        """Test getting free plan information."""
        plan_info = PaymentService.get_plan_info(PlanType.FREE)
        assert plan_info["name"] == "Free"
        assert plan_info["price"] == 0
        assert plan_info["credits"] == 5
    
    def test_get_plan_info_basic(self):
        """Test getting basic plan information."""
        plan_info = PaymentService.get_plan_info(PlanType.BASIC)
        assert plan_info["name"] == "Basic"
        assert plan_info["price"] == 1999
        assert plan_info["credits"] == 50
    
    def test_get_plan_info_pro(self):
        """Test getting pro plan information."""
        plan_info = PaymentService.get_plan_info(PlanType.PRO)
        assert plan_info["name"] == "Pro"
        assert plan_info["price"] == 4999
        assert plan_info["credits"] == 200
    
    def test_get_all_plans(self):
        """Test getting all available plans."""
        plans = PaymentService.get_all_plans()
        assert len(plans) == 3
        assert plans[0]["plan_type"] == "free"
        assert plans[1]["plan_type"] == "basic"
        assert plans[2]["plan_type"] == "pro"
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_free_plan_raises_error(self):
        """Test that creating checkout for free plan raises ValueError."""
        user = Mock(spec=User)
        user.id = "test-user-id"
        
        with pytest.raises(ValueError, match="Cannot create checkout for free plan"):
            await PaymentService.create_checkout_session(
                user=user,
                plan_type=PlanType.FREE,
                success_url="http://example.com/success",
                cancel_url="http://example.com/cancel"
            )
    
    @pytest.mark.asyncio
    @patch('stripe.checkout.Session.create')
    async def test_create_checkout_session_basic_plan(self, mock_stripe_create):
        """Test creating checkout session for basic plan."""
        # Mock Stripe response
        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe_create.return_value = mock_session
        
        user = Mock(spec=User)
        user.id = "test-user-id"
        
        result = await PaymentService.create_checkout_session(
            user=user,
            plan_type=PlanType.BASIC,
            success_url="http://example.com/success",
            cancel_url="http://example.com/cancel"
        )
        
        assert result["session_id"] == "cs_test_123"
        assert result["url"] == "https://checkout.stripe.com/test"
        
        # Verify Stripe was called with correct parameters
        mock_stripe_create.assert_called_once()
        call_kwargs = mock_stripe_create.call_args[1]
        assert call_kwargs["mode"] == "payment"
        assert call_kwargs["client_reference_id"] == "test-user-id"
        assert call_kwargs["metadata"]["plan_type"] == "basic"
        assert call_kwargs["metadata"]["credits"] == 50
    
    @pytest.mark.asyncio
    @patch('stripe.checkout.Session.create')
    async def test_create_checkout_session_stripe_error(self, mock_stripe_create):
        """Test handling of Stripe errors during checkout creation."""
        # Mock Stripe error
        mock_stripe_create.side_effect = stripe.error.InvalidRequestError(
            message="Invalid request",
            param="price"
        )
        
        user = Mock(spec=User)
        user.id = "test-user-id"
        
        with pytest.raises(CheckoutCreationError, match="Invalid request"):
            await PaymentService.create_checkout_session(
                user=user,
                plan_type=PlanType.BASIC,
                success_url="http://example.com/success",
                cancel_url="http://example.com/cancel"
            )
    
    @pytest.mark.asyncio
    async def test_handle_checkout_completed_success(self, db):
        """Test successful checkout completion webhook handling."""
        # Create test user directly without password hashing
        from app.models.user import User
        import uuid
        
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            plan_type="free",
            credits=5
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        event_data = {
            "object": {
                "metadata": {
                    "user_id": str(user.id),
                    "plan_type": "basic",
                    "credits": "50"
                }
            }
        }
        
        result = await PaymentService._handle_checkout_completed(event_data, db)
        
        assert result["processed"] is True
        assert "upgraded to basic" in result["message"]
        
        # Verify user was updated
        db.refresh(user)
        assert user.plan_type == "basic"
        assert user.credits == 50
        
        # Cleanup
        db.delete(user)
        db.commit()
    
    @pytest.mark.asyncio
    async def test_handle_checkout_completed_missing_metadata(self, db):
        """Test checkout completion with missing metadata."""
        event_data = {
            "object": {
                "metadata": {}
            }
        }
        
        result = await PaymentService._handle_checkout_completed(event_data, db)
        
        assert result["processed"] is False
        assert "Missing user_id or plan_type" in result["message"]
    
    @pytest.mark.asyncio
    async def test_handle_checkout_completed_invalid_plan_type(self, db):
        """Test checkout completion with invalid plan type."""
        event_data = {
            "object": {
                "metadata": {
                    "user_id": "test-user-id",
                    "plan_type": "invalid_plan",
                    "credits": "50"
                }
            }
        }
        
        result = await PaymentService._handle_checkout_completed(event_data, db)
        
        assert result["processed"] is False
        assert "Invalid plan_type" in result["message"]
    
    @pytest.mark.asyncio
    async def test_handle_checkout_completed_user_not_found(self, db):
        """Test checkout completion when user doesn't exist."""
        import uuid
        
        event_data = {
            "object": {
                "metadata": {
                    "user_id": str(uuid.uuid4()),  # Use valid UUID format
                    "plan_type": "basic",
                    "credits": "50"
                }
            }
        }
        
        result = await PaymentService._handle_checkout_completed(event_data, db)
        
        assert result["processed"] is False
        assert "User not found" in result["message"]
    
    def test_verify_webhook_signature_invalid_payload(self):
        """Test webhook signature verification with invalid payload."""
        result = PaymentService.verify_webhook_signature(
            payload=b"invalid",
            signature="invalid_signature"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_webhook_event_unknown_type(self, db):
        """Test handling of unknown webhook event types."""
        result = await PaymentService.handle_webhook_event(
            event_type="unknown.event.type",
            event_data={},
            db=db
        )
        
        assert result["processed"] is True
        assert "not handled" in result["message"]
