"""Tests for GenericService.

This module contains unit tests for the GenericService class.
"""

import unittest
from unittest.mock import MagicMock, patch

from app.repositories.generic_repository import GenericRepository
from app.services.generic_service import GenericService
from app.utils.cache_util_model import CacheModel


class FakeEntity:
    """A minimal fake entity for testing purposes."""

    def __init__(self, entity_id, name):
        self.id = entity_id
        self.name = name

    def __str__(self):
        return f"FakeEntity(id={self.id}, name={self.name})"


class TestGenericService(unittest.TestCase):
    """Tests for the GenericService class."""

    def setUp(self):
        """Set up a mock repository and a GenericService instance for testing."""
        self.mock_repo = MagicMock(spec=GenericRepository)
        self.service = GenericService(self.mock_repo)
        self.fake_entity = FakeEntity(1, "TestName")
        self.cache_model = CacheModel(key="fake_key", expiration=60)

    @patch("app.services.generic_service.logger")
    def test_save_success(self, mock_logger):
        """Test that save() creates an entity via the repository successfully."""
        self.mock_repo.create_entity.return_value = self.fake_entity
        result = self.service.save(self.fake_entity, self.cache_model)
        self.mock_repo.create_entity.assert_called_once_with(
            self.fake_entity, self.cache_model
        )
        self.assertEqual(result, self.fake_entity)
        mock_logger.info.assert_called()

    @patch("app.services.generic_service.logger")
    def test_find_by_id_success(self, mock_logger):
        """Test that find_by_id() returns the entity when it exists."""
        self.mock_repo.find_entity_by_id.return_value = self.fake_entity
        result = self.service.find_by_id(123, self.cache_model)
        self.mock_repo.find_entity_by_id.assert_called_once_with(123, self.cache_model)
        self.assertEqual(result, self.fake_entity)
        mock_logger.info.assert_called()

    @patch("app.services.generic_service.logger")
    def test_update_success(self, mock_logger):
        """Test that update() returns the updated entity."""
        updated_entity = FakeEntity(1, "UpdatedName")
        self.mock_repo.update_entity.return_value = updated_entity
        result = self.service.update(1, {"name": "UpdatedName"}, self.cache_model)
        self.mock_repo.update_entity.assert_called_once_with(
            1, {"name": "UpdatedName"}, self.cache_model
        )
        self.assertEqual(result, updated_entity)
        mock_logger.info.assert_called()

    @patch("app.services.generic_service.logger")
    def test_delete_success(self, mock_logger):
        """Test that delete() returns True when deletion is successful."""
        self.mock_repo.delete_entity.return_value = True
        result = self.service.delete(999, self.cache_model)
        self.mock_repo.delete_entity.assert_called_once_with(999, self.cache_model)
        self.assertTrue(result)
        mock_logger.info.assert_called()

    @patch("app.services.generic_service.logger")
    def test_find_all(self, mock_logger):
        """Test that find_all() returns all entities."""
        fake_list = [FakeEntity(1, "One"), FakeEntity(2, "Two")]
        self.mock_repo.get_all_entities.return_value = fake_list
        result = self.service.find_all(self.cache_model)
        self.mock_repo.get_all_entities.assert_called_once_with(self.cache_model)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "One")
        mock_logger.info.assert_called()

    @patch("app.services.generic_service.logger")
    def test_find_with_pagination(self, mock_logger):
        """Test that find_with_pagination() returns the expected paginated result."""
        paginated_result = {
            "data": [FakeEntity(10, "Ten"), FakeEntity(20, "Twenty")],
            "count": 2,
        }
        self.mock_repo.get_entities_with_pagination.return_value = paginated_result
        result = self.service.find_with_pagination(5, 10, self.cache_model)
        self.mock_repo.get_entities_with_pagination.assert_called_once_with(
            5, 10, self.cache_model
        )
        self.assertIn("data", result)
        self.assertIn("count", result)
        mock_logger.info.assert_called()
