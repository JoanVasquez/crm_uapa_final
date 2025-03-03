import json
import unittest
from unittest.mock import MagicMock, patch

from app.errors import BaseAppException, ResourceNotFoundError
from app.repositories.user_repository import UserRepository
from app.utils.cache_util_model import CacheModel


class DummyUser:
    """
    A dummy user class that mimics the expected attributes.
    """

    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    def __eq__(self, other):
        if isinstance(other, DummyUser):
            return (
                self.id == other.id
                and self.username == other.username
                and self.email == other.email
            )
        return False


class TestUserRepository(unittest.TestCase):
    def setUp(self):
        # Instantiate the repository.
        self.repo = UserRepository()
        # Create a cache model for testing.
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
        to create and return a user, and the database query should not be triggered.
        """
        cached_data = json.dumps(self.user_dict)
        mock_cache.get.return_value = cached_data

        # Configure deserialize_instance to return our dummy user.
        mock_deserialize_instance.side_effect = lambda model, data: DummyUser(**data)

        fake_session = MagicMock()
        mock_session_local.return_value = fake_session

        result = self.repo.find_user_by_username(self.username, self.cache_model)

        mock_cache.get.assert_called_with(self.cache_model.key)
        mock_session_local.assert_called_once()
        fake_session.close.assert_called_once()
        mock_deserialize_instance.assert_called_with(self.repo.model, self.user_dict)
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
        mock_cache.get.return_value = None

        # WORKAROUND: Ensure that the model has a 'username' attribute.
        setattr(self.repo.model, "username", MagicMock())

        fake_session = MagicMock()
        fake_query = MagicMock()
        fake_query.first.return_value = self.dummy_user
        fake_query_chain = MagicMock()
        fake_query_chain.filter.return_value = fake_query
        fake_session.query.return_value = fake_query_chain
        mock_session_local.return_value = fake_session

        result = self.repo.find_user_by_username(self.username, self.cache_model)

        mock_session_local.assert_called_once()
        fake_session.query.assert_called_with(self.repo.model)
        # We don't specify exact args here.
        fake_query_chain.filter.assert_called()
        fake_query.first.assert_called_once()

        expected_cache_data = json.dumps(self.user_dict, default=str)
        mock_cache.set.assert_called_with(
            self.cache_model.key,
            expected_cache_data,
            timeout=self.cache_model.expiration,
        )
        self.assertEqual(result, self.dummy_user)
        fake_session.close.assert_called_once()

    @patch("app.repositories.user_repository.cache")
    @patch("app.repositories.user_repository.SessionLocal")
    def test_find_user_by_username_not_found(self, mock_session_local, mock_cache):
        """
        If the user is not found in the database, the repository should raise a
        ResourceNotFoundError.
        """
        mock_cache.get.return_value = None

        fake_session = MagicMock()
        fake_query = MagicMock()
        fake_query.first.return_value = None
        fake_query_chain = MagicMock()
        fake_query_chain.filter.return_value = fake_query
        fake_session.query.return_value = fake_query_chain
        mock_session_local.return_value = fake_session

        with self.assertRaises(ResourceNotFoundError) as context:
            self.repo.find_user_by_username(self.username, self.cache_model)
        fake_session.close.assert_called_once()
        self.assertIn(
            f"User with username {self.username} not found", str(context.exception)
        )

    @patch("app.repositories.user_repository.cache")
    @patch("app.repositories.user_repository.SessionLocal")
    def test_find_user_by_username_exception(self, mock_session_local, mock_cache):
        """
        Simulate an exception (e.g., a query error) during the database query,
        ensuring that a BaseAppException is raised and the session is closed.
        """
        mock_cache.get.return_value = None

        fake_session = MagicMock()
        fake_session.query.side_effect = Exception("Database error")
        mock_session_local.return_value = fake_session

        with self.assertRaises(BaseAppException) as context:
            self.repo.find_user_by_username(self.username, self.cache_model)
        self.assertIn("Error finding user by username", str(context.exception))
        fake_session.close.assert_called_once()
