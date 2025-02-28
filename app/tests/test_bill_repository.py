import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

# --- Fake Model Setup ---


class DummyColumn:
    def __init__(self, name):
        self.name = name


class FakeTable:
    @property
    def columns(self):
        return [
            DummyColumn("id"),
            DummyColumn("user_id"),
            DummyColumn("date"),
            DummyColumn("total_amount")
        ]


class FakeBill:
    __table__ = FakeTable()

    def __init__(self, id, user_id, date, total_amount):
        self.id = id
        self.user_id = user_id
        self.date = date
        self.total_amount = total_amount

    def __eq__(self, other):
        return (
            isinstance(other, FakeBill)
            and self.id == other.id
            and self.user_id == other.user_id
            and self.date == other.date
            and float(self.total_amount) == float(other.total_amount)
        )

    def __repr__(self):
        return f"FakeBill(id={self.id}, user_id={self.user_id})"

# --- Test Cases for BillRepository ---


class TestBillRepository(unittest.TestCase):
    def setUp(self):
        from app.repositories.bill_repository import BillRepository
        self.repo = BillRepository()

        # Patch SessionLocal so that a fake session is used.
        session_patcher = patch(
            "app.repositories.bill_repository.SessionLocal")
        self.mock_session_local = session_patcher.start()
        self.addCleanup(session_patcher.stop)

        self.fake_session = MagicMock()
        self.mock_session_local.return_value = self.fake_session

        # Patch the global cache.
        cache_patcher = patch("app.repositories.bill_repository.cache")
        self.mock_cache = cache_patcher.start()
        self.addCleanup(cache_patcher.stop)

        # Create a fake Bill instance.
        self.fake_bill = FakeBill(
            id=1,
            user_id=10,
            date=datetime(2023, 1, 1, 12, 0, 0),
            total_amount=100.50
        )
        self.user_id = 10
        # Create a CacheModel instance.
        from app.utils.cache_util_model import CacheModel
        self.cache_model = CacheModel(
            key=f"bill_user_{self.user_id}", expiration=300)

    def test_find_bills_by_user_id_cache_hit(self):
        """
        If cache.get returns a JSON list, the repository should deserialize that list
        and return a list of Bill instances without querying the DB.
        """
        bill_data = {
            "id": self.fake_bill.id,
            "user_id": self.fake_bill.user_id,
            "date": self.fake_bill.date.isoformat(),  # stored as a string in cache
            "total_amount": float(self.fake_bill.total_amount)
        }
        # Simulate a cache hit.
        self.mock_cache.get.return_value = json.dumps([bill_data])

        result = self.repo.find_bills_by_user_id(
            self.user_id, self.cache_model)

        self.mock_cache.get.assert_called_once_with(self.cache_model.key)
        # No DB query should be triggered.
        self.fake_session.query.assert_not_called()
        self.assertEqual(len(result), 1)
        bill = result[0]
        self.assertEqual(bill.id, self.fake_bill.id)
        self.assertEqual(bill.user_id, self.fake_bill.user_id)
        # Compare the cached date string directly.
        self.assertEqual(bill.date, self.fake_bill.date.isoformat())
        self.assertEqual(float(bill.total_amount),
                         float(self.fake_bill.total_amount))

    def test_find_bills_by_user_id_db_hit(self):
        """
        If cache.get returns None, the repository should query the DB,
        cache the result, and return the list of Bill instances.
        """
        self.mock_cache.get.return_value = None

        fake_query = MagicMock()
        fake_filter = MagicMock()
        fake_filter.all.return_value = [self.fake_bill]
        fake_query.filter.return_value = fake_filter
        self.fake_session.query.return_value = fake_query

        result = self.repo.find_bills_by_user_id(
            self.user_id, self.cache_model)

        self.mock_cache.get.assert_called_once_with(self.cache_model.key)
        self.fake_session.query.assert_called_once_with(self.repo.model)
        fake_query.filter.assert_called_once()  # Check that filter is applied.
        fake_filter.all.assert_called_once()
        self.mock_cache.set.assert_called_once()
        self.assertEqual(result, [self.fake_bill])
        self.fake_session.close.assert_called_once()

    def test_find_bills_by_user_id_not_found(self):
        """
        If the DB returns an empty list and cache is empty, the repository should return an empty list.
        """
        self.mock_cache.get.return_value = None
        fake_query = MagicMock()
        fake_filter = MagicMock()
        fake_filter.all.return_value = []
        fake_query.filter.return_value = fake_filter
        self.fake_session.query.return_value = fake_query

        result = self.repo.find_bills_by_user_id(
            self.user_id, self.cache_model)
        self.assertEqual(result, [])
        self.fake_session.close.assert_called_once()

    def test_to_dict_helper(self):
        """Test that the _to_dict helper returns the correct dictionary."""
        result = self.repo._to_dict(self.fake_bill)
        expected = {
            "id": self.fake_bill.id,
            "user_id": self.fake_bill.user_id,
            "date": self.fake_bill.date.isoformat(),
            "total_amount": float(self.fake_bill.total_amount)
        }
        self.assertEqual(result, expected)
