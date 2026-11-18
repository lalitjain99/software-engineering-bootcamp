import pytest
from fastapi.testclient import TestClient
from dependencies import get_product_service
from services.products import ProductNotFoundError
from main import app


class FakeProductService:
    def get_product(self,product_id: int):
        if product_id == 101:
            return {
                "id": 101,
                "name": "Fan",
                "price": 4999.91,
                "category": "Electronics",
                "stock": 5
            }
        raise ProductNotFoundError(product_id=product_id)


@pytest.fixture
def client():

    app.dependency_overrides[get_product_service] = (
        lambda: FakeProductService()
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_product_service)


def test_shared_product_fields_are_compatible(client):
    response_v1 = client.get("/api/v1/products/101")
    response_v2 = client.get("/api/v2/products/101")

    assert response_v1.status_code == 200
    assert response_v2.status_code == 200

    data_v1 = response_v1.json()
    assert data_v1["id"] == 101
    assert data_v1["name"] == "Fan"
    assert data_v1["price"] == 4999.91
    assert "category" not in data_v1
    assert "stock" not in data_v1

    data_v2 = response_v2.json()
    assert data_v2["id"] == 101
    assert data_v2["name"] == "Fan"
    assert data_v2["price"] == 4999.91
    assert data_v2["category"] == "Electronics"
    assert data_v2["stock"] == 5

    assert data_v1["id"] == data_v2["id"]
    assert data_v1["name"] == data_v2["name"]
    assert data_v1["price"] == data_v2["price"]
