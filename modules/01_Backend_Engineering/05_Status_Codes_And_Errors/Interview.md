# Topic 05 — Status Codes and Error Responses: Interview Guide

> Reviewed answers from the chat interview, refined for Senior Engineer and Technical Lead discussions.

## 🌱 Foundation Questions

### 1. Why does a missing product return `404`, while an empty search returns `200`?

**Answer**

```http
GET /products/999
```

This asks for one specific resource. If product `999` does not exist, return:

```http
404 Not Found
```

By contrast:

```http
GET /products?category=unknown
```

is a valid query against an existing collection. The query succeeded but found zero matches, so return:

```http
200 OK
Content-Type: application/json

[]
```

An empty collection is not the same as a missing individual resource. Say “empty collection” rather than “empty response,” because the response still contains a JSON body.

---

### 2. Why use `200`, `201`, and `204` for different successful operations?

**Answer**

| Outcome | Code | Meaning |
|---|:---:|---|
| Product read successfully and returned | `200 OK` | Success with a response representation |
| New product created | `201 Created` | A resource was created |
| Product deleted with nothing to return | `204 No Content` | Success without a response body |

A `201` response may return the created representation and a `Location` header:

```http
Location: /products/103
```

A `204` response must not contain a response body.

The HTTP method alone does not decide the status. A `POST` does not always mean `201`, and a `DELETE` does not always mean `204`; the actual outcome determines the code.

---

### 3. Why does a duplicate SKU return `409`, while a missing field returns `422`?

**Answer**

A duplicate SKU request is structurally valid and passes Pydantic validation. The endpoint executes, but application logic discovers a conflict with current server state, so it returns:

```http
409 Conflict
```

A request missing the required `price` field does not satisfy the request schema. FastAPI and Pydantic reject it before the endpoint executes:

```http
422 Unprocessable Entity
```

The JSON may be syntactically readable, but its data cannot be processed because it fails schema validation.

---

### 4. What is the difference between `401` and `403`?

**Answer**

```text
401 = Authentication did not succeed
403 = Authentication succeeded, but permission is insufficient
```

Examples:

- Missing, invalid, or expired access token → `401 Unauthorized`
- Valid employee token attempting an administrator-only operation → `403 Forbidden`

Despite its name, `401 Unauthorized` normally represents an authentication failure.

---

## 🧩 Applied Questions

### 5. Why is returning `200 OK` with an error body harmful?

**Answer**

This response contradicts itself:

```http
HTTP/1.1 200 OK

{
  "success": false,
  "message": "Product not found"
}
```

The HTTP contract says success, while the JSON says failure. Return a real `404` with a useful application error:

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product 999 does not exist"
  }
}
```

Correct status codes matter because:

- Clients can select the correct UI or control flow.
- HTTP libraries can detect failures through functions such as `raise_for_status()`.
- SDKs can map outcomes to typed results or exceptions.
- Gateways can apply policies using `2xx`, `4xx`, `429`, and `5xx`.
- Monitoring can calculate correct error rates and trigger alerts.
- Retry logic can distinguish permanent failures from temporary failures.

These components understand standard HTTP outcomes but usually do not understand a custom `"success": false` field.

HTTP status codes belong to the HTTP application protocol. Lower-level protocols such as TCP do not interpret `200` or `404`.

---

### 6. What should an API return when a required database is temporarily unavailable?

**Answer**

Return:

```http
503 Service Unavailable
```

A `404` is incorrect because the product may exist—the service cannot currently check. A `500` describes an unexpected internal failure, while `503` communicates temporary inability to serve the request because a critical dependency is unavailable.

The client must not retry immediately and indefinitely. It should:

- Use a limited number of attempts.
- Wait between attempts using backoff.
- Respect `Retry-After` when supplied.
- Avoid blindly retrying non-idempotent operations unless an idempotency mechanism exists.

Detailed retry design is covered later in the roadmap.

---

## 🧭 Technical Lead Questions

### 7. What is the purpose of each field in a structured error body?

**Answer**

```json
{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product 999 does not exist",
    "details": {
      "product_id": 999
    },
    "correlation_id": "req-123"
  }
}
```

| Field | Purpose |
|---|---|
| `code` | Stable, machine-readable application error identifier |
| `message` | Safe, human-readable explanation |
| `details` | Structured context for this occurrence |
| `correlation_id` | Connects the client-visible failure to logs across components |

Clients should branch on `code`, not parse `message`. Messages can be reworded, expanded, or translated, while the stable application code remains part of the API contract.

The body must not expose stack traces, credentials, database statements, internal paths, or sensitive infrastructure details.

---

### 8. Why do application errors and FastAPI validation errors have different bodies, and how can they be normalized?

**Answer**

The application creates its `404` and `409` responses explicitly through `HTTPException`, using the custom `detail` structure chosen by the service.

FastAPI creates a `422` automatically when Pydantic validation fails before the endpoint executes. It therefore uses FastAPI's framework-defined validation-error structure.

In a production service, a Technical Lead can define centralized exception handlers for:

- FastAPI/Starlette `HTTPException`
- Pydantic request-validation errors
- Domain-specific application exceptions
- Unexpected exceptions

Those handlers translate different internal failures into one documented external error contract. Shared response models and OpenAPI documentation can describe that contract. This avoids copying error-formatting logic into every endpoint.

The handler should preserve the correct HTTP status, attach a correlation ID, redact sensitive data, and log internal diagnostic detail safely.

---

## ⚠️ Common Mistakes

### Returning `200` for failures

A JSON flag does not replace the HTTP status. Infrastructure may count the request as successful.

### Choosing status codes only from the HTTP method

Choose the code from the outcome. Not every `POST` creates a resource, and not every `DELETE` returns no content.

### Confusing an empty collection with a missing resource

A valid collection query with zero results normally returns `200` with `[]`. A missing specifically addressed resource normally returns `404`.

### Confusing `401` and `403`

Use `401` when authentication is absent or unacceptable. Use `403` when identity is known but permission is insufficient.

### Using `404` when a dependency fails

The resource may exist. A temporarily unavailable required dependency normally points to `503`.

### Retrying immediately and forever

Unbounded retries can worsen an outage. Use limits, backoff, and safe retry semantics.

### Making clients parse error messages

Messages are written for people and may change. Clients should use stable application error codes.

### Returning a body with `204`

`204 No Content` must not contain a response body.

### Exposing internal diagnostics

Log detailed exceptions internally with a correlation ID. Return only safe information to the client.

### Formatting every error inside every endpoint

Centralize translation with shared exceptions and handlers once the application reaches that level of architecture.

---

## ✅ Completion Check

You should now be able to:

- Select status codes based on outcomes rather than methods
- Distinguish missing resources from empty collections
- Explain `401`, `403`, `404`, `409`, `422`, `500`, and `503`
- Design a stable, safe application error contract
- Explain how status codes affect clients and production infrastructure
- Describe how a production FastAPI service can normalize errors centrally
