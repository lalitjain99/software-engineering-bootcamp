# Topic 03 — Sending Input to an API

> **Single learning goal:** Put each input where its meaning is clearest: path, query string, or request body.

## 🌱 The Next Problem Appears

Our Product API now understands the client's intention through the HTTP method:

```http
GET    /products/101
POST   /products
PATCH  /products/101
```

But every operation also needs information:

- Which product should be retrieved?
- Which products should be filtered?
- What data describes a new product?
- Which fields should be changed?

The method tells us **what to do**. It does not carry all the values needed to do it.

We therefore need to decide where each input belongs.

---

## 🧭 One Mental Model

Use this starting rule:

| Input meaning | Location | Example |
|---|---|---|
| Identifies the target resource | Path parameter | `/products/101` |
| Filters or modifies how results are returned | Query parameter | `/products?category=keyboard` |
| Describes structured data to create or change | Request body | `{"name": "Keyboard", "price": 2500}` |

In short:

```text
Path  = Which resource?
Query = Which view or options?
Body  = What structured data?
```

This rule is more useful than memorizing syntax because it helps you design new endpoints.

---

## 📍 Path Parameters — Identify the Target

Consider:

```http
GET /products/101
```

Here, `101` identifies the product being requested.

FastAPI declares the changing part inside braces:

```python
@app.get("/products/{product_id}")
def get_product(product_id: int):
    return {"product_id": product_id}
```

When the client calls `/products/101`:

1. FastAPI extracts `101` from the path.
2. It converts the value to an integer.
3. It passes `product_id=101` to the function.
4. If conversion fails, the function does not run.

### When a path parameter fits

Use it when the value identifies a specific resource or a clear location in a resource hierarchy:

```http
GET /products/101
GET /customers/42/orders/9001
```

In the second example:

- `42` identifies the customer.
- `9001` identifies the order within that route.

### Important property

A path parameter is required because the route cannot be formed without it:

```text
/products/{product_id}
```

There is no meaningful way to omit `product_id` while still matching that route.

---

## 🔎 Query Parameters — Filter or Adjust the Result

Now suppose the client wants a list of products, but only keyboards below a certain price:

```http
GET /products?category=keyboard&max_price=5000
```

The query string starts after `?`. Multiple parameters are separated by `&`:

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

These values do not identify one product. They modify which products or how many products the server returns.

### Common uses

- Filtering: `?category=keyboard`
- Searching: `?search=wireless`
- Sorting: `?sort=price`
- Pagination: `?page=2&limit=20`
- Optional behaviour: `?include_reviews=true`

### Optional versus required

Query parameters are often optional, but they do not have to be.

With a default value, the parameter is optional:

```python
def list_products(limit: int = 20):
    ...
```

Without a default value, it is required:

```python
def search_products(search: str):
    ...
```

Therefore:

> “Path means required and query means optional” is not a reliable rule.

Choose based on meaning first. Requiredness is a separate decision.

---

## 📦 Request Body — Describe Structured Data

To create a product, the client must send several related fields:

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

Instead of accepting an unrestricted dictionary, FastAPI applications usually define the expected shape with a Pydantic model:

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

FastAPI then:

1. Reads the incoming body.
2. Parses the JSON.
3. Validates it against `ProductCreate`.
4. Creates a Python object.
5. Calls the function only when validation succeeds.

The model is an API contract: it declares which fields exist, their types, and which fields are required.

We will study deeper validation rules later. For now, notice why a structured body is clearer than placing an entire product in the URL.

---

## 🧩 One Request Can Use All Three

The three locations are not competing choices for the whole request. Each individual value should go where its meaning belongs.

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

FastAPI interprets the inputs as follows:

| Function parameter | Location | Why |
|---|---|---|
| `store_id` | Path | Its name appears in `/stores/{store_id}/products` |
| `notify` | Query | It is a simple value not declared in the path |
| `product` | Body | It is a Pydantic model |

The request therefore says:

> Create this product body inside store 7, and use the optional notification behaviour.

---

## ⚙️ How FastAPI Decides

For the cases covered in this lesson, FastAPI follows a useful pattern:

1. A parameter whose name appears in the route path comes from the **path**.
2. A simple typed parameter such as `str`, `int`, `float`, or `bool` that is not in the path normally comes from the **query string**.
3. A parameter typed as a Pydantic model normally comes from the **request body**.

Example:

```python
@app.post("/stores/{store_id}/products")
def create_product(
    store_id: int,
    product: ProductCreate,
    notify: bool = False,
):
    ...
```

The function signature is not only Python syntax. It helps define the HTTP contract and the generated API documentation.

---

## 🤔 Path Parameter or Query Parameter?

Both of these URLs can technically locate product 101:

```http
GET /products/101
GET /products?id=101
```

The first is normally clearer when product 101 is the primary resource being addressed:

```http
GET /products/101
```

A query parameter is clearer when selecting or filtering a collection:

```http
GET /products?category=keyboard
```

Ask:

> If I remove this value, am I still talking about the same endpoint and collection?

- Without `101`, `/products/101` no longer identifies that product → path.
- Without `category=keyboard`, `/products` still represents the product collection → query.

This is a design heuristic, not a law that replaces engineering judgment.

---

## 🚫 Should a GET Request Use a Body?

A `GET` request can technically carry content, but its meaning is not generally defined and support across clients, proxies, caches, and documentation tools is unreliable.

Prefer:

```http
GET /products?category=keyboard&max_price=5000
```

For an unusually complex search containing deeply structured criteria, an API may deliberately use:

```http
POST /products/search
```

with a JSON body.

The practical rule is:

> Do not use a GET body as a normal replacement for query parameters.

---

## 🔐 Do Not Confuse Location with Security

Query parameters are visible in the URL and may appear in browser history, access logs, monitoring systems, or shared links.

Do not place passwords, access tokens, or other secrets in the query string.

A request body is less visible in the URL, but it is not automatically secure. Transport security and authentication will be covered later.

---

## 🧠 Decision Checklist

For every input, ask in this order:

1. **Does it identify the resource or its location?**  
   Use a path parameter.

2. **Does it filter, sort, paginate, search, or enable an option?**  
   Use a query parameter.

3. **Does it describe structured data being created or changed?**  
   Use a request body.

4. **Is it metadata about the request rather than business data?**  
   It may belong in a header—the next topic.

### Examples

| Requirement | Design |
|---|---|
| Retrieve order 9001 | `GET /orders/9001` |
| List pending orders | `GET /orders?status=pending` |
| Return page 3 | `GET /orders?page=3` |
| Create an order | `POST /orders` plus a body |
| Change only an order address | `PATCH /orders/9001` plus a body |

---

## 🧠 Technical Lead Perspective

Input placement is part of the public API contract. A Technical Lead checks:

- Does the path express stable resource identity?
- Are filters and options represented consistently across endpoints?
- Is the body a clear, validated model instead of an unrestricted dictionary?
- Are optional and required inputs intentional?
- Could sensitive information leak through a URL?
- Will another engineer understand the contract without reading the function implementation?

Good API design makes the common request unsurprising.

---

## ✅ Check Your Understanding

1. In `GET /products/101`, why is `101` a path parameter?
2. Where should `category=keyboard` go when listing products?
3. Why is a product's complete creation data better suited to a body?
4. Can a query parameter be required?
5. How does FastAPI decide that a Pydantic model comes from the body?
6. Where would each input belong in this request?

```text
Create a product in store 7, optionally send a notification,
and provide its name and price.
```

---

## 🛑 Intentional Stop Point

This lesson does not yet cover:

- Detailed Pydantic validation and constraints
- Multiple or nested body models
- Form data and file uploads
- URL encoding details
- Request and response headers
- Authentication or transport security
- Detailed status-code selection

Those concepts will be introduced when the application needs them.

## ➡️ Next Step

Build one FastAPI endpoint that combines a path parameter, query parameter, and validated request body. After the hands-on exercise, the interview questions will be asked one at a time in chat before `Interview.md` is created.

## 📚 References

- [FastAPI — Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- [FastAPI — Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [FastAPI — Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
