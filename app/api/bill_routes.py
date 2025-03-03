"""
Bill API routes.

This module defines API endpoints for bill operations including creation, retrieval,
updating, and deletion. All endpoints are protected by JWT authentication using AWS Cognito.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, condecimal

from app.services.authentication_service import CognitoAuthenticationService
from app.services.bill_service import BillService
from app.utils.http_response import HttpResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
security = HTTPBearer()
router = APIRouter(prefix="/bills", tags=["Bills"])


# Dependency: JWT validation via AWS Cognito
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        auth_service = CognitoAuthenticationService()
        user = auth_service.verify_jwt_token(token)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e


# Pydantic models for bill requests/responses
class BillCreate(BaseModel):
    user_id: int = Field(..., example=1)
    # Optional: let the date default to now if not provided.
    date: Optional[datetime] = Field(default_factory=datetime.utcnow)
    total_amount: condecimal(gt=0) = Field(..., example=100.00)


class BillUpdate(BaseModel):
    total_amount: Optional[condecimal(gt=0)] = Field(None, example=150.00)


class BillResponse(BaseModel):
    id: int
    user_id: int
    date: datetime
    total_amount: float


@router.post("/", response_model=BillResponse, response_class=JSONResponse)
async def create_bill(bill: BillCreate, user=Depends(verify_token)) -> JSONResponse:
    """
    Create a new bill.

    Creates a bill record with the provided data. Protected by JWT authentication.
    """
    bill_service = BillService()
    try:
        new_bill = bill_service.create_bill(bill.dict())
        return JSONResponse(
            content=HttpResponse.success(new_bill, "Bill created successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[BillController] Failed to create bill", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bill",
        ) from error


@router.get("/", response_model=List[BillResponse], response_class=JSONResponse)
async def list_bills(user=Depends(verify_token)) -> JSONResponse:
    """
    Retrieve all bills.

    Returns a list of all bills. Protected by JWT authentication.
    """
    bill_service = BillService()
    try:
        bills = bill_service.get_all_bills()
        return JSONResponse(
            content=HttpResponse.success(bills, "Bills retrieved successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[BillController] Failed to retrieve bills", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bills",
        ) from error


@router.get("/{bill_id}", response_model=BillResponse, response_class=JSONResponse)
async def get_bill(bill_id: int, user=Depends(verify_token)) -> JSONResponse:
    """
    Retrieve a bill by its ID.

    Protected by JWT authentication.
    """
    bill_service = BillService()
    try:
        bill = bill_service.get_bill_by_id(bill_id)
        if not bill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill not found",
            )
        return JSONResponse(
            content=HttpResponse.success(bill, "Bill retrieved successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[BillController] Failed to retrieve bill", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bill",
        ) from error


@router.put("/{bill_id}", response_model=BillResponse, response_class=JSONResponse)
async def update_bill(
    bill_id: int, bill: BillUpdate, user=Depends(verify_token)
) -> JSONResponse:
    """
    Update a bill by its ID.

    Protected by JWT authentication.
    """
    bill_service = BillService()
    try:
        updated_bill = bill_service.update_bill(bill_id, bill.dict(exclude_unset=True))
        if not updated_bill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill not found",
            )
        return JSONResponse(
            content=HttpResponse.success(updated_bill, "Bill updated successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[BillController] Failed to update bill", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bill",
        ) from error


@router.delete("/{bill_id}", response_class=JSONResponse)
async def delete_bill(bill_id: int, user=Depends(verify_token)) -> JSONResponse:
    """
    Delete a bill by its ID.

    Protected by JWT authentication.
    """
    bill_service = BillService()
    try:
        success = bill_service.delete_bill(bill_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill not found",
            )
        return JSONResponse(
            content=HttpResponse.success(None, "Bill deleted successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[BillController] Failed to delete bill", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bill",
        ) from error
