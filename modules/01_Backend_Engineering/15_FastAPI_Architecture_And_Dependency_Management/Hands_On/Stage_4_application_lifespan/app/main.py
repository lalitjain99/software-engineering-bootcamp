from fastapi import FastAPI
from app.api.routes.products import router as product_router

app = FastAPI(title="Product API")

app.include_router(product_router)

@app.get("/health")
def health() -> dict[str,str]:
    return {"status": "ok"}