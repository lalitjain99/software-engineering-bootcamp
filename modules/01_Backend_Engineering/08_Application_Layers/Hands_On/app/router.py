from fastapi import APIRouter, HTTPException

from app.exceptions import DuplicateSkuError, ProductNotFoundError
from app.repository import ProductRepository
from app.schemas import ProductCreate, ProductResponse
from app.service import ProductService


router = APIRouter()

product_repository = ProductRepository()
product_service = ProductService(product_repository)


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=201,
)
def create_product(product: ProductCreate) -> dict[str, object]:
    try:
        return product_service.create_product(
            name=product.name,
            sku=product.sku,
            category=product.category,
            price=product.price,
        )
    except DuplicateSkuError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
)
def get_product(product_id: int) -> dict[str, object]:
    try:
        return product_service.get_product(product_id)
    except ProductNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.get(
    "/products",
    response_model=list[ProductResponse],
)
def list_products(
    category: str | None = None,
) -> list[dict[str, object]]:
    return product_service.list_products(category=category)
