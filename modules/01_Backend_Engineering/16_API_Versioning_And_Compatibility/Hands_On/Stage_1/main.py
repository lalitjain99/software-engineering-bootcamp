from contextlib import asynccontextmanager
import logging
import uuid

from fastapi import FastAPI
from api.v1_routes.products import router as product_v1_router
from api.v2_routes.products import router as product_v2_router


logger = logging.getLogger("uvicorn.error")


class ApplicationResources:
    def __init__(self):
        self.active = True
        self.resource_id = uuid.uuid4()
        self.message = "Application starting up"

    def close(self):
        self.active = False
        self.message = "Application shutting down"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_resource = ApplicationResources()
    app.state.shared_resource = app_resource
    
    yield

    app_resource.close()

app = FastAPI(title="API versioning Demonstration",lifespan=lifespan)

app.include_router(product_v1_router)
app.include_router(product_v2_router)


@app.get("/health")
def get_health():
    return {
        "status": "ok"
    }