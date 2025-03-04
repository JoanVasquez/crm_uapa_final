from unittest.mock import patch

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.user_routes import router

# Create a FastAPI app and include the User API router.
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_register_user_success():
    register_payload = {
        "email": "johndoe@example.com",
        "name": "John Doe",
        "password": "secretpassword",
    }
    fake_user = {"id": 1, "email": "johndoe@example.com", "name": "John Doe"}
    # Patch the global userService.save method.
    with patch(
        "app.api.user_routes.userService.save", return_value=fake_user
    ) as mock_save:
        response = client.post("/users/register", json=register_payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_user
        assert data["message"] == "User registered successfully"
        mock_save.assert_called_once()


def test_confirm_user_registration_success():
    confirm_payload = {"email": "johndoe@example.com", "confirmationCode": "123456"}
    fake_response = {"confirmed": True}
    with patch(
        "app.api.user_routes.userService.confirm_registration",
        return_value=fake_response,
    ) as mock_confirm:
        response = client.post("/users/confirm", json=confirm_payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_response
        assert data["message"] == "User confirmed successfully"
        mock_confirm.assert_called_once_with("johndoe@example.com", "123456")


def test_authenticate_user_success():
    auth_payload = {"email": "johndoe@example.com", "password": "secretpassword"}
    fake_auth = {"token": "fake_jwt_token"}
    with patch(
        "app.api.user_routes.userService.authenticate", return_value=fake_auth
    ) as mock_auth:
        response = client.post("/users/authenticate", json=auth_payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_auth
        assert data["message"] == "Authentication successful"
        mock_auth.assert_called_once_with("johndoe@example.com", "secretpassword")


def test_initiate_password_reset_success():
    reset_payload = {"email": "johndoe@example.com"}
    fake_reset = {"reset": "initiated"}
    with patch(
        "app.api.user_routes.userService.initiate_password_reset",
        return_value=fake_reset,
    ) as mock_initiate:
        response = client.post("/users/password-reset/initiate", json=reset_payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_reset
        assert data["message"] == "Password reset initiated successfully"
        mock_initiate.assert_called_once_with("johndoe@example.com")


def test_complete_password_reset_success():
    complete_payload = {
        "email": "johndoe@example.com",
        "newPassword": "newsecretpassword",
        "confirmationCode": "123456",
    }
    fake_complete = {"reset": "completed"}
    with patch(
        "app.api.user_routes.userService.complete_password_reset",
        return_value=fake_complete,
    ) as mock_complete:
        response = client.post("/users/password-reset/complete", json=complete_payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_complete
        assert data["message"] == "Password reset completed successfully"
        mock_complete.assert_called_once_with(
            "johndoe@example.com", "newsecretpassword", "123456"
        )


def test_get_user_by_id_success():
    fake_user = {"id": 1, "email": "johndoe@example.com", "name": "John Doe"}
    with patch(
        "app.api.user_routes.userService.find_by_id", return_value=fake_user
    ) as mock_find:
        response = client.get("/users/1")
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_user
        assert data["message"] == "User retrieved successfully"
        mock_find.assert_called_once_with(1)


def test_get_user_by_id_not_found():
    with patch(
        "app.api.user_routes.userService.find_by_id", return_value=None
    ) as mock_find:
        response = client.get("/users/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        data = response.json()
        # Expect error message "User not found" (could be in "message" or "detail")
        assert (
            "User not found" in data.get("message", "")
            or data.get("detail") == "User not found"
        )
        mock_find.assert_called_once_with(999)


def test_update_user_success():
    update_payload = {"email": "janedoe@example.com", "name": "Jane Doe"}
    fake_updated_user = {"id": 1, "email": "janedoe@example.com", "name": "Jane Doe"}
    with patch(
        "app.api.user_routes.userService.update", return_value=fake_updated_user
    ) as mock_update:
        response = client.put("/users/1", json=update_payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_updated_user
        assert data["message"] == "User updated successfully"
        mock_update.assert_called_once_with(1, update_payload)


def test_update_user_not_found():
    update_payload = {"email": "janedoe@example.com"}
    with patch(
        "app.api.user_routes.userService.update", return_value=None
    ) as mock_update:
        response = client.put("/users/999", json=update_payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        data = response.json()
        assert (
            "User not found" in data.get("message", "")
            or data.get("detail") == "User not found"
        )
        mock_update.assert_called_once_with(999, update_payload)
