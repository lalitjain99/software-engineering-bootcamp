from fastapi import Request

from app.repositories.products import ProductRepository
from app.services.products import ProductService

import logging

logger = logging.getLogger("uvicorn.error")

class ResourceLifeCycleMarker:
    def __init__(self):
        logger.info("[Lifecycle] Request scoped resource initiated")
        self.active = True

    def close(self):
        self.active = False
        logger.info("[Lifecycle] Request scoped resource cleaned up")

def get_shared_resources(request: Request):
    resource = getattr(request.app.state, "shared_resources", None)

    if resource is None:
        raise RuntimeError(
            "Application shared resources is not initialized"
            )

    return resource

def get_product_service():
    try:
        resource = ResourceLifeCycleMarker()
        repository = ProductRepository()
        service = ProductService(repository)
        yield service
    finally:
        resource.close()