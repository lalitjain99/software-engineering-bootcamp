# Topic 02 — HTTP Methods and Their Meaning

> **Single learning goal:** Choose an HTTP method that clearly expresses what the client wants to do.

## 🌱 The Problem Appears

In Topic 01, the client only retrieved a product:

```http
GET /products/101
```

Now the application must support more operations:

- View a product
- Create a product
- Replace a product
- Change only its price
- Delete a product

The path `/products/101` identifies the product, but the path alone does not tell the server what the client wants to do.

```text
/products/101  → Which product?
HTTP method   → What should happen to it?
```

That is why HTTP provides methods.

---

## 🧭 Method as Intent

An HTTP method communicates the client's **intention**.

A useful design principle is:

```text
Path identifies a resource.
Method identifies the intended operation.
```

For example:

| Client intention | Method and path |
|---|---|
| Read product 101 | `GET /products/101` |
| Replace product 101 | `PUT /products/101` |
| Change part of product 101 | `PATCH /products/101` |
| Delete product 101 | `DELETE /products/101` |
| Create a product | `POST /products` |

The method is not decoration. It gives the request a predictable meaning for developers, frameworks, clients, and other web components.

---

## 📖 GET — Retrieve Information

Use `GET` when the client wants to read a resource.

```http
GET /products/101
```

FastAPI route:

```python
@app.get("/products/{product_id}")
def get_product(product_id: int):
    return products[product_id]
```

A `GET` request should not intentionally change business data.

For example, this would be misleading:

```http
GET /products/101/delete
```

A client, browser, or automated tool may repeat a `GET` request because it expects reading to be harmless. Using `GET` to delete data violates that expectation.

### Mental model

```text
GET = Show me the current representation of this resource.
```

---

## ➕ POST — Submit Something for Processing

Use `POST` when the client submits data to a resource for processing. Creating a new resource inside a collection is its most common use.

```http
POST /products
```

Example request body:

```json
{
  "name": "Wireless Mouse",
  "price": 1800
}
```

The server may create product `102` and assign its identifier.

FastAPI route:

```python
@app.post("/products")
def create_product(product: dict):
    ...
```

`POST` is broader than “create.” It can represent a command or processing operation when it does not fit the meaning of the other methods.

For example:

```http
POST /orders/123/cancel
```

Here, `cancel` is a business action rather than a simple replacement or deletion.

### Mental model

```text
POST = Process this submitted information as a new operation.
```

---

## 🔄 PUT — Replace a Resource

Use `PUT` when the client wants to replace the complete representation of a resource at a known path.

```http
PUT /products/101
```

Example body:

```json
{
  "name": "Mechanical Keyboard Pro",
  "price": 5000
}
```

The request says: “Make product `101` look like this representation.”

FastAPI route:

```python
@app.put("/products/{product_id}")
def replace_product(product_id: int, product: dict):
    ...
```

A `PUT` request normally communicates complete replacement, not “change whichever fields happen to be present.”

### Mental model

```text
PUT = Replace the resource at this known location with this representation.
```

---

## ✏️ PATCH — Change Part of a Resource

Use `PATCH` when the client wants to modify only part of an existing resource.

```http
PATCH /products/101
```

Example body:

```json
{
  "price": 4300
}
```

The product name remains unchanged because the request modifies only the price.

FastAPI route:

```python
@app.patch("/products/{product_id}")
def update_product(product_id: int, changes: dict):
    ...
```

### Mental model

```text
PATCH = Apply these partial changes to the resource.
```

---

## 🗑️ DELETE — Remove a Resource

Use `DELETE` when the client wants the resource removed.

```http
DELETE /products/101
```

FastAPI route:

```python
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    ...
```

### Mental model

```text
DELETE = Remove the resource at this location.
```

Whether deletion is permanent or implemented as a soft deletion is an internal design decision. The method still communicates that the resource should no longer be available in its normal active form.

---

## 🛡️ Safe Methods

A method is **safe** when the client is asking only to retrieve information, not to change business state.

Among the methods in this lesson:

```text
GET is safe.
POST, PUT, PATCH, and DELETE are not safe.
```

A server may still write access logs or update internal metrics during a `GET`. That does not change the client's intended operation: the client asked only to read data.

Why safety matters:

- Clients can retrieve information without requesting a business change.
- Automated systems can treat read operations differently from write operations.
- Security and operational rules can distinguish viewing from modification.

---

## 🔁 Idempotent Methods

An operation is **idempotent** when repeating the same request has the same intended final effect as performing it once.

Imagine a network problem: the server processes a request, but the client does not receive the response. The client does not know whether the operation succeeded and may retry.

### PUT example

```text
Set product 101 price to 5000.
Set product 101 price to 5000 again.
```

The final price remains `5000`. The operation is idempotent.

### POST example

```text
Create a new product.
Create a new product again.
```

The server may create two products. `POST` is not idempotent by default.

### DELETE example

```text
Delete product 101.
Delete product 101 again.
```

After either sequence, product `101` is absent. The second response might differ—for example, it may say the product no longer exists—but the intended final state is the same.

This gives us an important rule:

> Idempotency concerns the intended effect, not whether every repeated response is identical.

### PATCH depends on the operation

Setting a price can be idempotent:

```text
Set price to 4300.
```

Incrementing a price may not be:

```text
Increase price by 100.
```

Repeating the second operation changes the result again.

---

## 📊 Method Properties

| Method | Primary meaning | Safe? | Idempotent by standard meaning? |
|---|---|:---:|:---:|
| `GET` | Retrieve | Yes | Yes |
| `POST` | Submit/process, commonly create | No | No |
| `PUT` | Replace at a known location | No | Yes |
| `PATCH` | Partially modify | No | Depends on the change |
| `DELETE` | Remove | No | Yes |

These properties describe the intended semantics. Application bugs or badly designed endpoints can still violate them.

---

## 🧠 Choosing a Method

Start with the client's intention:

```text
Read a resource?
  → GET

Create or submit a new operation?
  → POST

Replace the complete resource at a known path?
  → PUT

Change only selected parts?
  → PATCH

Remove the resource?
  → DELETE
```

Avoid paths that repeat the method as an action:

| Less expressive | Clearer HTTP design |
|---|---|
| `POST /getProduct/101` | `GET /products/101` |
| `POST /createProduct` | `POST /products` |
| `POST /updateProduct/101` | `PUT` or `PATCH /products/101` |
| `POST /deleteProduct/101` | `DELETE /products/101` |

This is a design guideline, not a rule that every business operation must fit CRUD. Business commands such as cancelling an order can still require action-oriented paths.

---

## 🧠 Technical Lead Perspective

Choosing the correct method communicates a contract beyond the endpoint function.

A Technical Lead asks:

- Is this operation read-only or does it change business state?
- What should happen if the client repeats the request?
- Is the client creating something new or targeting an existing resource?
- Is the client replacing the entire resource or changing only part of it?
- Does this operation fit resource manipulation, or is it a distinct business command?

Method choice should reflect behaviour, not simply which decorator is easiest to use.

---

## ✅ Check Your Understanding

1. Why is a path alone insufficient to describe an API operation?
2. Which method would retrieve product `101`?
3. When would you choose `PUT` instead of `PATCH`?
4. Why is `GET /products/101/delete` a dangerous design?
5. Why is `DELETE` idempotent even if the second request returns a different response?
6. Is every `PATCH` request idempotent? Why or why not?

---

## 🛑 Intentional Stop Point

This lesson does not yet cover:

- Path versus query parameters versus request body
- Request or response headers
- Detailed status-code selection
- Authentication and authorization
- Databases
- Implementing retry protection or idempotency keys

Those topics will build on the method semantics introduced here.

## ➡️ Next Topic

The next topic asks: **where should the client place the information an endpoint needs?**

That leads to path parameters, query parameters, and request bodies.
