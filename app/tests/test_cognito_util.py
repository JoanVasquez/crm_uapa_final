# test_cognito_util.py
import os
import unittest
from unittest.mock import MagicMock, patch

import app.utils.cognito_util as cognito_service


class TestCognitoService(unittest.TestCase):
    def setUp(self):
        """
        We rely on .env.test for environment variables, so no manual
        os.environ[...] calls here. We only set up the fake SSM parameter data.
        """
        self.fake_ssm_params = {
            "/myapp/cognito/client-id": "fake-client-id",
            "/myapp/cognito/user-pool-id": "fake-user-pool-id",
        }

    def fake_get_cached_parameter(self, param):
        """
        Our mocked get_cached_parameter returns a mapped value if it exists,
        otherwise just returns the param as-is.
        """
        return self.fake_ssm_params.get(param, param)

    def tearDown(self):
        # Re-set environment if needed so subsequent tests are not broken
        os.environ["COGNITO_CLIENT_ID_SSM_PATH"] = "/myapp/cognito/client-id"

    @patch("app.utils.cognito_util.cognito_client")
    @patch("app.utils.cognito_util.get_cached_parameter", new_callable=MagicMock)
    def test_authenticate_success(self, mock_get_cached_parameter, mock_cognito_client):
        # Fake parameter side effect
        mock_get_cached_parameter.side_effect = self.fake_get_cached_parameter

        # Fake Cognito response
        fake_response = {"AuthenticationResult": {"IdToken": "fake-id-token"}}
        mock_cognito_client.admin_initiate_auth.return_value = fake_response

        # Call the method
        token = cognito_service.authenticate("testuser", "testpassword")
        self.assertEqual(token, "fake-id-token")

        # Confirm correct calls
        mock_cognito_client.admin_initiate_auth.assert_called_with(
            UserPoolId="fake-user-pool-id",
            ClientId="fake-client-id",
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={"USERNAME": "testuser",
                            "PASSWORD": "testpassword"},
        )

    @patch("app.utils.cognito_util.cognito_client")
    @patch("app.utils.cognito_util.get_cached_parameter", new_callable=MagicMock)
    def test_register_user_success(self, mock_get_cached_parameter, mock_cognito_client):
        mock_get_cached_parameter.side_effect = self.fake_get_cached_parameter
        # Fake sign_up response
        mock_cognito_client.sign_up.return_value = {
            "message": "User registered successfully"}

        result = cognito_service.register_user(
            "newuser", "newpassword", "newuser@example.com")
        self.assertEqual(result, {"message": "User registered successfully"})

        mock_cognito_client.sign_up.assert_called_with(
            ClientId="fake-client-id",
            Username="newuser",
            Password="newpassword",
            UserAttributes=[{"Name": "email", "Value": "newuser@example.com"}],
        )

    @patch("app.utils.cognito_util.cognito_client")
    @patch("app.utils.cognito_util.get_cached_parameter", new_callable=MagicMock)
    def test_confirm_user_registration_success(self, mock_get_cached_parameter, mock_cognito_client):
        mock_get_cached_parameter.side_effect = self.fake_get_cached_parameter

        result = cognito_service.confirm_user_registration(
            "confirmuser", "123456")
        self.assertEqual(result, {"message": "User confirmed successfully"})

        mock_cognito_client.confirm_sign_up.assert_called_with(
            ClientId="fake-client-id",
            Username="confirmuser",
            ConfirmationCode="123456",
        )

    @patch("app.utils.cognito_util.cognito_client")
    @patch("app.utils.cognito_util.get_cached_parameter", new_callable=MagicMock)
    def test_initiate_password_reset_success(self, mock_get_cached_parameter, mock_cognito_client):
        mock_get_cached_parameter.side_effect = self.fake_get_cached_parameter

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
    def test_complete_password_reset_success(self, mock_get_cached_parameter, mock_cognito_client):
        mock_get_cached_parameter.side_effect = self.fake_get_cached_parameter

        result = cognito_service.complete_password_reset(
            "resetuser", "newpassword", "654321")
        self.assertEqual(result, {"message": "Password reset successfully"})

        mock_cognito_client.confirm_forgot_password.assert_called_with(
            ClientId="fake-client-id",
            Username="resetuser",
            Password="newpassword",
            ConfirmationCode="654321",
        )

    @patch("app.utils.cognito_util.get_cached_parameter", new_callable=MagicMock)
    def test_missing_env_var(self, mock_get_cached_parameter):
        # Remove the required environment variable for an error scenario
        if "COGNITO_CLIENT_ID_SSM_PATH" in os.environ:
            del os.environ["COGNITO_CLIENT_ID_SSM_PATH"]

        with self.assertRaises(Exception) as context:
            cognito_service.authenticate("user", "password")
        self.assertIn("Authentication failed", str(context.exception))
