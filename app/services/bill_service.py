from app.errors import BaseAppException, ResourceNotFoundError
from app.models import Bill
from app.repositories.bill_repository import BillRepository
from app.services.generic_service import GenericService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BillService(GenericService[Bill]):
    def __init__(self) -> None:
        # Initialize the repository and pass it to the GenericService
        self.bill_repository = BillRepository()
        super().__init__(self.bill_repository)

    def get_bills_by_user_id(self, user_id: int) -> list:
        """
        Retrieve all bills for the given user_id.
        Raises ResourceNotFoundError if no bills are found.
        Wraps any other exceptions in a BaseAppException.
        """
        try:
            bills = self.bill_repository.find_bills_by_user_id(user_id)
            return bills
        except ResourceNotFoundError as rnfe:
            logger.error("Bills not found for user_id: %s", user_id, exc_info=True)
            raise rnfe
        except Exception as error:
            logger.error(
                "Error retrieving bills for user_id: %s", user_id, exc_info=True
            )
            raise BaseAppException(
                "Error retrieving bills", details=str(error)
            ) from error
