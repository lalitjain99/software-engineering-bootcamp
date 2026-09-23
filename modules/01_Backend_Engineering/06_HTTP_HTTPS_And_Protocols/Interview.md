# Topic 06 — Interview Guide: HTTP, HTTPS, and Protocol Foundations

> These answers were refined from the chat interview after completing the [notes](Notes.md) and [hands-on observations](Hands_On/observations.md).

## 1. Where does TLS terminate?

**Question**

A client sends a request over HTTPS to a load balancer, which forwards it over plain HTTP to Uvicorn. Where does TLS terminate, and is the second hop protected?

**Answer**

The client’s TLS connection terminates at the load balancer. The load balancer decrypts the request and forwards it to Uvicorn over plain HTTP, so the load-balancer-to-Uvicorn hop is not protected by TLS.

If the second hop used HTTPS, the load balancer would establish or reuse a separate TLS connection to the backend. The two hops are separate connections:

```text
Client ── HTTPS connection 1 ──► Load balancer
Load balancer ── HTTPS connection 2 ──► Backend
```

The load balancer does not necessarily create a new backend connection for every request; it can reuse suitable connections.

## 2. Why trust forwarded headers only from known proxies?

**Question**

Why should Uvicorn trust `X-Forwarded-Proto: https` only when it comes from a known proxy?

**Answer**

HTTP headers can be supplied by clients. An attacker could connect directly over plain HTTP and send `X-Forwarded-Proto: https`, causing the application to believe the original request used HTTPS.

The header describes the original client-to-proxy scheme. It does not prove that the proxy-to-backend hop is encrypted.

The backend should accept forwarded headers only from trusted proxy addresses. The trusted proxy should also replace or sanitize client-supplied forwarded headers. Applications may use the interpreted scheme when generating redirects, absolute URLs, or applying security rules, so misplaced trust can cause incorrect or unsafe behaviour.

## 3. Does a certificate failure reach FastAPI?

**Question**

A client resolves `api.example.com` and connects to port `443`, but the server certificate belongs to a different hostname. Does FastAPI receive the request?

**Answer**

No. DNS resolution and TCP connection establishment succeed, but certificate validation fails during the TLS handshake. The client aborts before sending the normal HTTP request, so FastAPI does not receive it.

The HTTPS client does not normally fall back to plain HTTP after certificate validation fails.

## 4. Connection refused versus HTTP 404

**Question**

What is the difference between a connection refusal on port `8001` and `404 Not Found` for `/products/999` on port `8000`?

**Answer**

A connection refusal occurs while establishing the TCP connection. In the local exercise, nothing is listening on port `8001`, so no HTTP request reaches Uvicorn or FastAPI.

For `/products/999`, the TCP connection succeeds, Uvicorn parses the HTTP request, and FastAPI executes the endpoint. The application cannot find product `999`, so it completes the HTTP exchange with `404 Not Found`.

A `404` proves that an HTTP response was received. A connection error occurs before an application can return an HTTP status.

## 5. Why can one curl command reuse a connection?

**Question**

Why can two URLs in one `curl` command reuse a TCP connection while two separate `curl` commands create separate connections?

**Answer**

Two URLs supplied to one curl process can share its connection pool. After the first HTTP/1.1 response, curl can reuse the still-open, suitable TCP connection for the second request.

Separate curl commands start separate processes with separate connection pools. The later process cannot access the previous process’s connection and must establish its own.

Connection reuse also depends on the first connection remaining open and being suitable for the next request.

## 6. Can HTTP versions differ across proxy hops?

**Question**

A client uses HTTP/2 with a load balancer, while the load balancer uses HTTP/1.1 with Uvicorn. Is this valid?

**Answer**

Yes. An HTTP load balancer or reverse proxy ends the client-side HTTP connection, interprets the request, and creates or reuses a separate backend connection. It can translate the message representation:

```text
Client ── HTTP/2 ──► Load balancer ── HTTP/1.1 ──► Uvicorn
```

The HTTP versions can differ while the method, path, headers, body, status, and other HTTP semantics remain consistent.

A component configured only for TCP pass-through does not terminate and translate HTTP in this manner.

## 7. Can HTTPS requests expose tokens through logs?

**Question**

An API uses HTTPS, but the load balancer logs complete URLs and the application logs every request header. Why can tokens still be exposed?

**Answer**

HTTPS protects the request while it travels across the protected hop. Components processing the request see the decrypted URL and headers.

A token placed in a query string can appear in load-balancer access logs. A bearer token placed correctly in the `Authorization` header can still appear in application logs if every header is recorded.

Sensitive values should not be placed in URLs. Tokens should use the appropriate authentication header, and logging, tracing, proxy, and monitoring systems should omit or redact authorization headers, cookies, API keys, session identifiers, and sensitive parameters. Access to logs should also be restricted.

## 8. What happens when the gateway timeout is shorter than the endpoint?

**Question**

A load balancer has a 30-second upstream response timeout, but a FastAPI endpoint takes 45 seconds. What happens?

**Answer**

The client will likely receive a gateway timeout, commonly `504 Gateway Timeout`, after approximately 30 seconds. The exact response depends on the gateway.

This does not guarantee that the FastAPI work stops. The gateway may close or abandon the upstream connection while application code, a database query, or an external call continues. Cancellation requires support from the server, application code, and dependency involved.

Investigate:

- Endpoint latency and its database or external-service bottlenecks
- Client, gateway, proxy, and backend timeout settings
- Whether disconnected requests and downstream calls can be cancelled
- Whether the operation should be redesigned as an asynchronous job

For inherently long and important work, return `202 Accepted` with a job ID and status URL, and run the work through a durable queue and worker. In-process `BackgroundTasks` are more suitable for small, non-critical tasks.

## 9. Packet loss in HTTP/2 versus HTTP/3

**Question**

Two HTTP requests share one connection. How can one lost packet affect HTTP/2 and HTTP/3 differently?

**Answer**

HTTP/2 multiplexes multiple logical HTTP streams over one TCP connection. TCP exposes one ordered byte stream and does not understand HTTP/2 stream boundaries. If a TCP packet is lost, TCP recovers the missing bytes before delivering later bytes, so multiple HTTP/2 streams can temporarily wait. This is TCP head-of-line blocking.

HTTP/3 uses QUIC, where requests use independent streams. Packet loss affecting one stream delays that stream, while another stream can continue when its data is available.

QUIC streams still share a network path and congestion limits, so QUIC does not eliminate every source of delay.

## 10. Trace a complete HTTPS request

**Question**

Trace this request from the hostname to the FastAPI endpoint:

```text
https://api.example.com/products/101
```

**Answer**

1. The client reads the URL: scheme `https`, hostname `api.example.com`, implied port `443`, and path `/products/101`.
2. DNS resolves the hostname to an IP address.
3. IP provides the destination machine’s network address.
4. Port `443` identifies the listening network service on that machine.
5. For HTTP/1.1 or HTTP/2, the client establishes a TCP connection. TCP provides reliable, ordered byte delivery.
6. The client and TLS endpoint perform a TLS handshake. The client validates the server certificate, and both sides establish keys that protect the HTTP exchange.
7. The HTTP client represents the request according to HTTP rules and sends it through TLS and TCP.
8. Uvicorn or an infrastructure component accepts the connection. Uvicorn reads and parses the HTTP message and exposes it to the application through ASGI.
9. FastAPI matches `/products/{product_id}`, validates `101`, executes the endpoint, and builds the application response.
10. Uvicorn serializes the HTTP response. TLS protects it, TCP transports it, and the client receives, decrypts, and interprets it.

In production, DNS may point to a load balancer. That component can terminate TLS and create or reuse a separate connection to Uvicorn.

## Common Mistakes

### Treating a port as the application itself

A port identifies a listening network service. The operating system delivers traffic to a socket bound to that port; the service process uses that socket.

### Assuming HTTPS means every internal hop is encrypted

The browser’s HTTPS connection may terminate at a load balancer. Inspect every subsequent hop separately.

### Saying a failed TLS connection becomes plain HTTP

Certificate failure normally causes the client to abort. It does not silently downgrade to HTTP.

### Treating connection errors as HTTP errors

Without a connection and HTTP response, there is no HTTP status code. `404` and `422` require the request to reach an HTTP server.

### Assuming separate curl processes share connections

Connection pools belong to a process or long-lived client instance. A later curl process cannot inherit the earlier process’s pool.

### Confusing ALPN with the TLS version

ALPN negotiates an application protocol such as HTTP/1.1 or HTTP/2. It does not by itself report the negotiated TLS version.

### Assuming a gateway timeout cancels backend work

The client-facing response and the backend task lifecycle are separate concerns. Cancellation must be supported and propagated.

### Trusting forwarded headers from every source

Forwarded headers are safe to use only inside a correctly configured trust boundary with known proxies and sanitized client input.

## Revision Checklist

You should now be able to:

- Separate DNS, IP, port, TCP, TLS, HTTP, Uvicorn, and FastAPI responsibilities
- Explain TLS termination across multiple hops
- Distinguish a connection failure, TLS failure, HTTP error, and application error
- Explain HTTP/1.1 connection reuse and connection pools
- Explain why HTTP versions can differ across proxy hops
- Identify logging and forwarded-header risks
- Reason about gateway and backend timeouts
- Compare HTTP/2 over TCP with HTTP/3 over QUIC
