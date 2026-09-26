from fastapi import FastAPI, HTTPException
from app.schemas import ProductResponse,ProductCreate
from app.repository import products

app = FastAPI(title="Product Application Layering Lab")




@app.post(
    "/products",
    response_model=ProductResponse,
    status_code=201,
)
def create_product(product: ProductCreate) -> dict:
    normalized_sku = product.sku.strip().upper()

    for existing_product in products.values():
        if existing_product["sku"] == normalized_sku:
            raise HTTPException(
                status_code=409,
                detail=f"Product with SKU {normalized_sku} already exists",
            )

    product_id = max(products, default=100) + 1

    created_product = {
        "id": product_id,
        "name": product.name.strip(),
        "sku": normalized_sku,
        "category": product.category.strip().lower(),
        "price": product.price,
    }

    products[product_id] = created_product
    return created_product


@app.get(
    "/products/{product_id}",
    response_model=ProductResponse,
)
def get_product(product_id: int) -> dict:
    product = products.get(product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail=f"Product {product_id} was not found",
        )

    return product


@app.get(
    "/products",
    response_model=list[ProductResponse],
)
def list_products(
    category: str | None = None,
) -> list[dict]:
    stored_products = list(products.values())

    if category is None:
        return stored_products

    normalized_category = category.strip().lower()

    return [
        product
        for product in stored_products
        if product["category"] == normalized_category
    ]
