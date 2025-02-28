import json
import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.user_service import UserService

# Define a FakeUser that accepts a "username" keyword (mapping it to "name")


class FakeUser:
    def __init__(self, **kwargs):
        # Accept "username" and use it as the name.
        self.id = kwargs.get("id", 1)
        self.name = kwargs.get("username") or kwargs.get("name")
        self.password = kwargs.get("password")
        self.email = kwargs.get("email")

    def __eq__(self, other):
        return (
            isinstance(other, FakeUser)
            and self.id == other.id
            and self.name == other.name
            and self.password == other.password
            and self.email == other.email
        )

    def __repr__(self):
        return f"FakeUser(id={self.id}, name={self.name})"


class TestUserService(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch external dependencies inside the user_service module.
        patcher_auth = patch(
            "app.services.user_service.AuthenticationService", autospec=True)
        patcher_pass = patch(
            "app.services.user_service.PasswordService", autospec=True)
        patcher_repo = patch(
            "app.services.user_service.UserRepository", autospec=True)
        patcher_cache = patch("app.services.user_service.cache")
        patcher_validator = patch(
            "app.services.user_service.reset_password_input_validator")
        patcher_user = patch("app.services.user_service.User", new=FakeUser)

        self.mock_auth_cls = patcher_auth.start()
        self.mock_pass_cls = patcher_pass.start()
        self.mock_repo_cls = patcher_repo.start()
        self.mock_cache = patcher_cache.start()
        self.mock_validator = patcher_validator.start()
        self.mock_user_cls = patcher_user.start()

        self.addCleanup(patcher_auth.stop)
        self.addCleanup(patcher_pass.stop)
        self.addCleanup(patcher_repo.stop)
        self.addCleanup(patcher_cache.stop)
        self.addCleanup(patcher_validator.stop)
        self.addCleanup(patcher_user.stop)

        # Create instance mocks for the patched classes.
        self.mock_auth = MagicMock()
        self.mock_pass = MagicMock()
        self.mock_repo = MagicMock()

        self.mock_auth_cls.return_value = self.mock_auth
        self.mock_pass_cls.return_value = self.mock_pass
        self.mock_repo_cls.return_value = self.mock_repo

        # Instantiate UserService under test.
        self.user_service = UserService()
        # Override its repository with our patched repository.
        self.user_service.user_repository = self.mock_repo

        # Test data.
        self.test_email = "test@example.com"
        self.test_username = "testuser"
        self.test_password = "secret123"
        self.fake_user = FakeUser(id=1, username=self.test_username,
                                  password=self.test_password, email=self.test_email)

    # ----- Test: save() -----
    async def test_save_success(self):
        """Test that save() registers the user, encrypts the password,
        and creates the user in the repository."""
        self.mock_auth.register_user = AsyncMock(return_value=None)
        # Simulate get_password_encrypted returning a plain string.
        self.mock_pass.get_password_encrypted.return_value = "encrypted-pass"
        self.mock_repo.create_entity.return_value = self.fake_user

        # Create a dummy input. Here, we simulate an object with the expected attributes.
        DummyUser = type("DummyUser", (), {
            "username": self.test_username,
            "password": self.test_password,
            "email": self.test_email
        })
        user_input = DummyUser()

        result = await self.user_service.save(user_input)
        self.mock_auth.register_user.assert_awaited_once_with(
            self.test_username, self.test_password, self.test_email
        )
        self.mock_pass.get_password_encrypted.assert_called_once_with(
            self.test_password)
        self.mock_repo.create_entity.assert_called_once()
        self.assertEqual(result, self.fake_user)

    async def test_save_failure_auth(self):
        """Test that if register_user fails, save() raises 'Registration failed'."""
        self.mock_auth.register_user = AsyncMock(
            side_effect=Exception("Auth error"))
        DummyUser = type("DummyUser", (), {
            "username": self.test_username,
            "password": self.test_password,
            "email": self.test_email
        })
        user_input = DummyUser()
        with self.assertRaises(Exception) as ctx:
            await self.user_service.save(user_input)
        self.assertIn("Registration failed", str(ctx.exception))

    # ----- Test: confirm_registration() -----
    async def test_confirm_registration_success(self):
        fake_response = {"message": "User confirmed successfully"}
        self.mock_auth.confirm_user_registration = AsyncMock(
            return_value=fake_response)
        result = await self.user_service.confirm_registration(self.test_email, "123456")
        self.mock_auth.confirm_user_registration.assert_awaited_once_with(
            self.test_email, "123456")
        self.assertEqual(result, fake_response)

    async def test_confirm_registration_failure(self):
        self.mock_auth.confirm_user_registration = AsyncMock(
            side_effect=Exception("Confirm error"))
        with self.assertRaises(Exception) as ctx:
            await self.user_service.confirm_registration(self.test_email, "000000")
        self.assertIn("User confirmation failed", str(ctx.exception))

    # ----- Test: authenticate() -----
    async def test_authenticate_success_in_cache(self):
        """Test that if the user is found in cache, the repository is not queried."""
        self.mock_auth.authenticate_user = AsyncMock(return_value="fake-jwt")
        # Simulate cache returning a JSON representation of a user.
        cached_user = {"id": 1, "name": self.test_username,
                       "password": "encrypted-pass", "email": self.test_email}
        self.mock_cache.get = AsyncMock(return_value=json.dumps(cached_user))
        self.mock_cache.set = AsyncMock()
        self.mock_repo.find_user_by_username = MagicMock()

        result = await self.user_service.authenticate(self.test_email, self.test_password)
        self.mock_auth.authenticate_user.assert_awaited_once_with(
            self.test_email, self.test_password)
        self.mock_repo.find_user_by_username.assert_not_called()
        self.mock_cache.set.assert_not_awaited()
        self.assertEqual(result, {"token": "fake-jwt"})

    async def test_authenticate_success_not_in_cache(self):
        """Test that if cache returns None, the repository is used and then the user is cached."""
        self.mock_auth.authenticate_user = AsyncMock(return_value="fake-jwt")
        self.mock_cache.get = AsyncMock(return_value=None)
        self.mock_cache.set = AsyncMock()
        self.mock_repo.find_user_by_username.return_value = self.fake_user

        result = await self.user_service.authenticate(self.test_email, self.test_password)
        self.mock_auth.authenticate_user.assert_awaited_once_with(
            self.test_email, self.test_password)
        self.mock_repo.find_user_by_username.assert_called_once_with(
            self.test_email)
        self.mock_cache.set.assert_awaited_once()
        self.assertEqual(result, {"token": "fake-jwt"})

    async def test_authenticate_failure_no_user(self):
        """Test that if no user is found in cache or repository, an exception is raised."""
        self.mock_auth.authenticate_user = AsyncMock(return_value="fake-jwt")
        self.mock_cache.get = AsyncMock(return_value=None)
        self.mock_repo.find_user_by_username.return_value = None

        with self.assertRaises(Exception) as ctx:
            await self.user_service.authenticate(self.test_email, self.test_password)
        self.assertIn(
            "Authentication failed: Invalid username or password", str(ctx.exception))

    # ----- Test: initiate_password_reset() -----
    async def test_initiate_password_reset_success(self):
        self.mock_pass.initiate_user_password_reset = AsyncMock(
            return_value="OK")
        result = await self.user_service.initiate_password_reset(self.test_email)
        self.mock_pass.initiate_user_password_reset.assert_awaited_once_with(
            self.test_email)
        self.assertIn("Password reset initiated", result["message"])

    async def test_initiate_password_reset_failure(self):
        self.mock_pass.initiate_user_password_reset = AsyncMock(
            side_effect=Exception("Reset error"))
        with self.assertRaises(Exception) as ctx:
            await self.user_service.initiate_password_reset(self.test_email)
        self.assertIn("Failed to initiate password reset", str(ctx.exception))

    # ----- Test: complete_password_reset() -----
    async def test_complete_password_reset_success(self):
        """
        Test that complete_password_reset validates input, calls the password service,
        gets an encrypted password, finds the user via the repository, updates it,
        and returns a success message.
        """
        self.mock_validator.return_value = None  # Validator passes.
        self.mock_pass.complete_user_password_reset = AsyncMock(
            return_value="OK")
        self.mock_pass.get_password_encrypted.return_value = "encrypted-new"
        self.mock_repo.find_user_by_username.return_value = self.fake_user
        self.mock_repo.update_entity.return_value = self.fake_user

        result = await self.user_service.complete_password_reset(self.test_email, "NewPass", "111111")
        self.mock_pass.complete_user_password_reset.assert_awaited_once_with(
            self.test_email, "NewPass", "111111")
        self.mock_pass.get_password_encrypted.assert_called_once_with(
            "NewPass")
        self.mock_repo.find_user_by_username.assert_called_once_with(
            self.test_email)
        self.mock_repo.update_entity.assert_called_once_with(
            self.fake_user.id, {"password": "encrypted-new"})
        self.assertIn("Password reset successfully completed",
                      result["message"])

    async def test_complete_password_reset_failure_no_user(self):
        self.mock_pass.complete_user_password_reset = AsyncMock(
            return_value="OK")
        self.mock_repo.find_user_by_username.return_value = None
        with self.assertRaises(Exception) as ctx:
            await self.user_service.complete_password_reset(self.test_email, "NewPass", "654321")
        self.assertIn("Failed to complete password reset", str(ctx.exception))

    async def test_complete_password_reset_failure_validator(self):
        from app.services.user_service import reset_password_input_validator
        self.mock_validator.side_effect = ValueError("Invalid input")
        with self.assertRaises(Exception) as ctx:
            await self.user_service.complete_password_reset(self.test_email, "NewPass", "654321")
        self.assertIn("Failed to complete password reset", str(ctx.exception))
