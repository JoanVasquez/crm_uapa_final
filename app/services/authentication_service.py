"""Authentication service module.

This module defines the AuthenticationService class, which provides methods to
register users, authenticate users, and confirm user registration via Amazon Cognito.
"""

from app.errors import BaseAppException, UnauthorizedError
from app.utils.cache_util import cache
from app.utils.cognito_util import authenticate as cognito_authenticate
from app.utils.cognito_util import (
    confirm_user_registration as cognito_confirm_user_registration,
)
from app.utils.cognito_util import register_user as cognito_register_user
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthenticationService:
    """Service for handling user authentication and registration using Cognito."""

    def register_user(self, username: str, password: str, email: str) -> None:
        """
        Register a new user using Cognito.

        This method registers a new user and, if needed, performs a rollback in case of failure.

        Args:
            username (str): The username for registration.
            password (str): The password for registration.
            email (str): The email address of the user.

        Raises:
            BaseAppException: If registration fails.
        """
        cognito_user_created = False
        try:
            logger.info(
                "[AuthenticationService] Registering user in Cognito: %s", username
            )
            cognito_register_user(username, password, email)
            cognito_user_created = True
            logger.info(
                "[AuthenticationService] User registered in Cognito: %s", username
            )
        except Exception as error:
            if cognito_user_created:
                logger.info("[UserService] Rolling back Cognito user: %s", username)
                cache.delete(username)
                logger.info("[UserService] Cognito user rolled back: %s", username)
            logger.info("[UserService] Removing cache for user: %s", username)
            cache.delete("user:%s" % username)
            logger.info("[UserService] Cache removed for user: %s", username)
            raise BaseAppException("Registration failed", details=str(error)) from error

    def authenticate_user(self, username: str, password: str) -> str:
        """
        Authenticate a user using Cognito.

        Args:
            username (str): The username.
            password (str): The user's password.

        Returns:
            str: The authentication token (IdToken).

        Raises:
            UnauthorizedError: If authentication fails.
        """
        logger.info("[AuthenticationService] Authenticating user: %s", username)
        token = cognito_authenticate(username, password)
        if not token:
            logger.error(
                "[AuthenticationService] Failed to retrieve token for user: %s",
                username,
            )
            raise UnauthorizedError("Authentication failed")
        return token

    def confirm_user_registration(self, username: str, confirmation_code: str) -> None:
        """
        Confirm a user's registration in Cognito.

        Args:
            username (str): The username to confirm.
            confirmation_code (str): The confirmation code provided to the user.

        Raises:
            BaseAppException: If user confirmation fails.
        """
        try:
            logger.info(
                "[AuthenticationService] Confirming registration for user: %s", username
            )
            cognito_confirm_user_registration(username, confirmation_code)
            logger.info(
                "[AuthenticationService] User registration confirmed: %s", username
            )
        except Exception as error:
            logger.error(
                "[AuthenticationService] User confirmation failed for user: %s",
                username,
                exc_info=True,
            )
            raise BaseAppException(
                "User confirmation failed", details=str(error)
            ) from error
