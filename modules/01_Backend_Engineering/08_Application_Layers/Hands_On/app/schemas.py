from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    category: str = Field(min_length=1)
    price: float = Field(gt=0)


class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    category: str
    price: float