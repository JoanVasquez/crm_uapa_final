from app.errors import BaseAppException, ResourceNotFoundError
from app.models import Product
from app.repositories.product_repository import ProductRepository
from app.services.generic_service import GenericService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProductService(GenericService[Product]):
    def __init__(self) -> None:
        # Initialize the repository and pass it to the GenericService.
        self.product_repository = ProductRepository()
        super().__init__(self.product_repository)

    def get_product_by_name(self, name: str) -> Product:
        """
        Retrieve a product by its name.
        Raises ResourceNotFoundError if the product is not found.
        """
        try:
            product = self.product_repository.find_product_by_name(name)
            return product
        except ResourceNotFoundError as rnfe:
            logger.error("Product not found: %s", name, exc_info=True)
            raise rnfe
        except Exception as error:
            logger.error("Error retrieving product by name: %s", name, exc_info=True)
            raise BaseAppException(
                "Error getting product by name", details=str(error)
            ) from error
