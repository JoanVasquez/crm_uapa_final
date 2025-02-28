import json
from typing import Optional

from app.models import User
from app.repositories.generic_repository import GenericRepository, deserialize_instance
from app.utils.cache_util import cache
from app.utils.cache_util_model import CacheModel
from app.utils.logger import get_logger
from app.config.database import SessionLocal
from app.errors import BaseAppException, ResourceNotFoundError

logger = get_logger(__name__)


class UserRepository(GenericRepository):
    def __init__(self) -> None:
        # Here we pass None for the session because find_user_by_username creates its own session.
        super().__init__(User, None)

    def find_user_by_username(
        self, username: str, cache_model: Optional[CacheModel] = None
    ) -> Optional[User]:
        session = SessionLocal()
        try:
            # Try retrieving from cache first.
            if cache_model:
                cache_entity = cache.get(cache_model.key)
                if cache_entity:
                    data = json.loads(cache_entity)
                    return deserialize_instance(self.model, data)
            # Query the database for the user by username.
            user = session.query(self.model).filter(
                self.model.username == username
            ).first()
            if not user:
                logger.warning(
                    f"[UserRepository] No user found with username: {username}")
                raise ResourceNotFoundError(
                    f"User with username {username} not found")
            # Cache the user if needed.
            if cache_model:
                data = json.dumps(self._to_dict(user), default=str)
                cache.set(cache_model.key, data,
                          timeout=cache_model.expiration)
            return user
        except Exception as error:
            logger.error(
                "[UserRepository] Error finding user by username:", exc_info=True)
            if isinstance(error, BaseAppException):
                raise error
            raise BaseAppException(
                "Error finding user by username", details=str(error)) from error
        finally:
            session.close()

    def _to_dict(self, instance: User) -> dict:
        """
        Convert a User instance to a dict.
        Assumes the User model has attributes 'id', 'username', and 'email'.
        """
        return {
            "id": instance.id,
            "username": instance.username,
            "email": instance.email,
        }
