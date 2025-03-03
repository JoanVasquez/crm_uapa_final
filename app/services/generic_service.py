"""Generic service module.

This module provides a GenericService class that implements common CRUD operations
by delegating to a GenericRepository. It also supports pagination and error handling.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from app.errors import BaseAppException
from app.repositories.generic_repository import GenericRepository
from app.services.crud_methods import ICRUD
from app.utils.cache_util_model import CacheModel
from app.utils.logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


class GenericService(ICRUD[T], Generic[T]):
    """
    A generic service that provides CRUD operations for a given model.

    It delegates calls to the underlying GenericRepository and handles errors.
    """

    def __init__(self, generic_repository: GenericRepository) -> None:
        """
        Initialize the service with a given generic repository.

        Args:
            generic_repository (GenericRepository): The repository instance.
        """
        self.generic_repository = generic_repository

    def save(self, entity: T, cache_model: Optional[CacheModel] = None) -> Optional[T]:
        """
        Save an entity using the underlying repository.

        Args:
            entity (T): The entity to save.
            cache_model (Optional[CacheModel]): Optional cache configuration.

        Returns:
            Optional[T]: The saved entity.

        Raises:
            BaseAppException: If an error occurs during saving.
        """
        try:
            logger.info("[GenericService] Saving entity: %s", entity)
            return self.generic_repository.create_entity(entity, cache_model)
        except Exception as error:
            logger.error(
                "[GenericService] Error saving entity: %s", error, exc_info=True
            )
            raise BaseAppException("Error saving entity", details=str(error)) from error

    def find_by_id(
        self, entity_id: int, cache_model: Optional[CacheModel] = None
    ) -> Optional[T]:
        """
        Find an entity by its ID.

        Args:
            entity_id (int): The ID of the entity.
            cache_model (Optional[CacheModel]): Optional cache configuration.

        Returns:
            Optional[T]: The found entity.

        Raises:
            BaseAppException: If an error occurs during the lookup.
        """
        try:
            logger.info("[GenericService] Finding entity by ID: %s", entity_id)
            return self.generic_repository.find_entity_by_id(entity_id, cache_model)
        except Exception as error:
            logger.error(
                "[GenericService] Error finding entity by ID %s: %s",
                entity_id,
                error,
                exc_info=True,
            )
            raise BaseAppException(
                "Error finding entity by ID", details=str(error)
            ) from error

    def update(
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
            cache_model (Optional[CacheModel]): Optional cache configuration.

        Returns:
            Optional[T]: The updated entity.

        Raises:
            BaseAppException: If an error occurs during the update.
        """
        try:
            logger.info(
                "[GenericService] Updating entity with ID: %s with data: %s",
                entity_id,
                updated_data,
            )
            return self.generic_repository.update_entity(
                entity_id, updated_data, cache_model
            )
        except Exception as error:
            logger.error(
                "[GenericService] Error updating entity with ID %s: %s",
                entity_id,
                error,
                exc_info=True,
            )
            raise BaseAppException(
                "Error updating entity", details=str(error)
            ) from error

    def delete(self, entity_id: int, cache_model: Optional[CacheModel] = None) -> bool:
        """
        Delete an entity by its ID.

        Args:
            entity_id (int): The ID of the entity to delete.
            cache_model (Optional[CacheModel]): Optional cache configuration.

        Returns:
            bool: True if the entity was successfully deleted.

        Raises:
            BaseAppException: If an error occurs during deletion.
        """
        try:
            logger.info("[GenericService] Deleting entity with ID: %s", entity_id)
            return self.generic_repository.delete_entity(entity_id, cache_model)
        except Exception as error:
            logger.error(
                "[GenericService] Error deleting entity with ID %s: %s",
                entity_id,
                error,
                exc_info=True,
            )
            raise BaseAppException(
                "Error deleting entity", details=str(error)
            ) from error

    def find_all(self, cache_model: Optional[CacheModel] = None) -> List[T]:
        """
        Retrieve all entities.

        Args:
            cache_model (Optional[CacheModel]): Optional cache configuration.

        Returns:
            List[T]: A list of all entities.

        Raises:
            BaseAppException: If an error occurs during retrieval.
        """
        try:
            logger.info("[GenericService] Finding all entities")
            return self.generic_repository.get_all_entities(cache_model)
        except Exception as error:
            logger.error(
                "[GenericService] Error retrieving all entities: %s",
                error,
                exc_info=True,
            )
            raise BaseAppException(
                "Error retrieving all entities", details=str(error)
            ) from error

    def find_with_pagination(
        self, skip: int, take: int, cache_model: Optional[CacheModel] = None
    ) -> Dict[str, Any]:
        """
        Retrieve entities with pagination.

        Args:
            skip (int): The number of records to skip.
            take (int): The number of records to return.
            cache_model (Optional[CacheModel]): Optional cache configuration.

        Returns:
            Dict[str, Any]: A dictionary with paginated data and the total count.

        Raises:
            BaseAppException: If an error occurs during retrieval.
        """
        try:
            logger.info(
                "[GenericService] Finding entities with pagination: skip=%s, take=%s",
                skip,
                take,
            )
            return self.generic_repository.get_entities_with_pagination(
                skip, take, cache_model
            )
        except Exception as error:
            logger.error(
                "[GenericService] Error retrieving entities with pagination: %s",
                error,
                exc_info=True,
            )
            raise BaseAppException(
                "Error retrieving entities with pagination", details=str(error)
            ) from error
