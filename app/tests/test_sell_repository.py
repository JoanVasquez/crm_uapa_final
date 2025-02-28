import json
import unittest
from unittest.mock import MagicMock, patch

# Create dummy column and table objects for FakeSell.


class DummyColumn:
    def __init__(self, name):
        self.name = name


class FakeTable:
    @property
    def columns(self):
        return [
            DummyColumn("id"),
            DummyColumn("bill_id"),
            DummyColumn("product_id"),
            DummyColumn("quantity"),
            DummyColumn("sale_price")
        ]

# Define a FakeSell model that simulates the Sell model.


class FakeSell:
    __table__ = FakeTable()

    def __init__(self, id, bill_id, product_id, quantity, sale_price):
        self.id = id
        self.bill_id = bill_id
        self.product_id = product_id
        self.quantity = quantity
        self.sale_price = sale_price

    def __eq__(self, other):
        return (
            isinstance(other, FakeSell)
            and self.id == other.id
            and self.bill_id == other.bill_id
            and self.product_id == other.product_id
            and self.quantity == other.quantity
            and float(self.sale_price) == float(other.sale_price)
        )

    def __repr__(self):
        return f"FakeSell(id={self.id}, bill_id={self.bill_id})"


class TestSellRepository(unittest.TestCase):
    def setUp(self):
        # Import the repository class.
        from app.repositories.sell_repository import SellRepository
        self.repo = SellRepository()

        # Patch the SessionLocal so that a fake session is used.
        session_patcher = patch(
            "app.repositories.sell_repository.SessionLocal")
        self.mock_session_local = session_patcher.start()
        self.addCleanup(session_patcher.stop)

        self.fake_session = MagicMock()
        self.mock_session_local.return_value = self.fake_session

        # Patch the global cache in the repository module.
        cache_patcher = patch("app.repositories.sell_repository.cache")
        self.mock_cache = cache_patcher.start()
        self.addCleanup(cache_patcher.stop)

        # Set up a fake Sell instance.
        self.fake_sell = FakeSell(
            id=1,
            bill_id=10,
            product_id=5,
            quantity=2,
            sale_price=9.99
        )
        self.bill_id = 10
        # Create a CacheModel instance (for example purposes).
        from app.utils.cache_util_model import CacheModel
        self.cache_model = CacheModel(
            key=f"sell_bill_{self.bill_id}", expiration=300)

    def test_find_sells_by_bill_cache_hit(self):
        """
        If cache.get returns a JSON list, the repository should deserialize
        the list and return Sell instances without performing a DB query.
        """
        # Prepare a dictionary for the fake sell.
        sell_data = {
            "id": self.fake_sell.id,
            "bill_id": self.fake_sell.bill_id,
            "product_id": self.fake_sell.product_id,
            "quantity": self.fake_sell.quantity,
            "sale_price": float(self.fake_sell.sale_price)
        }
        # Simulate a cache hit.
        self.mock_cache.get.return_value = json.dumps([sell_data])

        result = self.repo.find_sells_by_bill(self.bill_id, self.cache_model)

        self.mock_cache.get.assert_called_once_with(self.cache_model.key)
        # When cache is hit, no DB query should occur.
        self.fake_session.query.assert_not_called()
        self.assertEqual(len(result), 1)
        sell = result[0]
        self.assertEqual(sell.id, self.fake_sell.id)
        self.assertEqual(sell.bill_id, self.fake_sell.bill_id)
        self.assertEqual(sell.product_id, self.fake_sell.product_id)
        self.assertEqual(sell.quantity, self.fake_sell.quantity)
        self.assertEqual(float(sell.sale_price),
                         float(self.fake_sell.sale_price))

    def test_find_sells_by_bill_db_hit(self):
        """
        If cache.get returns None, the repository should query the DB,
        cache the result, and return the list of Sell instances.
        """
        self.mock_cache.get.return_value = None

        # Set up a fake query chain:
        fake_query = MagicMock()
        fake_filter = MagicMock()
        fake_filter.all.return_value = [self.fake_sell]
        fake_query.filter.return_value = fake_filter
        self.fake_session.query.return_value = fake_query

        result = self.repo.find_sells_by_bill(self.bill_id, self.cache_model)

        self.mock_cache.get.assert_called_once_with(self.cache_model.key)
        self.fake_session.query.assert_called_once_with(self.repo.model)
        fake_query.filter.assert_called_once()  # Ensure filter is called.
        fake_filter.all.assert_called_once()
        # Ensure cache.set is called with the serialized result.
        self.mock_cache.set.assert_called_once()
        self.assertEqual(result, [self.fake_sell])
        self.fake_session.close.assert_called_once()

    def test_find_sells_by_bill_exception(self):
        """
        If an exception occurs during the DB query (e.g. a DB error),
        the repository should return an empty list.
        """
        self.mock_cache.get.return_value = None
        self.fake_session.query.side_effect = Exception("DB error")
        result = self.repo.find_sells_by_bill(self.bill_id, self.cache_model)
        self.assertEqual(result, [])
        self.fake_session.close.assert_called_once()
