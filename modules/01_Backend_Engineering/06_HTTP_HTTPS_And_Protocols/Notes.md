# Topic 06 — HTTP, HTTPS, and Protocol Foundations

> **Single learning goal:** Understand which layer finds the server, carries the data, protects it, and gives the request meaning.

## 🌱 The Missing Part of the Journey

We already understand an HTTP request such as:

```http
GET /products/101 HTTP/1.1
Host: api.example.com
Accept: application/json
```

But how does that request travel from a client to a server on another machine?

Consider:

```text
https://api.example.com/products/101
```

Before FastAPI can match `/products/101`, several different technologies cooperate:

- A hostname must lead to an IP address.
- The operating system must find the listening service.
- Data must travel between the two machines.
- The conversation must be protected.
- The bytes must be understood as an HTTP request.

No single protocol performs all these jobs.

---

## 🧭 One Mental Model

```text
DNS   → Which IP address belongs to this hostname?
IP    → Which machine should receive the packets?
Port  → Which service on that machine should receive them?
TCP   → How are bytes delivered reliably and in order?
TLS   → How is the communication protected in transit?
HTTP  → What do the request and response mean?
```

This is a learning model, not a complete map of every network component. Its purpose is to keep the responsibilities separate.

For HTTP/3, QUIC replaces the TCP part and incorporates secure transport. We will reach that after understanding the traditional HTTP/1.1 and HTTP/2 journey.

---

## 🏠 IP Address — Find the Machine

An IP address identifies a network destination.

Examples:

```text
127.0.0.1       → this computer itself
192.168.1.20    → a private-network address
203.0.113.10    → example public address
```

When you use:

```text
api.example.com
```

DNS normally resolves that hostname to an IP address. DNS makes names convenient; IP provides the address used for network delivery.

An IP address alone does not identify which application should receive the traffic. The same machine can run a web server, database, SSH server, and many other services.

That is why we also need a port.

---

## 🚪 Port — Find the Service

A port identifies a listening network service on a machine.

```text
127.0.0.1:8000
│         └── port
└──────────── IP address
```

The operating system uses the destination IP, transport protocol, and port to deliver incoming traffic to the appropriate listening socket.

Common conventions are:

| Scheme | Default port |
|---|:---:|
| `http` | `80` |
| `https` | `443` |

Therefore:

```text
https://api.example.com/products
```

normally implies port `443`.

But:

```text
https://api.example.com:8443/products
```

explicitly selects port `8443`.

A port number does not make traffic secure. Security depends on the protocol used on that port. A service could technically run HTTPS on `8443` or plain HTTP on another port.

---

## 📞 TCP — Create a Reliable Conversation

HTTP/1.1 and HTTP/2 commonly use TCP.

Think of TCP as a **reliable courier for bytes**. If a courier must deliver a ten-page document:

- The pages are numbered.
- The receiver confirms what arrived.
- A missing page is sent again.
- Pages that arrive out of order are rearranged.
- The complete document is delivered in the correct order.

TCP provides the same general behaviour for application data.

### Example: calling the local FastAPI server

When you request:

```text
http://127.0.0.1:8000/products/101
```

a simplified connection looks like:

```text
Client                              FastAPI server
127.0.0.1:53000                     127.0.0.1:8000
        │                                    │
        ├── Establish TCP connection ───────►│
        ├── Send HTTP request bytes ────────►│
        │◄── Send HTTP response bytes ───────┤
        └── Close or reuse connection ───────┘
```

Port `53000` represents an example temporary client port selected by the operating system. Uvicorn is listening on server port `8000`.

TCP provides an ordered, reliable byte stream between these endpoints. At a high level, it:

1. Establishes a connection.
2. Tracks the position of transmitted bytes.
3. Detects missing data.
4. Retransmits lost data.
5. Delivers bytes to the application in order.

### How TCP preserves order

Suppose the application sends:

```text
ABCDEFGHI
```

TCP might carry it in segments whose bytes begin at different sequence positions:

```text
ABC → starts at sequence position 1
DEF → starts at sequence position 4
GHI → starts at sequence position 7
```

The network might deliver them in this order:

```text
ABC → GHI → DEF
```

The receiving TCP:

1. Accepts `ABC` and expects the byte at position 4 next.
2. Receives `GHI`, recognizes that earlier bytes are missing, and keeps it in a receive buffer.
3. Uses acknowledgements to report which bytes have arrived and which position is expected next.
4. Receives—or requests retransmission of—the missing `DEF`.
5. Reconstructs `ABCDEFGHI`.
6. Delivers the ordered byte stream to the HTTP layer.

Sequence numbers identify byte positions, the receive buffer holds out-of-order data, acknowledgements report progress, and retransmission recovers missing data.

Reliability does not mean the API operation succeeds. TCP can deliver a request perfectly while FastAPI returns `404`, `422`, or `500`. Those are HTTP or application outcomes.

### HTTP gives the delivered bytes meaning

TCP does **not** understand:

- `GET` or `POST`
- Paths
- Headers
- JSON
- Status codes

It only transports bytes. HTTP defines how two applications express and interpret requests and responses.

```text
Client application
        ↓ creates an HTTP request
HTTP
        ↓ represents the message as bytes
TCP
        ↓ transports the bytes reliably and in order
IP
        ↓ routes them to the destination machine
TCP
        ↓ reconstructs the ordered byte stream
HTTP
        ↓ interprets the method, path, headers, and body
Server application
```

A useful analogy is:

```text
HTTP = language and letter format
TCP  = reliable courier
IP   = destination address
Port = receiving department
```

TCP is not a separate middleman application. It is a transport protocol implemented by the networking systems at both endpoints.

### The trade-off: waiting for missing data

If a TCP segment is missing, later bytes may already have arrived, but TCP cannot give the application an incomplete ordered stream. It waits for the missing bytes to be recovered.

This is called **head-of-line blocking**. It becomes important when comparing HTTP/2 over TCP with HTTP/3 over QUIC.

---

## 🔓 Plain HTTP — Meaning Without Protection

With plain HTTP, the HTTP message is not protected by TLS while travelling across the network.

Conceptually, an observer able to inspect the traffic could see or alter information such as:

- Request path and query string
- Headers
- Authorization tokens
- Request body
- Response body

Putting a token in the `Authorization` header gives it the correct HTTP location; it does not encrypt it.

This is why sensitive APIs require HTTPS.

---

## 🔐 TLS — Protect the Conversation

TLS creates a protected channel between communicating endpoints.

During the TLS setup, the client and server establish cryptographic keys. The server normally presents a certificate, and the client verifies important facts such as:

- The certificate covers the requested hostname.
- The certificate is currently valid.
- It chains to a trusted certificate authority.

After the secure session is established, efficient session keys protect application data.

TLS provides three central properties:

| Property | Meaning |
|---|---|
| Confidentiality | Observers should not be able to read the protected content |
| Integrity | Undetected modification should be prevented |
| Server authentication | The client can verify the server identity represented by the certificate |

Client certificates can also authenticate clients, but most public APIs use other client-authentication mechanisms. Mutual TLS will be covered later when it becomes relevant.

---

## 🔒 HTTPS — HTTP Through a Protected Channel

HTTPS keeps HTTP semantics while protecting the exchange with TLS.

The following concepts remain HTTP concepts:

- Methods such as `GET` and `POST`
- Paths and query parameters
- Headers and bodies
- Status codes
- Content negotiation

HTTPS does not replace HTTP business semantics. It adds transport protection and authenticated server identity.

```text
HTTP/1.1 or HTTP/2 journey:

HTTP message
     ↓
TLS protection
     ↓
TCP delivery
     ↓
IP routing
```

When the server receives the data, these responsibilities are processed in the reverse direction until the web application receives a parsed HTTP request.

---

## 🛣️ A Complete HTTPS Request Journey

Suppose the client requests:

```text
https://api.example.com/products/101?include_reviews=true
```

A simplified journey is:

1. The client reads the URL:
   - Scheme: `https`
   - Host: `api.example.com`
   - Default port: `443`
   - Path: `/products/101`
   - Query: `include_reviews=true`
2. DNS resolves `api.example.com` to an IP address.
3. For HTTP/1.1 or HTTP/2, the client establishes a TCP connection to that IP and port.
4. The client and server perform the TLS setup and verify the server certificate.
5. The client sends the HTTP request through the protected channel.
6. A server, load balancer, or reverse proxy receives and parses the request.
7. The request reaches Uvicorn/FastAPI.
8. FastAPI matches the route, validates input, and executes the endpoint.
9. The HTTP response travels back through the protected connection.

FastAPI does not perform DNS resolution or IP routing. Those responsibilities exist before the request reaches the application.

---

## 👀 What HTTPS Protects—and What It Does Not

For an HTTPS request, the path, query, headers, and body are protected in transit after the secure connection is established.

However, HTTPS does not make everything invisible or safe.

Network observers can still commonly learn some connection metadata, such as:

- Destination IP address
- Destination port
- Approximate traffic timing and size

DNS resolution may also be observable unless a protected DNS mechanism is used.

HTTPS also does not automatically protect:

- URLs stored in browser history
- Query parameters written to application or proxy logs
- Data stored unencrypted in a database
- Secrets logged by application code
- Data after either endpoint is compromised
- Traffic after TLS terminates, unless the next internal hop is also protected

This explains why sensitive values still should not be placed in URLs even when HTTPS is used.

---

## 🏢 Where Does TLS End in Production?

A local development server may receive traffic directly:

```text
Client → Uvicorn/FastAPI
```

Production systems often place infrastructure in front:

```text
Client → Load balancer / API gateway → FastAPI service
              TLS may terminate here
```

**TLS termination** means that component decrypts the incoming HTTPS connection.

The next hop might use:

- HTTP inside a controlled network
- HTTPS again
- Mutual TLS inside a service mesh

The correct choice depends on the security model and infrastructure.

A Technical Lead must know:

- Which component owns the certificate
- Where TLS terminates
- Whether internal traffic is encrypted
- How certificates are renewed
- Which proxy headers the application is allowed to trust

A header such as `X-Forwarded-Proto: https` is only trustworthy when it comes from approved infrastructure.

---

## 🚀 HTTP/1.1, HTTP/2, and HTTP/3

HTTP semantics remain broadly consistent across versions. A `GET`, header, status code, and response body keep their meaning. The versions mainly change how messages are framed and transported.

| Version | Transport foundation | Main improvement | Important limitation |
|---|---|---|---|
| HTTP/1.1 | TCP | Persistent connections and a widely compatible message format | Parallel work often needs multiple connections; responses on one connection are constrained by ordering |
| HTTP/2 | TCP | Binary framing, header compression, and multiplexed streams on one connection | TCP packet loss can delay all streams sharing that connection |
| HTTP/3 | QUIC over UDP | Secure multiplexed streams without TCP-level blocking between independent streams | Requires HTTP/3/QUIC support across clients and infrastructure |

### HTTP/1.1

HTTP/1.1 can reuse a TCP connection rather than opening a new connection for every request. Clients often use multiple connections to perform work in parallel.

### HTTP/2

HTTP/2 uses binary frames and allows multiple HTTP streams to share one TCP connection. This reduces the need for many parallel TCP connections.

Because all streams share the same ordered TCP connection, packet loss can temporarily delay progress across the connection.

### HTTP/3

HTTP/3 maps HTTP semantics over QUIC. QUIC runs over UDP but implements secure, reliable transport behaviour itself. TLS 1.3 is integrated into QUIC.

QUIC supports independent streams, so loss affecting one stream does not require unrelated streams to wait for the same missing stream data.

Do not interpret “UDP” as meaning HTTP/3 is unreliable. QUIC builds the reliability and security HTTP/3 needs above UDP.

---

## ⚙️ What FastAPI Usually Sees

Your endpoint normally receives an already-parsed request:

```python
@app.get("/products/{product_id}")
def get_product(product_id: int):
    ...
```

By the time this function runs:

- Network packets have arrived.
- The transport has delivered data.
- TLS may have been processed.
- The HTTP server has parsed the HTTP message.
- FastAPI has matched the route and validated the path parameter.

This separation is useful during diagnosis:

| Symptom | Likely area |
|---|---|
| Hostname cannot be resolved | DNS |
| Connection refused on a port | No reachable service listening there |
| Certificate warning | TLS identity or certificate configuration |
| Request reaches server but path returns `404` | HTTP routing/application contract |
| Endpoint returns `422` | FastAPI/Pydantic input validation |

---

## 🧠 Technical Lead Perspective

When reviewing a production API, ask:

- Where does TLS terminate?
- Is traffic protected on every required hop?
- Who owns certificate issuance and renewal?
- Which HTTP versions are supported by the load balancer and clients?
- Are sensitive headers and URLs redacted from logs?
- Does the application trust forwarded headers only from known proxies?
- Are connection, request, and upstream timeouts defined?
- Can failures be located at DNS, connection, TLS, HTTP, or application level?

The ability to name the failing layer prevents wasted debugging.

---

## ✅ Check Your Understanding

1. Why can one IP address host several services?
2. What role does a port play after the IP address is known?
3. What does TCP provide that HTTP itself does not?
4. Does placing a token in an HTTP header encrypt it?
5. What three primary protections does TLS provide?
6. Which parts of an HTTPS request are still likely visible as network metadata?
7. Why can TLS termination at a load balancer matter to backend security?
8. What changed from HTTP/1.1 to HTTP/2 and HTTP/3?
9. Does HTTP/3 lose reliability because it uses UDP?
10. If a connection is refused before FastAPI logs anything, which layers would you inspect first?

---

## 🛑 Intentional Stop Point

This lesson does not yet cover:

- DNS caching and recursive resolution in depth
- Routers, subnets, NAT, and BGP
- TCP congestion-control algorithms
- Cryptographic mathematics
- Complete certificate-chain and revocation behaviour
- QUIC packet structure and connection migration
- Detailed reverse-proxy configuration
- Mutual TLS implementation

These will be introduced when system design, security, or production deployment creates the need.

## ➡️ Next Step

Observe DNS resolution, TCP connection details, TLS certificate verification, and HTTP request/response information with command-line tools. Then answer interview questions one at a time before creating `Interview.md`.

## 📚 References

- [RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [RFC 9293 — Transmission Control Protocol](https://www.rfc-editor.org/rfc/rfc9293.html)
- [RFC 8446 — TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html)
- [RFC 9113 — HTTP/2](https://www.rfc-editor.org/rfc/rfc9113.html)
- [RFC 9114 — HTTP/3](https://www.rfc-editor.org/rfc/rfc9114.html)
- [RFC 9000 — QUIC](https://www.rfc-editor.org/rfc/rfc9000.html)
