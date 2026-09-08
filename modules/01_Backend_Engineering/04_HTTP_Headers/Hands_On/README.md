# Hands-On Exercise — Observe and Return HTTP Headers

> **Time:** approximately 45–60 minutes  
> **Goal:** Read request headers, safely inspect them, and add headers to a FastAPI response.

## What You Will Build

Create two endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /inspect-headers` | Read and safely inspect request headers |
| `POST /products` | Accept a JSON body and add response headers |

You will practise:

- `Content-Type`
- `Accept`
- `Authorization`
- `X-Correlation-ID`
- A custom `X-Client-Version` header
- FastAPI's `Header` and `Response` parameters

This is a learning exercise. Do not implement real authentication or full content negotiation yet.

---

## 1. Create the Exercise File

Create:

```text
modules/01_Backend_Engineering/04_HTTP_Headers/Hands_On/main.py
```

Run it from the repository root:

```bash
uv run uvicorn main:app --app-dir modules/01_Backend_Engineering/04_HTTP_Headers/Hands_On --reload --host 127.0.0.1 --port 8000
```

---

## 2. Build the Header-Inspection Endpoint

Implement:

```http
GET /inspect-headers
```

Read these optional request headers:

| HTTP header | Python parameter |
|---|---|
| `Accept` | `accept` |
| `Authorization` | `authorization` |
| `X-Correlation-ID` | `x_correlation_id` |
| `X-Client-Version` | `x_client_version` |

Use FastAPI's `Header` declaration for each one.

### Safety requirement

Never return or print the complete `Authorization` value.

The response body may show only:

- Whether the header was provided
- Its scheme, such as `Bearer`

Example learning response:

```json
{
  "accept": "application/json",
  "client_version": "3.4.0",
  "authorization_present": true,
  "authorization_scheme": "Bearer"
}
```

This debug-style endpoint is only for observing headers. A normal business endpoint would not return request metadata in its body.

---

## 3. Return Correlation and API-Version Headers

For `GET /inspect-headers`:

1. If the client sends `X-Correlation-ID`, use that value.
2. If it is absent, generate a value using `uuid4()`.
3. Return the chosen value in this response header:

```http
X-Correlation-ID: <chosen-value>
```

4. Also add this custom response header:

```http
X-API-Version: 1
```

Keep these values in response headers rather than adding them to the business response body.

---

## 4. Send and Inspect Request Headers

Send a request with explicit headers:

```bash
curl -i http://127.0.0.1:8000/inspect-headers -H "Accept: application/json" -H "Authorization: Bearer demo-token" -H "X-Correlation-ID: request-123" -H "X-Client-Version: 3.4.0"
```

Confirm:

- The body reports that authorization was present.
- Only `Bearer` is shown, not `demo-token`.
- The response contains `X-Correlation-ID: request-123`.
- The response contains `X-API-Version: 1`.
- The response `Content-Type` is `application/json`.

Tools such as curl and Postman may add their own default headers. Distinguish those from the headers you explicitly supplied.

---

## 5. Prove Header Names Are Case-Insensitive

Repeat the request using different capitalization:

```bash
curl -i http://127.0.0.1:8000/inspect-headers -H "accept: application/json" -H "X-CORRELATION-ID: case-test" -H "x-client-version: 3.4.0"
```

Your endpoint should still receive the values, and the response should contain:

```http
X-Correlation-ID: case-test
```

Explain why Python can use `x_correlation_id` while the HTTP request uses `X-Correlation-ID`.

---

## 6. Generate a Missing Correlation ID

Call the endpoint without `X-Correlation-ID`:

```bash
curl -i http://127.0.0.1:8000/inspect-headers
```

Run the same command again.

Confirm that:

- Both responses contain `X-Correlation-ID`.
- Each response receives a generated identifier.
- The two generated values are different.

---

## 7. Build the Product Endpoint

Define this request-body model:

```python
class ProductCreate(BaseModel):
    name: str
    price: float
```

Implement:

```http
POST /products
```

Requirements:

- Accept `ProductCreate` as the JSON request body.
- Read optional `X-Correlation-ID` from the request.
- Reuse it or generate one when absent.
- Add `X-Correlation-ID` to the response headers.
- Add `X-API-Version: 1` to the response headers.
- Return the product representation in the body.
- Do not place the product fields in custom response headers.

A fixed or generated product ID is sufficient. Persistence is outside this exercise.

Test:

```bash
curl -i -X POST http://127.0.0.1:8000/products -H "Content-Type: application/json" -H "Accept: application/json" -H "X-Correlation-ID: product-456" -d '{"name":"Keyboard","price":2500}'
```

Identify separately:

- Request `Content-Type`
- Request `Accept`
- Response `Content-Type`
- Response `X-Correlation-ID`
- Response body

---

## 8. Observe What Accept Does Not Do Automatically

Send:

```bash
curl -i http://127.0.0.1:8000/inspect-headers -H "Accept: application/pdf"
```

Observe the response format.

The endpoint reads `Accept`, but it does not implement logic that produces a PDF. FastAPI still returns JSON because the endpoint returns a dictionary.

Explain this distinction:

```text
Accept communicates a client preference.
Application code and the API contract determine whether that format is supported.
```

Do not implement PDF generation or an error response for this exercise.

---

## 9. Inspect FastAPI Documentation

Open:

```text
http://127.0.0.1:8000/docs
```

Confirm that the inspection endpoint documents:

- `accept` as a header
- `authorization` as a header
- `x-correlation-id` as a header
- `x-client-version` as a header

If one appears as a query parameter, review whether `Header(...)` was declared.

---

<details>
<summary>Hints—open only if you are blocked</summary>

Useful imports:

```python
from uuid import uuid4

from fastapi import FastAPI, Header, Response
from pydantic import BaseModel
```

A header parameter can be declared as:

```python
x_correlation_id: str | None = Header(default=None)
```

Choose or generate the identifier:

```python
correlation_id = x_correlation_id or str(uuid4())
```

Set response headers:

```python
response.headers["X-Correlation-ID"] = correlation_id
response.headers["X-API-Version"] = "1"
```

Safely obtain only the authorization scheme:

```python
authorization_scheme = (
    authorization.split(" ", maxsplit=1)[0]
    if authorization
    else None
)
```

</details>

---

## ✅ Completion Check

After implementing and pushing `main.py`, share:

1. The commit or tell me it has been pushed.
2. The response headers from a request with `X-Correlation-ID: request-123`.
3. The two generated correlation IDs when the header was omitted.
4. What happened when header capitalization changed.
5. The request and response `Content-Type` values for `POST /products`.
6. What happened when `Accept: application/pdf` was sent.
7. Why the complete authorization value was not returned or logged.
8. How FastAPI mapped underscore-based Python names to hyphenated headers.

I will review the implementation in GitHub. After it works, the interview questions will be asked one at a time in chat. We will create `Interview.md` only after reviewing your answers.
