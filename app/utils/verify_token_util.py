from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.errors import UnauthorizedError
from app.services.user_service import UserService

security = HTTPBearer()


# Dependency: JWT validation via AWS Cognito
# Dependency: JWT validation via the UserService's verify_token method.
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        user_service = UserService()
        # Call the async verify_token method in UserService.
        user = await user_service.verify_token(token)
        return user
    except Exception as e:
        raise UnauthorizedError("Invalid or expired token") from e
