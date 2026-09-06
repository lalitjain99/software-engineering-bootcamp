'''
Operation	Method and path	Inputs practised
Get one product	GET /stores/{store_id}/products/{product_id}	Path
Filter products	GET /stores/{store_id}/products	Path + query
Create a product	POST /stores/{store_id}/products	Path + query + body

'''


from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel



app = FastAPI(title="API input exercise")

class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    in_stock: bool = True

products = {
    7: {
        101: {
            "name": "Keyboard",
            "category": "electronics",
            "price": 2500.0,
        },
        102: {
            "name": "Mouse",
            "category": "electronics",
            "price": 1200.0,
        },
        103: {
            "name": "Desk",
            "category": "furniture",
            "price": 8000.0,
        },
    }
}



@app.get("/stores/{store_id}/products/{product_id}",status_code=status.HTTP_200_OK)
def get_product(store_id:int,product_id:int):
    if store_id not in products:
        raise HTTPException(status_code=404, detail="Store not found")
    
    store = products.get(store_id)
    if product_id not in store:
        raise HTTPException(
                    status_code=404,detail="Product not found"
                )
    product = store.get(product_id)

    return {
        "store_id":store_id,
        "product_id": product_id,
        **product
    }

@app.get("/stores/{store_id}/products",status_code=status.HTTP_200_OK)
def list_product(
        store_id:int,
        category:str | None=None,
        max_price:float | None=None,
        limit: int = 10,
    ):

    if store_id not in products:
        raise HTTPException(status_code=404, detail="Store not found")

    store = products[store_id]

    filtered_products = [
    {
        "product_id": product_id,
        **product,
    }
    for product_id, product in store.items()
    if (category is None or product["category"] == category)
    and (max_price is None or product["price"] <= max_price)
]

    return filtered_products[:limit]


@app.post("/stores/{store_id}/products",status_code=status.HTTP_201_CREATED)
def create_product(
                    store_id: int,
                    product: CreateProduct,
                    notify_supplier: bool = False
                ):
    if store_id not in products:
        raise HTTPException(status_code=404, detail="Store not found")

    product_id = max(products[store_id],default=100) + 1
    created_product = product.model_dump()

    products[store_id][product_id] = created_product
    return {
        "store_id": store_id,
        "product_id": product_id,
        **created_product,
        "notify_supplier": notify_supplier,
    }
    


