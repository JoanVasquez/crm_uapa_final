from typing import Optional


class BaseAppException(Exception):
    """
    A base exception for your application's domain errors.
    Subclasses can override status_code or accept additional data.
    """

    def __init__(self, message: str, status_code: int = 500, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class ValidationError(BaseAppException):
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, status_code=400, details=details)


class UnauthorizedError(BaseAppException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ResourceNotFoundError(BaseAppException):
    def __init__(self, message: str = "Resource not found", details: Optional[str] = None):
        super().__init__(message, status_code=404, details=details)
