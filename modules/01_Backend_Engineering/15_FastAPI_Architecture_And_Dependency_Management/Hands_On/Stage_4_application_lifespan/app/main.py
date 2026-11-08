from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.api.routes.products import router as product_router


logger = logging.getLogger("uvicorn.error")


class ApplicationResources:
    def __init__(self):
        self.active = True
        logger.info("Application starting up")

    def close(self):
        self.active = False
        logger.info("Application shutting down")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_resource = ApplicationResources()

    app.state.shared_resource = app_resource

    yield

    app_resource.close()


app = FastAPI(title="Product API", lifespan=lifespan)

app.include_router(product_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}