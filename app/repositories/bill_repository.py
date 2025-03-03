# pylint: disable=duplicate-code
import json
from typing import Optional

from app.config.database import SessionLocal
from app.errors import BaseAppException, ResourceNotFoundError
from app.models import Bill
from app.repositories.generic_repository import GenericRepository, deserialize_instance
from app.utils.cache_util import cache
from app.utils.cache_util_model import CacheModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BillRepository(GenericRepository):
    def __init__(self) -> None:
        # Initialize using the Bill model; we pass None as session because we create our own sessions in custom queries.
        super().__init__(Bill, None)

    def find_bills_by_user_id(
        self, user_id: int, cache_model: Optional[CacheModel] = None
    ) -> list:
        """
        Retrieve all Bill records for a given user_id.
        If a CacheModel is provided, first attempt to retrieve from cache.
        Raises ResourceNotFoundError if no bills are found,
        or wraps any other exceptions in a BaseAppException.
        """
        session = SessionLocal()
        try:
            if cache_model:
                cached = cache.get(cache_model.key)
                if cached:
                    # Expecting cached value is a JSON list of bill dictionaries.
                    data_list = json.loads(cached)
                    return [
                        deserialize_instance(self.model, data) for data in data_list
                    ]
            bills = (
                session.query(self.model).filter(self.model.user_id == user_id).all()
            )
            if not bills:
                logger.warning(
                    f"[BillRepository] No bills found for user_id: {user_id}"
                )
                raise ResourceNotFoundError(f"Bills for user_id {user_id} not found")
            if cache_model:
                data_list = [self._to_dict(bill) for bill in bills]
                cache.set(
                    cache_model.key,
                    json.dumps(data_list),
                    timeout=cache_model.expiration,
                )
            return bills
        except Exception as error:
            logger.error("Error finding bills by user_id: %s", error, exc_info=True)
            if isinstance(error, BaseAppException):
                raise error
            raise BaseAppException(
                "Error finding bills by user_id", details=str(error)
            ) from error
        finally:
            session.close()

    def _to_dict(self, instance: Bill) -> dict:
        """
        Convert a Bill instance to a dictionary.
        """
        return {
            "id": instance.id,
            "user_id": instance.user_id,
            "date": instance.date.isoformat() if instance.date else None,
            "total_amount": (
                float(instance.total_amount)
                if instance.total_amount is not None
                else None
            ),
        }
