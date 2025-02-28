from app.utils.cache_util import cache
from app.utils.cognito_util import authenticate as cognito_authenticate
from app.utils.cognito_util import \
    confirm_user_registration as cognito_confirm_user_registration
from app.utils.cognito_util import register_user as cognito_register_user
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthenticationService:

    def register_user(self, username: str, password: str, email: str) -> None:
        cognito_user_created = False
        try:
            logger.info(("[AuthenticationService] Registering user in "
                         f"Cognito: {username}"))
            cognito_register_user(username, password, email)
            cognito_user_created = True
            logger.info(("[AuthenticationService] User registered in "
                         f"Cognito: {username}"))
        except Exception:
            if cognito_user_created:
                logger.info(("[UserService] Rolling back Cognito user: "
                             f"{username}"))
                cache.delete(username)
                logger.info(("[UserService] Cognito user rolled back: "
                             f"{username}"))
            logger.info(f"[UserService] Removing cache for user: {username}")
            cache.delete(f"user:{username}")
            logger.info(f"[UserService] Cache removed for user: {username}")

    def authenticate_user(self, username: str, password: str) -> str:
        logger.info(("[AuthenticationService] Authenticating user: "
                     f"{username}"))
        token = cognito_authenticate(username, password)
        if not token:
            logger.error(("[AuthenticationService] Failed to retrieve token "
                          f"for user: {username}"))
            raise Exception("Authentication failed")
        return token

    def confirm_user_registration(self, username: str,
                                  confirmation_code: str) -> None:
        logger.info(
            ("[AuthenticationService] Confirming registration for user: "
             f"{username}"))
        cognito_confirm_user_registration(username, confirmation_code)
        logger.info(("[AuthenticationService] User registration confirmed: "
                     f"{username}"))
