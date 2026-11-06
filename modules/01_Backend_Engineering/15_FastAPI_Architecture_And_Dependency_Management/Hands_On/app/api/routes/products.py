from fastapi import APIRouter, Depends
from app.dependencies import get_product_service
from app.schemas.products import ProductResponse

router = APIRouter(prefix="/products",
                   tags=["Products"])

@router.get("/products/{product_id}",response_model=ProductResponse)
def get_product(product_id:int,service = Depends(get_product_service)):
    product = service
