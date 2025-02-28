import os
import boto3

from app.utils.logger import get_logger
from app.utils.ssm_util import get_cached_parameter

logger = get_logger(__name__)

cognito_client = boto3.client(
    "cognito-idp",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)


def authenticate(username: str, password: str) -> str:
    """Authenticate a user using Cognito."""
    try:
        CLIENT_ID_SSM_PATH = os.environ.get("COGNITO_CLIENT_ID_SSM_PATH")
        if not CLIENT_ID_SSM_PATH:
            raise ValueError(
                "COGNITO_CLIENT_ID_SSM_PATH environment variable is not set")
        CLIENT_ID = get_cached_parameter(CLIENT_ID_SSM_PATH)

        logger.info(f"[CognitoService] Authenticating user: {username}")
        user_pool_id = get_cached_parameter(os.environ["COGNITO_USER_POOL_ID"])
        response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=CLIENT_ID,
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": password
            },
        )
        logger.info(
            f"[CognitoService] User authenticated successfully: {username}")
        auth_result = response.get("AuthenticationResult")
        if auth_result is None:
            raise Exception("Authentication failed: no result")
        return auth_result.get("IdToken")
    except Exception as error:
        logger.error(
            f"[CognitoService] Authentication failed for user: {username}",
            exc_info=True,
        )
        raise Exception("Authentication failed") from error


def register_user(username: str, password: str, email: str) -> dict:
    """Register a new user in Cognito."""
    try:
        CLIENT_ID_SSM_PATH = os.environ.get("COGNITO_CLIENT_ID_SSM_PATH")
        if not CLIENT_ID_SSM_PATH:
            raise ValueError(
                "COGNITO_CLIENT_ID_SSM_PATH environment variable is not set")
        CLIENT_ID = get_cached_parameter(CLIENT_ID_SSM_PATH)
        logger.info(f"[CognitoService] Registering user: {username}")
        cognito_client.sign_up(
            ClientId=CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[{
                "Name": "email",
                "Value": email
            }],
        )
        logger.info(
            f"[CognitoService] User registered successfully: {username}")
        return {"message": "User registered successfully"}
    except Exception as error:
        logger.error(
            f"[CognitoService] Registration failed for user: {username}",
            exc_info=True,
        )
        raise Exception("Registration failed") from error


def confirm_user_registration(username: str, confirmation_code: str) -> dict:
    """Confirm a user's registration in Cognito."""
    try:
        CLIENT_ID_SSM_PATH = os.environ.get("COGNITO_CLIENT_ID_SSM_PATH")
        if not CLIENT_ID_SSM_PATH:
            raise ValueError(
                "COGNITO_CLIENT_ID_SSM_PATH environment variable is not set")
        CLIENT_ID = get_cached_parameter(CLIENT_ID_SSM_PATH)
        logger.info(
            f"[CognitoService] Confirming registration for user: {username}")
        cognito_client.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=username,
            ConfirmationCode=confirmation_code,
        )
        logger.info(
            f"[CognitoService] User registration confirmed successfully: {username}")
        return {"message": "User confirmed successfully"}
    except Exception as error:
        logger.error(
            f"[CognitoService] Confirmation failed for user: {username}",
            exc_info=True,
        )
        raise Exception("User confirmation failed") from error


def initiate_password_reset(username: str) -> dict:
    """Initiate password reset in Cognito."""
    try:
        CLIENT_ID_SSM_PATH = os.environ.get("COGNITO_CLIENT_ID_SSM_PATH")
        if not CLIENT_ID_SSM_PATH:
            raise ValueError(
                "COGNITO_CLIENT_ID_SSM_PATH environment variable is not set")
        CLIENT_ID = get_cached_parameter(CLIENT_ID_SSM_PATH)
        logger.info(
            f"[CognitoService] Initiating password reset for user: {username}")
        cognito_client.forgot_password(
            ClientId=CLIENT_ID,
            Username=username,
        )
        logger.info(
            f"[CognitoService] Password reset initiated successfully for user: {username}")
        return {
            "message": "Password reset initiated. Check your email for the code."
        }
    except Exception as error:
        logger.error(
            f"[CognitoService] Failed to initiate password reset for user: {username}",
            exc_info=True,
        )
        raise Exception("Password reset initiation failed") from error


def complete_password_reset(username: str, new_password: str, confirmation_code: str) -> dict:
    """Complete password reset in Cognito."""
    try:
        CLIENT_ID_SSM_PATH = os.environ.get("COGNITO_CLIENT_ID_SSM_PATH")
        if not CLIENT_ID_SSM_PATH:
            raise ValueError(
                "COGNITO_CLIENT_ID_SSM_PATH environment variable is not set")
        CLIENT_ID = get_cached_parameter(CLIENT_ID_SSM_PATH)
        logger.info(
            f"[CognitoService] Completing password reset for user: {username}")
        cognito_client.confirm_forgot_password(
            ClientId=CLIENT_ID,
            Username=username,
            Password=new_password,
            ConfirmationCode=confirmation_code,
        )
        logger.info(
            f"[CognitoService] Password reset completed successfully for user: {username}")
        return {"message": "Password reset successfully"}
    except Exception as error:
        logger.error(
            f"[CognitoService] Failed to complete password reset for user: {username}",
            exc_info=True,
        )
        raise Exception("Password reset failed") from error
