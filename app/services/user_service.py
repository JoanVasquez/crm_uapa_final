"""User service module.

This module implements the UserService class, which provides asynchronous methods
for registering users, confirming registration, authentication, and password resets.
It leverages the underlying UserRepository, AuthenticationService, and PasswordService.
"""

import json
from typing import Any, Dict, Optional

from app.errors import BaseAppException, ResourceNotFoundError
from app.models import User
from app.repositories.user_repository import UserRepository
from app.services.authentication_service import AuthenticationService
from app.services.generic_service import GenericService
from app.services.password_service import PasswordService
from app.utils.cache_util import cache
from app.utils.cache_util_model import CacheModel
from app.utils.deserialize_instance import deserialize_instance
from app.utils.logger import get_logger
from app.utils.reset_password_input_validator import reset_password_input_validator

logger = get_logger(__name__)


class UserService(GenericService[User]):
    """
    Service for handling user operations including registration, authentication,
    and password reset. This class uses asynchronous methods for I/O-bound operations.
    """

    user_repository: UserRepository = UserRepository()

    def __init__(self) -> None:
        """
        Initialize the UserService.

        This sets up the repository, authentication, and password services.
        """
        super().__init__(UserService.user_repository)
        self.auth_service = AuthenticationService()
        self.password_service = PasswordService()

    # pylint: disable=invalid-overridden-method
    async def save(
        self, entity: User, cache_model: Optional[CacheModel] = None
    ) -> Optional[User]:
        """
        Asynchronously register and save a new user.

        This method registers the user via the authentication service, encrypts the password,
        and creates the user in the database using the repository.

        Args:
            entity (User): The user entity containing username, password, and email.
            cache_model (Optional[CacheModel]): Optional cache configuration.

        Returns:
            Optional[User]: The newly created user.

        Raises:
            BaseAppException: If registration fails.
        """
        try:
            logger.info("[UserService] Registering user: %s", entity.username)
            # Register the user via the authentication service.
            await self.auth_service.register_user(
                entity.username, entity.password, entity.email
            )
            # Encrypt the password.
            encrypted_password = self.password_service.get_password_encrypted(
                entity.password
            )
            logger.info("[UserService] Password encrypted.")
            # Create the user in the database using the repository.
            user = self.user_repository.create_entity(
                User(
                    username=entity.username,
                    password=encrypted_password,
                    email=entity.email,
                ),
                cache_model,
            )
            logger.info("[UserService] User created in database: %s", entity.username)
            return user
        except Exception as error:
            logger.error(
                "[UserService] Registration failed for user: %s",
                entity.username,
                exc_info=True,
            )
            raise BaseAppException("Registration failed", details=str(error)) from error

    # pylint: enable=invalid-overridden-method

    async def confirm_registration(
        self, username: str, confirmation_code: str
    ) -> Dict[str, Any]:
        """
        Asynchronously confirm a user's registration.

        Args:
            username (str): The username to confirm.
            confirmation_code (str): The confirmation code.

        Returns:
            Dict[str, Any]: A dictionary containing confirmation response.

        Raises:
            BaseAppException: If user confirmation fails.
        """
        try:
            logger.info("[UserService] Confirming registration for user: %s", username)
            response = await self.auth_service.confirm_user_registration(
                username, confirmation_code
            )
            logger.info("[UserService] User confirmed successfully: %s", username)
            return response
        except Exception as error:
            logger.error(
                "[UserService] Confirmation failed for user: %s",
                username,
                exc_info=True,
            )
            raise BaseAppException(
                "User confirmation failed", details=str(error)
            ) from error

    async def authenticate(self, username: str, password: str) -> Dict[str, str]:
        """
        Asynchronously authenticate a user and retrieve an authentication token.

        This method calls the authentication service to obtain a token and then attempts to
        retrieve and cache the user data.

        Args:
            username (str): The username.
            password (str): The user's password.

        Returns:
            Dict[str, str]: A dictionary with the token.

        Raises:
            BaseAppException: If authentication fails.
        """
        try:
            logger.info("[UserService] Starting authentication for user: %s", username)
            token = await self.auth_service.authenticate_user(username, password)
            cached_user = await cache.get("user:%s" % username)
            if cached_user:
                data = json.loads(cached_user)
                user = deserialize_instance(User, data)
            else:
                user = self.user_repository.find_user_by_username(username)
            if not user:
                logger.warning(
                    "[UserService] User not found in cache or database: %s", username
                )
                raise ResourceNotFoundError("User not found")
            if not cached_user:
                await cache.set(
                    "user:%s" % username,
                    json.dumps(self.user_repository._to_dict(user), default=str),
                    3600,
                )
            logger.info("[UserService] User authenticated successfully: %s", username)
            return {"token": token}
        except Exception as error:
            logger.error(
                "[UserService] Authentication process failed for user: %s",
                username,
                exc_info=True,
            )
            raise BaseAppException(
                "Authentication failed: Invalid username or password",
                details=str(error),
            ) from error

    async def initiate_password_reset(self, username: str) -> Dict[str, Any]:
        """
        Asynchronously initiate a password reset for a user.

        Args:
            username (str): The username for which to initiate a password reset.

        Returns:
            Dict[str, Any]: A dictionary with a success message and response details.

        Raises:
            BaseAppException: If the password reset initiation fails.
        """
        try:
            logger.info(
                "[UserService] Initiating password reset for user: %s", username
            )
            response = await self.password_service.initiate_user_password_reset(
                username
            )
            logger.info(
                "[UserService] Password reset initiated successfully for user: %s",
                username,
            )
            return {
                "message": "Password reset initiated. Check your email for the code.",
                "response": response,
            }
        except Exception as error:
            logger.error(
                "[UserService] Failed to initiate password reset for user: %s",
                username,
                exc_info=True,
            )
            raise BaseAppException(
                "Failed to initiate password reset", details=str(error)
            ) from error

    async def complete_password_reset(
        self, username: str, new_password: str, confirmation_code: str
    ) -> Dict[str, Any]:
        """
        Asynchronously complete the password reset process for a user.

        This method validates the input, calls the password service to complete the reset,
        encrypts the new password, updates the user in the repository, and returns a success message.

        Args:
            username (str): The username.
            new_password (str): The new password.
            confirmation_code (str): The confirmation code.

        Returns:
            Dict[str, Any]: A dictionary with a success message and response details.

        Raises:
            BaseAppException: If completing the password reset fails.
        """
        try:
            logger.info("[UserService] Starting password reset for user: %s", username)
            reset_password_input_validator(username, new_password, confirmation_code)
            response = await self.password_service.complete_user_password_reset(
                username, new_password, confirmation_code
            )
            logger.info(
                "[UserService] Cognito password reset completed for user: %s", username
            )
            encrypted_password = self.password_service.get_password_encrypted(
                new_password
            )
            logger.info(
                "[UserService] Password encrypted successfully for user: %s", username
            )
            user = self.user_repository.find_user_by_username(username)
            if not user:
                logger.warning(
                    "[UserService] User not found in repository: %s", username
                )
                raise ResourceNotFoundError("User not found in the repository")
            self.user_repository.update_entity(
                user.id, {"password": encrypted_password}
            )
            logger.info(
                "[UserService] Password updated in the database for user: %s", username
            )
            logger.info(
                "[UserService] Password reset successfully completed for user: %s",
                username,
            )
            return {
                "message": "Password reset successfully completed.",
                "response": response,
            }
        except Exception as error:
            logger.error(
                "[UserService] Failed to complete password reset for user: %s",
                username,
                exc_info=True,
            )
            raise BaseAppException(
                "Failed to complete password reset", details=str(error)
            ) from error
