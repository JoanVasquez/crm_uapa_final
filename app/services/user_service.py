import json
from typing import Any, Dict, Optional

from app.models import User
from app.repositories.user_repository import UserRepository
from app.services.authentication_service import AuthenticationService
from app.services.generic_service import GenericService
from app.services.password_service import PasswordService
from app.utils.cache_util_model import CacheModel
from app.utils.logger import get_logger
from app.utils.deserialize_instance import deserialize_instance
from app.utils.cache_util import cache
from app.utils.reset_password_input_validator import (
    reset_password_input_validator)

logger = get_logger(__name__)


class UserService(GenericService[User]):
    user_repository: UserRepository = UserRepository()

    def __init__(self) -> None:
        super().__init__(UserService.user_repository)
        self.auth_service = AuthenticationService()
        self.password_service = PasswordService()

    async def save(self,
                   entity: User,
                   cache_model: Optional[CacheModel] = None) -> Optional[User]:
        try:
            logger.info(f"[UserService] Registering user: {entity.username}")
            # Register the user via the authentication service.
            await self.auth_service.register_user(entity.username,
                                                  entity.password,
                                                  entity.email)
            # Encrypt the password.
            encrypted_password = self.password_service.get_password_encrypted(
                entity.password)
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
            logger.info(
                f"[UserService] User created in database: {entity.username}")
            return user
        except Exception as error:
            logger.error(
                f"[UserService] Registration failed for user: {entity.username}", exc_info=True)
            raise Exception("Registration failed") from error

    async def confirm_registration(self,
                                   username: str,
                                   confirmation_code: str) -> Dict[str, Any]:
        try:
            logger.info(
                f"[UserService] Confirming registration for user: {username}")
            response = await self.auth_service.confirm_user_registration(
                username, confirmation_code)
            logger.info(
                f"[UserService] User confirmed successfully: {username}")
            return response
        except Exception as error:
            logger.error(
                f"[UserService] Confirmation failed for user: {username}",
                exc_info=True,
            )
            raise Exception("User confirmation failed") from error

    async def authenticate(
            self, username: str, password: str) -> Dict[str, str]:
        try:
            logger.info(
                f"[UserService] Starting authentication for user: {username}")
            token = await self.auth_service.authenticate_user(
                username, password)
            cached_user = await cache.get(f"user:{username}")
            if cached_user:
                data = json.loads(cached_user)
                user = deserialize_instance(User, data)
            else:
                user = self.user_repository.find_user_by_username(username)
            if not user:
                logger.warning(
                    f"[UserService] User not found in cache or database: "
                    f"{username}")
                raise Exception("User not found")
            if not cached_user:
                # Use the repository helper to serialize the user.
                await cache.set(f"user:{username}",
                                json.dumps(self.user_repository._to_dict(
                                    user), default=str),
                                3600)
            logger.info(
                f"[UserService] User authenticated successfully: {username}")
            return {"token": token}
        except Exception as error:
            logger.error(
                f"[UserService] Authentication process failed for user: "
                f"{username}",
                exc_info=True,
            )
            raise Exception(
                "Authentication failed: "
                "Invalid username or password") from error

    async def initiate_password_reset(self, username: str) -> Dict[str, Any]:
        try:
            logger.info(
                f"[UserService] Initiating password reset "
                f"for user: {username}")
            response = await (
                self.password_service.initiate_user_password_reset(username)
            )
            logger.info(
                f"[UserService] Password reset initiated successfully "
                f"for user: {username}")
            return {
                "message": ("Password reset initiated. "
                            "Check your email for the code."),
                "response": response,
            }
        except Exception as error:
            logger.error(
                f"[UserService] Failed to initiate password reset for user: {username}", exc_info=True)
            raise Exception("Failed to initiate password reset") from error

    async def complete_password_reset(
            self,
            username: str,
            new_password: str,
            confirmation_code: str
    ) -> Dict[str, Any]:
        try:
            logger.info(
                f"[UserService] Starting password reset for user: {username}")
            reset_password_input_validator(
                username, new_password, confirmation_code)
            response = await (
                self.password_service.complete_user_password_reset(
                    username, new_password, confirmation_code)
            )
            logger.info(
                f"[UserService] Cognito password reset completed "
                f"for user: {username}")
            encrypted_password = self.password_service.get_password_encrypted(
                new_password)
            logger.info(
                "[UserService] Password encrypted successfully "
                f"for user: {username}")
            user = self.user_repository.find_user_by_username(username)
            if not user:
                logger.warning(
                    f"[UserService] User not found in repository: {username}")
                raise Exception("User not found in the repository")
            self.user_repository.update_entity(
                user.id, {"password": encrypted_password})
            logger.info(
                f"[UserService] Password updated in the database "
                f"for user: {username}")
            logger.info(
                f"[UserService] Password reset successfully completed "
                f"for user: {username}")
            return {
                "message": "Password reset successfully completed.",
                "response": response,
            }
        except Exception as error:
            logger.error(
                f"[UserService] Failed to complete password reset for user: {username}", exc_info=True)
            raise Exception("Failed to complete password reset") from error
