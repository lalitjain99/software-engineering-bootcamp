from contextlib import asynccontextmanager
import logging


from fastapi import FastAPI
from api.v1_routes.products import get_product as product_v1_router
from api.v2_routes.products import get_product as product_v2_router

class ApplicationResources:

app = FastAPI(title="API vesioning Demonstration")

app.include_router(product_v1_router)
app.include_router(product_v2_router)


@app.get("/health")
def get_health():
    return {
        "status": "ok"
    }