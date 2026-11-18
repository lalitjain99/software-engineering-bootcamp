from fastapi import APIRouter, HTTPException, Depends, Response
from schemas.v1.products import ProductResponse
from services.products import ProductService, ProductNotFoundError
from dependencies import get_product_service


router = APIRouter(tags=["products"],
                   prefix="/api/v1/products")

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int,response: Response, service: ProductService = Depends(get_product_service)):
    try:
        headers = {
            "Deprecation": "true",
            "Sunset": "Wed, 31 Dec 2026 23:59:59 GMT",
            "Link": '</api/v2/products/101>; rel="successor-version"'
        }
        response.headers.update(headers)
        product = service.get_product(product_id=product_id)
        return product
    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=e.message,
            headers=headers
        )
