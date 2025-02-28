import unittest

from app.utils.http_response import HttpResponse


class TestHttpResponse(unittest.TestCase):

    def test_success_without_message(self):
        # Arrange
        data = {"key": "value"}
        expected = {"success": True, "message": "", "data": data}

        # Act
        result = HttpResponse.success(data)

        # Assert
        self.assertEqual(result, expected)

    def test_success_with_message(self):
        # Arrange
        data = [1, 2, 3]
        message = "Operation successful"
        expected = {"success": True, "message": message, "data": data}

        # Act
        result = HttpResponse.success(data, message)

        # Assert
        self.assertEqual(result, expected)

    def test_error_without_details(self):
        # Arrange
        message = "Something went wrong"
        code = 500
        expected = {
            "success": False,
            "message": message,
            "code": code,
            "details": None
        }

        # Act
        result = HttpResponse.error(message, code)

        # Assert
        self.assertEqual(result, expected)

    def test_error_with_details(self):
        # Arrange
        message = "Error occurred"
        code = 404
        details = "Not Found"
        expected = {
            "success": False,
            "message": message,
            "code": code,
            "details": details
        }

        # Act
        result = HttpResponse.error(message, code, details)

        # Assert
        self.assertEqual(result, expected)
