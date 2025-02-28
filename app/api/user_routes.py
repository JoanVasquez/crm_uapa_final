from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from core.services.user_service import UserService
from core.utils.http_response import HttpResponse
from core.utils.logger import get_logger

logger = get_logger(__name__)
userService = UserService()

router = APIRouter()


# ---------------------------
# Pydantic models for request bodies
# ---------------------------
class RegisterUserRequest(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")
    name: str = Field(..., example="John Doe")
    password: str = Field(..., example="secretpassword")


class ConfirmUserRegistrationRequest(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")
    confirmationCode: str = Field(..., example="123456")


class AuthenticateUserRequest(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")
    password: str = Field(..., example="secretpassword")


class InitiatePasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")


class CompletePasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")
    newPassword: str = Field(..., example="newsecretpassword")
    confirmationCode: str = Field(..., example="123456")


class UpdateUserRequest(BaseModel):
    # Optional fields for updating a user.
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


# ---------------------------
# Endpoints
# ---------------------------

@router.post("/register", response_class=JSONResponse)
async def register_user(request_body: RegisterUserRequest) -> JSONResponse:
    try:
        # Convert request body to a dict; using email, name, and password.
        user_data = request_body.dict()
        response = userService.save(user_data)
        return JSONResponse(
            content=HttpResponse.success(
                response, "User registered successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[UserController] Registration failed", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error(
                "Failed to register user", 500, str(error)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/confirm", response_class=JSONResponse)
async def confirm_user_registration(
    request_body: ConfirmUserRegistrationRequest,
) -> JSONResponse:
    try:
        data = request_body.dict()
        response = userService.confirm_registration(
            data["email"], data["confirmationCode"])
        return JSONResponse(
            content=HttpResponse.success(
                response, "User confirmed successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error(
            "[UserController] User confirmation failed", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error(
                "Failed to confirm user", 500, str(error)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/authenticate", response_class=JSONResponse)
async def authenticate_user(request_body: AuthenticateUserRequest) -> JSONResponse:
    try:
        data = request_body.dict()
        response = userService.authenticate(data["email"], data["password"])
        return JSONResponse(
            content=HttpResponse.success(
                response, "Authentication successful"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[UserController] Authentication failed", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error(
                "Authentication failed", 500, str(error)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/password-reset/initiate", response_class=JSONResponse)
async def initiate_password_reset(
    request_body: InitiatePasswordResetRequest,
) -> JSONResponse:
    try:
        data = request_body.dict()
        response = userService.initiate_password_reset(data["email"])
        return JSONResponse(
            content=HttpResponse.success(
                response, "Password reset initiated successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error(
            "[UserController] Password reset initiation failed", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error(
                "Failed to initiate password reset", 500, str(error)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/password-reset/complete", response_class=JSONResponse)
async def complete_password_reset(
    request_body: CompletePasswordResetRequest,
) -> JSONResponse:
    try:
        data = request_body.dict()
        response = userService.complete_password_reset(
            data["email"], data["newPassword"], data["confirmationCode"]
        )
        return JSONResponse(
            content=HttpResponse.success(
                response, "Password reset completed successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error(
            "[UserController] Password reset completion failed", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error(
                "Failed to complete password reset", 500, str(error)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/user/{id}", response_class=JSONResponse)
async def get_user_by_id(id: int) -> JSONResponse:
    try:
        if not id:
            logger.warning(
                "[UserController] Missing user ID in path parameters")
            return JSONResponse(
                content=HttpResponse.error("User ID is required", 400),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = userService.findById(id)
        if not user:
            logger.warning(f"[UserController] User not found with ID: {id}")
            return JSONResponse(
                content=HttpResponse.error("User not found", 404),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        logger.info(
            f"[UserController] User retrieved successfully with ID: {id}")
        return JSONResponse(
            content=HttpResponse.success(user, "User retrieved successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error(
            "[UserController] Failed to fetch user by ID", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error(
                "Failed to fetch user", 500, str(error)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.put("/user/{id}", response_class=JSONResponse)
async def update_user(id: int, request_body: UpdateUserRequest) -> JSONResponse:
    try:
        if not id:
            logger.warning(
                "[UserController] Missing user ID in path parameters")
            return JSONResponse(
                content=HttpResponse.error("User ID is required", 400),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        updated_data = request_body.dict(exclude_unset=True)
        if not updated_data:
            logger.warning("[UserController] Missing update data")
            return JSONResponse(
                content=HttpResponse.error("Update data is required", 400),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        updated_user = userService.update(id, updated_data)
        if not updated_user:
            logger.warning(
                f"[UserController] Failed to update user with ID: {id}")
            return JSONResponse(
                content=HttpResponse.error("User not found", 404),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        logger.info(
            f"[UserController] User updated successfully with ID: {id}")
        return JSONResponse(
            content=HttpResponse.success(
                updated_user, "User updated successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[UserController] Failed to update user", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error(
                "Failed to update user", 500, str(error)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
