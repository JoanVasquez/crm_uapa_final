import unittest
from unittest.mock import patch

from app.utils.reset_password_input_validator import \
    reset_password_input_validator


class TestResetPasswordInputValidator(unittest.TestCase):

    def test_valid_input(self):
        """
        When all required fields are provided, the function should complete
        without raising any exceptions.
        """
        try:
            reset_password_input_validator("user123", "newPassword", "ABC123")
        except Exception as e:
            self.fail(
                f"reset_password_input_validator raised an exception with "
                f"valid input: {e}")

    @patch("app.utils.reset_password_input_validator.logger")
    def test_missing_username(self, mock_logger):
        """
        When the username is missing (empty string), the function should raise
        a ValueError and log a warning.
        """
        with self.assertRaises(ValueError) as context:
            reset_password_input_validator("", "newPassword", "ABC123")
        self.assertIn("Missing required fields", str(context.exception))
        mock_logger.warning.assert_called_with(
            "[UserService] Missing required fields for password reset.")

    @patch("app.utils.reset_password_input_validator.logger")
    def test_missing_password(self, mock_logger):
        """
        When the password is missing, the function should raise a ValueError
        and log a warning.
        """
        with self.assertRaises(ValueError) as context:
            reset_password_input_validator("user123", "", "ABC123")
        self.assertIn("Missing required fields", str(context.exception))
        mock_logger.warning.assert_called_with(
            "[UserService] Missing required fields for password reset.")

    @patch("app.utils.reset_password_input_validator.logger")
    def test_missing_confirmation_code(self, mock_logger):
        """
        When the confirmation code is missing, the function should raise a
        ValueError and log a warning.
        """
        with self.assertRaises(ValueError) as context:
            reset_password_input_validator("user123", "newPassword", "")
        self.assertIn("Missing required fields", str(context.exception))
        mock_logger.warning.assert_called_with(
            "[UserService] Missing required fields for password reset.")
