import json
from abc import ABC
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from app.utils.cache_util import cache
from app.utils.cache_util_model import CacheModel
from app.utils.logger import get_logger
from app.utils.deserialize_instance import deserialize_instance

logger = get_logger(__name__)

T = TypeVar("T")


def model_to_dict(instance: Any) -> Dict[str, Any]:
    """
    Convert an SQLAlchemy model instance to a dictionary by iterating over its columns.
    """
    return {
        column.name: getattr(instance, column.name)
        for column in instance.__table__.columns
    }


class GenericRepository(ABC):
    """
    A generic repository for SQLAlchemy models.
    Concrete repositories should inherit from this class.
    """

    def __init__(self, model: Type[T], session: Session) -> None:
        self.model = model
        self.session = session

    def create_entity(
        self,
        entity: T,
        cache_model: Optional[CacheModel] = None
    ) -> Optional[T]:
        try:
            self.session.add(entity)
            self.session.commit()

            if cache_model:
                data = json.dumps(model_to_dict(entity))
                cache.set(cache_model.key, data,
                          timeout=cache_model.expiration)
            return entity
        except Exception as error:
            self.session.rollback()
            logger.error("[GenericRepository] Error creating entity: %s",
                         error, exc_info=True)
            return None

    def find_entity_by_id(
        self,
        id: int,
        cache_model: Optional[CacheModel] = None
    ) -> Optional[T]:
        try:
            if cache_model:
                cached = cache.get(cache_model.key)
                if cached:
                    data = json.loads(cached)
                    return deserialize_instance(self.model, data)
            # Using Session.get() if available, or fallback to query/filter_by.
            entity = self.session.get(self.model, id)
            if not entity:
                logger.info(
                    "[GenericRepository] Entity with id %s not found", id)
                raise Exception("Entity not found")
            if cache_model:
                data = json.dumps(model_to_dict(entity))
                cache.set(cache_model.key, data,
                          timeout=cache_model.expiration)
            return entity
        except Exception as error:
            logger.error("[GenericRepository] Error finding entity: %s",
                         error, exc_info=True)
            return None

    def update_entity(
        self,
        id: int,
        updated_data: Dict[str, Any],
        cache_model: Optional[CacheModel] = None,
    ) -> Optional[T]:
        try:
            # Update directly via query
            query = self.session.query(self.model).filter_by(id=id)
            updated_count = query.update(updated_data)
            if updated_count == 0:
                logger.error(
                    "[GenericRepository] Entity with id %s not found for update", id)
                raise Exception(f"Entity with id {id} not found")
            self.session.commit()

            updated_entity = self.find_entity_by_id(id)
            if not updated_entity:
                logger.error(
                    "[GenericRepository] Updated entity with id %s not found", id)
                raise Exception(f"Entity with id {id} not found")
            if cache_model:
                data = json.dumps(model_to_dict(updated_entity))
                cache.set(cache_model.key, data,
                          timeout=cache_model.expiration)
            return updated_entity
        except Exception as error:
            self.session.rollback()
            logger.error("[GenericRepository] Error updating entity: %s",
                         error, exc_info=True)
            return None

    def delete_entity(
        self,
        id: int,
        cache_model: Optional[CacheModel] = None
    ) -> bool:
        try:
            query = self.session.query(self.model).filter_by(id=id)
            deleted_count = query.delete()
            if deleted_count == 0:
                logger.error(
                    "[GenericRepository] Failed to delete entity with id %s", id)
                raise Exception(f"Entity with id {id} not found")
            self.session.commit()
            if cache_model:
                cache.delete(cache_model.key)
            return True
        except Exception as error:
            self.session.rollback()
            logger.error("[GenericRepository] Error deleting entity: %s",
                         error, exc_info=True)
            return False

    def get_all_entities(
        self,
        cache_model: Optional[CacheModel] = None
    ) -> List[T]:
        try:
            if cache_model:
                cached = cache.get(cache_model.key)
                if cached:
                    data_list = json.loads(cached)
                    return [
                        deserialize_instance(self.model, data)
                        for data in data_list
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
                error, exc_info=True,
            )
            return []

    def get_entities_with_pagination(
        self,
        skip: int,
        take: int,
        cache_model: Optional[CacheModel] = None
    ) -> Dict[str, Any]:
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
                cache_data = json.dumps({
                    "data": serializable_data,
                    "count": count
                })
                cache.set(cache_model.key, cache_data,
                          timeout=cache_model.expiration)
            return result
        except Exception as error:
            logger.error("[GenericRepository] Error in pagination: %s",
                         error, exc_info=True)
            return {"data": [], "count": 0}
