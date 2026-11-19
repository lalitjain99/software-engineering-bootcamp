import pytest
from fastapi.testclient import TestClient
from services.products import ProductNotFoundError
from dependencies import get_product_service
from main import app


class FakeProductService:
    def get_product(self,product_id: int):
        if product_id == 101:
            return {
            "id": 101,
            "name": "Monitor",
            "price": 999.99,
            "category": "Electronics",
            "stock": 3
        }

        if product_id == 102:
            return {
                "id": 102,
                "name": "Keyboard",
                "price": 99.99,
                "category": "Electronics",
                "stock": 6,
                "discount_percentage": 20
            }
        raise ProductNotFoundError(product_id=product_id)


@pytest.fixture
def client():
    app.dependency_overrides[get_product_service] = lambda: FakeProductService()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_product_service,None)


def test_v2_expand_phase_success(client):

    response = client.get("/api/v2/products/101")
    assert response.status_code == 200
    assert response.json() == {
        "id": 101,
        "name": "Monitor",
        "price": 999.99,
        "category": "Electronics",
        "stock": 3,
        "discount_percentage": None
    }

    response = client.get("/api/v2/products/102")
    assert response.status_code == 200
    assert response.json() == {
        "id": 102,
        "name": "Keyboard",
        "price": 99.99,
        "category": "Electronics",
        "stock": 6,
        "discount_percentage": 20
    }

def test_v1_expand_phase_success(client):

    response = client.get("/api/v1/products/102")
    assert response.status_code == 200
    assert response.json() == {
        "id": 102,
        "name": "Keyboard",
        "price": 99.99,
    }

    