import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.errors import ResourceNotFoundError
from app.repositories.bill_repository import BillRepository
from app.tests.helpers import FakeBill
from app.utils.cache_util_model import CacheModel


class TestBillRepository(unittest.TestCase):
    def setUp(self):
        # Instantiate the repository and override its model with FakeBill.
        self.repo = BillRepository()
        self.repo.model = FakeBill
        self.user_id = 10
        self.fake_bill = FakeBill(
            id=1,
            user_id=self.user_id,
            date=datetime(2023, 1, 1, 12, 0, 0),
            total_amount=100.50,
        )
        self.cache_model = CacheModel(key=f"bill_user_{self.user_id}", expiration=300)

        # Patch SessionLocal so that a fake session is used.
        session_patcher = patch("app.repositories.bill_repository.SessionLocal")
        self.mock_session_local = session_patcher.start()
        self.addCleanup(session_patcher.stop)
        self.fake_session = MagicMock()
        self.mock_session_local.return_value = self.fake_session

        # Patch the global cache.
        cache_patcher = patch("app.repositories.bill_repository.cache")
        self.mock_cache = cache_patcher.start()
        self.addCleanup(cache_patcher.stop)

    def test_find_bills_by_user_id_cache_hit(self):
        """
        If cache.get returns a JSON list, the repository should deserialize that list
        and return a list of Bill instances without querying the DB.
        """
        bill_data = {
            "id": self.fake_bill.id,
            "user_id": self.fake_bill.user_id,
            "date": self.fake_bill.date.isoformat(),
            "total_amount": float(self.fake_bill.total_amount),
        }
        self.mock_cache.get.return_value = json.dumps([bill_data])

        result = self.repo.find_bills_by_user_id(self.user_id, self.cache_model)

        self.mock_cache.get.assert_called_once_with(self.cache_model.key)
        # When cache hit occurs, no DB query should be triggered.
        self.fake_session.query.assert_not_called()
        self.assertEqual(len(result), 1)
        bill = result[0]
        self.assertEqual(bill.id, self.fake_bill.id)
        self.assertEqual(bill.user_id, self.fake_bill.user_id)
        # Note: In a cache hit scenario, the "date" is stored as an ISO string.
        self.assertEqual(bill.date, self.fake_bill.date.isoformat())
        self.assertEqual(float(bill.total_amount), float(self.fake_bill.total_amount))
        self.fake_session.close.assert_called_once()

    def test_find_bills_by_user_id_db_hit(self):
        """
        If cache.get returns None, the repository should query the DB,
        cache the result, and return the list of Bill instances.
        """
        self.mock_cache.get.return_value = None

        fake_query = MagicMock()
        fake_filter = MagicMock()
        fake_filter.all.return_value = [self.fake_bill]
        # Set up the query chain: session.query(...).filter(...) returns fake_filter.
        fake_query.filter.return_value = fake_filter
        self.fake_session.query.return_value = fake_query

        result = self.repo.find_bills_by_user_id(self.user_id, self.cache_model)

        self.mock_cache.get.assert_called_once_with(self.cache_model.key)
        self.fake_session.query.assert_called_once_with(self.repo.model)
        fake_query.filter.assert_called_once_with(
            self.repo.model.user_id == self.user_id
        )
        fake_filter.all.assert_called_once()

        expected_data = json.dumps(
            [
                {
                    "id": self.fake_bill.id,
                    "user_id": self.fake_bill.user_id,
                    "date": self.fake_bill.date.isoformat(),
                    "total_amount": float(self.fake_bill.total_amount),
                }
            ]
        )
        self.mock_cache.set.assert_called_once_with(
            self.cache_model.key, expected_data, timeout=self.cache_model.expiration
        )
        self.assertEqual(result, [self.fake_bill])
        self.fake_session.close.assert_called_once()

    def test_find_bills_by_user_id_not_found(self):
        """
        If the DB returns an empty list and cache is empty, the repository should raise a ResourceNotFoundError.
        """
        self.mock_cache.get.return_value = None

        fake_query = MagicMock()
        fake_filter = MagicMock()
        fake_filter.all.return_value = []  # No bills found.
        fake_query.filter.return_value = fake_filter
        self.fake_session.query.return_value = fake_query

        with self.assertRaises(ResourceNotFoundError) as context:
            self.repo.find_bills_by_user_id(self.user_id, self.cache_model)
        self.fake_session.close.assert_called_once()
        self.assertIn(
            f"Bills for user_id {self.user_id} not found", str(context.exception)
        )

    def test_to_dict_helper(self):
        """Test that the _to_dict helper returns the correct dictionary."""
        result = self.repo._to_dict(self.fake_bill)
        expected = {
            "id": self.fake_bill.id,
            "user_id": self.fake_bill.user_id,
            "date": self.fake_bill.date.isoformat(),
            "total_amount": float(self.fake_bill.total_amount),
        }
        self.assertEqual(result, expected)
