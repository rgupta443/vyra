"""
Database query optimization utilities.

This module provides utilities for optimizing database queries including:
- Eager loading strategies
- Query result caching
- Batch operations
- Index usage optimization

Validates Requirements: System performance
"""
import logging
from typing import List, Optional, Type, TypeVar
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_

from app.models.user import User
from app.models.face import Face
from app.models.generation import Generation
from app.models.preset import PresetConfig

logger = logging.getLogger(__name__)

T = TypeVar('T')


class QueryOptimizer:
    """Utilities for optimizing database queries."""
    
    @staticmethod
    def get_user_with_face(db: Session, user_id: str) -> Optional[User]:
        """
        Get user with their active face in a single query.
        
        Uses eager loading to avoid N+1 query problem.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User with face loaded, or None
        """
        return (
            db.query(User)
            .options(joinedload(User.faces))
            .filter(User.id == user_id)
            .first()
        )
    
    @staticmethod
    def get_generations_with_relations(
        db: Session,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Generation]:
        """
        Get user's generations with all related data in optimized queries.
        
        Uses select-in loading for better performance with multiple records.
        
        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of records
            offset: Offset for pagination
            
        Returns:
            List of generations with relations loaded
        """
        return (
            db.query(Generation)
            .options(
                selectinload(Generation.user),
                selectinload(Generation.face)
            )
            .filter(Generation.user_id == user_id)
            .order_by(Generation.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    @staticmethod
    def get_active_presets(db: Session) -> List[PresetConfig]:
        """
        Get all active presets with optimized query.
        
        Args:
            db: Database session
            
        Returns:
            List of active presets
        """
        return (
            db.query(PresetConfig)
            .filter(PresetConfig.is_active == True)
            .all()
        )
    
    @staticmethod
    def batch_get_by_ids(
        db: Session,
        model: Type[T],
        ids: List[str]
    ) -> List[T]:
        """
        Get multiple records by IDs in a single query.
        
        More efficient than multiple individual queries.
        
        Args:
            db: Database session
            model: SQLAlchemy model class
            ids: List of IDs to fetch
            
        Returns:
            List of model instances
        """
        if not ids:
            return []
        
        return db.query(model).filter(model.id.in_(ids)).all()
    
    @staticmethod
    def count_user_generations(db: Session, user_id: str) -> int:
        """
        Count user's generations efficiently.
        
        Uses COUNT query instead of loading all records.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Count of generations
        """
        return (
            db.query(Generation)
            .filter(Generation.user_id == user_id)
            .count()
        )
    
    @staticmethod
    def get_recent_completed_generations(
        db: Session,
        user_id: str,
        limit: int = 10
    ) -> List[Generation]:
        """
        Get user's recent completed generations.
        
        Optimized query with index usage on status and created_at.
        
        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of records
            
        Returns:
            List of completed generations
        """
        from app.models.generation import GenerationStatus
        
        return (
            db.query(Generation)
            .filter(
                and_(
                    Generation.user_id == user_id,
                    Generation.status == GenerationStatus.COMPLETED
                )
            )
            .order_by(Generation.created_at.desc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def exists(db: Session, model: Type[T], **filters) -> bool:
        """
        Check if a record exists without loading it.
        
        More efficient than querying and checking for None.
        
        Args:
            db: Database session
            model: SQLAlchemy model class
            **filters: Filter conditions
            
        Returns:
            True if record exists, False otherwise
        """
        query = db.query(model)
        for key, value in filters.items():
            query = query.filter(getattr(model, key) == value)
        
        return db.query(query.exists()).scalar()


class BatchOperations:
    """Utilities for batch database operations."""
    
    @staticmethod
    def bulk_insert(db: Session, model: Type[T], records: List[dict]) -> int:
        """
        Bulk insert records efficiently.
        
        Args:
            db: Database session
            model: SQLAlchemy model class
            records: List of record dictionaries
            
        Returns:
            Number of records inserted
        """
        if not records:
            return 0
        
        try:
            db.bulk_insert_mappings(model, records)
            db.commit()
            return len(records)
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            db.rollback()
            return 0
    
    @staticmethod
    def bulk_update(db: Session, model: Type[T], records: List[dict]) -> int:
        """
        Bulk update records efficiently.
        
        Args:
            db: Database session
            model: SQLAlchemy model class
            records: List of record dictionaries with IDs
            
        Returns:
            Number of records updated
        """
        if not records:
            return 0
        
        try:
            db.bulk_update_mappings(model, records)
            db.commit()
            return len(records)
        except Exception as e:
            logger.error(f"Bulk update failed: {e}")
            db.rollback()
            return 0


class IndexHints:
    """
    Documentation of database indexes for query optimization.
    
    This class documents the indexes that should exist on tables
    for optimal query performance.
    """
    
    # User table indexes
    USER_INDEXES = [
        "idx_user_email",  # For login queries
        "idx_user_google_id",  # For OAuth queries
    ]
    
    # Face table indexes
    FACE_INDEXES = [
        "idx_face_user_id",  # For user face queries
        "idx_face_user_id_active",  # For active face queries
    ]
    
    # Generation table indexes
    GENERATION_INDEXES = [
        "idx_generation_user_id",  # For user generation queries
        "idx_generation_status",  # For status filtering
        "idx_generation_user_id_status",  # Composite for user + status
        "idx_generation_created_at",  # For ordering by date
        "idx_generation_user_id_created_at",  # Composite for user + date
    ]
    
    # Preset table indexes
    PRESET_INDEXES = [
        "idx_preset_name",  # For preset lookup
        "idx_preset_is_active",  # For active preset queries
    ]
    
    @staticmethod
    def get_recommended_indexes() -> dict:
        """
        Get recommended indexes for all tables.
        
        Returns:
            Dict mapping table names to index lists
        """
        return {
            "users": IndexHints.USER_INDEXES,
            "faces": IndexHints.FACE_INDEXES,
            "generations": IndexHints.GENERATION_INDEXES,
            "preset_configs": IndexHints.PRESET_INDEXES,
        }
