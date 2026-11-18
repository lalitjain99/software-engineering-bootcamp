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

    app.dependency_overrides.pop(get_product_service, None)

def test_get_product_v1_with_deprecation_headers_success(client):
    response = client.get("/api/v1/products/101")

    assert response.status_code == 200
    assert response.json() == {
        "id": 101,
        "name": "Fan",
        "price": 4999.91,
    }
    assert response.headers["deprecation"] == "true"
    assert response.headers["sunset"] == "Thu, 31 Dec 2026 23:59:59 GMT"
    assert response.headers["link"] == (
        '</api/v2/products/101>; rel="successor-version"'
    )

def test_get_product_v1_with_deprecation_headers_failue(client):
    response = client.get("/api/v1/products/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Product with product id 999 not found"
    }
    assert response.headers["deprecation"] == "true"
    assert response.headers["sunset"] == "Thu, 31 Dec 2026 23:59:59 GMT"
    assert response.headers["link"] == (
        '</api/v2/products/999>; rel="successor-version"'
    )

def test_get_product_v2_success(client):
    response = client.get("/api/v2/products/101")

    assert response.status_code == 200
    assert response.json() == {
        "id": 101,
        "name": "Fan",
        "price": 4999.91,
        "category": "Electronics",
        "stock": 5
    }
    assert "deprecation" not in response.headers
    assert "sunset" not in response.headers
    assert "link" not in response.headers