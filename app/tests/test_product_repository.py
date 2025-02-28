import json
import unittest
from unittest.mock import MagicMock, patch

from app.repositories.product_repository import ProductRepository
from app.models import Product
from app.utils.cache_util_model import CacheModel
from app.repositories.generic_repository import model_to_dict

# Create a FakeProduct for testing. You can use your real Product if it has a simple constructor.


class FakeProduct:
    def __init__(self, id, name, description, price, available_quantity):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.available_quantity = available_quantity

    def __eq__(self, other):
        return (
            isinstance(other, FakeProduct) and
            self.id == other.id and
            self.name == other.name and
            self.description == other.description and
            self.price == other.price and
            self.available_quantity == other.available_quantity
        )

    def __repr__(self):
        return f"FakeProduct(id={self.id}, name={self.name})"


class TestProductRepository(unittest.TestCase):
    def setUp(self):
        # Create an instance of ProductRepository.
        self.repo = ProductRepository()
        # Patch the SessionLocal to return a fake session.
        self.session_patch = patch(
            "app.repositories.product_repository.SessionLocal")
        self.mock_session_local = self.session_patch.start()
        self.addCleanup(self.session_patch.stop)

        # Create a fake session (a MagicMock)
        self.fake_session = MagicMock()
        self.mock_session_local.return_value = self.fake_session

        # Create a fake product for testing.
        self.fake_product = FakeProduct(
            id=1,
            name="TestProduct",
            description="A product for testing",
            price=19.99,
            available_quantity=100
        )
        # Create a CacheModel instance for testing.
        self.cache_model = CacheModel(
            key="product_TestProduct", expiration=300)

        # Patch the global cache in the module.
        self.cache_patch = patch("app.repositories.product_repository.cache")
        self.mock_cache = self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)

        # Also patch logger if needed (optional)
        self.logger_patch = patch("app.repositories.product_repository.logger")
        self.mock_logger = self.logger_patch.start()
        self.addCleanup(self.logger_patch.stop)

    def test_find_product_by_name_cache_hit(self):
        """Test that if the product is in cache, it is returned without querying the DB."""
        # Prepare a JSON string representing the product.
        product_dict = {
            "id": self.fake_product.id,
            "name": self.fake_product.name,
            "description": self.fake_product.description,
            "price": float(self.fake_product.price),
            "available_quantity": self.fake_product.available_quantity,
        }
        self.mock_cache.get.return_value = json.dumps(product_dict)

        result = self.repo.find_product_by_name(
            "TestProduct", self.cache_model)
        # Check that the cache was queried.
        self.mock_cache.get.assert_called_once_with(self.cache_model.key)
        # Because we got a cache hit, session.query should not be used.
        self.fake_session.query.assert_not_called()
        # The result should be a Product-like instance (created via deserialize_instance).
        # We check that the deserialized instance has the same attributes.
        self.assertEqual(result.id, self.fake_product.id)
        self.assertEqual(result.name, self.fake_product.name)
        self.assertEqual(result.description, self.fake_product.description)
        self.assertEqual(float(result.price), float(self.fake_product.price))
        self.assertEqual(result.available_quantity,
                         self.fake_product.available_quantity)

    def test_find_product_by_name_db_hit(self):
        """Test that if cache is empty, the repository queries the DB and caches the result."""
        self.mock_cache.get.return_value = None
        # Set up the fake session query chain.
        fake_query = MagicMock()
        fake_filter = MagicMock()
        fake_query.filter.return_value = fake_filter
        fake_filter.first.return_value = self.fake_product
        self.fake_session.query.return_value = fake_query

        result = self.repo.find_product_by_name(
            "TestProduct", self.cache_model)
        # Ensure cache.get was called.
        self.mock_cache.get.assert_called_once_with(self.cache_model.key)
        # Ensure the session query was executed.
        self.fake_session.query.assert_called_once_with(self.repo.model)
        # filtering by product.name == "TestProduct"
        fake_query.filter.assert_called_once()
        fake_filter.first.assert_called_once()
        # Check that cache.set was called with the serialized product.
        self.mock_cache.set.assert_called_once()
        # The result should be the fake product.
        self.assertEqual(result, self.fake_product)
        # Verify that the session is closed.
        self.fake_session.close.assert_called_once()

    def test_find_product_by_name_not_found(self):
        """Test that if no product is found, the method returns None (after logging error)."""
        self.mock_cache.get.return_value = None
        fake_query = MagicMock()
        fake_filter = MagicMock()
        fake_query.filter.return_value = fake_filter
        # Simulate DB returning no product.
        fake_filter.first.return_value = None
        self.fake_session.query.return_value = fake_query

        result = self.repo.find_product_by_name(
            "NonExistent", self.cache_model)
        # Expect that the method returns None.
        self.assertIsNone(result)
        # Verify that session.close() was called.
        self.fake_session.close.assert_called_once()

    def test__to_dict(self):
        """Test the helper _to_dict method returns the correct dictionary."""
        # Call _to_dict on fake_product.
        result = self.repo._to_dict(self.fake_product)
        expected = {
            "id": self.fake_product.id,
            "name": self.fake_product.name,
            "description": self.fake_product.description,
            "price": float(self.fake_product.price),
            "available_quantity": self.fake_product.available_quantity,
        }
        self.assertEqual(result, expected)
