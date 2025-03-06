from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.services.product_service import ProductService
from app.utils.http_response import HttpResponse
from app.utils.logger import get_logger
from app.utils.verify_token_util import verify_token

logger = get_logger(__name__)

router = APIRouter(prefix="/products", tags=["Products"])

# Define a constant for the "Product not found" message.
PRODUCT_NOT_FOUND_MSG = "Product not found: %s"


# Pydantic models for product requests/responses
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    available_quantity: int


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    available_quantity: Optional[int] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    available_quantity: int


@router.post("/", response_model=ProductResponse)
def create_product(product: ProductCreate, user=Depends(verify_token)):
    """
    Create a new product.

    This endpoint creates a product using the provided data. It is protected by JWT authentication.
    """
    logger.info("Creating product: %s", product.name)
    product_service = ProductService()
    try:
        new_product = product_service.create_product(product.dict())
        logger.info("Product created successfully: %s", new_product)
        return HttpResponse.success(new_product, "Product created successfully")
    except Exception as e:
        logger.error("Failed to create product", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product",
        ) from e


@router.get("/", response_model=List[ProductResponse])
def list_products(user=Depends(verify_token)):
    """
    Retrieve a list of products.

    This endpoint returns all products and is protected by JWT authentication.
    """
    logger.info("Listing products")
    product_service = ProductService()
    try:
        products = product_service.get_all_products()
        logger.info("Products retrieved successfully")
        return HttpResponse.success(products, "Products retrieved successfully")
    except Exception as e:
        logger.error("Failed to retrieve products", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products",
        ) from e


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, user=Depends(verify_token)):
    """
    Retrieve a product by its ID.

    This endpoint is protected by JWT authentication.
    """
    logger.info("Retrieving product with ID: %s", product_id)
    product_service = ProductService()
    try:
        product = product_service.get_product_by_id(product_id)
        if not product:
            logger.warning(PRODUCT_NOT_FOUND_MSG, product_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=PRODUCT_NOT_FOUND_MSG % product_id,
            )
        logger.info("Product retrieved successfully: %s", product_id)
        return HttpResponse.success(product, "Product retrieved successfully")
    except Exception as e:
        logger.error("Failed to retrieve product", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product",
        ) from e


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate, user=Depends(verify_token)):
    """
    Update an existing product.

    This endpoint updates a product with the provided data and is protected by JWT authentication.
    """
    logger.info("Updating product with ID: %s", product_id)
    product_service = ProductService()
    try:
        updated_product = product_service.update_product(
            product_id, product.dict(exclude_unset=True)
        )
        if not updated_product:
            logger.warning(PRODUCT_NOT_FOUND_MSG, product_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=PRODUCT_NOT_FOUND_MSG % product_id,
            )
        logger.info("Product updated successfully: %s", product_id)
        return HttpResponse.success(updated_product, "Product updated successfully")
    except Exception as e:
        logger.error("Failed to update product", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product",
        ) from e


@router.delete("/{product_id}")
def delete_product(product_id: int, user=Depends(verify_token)):
    """
    Delete a product by its ID.

    This endpoint deletes a product and is protected by JWT authentication.
    """
    logger.info("Deleting product with ID: %s", product_id)
    product_service = ProductService()
    try:
        success = product_service.delete_product(product_id)
        if not success:
            logger.warning(PRODUCT_NOT_FOUND_MSG, product_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=PRODUCT_NOT_FOUND_MSG % product_id,
            )
        logger.info("Product deleted successfully: %s", product_id)
        return HttpResponse.success(None, "Product deleted successfully")
    except Exception as e:
        logger.error("Failed to delete product", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product",
        ) from e
