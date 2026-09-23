from fastapi import FastAPI, Response, status
from pydantic import BaseModel, Field

app = FastAPI(title="Supplier Webhook Receiver")

received_events: list[dict] = []


class ProductData(BaseModel):
    product_id: int
    name: str
    price: float = Field(gt=0)


class ProductCreatedEvent(BaseModel):
    event_id: str
    event_type: str
    data: ProductData


@app.post(
    "/webhooks/product-created",
    status_code=status.HTTP_204_NO_CONTENT,
)
def receive_product_created(event: ProductCreatedEvent) -> Response:
    received_events.append(event.model_dump())

    print(
        "Webhook received:",
        event.event_type,
        event.event_id,
        event.data.model_dump(),
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/received-events")
def list_received_events() -> list[dict]:
    return received_events
