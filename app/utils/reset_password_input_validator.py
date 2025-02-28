from app.utils.logger import get_logger

logger = get_logger(__name__)


def reset_password_input_validator(username: str, password: str,
                                   confirmation_code: str) -> None:
    if not username or not password or not confirmation_code:
        logger.warning("[UserService] Missing required fields "
                       "for password reset.")
        raise ValueError("Missing required fields: username, newPassword, "
                         "or confirmationCode")
