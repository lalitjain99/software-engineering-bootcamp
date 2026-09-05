"""
Hands-on: Product API

Build these endpoints using an in-memory Python dictionary:

Operation	Method	Endpoint	Expected success
List products	GET	/products	200 OK
Get one product	GET	/products/{product_id}	200 OK
Create product	POST	/products	201 Created
Replace product	PUT	/products/{product_id}	200 OK
Partially update product	PATCH	/products/{product_id}	200 OK
Delete product	DELETE	/products/{product_id}	204 No Content

products = {
    101: {
        "name": "Keyboard",
        "price": 2500
    }
}

"""

from fastapi import Body, FastAPI, HTTPException, status, Response


app = FastAPI(title="Http method exercise")


products = {
    101: {
        "name": "Keyboard",
        "price": 2500
    }
}


@app.get("/products",status_code=status.HTTP_200_OK)
def get_product_list():
    product_info = []
    for product_id,details in products.items():
        product_info.append(details)
    return product_info

#get method to fetch single product
@app.get("/products/{product_id}")
def get_product(product_id:int):
    product = products.get(product_id)

    if product is None:
        raise HTTPException(
            status_code=404, 
            detail="Product not found")

    return product

#post method
@app.post("/products", status_code=status.HTTP_201_CREATED)
def add_product(product: dict = Body(...)):
    if "name" not in product or "price" not in product:
        raise HTTPException(
            status_code=400,
            detail="product must include name and price information")

    product_id = max(products, default=100) + 1
    products[product_id] = product

    return {
        "id": product_id,
        **product,
    }

#put request
@app.put("/products/{product_id}",status_code=status.HTTP_200_OK)
def replace_product(product_id: int,product: dict = Body(...)):
    if product_id not in products:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    if "name" not in product or "price" not in product:
        raise HTTPException(
            status_code=400,
            detail="product must include name and price"
        )

    products[product_id] = product

    return {
        "id": product_id,
        **product,
    }


#patch request
@app.patch("/products/{product_id}",status_code=status.HTTP_200_OK)
def update_product(product_id: int,product: dict = Body(...)):
    if product_id not in products:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    allowed_fields = {"name", "price"}
    changes = {
        key: value
        for key, value in product.items()
        if key in allowed_fields
    }

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide name or price to update",
        )

    products[product_id].update(changes)


    return {
        "id": product_id,
        **products[product_id],
    }


#delete request
@app.delete("/products/{product_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int):
    if product_id not in products:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    del products[product_id]

    return Response(status_code=status.HTTP_204_NO_CONTENT)





