import unittest
from datetime import datetime
from unittest.mock import MagicMock

from app.errors import BaseAppException, ResourceNotFoundError
from app.services.bill_service import BillService
from app.tests.helpers import DummyBill
from app.utils.cache_util_model import CacheModel


class TestBillService(unittest.TestCase):
    def setUp(self):
        # Instantiate the service and patch its underlying repository
        self.bill_service = BillService()
        self.mock_repo = MagicMock()
        self.bill_service.bill_repository = self.mock_repo
        self.user_id = 10
        # Create a dummy bill
        self.fake_bill = DummyBill(
            id=1,
            user_id=self.user_id,
            date=datetime(2023, 1, 1, 12, 0, 0),
            total_amount=150.75,
        )
        # A cache model for testing
        self.cache_model = CacheModel(key=f"bill_user_{self.user_id}", expiration=300)

    def test_get_bills_by_user_id_success(self):
        """Test that get_bills_by_user_id returns the list of bills when found."""
        # Simulate the repository returning a list with one bill.
        self.mock_repo.find_bills_by_user_id.return_value = [self.fake_bill]

        result = self.bill_service.get_bills_by_user_id(self.user_id)
        self.mock_repo.find_bills_by_user_id.assert_called_once_with(self.user_id)
        self.assertEqual(result, [self.fake_bill])

    def test_get_bills_by_user_id_not_found(self):
        """Test that if no bills are found, a ResourceNotFoundError is raised."""
        self.mock_repo.find_bills_by_user_id.side_effect = ResourceNotFoundError(
            "Bills for user_id 10 not found"
        )

        with self.assertRaises(ResourceNotFoundError) as context:
            self.bill_service.get_bills_by_user_id(self.user_id)
        self.assertIn("Bills for user_id 10 not found", str(context.exception))
        self.mock_repo.find_bills_by_user_id.assert_called_once_with(self.user_id)

    def test_get_bills_by_user_id_generic_error(self):
        """Test that a generic exception is wrapped in a BaseAppException."""
        self.mock_repo.find_bills_by_user_id.side_effect = Exception("Database error")

        with self.assertRaises(BaseAppException) as context:
            self.bill_service.get_bills_by_user_id(self.user_id)
        self.assertIn("Error retrieving bills", str(context.exception))
        self.mock_repo.find_bills_by_user_id.assert_called_once_with(self.user_id)
