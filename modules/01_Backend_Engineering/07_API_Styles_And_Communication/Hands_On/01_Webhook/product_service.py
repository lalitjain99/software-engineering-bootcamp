import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, status
from pydantic import BaseModel, Field

app = FastAPI(title="Product Service")

WEBHOOK_URL = "http://127.0.0.1:8001/webhooks/product-created"

products: list[dict] = []


class ProductCreate(BaseModel):
    name: str
    price: float = Field(gt=0)


def deliver_webhook(event: dict) -> dict:
    request = Request(
        WEBHOOK_URL,
        data=json.dumps(event).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=3) as response:
            return {
                "status": "delivered",
                "receiver_status_code": response.status,
            }
    except HTTPError as exc:
        return {
            "status": "failed",
            "receiver_status_code": exc.code,
        }
    except URLError:
        return {
            "status": "failed",
            "receiver_status_code": None,
        }


@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product_input: ProductCreate) -> dict:
    product = {
        "product_id": 101 + len(products),
        **product_input.model_dump(),
    }
    products.append(product)

    event = {
        "event_id": f"product-created-{product['product_id']}",
        "event_type": "product.created",
        "data": product,
    }

    delivery_result = deliver_webhook(event)

    return {
        "product": product,
        "webhook_delivery": delivery_result,
    }
