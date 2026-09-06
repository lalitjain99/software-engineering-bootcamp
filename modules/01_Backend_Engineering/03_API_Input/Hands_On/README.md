# Hands-On Exercise — Place API Inputs Correctly

> **Time:** approximately 45–60 minutes  
> **Goal:** Build endpoints that deliberately use path parameters, query parameters, and a validated request body.

## What You Will Build

A small store-specific Product API using an in-memory dictionary.

| Operation | Method and path | Inputs practised |
|---|---|---|
| Get one product | `GET /stores/{store_id}/products/{product_id}` | Path |
| Filter products | `GET /stores/{store_id}/products` | Path + query |
| Create a product | `POST /stores/{store_id}/products` | Path + query + body |

Do not add a database, service layer, authentication, or advanced validation. This exercise is only about input placement.

---

## 1. Create the Exercise File

Create:

```text
modules/01_Backend_Engineering/03_API_Input/Hands_On/main.py
```

Use this starting data:

```python
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
```

The outer key is `store_id` and the inner key is `product_id`.

---

## 2. Define the Request-Body Contract

Create a Pydantic model named `ProductCreate` containing:

| Field | Type | Required? |
|---|---|:---:|
| `name` | `str` | Yes |
| `category` | `str` | Yes |
| `price` | `float` | Yes |
| `in_stock` | `bool` | No—default `True` |

Use this model as the body parameter of the create endpoint. Do not accept the body as an unrestricted `dict` and do not use `Body(...)`.

---

## 3. Retrieve One Product

Implement:

```http
GET /stores/{store_id}/products/{product_id}
```

Requirements:

- `store_id` must be an integer path parameter.
- `product_id` must be an integer path parameter.
- Return both IDs with the product information.
- Return `404` when the store or product does not exist.

Successful response shape:

```json
{
  "store_id": 7,
  "product_id": 101,
  "name": "Keyboard",
  "category": "electronics",
  "price": 2500.0
}
```

Test:

```bash
curl -i http://127.0.0.1:8000/stores/7/products/101
```

Then replace `7` or `101` with `abc`. Observe whether your function executes.

---

## 4. Filter the Product Collection

Implement:

```http
GET /stores/{store_id}/products
```

Use these query parameters:

| Parameter | Type | Default | Meaning |
|---|---|---:|---|
| `category` | `str \| None` | `None` | Return only this category |
| `max_price` | `float \| None` | `None` | Return products at or below this price |
| `limit` | `int` | `10` | Return at most this many products |

Apply only filters that the client supplied. Include `product_id` in every returned item.

Test the endpoint gradually:

```bash
curl -i http://127.0.0.1:8000/stores/7/products
```

```bash
curl -i "http://127.0.0.1:8000/stores/7/products?category=electronics"
```

```bash
curl -i "http://127.0.0.1:8000/stores/7/products?category=electronics&max_price=1500&limit=1"
```

Also try:

```bash
curl -i "http://127.0.0.1:8000/stores/7/products?max_price=cheap"
```

Explain why the last request should fail before your function runs.

---

## 5. Combine Path, Query, and Body

Implement:

```http
POST /stores/{store_id}/products?notify_supplier=true
```

Inputs:

- `store_id` → integer path parameter
- `notify_supplier` → optional Boolean query parameter with default `False`
- `product` → `ProductCreate` request body

Generate the next product ID inside the selected store and return:

- `store_id`
- `product_id`
- All validated product fields
- The converted `notify_supplier` value

Example request:

```bash
curl -i -X POST "http://127.0.0.1:8000/stores/7/products?notify_supplier=true" -H "Content-Type: application/json" -d '{"name":"Monitor","category":"electronics","price":15000,"in_stock":true}'
```

Confirm that the response contains:

```json
{
  "store_id": 7,
  "product_id": 104,
  "name": "Monitor",
  "category": "electronics",
  "price": 15000.0,
  "in_stock": true,
  "notify_supplier": true
}
```

The exact field order does not matter.

Now repeat the request without `?notify_supplier=true` and observe the default value.

---

## 6. Observe Body Validation

Send a body that omits `price`:

```bash
curl -i -X POST "http://127.0.0.1:8000/stores/7/products" -H "Content-Type: application/json" -d '{"name":"Monitor","category":"electronics"}'
```

Then send the wrong type:

```bash
curl -i -X POST "http://127.0.0.1:8000/stores/7/products" -H "Content-Type: application/json" -d '{"name":"Monitor","category":"electronics","price":"expensive"}'
```

For each request, identify:

- Which input location failed
- Which field failed
- Whether the endpoint function ran

---

## 7. Inspect FastAPI Documentation

Open:

```text
http://127.0.0.1:8000/docs
```

For the create endpoint, confirm that FastAPI displays:

- `store_id` under path parameters
- `notify_supplier` under query parameters
- `ProductCreate` as the request body schema

Connect each displayed location to the endpoint's function signature.

---

## 8. Run from the Repository Root

The repository uses the shared root environment:

```bash
uv sync
```

Start this exercise from the repository root:

```bash
uv run uvicorn main:app --app-dir modules/01_Backend_Engineering/03_API_Input/Hands_On --reload --host 127.0.0.1 --port 8000
```

---

<details>
<summary>Hints—open only if you are blocked</summary>

A suitable create-model shape is:

```python
class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    in_stock: bool = True
```

A suitable filter signature is:

```python
def list_products(
    store_id: int,
    category: str | None = None,
    max_price: float | None = None,
    limit: int = 10,
):
    ...
```

Convert a Pydantic object into a dictionary using:

```python
product.model_dump()
```

Generate an ID inside one store using:

```python
product_id = max(store_products, default=100) + 1
```

</details>

---

## ✅ Completion Check

After implementing and pushing `main.py`, share:

1. The commit or tell me it has been pushed.
2. The response from the combined `POST` request.
3. Why `store_id` belongs in the path.
4. Why `notify_supplier` belongs in the query string.
5. Why the product belongs in the body.
6. What happened for an invalid path value, invalid query value, and invalid body.
7. What changed when `notify_supplier` was omitted.

I will review the implementation in GitHub. After the code works, I will ask the interview questions one at a time here in chat. We will create `Interview.md` only after reviewing your answers.
