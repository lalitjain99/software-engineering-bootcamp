import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_product_service,get_shared_resource
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
    with TestClient(app) as test_client:
        yield test_client


def test_application_resource_lifecycle(client):

    resource = app.state.shared_resource
    assert resource.active is True

    first_response = client.get("/products/resource-status")
    second_response = client.get("/products/resource-status")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["resource_id"] == second_response.json()["resource_id"]

    resource_id = str(resource.resource_id)

    assert first_response.json()["resource_id"] == resource_id
    assert second_response.json()["resource_id"] == resource_id


def test_resource_closes_when_client_exits():
    with TestClient(app) as client:
        resource = app.state.shared_resource
        assert resource.active is True

        response = client.get("/products/resource-status")
        assert response.status_code == 200

