"""Unit tests for Cognito utility functions.

This module tests the functionality provided by the Cognito service utility functions,
including authentication, user registration, confirmation, and password resets.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

import app.utils.cognito_util as cognito_service


class TestCognitoService(unittest.TestCase):
    """Unit tests for the Cognito service functions."""

    def setUp(self):
        """
        Set up fake SSM parameter data.

        The test relies on environment variables defined in .env.test.
        """
        self.fake_ssm_params = {
            "/crm/cognito/client-id": "fake-client-id",
            "/crm/cognito/user-pool-id": "fake-user-pool-id",
        }

    def fake_get_cached_parameter(self, param):
        """
        Mock implementation of get_cached_parameter.

        Args:
            param (str): The parameter key.

        Returns:
            str: The corresponding fake value if present; otherwise, the original param.
        """
        return self.fake_ssm_params.get(param, param)

    def tearDown(self):
        """Reset environment variables for subsequent tests."""
        os.environ["COGNITO_CLIENT_ID_SSM_PATH"] = "/crm/cognito/client-id"

    @patch("app.utils.cognito_util.cognito_client")
    @patch("app.utils.cognito_util.get_cached_parameter", new_callable=MagicMock)
    def test_authenticate_success(
        self, _mock_get_cached_parameter, mock_cognito_client
    ):
        """
        Test that authenticate() returns a valid IdToken when authentication succeeds.

        The fake Cognito response contains an 'AuthenticationResult' with an 'IdToken'.
        """
        _mock_get_cached_parameter.side_effect = self.fake_get_cached_parameter

        fake_response = {"AuthenticationResult": {"IdToken": "fake-id-token"}}
        mock_cognito_client.admin_initiate_auth.return_value = fake_response

        token = cognito_service.authenticate("testuser", "testpassword")
        self.assertEqual(token, "fake-id-token")

        mock_cognito_client.admin_initiate_auth.assert_called_with(
            UserPoolId="fake-user-pool-id",
            ClientId="fake-client-id",
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={"USERNAME": "testuser", "PASSWORD": "testpassword"},
        )

    @patch("app.utils.cognito_util.cognito_client")
    @patch("app.utils.cognito_util.get_cached_parameter", new_callable=MagicMock)
    def test_register_user_success(
        self, _mock_get_cached_parameter, mock_cognito_client
    ):
        """
        Test that register_user() returns a success message when registration succeeds.
        """
        _mock_get_cached_parameter.side_effect = self.fake_get_cached_parameter

        mock_cognito_client.sign_up.return_value = {
            "message": "User registered successfully"
        }

        result = cognito_service.register_user(
            "newuser", "newpassword", "newuser@example.com"
        )
        self.assertEqual(result, {"message": "User registered successfully"})

        mock_cognito_client.sign_up.assert_called_with(
            ClientId="fake-client-id",
            Username="newuser",
            Password="newpassword",
            UserAttributes=[{"Name": "email", "Value": "newuser@example.com"}],
        )

    @patch("app.utils.cognito_util.cognito_client")
    @patch("app.utils.cognito_util.get_cached_parameter", new_callable=MagicMock)
    def test_confirm_user_registration_success(
        self, _mock_get_cached_parameter, mock_cognito_client
    ):
        """
        Test that confirm_user_registration() returns a success message when confirmation succeeds.
        """
        _mock_get_cached_parameter.side_effect = self.fake_get_cached_parameter

        result = cognito_service.confirm_user_registration("confirmuser", "123456")
        self.assertEqual(result, {"message": "User confirmed successfully"})

        mock_cognito_client.confirm_sign_up.assert_called_with(
            ClientId="fake-client-id",
            Username="confirmuser",
            ConfirmationCode="123456",
        )

    @patch("app.utils.cognito_util.cognito_client")
    @patch("app.utils.cognito_util.get_cached_parameter", new_callable=MagicMock)
    def test_initiate_password_reset_success(
        self, _mock_get_cached_parameter, mock_cognito_client
    ):
        """
        Test that initiate_password_reset() returns a success message when reset is initiated.
        """
        _mock_get_cached_parameter.side_effect = self.fake_get_cached_parameter

        result = cognito_service.initiate_password_reset("resetuser")
        self.assertEqual(
            result,
            {"message": "Password reset initiated. Check your email for the code."},
        )
        mock_cognito_client.forgot_password.assert_called_with(
            ClientId="fake-client-id",
            Username="resetuser",
        )

    @patch("app.utils.cognito_util.cognito_client")
    @patch("app.utils.cognito_util.get_cached_parameter", new_callable=MagicMock)
    def test_complete_password_reset_success(
        self, _mock_get_cached_parameter, mock_cognito_client
    ):
        """
        Test that complete_password_reset() returns a success message when reset completes.
        """
        _mock_get_cached_parameter.side_effect = self.fake_get_cached_parameter

        result = cognito_service.complete_password_reset(
            "resetuser", "newpassword", "654321"
        )
        self.assertEqual(result, {"message": "Password reset successfully"})
        mock_cognito_client.confirm_forgot_password.assert_called_with(
            ClientId="fake-client-id",
            Username="resetuser",
            Password="newpassword",
            ConfirmationCode="654321",
        )

    @patch("app.utils.cognito_util.get_cached_parameter", new_callable=MagicMock)
    def test_missing_env_var(self, _mock_get_cached_parameter):
        """
        Test that authenticate() raises an exception when the required environment variable is missing.
        """
        if "COGNITO_CLIENT_ID_SSM_PATH" in os.environ:
            del os.environ["COGNITO_CLIENT_ID_SSM_PATH"]

        with self.assertRaises(Exception) as context:
            cognito_service.authenticate("user", "password")
        self.assertIn("Authentication failed", str(context.exception))
