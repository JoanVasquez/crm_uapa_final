"""
User API routes.

This module defines API endpoints for user registration, confirmation, authentication,
password reset, retrieval, and updates.

# pylint: disable=broad-exception-caught
"""

from typing import Optional

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from app.services.user_service import UserService
from app.utils.http_response import HttpResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
userService = UserService()

router = APIRouter()


# ---------------------------
# Pydantic models for request bodies
# ---------------------------
class RegisterUserRequest(BaseModel):
    """Request model for registering a new user."""

    email: EmailStr = Field(..., example="johndoe@example.com")
    name: str = Field(..., example="John Doe")
    password: str = Field(..., example="secretpassword")


class ConfirmUserRegistrationRequest(BaseModel):
    """Request model for confirming user registration."""

    email: EmailStr = Field(..., example="johndoe@example.com")
    confirmationCode: str = Field(..., example="123456")


class AuthenticateUserRequest(BaseModel):
    """Request model for authenticating a user."""

    email: EmailStr = Field(..., example="johndoe@example.com")
    password: str = Field(..., example="secretpassword")


class InitiatePasswordResetRequest(BaseModel):
    """Request model for initiating a password reset."""

    email: EmailStr = Field(..., example="johndoe@example.com")


class CompletePasswordResetRequest(BaseModel):
    """Request model for completing a password reset."""

    email: EmailStr = Field(..., example="johndoe@example.com")
    newPassword: str = Field(..., example="newsecretpassword")
    confirmationCode: str = Field(..., example="123456")


class UpdateUserRequest(BaseModel):
    """Request model for updating a user."""

    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


# ---------------------------
# Endpoints
# ---------------------------
@router.post("/register", response_class=JSONResponse)
async def register_user(request_body: RegisterUserRequest) -> JSONResponse:
    """
    Register a new user.

    Converts the request body to a dictionary and calls the user service to register
    the user. Returns a JSON response with a success message, or an error response on failure.
    """
    try:
        user_data = request_body.dict()
        response = userService.save(user_data)
        return JSONResponse(
            content=HttpResponse.success(response, "User registered successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[UserController] Registration failed", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error("Failed to register user", 500, str(error)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/confirm", response_class=JSONResponse)
async def confirm_user_registration(
    request_body: ConfirmUserRegistrationRequest,
) -> JSONResponse:
    """
    Confirm user registration.

    Validates the request and calls the user service to confirm the user's registration.
    """
    try:
        data = request_body.dict()
        response = userService.confirm_registration(
            data["email"], data["confirmationCode"]
        )
        return JSONResponse(
            content=HttpResponse.success(response, "User confirmed successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[UserController] User confirmation failed", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error("Failed to confirm user", 500, str(error)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/authenticate", response_class=JSONResponse)
async def authenticate_user(request_body: AuthenticateUserRequest) -> JSONResponse:
    """
    Authenticate a user.

    Extracts email and password from the request and calls the user service to authenticate.
    """
    try:
        data = request_body.dict()
        response = userService.authenticate(data["email"], data["password"])
        return JSONResponse(
            content=HttpResponse.success(response, "Authentication successful"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[UserController] Authentication failed", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error("Authentication failed", 500, str(error)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/password-reset/initiate", response_class=JSONResponse)
async def initiate_password_reset(
    request_body: InitiatePasswordResetRequest,
) -> JSONResponse:
    """
    Initiate password reset.

    Calls the user service to initiate a password reset process.
    """
    try:
        data = request_body.dict()
        response = userService.initiate_password_reset(data["email"])
        return JSONResponse(
            content=HttpResponse.success(
                response, "Password reset initiated successfully"
            ),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[UserController] Password reset initiation failed", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error(
                "Failed to initiate password reset", 500, str(error)
            ),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/password-reset/complete", response_class=JSONResponse)
async def complete_password_reset(
    request_body: CompletePasswordResetRequest,
) -> JSONResponse:
    """
    Complete password reset.

    Completes the password reset process by validating the confirmation code and updating
    the password.
    """
    try:
        data = request_body.dict()
        response = userService.complete_password_reset(
            data["email"], data["newPassword"], data["confirmationCode"]
        )
        return JSONResponse(
            content=HttpResponse.success(
                response, "Password reset completed successfully"
            ),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[UserController] Password reset completion failed", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error(
                "Failed to complete password reset", 500, str(error)
            ),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/user/{user_id}", response_class=JSONResponse)
async def get_user_by_id(user_id: int) -> JSONResponse:
    """
    Retrieve a user by their ID.

    If the user_id is missing or the user is not found, returns an appropriate error response.
    """
    try:
        if not user_id:
            logger.warning("[UserController] Missing user ID in path parameters")
            return JSONResponse(
                content=HttpResponse.error("User ID is required", 400),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = userService.find_by_id(user_id)
        if not user:
            logger.warning("[UserController] User not found with ID: %s", user_id)
            return JSONResponse(
                content=HttpResponse.error("User not found", 404),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        logger.info("[UserController] User retrieved successfully with ID: %s", user_id)
        return JSONResponse(
            content=HttpResponse.success(user, "User retrieved successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[UserController] Failed to fetch user by ID", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error("Failed to fetch user", 500, str(error)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.put("/user/{user_id}", response_class=JSONResponse)
async def update_user(user_id: int, request_body: UpdateUserRequest) -> JSONResponse:
    """
    Update a user by their ID.

    Validates the path parameter and request body, calls the user service to update the user,
    and returns the updated user.
    """
    try:
        if not user_id:
            logger.warning("[UserController] Missing user ID in path parameters")
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

        updated_user = userService.update(user_id, updated_data)
        if not updated_user:
            logger.warning(
                "[UserController] Failed to update user with ID: %s", user_id
            )
            return JSONResponse(
                content=HttpResponse.error("User not found", 404),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        logger.info("[UserController] User updated successfully with ID: %s", user_id)
        return JSONResponse(
            content=HttpResponse.success(updated_user, "User updated successfully"),
            status_code=status.HTTP_200_OK,
        )
    except Exception as error:
        logger.error("[UserController] Failed to update user", exc_info=True)
        return JSONResponse(
            content=HttpResponse.error("Failed to update user", 500, str(error)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
