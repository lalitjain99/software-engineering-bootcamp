import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_product_service
from app.services.products import ProductNotFoundError

class FakeProductService:
    def get_product(self, product_id: int):
        if product_id == 1:
            return {
                "id": 1,
                "name": "Laptop",
                "price": 999.99,
            }

        raise ProductNotFoundError(product_id=product_id)


@pytest.fixture
def client():
    app.dependency_overrides[get_product_service] = ( 
        lambda: FakeProductService() 
        )
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_product_service,None)


def test_get_product_success(client):
    response = client.get("/products/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Laptop"
    assert data["price"] == 999.99


def test_get_product_failure(client):
    response = client.get("/products/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product with ID 999 was not found"

