import json
from typing import Optional

from app.models import User
from app.repositories.generic_repository import GenericRepository, deserialize_instance
from app.utils.cache_util import cache
from app.utils.cache_util_model import CacheModel
from app.utils.logger import get_logger
# Import the SQLAlchemy session factory
from app.config.database import SessionLocal

logger = get_logger(__name__)


class UserRepository(GenericRepository):
    def __init__(self) -> None:
        # Note: If your GenericRepository now requires a session argument in its constructor,
        # you may either pass a session or override methods that create their own sessions.
        # Here we pass None because find_user_by_username creates its own session.
        super().__init__(User, None)

    def find_user_by_username(
        self, username: str, cache_model: Optional[CacheModel] = None
    ) -> Optional[User]:
        session = SessionLocal()
        try:
            # Try retrieving from cache first
            if cache_model:
                cache_entity = cache.get(cache_model.key)
                if cache_entity:
                    data = json.loads(cache_entity)
                    return deserialize_instance(self.model, data)
            # Query the database for the user by username
            user = session.query(self.model).filter(
                self.model.username == username
            ).first()
            if not user:
                logger.warning(
                    f"[UserRepository] No user found with username: {username}"
                )
                raise Exception(f"User with username {username} not found")
            # Cache the user if needed
            if cache_model:
                # You can use your own serialization helper here (e.g. model_to_dict)
                data = json.dumps(self._to_dict(user), default=str)
                cache.set(cache_model.key, data,
                          timeout=cache_model.expiration)
            return user
        except Exception:
            logger.error(
                "[UserRepository] Error finding user by username:",
                exc_info=True
            )
            return None
        finally:
            session.close()

    def _to_dict(self, instance: User) -> dict:
        """
        Convert a User instance to a dict.
        If you already have a helper function (e.g. model_to_dict) defined in GenericRepository,
        you can import and use it here instead.
        """
        # Here we assume your User model has attributes 'id', 'username', and 'email'
        return {
            "id": instance.id,
            "username": instance.username,
            "email": instance.email,
        }
