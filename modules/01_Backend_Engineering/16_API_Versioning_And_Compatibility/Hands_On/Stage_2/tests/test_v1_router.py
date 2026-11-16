import pytest
from fastapi.testclient import TestClient
from dependencies import get_product_service
from services.products import ProductNotFoundError
from main import app


class FakeProductService:
    def get_product(self,product_id: int):
        if product_id == 1:
            return {
                "id": 1,
                "name": "Shirt",
                "price": 499.96,
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


def test_get_products_v1(client):
    response = client.get("/products/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Shirt"
    assert data["price"] == 499.96