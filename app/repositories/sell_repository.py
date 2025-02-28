import json
from typing import Optional

from app.models import Sell
from app.repositories.generic_repository import GenericRepository, deserialize_instance, model_to_dict
from app.config.database import SessionLocal
from app.utils.cache_util import cache
from app.utils.cache_util_model import CacheModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SellRepository(GenericRepository):
    def __init__(self) -> None:
        # Pass Sell model and None for session because we create our own session in custom methods.
        super().__init__(Sell, None)

    def find_sells_by_bill(self, bill_id: int, cache_model: Optional[CacheModel] = None) -> list:
        """
        Retrieve all Sell records for a given bill_id.
        If a CacheModel is provided, first attempt to retrieve from cache.
        """
        session = SessionLocal()
        try:
            if cache_model:
                cached = cache.get(cache_model.key)
                if cached:
                    # Expect cached value is a JSON list of sell dicts.
                    data_list = json.loads(cached)
                    return [deserialize_instance(self.model, data) for data in data_list]
            sells = session.query(self.model).filter(
                self.model.bill_id == bill_id).all()
            if cache_model:
                data_list = [model_to_dict(sell) for sell in sells]
                cache.set(cache_model.key, json.dumps(data_list),
                          timeout=cache_model.expiration)
            return sells
        except Exception as error:
            logger.error("Error finding sells by bill_id: %s",
                         error, exc_info=True)
            return []
        finally:
            session.close()
