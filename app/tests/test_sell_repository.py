import json
import unittest
from unittest.mock import MagicMock, patch

from app.repositories.sell_repository import SellRepository, model_to_dict
from app.utils.cache_util_model import CacheModel

# Define a dummy Sell model that simulates an SQLAlchemy model.


class DummySell:
    # Provide a class attribute to mimic a column.
    bill_id = 0

    __table__ = type(
        "Table",
        (),
        {
            "columns": [
                type("Column", (), {"name": "id"}),
                type("Column", (), {"name": "bill_id"}),
            ]
        },
    )

    def __init__(self, id, bill_id):
        self.id = id
        self.bill_id = bill_id

    def __eq__(self, other):
        if isinstance(other, DummySell):
            return self.id == other.id and self.bill_id == other.bill_id
        return False

    def __repr__(self):
        return f"DummySell(id={self.id}, bill_id={self.bill_id})"


class TestSellRepository(unittest.TestCase):
    def setUp(self):
        # Instantiate the repository and override its model with DummySell.
        self.repo = SellRepository()
        self.repo.model = DummySell
        self.cache_model = CacheModel(key="sell_cache_key", expiration=60)
        self.bill_id = 10
        self.fake_sell = DummySell(id=1, bill_id=self.bill_id)

    @patch("app.repositories.sell_repository.cache")
    @patch("app.repositories.sell_repository.SessionLocal")
    def test_find_sells_by_bill_db_hit(self, mock_session_local, mock_cache):
        """
        Test that if the cache is empty, the method queries the DB,
        caches the result, and returns it.
        """
        # Simulate cache miss.
        mock_cache.get.return_value = None

        # Set up a fake session with a query chain.
        fake_session = MagicMock()
        fake_query = MagicMock()
        # Simulate the query returning our fake sell.
        fake_query.all.return_value = [self.fake_sell]
        fake_query_chain = MagicMock()
        # The filter method should be called and return fake_query.
        fake_query_chain.filter.return_value = fake_query
        fake_session.query.return_value = fake_query_chain
        mock_session_local.return_value = fake_session

        # Call the method.
        result = self.repo.find_sells_by_bill(self.bill_id, self.cache_model)

        # Assertions:
        mock_cache.get.assert_called_once_with(self.cache_model.key)
        fake_session.query.assert_called_once_with(self.repo.model)
        # We do not check the exact args here.
        fake_query_chain.filter.assert_called_once()
        fake_query.all.assert_called_once()
        # Check that cache.set was called with the serialized list.
        expected_data = json.dumps([model_to_dict(self.fake_sell)])
        mock_cache.set.assert_called_once_with(
            self.cache_model.key, expected_data, timeout=self.cache_model.expiration
        )
        self.assertEqual(result, [self.fake_sell])
        fake_session.close.assert_called_once()

    @patch("app.repositories.sell_repository.cache")
    @patch("app.repositories.sell_repository.SessionLocal")
    def test_find_sells_by_bill_cache_hit(self, mock_session_local, mock_cache):
        """
        Test that if cache.get returns a JSON list, the repository deserializes
        and returns that list without querying the database.
        """
        dummy_data = {"id": self.fake_sell.id, "bill_id": self.fake_sell.bill_id}
        mock_cache.get.return_value = json.dumps([dummy_data])
        # Even if SessionLocal is patched, its returned session should be closed.
        fake_session = MagicMock()
        mock_session_local.return_value = fake_session

        result = self.repo.find_sells_by_bill(self.bill_id, self.cache_model)
        mock_cache.get.assert_called_once_with(self.cache_model.key)
        fake_session.close.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, self.fake_sell.id)
        self.assertEqual(result[0].bill_id, self.fake_sell.bill_id)
