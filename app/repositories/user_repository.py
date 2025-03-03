"""
Repository for user-related operations.

This module implements a repository for performing operations on the User model,
including looking up users by username. It leverages caching when a CacheModel is provided.
"""

import json
from typing import Optional

from app.config.database import SessionLocal
from app.errors import BaseAppException, ResourceNotFoundError
from app.models import User
from app.repositories.generic_repository import GenericRepository, deserialize_instance
from app.utils.cache_util import cache
from app.utils.cache_util_model import CacheModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserRepository(GenericRepository):
    """Repository for performing operations related to the User model.

    Inherits from GenericRepository.
    """

    def __init__(self) -> None:
        """
        Initialize a new UserRepository instance.

        Note:
            Passes None for the session because find_user_by_username creates its own session.
        """
        super().__init__(User, None)

    def find_user_by_username(
        self, username: str, cache_model: Optional[CacheModel] = None
    ) -> Optional[User]:
        """
        Find a user by their username.

        This method first attempts to retrieve the user from cache if a cache model is provided.
        If the user is not found in the cache, it queries the database. The result is then cached if needed.

        Args:
            username (str): The username to search for.
            cache_model (Optional[CacheModel]): An optional cache model for caching the lookup result.

        Returns:
            Optional[User]: The found User instance.

        Raises:
            ResourceNotFoundError: If no user is found.
            BaseAppException: If any other error occurs during the lookup.
        """
        session = SessionLocal()
        try:
            # Attempt to retrieve the user from cache.
            if cache_model:
                cache_entity = cache.get(cache_model.key)
                if cache_entity:
                    data = json.loads(cache_entity)
                    return deserialize_instance(self.model, data)
            # Query the database for the user by username.
            user = (
                session.query(self.model)
                .filter(self.model.username == username)
                .first()
            )
            if not user:
                logger.warning(
                    f"[UserRepository] No user found with username: {username}"
                )
                raise ResourceNotFoundError(f"User with username {username} not found")
            # Cache the user if a cache model is provided.
            if cache_model:
                data = json.dumps(self._to_dict(user), default=str)
                cache.set(cache_model.key, data, timeout=cache_model.expiration)
            return user
        except Exception as error:
            logger.error(
                "[UserRepository] Error finding user by username: %s",
                username,
                exc_info=True,
            )
            if isinstance(error, BaseAppException):
                raise error
            raise BaseAppException(
                "Error finding user by username", details=str(error)
            ) from error
        finally:
            session.close()

    def _to_dict(self, instance: User) -> dict:
        """
        Convert a User instance to a dictionary.

        Assumes the User model has attributes 'id', 'username', and 'email'.

        Args:
            instance (User): The User instance to convert.

        Returns:
            dict: A dictionary representation of the user.
        """
        return {
            "id": instance.id,
            "username": instance.username,
            "email": instance.email,
        }
