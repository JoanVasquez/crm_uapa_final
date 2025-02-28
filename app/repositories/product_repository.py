import json
from typing import Optional
from app.models import Product
from app.repositories.generic_repository import GenericRepository, deserialize_instance, model_to_dict
from app.config.database import SessionLocal
from app.utils.cache_util import cache
from app.utils.cache_util_model import CacheModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProductRepository(GenericRepository):
    def __init__(self) -> None:
        # Pass the Product model and a session (None here, because methods like find_product_by_name create their own session)
        super().__init__(Product, None)

    def find_product_by_name(self, name: str, cache_model: Optional[CacheModel] = None) -> Optional[Product]:
        """
        Retrieve a product by its name.
        If a cache_model is provided, first attempt to retrieve from cache.
        """
        session = SessionLocal()
        try:
            if cache_model:
                cache_entity = cache.get(cache_model.key)
                if cache_entity:
                    data = json.loads(cache_entity)
                    return deserialize_instance(self.model, data)
            product = session.query(self.model).filter(
                self.model.name == name).first()
            if not product:
                logger.warning(
                    f"[ProductRepository] No product found with name: {name}")
                raise Exception(f"Product with name {name} not found")
            if cache_model:
                data = json.dumps(self._to_dict(product), default=str)
                cache.set(cache_model.key, data,
                          timeout=cache_model.expiration)
            return product
        except Exception as error:
            logger.error(
                "[ProductRepository] Error finding product by name: %s", error, exc_info=True)
            return None
        finally:
            session.close()

    def _to_dict(self, instance: Product) -> dict:
        """
        Convert a Product instance to a dictionary.
        """
        return {
            "id": instance.id,
            "name": instance.name,
            "description": instance.description,
            "price": float(instance.price) if instance.price is not None else None,
            "available_quantity": instance.available_quantity,
        }
