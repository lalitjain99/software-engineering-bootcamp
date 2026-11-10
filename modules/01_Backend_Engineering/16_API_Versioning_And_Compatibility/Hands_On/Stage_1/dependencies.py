from services.products import ProductService
from repositories.products import ProductRepository

import logging

logger = logging.getLogger("uvicorn.error")

class ApplicationResource:
    def __init__(self):
        self.active = True
        logger.info("Application resource are created")

    def close(self):
        self.active = False
        logger.info("Application resource are shutdown")



def get_product_service():
    try:
        resource = ApplicationResource()
        repository = ProductRepository()
        service = ProductService(repository=repository)
        return service
    finally:
        resource.close
