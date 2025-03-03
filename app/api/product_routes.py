from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.services.authentication_service import CognitoAuthenticationService
from app.services.product_service import ProductService
from app.utils.http_response import HttpResponse

router = APIRouter(prefix="/products", tags=["Products"])
security = HTTPBearer()


# Pydantic models for product requests/responses
class ProductCreate(BaseModel):
    name: str
    description: str = None
    price: float
    available_quantity: int


class ProductUpdate(BaseModel):
    name: str = None
    description: str = None
    price: float = None
    available_quantity: int = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str = None
    price: float
    available_quantity: int


# Dependency that validates the JWT using AWS Cognito
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # Verify the JWT token using your AWS Cognito integration.
        auth_service = CognitoAuthenticationService()
        user = auth_service.verify_jwt_token(token)
        return user  # Return user information if needed
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e


@router.post("/", response_model=ProductResponse)
def create_product(product: ProductCreate, user=Depends(verify_token)):
    """
    Create a new product.

    This endpoint creates a product using the provided data. It is protected by JWT authentication.
    """
    product_service = ProductService()
    try:
        new_product = product_service.create_product(product.dict())
        return HttpResponse.success(new_product, "Product created successfully")
    except Exception as e:
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
    product_service = ProductService()
    try:
        products = product_service.get_all_products()
        return HttpResponse.success(products, "Products retrieved successfully")
    except Exception as e:
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
    product_service = ProductService()
    try:
        product = product_service.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )
        return HttpResponse.success(product, "Product retrieved successfully")
    except Exception as e:
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
    product_service = ProductService()
    try:
        updated_product = product_service.update_product(
            product_id, product.dict(exclude_unset=True)
        )
        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )
        return HttpResponse.success(updated_product, "Product updated successfully")
    except Exception as e:
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
    product_service = ProductService()
    try:
        success = product_service.delete_product(product_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )
        return HttpResponse.success(None, "Product deleted successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product",
        ) from e
