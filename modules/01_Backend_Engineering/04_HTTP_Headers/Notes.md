# Topic 04 — HTTP Headers

> **Single learning goal:** Use headers for metadata about an HTTP message, not for the primary business data.

## 🌱 The Missing Information

Our Product API can now express:

- The operation through the HTTP method
- The resource through the path
- Filters and options through the query string
- Structured product data through the body

Consider this request:

```http
POST /products HTTP/1.1
Content-Type: application/json

{
  "name": "Keyboard",
  "price": 2500
}
```

The body contains product data, but the server still needs information **about the message**:

- What format is the body?
- What response format can the client understand?
- What credentials did the client provide?
- How can this request be traced through logs and services?

This supporting information belongs in HTTP headers.

---

## 🧭 One Mental Model

```text
Body    = the business representation
Headers = metadata about the message or request context
```

Examples:

| Information | Correct location |
|---|---|
| Product name and price | Request body |
| Body format is JSON | `Content-Type` header |
| Client wants JSON back | `Accept` header |
| Access credential | `Authorization` header |
| Request tracing identifier | Correlation header |

A header is normally written as a name-value pair:

```http
Header-Name: header value
```

---

## ✉️ Request Headers and Response Headers

Request headers travel from the client to the server:

```http
POST /products HTTP/1.1
Host: api.example.com
Content-Type: application/json
Accept: application/json
Authorization: Bearer <token>
X-Correlation-ID: req-7f31

{
  "name": "Keyboard",
  "price": 2500
}
```

Response headers travel from the server to the client:

```http
HTTP/1.1 201 Created
Content-Type: application/json
X-Correlation-ID: req-7f31

{
  "product_id": 101,
  "name": "Keyboard",
  "price": 2500
}
```

Notice the blank line between the headers and body.

Also notice that these are not headers:

- `POST /products HTTP/1.1` is the request line.
- `HTTP/1.1 201 Created` is the status line.
- The JSON section is the body.

---

## 📦 Content-Type — What Format Is This Body?

`Content-Type` describes the format of the body attached to the **same message**.

Request example:

```http
Content-Type: application/json
```

This tells the server to interpret the request body as JSON.

Response example:

```http
Content-Type: application/json
```

This tells the client that the response body is JSON.

Other examples include:

```http
Content-Type: text/plain
Content-Type: text/html
Content-Type: application/pdf
```

A useful sentence is:

> `Content-Type` describes what I am sending in this message.

If a request has no body, it often does not need a `Content-Type` header.

---

## 🎯 Accept — What Can the Client Receive?

`Accept` is a request header describing which response formats the client can handle or prefers.

```http
Accept: application/json
```

The client is saying:

> Send me JSON if you can.

This is different from `Content-Type`:

| Header | Question answered |
|---|---|
| `Content-Type` | What format is the body I am sending? |
| `Accept` | What response format can I receive? |

Example:

```http
POST /reports HTTP/1.1
Content-Type: application/json
Accept: application/pdf
```

The client sends report criteria as JSON but asks to receive a PDF.

Whether the server supports that response format is a separate API-contract decision.

---

## 🔑 Authorization — What Credential Is Presented?

A client commonly sends credentials using the `Authorization` request header:

```http
Authorization: Bearer <access-token>
```

Here:

- `Authorization` is the header name.
- `Bearer` identifies the authentication scheme.
- The remaining value is the credential.

The header does not mean that access is automatically granted. The server must validate the credential and decide what the caller is allowed to do.

Do not put access tokens in paths or query strings. Do not log the `Authorization` value.

Authentication mechanisms, token validation, and permissions will be covered later.

---

## 🔗 Correlation IDs — Follow One Request

A request can pass through several components:

```text
Client → API gateway → Product service → Inventory service
```

If every component writes logs, how do we find all entries belonging to the same request?

A correlation ID provides one value that can be carried and logged across the journey:

```http
X-Correlation-ID: req-7f31
```

A common flow is:

1. The client or first trusted server provides an identifier.
2. Each service includes it in relevant logs.
3. Downstream calls propagate it.
4. The API returns it in the response.
5. Support engineers use it to trace a failure.

The identifier helps observability; it is not proof of identity and must not be treated as an authorization credential.

Different organizations use different names. This lesson uses `X-Correlation-ID` because it is easy to recognize. Standardized distributed-tracing headers will be introduced with observability.

---

## 🧩 Custom Headers

Applications can define headers for cross-cutting metadata not already represented by a standard header.

Examples might include:

```http
X-Correlation-ID: req-7f31
Client-Version: 3.4.0
```

Before creating one, ask:

- Does a standard header already solve this?
- Is this genuinely metadata rather than business data?
- Will every client and service use the same name and meaning?
- Is it documented in the API contract?

Avoid moving normal product fields into custom headers:

```http
Product-Price: 2500
```

Price is part of the product representation and belongs in the body.

---

## ⚙️ Reading Headers in FastAPI

FastAPI uses `Header` to declare a header parameter:

```python
from fastapi import FastAPI, Header


app = FastAPI()


@app.get("/products/{product_id}")
def get_product(
    product_id: int,
    accept: str | None = Header(default=None),
    x_correlation_id: str | None = Header(default=None),
):
    return {
        "product_id": product_id,
        "accept": accept,
        "correlation_id": x_correlation_id,
    }
```

Without `Header(...)`, a simple parameter that is not in the path would normally be interpreted as a query parameter.

FastAPI converts underscores in Python names to hyphens in header names:

```text
x_correlation_id  ↔  X-Correlation-ID
```

HTTP header names are case-insensitive, so these names refer to the same header:

```http
Content-Type
content-type
CONTENT-TYPE
```

Use conventional capitalization in documentation for readability.

---

## 📤 Setting Response Headers in FastAPI

A route can add a response header through a `Response` parameter:

```python
from uuid import uuid4

from fastapi import FastAPI, Header, Response


app = FastAPI()


@app.get("/products/{product_id}")
def get_product(
    product_id: int,
    response: Response,
    x_correlation_id: str | None = Header(default=None),
):
    correlation_id = x_correlation_id or str(uuid4())
    response.headers["X-Correlation-ID"] = correlation_id

    return {
        "product_id": product_id,
        "name": "Keyboard",
    }
```

FastAPI still converts the returned dictionary to JSON. The additional header is attached to the final response.

For production applications, generating and propagating correlation IDs is usually centralized rather than repeated inside every endpoint. We will introduce that structure later.

---

## 🗺️ Where Does Each Value Belong?

Combine the rules learned so far:

| Location | Meaning | Example |
|---|---|---|
| Path | Resource identity | `/products/101` |
| Query | Filters or operation options | `?include_reviews=true` |
| Body | Structured business representation | `{"name": "Keyboard"}` |
| Header | Message metadata or cross-cutting context | `Accept: application/json` |

Ask:

> Is this value part of the business resource, or information about how the message should be understood and processed?

Use the body for the resource. Use a header for message-level metadata when a standard or documented custom header fits.

---

## 🔐 Security and Trust

Headers come from the client, so they are untrusted input.

A Technical Lead should ensure that:

- Credentials are validated, not merely read.
- `Authorization` values are redacted from logs.
- Correlation IDs are safe to log and have controlled length.
- Services trust identity-related headers only from approved infrastructure.
- HTTPS protects headers and bodies while they travel across the network.

A header is a location for information—not a security mechanism by itself.

---

## 🧠 Technical Lead Perspective

When reviewing an API, ask:

- Are `Content-Type` and `Accept` being confused?
- Is business data incorrectly placed in custom headers?
- Are required headers documented and validated?
- Are correlation IDs propagated consistently?
- Are credentials and sensitive headers excluded from logs?
- Could a gateway or proxy add, remove, or change this header?
- Is header handling centralized when every endpoint needs it?

Headers form part of the public contract even though they are less visible than the URL and body.

---

## ✅ Check Your Understanding

1. What is the difference between a request header and a response header?
2. How do `Content-Type` and `Accept` differ?
3. Can a GET request send an `Accept` header without a request body?
4. Why should `Authorization` not appear in a query string?
5. What problem does a correlation ID solve?
6. Why should product price not be stored in a custom header?
7. How does FastAPI map `x_correlation_id` to `X-Correlation-ID`?
8. Is a status line an HTTP header?

---

## 🛑 Intentional Stop Point

This lesson does not yet cover:

- Authentication flows, JWT validation, or authorization rules
- Cookies and sessions
- CORS
- Caching and conditional-request headers
- Full content-negotiation algorithms
- Distributed-tracing standards
- Proxy trust configuration
- Detailed status-code selection

## ➡️ Next Step

Inspect and manipulate request and response headers in a focused FastAPI hands-on exercise. Interview questions will again be asked one at a time in chat before `Interview.md` is created.

## 📚 References

- [RFC 9110 — HTTP Fields](https://www.rfc-editor.org/rfc/rfc9110.html#section-5)
- [RFC 9110 — Content-Type](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.3)
- [RFC 9110 — Accept](https://www.rfc-editor.org/rfc/rfc9110.html#section-12.5.1)
- [RFC 9110 — Authorization](https://www.rfc-editor.org/rfc/rfc9110.html#section-11.6.2)
- [FastAPI — Header Parameters](https://fastapi.tiangolo.com/tutorial/header-params/)
- [FastAPI — Response Headers](https://fastapi.tiangolo.com/advanced/response-headers/)
