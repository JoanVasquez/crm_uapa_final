"""
Generic repository module.

This module defines a generic repository for SQLAlchemy models. It provides common CRUD operations,
pagination, and caching support. Concrete repositories should inherit from GenericRepository.
"""

import json
from abc import ABC
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from app.errors import BaseAppException, ResourceNotFoundError
from app.utils.cache_util import cache
from app.utils.cache_util_model import CacheModel
from app.utils.deserialize_instance import deserialize_instance
from app.utils.logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


def model_to_dict(instance: Any) -> Dict[str, Any]:
    """
    Convert an SQLAlchemy model instance to a dictionary by iterating over its columns.

    Args:
        instance (Any): The SQLAlchemy model instance.

    Returns:
        Dict[str, Any]: A dictionary representation of the instance.
    """
    return {
        column.name: getattr(instance, column.name)
        for column in instance.__table__.columns
    }


class GenericRepository(ABC):
    """
    A generic repository for SQLAlchemy models.

    Provides common CRUD operations, including create, read, update, delete, and pagination.
    """

    def __init__(self, model: Type[T], session: Session) -> None:
        """
        Initialize the repository with the model and a SQLAlchemy session.

        Args:
            model (Type[T]): The SQLAlchemy model class.
            session (Session): The SQLAlchemy session.
        """
        self.model = model
        self.session = session

    def create_entity(
        self, entity: T, cache_model: Optional[CacheModel] = None
    ) -> Optional[T]:
        """
        Create a new entity in the database and optionally cache it.

        Args:
            entity (T): The entity to create.
            cache_model (Optional[CacheModel]): Cache configuration for the entity.

        Returns:
            Optional[T]: The created entity.

        Raises:
            BaseAppException: If an error occurs during creation.
        """
        try:
            self.session.add(entity)
            self.session.commit()
            if cache_model:
                data = json.dumps(model_to_dict(entity))
                cache.set(cache_model.key, data, timeout=cache_model.expiration)
            return entity
        except Exception as error:
            self.session.rollback()
            logger.error(
                "[GenericRepository] Error creating entity: %s", error, exc_info=True
            )
            if isinstance(error, BaseAppException):
                raise error
            raise BaseAppException(
                "Error creating entity", details=str(error)
            ) from error

    def find_entity_by_id(
        self, entity_id: int, cache_model: Optional[CacheModel] = None
    ) -> Optional[T]:
        """
        Find an entity by its ID, using cache if available.

        Args:
            entity_id (int): The ID of the entity to retrieve.
            cache_model (Optional[CacheModel]): Cache configuration for the entity.

        Returns:
            Optional[T]: The found entity.

        Raises:
            ResourceNotFoundError: If no entity is found with the given ID.
            BaseAppException: If an error occurs during retrieval.
        """
        try:
            if cache_model:
                cached = cache.get(cache_model.key)
                if cached:
                    data = json.loads(cached)
                    return deserialize_instance(self.model, data)
            entity = self.session.get(self.model, entity_id)
            if not entity:
                logger.info(f"[GenericRepository] Entity with id {entity_id} not found")
                raise ResourceNotFoundError(f"Entity with id {entity_id} not found")
            if cache_model:
                data = json.dumps(model_to_dict(entity))
                cache.set(cache_model.key, data, timeout=cache_model.expiration)
            return entity
        except Exception as error:
            logger.error(
                "[GenericRepository] Error finding entity: %s", error, exc_info=True
            )
            if isinstance(error, BaseAppException):
                raise error
            raise BaseAppException(
                "Error finding entity", details=str(error)
            ) from error

    def update_entity(
        self,
        entity_id: int,
        updated_data: Dict[str, Any],
        cache_model: Optional[CacheModel] = None,
    ) -> Optional[T]:
        """
        Update an entity with the given data.

        Args:
            entity_id (int): The ID of the entity to update.
            updated_data (Dict[str, Any]): A dictionary of updated values.
            cache_model (Optional[CacheModel]): Cache configuration for the entity.

        Returns:
            Optional[T]: The updated entity.

        Raises:
            ResourceNotFoundError: If no entity is found for update.
            BaseAppException: If an error occurs during update.
        """
        try:
            query = self.session.query(self.model).filter_by(id=entity_id)
            updated_count = query.update(updated_data)
            if updated_count == 0:
                logger.error(
                    f"[GenericRepository] Entity with id {entity_id} not found for update"
                )
                raise ResourceNotFoundError(f"Entity with id {entity_id} not found")
            self.session.commit()
            updated_entity = self.find_entity_by_id(entity_id)
            if not updated_entity:
                logger.error(
                    f"[GenericRepository] Updated entity with id {entity_id} not found"
                )
                raise ResourceNotFoundError(f"Entity with id {entity_id} not found")
            if cache_model:
                data = json.dumps(model_to_dict(updated_entity))
                cache.set(cache_model.key, data, timeout=cache_model.expiration)
            return updated_entity
        except Exception as error:
            self.session.rollback()
            logger.error(
                "[GenericRepository] Error updating entity: %s", error, exc_info=True
            )
            if isinstance(error, BaseAppException):
                raise error
            raise BaseAppException(
                "Error updating entity", details=str(error)
            ) from error

    def delete_entity(
        self, entity_id: int, cache_model: Optional[CacheModel] = None
    ) -> bool:
        """
        Delete an entity by its ID.

        Args:
            entity_id (int): The ID of the entity to delete.
            cache_model (Optional[CacheModel]): Cache configuration to delete associated cache.

        Returns:
            bool: True if the deletion was successful.

        Raises:
            ResourceNotFoundError: If the entity is not found.
            BaseAppException: If an error occurs during deletion.
        """
        try:
            query = self.session.query(self.model).filter_by(id=entity_id)
            deleted_count = query.delete()
            if deleted_count == 0:
                logger.error(
                    f"[GenericRepository] Failed to delete entity with id {entity_id}"
                )
                raise ResourceNotFoundError(f"Entity with id {entity_id} not found")
            self.session.commit()
            if cache_model:
                cache.delete(cache_model.key)
            return True
        except Exception as error:
            self.session.rollback()
            logger.error(
                "[GenericRepository] Error deleting entity: %s", error, exc_info=True
            )
            if isinstance(error, BaseAppException):
                raise error
            raise BaseAppException(
                "Error deleting entity", details=str(error)
            ) from error

    def get_all_entities(self, cache_model: Optional[CacheModel] = None) -> List[T]:
        """
        Retrieve all entities from the database, optionally using cache.

        Args:
            cache_model (Optional[CacheModel]): Cache configuration for the query.

        Returns:
            List[T]: A list of all entities.

        Raises:
            BaseAppException: If an error occurs during retrieval.
        """
        try:
            if cache_model:
                cached = cache.get(cache_model.key)
                if cached:
                    data_list = json.loads(cached)
                    return [
                        deserialize_instance(self.model, data) for data in data_list
                    ]
            entities = self.session.query(self.model).all()
            if cache_model:
                data_list = [model_to_dict(e) for e in entities]
                cache.set(
                    cache_model.key,
                    json.dumps(data_list),
                    timeout=cache_model.expiration,
                )
            return entities
        except Exception as error:
            logger.error(
                "[GenericRepository] Error retrieving all entities: %s",
                error,
                exc_info=True,
            )
            if isinstance(error, BaseAppException):
                raise error
            raise BaseAppException(
                "Error retrieving all entities", details=str(error)
            ) from error

    def get_entities_with_pagination(
        self, skip: int, take: int, cache_model: Optional[CacheModel] = None
    ) -> Dict[str, Any]:
        """
        Retrieve entities with pagination.

        Args:
            skip (int): Number of records to skip.
            take (int): Number of records to take.
            cache_model (Optional[CacheModel]): Cache configuration for the query.

        Returns:
            Dict[str, Any]: A dictionary containing the list of entities and the total count.

        Raises:
            BaseAppException: If an error occurs during pagination.
        """
        try:
            if cache_model:
                cached = cache.get(cache_model.key)
                if cached:
                    return json.loads(cached)
            query = self.session.query(self.model)
            count = query.count()
            data = query.offset(skip).limit(take).all()
            result = {"data": data, "count": count}
            if cache_model:
                serializable_data = [model_to_dict(e) for e in data]
                cache_data = json.dumps({"data": serializable_data, "count": count})
                cache.set(cache_model.key, cache_data, timeout=cache_model.expiration)
            return result
        except Exception as error:
            logger.error(
                "[GenericRepository] Error in pagination: %s", error, exc_info=True
            )
            if isinstance(error, BaseAppException):
                raise error
            raise BaseAppException("Error in pagination", details=str(error)) from error
