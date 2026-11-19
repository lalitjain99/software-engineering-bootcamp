from fastapi import APIRouter, HTTPException, Depends
from schemas.v2.products import ProductResponse
from services.products import ProductService, ProductNotFoundError
from dependencies import get_product_service


router = APIRouter(tags=["products"],
                   prefix="/api/v2/products")

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, service: ProductService = Depends(get_product_service)):
    try:
        product = service.get_product(product_id=product_id)
        return product
    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=e.message
        )
