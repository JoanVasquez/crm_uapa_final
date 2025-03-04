"""
Sell API routes.

This module defines API endpoints for sell transactions. Endpoints include creating a sell,
retrieving sells (list and by ID), updating, and deleting sells. All endpoints are protected
by JWT authentication using AWS Cognito.
"""

from decimal import Decimal
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, condecimal, conint

from app.services.sell_service import SellService
from app.utils.http_response import HttpResponse
from app.utils.logger import get_logger
from app.utils.verify_token_util import verify_token

logger = get_logger(__name__)
router = APIRouter(prefix="/sells", tags=["Sells"])

# Define a constant for "Sell not found"
SELL_NOT_FOUND = "Sell not found"


# Pydantic models for sell requests/responses
class SellCreate(BaseModel):
    bill_id: int = Field(..., example=1)
    product_id: int = Field(..., example=2)
    quantity: Annotated[int, conint(gt=0)] = Field(..., example=3)
    sale_price: Annotated[Decimal, condecimal(gt=Decimal("0"))] = Field(
        ..., example=19.99
    )


class SellUpdate(BaseModel):
    quantity: Optional[Annotated[int, conint(gt=0)]] = Field(None, example=5)
    sale_price: Optional[Annotated[Decimal, condecimal(gt=Decimal("0"))]] = Field(
        None, example=18.99
    )


class SellResponse(BaseModel):
    id: int
    bill_id: int
    product_id: int
    quantity: int
    sale_price: float


@router.post("/", response_model=SellResponse, response_class=JSONResponse)
async def create_sell(sell: SellCreate, user=Depends(verify_token)) -> JSONResponse:
    """
    Create a new sell transaction.

    This endpoint creates a sell record using the provided data.
    """
    sell_service = SellService()
    try:
        new_sell = sell_service.create_sell(sell.dict())
        return JSONResponse(
            content=HttpResponse.success(new_sell, "Sell created successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[SellController] Failed to create sell", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create sell",
        ) from error


@router.get("/", response_model=List[SellResponse], response_class=JSONResponse)
async def list_sells(user=Depends(verify_token)) -> JSONResponse:
    """
    Retrieve a list of sell transactions.

    Returns all sell records.
    """
    sell_service = SellService()
    try:
        sells = sell_service.get_all_sells()
        return JSONResponse(
            content=HttpResponse.success(sells, "Sells retrieved successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[SellController] Failed to retrieve sells", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sells",
        ) from error


@router.get("/{sell_id}", response_model=SellResponse, response_class=JSONResponse)
async def get_sell(sell_id: int, user=Depends(verify_token)) -> JSONResponse:
    """
    Retrieve a sell transaction by its ID.
    """
    sell_service = SellService()
    try:
        sell_record = sell_service.get_sell_by_id(sell_id)
        if not sell_record:
            logger.warning("Sell not found: %s", sell_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=SELL_NOT_FOUND,
            )
        return JSONResponse(
            content=HttpResponse.success(sell_record, "Sell retrieved successfully"),
            status_code=status.HTTP_200_OK,
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as error:
        logger.error("[SellController] Failed to retrieve sell", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sell",
        ) from error


@router.put("/{sell_id}", response_model=SellResponse, response_class=JSONResponse)
async def update_sell(
    sell_id: int, sell: SellUpdate, user=Depends(verify_token)
) -> JSONResponse:
    """
    Update a sell transaction by its ID.

    Updates the sell record with the provided details.
    """
    sell_service = SellService()
    try:
        updated_sell = sell_service.update_sell(sell_id, sell.dict(exclude_unset=True))
        if not updated_sell:
            logger.warning("%s: %s", SELL_NOT_FOUND, sell_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=SELL_NOT_FOUND,
            )
        return JSONResponse(
            content=HttpResponse.success(updated_sell, "Sell updated successfully"),
            status_code=status.HTTP_200_OK,
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as error:
        logger.error("[SellController] Failed to update sell", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update sell",
        ) from error


@router.delete("/{sell_id}", response_class=JSONResponse)
async def delete_sell(sell_id: int, user=Depends(verify_token)) -> JSONResponse:
    """
    Delete a sell transaction by its ID.
    """
    sell_service = SellService()
    try:
        success = sell_service.delete_sell(sell_id)
        if not success:
            logger.warning("Sell not found: %s", sell_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=SELL_NOT_FOUND,
            )
        return JSONResponse(
            content=HttpResponse.success(None, "Sell deleted successfully"),
            status_code=status.HTTP_200_OK,
        )
    except HTTPException as http_exc:
        # Re-raise HTTPException so that a 404 remains a 404.
        raise http_exc
    except Exception as error:
        logger.error("[SellController] Failed to delete sell", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete sell",
        ) from error
