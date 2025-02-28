import json
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.utils.cache_util_model import CacheModel
from app.repositories.generic_repository import GenericRepository, model_to_dict

# -----------------------------------------------------------------------------
# Dummy SQLAlchemy model for testing
# -----------------------------------------------------------------------------


class DummyModel:
    # Simulate a __table__ with two columns: id and name
    __table__ = type('Table', (), {
        'columns': [
            type('Column', (), {'name': 'id'}),
            type('Column', (), {'name': 'name'}),
        ]
    })

    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name

    def __eq__(self, other):
        if isinstance(other, DummyModel):
            return self.id == other.id and self.name == other.name
        return False

# Create a concrete repository using DummyModel


class DummyRepository(GenericRepository):
    def __init__(self, session: Session):
        super().__init__(DummyModel, session)

# -----------------------------------------------------------------------------
# Unit tests for GenericRepository
# -----------------------------------------------------------------------------


class TestGenericRepository(unittest.TestCase):

    def setUp(self):
        # Create a mock SQLAlchemy session
        self.session = MagicMock(spec=Session)
        # Instantiate our dummy repository with the mock session
        self.repo = DummyRepository(self.session)
        # Create a dummy cache model for tests
        self.cache_model = CacheModel(key="dummy_key", expiration=60)

    # --- Test create_entity ---
    @patch("app.repositories.generic_repository.cache")
    def test_create_entity_success(self, mock_cache):
        # Create dummy entity
        entity = DummyModel(id=1, name="Test")
        # Call create_entity
        result = self.repo.create_entity(entity, self.cache_model)

        # Check that session.add() and session.commit() were called
        self.session.add.assert_called_with(entity)
        self.session.commit.assert_called()

        # Verify that cache.set() was called with the correct serialized data
        expected_data = json.dumps(model_to_dict(entity))
        mock_cache.set.assert_called_with(
            self.cache_model.key, expected_data, timeout=self.cache_model.expiration
        )
        self.assertEqual(result, entity)

    @patch("app.repositories.generic_repository.cache")
    def test_create_entity_exception(self, mock_cache):
        # Create dummy entity
        entity = DummyModel(id=1, name="Test")
        # Simulate an exception during commit
        self.session.commit.side_effect = Exception("DB error")

        result = self.repo.create_entity(entity, self.cache_model)
        # Ensure rollback was called due to exception
        self.session.rollback.assert_called()
        self.assertIsNone(result)
        # Cache should not be set if there is an exception
        mock_cache.set.assert_not_called()

    # --- Test find_entity_by_id ---
    @patch("app.repositories.generic_repository.cache")
    def test_find_entity_by_id_with_cache_hit(self, mock_cache):
        # Simulate a cache hit: prepare a dummy entity and cache its JSON representation
        entity = DummyModel(id=1, name="Cached")
        cache_data = json.dumps(model_to_dict(entity))
        mock_cache.get.return_value = cache_data

        result = self.repo.find_entity_by_id(1, self.cache_model)
        # With a cache hit, session.get should not be called
        self.session.get.assert_not_called()
        self.assertEqual(result, entity)

    @patch("app.repositories.generic_repository.cache")
    def test_find_entity_by_id_cache_miss(self, mock_cache):
        # Simulate cache miss
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

    # --- Test update_entity ---
    @patch("app.repositories.generic_repository.cache")
    def test_update_entity_success(self, mock_cache):
        # Create a dummy query mock that simulates a successful update (1 row updated)
        query_mock = MagicMock()
        query_mock.update.return_value = 1
        # Force find_entity_by_id to return an updated entity
        updated_entity = DummyModel(id=1, name="Updated")
        self.repo.find_entity_by_id = MagicMock(return_value=updated_entity)

        # Setup the query chain: session.query(...).filter_by(id=1) returns query_mock
        self.session.query.return_value.filter_by.return_value = query_mock

        updated_data = {"name": "Updated"}
        result = self.repo.update_entity(1, updated_data, self.cache_model)
        query_mock.update.assert_called_with(updated_data)
        self.session.commit.assert_called()
        self.repo.find_entity_by_id.assert_called_with(1)

        expected_data = json.dumps(model_to_dict(updated_entity))
        mock_cache.set.assert_called_with(
            self.cache_model.key, expected_data, timeout=self.cache_model.expiration
        )
        self.assertEqual(result, updated_entity)

    @patch("app.repositories.generic_repository.cache")
    def test_update_entity_not_found(self, mock_cache):
        # Simulate update returning 0 rows updated
        query_mock = MagicMock()
        query_mock.update.return_value = 0
        self.session.query.return_value.filter_by.return_value = query_mock

        updated_data = {"name": "Updated"}
        result = self.repo.update_entity(1, updated_data, self.cache_model)
        self.session.rollback.assert_called()
        self.assertIsNone(result)

    # --- Test delete_entity ---
    @patch("app.repositories.generic_repository.cache")
    def test_delete_entity_success(self, mock_cache):
        query_mock = MagicMock()
        query_mock.delete.return_value = 1
        self.session.query.return_value.filter_by.return_value = query_mock

        result = self.repo.delete_entity(1, self.cache_model)
        query_mock.delete.assert_called()
        self.session.commit.assert_called()
        mock_cache.delete.assert_called_with(self.cache_model.key)
        self.assertTrue(result)

    @patch("app.repositories.generic_repository.cache")
    def test_delete_entity_not_found(self, mock_cache):
        query_mock = MagicMock()
        query_mock.delete.return_value = 0
        self.session.query.return_value.filter_by.return_value = query_mock

        result = self.repo.delete_entity(1, self.cache_model)
        self.session.rollback.assert_called()
        self.assertFalse(result)

    # --- Test get_all_entities ---
    @patch("app.repositories.generic_repository.cache")
    def test_get_all_entities_with_cache_hit(self, mock_cache):
        # Simulate cache hit: cache a list containing one entity's dict
        entity = DummyModel(id=1, name="Test")
        cache_data = json.dumps([model_to_dict(entity)])
        mock_cache.get.return_value = cache_data

        result = self.repo.get_all_entities(self.cache_model)
        # The method should deserialize the cached JSON into a DummyModel instance
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
        # Simulate a cache hit for pagination results
        pagination_data = {
            "data": [model_to_dict(DummyModel(id=1, name="Test"))],
            "count": 1
        }
        mock_cache.get.return_value = json.dumps(pagination_data)
        result = self.repo.get_entities_with_pagination(
            0, 10, self.cache_model)
        self.assertEqual(result, pagination_data)

    @patch("app.repositories.generic_repository.cache")
    def test_get_entities_with_pagination_cache_miss(self, mock_cache):
        mock_cache.get.return_value = None

        # Create a query mock to simulate count and pagination
        query_mock = MagicMock()
        query_mock.count.return_value = 1

        # Simulate the chain query.offset(...).limit(...).all() returning one entity.
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
        # Verify that the result contains the list of entities and the count.
        self.assertEqual(result, {"data": [dummy_instance], "count": 1})
