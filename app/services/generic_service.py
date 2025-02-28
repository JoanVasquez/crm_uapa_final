from typing import Any, Dict, Generic, List, Optional, TypeVar

from app.repositories.generic_repository import GenericRepository
from app.services.crud_methods import ICRUD
from app.utils.cache_util_model import CacheModel
from app.utils.logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


class GenericService(ICRUD[T], Generic[T]):

    def __init__(self, generic_repository: GenericRepository) -> None:
        self.generic_repository = generic_repository

    def save(self,
             entity: T,
             cache_model: Optional[CacheModel] = None) -> Optional[T]:
        logger.info(f"[GenericService] Saving entity: {entity}")
        return self.generic_repository.create_entity(entity, cache_model)

    def find_by_id(self,
                   id: int,
                   cache_model: Optional[CacheModel] = None) -> Optional[T]:
        logger.info(f"[GenericService] Finding entity by ID: {id}")
        return self.generic_repository.find_entity_by_id(id, cache_model)

    def update(
        self,
        id: int,
        updated_data: Dict[str, Any],
        cache_model: Optional[CacheModel] = None,
    ) -> Optional[T]:
        logger.info(
            f"[GenericService] Updating entity with ID: {id} with data: "
            f"{updated_data}")
        return self.generic_repository.update_entity(id, updated_data,
                                                     cache_model)

    def delete(self,
               id: int,
               cache_model: Optional[CacheModel] = None) -> bool:
        logger.info(f"[GenericService] Deleting entity with ID: {id}")
        return self.generic_repository.delete_entity(id, cache_model)

    def find_all(self, cache_model: Optional[CacheModel] = None) -> List[T]:
        logger.info("[GenericService] Finding all entities")
        return self.generic_repository.get_all_entities(cache_model)

    def find_with_pagination(
            self,
            skip: int,
            take: int,
            cache_model: Optional[CacheModel] = None) -> Dict[str, Any]:
        logger.info(
            f"[GenericService] Finding entities with pagination: skip={skip}, "
            f"take={take}")
        return self.generic_repository.get_entities_with_pagination(
            skip, take, cache_model)
