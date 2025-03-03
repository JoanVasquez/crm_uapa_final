import unittest
from unittest.mock import MagicMock

from app.errors import BaseAppException, ResourceNotFoundError
from app.services.product_service import ProductService
from app.tests.helpers import DummyProduct


class TestProductService(unittest.TestCase):
    def setUp(self):
        self.product_service = ProductService()
        # Replace the underlying repository with a MagicMock.
        self.product_service.product_repository = MagicMock()
        # Create a dummy product instance.
        self.dummy_product = DummyProduct(
            1, "TestProduct", "A test product", 19.99, 100
        )

    def test_get_product_by_name_success(self):
        # Simulate the repository returning a product.
        self.product_service.product_repository.find_product_by_name.return_value = (
            self.dummy_product
        )

        result = self.product_service.get_product_by_name("TestProduct")
        self.assertEqual(result, self.dummy_product)
        self.product_service.product_repository.find_product_by_name.assert_called_once_with(
            "TestProduct"
        )

    def test_get_product_by_name_not_found(self):
        # Simulate the repository raising ResourceNotFoundError.
        self.product_service.product_repository.find_product_by_name.side_effect = (
            ResourceNotFoundError("Product with name TestProduct not found")
        )

        with self.assertRaises(ResourceNotFoundError) as context:
            self.product_service.get_product_by_name("TestProduct")
        self.assertIn("Product with name TestProduct not found", str(context.exception))

    def test_get_product_by_name_generic_error(self):
        # Simulate a generic exception from the repository.
        self.product_service.product_repository.find_product_by_name.side_effect = (
            Exception("Database error")
        )

        with self.assertRaises(BaseAppException) as context:
            self.product_service.get_product_by_name("TestProduct")
        self.assertIn("Error getting product by name", str(context.exception))
