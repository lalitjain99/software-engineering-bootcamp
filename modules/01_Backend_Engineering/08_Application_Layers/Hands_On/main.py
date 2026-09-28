from fastapi import FastAPI
from app.router import router as product_router
app = FastAPI(title="Product Application Layering Lab")

app.include_router(product_router)

