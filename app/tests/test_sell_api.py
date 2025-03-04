from unittest.mock import patch

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.sell_routes import SELL_NOT_FOUND, router
from app.utils.verify_token_util import verify_token as vt

# Create a FastAPI app and include the Sell API router.
app = FastAPI()
app.include_router(router)


# Override verify_token dependency to always return a dummy user.
def override_verify_token():
    return {"id": 1, "username": "dummy_user"}


app.dependency_overrides[vt] = override_verify_token

client = TestClient(app)


def test_create_sell_success():
    sell_data = {
        "bill_id": 1,
        "product_id": 2,
        "quantity": 3,
        "sale_price": "19.99",  # Decimal input as string
    }
    fake_sell = {
        "id": 1,
        "bill_id": 1,
        "product_id": 2,
        "quantity": 3,
        "sale_price": 19.99,
    }
    with patch("app.api.sell_routes.SellService", autospec=True) as MockSellService:
        instance = MockSellService.return_value
        # Manually add the create_sell method using setattr.
        setattr(instance, "create_sell", lambda data: fake_sell)
        response = client.post("/sells/", json=sell_data)
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_sell
        assert data["message"] == "Sell created successfully"


def test_list_sells_success():
    fake_sells = [
        {
            "id": 1,
            "bill_id": 1,
            "product_id": 2,
            "quantity": 3,
            "sale_price": 19.99,
        },
        {
            "id": 2,
            "bill_id": 2,
            "product_id": 3,
            "quantity": 4,
            "sale_price": 29.99,
        },
    ]
    with patch("app.api.sell_routes.SellService", autospec=True) as MockSellService:
        instance = MockSellService.return_value
        instance.get_all_sells = lambda: fake_sells
        response = client.get("/sells/")
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_sells
        assert data["message"] == "Sells retrieved successfully"


def test_get_sell_found():
    fake_sell = {
        "id": 1,
        "bill_id": 1,
        "product_id": 2,
        "quantity": 3,
        "sale_price": 19.99,
    }
    with patch("app.api.sell_routes.SellService", autospec=True) as MockSellService:
        instance = MockSellService.return_value
        instance.get_sell_by_id = lambda sell_id: fake_sell if sell_id == 1 else None
        response = client.get("/sells/1")
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_sell
        assert data["message"] == "Sell retrieved successfully"


def test_get_sell_not_found():
    with patch("app.api.sell_routes.SellService", autospec=True) as MockSellService:
        instance = MockSellService.return_value
        instance.get_sell_by_id = lambda sell_id: None
        response = client.get("/sells/999")
        # Expect 404 with detail equal to SELL_NOT_FOUND.
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        data = response.json()
        assert data["detail"] == SELL_NOT_FOUND


def test_update_sell_success():
    updated_sell = {
        "id": 1,
        "bill_id": 1,
        "product_id": 2,
        "quantity": 5,
        "sale_price": 18.99,
    }
    with patch("app.api.sell_routes.SellService", autospec=True) as MockSellService:
        instance = MockSellService.return_value
        instance.update_sell = lambda sell_id, data: (
            updated_sell if sell_id == 1 else None
        )
        sell_update = {"quantity": 5, "sale_price": "18.99"}
        response = client.put("/sells/1", json=sell_update)
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == updated_sell
        assert data["message"] == "Sell updated successfully"


def test_update_sell_not_found():
    with patch("app.api.sell_routes.SellService", autospec=True) as MockSellService:
        instance = MockSellService.return_value
        instance.update_sell = lambda sell_id, data: None
        sell_update = {"quantity": 5, "sale_price": "18.99"}
        response = client.put("/sells/999", json=sell_update)
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        data = response.json()
        assert data["detail"] == SELL_NOT_FOUND


def test_delete_sell_success():
    with patch("app.api.sell_routes.SellService", autospec=True) as MockSellService:
        instance = MockSellService.return_value
        instance.delete_sell = lambda sell_id: True if sell_id == 1 else False
        response = client.delete("/sells/1")
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] is None
        assert data["message"] == "Sell deleted successfully"


def test_delete_sell_not_found():
    with patch("app.api.sell_routes.SellService", autospec=True) as MockSellService:
        instance = MockSellService.return_value
        instance.delete_sell = lambda sell_id: False
        response = client.delete("/sells/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        data = response.json()
        assert data["detail"] == SELL_NOT_FOUND
