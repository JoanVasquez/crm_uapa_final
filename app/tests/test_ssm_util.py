import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from botocore.exceptions import ClientError

from app.utils.ssm_util import get_cached_parameter


class TestGetCachedParameter(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Save current environment variables so we can restore them after tests.
        self.orig_env = dict(os.environ)

    def tearDown(self):
        # Restore environment variables.
        os.environ.clear()
        os.environ.update(self.orig_env)

    async def test_environment_returns_env_value(self):
        os.environ["DJANGO_ENV"] = "test"
        os.environ["TEST_PARAM"] = "myvalue"
        result = await get_cached_parameter("TEST_PARAM")
        self.assertEqual(result, "myvalue")

    async def test_environment_missing_variable_raises_exception(self):
        os.environ["DJANGO_ENV"] = "test"
        # Ensure the environment variable is not set.
        if "MISSING_PARAM" in os.environ:
            del os.environ["MISSING_PARAM"]

        with self.assertRaises(Exception) as context:
            await get_cached_parameter("MISSING_PARAM")
        self.assertIn("Environment variable 'MISSING_PARAM' is not set",
                      str(context.exception))

    @patch("app.utils.ssm_util.cache")
    @patch("app.utils.ssm_util.boto3.client")
    async def test_production_fetches_parameter_from_ssm(self, mock_boto_client, mock_cache):
        # Mock the Redis calls (so we don't have to init a real cache)
        mock_cache.get = AsyncMock(return_value=None)  # Force no cached value
        mock_cache.set = AsyncMock(return_value=None)

        # For production, ensure DJANGO_ENV is not set to "test".
        os.environ.pop("DJANGO_ENV", None)

        # Mock SSM client calls
        fake_ssm = MagicMock()
        fake_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "prod_value"}
        }
        mock_boto_client.return_value = fake_ssm

        result = await get_cached_parameter("TEST_PARAM")
        self.assertEqual(result, "prod_value")

        fake_ssm.get_parameter.assert_called_once_with(
            Name="TEST_PARAM", WithDecryption=True
        )

    @patch("app.utils.ssm_util.cache")
    @patch("app.utils.ssm_util.boto3.client")
    async def test_production_ssm_client_error_raises_exception(
        self, mock_boto_client, mock_cache
    ):
        # Mock the Redis calls
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=None)

        # For production, ensure DJANGO_ENV is not set to "test".
        os.environ.pop("DJANGO_ENV", None)

        fake_ssm = MagicMock()
        error_response = {
            "Error": {
                "Code": "UnrecognizedClientException",
                "Message": "Invalid credentials",
            }
        }
        fake_ssm.get_parameter.side_effect = ClientError(
            error_response, "GetParameter")
        mock_boto_client.return_value = fake_ssm

        with self.assertRaises(Exception) as context:
            await get_cached_parameter("TEST_PARAM")
        self.assertIn("Could not fetch parameter: TEST_PARAM",
                      str(context.exception))
