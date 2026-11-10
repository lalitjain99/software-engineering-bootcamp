from services.products import ProductService
from repositories.products import ProductRepository

import logging

logger = logging.getLogger("uvicorn.error")


def get_product_service():
    repository = ProductRepository()
    service = ProductService(repository=repository)
    return service
        
