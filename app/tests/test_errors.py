"""
Module for testing custom application errors.
"""

import unittest

from app.errors import (
    BaseAppException,
    ResourceNotFoundError,
    UnauthorizedError,
    ValidationError,
)


class TestErrors(unittest.TestCase):
    """Test cases for custom application error classes."""

    def test_base_app_exception_defaults(self):
        """Test default values for BaseAppException."""
        exc = BaseAppException("Base error")
        self.assertEqual(exc.message, "Base error")
        self.assertEqual(exc.status_code, 500)
        self.assertIsNone(exc.details)

    def test_base_app_exception_custom(self):
        """Test custom status code and details for BaseAppException."""
        exc = BaseAppException("Custom error", status_code=418, details="I'm a teapot")
        self.assertEqual(exc.message, "Custom error")
        self.assertEqual(exc.status_code, 418)
        self.assertEqual(exc.details, "I'm a teapot")

    def test_validation_error_default(self):
        """Test that ValidationError has default status code 400 and no details."""
        exc = ValidationError("Invalid input")
        self.assertEqual(exc.message, "Invalid input")
        self.assertEqual(exc.status_code, 400)
        self.assertIsNone(exc.details)

    def test_validation_error_custom(self):
        """Test custom details for ValidationError."""
        exc = ValidationError("Invalid input", details="Field X is missing")
        self.assertEqual(exc.message, "Invalid input")
        self.assertEqual(exc.status_code, 400)
        self.assertEqual(exc.details, "Field X is missing")

    def test_unauthorized_error_default(self):
        """Test that UnauthorizedError defaults to 'Unauthorized' with status code 401."""
        exc = UnauthorizedError()
        self.assertEqual(exc.message, "Unauthorized")
        self.assertEqual(exc.status_code, 401)
        self.assertIsNone(exc.details)

    def test_unauthorized_error_custom(self):
        """Test custom message for UnauthorizedError."""
        exc = UnauthorizedError("Access denied")
        self.assertEqual(exc.message, "Access denied")
        self.assertEqual(exc.status_code, 401)
        self.assertIsNone(exc.details)

    def test_resource_not_found_error_default(self):
        """Test that ResourceNotFoundError defaults to 'Resource not found' with status code 404."""
        exc = ResourceNotFoundError()
        self.assertEqual(exc.message, "Resource not found")
        self.assertEqual(exc.status_code, 404)
        self.assertIsNone(exc.details)

    def test_resource_not_found_error_custom(self):
        """Test custom message and details for ResourceNotFoundError."""
        exc = ResourceNotFoundError(
            "Item not found", details="No item exists with that ID"
        )
        self.assertEqual(exc.message, "Item not found")
        self.assertEqual(exc.status_code, 404)
        self.assertEqual(exc.details, "No item exists with that ID")
