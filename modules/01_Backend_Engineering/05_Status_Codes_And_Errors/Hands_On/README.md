# Hands-On Exercise — Status Codes and Error Responses

> **Time:** approximately 60–90 minutes  
> **Goal:** Make each API outcome communicate the correct HTTP status and a useful, predictable error.

## What You Will Build

Extend the in-memory Product API with four endpoints:

| Endpoint | Success outcome | Important failure |
|---|:---:|:---:|
| `GET /products/{product_id}` | `200 OK` | `404 Not Found` |
| `GET /products?category=...` | `200 OK` | Empty list is still `200` |
| `POST /products` | `201 Created` | Duplicate SKU is `409 Conflict` |
| `DELETE /products/{product_id}` | `204 No Content` | `404 Not Found` |

FastAPI should also produce `422 Unprocessable Entity` automatically when the request body fails Pydantic validation.

This exercise deliberately does not introduce global exception handlers, authentication, databases, or simulated server crashes.

---

## 1. Create the Exercise File

Create:

```text
modules/01_Backend_Engineering/05_Status_Codes_And_Errors/Hands_On/main.py
```

Run it from the repository root:

```bash
uv run uvicorn main:app --app-dir modules/01_Backend_Engineering/05_Status_Codes_And_Errors/Hands_On --reload --host 127.0.0.1 --port 8000
```

---

## 2. Create an In-Memory Product Store

Start with at least two products.

Each product should contain:

- `product_id`
- `sku`
- `name`
- `price`
- `category`

Example data:

```json
{
  "product_id": 101,
  "sku": "KEY-001",
  "name": "Keyboard",
  "price": 2500,
  "category": "electronics"
}
```

A Python dictionary keyed by `product_id` is sufficient. Persistence is outside this exercise.

Define a `ProductCreate` Pydantic model containing:

```text
sku: string
name: string
price: positive number
category: string
```

Use Pydantic validation to reject a price that is zero or negative.

---

## 3. Use One Shape for Application Errors

For errors created by your endpoint logic, use `HTTPException` and keep `detail` consistent:

```json
{
  "detail": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product 999 does not exist",
    "details": {
      "product_id": 999
    }
  }
}
```

Every application error in this exercise must include:

| Field | Meaning |
|---|---|
| `code` | Stable machine-readable value |
| `message` | Safe explanation for a human |
| `details` | Structured context relevant to the failure |

Do not return:

```json
{
  "status_code": 404,
  "message": "Not found"
}
```

with an actual HTTP status of `200`. The HTTP status and body must agree.

You may create a small helper function to build or raise errors consistently, but a global exception handler is not required yet.

---

## 4. Get One Product

Implement:

```http
GET /products/{product_id}
```

Behaviour:

- Return the product with `200 OK` when it exists.
- Return `404 Not Found` when it does not exist.
- Use error code `PRODUCT_NOT_FOUND`.
- Include the requested `product_id` inside `details`.

Test:

```bash
curl -i http://127.0.0.1:8000/products/101
```

```bash
curl -i http://127.0.0.1:8000/products/999
```

Confirm that the second response has a real HTTP `404`, not a `200` containing an error message.

---

## 5. Search the Product Collection

Implement:

```http
GET /products
GET /products?category=electronics
```

Behaviour:

- Without `category`, return all products.
- With `category`, return only matching products.
- If no product matches, return an empty JSON list with `200 OK`.

Test:

```bash
curl -i "http://127.0.0.1:8000/products?category=electronics"
```

```bash
curl -i "http://127.0.0.1:8000/products?category=unknown"
```

Explain why an empty search result is not the same as requesting one missing product.

---

## 6. Create a Product

Implement:

```http
POST /products
```

### Successful creation

When the SKU is new:

1. Generate a new product ID.
2. Store the product.
3. Return the created representation.
4. Return `201 Created`.
5. Add a `Location` response header containing the new resource path:

```http
Location: /products/<new-product-id>
```

Example request:

```bash
curl -i -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"sku":"MON-001","name":"Monitor","price":15000,"category":"electronics"}'
```

Confirm separately:

- The status line is `201 Created`.
- The response contains `Location`.
- The response body contains the generated `product_id`.

### Duplicate SKU

If the supplied SKU already belongs to a product:

- Return `409 Conflict`.
- Use error code `PRODUCT_SKU_CONFLICT`.
- Include the conflicting SKU in `details`.
- Do not add another product.

The comparison may be case-sensitive for this exercise. Document the choice in your code or README notes.

### Invalid body

Test a body with a missing field:

```bash
curl -i -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"sku":"BAD-001","name":"Invalid Product"}'
```

Then test a negative price:

```bash
curl -i -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"sku":"BAD-002","name":"Invalid Product","price":-10,"category":"test"}'
```

Both should receive FastAPI's automatic `422`, and the endpoint function should not execute.

Observe that FastAPI's automatic validation-error body differs from your application-error body. Do not customize it yet; simply record the difference. Later we will learn how production applications normalize framework and domain errors.

---

## 7. Delete a Product

Implement:

```http
DELETE /products/{product_id}
```

Behaviour:

- If the product exists, remove it and return `204 No Content`.
- The successful `204` response must have no response body.
- If the product does not exist, return `404 Not Found` using the same `PRODUCT_NOT_FOUND` error structure as the GET endpoint.

After creating a new product, delete it:

```bash
curl -i -X DELETE http://127.0.0.1:8000/products/<new-product-id>
```

Run the same request again. The first call should return `204`; the second should return `404`.

---

## 8. Inspect the OpenAPI Documentation

Open:

```text
http://127.0.0.1:8000/docs
```

Confirm:

- The POST operation documents `201` as its normal success response.
- Pydantic documents the request-body schema.
- `product_id` appears as an integer path parameter.
- `category` appears as an optional query parameter.

The documentation may not list every manually raised error automatically. We will improve error-response documentation later when we deepen the FastAPI contract.

---

## 9. Complete the Outcome Table

Run each case and record the actual status:

| Scenario | Expected |
|---|:---:|
| Read existing product | `200` |
| Read missing product | `404` |
| Search with matches | `200` |
| Search without matches | `200` with `[]` |
| Create new product | `201` |
| Create duplicate SKU | `409` |
| Create with missing field | `422` |
| Create with negative price | `422` |
| Delete existing product | `204` with no body |
| Delete the same product again | `404` |

No failure scenario should return `200 OK`.

---

<details>
<summary>Hints—open only if you are blocked</summary>

Useful imports:

```python
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field
```

A positive price can be declared with:

```python
price: float = Field(gt=0)
```

Set a response header through the injected response:

```python
response.headers["Location"] = f"/products/{product_id}"
```

A reusable error helper could accept:

```text
status_code, code, message, details
```

and build an `HTTPException` with the agreed `detail` structure.

A new in-memory ID can be generated from the current keys. Consider what should happen if the dictionary is empty.

To return `204` without a body:

```python
return Response(status_code=status.HTTP_204_NO_CONTENT)
```

</details>

---

## ✅ Completion Check

After implementing and pushing `main.py`, share that it has been pushed. I will review the code in GitHub.

Be ready to explain:

1. Why a missing individual product returns `404`, but an empty search returns `200`.
2. Why a duplicate SKU returns `409` rather than `400`.
3. Why successful creation returns `201` and includes `Location`.
4. Why a successful `204` response has no body.
5. Why the endpoint does not execute for Pydantic's `422`.
6. Why the application-error and automatic validation-error bodies currently differ.
7. What status you would choose if a required database were temporarily unavailable.

After the implementation works, interview questions will be asked one at a time in chat. We will create `Interview.md` only after reviewing your answers.
