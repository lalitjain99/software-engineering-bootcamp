from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_get_existing_product() -> None:
    response = client.get("/products/101")

    assert response.status_code == 200
    assert response.json() == {
        "id": 101,
        "name": "Keyboard",
        "sku": "KEY-101",
        "category": "electronics",
        "price": 2500.0,
    }


def test_get_missing_product_returns_404() -> None:
    response = client.get("/products/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Product 999 was not found",
    }


def test_list_products_can_filter_by_category() -> None:
    response = client.get(
        "/products",
        params={"category": " FURNITURE "},
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 102,
            "name": "Desk",
            "sku": "DESK-102",
            "category": "furniture",
            "price": 8000.0,
        }
    ]


def test_create_product_normalizes_input() -> None:
    response = client.post(
        "/products",
        json={
            "name": "  Mouse  ",
            "sku": " mou-103 ",
            "category": " Electronics ",
            "price": 1200,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 103,
        "name": "Mouse",
        "sku": "MOU-103",
        "category": "electronics",
        "price": 1200.0,
    }


def test_duplicate_sku_returns_409() -> None:
    response = client.post(
        "/products",
        json={
            "name": "Another Keyboard",
            "sku": " key-101 ",
            "category": "electronics",
            "price": 3000,
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Product with SKU KEY-101 already exists",
    }


def test_invalid_price_returns_422() -> None:
    response = client.post(
        "/products",
        json={
            "name": "Monitor",
            "sku": "MON-104",
            "category": "electronics",
            "price": 0,
        },
    )

    assert response.status_code == 422
