from fastapi import FastAPI, Header, status,Response
import uuid
from pydantic import BaseModel

app = FastAPI(title="Exercise on API Headers")



@app.get("/inspect-headers",status_code=status.HTTP_200_OK)
def get_products(
    response: Response,
    accept: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    x_correlation_id: str | None = Header(default=None),
    x_client_version: str | None = Header(default=None),
    ):
    correlation_id = x_correlation_id or str(uuid.uuid4())
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-API-Version"] = "1"
    authorization_scheme = authorization.split(maxsplit=1)[0] if authorization else None

    return {
        "accept": accept,
        "client_version": x_client_version,
        "authorization_present": authorization is not None,
        "authorization_scheme": authorization_scheme,
        
    }


class ProductCreate(BaseModel):
    name: str
    price: float


@app.post("/products",status_code=status.HTTP_201_CREATED)
def create_product(
        product:ProductCreate,
        response: Response,
        x_correlation_id: str | None = Header(default=None),
    ):
    correlation_id = x_correlation_id or str(uuid.uuid4())
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-API-Version"] = "1"

    return {
        "name":product.name,
        "price":product.price
    }