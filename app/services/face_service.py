"""
Face management service for upload validation, processing, and storage.
"""
import os
import io
import uuid
import hashlib
from typing import Optional, Tuple, BinaryIO
from pathlib import Path
from PIL import Image, ImageOps
import cv2
import numpy as np
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
import pickle
from cryptography.fernet import Fernet

from app.core.config import settings
from app.models.face import Face
from app.models.user import User
from app.services.plan_service import PlanService


class FaceValidationError(Exception):
    """Custom exception for face validation errors."""
    pass


class FaceService:
    """Service for face upload validation and management."""
    
    # Supported image formats
    SUPPORTED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}
    
    # Image constraints
    MIN_IMAGE_SIZE = (224, 224)  # Minimum size for face detection
    MAX_IMAGE_SIZE = (2048, 2048)  # Maximum size to prevent memory issues
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Identity consistency threshold
    IDENTITY_THRESHOLD = 0.95
    
    @classmethod
    def _get_encryption_key(cls) -> bytes:
        """
        Get or create encryption key for face embeddings.
        
        Returns:
            Encryption key bytes
        """
        # In production, this should be stored securely (e.g., AWS KMS, HashiCorp Vault)
        # For now, we'll derive it from the secret key
        key_material = settings.SECRET_KEY.encode()
        # Use first 32 bytes of SHA-256 hash for Fernet key
        key_hash = hashlib.sha256(key_material).digest()[:32]
        # Fernet requires base64-encoded key
        import base64
        return base64.urlsafe_b64encode(key_hash)
    
    @classmethod
    def _encrypt_embedding(cls, embedding: np.ndarray) -> bytes:
        """
        Encrypt face embedding for secure storage.
        
        Args:
            embedding: Face embedding array
            
        Returns:
            Encrypted embedding bytes
        """
        # Serialize embedding
        embedding_bytes = pickle.dumps(embedding)
        
        # Encrypt
        fernet = Fernet(cls._get_encryption_key())
        encrypted_bytes = fernet.encrypt(embedding_bytes)
        
        return encrypted_bytes
    
    @classmethod
    def _decrypt_embedding(cls, encrypted_data: bytes) -> np.ndarray:
        """
        Decrypt face embedding from storage.
        
        Args:
            encrypted_data: Encrypted embedding bytes
            
        Returns:
            Face embedding array
        """
        # Decrypt
        fernet = Fernet(cls._get_encryption_key())
        embedding_bytes = fernet.decrypt(encrypted_data)
        
        # Deserialize
        embedding = pickle.loads(embedding_bytes)
        
        return embedding
    
    @classmethod
    def generate_face_embedding(cls, image: Image.Image, face_box: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Generate face embedding from detected face region.
        
        Args:
            image: PIL Image containing the face
            face_box: Tuple of (x, y, width, height) for face region
            
        Returns:
            Face embedding as numpy array
        """
        x, y, w, h = face_box
        
        # Extract face region with some padding
        padding = int(min(w, h) * 0.2)  # 20% padding
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(image.size[0], x + w + padding)
        y2 = min(image.size[1], y + h + padding)
        
        # Crop face region
        face_image = image.crop((x1, y1, x2, y2))
        
        # Resize to standard size for embedding
        face_image = face_image.resize((224, 224), Image.Resampling.LANCZOS)
        
        # Convert to numpy array
        face_array = np.array(face_image)
        
        # Normalize pixel values
        face_array = face_array.astype(np.float32) / 255.0
        
        # For now, we'll create a simple embedding based on image statistics
        # In a production system, this would use a proper face recognition model
        # like FaceNet, ArcFace, or similar
        
        # Calculate basic image features as a simple embedding
        # This is a placeholder - in production, use a proper face recognition model
        embedding_features = []
        
        # Color channel means
        embedding_features.extend(np.mean(face_array, axis=(0, 1)))
        
        # Color channel standard deviations
        embedding_features.extend(np.std(face_array, axis=(0, 1)))
        
        # Histogram features for each channel
        for channel in range(3):
            hist, _ = np.histogram(face_array[:, :, channel], bins=16, range=(0, 1))
            embedding_features.extend(hist / np.sum(hist))  # Normalize histogram
        
        # Texture features (simple gradient-based)
        gray = np.mean(face_array, axis=2)
        grad_x = np.gradient(gray, axis=1)
        grad_y = np.gradient(gray, axis=0)
        embedding_features.extend([
            np.mean(np.abs(grad_x)),
            np.std(grad_x),
            np.mean(np.abs(grad_y)),
            np.std(grad_y)
        ])
        
        # Convert to numpy array and normalize
        embedding = np.array(embedding_features, dtype=np.float32)
        embedding = embedding / np.linalg.norm(embedding)  # L2 normalize
        
        return embedding
    
    @classmethod
    def calculate_identity_strength(cls, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate identity strength between two face embeddings.
        
        Args:
            embedding1: First face embedding
            embedding2: Second face embedding
            
        Returns:
            Identity strength score (0.0 to 1.0)
        """
        # Calculate cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cosine_similarity = dot_product / (norm1 * norm2)
        
        # Convert to 0-1 range (cosine similarity is -1 to 1)
        identity_strength = (cosine_similarity + 1) / 2
        
        return float(identity_strength)
    
    @classmethod
    def validate_identity_consistency(cls, new_embedding: np.ndarray, stored_embedding: np.ndarray) -> bool:
        """
        Validate that new embedding maintains identity consistency.
        
        Args:
            new_embedding: New face embedding to validate
            stored_embedding: Previously stored face embedding
            
        Returns:
            True if identity is consistent, False otherwise
        """
        identity_strength = cls.calculate_identity_strength(new_embedding, stored_embedding)
        return identity_strength >= cls.IDENTITY_THRESHOLD
    
    @classmethod
    def validate_upload_file(cls, file: UploadFile) -> None:
        """
        Validate uploaded file meets basic requirements.
        
        Args:
            file: FastAPI UploadFile object
            
        Raises:
            FaceValidationError: If file doesn't meet requirements
        """
        # Check file size
        if file.size and file.size > cls.MAX_FILE_SIZE:
            raise FaceValidationError(f"File size {file.size} exceeds maximum {cls.MAX_FILE_SIZE} bytes")
        
        # Check content type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise FaceValidationError("File must be an image")
        
        # Check filename extension
        if not file.filename:
            raise FaceValidationError("Filename is required")
        
        file_ext = Path(file.filename).suffix.upper().lstrip(".")
        if file_ext not in cls.SUPPORTED_FORMATS:
            raise FaceValidationError(f"Unsupported format. Supported: {', '.join(cls.SUPPORTED_FORMATS)}")
    
    @classmethod
    def validate_image_content(cls, image_data: bytes) -> Tuple[Image.Image, dict]:
        """
        Validate image content and extract metadata.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Tuple of (PIL Image, metadata dict)
            
        Raises:
            FaceValidationError: If image is invalid or doesn't meet requirements
        """
        try:
            # Open and validate image
            image = Image.open(io.BytesIO(image_data))
            
            # Fix orientation based on EXIF data
            image = ImageOps.exif_transpose(image)
            
            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Check image dimensions
            width, height = image.size
            if width < cls.MIN_IMAGE_SIZE[0] or height < cls.MIN_IMAGE_SIZE[1]:
                raise FaceValidationError(
                    f"Image too small. Minimum size: {cls.MIN_IMAGE_SIZE[0]}x{cls.MIN_IMAGE_SIZE[1]}"
                )
            
            if width > cls.MAX_IMAGE_SIZE[0] or height > cls.MAX_IMAGE_SIZE[1]:
                raise FaceValidationError(
                    f"Image too large. Maximum size: {cls.MAX_IMAGE_SIZE[0]}x{cls.MAX_IMAGE_SIZE[1]}"
                )
            
            # Extract metadata
            metadata = {
                "width": width,
                "height": height,
                "format": image.format,
                "mode": image.mode,
                "size_bytes": len(image_data)
            }
            
            return image, metadata
            
        except Exception as e:
            if isinstance(e, FaceValidationError):
                raise
            raise FaceValidationError(f"Invalid image file: {str(e)}")
    
    @classmethod
    def detect_and_validate_face(cls, image: Image.Image) -> dict:
        """
        Detect face in image and validate quality.
        
        Args:
            image: PIL Image object
            
        Returns:
            Dict with face detection results
            
        Raises:
            FaceValidationError: If no face detected or quality insufficient
        """
        # Convert PIL image to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Load OpenCV face cascade classifier
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            cv_image,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        if len(faces) == 0:
            raise FaceValidationError("No face detected in image. Please upload a clear front-facing photo.")
        
        if len(faces) > 1:
            raise FaceValidationError("Multiple faces detected. Please upload an image with only one face.")
        
        # Get the detected face
        x, y, w, h = faces[0]
        
        # Validate face size (should be reasonable portion of image)
        image_area = image.size[0] * image.size[1]
        face_area = w * h
        face_ratio = face_area / image_area
        
        if face_ratio < 0.05:  # Face too small
            raise FaceValidationError("Face is too small in the image. Please use a closer photo.")
        
        if face_ratio > 0.8:  # Face too large (likely cropped)
            raise FaceValidationError("Face takes up too much of the image. Please use a photo with more context.")
        
        # Check if face is roughly centered and front-facing
        face_center_x = x + w // 2
        face_center_y = y + h // 2
        image_center_x = image.size[0] // 2
        image_center_y = image.size[1] // 2
        
        # Allow some deviation from center
        center_deviation_x = abs(face_center_x - image_center_x) / image.size[0]
        center_deviation_y = abs(face_center_y - image_center_y) / image.size[1]
        
        if center_deviation_x > 0.3 or center_deviation_y > 0.3:
            raise FaceValidationError("Face should be centered in the image for best results.")
        
        return {
            "face_box": (x, y, w, h),
            "face_ratio": face_ratio,
            "center_deviation": (center_deviation_x, center_deviation_y),
            "quality_score": 1.0 - (center_deviation_x + center_deviation_y)  # Simple quality metric
        }
    
    @classmethod
    def save_image_securely(cls, image: Image.Image, user_id: str) -> str:
        """
        Save image to secure storage location.
        
        Args:
            image: PIL Image to save
            user_id: User ID for organizing storage
            
        Returns:
            Relative path to saved image
        """
        # Create upload directory if it doesn't exist
        upload_dir = Path(settings.UPLOAD_DIR) / "faces" / str(user_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.jpg"
        file_path = upload_dir / filename
        
        # Save image as JPEG with high quality
        image.save(file_path, "JPEG", quality=95, optimize=True)
        
        # Return relative path for database storage
        return str(file_path.relative_to(Path(settings.UPLOAD_DIR)))
    
    @classmethod
    def can_upload_face(cls, db: Session, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if user can upload a new face based on plan limits.
        Returns (can_upload, restriction_message).
        """
        return PlanService.can_upload_face(db, user_id)
    
    @classmethod
    def get_user_active_face(cls, db: Session, user_id: str) -> Optional[Face]:
        """
        Get user's currently active face.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Active Face object or None
        """
        return db.query(Face).filter(
            Face.user_id == user_id,
            Face.is_active == True
        ).first()
    
    @classmethod
    def deactivate_user_faces(cls, db: Session, user_id: str) -> None:
        """
        Deactivate all faces for a user.
        
        Args:
            db: Database session
            user_id: User ID
        """
        db.query(Face).filter(Face.user_id == user_id).update({"is_active": False})
        db.commit()
    
    @classmethod
    def get_cached_embedding(cls, face_id: str) -> Optional[np.ndarray]:
        """
        Get cached face embedding from Redis.
        
        Args:
            face_id: Face ID to look up
            
        Returns:
            Face embedding if cached, None otherwise
        """
        try:
            from app.core.redis import redis_client
            
            cache_key = f"face_embedding:{face_id}"
            cached_data = redis_client.get(cache_key)
            
            if cached_data:
                # Deserialize the embedding
                embedding = pickle.loads(cached_data)
                return embedding
                
        except Exception:
            # If caching fails, continue without cache
            pass
        
        return None
    
    @classmethod
    def cache_embedding(cls, face_id: str, embedding: np.ndarray, ttl: int = 3600) -> None:
        """
        Cache face embedding in Redis.
        
        Args:
            face_id: Face ID for cache key
            embedding: Face embedding to cache
            ttl: Time to live in seconds (default 1 hour)
        """
        try:
            from app.core.redis import redis_client
            
            cache_key = f"face_embedding:{face_id}"
            embedding_bytes = pickle.dumps(embedding)
            
            redis_client.setex(cache_key, ttl, embedding_bytes)
            
        except Exception:
            # If caching fails, continue without cache
            pass
    
    @classmethod
    def invalidate_embedding_cache(cls, face_id: str) -> None:
        """
        Invalidate cached face embedding.
        
        Args:
            face_id: Face ID to invalidate
        """
        try:
            from app.core.redis import redis_client
            
            cache_key = f"face_embedding:{face_id}"
            redis_client.delete(cache_key)
            
        except Exception:
            # If cache invalidation fails, continue
            pass
    
    @classmethod
    def get_face_embedding(cls, db: Session, face_id: str) -> Optional[np.ndarray]:
        """
        Get face embedding with caching support.
        
        Args:
            db: Database session
            face_id: Face ID
            
        Returns:
            Face embedding or None if not found
        """
        # Try cache first
        cached_embedding = cls.get_cached_embedding(face_id)
        if cached_embedding is not None:
            return cached_embedding
        
        # Get from database
        face = db.query(Face).filter(Face.id == face_id).first()
        if not face or not face.embedding_data:
            return None
        
        # Decrypt embedding
        embedding = cls._decrypt_embedding(face.embedding_data)
        
        # Cache for future use
        cls.cache_embedding(face_id, embedding)
        
        return embedding
    
    @classmethod
    def delete_face_file(cls, image_path: str) -> None:
        """
        Delete face image file from storage.
        
        Args:
            image_path: Relative path to image file
        """
        try:
            full_path = Path(settings.UPLOAD_DIR) / image_path
            if full_path.exists():
                full_path.unlink()
        except Exception:
            # Log error but don't fail - file might already be deleted
            pass