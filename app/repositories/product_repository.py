"""
Module for Product repository.

This module defines ProductRepository for managing Product model operations,
including retrieving products by name with optional caching.
"""

import json
from typing import Optional

from app.config.database import SessionLocal
from app.errors import BaseAppException, ResourceNotFoundError
from app.models import Product
from app.repositories.generic_repository import GenericRepository, deserialize_instance
from app.utils.cache_util import cache
from app.utils.cache_util_model import CacheModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProductRepository(GenericRepository):
    """Repository for Product model operations.

    Inherits from GenericRepository.
    """

    def __init__(self) -> None:
        """
        Initialize the repository with the Product model.

        Note:
            The session is managed within each method.
        """
        super().__init__(Product, None)

    def find_product_by_name(
        self, name: str, cache_model: Optional[CacheModel] = None
    ) -> Optional[Product]:
        """
        Retrieve a product by its name.

        First, attempt to retrieve from cache if cache_model is provided.
        Otherwise, query the database and cache the result if needed.

        Args:
            name (str): The product name.
            cache_model (Optional[CacheModel]): Cache configuration.

        Returns:
            Optional[Product]: The found Product instance.

        Raises:
            ResourceNotFoundError: If no product is found.
            BaseAppException: If any other error occurs.
        """
        session = SessionLocal()
        try:
            if cache_model:
                cache_entity = cache.get(cache_model.key)
                if cache_entity:
                    data = json.loads(cache_entity)
                    return deserialize_instance(self.model, data)
            product = session.query(self.model).filter(self.model.name == name).first()
            if not product:
                logger.warning(
                    f"[ProductRepository] No product found with name: {name}"
                )
                raise ResourceNotFoundError(f"Product with name {name} not found")
            if cache_model:
                data = json.dumps(self._to_dict(product), default=str)
                cache.set(cache_model.key, data, timeout=cache_model.expiration)
            return product
        except Exception as error:
            logger.error(
                "[ProductRepository] Error finding product by name: %s",
                error,
                exc_info=True,
            )
            if isinstance(error, BaseAppException):
                raise error
            raise BaseAppException(
                "Error finding product by name", details=str(error)
            ) from error
        finally:
            session.close()

    def _to_dict(self, instance: Product) -> dict:
        """
        Convert a Product instance to a dictionary.

        Args:
            instance (Product): The product instance.

        Returns:
            dict: Dictionary representation of the product.
        """
        return {
            "id": instance.id,
            "name": instance.name,
            "description": instance.description,
            "price": float(instance.price) if instance.price is not None else None,
            "available_quantity": instance.available_quantity,
        }
