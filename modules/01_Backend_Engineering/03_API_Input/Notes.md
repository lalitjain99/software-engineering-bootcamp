# Topic 03 — Sending Input to an API

> **Single learning goal:** Put each input where its meaning is clearest: path, query string, or request body.

## 🌱 The Next Problem

HTTP methods tell the server what the client wants to do:

```http
GET   /products/101
POST  /products
PATCH /products/101
```

The operation also needs values:

- Which product?
- Which products should be filtered?
- What describes the new product?
- Which fields should change?

The method communicates the **operation**. The path, query string, and body carry the **input**.

---

## 🧭 One Mental Model

| Input meaning | Location | Example |
|---|---|---|
| Identifies the target | Path parameter | `/products/101` |
| Filters or adjusts the result | Query parameter | `/products?category=keyboard` |
| Describes structured data | Request body | `{"name": "Keyboard", "price": 2500}` |

Remember:

```text
Path  = Which resource?
Query = Which view or options?
Body  = What structured data?
```

---

## 📍 Path Parameters — Identify the Target

In this request, `101` identifies the product:

```http
GET /products/101
```

FastAPI declares the changing part inside braces:

```python
@app.get("/products/{product_id}")
def get_product(product_id: int):
    return {"product_id": product_id}
```

FastAPI extracts `101`, converts it to an integer, and passes `product_id=101` to the function. If conversion fails, the function does not run.

Use path parameters for resource identity or a clear hierarchy:

```http
GET /products/101
GET /customers/42/orders/9001
```

A path parameter is required. Without `product_id`, the route `/products/{product_id}` cannot identify the requested product.

---

## 🔎 Query Parameters — Filter or Adjust

Suppose the client wants keyboards below a particular price:

```http
GET /products?category=keyboard&max_price=5000
```

The query string begins after `?`. Multiple values are separated by `&`.

```text
Path:  /products
Query: category=keyboard&max_price=5000
```

FastAPI example:

```python
@app.get("/products")
def list_products(
    category: str | None = None,
    max_price: float | None = None,
    limit: int = 20,
):
    ...
```

Common uses include:

- Filtering: `?category=keyboard`
- Searching: `?search=wireless`
- Sorting: `?sort=price`
- Pagination: `?page=2&limit=20`
- Optional behaviour: `?include_reviews=true`

### Optional versus required

Query parameters are often optional, but not always.

A default value makes this parameter optional:

```python
def list_products(limit: int = 20):
    ...
```

No default makes this one required:

```python
def search_products(search: str):
    ...
```

Therefore, do not memorize “path means required and query means optional.” Choose the location based on meaning; decide requiredness separately.

---

## 📦 Request Body — Describe Structured Data

Creating a product requires several related values:

```http
POST /products
```

```json
{
  "name": "Mechanical Keyboard",
  "price": 4500,
  "in_stock": true
}
```

This structured representation belongs in the request body.

FastAPI applications normally describe its expected shape with a Pydantic model:

```python
from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    price: float
    in_stock: bool = True


@app.post("/products")
def create_product(product: ProductCreate):
    return product
```

FastAPI reads the body, parses the JSON, validates it, and creates a `ProductCreate` object before running the function.

The model is an API contract: it declares the fields, types, and defaults. Detailed validation will come later.

---

## 🧩 One Request Can Use All Three

Each value should be placed according to its own meaning:

```http
POST /stores/7/products?notify=true
```

```json
{
  "name": "Mechanical Keyboard",
  "price": 4500
}
```

FastAPI:

```python
@app.post("/stores/{store_id}/products")
def create_product(
    store_id: int,
    product: ProductCreate,
    notify: bool = False,
):
    ...
```

| Parameter | Location | Reason |
|---|---|---|
| `store_id` | Path | Identifies the store |
| `notify` | Query | Enables an optional behaviour |
| `product` | Body | Describes the new product |

### How FastAPI decides

For the cases in this lesson:

1. A parameter named in the route comes from the **path**.
2. A simple type such as `str`, `int`, `float`, or `bool` that is not in the path normally comes from the **query string**.
3. A Pydantic model normally comes from the **request body**.

The function signature therefore helps define both the Python function and the HTTP contract.

---

## 🤔 Path or Query?

Both can technically locate product 101:

```http
GET /products/101
GET /products?id=101
```

The path is usually clearer when product 101 is the primary resource:

```http
GET /products/101
```

The query is clearer when selecting from a collection:

```http
GET /products?category=keyboard
```

Ask:

> If I remove this value, am I still addressing the same collection or endpoint?

- Without `101`, the request no longer identifies that product → path.
- Without `category=keyboard`, `/products` still identifies the product collection → query.

This is a design heuristic, not an absolute rule.

---

## 🚫 Should GET Use a Body?

A `GET` request can technically carry content, but its meaning is not generally defined and support is unreliable.

Prefer query parameters for ordinary retrieval:

```http
GET /products?category=keyboard&max_price=5000
```

For unusually complex structured search criteria, an API may deliberately use:

```http
POST /products/search
```

with a JSON body.

Practical rule:

> Do not use a GET body as a normal replacement for query parameters.

---

## 🔐 Location Is Not Security

Query parameters appear in the URL and may be stored in browser history, logs, monitoring systems, or shared links. Do not put passwords or access tokens in them.

A request body is less visible in the URL, but it is not automatically secure. HTTPS and authentication will be covered later.

---

## 🧠 Decision Checklist

For every input, ask:

1. **Does it identify the resource?**  
   Use a path parameter.

2. **Does it filter, sort, paginate, search, or enable an option?**  
   Use a query parameter.

3. **Does it describe structured data being created or changed?**  
   Use a request body.

4. **Is it metadata rather than business data?**  
   It may belong in a header—the later headers topic.

| Requirement | Design |
|---|---|
| Retrieve order 9001 | `GET /orders/9001` |
| List pending orders | `GET /orders?status=pending` |
| Return page 3 | `GET /orders?page=3` |
| Create an order | `POST /orders` plus a body |
| Change an order address | `PATCH /orders/9001` plus a body |

---

## 🧠 Technical Lead Perspective

Input placement is part of the public API contract. Check that:

- Paths express stable resource identity.
- Filters and options are consistent across endpoints.
- Bodies use clear models instead of unrestricted dictionaries.
- Required and optional inputs are intentional.
- Sensitive data cannot leak through URLs.
- Another engineer can understand the contract without reading the implementation.

Good API design makes common requests unsurprising.

---

## ✅ Check Your Understanding

1. Why is `101` a path parameter in `GET /products/101`?
2. Where should `category=keyboard` go when listing products?
3. Why does complete product data belong in a body?
4. Can a query parameter be required?
5. How does FastAPI identify a body model?
6. Design this request using all necessary input locations:

```text
Create a product in store 7, optionally send a notification,
and provide its name and price.
```

---

## 🛑 Intentional Stop Point

This lesson does not yet cover:

- Detailed Pydantic constraints
- Nested body models
- Forms and file uploads
- URL encoding
- HTTP headers
- Authentication
- Detailed status-code selection

## ➡️ Next Step

Build one FastAPI endpoint combining a path parameter, query parameter, and validated request body. After the hands-on exercise, interview questions will be asked one at a time in chat before `Interview.md` is created.

## 📚 References

- [FastAPI — Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- [FastAPI — Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [FastAPI — Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
