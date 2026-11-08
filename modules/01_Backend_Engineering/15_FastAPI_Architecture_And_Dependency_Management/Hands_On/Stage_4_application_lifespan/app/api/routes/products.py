from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_product_service, get_shared_resource
from app.schemas.products import ProductResponse
from app.services.products import ProductService, ProductNotFoundError


router = APIRouter(prefix="/products",
                   tags=["Products"])


@router.get("/resource-status")
def get_resource_status(resource=Depends(get_shared_resource)):
    return {"active": resource.active}


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, service: ProductService = Depends(get_product_service)):
    try:
        product = service.get_product(product_id)
        return product
    except ProductNotFoundError as e:
        raise HTTPException(status_code=404,
                            detail=e.message)



