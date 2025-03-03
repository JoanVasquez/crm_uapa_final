"""Utility functions for Amazon Cognito operations.

This module provides functions for authenticating users, registering users,
confirming user registration, and handling password resets using Amazon Cognito.
"""

import os

import boto3

from app.errors import BaseAppException, UnauthorizedError
from app.utils.logger import get_logger
from app.utils.ssm_util import get_cached_parameter

logger = get_logger(__name__)

cognito_client = boto3.client(
    "cognito-idp", region_name=os.environ.get("AWS_REGION", "us-east-1")
)

_COGNITO_CLIENT_ID_SSM_PATH_STR = "COGNITO_CLIENT_ID_SSM_PATH"
_COGNITO_CLIENT_ID_SSM_PATH_STR_ERROR = (
    "COGNITO_CLIENT_ID_SSM_PATH environment variable is not set"
)
cognito_client_id_ssm_path = os.environ.get(_COGNITO_CLIENT_ID_SSM_PATH_STR)


def authenticate(username: str, password: str) -> str:
    """Authenticate a user using Amazon Cognito.

    Args:
        username (str): The username of the user.
        password (str): The user's password.

    Returns:
        str: The IdToken from Cognito if authentication is successful.

    Raises:
        BaseAppException: If required environment variables are missing or authentication fails.
        UnauthorizedError: If authentication fails with no result.
    """
    try:
        if not cognito_client_id_ssm_path:
            raise BaseAppException(_COGNITO_CLIENT_ID_SSM_PATH_STR_ERROR)
        client_id = get_cached_parameter(cognito_client_id_ssm_path)
        logger.info("[CognitoService] Authenticating user: %s", username)
        user_pool_id = get_cached_parameter(os.environ["COGNITO_USER_POOL_ID"])
        response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
        )
        logger.info("[CognitoService] User authenticated successfully: %s", username)
        auth_result = response.get("AuthenticationResult")
        if auth_result is None:
            raise UnauthorizedError("Authentication failed: no result")
        return auth_result.get("IdToken")
    except Exception as error:
        logger.error(
            "[CognitoService] Authentication failed for user: %s",
            username,
            exc_info=True,
        )
        if isinstance(error, UnauthorizedError):
            raise error
        raise BaseAppException("Authentication failed") from error


def register_user(username: str, password: str, email: str) -> dict:
    """Register a new user in Amazon Cognito.

    Args:
        username (str): The desired username.
        password (str): The user's password.
        email (str): The user's email address.

    Returns:
        dict: A dictionary containing a success message.

    Raises:
        BaseAppException: If user registration fails.
    """
    try:
        if not cognito_client_id_ssm_path:
            raise BaseAppException(_COGNITO_CLIENT_ID_SSM_PATH_STR_ERROR)
        client_id = get_cached_parameter(cognito_client_id_ssm_path)
        logger.info("[CognitoService] Registering user: %s", username)
        cognito_client.sign_up(
            ClientId=client_id,
            Username=username,
            Password=password,
            UserAttributes=[{"Name": "email", "Value": email}],
        )
        logger.info("[CognitoService] User registered successfully: %s", username)
        return {"message": "User registered successfully"}
    except Exception as error:
        logger.error(
            "[CognitoService] Registration failed for user: %s", username, exc_info=True
        )
        raise BaseAppException("Registration failed") from error


def confirm_user_registration(username: str, confirmation_code: str) -> dict:
    """Confirm a user's registration in Amazon Cognito.

    Args:
        username (str): The username to confirm.
        confirmation_code (str): The confirmation code received by the user.

    Returns:
        dict: A dictionary containing a success message.

    Raises:
        BaseAppException: If user confirmation fails.
    """
    try:
        if not cognito_client_id_ssm_path:
            raise BaseAppException(_COGNITO_CLIENT_ID_SSM_PATH_STR_ERROR)
        client_id = get_cached_parameter(cognito_client_id_ssm_path)
        logger.info("[CognitoService] Confirming registration for user: %s", username)
        cognito_client.confirm_sign_up(
            ClientId=client_id,
            Username=username,
            ConfirmationCode=confirmation_code,
        )
        logger.info(
            "[CognitoService] User registration confirmed successfully: %s", username
        )
        return {"message": "User confirmed successfully"}
    except Exception as error:
        logger.error(
            "[CognitoService] Confirmation failed for user: %s", username, exc_info=True
        )
        raise BaseAppException("User confirmation failed") from error


def initiate_password_reset(username: str) -> dict:
    """Initiate a password reset for a user in Amazon Cognito.

    Args:
        username (str): The username for which to initiate the password reset.

    Returns:
        dict: A dictionary containing a success message indicating that password reset was initiated.

    Raises:
        BaseAppException: If initiating the password reset fails.
    """
    try:
        if not cognito_client_id_ssm_path:
            raise BaseAppException(_COGNITO_CLIENT_ID_SSM_PATH_STR_ERROR)
        client_id = get_cached_parameter(cognito_client_id_ssm_path)
        logger.info("[CognitoService] Initiating password reset for user: %s", username)
        cognito_client.forgot_password(
            ClientId=client_id,
            Username=username,
        )
        logger.info(
            "[CognitoService] Password reset initiated successfully for user: %s",
            username,
        )
        return {"message": "Password reset initiated. Check your email for the code."}
    except Exception as error:
        logger.error(
            "[CognitoService] Failed to initiate password reset for user: %s",
            username,
            exc_info=True,
        )
        raise BaseAppException("Password reset initiation failed") from error


def complete_password_reset(
    username: str, new_password: str, confirmation_code: str
) -> dict:
    """Complete the password reset process for a user in Amazon Cognito.

    Args:
        username (str): The username for which to reset the password.
        new_password (str): The new password.
        confirmation_code (str): The confirmation code received by the user.

    Returns:
        dict: A dictionary containing a success message.

    Raises:
        BaseAppException: If completing the password reset fails.
    """
    try:
        if not cognito_client_id_ssm_path:
            raise BaseAppException(_COGNITO_CLIENT_ID_SSM_PATH_STR_ERROR)
        client_id = get_cached_parameter(cognito_client_id_ssm_path)
        logger.info("[CognitoService] Completing password reset for user: %s", username)
        cognito_client.confirm_forgot_password(
            ClientId=client_id,
            Username=username,
            Password=new_password,
            ConfirmationCode=confirmation_code,
        )
        logger.info(
            "[CognitoService] Password reset completed successfully for user: %s",
            username,
        )
        return {"message": "Password reset successfully"}
    except Exception as error:
        logger.error(
            "[CognitoService] Failed to complete password reset for user: %s",
            username,
            exc_info=True,
        )
        raise BaseAppException("Password reset failed") from error
