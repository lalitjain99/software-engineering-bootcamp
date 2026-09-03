"""A minimal FastAPI application for observing the request-response flow."""

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Request Lifecycle Exercise")

products = {
    101: {
        "id": 101,
        "name": "Mechanical Keyboard",
        "price": 4500,
    }
}


@app.get("/products/{product_id}")
def get_product(product_id: int):
    """Return one product or an HTTP 404 response."""
    product = products.get(product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product
