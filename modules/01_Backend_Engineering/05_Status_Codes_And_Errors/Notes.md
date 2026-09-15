# Topic 05 — Status Codes and Error Responses

> **Single learning goal:** The status code tells the client what happened; the response body explains it.

## 🌱 One Endpoint, Several Outcomes

Consider:

```http
GET /products/101
```

The route and method tell the server what the client wants. But the request can end in different ways:

- The product exists.
- The product does not exist.
- The client is not allowed to see it.
- The database is temporarily unavailable.
- The application encounters an unexpected bug.

Returning the same response for every outcome would force the client to inspect text and guess what happened.

HTTP status codes give clients a standard outcome signal:

```http
HTTP/1.1 200 OK
```

or:

```http
HTTP/1.1 404 Not Found
```

The status code is part of the **status line**, not a header.

---

## 🧭 The Mental Model

```text
Status code = outcome category
Response body = useful explanation
```

Example:

```http
HTTP/1.1 404 Not Found
Content-Type: application/json
X-Correlation-ID: req-7f31

{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product 101 does not exist"
  }
}
```

The client can make a quick decision from `404`. The body provides application-specific detail.

---

## 🗂️ Status-Code Families

The first digit gives the broad outcome:

| Family | Meaning | Simple interpretation |
|:---:|---|---|
| `1xx` | Informational | The exchange is still progressing |
| `2xx` | Success | The operation succeeded |
| `3xx` | Redirection | Use another location or cached representation |
| `4xx` | Request/caller issue | The server cannot complete this request as sent |
| `5xx` | Server-side failure | The server failed to complete a valid request |

For our API work, we will initially focus on `2xx`, `4xx`, and `5xx`.

A useful refinement:

- `4xx` does not simply mean “blame the client.” The request may conflict with current state or lack valid credentials.
- `5xx` means the service or one of its dependencies failed while handling the request.

---

## ✅ Choosing a Success Code

### `200 OK` — successful response with content

Common for successful reads and updates:

```http
GET /products/101
HTTP/1.1 200 OK
```

The response normally contains a representation in the body.

### `201 Created` — a new resource was created

Common for successful creation:

```http
POST /products
HTTP/1.1 201 Created
Location: /products/101
```

The optional `Location` header can identify the new resource.

### `204 No Content` — success with no response body

Useful when the operation succeeded but there is nothing to return:

```http
DELETE /products/101
HTTP/1.1 204 No Content
```

A `204` response must not contain a message body.

### A practical selection rule

| Outcome | Typical code |
|---|:---:|
| Successful read with data | `200` |
| Resource successfully created | `201` |
| Successful operation with no body | `204` |

Do not choose `201` merely because the request used `POST`. Choose it because a resource was actually created.

---

## ⚠️ Choosing a Client-Error Code

### `400 Bad Request`

Use when the request is malformed or cannot be processed as a valid request at a basic level.

### `401 Unauthorized`

Despite its name, this normally means the caller is **not authenticated** with acceptable credentials:

- The credential is missing.
- The token is invalid.
- The token has expired.

### `403 Forbidden`

The server understands who the caller is, but the caller is not permitted to perform the operation.

```text
401 = Who are you? Your credentials are missing or unacceptable.
403 = I know who you are, but you cannot do this.
```

### `404 Not Found`

The requested resource does not exist—or the API deliberately does not reveal whether it exists.

```http
GET /products/999
HTTP/1.1 404 Not Found
```

### `409 Conflict`

The request conflicts with the resource's current state.

Examples:

- Creating a product with an identifier that already exists
- Updating a stale version of a resource
- Performing an operation that violates a state transition

### `422 Unprocessable Content`

The request representation can be read, but its supplied values fail validation or cannot be processed semantically.

FastAPI commonly returns `422` automatically when Pydantic validation fails—for example, when a required field is missing or a value has the wrong type.

Frameworks and API conventions differ on some `400` versus `422` cases. The important Technical Lead decision is to define a consistent contract and document it.

### `429 Too Many Requests`

The caller has exceeded an allowed request rate. A server may include:

```http
Retry-After: 30
```

This tells the client when retrying may be appropriate.

---

## 🧯 Choosing a Server-Error Code

### `500 Internal Server Error`

Use for an unexpected server failure:

- An unhandled exception
- A programming error
- An unexpected internal condition

Do not expose stack traces, database statements, internal paths, secrets, or infrastructure details in the client response.

### `503 Service Unavailable`

The service is temporarily unable to handle the request.

Examples:

- Planned maintenance
- Temporary overload
- A critical dependency is unavailable

A `503` can be temporary, but clients still should not retry aggressively without limits or backoff. Retry behaviour will be covered later.

---

## 🔍 Missing Resource or Empty Collection?

These requests represent different questions:

```http
GET /products/999
```

A specific product was requested. If it does not exist, return `404`.

```http
GET /products?category=unknown
```

The products collection exists, but the filter found no matches. A normal response is:

```http
HTTP/1.1 200 OK

[]
```

An empty collection is still a successful collection query.

---

## 📦 Designing a Useful Error Body

A status code alone cannot explain your business context. Use a predictable error structure:

```json
{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product 101 does not exist",
    "details": {
      "product_id": 101
    },
    "correlation_id": "req-7f31"
  }
}
```

Each field has a purpose:

| Field | Purpose |
|---|---|
| `code` | Stable, machine-readable application error |
| `message` | Safe, human-readable explanation |
| `details` | Optional structured context |
| `correlation_id` | Links the response to server-side logs |

The HTTP status and application error code solve different problems:

```text
404                 = standard HTTP outcome
PRODUCT_NOT_FOUND   = application-specific reason
```

Clients may branch on the stable error code. They should not parse the human-readable message to make program decisions.

---

## 🚫 Do Not Return `200 OK` for an Error

This is misleading:

```http
HTTP/1.1 200 OK

{
  "success": false,
  "message": "Product not found"
}
```

Monitoring, gateways, SDKs, retry policies, and clients may all interpret `200` as success.

Prefer:

```http
HTTP/1.1 404 Not Found

{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product does not exist"
  }
}
```

The status code and body should tell the same story.

---

## ⚙️ Status Codes in FastAPI

Declare the normal success outcome on the route:

```python
from fastapi import FastAPI, status

app = FastAPI()


@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate):
    return {
        "product_id": 101,
        **product.model_dump(),
    }
```

FastAPI converts the returned data into the response body and uses `201 Created`.

Raise `HTTPException` for an expected failure:

```python
from fastapi import HTTPException, status


@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = find_product(product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PRODUCT_NOT_FOUND",
                "message": f"Product {product_id} does not exist",
            },
        )

    return product
```

Raising the exception stops normal endpoint execution. FastAPI returns the chosen status and places the supplied value under its standard `detail` field.

Request-model validation happens before the endpoint runs, so invalid input normally receives FastAPI's automatic `422` response.

For a `204` response, return no body:

```python
from fastapi import Response, status


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    delete_existing_product(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

---

## 🧠 A Technical Lead's Decision Process

When choosing an outcome:

1. Did the operation succeed? Choose the appropriate `2xx`.
2. Is the request invalid, unauthenticated, forbidden, missing a resource, or conflicting with state? Choose a specific `4xx`.
3. Did the application or a required dependency fail? Choose an appropriate `5xx`.
4. Add a consistent, safe error body.
5. Preserve the correlation ID so the incident can be traced.
6. Document outcomes in the API contract and test them.

Avoid inventing a different response shape for every endpoint.

---

## ✅ Check Your Understanding

1. Why is a status code not an HTTP header?
2. When would you choose `200`, `201`, or `204`?
3. What is the difference between `401` and `403`?
4. Why can a missing individual product return `404` while an empty product search returns `200`?
5. When might `409` be more appropriate than `400`?
6. Why should a client use an application error code instead of parsing the error message?
7. Why is returning `200` with `"success": false` harmful?
8. What information must never appear in a production error response?

---

## 🛑 Intentional Stop Point

This lesson does not yet cover:

- Global exception handlers and middleware
- Full authentication and authorization flows
- Retry algorithms and idempotency
- Gateway-specific `502` and `504` failures
- Observability standards and alerting
- Domain exception hierarchies

These concepts will be introduced when the application develops the problem that needs them.

## ➡️ Next Step

Build a focused FastAPI exercise that returns correct success codes, distinguishes common client errors, and produces a consistent error structure. Interview questions will be asked one at a time in chat after the implementation is reviewed.

## 📚 References

- [RFC 9110 — Status Codes](https://www.rfc-editor.org/rfc/rfc9110.html#section-15)
- [RFC 9110 — Client Error 4xx](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5)
- [RFC 9110 — Server Error 5xx](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.6)
- [FastAPI — Response Status Codes](https://fastapi.tiangolo.com/tutorial/response-status-code/)
- [FastAPI — Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
