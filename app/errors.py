"""Module for application-specific exceptions.

This module defines custom exceptions for the application, including a base exception
and more specific exceptions such as ValidationError, UnauthorizedError, and ResourceNotFoundError.
"""

from typing import Optional


class BaseAppException(Exception):
    """Base exception for the application's domain errors.

    Attributes:
        message (str): The error message.
        status_code (int): HTTP status code associated with the error.
        details (Optional[str]): Additional error details.
    """

    def __init__(
        self, message: str, status_code: int = 500, details: Optional[str] = None
    ):
        """
        Initialize a BaseAppException.

        Args:
            message (str): The error message.
            status_code (int): The HTTP status code (default 500).
            details (Optional[str]): Additional error details.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class ValidationError(BaseAppException):
    """Exception raised for validation errors with an HTTP status code 400."""

    def __init__(self, message: str, details: Optional[str] = None):
        """
        Initialize a ValidationError.

        Args:
            message (str): The error message.
            details (Optional[str]): Additional error details.
        """
        super().__init__(message, status_code=400, details=details)


class UnauthorizedError(BaseAppException):
    """Exception raised for unauthorized access with an HTTP status code 401."""

    def __init__(self, message: str = "Unauthorized"):
        """
        Initialize an UnauthorizedError.

        Args:
            message (str): The error message. Defaults to "Unauthorized".
        """
        super().__init__(message, status_code=401)


class ResourceNotFoundError(BaseAppException):
    """Exception raised when a requested resource is not found (HTTP status code 404)."""

    def __init__(
        self, message: str = "Resource not found", details: Optional[str] = None
    ):
        """
        Initialize a ResourceNotFoundError.

        Args:
            message (str): The error message. Defaults to "Resource not found".
            details (Optional[str]): Additional error details.
        """
        super().__init__(message, status_code=404, details=details)
