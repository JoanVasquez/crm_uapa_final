import os

from app.errors import BaseAppException  # Import your custom error classes
from app.utils.cognito_util import complete_password_reset, initiate_password_reset
from app.utils.kms_util import encrypt_password
from app.utils.logger import get_logger
from app.utils.ssm_util import get_cached_parameter

logger = get_logger(__name__)


class PasswordService:
    async def get_password_encrypted(self, new_password: str) -> str:
        """
        Encrypt the given password using KMS and return the encrypted string.
        """
        try:
            kms_key_id = await get_cached_parameter(os.environ["KMS_KEY_ID"])
            return encrypt_password(new_password, kms_key_id)
        except Exception as error:
            msg = f"[PasswordService] Failed to encrypt password: {error}"
            logger.error(msg, exc_info=True)
            raise BaseAppException(
                "Failed to encrypt password", details=str(error)
            ) from error

    async def initiate_user_password_reset(self, username: str) -> None:
        """
        Initiate a password reset for the given username using Cognito.
        """
        try:
            logger.info(
                f"[PasswordService] Initiate user password reset in Cognito: {username}"
            )
            await initiate_password_reset(username)
            logger.info(
                f"[PasswordService] Password reset initiated for user: {username}"
            )
        except Exception as error:
            msg = f"[PasswordService] Failed to initiate password reset for user: {username}"
            logger.error(msg, exc_info=True)
            raise BaseAppException(
                "Failed to initiate password reset", details=str(error)
            ) from error

    async def complete_user_password_reset(
        self, username: str, confirmation_code: str, new_password: str
    ) -> None:
        """
        Complete the password reset for the given user.
        """
        try:
            logger.info(
                f"[AuthenticationService] Completing password reset for user: {username}"
            )
            await complete_password_reset(username, confirmation_code, new_password)
            logger.info(
                f"[AuthenticationService] Password reset completed for user: {username}"
            )
        except Exception as error:
            msg = f"[AuthenticationService] Failed to complete password reset for user: {username}"
            logger.error(msg, exc_info=True)
            raise BaseAppException(
                "Failed to complete password reset", details=str(error)
            ) from error
