import json
import unittest
from unittest.mock import MagicMock, patch

from app.repositories.user_repository import UserRepository
from app.models import User
from app.utils.cache_util_model import CacheModel


class DummyUser:
    """
    A dummy user class that mimics the expected attributes and accepts keyword arguments.
    This will be used as the return value for deserialize_instance and as our dummy user.
    """

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.username = kwargs.get("username")
        self.email = kwargs.get("email")

    def __eq__(self, other):
        if isinstance(other, DummyUser):
            return (
                self.id == other.id and
                self.username == other.username and
                self.email == other.email
            )
        return False


class TestUserRepository(unittest.TestCase):
    def setUp(self):
        self.repo = UserRepository()
        self.cache_model = CacheModel(key="user_cache_key", expiration=60)
        self.username = "testuser"
        self.user_dict = {
            "id": 1,
            "username": self.username,
            "email": "test@example.com",
        }
        # Prepare a dummy user instance that matches user_dict.
        self.dummy_user = DummyUser(**self.user_dict)

    @patch("app.repositories.user_repository.deserialize_instance")
    @patch("app.repositories.user_repository.cache")
    @patch("app.repositories.user_repository.SessionLocal")
    def test_find_user_by_username_cache_hit(
        self, mock_session_local, mock_cache, mock_deserialize_instance
    ):
        """
        When the cache returns a value, the repository should use deserialize_instance
        to create and return a user, and the database query should not affect the outcome.
        """
        # Prepare cached data as JSON.
        cached_data = json.dumps(self.user_dict)
        mock_cache.get.return_value = cached_data

        # Configure deserialize_instance to return a DummyUser instance.
        mock_deserialize_instance.side_effect = lambda model, data: DummyUser(
            **data)

        # Even if SessionLocal is patched, its returned session should be closed.
        fake_session = MagicMock()
        mock_session_local.return_value = fake_session

        # Call the method.
        result = self.repo.find_user_by_username(
            self.username, self.cache_model)

        # Assert that cache.get was called.
        mock_cache.get.assert_called_with(self.cache_model.key)
        # Assert that SessionLocal was called.
        mock_session_local.assert_called_once()
        # Ensure that the session is closed even if we return from cache.
        fake_session.close.assert_called_once()

        # Check that deserialize_instance was called with the correct arguments.
        mock_deserialize_instance.assert_called_with(
            self.repo.model, self.user_dict)

        # The returned user should have the same attributes as in user_dict.
        self.assertEqual(result.id, self.user_dict["id"])
        self.assertEqual(result.username, self.user_dict["username"])
        self.assertEqual(result.email, self.user_dict["email"])

    @patch("app.repositories.user_repository.cache")
    @patch("app.repositories.user_repository.SessionLocal")
    def test_find_user_by_username_cache_miss(self, mock_session_local, mock_cache):
        """
        When the cache misses, the repository should query the database,
        cache the result, and return the user.
        """
        # Simulate cache miss.
        mock_cache.get.return_value = None

        # --- WORKAROUND for missing `username` attribute on the User model ---
        # Add a dummy attribute so that `self.model.username` exists.
        setattr(self.repo.model, "username", MagicMock())
        # -----------------------------------------------------------------------

        # Create a fake session and set up the query chain.
        fake_session = MagicMock()
        fake_query = MagicMock()
        fake_query.first.return_value = self.dummy_user
        # When query() is called with self.repo.model, return a mock that has filter().
        fake_query_chain = MagicMock()
        fake_query_chain.filter.return_value = fake_query
        fake_session.query.return_value = fake_query_chain
        mock_session_local.return_value = fake_session

        # Call the method.
        result = self.repo.find_user_by_username(
            self.username, self.cache_model)

        # Assert that a session was created and the query was executed.
        mock_session_local.assert_called_once()
        fake_session.query.assert_called_with(self.repo.model)
        # Assert that filter was called at least once.
        fake_query_chain.filter.assert_called()
        fake_query.first.assert_called_once()

        # Assert that cache.set was called with the correct parameters.
        expected_cache_data = json.dumps(self.user_dict, default=str)
        mock_cache.set.assert_called_with(
            self.cache_model.key, expected_cache_data, timeout=self.cache_model.expiration
        )

        # The returned user should match our dummy user.
        self.assertEqual(result, self.dummy_user)
        # Ensure that the session is closed.
        fake_session.close.assert_called_once()

    @patch("app.repositories.user_repository.cache")
    @patch("app.repositories.user_repository.SessionLocal")
    def test_find_user_by_username_not_found(self, mock_session_local, mock_cache):
        """
        If the user is not found in the database, the method should log a warning
        and return None.
        """
        # Simulate cache miss.
        mock_cache.get.return_value = None

        # Create a fake session with a query that returns None.
        fake_session = MagicMock()
        fake_query = MagicMock()
        fake_query.first.return_value = None
        fake_query_chain = MagicMock()
        fake_query_chain.filter.return_value = fake_query
        fake_session.query.return_value = fake_query_chain
        mock_session_local.return_value = fake_session

        # Call the method. It should catch the exception and return None.
        result = self.repo.find_user_by_username(
            self.username, self.cache_model)

        self.assertIsNone(result)
        fake_session.close.assert_called_once()

    @patch("app.repositories.user_repository.cache")
    @patch("app.repositories.user_repository.SessionLocal")
    def test_find_user_by_username_exception(self, mock_session_local, mock_cache):
        """
        Simulate an exception (e.g., a query error) during the database query,
        ensuring the method returns None and the session is closed.
        """
        mock_cache.get.return_value = None

        # Create a fake session that raises an exception when query is called.
        fake_session = MagicMock()
        fake_session.query.side_effect = Exception("Database error")
        mock_session_local.return_value = fake_session

        result = self.repo.find_user_by_username(
            self.username, self.cache_model)

        self.assertIsNone(result)
        fake_session.close.assert_called_once()
