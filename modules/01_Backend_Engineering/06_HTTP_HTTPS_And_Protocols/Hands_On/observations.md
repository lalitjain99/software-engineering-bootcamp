# Topic 06 — HTTP, TCP, and TLS Observations

These are selected lines from my `curl -v` runs. Repeated headers, response bodies, and progress output are shortened where they do not affect the conclusion. The local API is the Topic 05 Product API running on `127.0.0.1:8000`.

## 1. A plain HTTP request

**Command**

```bash
curl -v --http1.1 http://127.0.0.1:8000/products/101
```

**Evidence**

```http
* Established connection to 127.0.0.1 (127.0.0.1 port 8000) from 127.0.0.1 port 53345
> GET /products/101 HTTP/1.1
> Host: 127.0.0.1:8000
> Accept: */*
< HTTP/1.1 200 OK
< content-type: application/json

{"product_id":101,"sku":"KEY-001","name":"Keyboard","price":2500,"category":"electronics"}
```

**What it means**

- `GET /products/101 HTTP/1.1` is the **request line**. `GET` specifies the method; `/products/101` identifies the requested path and product ID.
- `content-type: application/json` is a **response header** describing the response body format.
- `HTTP/1.1 200 OK` is the **response status line**. `200` reports success.

## 2. Reusing a TCP connection

**Two URLs in one curl command**

```bash
curl -v --http1.1 http://127.0.0.1:8000/products/101 http://127.0.0.1:8000/products/102
```

**Evidence**

```text
* Established connection to 127.0.0.1 (127.0.0.1 port 8000) from 127.0.0.1 port 56913
> GET /products/101 HTTP/1.1
< HTTP/1.1 200 OK
* Connection #0 to host 127.0.0.1:8000 left intact
* Reusing existing http: connection with host 127.0.0.1
> GET /products/102 HTTP/1.1
< HTTP/1.1 200 OK
```

These two HTTP/1.1 requests ran **one after the other** on the same available TCP connection. Curl's reuse message confirms that a new TCP connection was unnecessary for the second request.

**Two separate curl commands**

Each run reported a new connection, using client port `55757` for the first and `55759` for the second. Each command starts a new `curl` process with its **own connection pool**. A later process cannot borrow the earlier process's connection, even if the second command starts before Uvicorn's idle timeout expires. This explains the difference more precisely than the time gap between requests.

`* Connection #0 ... left intact` means that connection was reusable **within the running curl process at that moment**. It does not mean a later curl process can inherit it.

## 3. HTTP 404 versus connection refused

**Missing product on the listening port**

```bash
curl -v --http1.1 http://127.0.0.1:8000/products/999
```

```http
* Established connection to 127.0.0.1 (127.0.0.1 port 8000)
> GET /products/999 HTTP/1.1
< HTTP/1.1 404 Not Found
< content-type: application/json

{"detail":{"code":"PRODUCT_NOT_FOUND","message":"Product 999 does not exists","details":{"product_id":999}}}
```

The connection succeeded. The application handled the request and returned an **HTTP response** saying that product `999` was not found.

**Unused port**

```bash
curl -v --connect-timeout 3 http://127.0.0.1:8001/products/101
```

```text
* Trying 127.0.0.1:8001...
* connect to 127.0.0.1 port 8001 ... failed: Connection refused
curl: (7) Failed to connect to 127.0.0.1:8001
```

Nothing was listening at `127.0.0.1:8001` during this test. The TCP connection failed **before HTTP could reach FastAPI**, so there was no HTTP status line and no FastAPI `404`.

## 4. HTTPS to example.com

**Command run in Windows**

```bat
curl -v -o NUL https://example.com/
```

**Evidence**

```text
* Host example.com:443 was resolved.
* IPv6: 2606:4700:90c5:72db:f264:4:ef6b:ff98
* IPv4: 172.66.147.243, 104.20.23.154
* ALPN: curl offers http/1.1
* ALPN: server accepted http/1.1
* Established connection to example.com (... port 443) from ... port 49180
> GET / HTTP/1.1
> Host: example.com
< HTTP/1.1 200 OK
< Content-Type: text/html
```

- **DNS:** Curl resolved `example.com` to IP addresses.
- **Connection:** The client connected to port `443`.
- **HTTP version:** ALPN selected `http/1.1`, and the HTTP request and response both show `HTTP/1.1`. This is the **HTTP version**, not the TLS version.
- **TLS:** The HTTPS transfer proceeded to an HTTP `200` without a reported certificate error. The captured `schannel` messages and ALPN lines do **not** explicitly show the negotiated TLS version or server-certificate verification details, so those details cannot be identified from this excerpt. The `schannel: disabled automatic use of client certificate` message refers to a *client* certificate, not verification of the server certificate.
- **Server side:** The response includes `Server: cloudflare` in the original output. The HTTPS endpoint may be an edge server; this test does not reveal how traffic travels from that edge to the origin.

Curl's `>` and `<` lines show readable HTTP **inside the client**, before it encrypts the outgoing request and after it decrypts the incoming response. They are not a capture of readable HTTP on the network.

## Outcome table

| Scenario | Connection succeeded? | HTTP status | Layer that explains the result |
|---|---|---|---|
| `/products/101` on port `8000` | Yes | `200` | HTTP request reached the application; product exists |
| Two URLs in one curl command | Yes; connection reused | `200` and `200` | HTTP/1.1 connection persistence and curl's connection pool |
| `/products/999` on port `8000` | Yes | `404` | HTTP/application response for a missing product |
| `/products/101` on unused port `8001` | No | None | TCP connection refused before HTTP |
| HTTPS request to `example.com` | Yes | `200` | DNS, connection, TLS-protected HTTP exchange |

## Final questions

1. **Which component defines the meaning of `GET` and `404`?**  
   The **HTTP protocol** defines the method and status-code semantics. `GET` appears in the request line; `404` appears in the response status line. The application chooses `404` here because the product is missing.

2. **Which component manages the listening port and idle client connections?**  
   **Uvicorn**, with the operating system's networking stack, creates and uses the listening socket and manages HTTP connection reuse and idle timeouts. The FastAPI endpoint handles the routed request.

3. **When can the HTTPS server understand the HTTP request?**  
   After the connection is established, the TLS handshake succeeds, and the **TLS endpoint on the server side decrypts** the incoming data. The HTTP server then parses the request; FastAPI receives it afterward. The client decrypts the **response** on its own side.

4. **Why can curl show readable HTTP for HTTPS?**  
   Curl constructs the readable request before its TLS layer encrypts it and reads the response after its TLS layer decrypts it. Verbose output is produced at the client endpoint, so readable debug text does not imply the traffic was readable in transit.
