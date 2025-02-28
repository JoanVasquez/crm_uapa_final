import json
import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.errors import BaseAppException, ResourceNotFoundError
from app.repositories.generic_repository import GenericRepository, model_to_dict
from app.utils.cache_util_model import CacheModel

# -----------------------------------------------------------------------------
# Dummy SQLAlchemy model for testing
# -----------------------------------------------------------------------------


class DummyColumn:
    def __init__(self, name):
        self.name = name


class DummyTable:
    @property
    def columns(self):
        return [DummyColumn("id"), DummyColumn("name")]


class DummyModel:
    __table__ = DummyTable()

    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name

    def __eq__(self, other):
        if isinstance(other, DummyModel):
            return self.id == other.id and self.name == other.name
        return False

    def __repr__(self):
        return f"DummyModel(id={self.id}, name={self.name})"

# -----------------------------------------------------------------------------
# Dummy Repository that extends GenericRepository
# -----------------------------------------------------------------------------


class DummyRepository(GenericRepository):
    def __init__(self, session: Session):
        super().__init__(DummyModel, session)

# -----------------------------------------------------------------------------
# Unit tests for GenericRepository with custom errors
# -----------------------------------------------------------------------------


class TestGenericRepository(unittest.TestCase):

    def setUp(self):
        # Create a fake session that conforms to Session
        self.session = MagicMock(spec=Session)
        self.repo = DummyRepository(self.session)
        self.cache_model = CacheModel(key="dummy_key", expiration=60)

    # --- Test create_entity ---
    @patch("app.repositories.generic_repository.cache")
    def test_create_entity_success(self, mock_cache):
        entity = DummyModel(id=1, name="Test")
        result = self.repo.create_entity(entity, self.cache_model)
        self.session.add.assert_called_with(entity)
        self.session.commit.assert_called_once()
        expected_data = json.dumps(model_to_dict(entity))
        mock_cache.set.assert_called_with(
            self.cache_model.key, expected_data, timeout=self.cache_model.expiration
        )
        self.assertEqual(result, entity)

    @patch("app.repositories.generic_repository.cache")
    def test_create_entity_exception(self, mock_cache):
        entity = DummyModel(id=1, name="Test")
        self.session.commit.side_effect = Exception("DB error")
        with self.assertRaises(BaseAppException) as cm:
            self.repo.create_entity(entity, self.cache_model)
        self.session.rollback.assert_called_once()
        mock_cache.set.assert_not_called()
        self.assertEqual(cm.exception.message, "Error creating entity")
        self.assertEqual(cm.exception.details, "DB error")

    # --- Test find_entity_by_id ---
    @patch("app.repositories.generic_repository.cache")
    def test_find_entity_by_id_with_cache_hit(self, mock_cache):
        entity = DummyModel(id=1, name="Cached")
        cache_data = json.dumps(model_to_dict(entity))
        mock_cache.get.return_value = cache_data

        result = self.repo.find_entity_by_id(1, self.cache_model)
        mock_cache.get.assert_called_once_with(self.cache_model.key)
        self.session.get.assert_not_called()
        self.assertEqual(result, entity)

    @patch("app.repositories.generic_repository.cache")
    def test_find_entity_by_id_cache_miss(self, mock_cache):
        mock_cache.get.return_value = None
        entity = DummyModel(id=1, name="DB")
        self.session.get.return_value = entity

        result = self.repo.find_entity_by_id(1, self.cache_model)
        self.session.get.assert_called_with(DummyModel, 1)
        expected_data = json.dumps(model_to_dict(entity))
        mock_cache.set.assert_called_with(
            self.cache_model.key, expected_data, timeout=self.cache_model.expiration
        )
        self.assertEqual(result, entity)

    @patch("app.repositories.generic_repository.cache")
    def test_find_entity_by_id_not_found(self, mock_cache):
        mock_cache.get.return_value = None
        self.session.get.return_value = None
        with self.assertRaises(ResourceNotFoundError) as cm:
            self.repo.find_entity_by_id(1, self.cache_model)
        self.assertIn("Entity with id 1 not found", str(cm.exception))

    # --- Test update_entity ---
    @patch("app.repositories.generic_repository.cache")
    def test_update_entity_success(self, mock_cache):
        query_mock = MagicMock()
        query_mock.update.return_value = 1
        updated_entity = DummyModel(id=1, name="Updated")
        # Stub find_entity_by_id to return updated_entity.
        self.repo.find_entity_by_id = MagicMock(return_value=updated_entity)
        self.session.query.return_value.filter_by.return_value = query_mock

        updated_data = {"name": "Updated"}
        result = self.repo.update_entity(1, updated_data, self.cache_model)
        query_mock.update.assert_called_with(updated_data)
        self.session.commit.assert_called_once()
        self.repo.find_entity_by_id.assert_called_with(1)
        expected_data = json.dumps(model_to_dict(updated_entity))
        mock_cache.set.assert_called_with(
            self.cache_model.key, expected_data, timeout=self.cache_model.expiration
        )
        self.assertEqual(result, updated_entity)

    @patch("app.repositories.generic_repository.cache")
    def test_update_entity_not_found(self, mock_cache):
        query_mock = MagicMock()
        query_mock.update.return_value = 0
        self.session.query.return_value.filter_by.return_value = query_mock

        updated_data = {"name": "Updated"}
        with self.assertRaises(ResourceNotFoundError) as cm:
            self.repo.update_entity(1, updated_data, self.cache_model)
        self.session.rollback.assert_called_once()
        self.assertIn("Entity with id 1 not found", str(cm.exception))

    # --- Test delete_entity ---
    @patch("app.repositories.generic_repository.cache")
    def test_delete_entity_success(self, mock_cache):
        query_mock = MagicMock()
        query_mock.delete.return_value = 1
        self.session.query.return_value.filter_by.return_value = query_mock

        result = self.repo.delete_entity(1, self.cache_model)
        query_mock.delete.assert_called()
        self.session.commit.assert_called_once()
        mock_cache.delete.assert_called_with(self.cache_model.key)
        self.assertTrue(result)

        @patch("app.repositories.generic_repository.cache")
        def test_delete_entity_not_found(self, mock_cache):
            query_mock = MagicMock()
            query_mock.delete.return_value = 0
            self.session.query.return_value.filter_by.return_value = query_mock

            with self.assertRaises(ResourceNotFoundError) as cm:
                self.repo.delete_entity(1, self.cache_model)
            self.session.rollback.assert_called_once()
            self.assertIn("Entity with id 1 not found", str(cm.exception))

    # --- Test get_all_entities ---

    @patch("app.repositories.generic_repository.cache")
    def test_get_all_entities_with_cache_hit(self, mock_cache):
        entity = DummyModel(id=1, name="Test")
        cache_data = json.dumps([model_to_dict(entity)])
        mock_cache.get.return_value = cache_data

        result = self.repo.get_all_entities(self.cache_model)
        self.assertEqual(result, [entity])

    @patch("app.repositories.generic_repository.cache")
    def test_get_all_entities_cache_miss(self, mock_cache):
        mock_cache.get.return_value = None
        entity = DummyModel(id=1, name="Test")
        self.session.query.return_value.all.return_value = [entity]

        result = self.repo.get_all_entities(self.cache_model)
        expected_data = json.dumps([model_to_dict(entity)])
        mock_cache.set.assert_called_with(
            self.cache_model.key, expected_data, timeout=self.cache_model.expiration
        )
        self.assertEqual(result, [entity])

    # --- Test get_entities_with_pagination ---
    @patch("app.repositories.generic_repository.cache")
    def test_get_entities_with_pagination_with_cache_hit(self, mock_cache):
        pagination_data = {"data": [model_to_dict(
            DummyModel(id=1, name="Test"))], "count": 1}
        mock_cache.get.return_value = json.dumps(pagination_data)
        result = self.repo.get_entities_with_pagination(
            0, 10, self.cache_model)
        self.assertEqual(result, pagination_data)

    @patch("app.repositories.generic_repository.cache")
    def test_get_entities_with_pagination_cache_miss(self, mock_cache):
        mock_cache.get.return_value = None
        query_mock = MagicMock()
        query_mock.count.return_value = 1
        dummy_instance = DummyModel(id=1, name="Test")
        offset_mock = MagicMock()
        limit_mock = MagicMock()
        limit_mock.all.return_value = [dummy_instance]
        offset_mock.limit.return_value = limit_mock
        query_mock.offset.return_value = offset_mock
        self.session.query.return_value = query_mock

        result = self.repo.get_entities_with_pagination(
            0, 10, self.cache_model)
        expected_data_list = [model_to_dict(dummy_instance)]
        expected_cache_data = json.dumps(
            {"data": expected_data_list, "count": 1})
        mock_cache.set.assert_called_with(
            self.cache_model.key, expected_cache_data, timeout=self.cache_model.expiration
        )
        self.assertEqual(result, {"data": [dummy_instance], "count": 1})
