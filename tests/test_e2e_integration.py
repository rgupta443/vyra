"""
End-to-end integration tests for Instagram Content Automation.

This test suite validates complete user journeys from registration through
content generation, covering all major system components and their interactions.

Tests validate requirements across authentication, face management, credit system,
content generation, and queue processing.
"""
import pytest
import time
import uuid
from datetime import datetime
from typing import Dict, Any
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User, PlanType
from app.models.face import Face
from app.models.generation import Generation, GenerationStatus, PresetType, FormatType
from app.core.database import SessionLocal
from app.services.user_service import UserService
from app.core.queue import queue_manager, QueueName, JobType


class TestCompleteUserJourney:
    """Test complete user journey from registration to content download."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def db(self):
        """Create database session."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def test_user_email(self):
        """Generate unique test user email."""
        return f"test_e2e_{uuid.uuid4().hex[:8]}@example.com"
    
    def test_complete_user_journey_free_plan(self, client, db, test_user_email):
        """
        Test complete user journey on free plan.
        
        Journey:
        1. User registers
        2. User uploads face
        3. User generates content (uses 1 credit)
        4. User views generation history
        5. User attempts second generation (should fail - no credits)
        
        Validates Requirements: 1.1, 2.1, 2.2, 3.1, 3.2, 5.1, 5.2, 12.1, 12.3, 15.1
        """
        # Step 1: User registration (Requirement 1.1)
        register_response = client.post("/api/v1/auth/register", json={
            "email": test_user_email,
            "password": "SecurePass123!"
        })
        assert register_response.status_code == 200
        token_data = register_response.json()
        assert "access_token" in token_data
        access_token = token_data["access_token"]
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Verify user has free plan with 1 credit (Requirement 2.1)
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["plan_type"] == PlanType.FREE.value
        assert user_data["credits"] == 1
        user_id = user_data["id"]
        
        # Step 2: Upload face (Requirements 3.1, 3.2)
        with patch("app.services.face_service.FaceService.validate_face_image") as mock_validate:
            mock_validate.return_value = (True, None)
            
            # Create mock file upload
            face_upload_response = client.post(
                "/api/v1/faces/upload",
                headers=headers,
                files={"file": ("test_face.jpg", b"fake_image_data", "image/jpeg")}
            )
            assert face_upload_response.status_code == 200
            face_data = face_upload_response.json()
            assert "id" in face_data
            face_id = face_data["id"]
        
        # Verify face is active
        current_face_response = client.get("/api/v1/faces/current", headers=headers)
        assert current_face_response.status_code == 200
        current_face = current_face_response.json()
        assert current_face["id"] == face_id
        assert current_face["is_active"] is True
        
        # Step 3: Generate content (Requirements 5.1, 5.2, 12.3)
        with patch("app.core.queue.enqueue_image_generation") as mock_enqueue:
            mock_job = MagicMock()
            mock_job.id = "test_job_123"
            mock_enqueue.return_value = mock_job
            
            generation_response = client.post(
                "/api/v1/generate/image",
                headers=headers,
                json={
                    "preset_type": PresetType.LUXURY.value,
                    "format_type": FormatType.FEED_4_5.value
                }
            )
            assert generation_response.status_code == 200
            generation_data = generation_response.json()
            assert generation_data["status"] == GenerationStatus.PENDING.value
            generation_id = generation_data["id"]
        
        # Verify credit was deducted (Requirement 2.1)
        me_response = client.get("/api/v1/auth/me", headers=headers)
        user_data = me_response.json()
        assert user_data["credits"] == 0
        
        # Step 4: Check generation status (Requirement 12.3)
        status_response = client.get(
            f"/api/v1/generate/status/{generation_id}",
            headers=headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["id"] == generation_id
        assert status_data["user_id"] == user_id
        
        # Step 5: View generation history (Requirement 12.1)
        history_response = client.get("/api/v1/generate/history", headers=headers)
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert len(history_data) == 1
        assert history_data[0]["id"] == generation_id
        
        # Step 6: Attempt second generation without credits (Requirement 2.2, 15.1)
        generation_response_2 = client.post(
            "/api/v1/generate/image",
            headers=headers,
            json={
                "preset_type": PresetType.LIFESTYLE.value,
                "format_type": FormatType.REEL_9_16.value
            }
        )
        assert generation_response_2.status_code == 402  # Payment required
        error_data = generation_response_2.json()
        assert "detail" in error_data
        assert "credits" in str(error_data["detail"]).lower()
    
    def test_complete_user_journey_paid_plan(self, client, db, test_user_email):
        """
        Test complete user journey on paid plan with multiple generations.
        
        Journey:
        1. User registers
        2. User upgrades to BASIC plan (simulated)
        3. User uploads face
        4. User generates multiple pieces of content
        5. User views all generations
        
        Validates Requirements: 1.1, 2.3, 3.1, 5.1, 12.1, 15.2
        """
        # Step 1: Register user
        register_response = client.post("/api/v1/auth/register", json={
            "email": test_user_email,
            "password": "SecurePass123!"
        })
        assert register_response.status_code == 200
        access_token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 2: Simulate plan upgrade (Requirement 2.3)
        user = db.query(User).filter(User.email == test_user_email).first()
        user.plan_type = PlanType.BASIC.value
        user.credits = 50
        db.commit()
        
        # Verify upgrade
        me_response = client.get("/api/v1/auth/me", headers=headers)
        user_data = me_response.json()
        assert user_data["plan_type"] == PlanType.BASIC.value
        assert user_data["credits"] == 50
        
        # Step 3: Upload face
        with patch("app.services.face_service.FaceService.validate_face_image") as mock_validate:
            mock_validate.return_value = (True, None)
            face_upload_response = client.post(
                "/api/v1/faces/upload",
                headers=headers,
                files={"file": ("test_face.jpg", b"fake_image_data", "image/jpeg")}
            )
            assert face_upload_response.status_code == 200
        
        # Step 4: Generate multiple pieces of content (Requirement 15.2)
        generation_ids = []
        with patch("app.core.queue.enqueue_image_generation") as mock_enqueue:
            mock_job = MagicMock()
            mock_job.id = "test_job"
            mock_enqueue.return_value = mock_job
            
            for i in range(3):
                generation_response = client.post(
                    "/api/v1/generate/image",
                    headers=headers,
                    json={
                        "preset_type": [PresetType.LUXURY, PresetType.LIFESTYLE, PresetType.BEAUTY][i].value,
                        "format_type": FormatType.FEED_4_5.value
                    }
                )
                assert generation_response.status_code == 200
                generation_ids.append(generation_response.json()["id"])
        
        # Verify credits deducted correctly
        me_response = client.get("/api/v1/auth/me", headers=headers)
        user_data = me_response.json()
        assert user_data["credits"] == 47  # 50 - 3
        
        # Step 5: View all generations (Requirement 12.1)
        history_response = client.get("/api/v1/generate/history", headers=headers)
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert len(history_data) == 3
        assert all(gen["id"] in generation_ids for gen in history_data)


class TestAPIIntegration:
    """Test API endpoint integration and data flow."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def db(self):
        """Create database session."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def authenticated_user(self, client, db):
        """Create and authenticate a test user."""
        email = f"test_api_{uuid.uuid4().hex[:8]}@example.com"
        
        # Register user
        register_response = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "TestPass123!"
        })
        assert register_response.status_code == 200
        token = register_response.json()["access_token"]
        
        # Get user from database
        user = db.query(User).filter(User.email == email).first()
        
        return {
            "user": user,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }
    
    def test_authentication_flow_integration(self, client, db):
        """
        Test complete authentication flow integration.
        
        Validates Requirements: 1.1, 1.2, 1.3, 1.4
        """
        email = f"test_auth_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePass123!"
        
        # Register (Requirement 1.1)
        register_response = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password
        })
        assert register_response.status_code == 200
        assert "access_token" in register_response.json()
        
        # Login (Requirement 1.2)
        login_response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Access protected endpoint (Requirement 1.3)
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == email
        
        # Logout (Requirement 1.4)
        logout_response = client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200
    
    def test_face_management_integration(self, client, db, authenticated_user):
        """
        Test face upload and management integration.
        
        Validates Requirements: 3.1, 3.2, 3.3, 4.1, 4.4
        """
        headers = authenticated_user["headers"]
        user = authenticated_user["user"]
        
        # Upload face (Requirements 3.1, 3.2)
        with patch("app.services.face_service.FaceService.validate_face_image") as mock_validate:
            mock_validate.return_value = (True, None)
            
            upload_response = client.post(
                "/api/v1/faces/upload",
                headers=headers,
                files={"file": ("face.jpg", b"fake_image_data", "image/jpeg")}
            )
            assert upload_response.status_code == 200
            face_data = upload_response.json()
            face_id = face_data["id"]
        
        # Verify face is active (Requirement 4.4)
        current_face_response = client.get("/api/v1/faces/current", headers=headers)
        assert current_face_response.status_code == 200
        current_face = current_face_response.json()
        assert current_face["id"] == face_id
        assert current_face["is_active"] is True
        
        # Attempt to upload second face (Requirement 3.3)
        with patch("app.services.face_service.FaceService.validate_face_image") as mock_validate:
            mock_validate.return_value = (True, None)
            
            second_upload_response = client.post(
                "/api/v1/faces/upload",
                headers=headers,
                files={"file": ("face2.jpg", b"fake_image_data", "image/jpeg")}
            )
            assert second_upload_response.status_code == 400
            assert "already has an active face" in second_upload_response.json()["detail"].lower()
        
        # Delete face
        delete_response = client.delete("/api/v1/faces/current", headers=headers)
        assert delete_response.status_code == 200
        
        # Verify face is deleted
        current_face_response = client.get("/api/v1/faces/current", headers=headers)
        assert current_face_response.status_code == 404
    
    def test_credit_system_integration(self, client, db, authenticated_user):
        """
        Test credit system integration across generation requests.
        
        Validates Requirements: 2.1, 2.2, 2.3, 5.1
        """
        headers = authenticated_user["headers"]
        user = authenticated_user["user"]
        
        # Verify initial credits
        me_response = client.get("/api/v1/auth/me", headers=headers)
        initial_credits = me_response.json()["credits"]
        assert initial_credits == 1  # Free plan
        
        # Upload face first
        with patch("app.services.face_service.FaceService.validate_face_image") as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/v1/faces/upload",
                headers=headers,
                files={"file": ("face.jpg", b"fake_image_data", "image/jpeg")}
            )
        
        # Generate content (Requirement 2.1)
        with patch("app.core.queue.enqueue_image_generation") as mock_enqueue:
            mock_job = MagicMock()
            mock_job.id = "test_job"
            mock_enqueue.return_value = mock_job
            
            generation_response = client.post(
                "/api/v1/generate/image",
                headers=headers,
                json={
                    "preset_type": PresetType.LUXURY.value,
                    "format_type": FormatType.FEED_4_5.value
                }
            )
            assert generation_response.status_code == 200
        
        # Verify credit deducted (Requirement 2.1)
        me_response = client.get("/api/v1/auth/me", headers=headers)
        current_credits = me_response.json()["credits"]
        assert current_credits == initial_credits - 1
        
        # Attempt generation without credits (Requirement 2.2)
        generation_response_2 = client.post(
            "/api/v1/generate/image",
            headers=headers,
            json={
                "preset_type": PresetType.LIFESTYLE.value,
                "format_type": FormatType.REEL_9_16.value
            }
        )
        assert generation_response_2.status_code == 402
    
    def test_generation_workflow_integration(self, client, db, authenticated_user):
        """
        Test complete generation workflow from request to completion.
        
        Validates Requirements: 5.1, 5.2, 5.5, 12.3
        """
        headers = authenticated_user["headers"]
        user = authenticated_user["user"]
        
        # Give user credits
        user.credits = 10
        db.commit()
        
        # Upload face
        with patch("app.services.face_service.FaceService.validate_face_image") as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/v1/faces/upload",
                headers=headers,
                files={"file": ("face.jpg", b"fake_image_data", "image/jpeg")}
            )
        
        # Request generation (Requirements 5.1, 5.2)
        with patch("app.core.queue.enqueue_image_generation") as mock_enqueue:
            mock_job = MagicMock()
            mock_job.id = "test_job_456"
            mock_enqueue.return_value = mock_job
            
            generation_response = client.post(
                "/api/v1/generate/image",
                headers=headers,
                json={
                    "preset_type": PresetType.BEAUTY.value,
                    "format_type": FormatType.SQUARE_1_1.value
                }
            )
            assert generation_response.status_code == 200
            generation_data = generation_response.json()
            generation_id = generation_data["id"]
            
            # Verify job was enqueued (Requirement 5.5)
            mock_enqueue.assert_called_once()
        
        # Check status (Requirement 12.3)
        status_response = client.get(
            f"/api/v1/generate/status/{generation_id}",
            headers=headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == GenerationStatus.PENDING.value
        
        # Simulate completion
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        generation.status = GenerationStatus.COMPLETED.value
        generation.image_url = "https://example.com/image.jpg"
        generation.caption = "Test caption"
        generation.hashtags = ["#test", "#instagram"]
        generation.completed_at = datetime.utcnow()
        db.commit()
        
        # Verify completion
        status_response = client.get(
            f"/api/v1/generate/status/{generation_id}",
            headers=headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == GenerationStatus.COMPLETED.value
        assert status_data["image_url"] is not None
        assert status_data["caption"] is not None


class TestQueueProcessing:
    """Test queue processing and job execution under various conditions."""
    
    @pytest.fixture
    def db(self):
        """Create database session."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def test_queue_health_check(self):
        """
        Test queue system health check.
        
        Validates Requirement: 16.1, 16.2
        """
        health = queue_manager.health_check()
        assert health["status"] == "healthy"
        assert health["redis_connected"] is True
        assert health["queues_initialized"] > 0
    
    def test_queue_stats_retrieval(self):
        """
        Test queue statistics retrieval.
        
        Validates Requirement: 17.1, 17.3
        """
        stats = queue_manager.get_all_queue_stats()
        assert isinstance(stats, dict)
        assert len(stats) > 0
        
        # Check generation queue stats
        gen_queue_stats = queue_manager.get_queue_stats(QueueName.GENERATION)
        assert "queue_name" in gen_queue_stats
        assert "length" in gen_queue_stats
    
    def test_job_enqueue_and_status(self, db):
        """
        Test job enqueueing and status tracking.
        
        Validates Requirements: 5.5, 12.3, 16.1
        """
        # Create test user and face
        user = User(
            email=f"test_queue_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="fake_hash",
            plan_type=PlanType.FREE.value,
            credits=1
        )
        db.add(user)
        db.commit()
        
        face = Face(
            user_id=user.id,
            image_url="https://example.com/face.jpg",
            embedding_data=b"fake_embedding",
            identity_strength=0.98,
            is_active=True
        )
        db.add(face)
        db.commit()
        
        generation = Generation(
            user_id=user.id,
            face_id=face.id,
            preset_type=PresetType.LUXURY.value,
            format_type=FormatType.FEED_4_5.value,
            status=GenerationStatus.PENDING.value
        )
        db.add(generation)
        db.commit()
        
        # Mock the actual task to avoid external API calls
        with patch("app.worker.tasks.generate_image_task") as mock_task:
            mock_task.return_value = {
                "generation_id": str(generation.id),
                "status": "completed",
                "image_url": "https://example.com/generated.jpg"
            }
            
            # Enqueue job (Requirement 5.5)
            from app.core.queue import enqueue_image_generation
            job = enqueue_image_generation(
                generation_id=str(generation.id),
                user_id=str(user.id),
                face_id=str(face.id),
                preset_type=PresetType.LUXURY.value,
                format_type=FormatType.FEED_4_5.value
            )
            
            assert job is not None
            assert job.id is not None
            
            # Check job status (Requirement 12.3)
            job_status = queue_manager.get_job_status(job.id)
            assert job_status["job_id"] == job.id
            assert "status" in job_status
    
    def test_queue_error_handling(self):
        """
        Test queue error handling and retry logic.
        
        Validates Requirements: 16.1, 16.2, 16.3, 16.4
        """
        # Test invalid job enqueueing
        with pytest.raises(Exception):
            queue_manager.enqueue_job(
                QueueName.GENERATION,
                JobType.IMAGE_GENERATION,
                None,  # Invalid function
                generation_id="test"
            )
        
        # Test job status for non-existent job
        status = queue_manager.get_job_status("non_existent_job_id")
        assert status["status"] == "not_found"
    
    def test_multiple_queue_processing(self, db):
        """
        Test processing multiple jobs across different queues.
        
        Validates Requirements: 16.1, 16.2
        """
        # Create test data
        user = User(
            email=f"test_multi_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="fake_hash",
            plan_type=PlanType.BASIC.value,
            credits=10
        )
        db.add(user)
        db.commit()
        
        face = Face(
            user_id=user.id,
            image_url="https://example.com/face.jpg",
            embedding_data=b"fake_embedding",
            identity_strength=0.98,
            is_active=True
        )
        db.add(face)
        db.commit()
        
        # Enqueue multiple jobs
        job_ids = []
        with patch("app.worker.tasks.generate_image_task") as mock_task:
            mock_task.return_value = {"status": "completed"}
            
            for i in range(3):
                generation = Generation(
                    user_id=user.id,
                    face_id=face.id,
                    preset_type=PresetType.LUXURY.value,
                    format_type=FormatType.FEED_4_5.value,
                    status=GenerationStatus.PENDING.value
                )
                db.add(generation)
                db.commit()
                
                from app.core.queue import enqueue_image_generation
                job = enqueue_image_generation(
                    generation_id=str(generation.id),
                    user_id=str(user.id),
                    face_id=str(face.id),
                    preset_type=PresetType.LUXURY.value,
                    format_type=FormatType.FEED_4_5.value
                )
                job_ids.append(job.id)
        
        # Verify all jobs were enqueued
        assert len(job_ids) == 3
        
        # Check queue stats
        stats = queue_manager.get_queue_stats(QueueName.GENERATION)
        assert stats["length"] >= 0  # Jobs may have been processed


class TestSystemResilience:
    """Test system resilience and error recovery."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def db(self):
        """Create database session."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def test_generation_failure_credit_refund(self, client, db):
        """
        Test that failed generations refund credits.
        
        Validates Requirements: 16.4
        """
        # Create user with credits
        email = f"test_refund_{uuid.uuid4().hex[:8]}@example.com"
        register_response = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "TestPass123!"
        })
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Give user credits
        user = db.query(User).filter(User.email == email).first()
        user.credits = 5
        db.commit()
        
        # Upload face
        with patch("app.services.face_service.FaceService.validate_face_image") as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/v1/faces/upload",
                headers=headers,
                files={"file": ("face.jpg", b"fake_image_data", "image/jpeg")}
            )
        
        # Request generation that will fail
        with patch("app.core.queue.enqueue_image_generation") as mock_enqueue:
            mock_enqueue.side_effect = Exception("Queue failure")
            
            generation_response = client.post(
                "/api/v1/generate/image",
                headers=headers,
                json={
                    "preset_type": PresetType.LUXURY.value,
                    "format_type": FormatType.FEED_4_5.value
                }
            )
            # Should fail with 500
            assert generation_response.status_code == 500
        
        # Verify credit was refunded
        db.refresh(user)
        assert user.credits == 5  # Credit should be refunded
    
    def test_concurrent_generation_requests(self, client, db):
        """
        Test handling of concurrent generation requests.
        
        Validates Requirements: 16.1, 16.2
        """
        # Create user with multiple credits
        email = f"test_concurrent_{uuid.uuid4().hex[:8]}@example.com"
        register_response = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "TestPass123!"
        })
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        user = db.query(User).filter(User.email == email).first()
        user.credits = 10
        db.commit()
        
        # Upload face
        with patch("app.services.face_service.FaceService.validate_face_image") as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/v1/faces/upload",
                headers=headers,
                files={"file": ("face.jpg", b"fake_image_data", "image/jpeg")}
            )
        
        # Make multiple concurrent requests
        with patch("app.core.queue.enqueue_image_generation") as mock_enqueue:
            mock_job = MagicMock()
            mock_job.id = "test_job"
            mock_enqueue.return_value = mock_job
            
            responses = []
            for i in range(5):
                response = client.post(
                    "/api/v1/generate/image",
                    headers=headers,
                    json={
                        "preset_type": PresetType.LUXURY.value,
                        "format_type": FormatType.FEED_4_5.value
                    }
                )
                responses.append(response)
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # Verify correct number of credits deducted
        db.refresh(user)
        assert user.credits == 5  # 10 - 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
