"""
Module for testing the AuthenticationService.
"""

import unittest
from unittest.mock import call, patch

from app.errors import BaseAppException, UnauthorizedError
from app.services.authentication_service import AuthenticationService


class TestAuthenticationService(unittest.TestCase):
    """Test cases for AuthenticationService methods."""

    def setUp(self):
        """Set up test variables and instantiate AuthenticationService."""
        self.auth_service = AuthenticationService()
        self.username = "testuser"
        self.password = "testpass"
        self.email = "test@example.com"
        self.confirmation_code = "123456"
        self.fake_token = "fake_token"

    @patch("app.services.authentication_service.logger")
    @patch("app.services.authentication_service.cache")
    @patch("app.services.authentication_service.cognito_register_user")
    def test_register_user_success(self, mock_register_user, mock_cache, _mock_logger):
        """
        Test that register_user calls cognito_register_user correctly and,
        on success, no cache deletion occurs.
        """
        # Call the method under test.
        self.auth_service.register_user(self.username, self.password, self.email)
        # Verify that cognito_register_user was called with the correct arguments.
        mock_register_user.assert_called_once_with(
            self.username, self.password, self.email
        )
        # Since no error occurred, cache.delete should not be called.
        mock_cache.delete.assert_not_called()
        # Optionally verify that logger.info was called.
        self.assertTrue(_mock_logger.info.called)

    @patch("app.services.authentication_service.logger")
    @patch("app.services.authentication_service.cache")
    @patch("app.services.authentication_service.cognito_register_user")
    def test_register_user_failure_before_user_created(
        self, mock_register_user, mock_cache, _mock_logger
    ):
        """
        Test that if an exception is raised before the user is marked as created,
        only the user cache (f"user:{username}") is deleted.
        """
        # Simulate an exception in cognito_register_user.
        mock_register_user.side_effect = Exception("Registration failed")
        with self.assertRaises(BaseAppException) as context:
            self.auth_service.register_user(self.username, self.password, self.email)
        self.assertIn("Registration failed", str(context.exception))
        # Since the user was not marked as created, only the user cache should be deleted.
        expected_cache_key = f"user:{self.username}"
        mock_cache.delete.assert_called_once_with(expected_cache_key)

    @patch("app.services.authentication_service.logger")
    @patch("app.services.authentication_service.cache")
    @patch("app.services.authentication_service.cognito_register_user")
    def test_register_user_failure_after_user_created(
        self, mock_register_user, mock_cache, _mock_logger
    ):
        """
        Test that if an exception is raised after the user is marked as created,
        the method performs a rollback by calling cache.delete twice: once for the username
        and once for the user cache.
        """
        # Let cognito_register_user succeed so that the service marks the user as created.
        mock_register_user.return_value = None

        # Define a side-effect for logger.info that raises an exception when the registration log is emitted.
        def info_side_effect(message, *_args, **_kwargs):
            if "User registered in Cognito:" in message:
                raise Exception("Test exception after user creation")
            # No return needed

        _mock_logger.info.side_effect = info_side_effect

        with self.assertRaises(BaseAppException) as context:
            self.auth_service.register_user(self.username, self.password, self.email)
        self.assertIn("Registration failed", str(context.exception))
        # Expect that cache.delete was called twice.
        self.assertEqual(mock_cache.delete.call_count, 2)
        expected_calls = [call(self.username), call(f"user:{self.username}")]
        mock_cache.delete.assert_has_calls(expected_calls, any_order=False)

    @patch("app.services.authentication_service.logger")
    @patch("app.services.authentication_service.cognito_authenticate")
    def test_authenticate_user_success(self, mock_authenticate, _mock_logger):
        """
        Test that authenticate_user returns the token provided by cognito_authenticate.
        """
        mock_authenticate.return_value = self.fake_token
        token = self.auth_service.authenticate_user(self.username, self.password)
        self.assertEqual(token, self.fake_token)
        mock_authenticate.assert_called_once_with(self.username, self.password)

    @patch("app.services.authentication_service.logger")
    @patch("app.services.authentication_service.cognito_authenticate")
    def test_authenticate_user_failure(self, mock_authenticate, _mock_logger):
        """
        Test that authenticate_user raises an UnauthorizedError when cognito_authenticate returns None.
        """
        mock_authenticate.return_value = None
        with self.assertRaises(UnauthorizedError) as context:
            self.auth_service.authenticate_user(self.username, self.password)
        self.assertIn("Authentication failed", str(context.exception))
        mock_authenticate.assert_called_once_with(self.username, self.password)

    @patch("app.services.authentication_service.logger")
    @patch("app.services.authentication_service.cognito_confirm_user_registration")
    def test_confirm_user_registration_success(self, mock_confirm, _mock_logger):
        """
        Test that confirm_user_registration calls cognito_confirm_user_registration with the correct arguments.
        """
        self.auth_service.confirm_user_registration(
            self.username, self.confirmation_code
        )
        mock_confirm.assert_called_once_with(self.username, self.confirmation_code)
        self.assertTrue(_mock_logger.info.called)

    @patch("app.services.authentication_service.logger")
    @patch("app.services.authentication_service.cognito_confirm_user_registration")
    def test_confirm_user_registration_failure(self, mock_confirm, _mock_logger):
        """
        Test that confirm_user_registration raises a BaseAppException when an error occurs.
        """
        mock_confirm.side_effect = Exception("Confirmation error")
        with self.assertRaises(BaseAppException) as context:
            self.auth_service.confirm_user_registration(
                self.username, self.confirmation_code
            )
        self.assertIn("User confirmation failed", str(context.exception))
        mock_confirm.assert_called_once_with(self.username, self.confirmation_code)
