"""Authentication service module.

This module defines the AuthenticationService class, which provides methods to
register users, authenticate users, confirm user registration via Amazon Cognito,
and verify JWT tokens.
"""

import json
import os

import jwt
import requests

from app.errors import BaseAppException, UnauthorizedError
from app.utils.cache_util import cache
from app.utils.cognito_util import authenticate as cognito_authenticate
from app.utils.cognito_util import (
    confirm_user_registration as cognito_confirm_user_registration,
)
from app.utils.cognito_util import register_user as cognito_register_user
from app.utils.logger import get_logger
from app.utils.ssm_util import get_cached_parameter

logger = get_logger(__name__)

# The SSM path for Cognito client ID should be set in your environment
cognito_client_id_ssm_path = os.environ.get("COGNITO_CLIENT_ID_SSM_PATH")
if not cognito_client_id_ssm_path:
    raise BaseAppException("COGNITO_CLIENT_ID_SSM_PATH environment variable is not set")


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

    def verify_token(self, token: str) -> dict:
        """
        Verify the provided JWT token by checking its signature and claims.

        This method retrieves the JWKS from Amazon Cognito and caches it locally so that subsequent
        verifications can use the cached keys instead of making a request to Cognito every time.
        The JWKS is cached for 3600 seconds (1 hour).

        Args:
            token (str): The JWT token to verify.

        Returns:
            dict: The decoded token claims if verification succeeds.

        Raises:
            UnauthorizedError: If token verification fails.
        """
        try:
            # Get region from environment (default to us-east-1 if not provided)
            region = os.environ.get("AWS_REGION", "us-east-1")
            # Retrieve Cognito configuration from SSM parameters
            user_pool_id = get_cached_parameter(os.environ["COGNITO_USER_POOL_ID"])
            client_id = get_cached_parameter(cognito_client_id_ssm_path)

            # Build JWKS URL and expected issuer URL
            jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
            issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"

            # Check if JWKS is already cached to avoid repeated network requests.
            jwks_cache_key = f"cognito_jwks:{user_pool_id}"
            jwks = cache.get(jwks_cache_key)
            if not jwks:
                logger.info(
                    "[AuthenticationService] JWKS not found in cache, fetching from: %s",
                    jwks_url,
                )
                response = requests.get(jwks_url)
                response.raise_for_status()
                jwks = response.json()
                # Cache the JWKS for 1 hour (3600 seconds)
                cache.set(jwks_cache_key, jwks, 3600)
            else:
                logger.info("[AuthenticationService] JWKS loaded from cache")

            # Decode token header to extract key id (kid)
            headers = jwt.get_unverified_header(token)
            kid = headers.get("kid")
            if not kid:
                raise UnauthorizedError("Token header missing 'kid'")

            # Find the public key in the JWKS that matches the kid
            key = None
            for jwk in jwks["keys"]:
                if jwk["kid"] == kid:
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
                    break
            if key is None:
                raise UnauthorizedError("Public key not found in JWKS")

            # Decode and verify the token using the public key, expected audience, and issuer
            decoded_token = jwt.decode(
                token,
                key=key,
                algorithms=["RS256"],
                audience=client_id,
                issuer=issuer,
            )
            logger.info("[AuthenticationService] Token verified successfully")
            return decoded_token
        except Exception as error:
            logger.error(
                "[AuthenticationService] Token verification failed", exc_info=True
            )
            raise UnauthorizedError(
                "Token verification failed: " + str(error)
            ) from error
