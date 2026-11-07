from app.repositories.products import ProductRepository
from app.services.products import ProductService

import logging

logger = logging.getLogger("uvicorn.error")

class ResourceLifeCycleMarker:
    def __init__(self):
        logging.info("[Lifecycle] Request scoped resource initiated")
        self.active = True

    def close(self):
        self.active = False
        logging.info("[Lifecycle] Request scoped resource cleaned up")


def get_product_service():
    try:
        resource = ResourceLifeCycleMarker()
        repository = ProductRepository()
        service = ProductService(repository)
        yield service
    finally:
        resource.close()