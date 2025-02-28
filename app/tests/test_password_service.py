import os
import unittest
from unittest.mock import patch, AsyncMock

from app.services.password_service import PasswordService


class TestPasswordService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):

        self.service = PasswordService()
        self.username = "testuser"
        self.new_password = "newpass"
        self.confirmation_code = "123456"
        self.kms_key_id = "kms-key-123"
        self.encrypted_password = "encrypted-newpass"

    # --- Tests for get_password_encrypted ---

    @patch("app.services.password_service.logger")
    @patch("app.services.password_service.get_cached_parameter", new_callable=AsyncMock)
    @patch("app.services.password_service.encrypt_password")
    async def test_get_password_encrypted_success(
        self, mock_encrypt, mock_get_param, mock_logger
    ):
        mock_get_param.return_value = self.kms_key_id
        mock_encrypt.return_value = self.encrypted_password

        result = await self.service.get_password_encrypted(self.new_password)

        mock_get_param.assert_called_once_with("/myapp/kms-key-id")
        mock_encrypt.assert_called_once_with(
            self.new_password, self.kms_key_id)
        self.assertEqual(result, self.encrypted_password)

    @patch("app.services.password_service.logger")
    @patch("app.services.password_service.get_cached_parameter", new_callable=AsyncMock)
    @patch("app.services.password_service.encrypt_password")
    async def test_get_password_encrypted_failure(
        self, mock_encrypt, mock_get_param, mock_logger
    ):
        mock_get_param.side_effect = Exception("Parameter not found")

        with self.assertRaises(Exception) as context:
            await self.service.get_password_encrypted(self.new_password)
        self.assertIn("Failed to encrypt password", str(context.exception))
        mock_logger.error.assert_called()

    # --- Tests for initiate_user_password_reset ---

    @patch("app.services.password_service.logger")
    @patch("app.services.password_service.initiate_password_reset", new_callable=AsyncMock)
    async def test_initiate_user_password_reset_success(
        self, mock_initiate, mock_logger
    ):
        await self.service.initiate_user_password_reset(self.username)
        mock_initiate.assert_called_once_with(self.username)
        self.assertTrue(mock_logger.info.called)

    @patch("app.services.password_service.logger")
    @patch("app.services.password_service.initiate_password_reset", new_callable=AsyncMock)
    async def test_initiate_user_password_reset_failure(
        self, mock_initiate, mock_logger
    ):
        mock_initiate.side_effect = Exception("Reset error")
        with self.assertRaises(Exception) as context:
            await self.service.initiate_user_password_reset(self.username)
        self.assertIn("Failed to initiate password reset",
                      str(context.exception))
        mock_logger.error.assert_called()

    # --- Tests for complete_user_password_reset ---

    @patch("app.services.password_service.logger")
    @patch("app.services.password_service.complete_password_reset", new_callable=AsyncMock)
    async def test_complete_user_password_reset_success(
        self, mock_complete, mock_logger
    ):
        await self.service.complete_user_password_reset(
            self.username, self.confirmation_code, self.new_password
        )
        mock_complete.assert_called_once_with(
            self.username, self.confirmation_code, self.new_password
        )
        self.assertTrue(mock_logger.info.called)

    @patch("app.services.password_service.logger")
    @patch("app.services.password_service.complete_password_reset", new_callable=AsyncMock)
    async def test_complete_user_password_reset_failure(
        self, mock_complete, mock_logger
    ):
        mock_complete.side_effect = Exception("Complete error")
        with self.assertRaises(Exception) as context:
            await self.service.complete_user_password_reset(
                self.username, self.confirmation_code, self.new_password
            )
        self.assertIn("Failed to complete password reset",
                      str(context.exception))
        mock_logger.error.assert_called()
