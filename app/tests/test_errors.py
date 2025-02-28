import unittest
from app.errors import BaseAppException, ValidationError, UnauthorizedError, ResourceNotFoundError


class TestErrors(unittest.TestCase):
    def test_base_app_exception_defaults(self):
        # Test default values for BaseAppException.
        exc = BaseAppException("Base error")
        self.assertEqual(exc.message, "Base error")
        self.assertEqual(exc.status_code, 500)
        self.assertIsNone(exc.details)

    def test_base_app_exception_custom(self):
        # Test custom status code and details.
        exc = BaseAppException(
            "Custom error", status_code=418, details="I'm a teapot")
        self.assertEqual(exc.message, "Custom error")
        self.assertEqual(exc.status_code, 418)
        self.assertEqual(exc.details, "I'm a teapot")

    def test_validation_error_default(self):
        # ValidationError should have status code 400.
        exc = ValidationError("Invalid input")
        self.assertEqual(exc.message, "Invalid input")
        self.assertEqual(exc.status_code, 400)
        self.assertIsNone(exc.details)

    def test_validation_error_custom(self):
        exc = ValidationError("Invalid input", details="Field X is missing")
        self.assertEqual(exc.message, "Invalid input")
        self.assertEqual(exc.status_code, 400)
        self.assertEqual(exc.details, "Field X is missing")

    def test_unauthorized_error_default(self):
        # UnauthorizedError should default to "Unauthorized" and status code 401.
        exc = UnauthorizedError()
        self.assertEqual(exc.message, "Unauthorized")
        self.assertEqual(exc.status_code, 401)
        self.assertIsNone(exc.details)

    def test_unauthorized_error_custom(self):
        # Test a custom message for UnauthorizedError.
        exc = UnauthorizedError("Access denied")
        self.assertEqual(exc.message, "Access denied")
        self.assertEqual(exc.status_code, 401)
        self.assertIsNone(exc.details)

    def test_resource_not_found_error_default(self):
        # ResourceNotFoundError should default to "Resource not found" and status code 404.
        exc = ResourceNotFoundError()
        self.assertEqual(exc.message, "Resource not found")
        self.assertEqual(exc.status_code, 404)
        self.assertIsNone(exc.details)

    def test_resource_not_found_error_custom(self):
        # Test a custom message and details for ResourceNotFoundError.
        exc = ResourceNotFoundError(
            "Item not found", details="No item exists with that ID")
        self.assertEqual(exc.message, "Item not found")
        self.assertEqual(exc.status_code, 404)
        self.assertEqual(exc.details, "No item exists with that ID")
