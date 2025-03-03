from app.errors import BaseAppException, ResourceNotFoundError
from app.models import Sell
from app.repositories.sell_repository import SellRepository
from app.services.generic_service import GenericService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SellService(GenericService[Sell]):
    def __init__(self) -> None:
        # Initialize the service with the SellRepository.
        sell_repo = SellRepository()
        super().__init__(sell_repo)
        self.sell_repo = sell_repo

    def get_sells_by_bill(self, bill_id: int, cache_key: str = None) -> list:
        """
        Retrieve all Sell records associated with a given bill_id.
        If a cache_key is provided, a CacheModel is created and used.
        Raises ResourceNotFoundError if no sells are found, or wraps other exceptions
        in a BaseAppException.
        """
        from app.utils.cache_util_model import CacheModel

        cache_model = CacheModel(key=cache_key, expiration=300) if cache_key else None
        try:
            sells = self.sell_repo.find_sells_by_bill(bill_id, cache_model)
            if not sells:
                raise ResourceNotFoundError(f"No sells found for bill id {bill_id}")
            return sells
        except Exception as error:
            logger.error(
                "Failed to get sells for bill id %s: %s", bill_id, error, exc_info=True
            )
            if isinstance(error, BaseAppException):
                raise error
            raise BaseAppException(
                "Failed to get sells for bill id", details=str(error)
            ) from error
