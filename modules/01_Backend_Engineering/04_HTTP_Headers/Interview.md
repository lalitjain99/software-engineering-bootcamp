# Topic 04 — HTTP Headers: Interview Guide

> Reviewed answers from the chat interview, refined for Senior Engineer and Technical Lead discussions.

## 🌱 Foundation Questions

### 1. What is the difference between request and response headers?

**Answer**

Request headers are metadata sent by the client to the server. They describe the incoming message or its context.

Examples:

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <access-token>
X-Correlation-ID: req-123
```

Response headers are metadata sent by the server to the client. They describe the returned message or provide response-level context.

Examples:

```http
Content-Type: application/json
X-Correlation-ID: req-123
X-API-Version: 1
```

The request line and status line are not headers, and the business representation belongs in the body.

---

### 2. What is the difference between `Content-Type` and `Accept`?

**Answer**

`Content-Type` describes the format of the body attached to the same HTTP message. `Accept` is a request header that describes which response formats the client can process or prefers.

```http
POST /products
Content-Type: application/json
Accept: application/xml
```

The client is saying:

> I am sending JSON and would prefer to receive XML.

`Accept` expresses a client preference; it does not automatically make the server produce that format.

---

### 3. Why can `Content-Type` appear in both a request and a response?

**Answer**

It has the same meaning in both directions: it describes the body of the message carrying the header.

- Request `Content-Type` describes the request body sent by the client.
- Response `Content-Type` describes the response body sent by the server.

```text
Client → Server: Content-Type describes the request body
Server → Client: Content-Type describes the response body
```

A message without a body usually does not require `Content-Type`.

---

## 🧩 Applied Questions

### 4. Why use the `Authorization` header instead of a query parameter?

**Answer**

Access tokens are sensitive. Query parameters can be captured in browser history, bookmarks, access logs, proxy logs, monitoring tools, and other URL-based records.

Use the standard header:

```http
Authorization: Bearer <access-token>
```

`Bearer` is the authentication scheme. It means whoever possesses the token can present it for access, subject to the token's validity, permissions, and scopes.

Moving a token into a header does not encrypt it. HTTPS is still required.

---

### 5. What problem does a correlation ID solve?

**Answer**

A correlation ID links logs and operations belonging to one request as it travels through multiple components.

```text
Client → API Gateway → Service A → Service B
              X-Correlation-ID: req-123
```

Each component should:

1. Read the correlation ID.
2. Include it in relevant logs.
3. explicitly propagate it to downstream calls.
4. Return it in the response when appropriate.

If the client does not provide one, the gateway or first receiving service should generate a unique value, such as a UUID.

A correlation ID supports observability; it is not an identity or authorization credential.

---

### 6. How does FastAPI map `x_correlation_id` to `X-Correlation-ID`?

**Answer**

FastAPI's `Header` declaration converts underscores in Python parameter names to hyphens by default:

```python
x_correlation_id: str | None = Header(default=None)
```

This maps to:

```http
X-Correlation-ID
```

HTTP header names are case-insensitive, so `X-Correlation-ID`, `x-correlation-id`, and `X-CORRELATION-ID` refer to the same header.

An explicit alias makes the API name deliberate:

```python
x_correlation_id: str | None = Header(
    default=None,
    alias="X-Correlation-ID",
)
```

The alias does not make capitalization case-sensitive.

---

### 7. What should happen when the client requests an unsupported representation?

**Answer**

Suppose the client sends:

```http
Accept: application/xml
```

If XML is the only acceptable format and the server cannot produce it, a properly implemented content-negotiation policy should return:

```http
HTTP/1.1 406 Not Acceptable
```

Reading `Accept` alone does not implement content negotiation. A FastAPI endpoint returning a dictionary will normally still produce JSON unless the application adds negotiation logic.

`Accept: application/xml` describes what the client can receive. `Content-Type: application/xml` declares that the body actually attached to that message is XML.

---

## 🧭 Technical Lead Questions

### 8. Why does business data belong in the body instead of custom headers?

**Answer**

Product fields such as `name`, `price`, and `category` form the resource representation, so they belong in the body.

JSON bodies naturally support:

- Nested objects and arrays
- Numbers, booleans, and null values
- Schema validation
- OpenAPI documentation
- Generated client SDKs
- Larger structured representations

Headers are textual metadata fields and are not designed for large, nested, strongly typed business documents.

Custom response headers are appropriate for cross-cutting metadata such as:

```http
X-Correlation-ID: req-123
X-API-Version: 1
Retry-After: 30
ETag: "product-101-v3"
```

Before creating a custom header, check whether a standard header already represents the concept.

---

### 9. How do optional and required headers differ in FastAPI?

**Answer**

Optional header:

```python
x_client_version: str | None = Header(default=None)
```

If the header is absent, FastAPI assigns `None` and allows the endpoint to execute. The endpoint—not this declaration—determines the final response status.

Required header:

```python
x_client_version: str = Header()
```

If the header is absent, request validation fails, FastAPI returns `422 Unprocessable Entity`, and the endpoint function is not executed.

If the required declaration succeeds, the function receives a string.

---

### 10. Is a bearer token secure merely because it is in a header?

**Answer**

No. Plain HTTP does not encrypt the request line, headers, or body. A bearer token sent through HTTP can be exposed to anyone able to observe or alter traffic on the route.

HTTPS uses TLS to provide:

- Confidentiality through encryption in transit
- Integrity against undetected modification
- Server authentication through certificates

The `Authorization` header provides a standard location for credentials; it is not encryption.

Full bearer tokens must never be written to application, proxy, tracing, or monitoring logs. Sensitive headers should be redacted. If diagnostic linkage is necessary, use a safe token identifier or approved non-secret metadata rather than the credential.

A Technical Lead should also understand where TLS terminates and ensure that any internal transport after termination follows the organization's security model.

---

## ⚠️ Common Mistakes

### Confusing `Accept` with `Content-Type`

```text
Content-Type = format of the body attached to this message
Accept       = response formats the client can receive
```

### Assuming `Accept` automatically transforms a response

FastAPI does not turn a dictionary into XML or PDF just because the client requests that format. The API must implement and document support.

### Treating `Authorization` as encryption

A header is only a location. Use HTTPS to protect headers and bodies in transit.

### Logging credentials

Never log the complete `Authorization` value. Redact sensitive headers in application logs, gateways, proxies, and observability tools.

### Forgetting correlation-ID propagation

Generating an identifier is not enough. Every downstream client call must explicitly propagate it.

### Trusting client-supplied headers automatically

Headers are untrusted input. Validate required formats, control their length, and trust identity-related headers only when added by approved infrastructure.

### Putting resource fields in headers

Business representations belong in the body. Use headers for message metadata and cross-cutting context.

### Accidentally declaring a query parameter

In FastAPI, use `Header(...)` when a value must come from a header. A plain function parameter that is not in the path is normally treated as a query parameter.

---

## ✅ Completion Check

You should now be able to:

- Distinguish request headers, response headers, request lines, status lines, and bodies
- Explain `Content-Type`, `Accept`, `Authorization`, and correlation IDs
- Read required and optional headers in FastAPI
- Set response headers without moving business data out of the body
- Explain header security and propagation from a Technical Lead perspective
