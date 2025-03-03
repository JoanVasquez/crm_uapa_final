import json
import unittest
from unittest.mock import MagicMock, patch

from app.errors import ResourceNotFoundError
from app.repositories.product_repository import ProductRepository
from app.tests.helpers import FakeProduct
from app.utils.cache_util_model import CacheModel


class TestProductRepository(unittest.TestCase):
    def setUp(self):
        # Instantiate the repository and override its model with FakeProduct.
        self.repo = ProductRepository()
        self.repo.model = FakeProduct
        self.cache_model = CacheModel(key="product_TestProduct", expiration=300)
        self.fake_product = FakeProduct(
            id=1,
            name="TestProduct",
            description="A product for testing",
            price=19.99,
            available_quantity=100,
        )
        # Patch SessionLocal to use a fake session.
        self.session_patch = patch("app.repositories.product_repository.SessionLocal")
        self.mock_session_local = self.session_patch.start()
        self.addCleanup(self.session_patch.stop)
        self.fake_session = MagicMock()
        self.mock_session_local.return_value = self.fake_session
        # Patch the global cache in the module.
        self.cache_patch = patch("app.repositories.product_repository.cache")
        self.mock_cache = self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)

    def test_find_product_by_name_cache_hit(self):
        """
        Test that if the product is in cache, it is deserialized and returned without querying the DB.
        """
        product_dict = {
            "id": self.fake_product.id,
            "name": self.fake_product.name,
            "description": self.fake_product.description,
            "price": float(self.fake_product.price),
            "available_quantity": self.fake_product.available_quantity,
        }
        self.mock_cache.get.return_value = json.dumps(product_dict)

        result = self.repo.find_product_by_name("TestProduct", self.cache_model)
        self.mock_cache.get.assert_called_once_with(self.cache_model.key)
        # Since we got a cache hit, the DB query should not be invoked.
        self.fake_session.query.assert_not_called()
        # Verify that the deserialized product has the expected attributes.
        self.assertEqual(result.id, self.fake_product.id)
        self.assertEqual(result.name, self.fake_product.name)
        self.assertEqual(result.description, self.fake_product.description)
        self.assertEqual(float(result.price), float(self.fake_product.price))
        self.assertEqual(
            result.available_quantity, self.fake_product.available_quantity
        )
        self.fake_session.close.assert_called_once()

    def test_find_product_by_name_db_hit(self):
        """
        Test that if cache is empty, the repository queries the DB, caches the result, and returns the product.
        """
        self.mock_cache.get.return_value = None
        # Set up the fake session query chain.
        fake_query = MagicMock()
        fake_filter = MagicMock()
        fake_filter.first.return_value = self.fake_product
        fake_query.filter.return_value = fake_filter
        self.fake_session.query.return_value = fake_query

        result = self.repo.find_product_by_name("TestProduct", self.cache_model)
        self.mock_cache.get.assert_called_once_with(self.cache_model.key)
        self.fake_session.query.assert_called_once_with(self.repo.model)
        # Not checking exact filter args here.
        fake_query.filter.assert_called_once()
        fake_filter.first.assert_called_once()
        expected_data = json.dumps(
            {
                "id": self.fake_product.id,
                "name": self.fake_product.name,
                "description": self.fake_product.description,
                "price": float(self.fake_product.price),
                "available_quantity": self.fake_product.available_quantity,
            },
            default=str,
        )
        self.mock_cache.set.assert_called_once_with(
            self.cache_model.key, expected_data, timeout=self.cache_model.expiration
        )
        self.assertEqual(result, self.fake_product)
        self.fake_session.close.assert_called_once()

    def test_find_product_by_name_not_found(self):
        """
        Test that if no product is found, the method raises a ResourceNotFoundError.
        """
        self.mock_cache.get.return_value = None

        fake_query = MagicMock()
        fake_filter = MagicMock()
        # Simulate no product found in DB.
        fake_filter.first.return_value = None
        fake_query.filter.return_value = fake_filter
        self.fake_session.query.return_value = fake_query

        with self.assertRaises(ResourceNotFoundError) as context:
            self.repo.find_product_by_name("NonExistent", self.cache_model)
        self.fake_session.close.assert_called_once()
        self.assertIn("Product with name NonExistent not found", str(context.exception))
