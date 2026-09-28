from fastapi import APIRouter, HTTPException
from app.schemas import ProductResponse, ProductCreate
from app.repository import ProductRepository
from app.service import ProductService
from app.exceptions import DuplicateSkuError, ProductNotFoundError

router = APIRouter()

product_repository = ProductRepository()
product_service = ProductService(product_repository)

@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=201,
)
def create_product(product: ProductCreate) -> dict:
    try:
        return product_service.create_product(
            name=product.name,
            sku=product.sku,
            category=product.category,
            price=product.price,
            )
    except DuplicateSkuError as e:
        raise HTTPException(
            status_code= 409,
            detail= str(e)
        ) from e
    


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
)
def get_product(product_id: int) -> dict:
    try:
        product = product_service.get_product(product_id)
        return product
    except ProductNotFoundError  as e:
        raise HTTPException(
            status_code= 404,
            detail= str(e)
        ) from e
    


@router.get(
    "/products",
    response_model=list[ProductResponse],
)
def list_products(
    category: str | None = None,
) -> list[dict]:
    try: 
        stored_products = product_service.list_products(category=category)
        return stored_products
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail= e
        )

