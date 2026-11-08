import logging

from fastapi import Request

from app.repositories.products import ProductRepository
from app.services.products import ProductService


logger = logging.getLogger("uvicorn.error")


class ResourceLifeCycleMarker:
    def __init__(self):
        logger.info("[Lifecycle] Request scoped resource initiated")
        self.active = True

    def close(self):
        self.active = False
        logger.info("[Lifecycle] Request scoped resource cleaned up")


def get_shared_resource(request: Request):
    resource = getattr(request.app.state, "shared_resource", None)

    if resource is None:
        raise RuntimeError(
            "Application shared resource is not initialized"
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