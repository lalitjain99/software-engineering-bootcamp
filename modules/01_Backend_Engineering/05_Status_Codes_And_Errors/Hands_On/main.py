from fastapi import FastAPI, status, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

app = FastAPI(title="Exercise on status code and error")

class ProductCreate(BaseModel):
  sku: str
  name: str
  price: float = Field(gt=0)
  category: str


products = {101: {
                "product_id": 101,
                "sku": "KEY-001",
                "name": "Keyboard",
                "price": 2500,
                "category": "electronics"
              },
            102: {
              "product_id": 102,
              "sku": "KEY-002",
              "name": "Shirt",
              "price": 1500,
              "category": "Apperal"
                },
          }


def raise_app_error(
    status_code: int,
    code: str,
    message: str,
    details: Optional[Dict[str,Any]] = None
  ):
  raise HTTPException(
    status_code=status_code,
    detail={
      "code" : code,
      "message" : message,
      "details" : details or {}
    }
  )

#get details for a particular product
@app.get("/products/{product_id}",status_code=status.HTTP_200_OK)
def get_product(product_id:int):
  product = products.get(product_id)
  if product is None:
    raise_app_error(
      status_code=status.HTTP_404_NOT_FOUND,
      code="PRODUCT_NOT_FOUND",
      message=f"Product {product_id} does not exists",
      details={"product_id": product_id}
    )
  return product

#filter product based on category
@app.get("/products",status_code=status.HTTP_200_OK)
def product(category:str| None = None):
  products_list = []
  if not category:
    for product,details in products.items():
      products_list.append(details)
  elif category:
    for product,details in products.items():
      if details["category"] == category:
        products_list.append(details)

  return products_list if products_list else {}

    
@app.post("/products",status_code=status.HTTP_201_CREATED)
def create_product(product:ProductCreate,response:Response):
  #create product
  for id,details in products.items():
    if details['sku'] == product.sku:
      raise_app_error(
        status_code=status.HTTP_409_CONFLICT,
        code="PRODUCT_SKU_CONFLICT",
        message=f"{product.sku} already exists",
        details={"product":id,
                 "sku":details["sku"]}
      )
  product_id = max(products, default=100) + 1
  created_product = {
    "product_id": product_id,
    **product.model_dump(),
  }
  response.headers["Location"] = f"/products/{product_id}"

  return created_product


@app.delete("/products/{product_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id:int):
  if product_id in products:
    del products[product_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
  else:
    raise_app_error(
      status_code=status.HTTP_404_NOT_FOUND,
      code="PRODUCT_NOT_FOUND",
      message=f"{product_id} does not exist",
      details={"product_id": product_id}
    )
  