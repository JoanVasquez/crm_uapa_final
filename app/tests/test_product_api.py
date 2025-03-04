from datetime import datetime
from unittest.mock import patch

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.bill_routes import BILL_NOT_FOUND, router
from app.utils.verify_token_util import verify_token as vt

# Create a FastAPI app and include the Bill API router.
app = FastAPI()
app.include_router(router)


# Override verify_token dependency to always return a dummy user.
def override_verify_token():
    return {"id": 1, "username": "dummy_user"}


app.dependency_overrides[vt] = override_verify_token

client = TestClient(app)


def test_create_bill_success():
    bill_data = {
        "user_id": 1,
        "total_amount": "100.00",  # Decimal input as string
    }
    fake_bill = {
        "id": 1,
        "user_id": 1,
        "date": datetime.utcnow().isoformat(),
        "total_amount": 100.0,
    }
    # Patch BillService as imported by the API routes.
    with patch("app.api.bill_routes.BillService", autospec=True) as MockBillService:
        instance = MockBillService.return_value
        instance.create_bill = lambda data: fake_bill
        response = client.post("/bills/", json=bill_data)
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_bill
        assert data["message"] == "Bill created successfully"


def test_list_bills_success():
    fake_bills = [
        {
            "id": 1,
            "user_id": 1,
            "date": datetime.utcnow().isoformat(),
            "total_amount": 100.0,
        },
        {
            "id": 2,
            "user_id": 2,
            "date": datetime.utcnow().isoformat(),
            "total_amount": 200.0,
        },
    ]
    with patch("app.api.bill_routes.BillService", autospec=True) as MockBillService:
        instance = MockBillService.return_value
        instance.get_all_bills = lambda: fake_bills
        response = client.get("/bills/")
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_bills
        assert data["message"] == "Bills retrieved successfully"


def test_get_bill_found():
    fake_bill = {
        "id": 1,
        "user_id": 1,
        "date": datetime.utcnow().isoformat(),
        "total_amount": 100.0,
    }
    with patch("app.api.bill_routes.BillService", autospec=True) as MockBillService:
        instance = MockBillService.return_value
        instance.get_bill_by_id = lambda bill_id: fake_bill if bill_id == 1 else None
        response = client.get("/bills/1")
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == fake_bill
        assert data["message"] == "Bill retrieved successfully"


def test_get_bill_not_found():
    with patch("app.api.bill_routes.BillService", autospec=True) as MockBillService:
        instance = MockBillService.return_value
        instance.get_bill_by_id = lambda bill_id: None
        response = client.get("/bills/999")
        # Expect 404 with detail equal to BILL_NOT_FOUND.
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        data = response.json()
        assert data["detail"] == BILL_NOT_FOUND


def test_update_bill_success():
    updated_bill = {
        "id": 1,
        "user_id": 1,
        "date": datetime.utcnow().isoformat(),
        "total_amount": 150.0,
    }
    with patch("app.api.bill_routes.BillService", autospec=True) as MockBillService:
        instance = MockBillService.return_value
        instance.update_bill = lambda bill_id, data: (
            updated_bill if bill_id == 1 else None
        )
        bill_update = {"total_amount": "150.00"}
        response = client.put("/bills/1", json=bill_update)
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] == updated_bill
        assert data["message"] == "Bill updated successfully"


def test_update_bill_not_found():
    with patch("app.api.bill_routes.BillService", autospec=True) as MockBillService:
        instance = MockBillService.return_value
        instance.update_bill = lambda bill_id, data: None
        bill_update = {"total_amount": "150.00"}
        response = client.put("/bills/999", json=bill_update)
        # Expect 404 with detail equal to BILL_NOT_FOUND.
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        data = response.json()
        assert data["detail"] == BILL_NOT_FOUND


def test_delete_bill_success():
    with patch("app.api.bill_routes.BillService", autospec=True) as MockBillService:
        instance = MockBillService.return_value
        instance.delete_bill = lambda bill_id: True if bill_id == 1 else False
        response = client.delete("/bills/1")
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["data"] is None
        assert data["message"] == "Bill deleted successfully"


def test_delete_bill_not_found():
    with patch("app.api.bill_routes.BillService", autospec=True) as MockBillService:
        instance = MockBillService.return_value
        instance.delete_bill = lambda bill_id: False
        response = client.delete("/bills/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        data = response.json()
        assert data["detail"] == BILL_NOT_FOUND
