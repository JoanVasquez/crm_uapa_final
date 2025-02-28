import base64
import unittest
from unittest.mock import patch

from botocore.exceptions import ClientError

import app.utils.kms_util as kms_util


class TestKMSUtil(unittest.TestCase):

    @patch("app.utils.kms_util.kms_client")
    def test_encrypt_password_success(self, mock_kms_client):
        # Prepare the fake response for a successful encryption.
        fake_ciphertext = b"encrypted-bytes"
        mock_kms_client.encrypt.return_value = {
            "CiphertextBlob": fake_ciphertext
        }
        password = "my_password"
        kms_key_id = "fake-key-id"

        # Call the encryption function.
        result = kms_util.encrypt_password(password, kms_key_id)

        # Expected result is the base64 encoded ciphertext.
        expected = base64.b64encode(fake_ciphertext).decode("utf-8")
        self.assertEqual(result, expected)

        # Verify that kms_client.encrypt was called with proper parameters.
        mock_kms_client.encrypt.assert_called_with(
            KeyId=kms_key_id, Plaintext=password.encode("utf-8"))

    @patch("app.utils.kms_util.kms_client")
    def test_encrypt_password_no_ciphertext_blob(self, mock_kms_client):
        # Simulate a response that does not contain CiphertextBlob.
        mock_kms_client.encrypt.return_value = {}
        password = "my_password"
        kms_key_id = "fake-key-id"

        with self.assertRaises(Exception) as context:
            kms_util.encrypt_password(password, kms_key_id)
        self.assertIn("Failed to encrypt password", str(context.exception))

    @patch("app.utils.kms_util.kms_client")
    def test_encrypt_password_client_error(self, mock_kms_client):
        # Simulate a ClientError being raised by kms_client.encrypt.
        error_response = {
            "Error": {
                "Code": "TestError",
                "Message": "Test failure"
            }
        }
        operation_name = "Encrypt"
        mock_kms_client.encrypt.side_effect = ClientError(
            error_response, operation_name)

        password = "my_password"
        kms_key_id = "fake-key-id"

        with self.assertRaises(Exception) as context:
            kms_util.encrypt_password(password, kms_key_id)
        self.assertIn("Failed to encrypt password", str(context.exception))
        # Optionally, check that the original exception is stored as __cause__.
        self.assertIsNotNone(context.exception.__cause__)

    @patch("app.utils.kms_util.kms_client")
    def test_decrypt_password_success(self, mock_kms_client):
        # Create a fake plaintext and corresponding ciphertext.
        fake_plaintext = b"decrypted_password"
        # First encode fake ciphertext using base64 (simulate the input string)
        fake_ciphertext_blob = b"encrypted-bytes"
        encrypted_password = base64.b64encode(fake_ciphertext_blob).decode(
            "utf-8")

        # When decrypt is called, return the fake plaintext.
        mock_kms_client.decrypt.return_value = {"Plaintext": fake_plaintext}

        kms_key_id = "fake-key-id"

        # Call the decryption function.
        result = kms_util.decrypt_password(encrypted_password, kms_key_id)

        self.assertEqual(result, fake_plaintext.decode("utf-8"))

        # Verify that kms_client.decrypt was called with the proper parameters.
        mock_kms_client.decrypt.assert_called_with(
            KeyId=kms_key_id,
            CiphertextBlob=base64.b64decode(encrypted_password))

    @patch("app.utils.kms_util.kms_client")
    def test_decrypt_password_no_plaintext(self, mock_kms_client):
        # Simulate a response that does not contain Plaintext.
        fake_ciphertext_blob = b"encrypted-bytes"
        encrypted_password = base64.b64encode(fake_ciphertext_blob).decode(
            "utf-8")

        mock_kms_client.decrypt.return_value = {}
        kms_key_id = "fake-key-id"

        with self.assertRaises(Exception) as context:
            kms_util.decrypt_password(encrypted_password, kms_key_id)
        self.assertIn("Failed to decrypt password", str(context.exception))

    @patch("app.utils.kms_util.kms_client")
    def test_decrypt_password_client_error(self, mock_kms_client):
        # Simulate a ClientError being raised by kms_client.decrypt.
        error_response = {
            "Error": {
                "Code": "TestError",
                "Message": "Test failure"
            }
        }
        operation_name = "Decrypt"
        mock_kms_client.decrypt.side_effect = ClientError(
            error_response, operation_name)

        fake_ciphertext_blob = b"encrypted-bytes"
        encrypted_password = base64.b64encode(fake_ciphertext_blob).decode(
            "utf-8")
        kms_key_id = "fake-key-id"

        with self.assertRaises(Exception) as context:
            kms_util.decrypt_password(encrypted_password, kms_key_id)
        self.assertIn("Failed to decrypt password", str(context.exception))
        self.assertIsNotNone(context.exception.__cause__)
