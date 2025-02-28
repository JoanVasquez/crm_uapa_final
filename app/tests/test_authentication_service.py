import unittest
from unittest.mock import patch

from app.services.authentication_service import AuthenticationService


class TestAuthenticationService(unittest.TestCase):

    def setUp(self):
        self.auth_service = AuthenticationService()
        self.username = "testuser"
        self.password = "testpass"
        self.email = "test@example.com"
        self.confirmation_code = "123456"
        self.fake_token = "fake_token"

    # --- Tests for register_user ---

    @patch('app.services.authentication_service.logger')
    @patch('app.services.authentication_service.cache')
    @patch('app.services.authentication_service.cognito_register_user')
    def test_register_user_success(self, mock_register_user, mock_cache,
                                   mock_logger):
        """
        Test that register_user calls cognito_register_user correctly and,
        on success, no cache deletion occurs.
        """
        # Call the method under test.
        self.auth_service.register_user(self.username, self.password,
                                        self.email)

        # Verify that cognito_register_user was called with the correct
        # arguments.
        mock_register_user.assert_called_once_with(self.username,
                                                   self.password, self.email)

        # Verify that no rollback (cache.delete) was triggered.
        mock_cache.delete.assert_not_called()

        # Optionally verify that some logging occurred.
        self.assertTrue(mock_logger.info.called)

    @patch('app.services.authentication_service.logger')
    @patch('app.services.authentication_service.cache')
    @patch('app.services.authentication_service.cognito_register_user')
    def test_register_user_failure_before_user_created(self,
                                                       mock_register_user,
                                                       mock_cache,
                                                       mock_logger):
        """
        Test that if an exception is raised before the user is marked as
        created, only the user cache (f"user:{username}") is deleted.
        """
        # Simulate an exception in cognito_register_user.
        mock_register_user.side_effect = Exception("Registration failed")

        # Call register_user (which catches the exception).
        self.auth_service.register_user(self.username, self.password,
                                        self.email)

        # Verify that cache.delete was called only once with the user
        # cache key.
        mock_cache.delete.assert_called_once_with(f"user:{self.username}")

    @patch('app.services.authentication_service.logger')
    @patch('app.services.authentication_service.cache')
    @patch('app.services.authentication_service.cognito_register_user')
    def test_register_user_failure_after_user_created(self, mock_register_user,
                                                      mock_cache, mock_logger):
        """
        Test that if an exception is raised after the user has been marked as
        created, the method performs a rollback by calling cache.delete twice:
        once for the rollback of the username and once for the user cache.
        """
        # Let cognito_register_user succeed so that the service marks
        # the user as created.
        mock_register_user.return_value = None

        # Define a side-effect for logger.info that raises an exception
        # when the log message indicates the user was registered in Cognito.
        def info_side_effect(message, *args, **kwargs):
            if "User registered in Cognito:" in message:
                raise Exception("Test exception after user creation")
            return None

        mock_logger.info.side_effect = info_side_effect

        # Call register_user; the exception is caught inside the method.
        self.auth_service.register_user(self.username, self.password,
                                        self.email)

        # Verify that rollback happens by checking that cache.delete is called
        # twice: once with the username and once with the user cache key.
        expected_calls = [((self.username, ), ),
                          ((f"user:{self.username}", ), )]
        self.assertEqual(mock_cache.delete.call_count, 2)
        mock_cache.delete.assert_has_calls(expected_calls, any_order=False)

    # --- Tests for authenticate_user ---

    @patch('app.services.authentication_service.logger')
    @patch('app.services.authentication_service.cognito_authenticate')
    def test_authenticate_user_success(self, mock_authenticate, mock_logger):
        """
        Test that authenticate_user returns the token provided by
        cognito_authenticate.
        """
        mock_authenticate.return_value = self.fake_token

        token = self.auth_service.authenticate_user(self.username,
                                                    self.password)

        self.assertEqual(token, self.fake_token)
        mock_authenticate.assert_called_once_with(self.username, self.password)

    @patch('app.services.authentication_service.logger')
    @patch('app.services.authentication_service.cognito_authenticate')
    def test_authenticate_user_failure(self, mock_authenticate, mock_logger):
        """
        Test that authenticate_user raises an Exception when
        cognito_authenticate returns None.
        """
        mock_authenticate.return_value = None

        with self.assertRaises(Exception) as context:
            self.auth_service.authenticate_user(self.username, self.password)
        self.assertIn("Authentication failed", str(context.exception))
        mock_authenticate.assert_called_once_with(self.username, self.password)

    # --- Tests for confirm_user_registration ---

    @patch('app.services.authentication_service.logger')
    @patch('app.services.authentication_service.'
           'cognito_confirm_user_registration')
    def test_confirm_user_registration_success(self, mock_confirm,
                                               mock_logger):
        """
        Test that confirm_user_registration calls
        cognito_confirm_user_registration with the correct arguments.
        """
        self.auth_service.confirm_user_registration(self.username,
                                                    self.confirmation_code)
        mock_confirm.assert_called_once_with(self.username,
                                             self.confirmation_code)
        self.assertTrue(mock_logger.info.called)
