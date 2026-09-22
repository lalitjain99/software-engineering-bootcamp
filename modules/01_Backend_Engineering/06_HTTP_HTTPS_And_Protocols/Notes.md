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

## 🔌 Socket — The Application's Network Endpoint

A **socket** is an operating-system-managed communication endpoint. An application uses it to send and receive bytes over a network connection.

A port and a socket are related, but they are not the same:

| Concept | Meaning |
|---|---|
| Port | A number used to locate a network service on a machine |
| Socket | The operating-system object an application uses to communicate |
| TCP connection | The communication relationship between a client socket and a server socket |

A useful analogy is:

```text
IP address = building address
Port       = department number
Socket     = telephone used by that department
TCP        = reliable telephone service
HTTP       = language and conversation rules
```

### Listening socket and connected sockets

When Uvicorn starts on `127.0.0.1:8000`, it asks the operating system to create a **listening socket** for that address and port. Its job is to wait for new connection attempts.

Suppose two clients connect:

```text
Client A: 127.0.0.1:53000 ──┐
                             ├── Server: 127.0.0.1:8000
Client B: 127.0.0.1:53001 ──┘
```

The server keeps its listening socket and the operating system creates a separate **connected socket** for each accepted client connection. The server port can remain `8000` for both because each TCP connection is identified by the combination of:

- Client IP address
- Client port
- Server IP address
- Server port

The client ports above are temporary example ports selected by the operating system.

At a low level, socket operations resemble:

```text
connect → send → receive → close
```

Most application code does not call these operations directly.

### Does a TCP connection exist when no request is being sent?

There are two different situations:

1. **No connection has been initiated:** no TCP connection exists merely because two applications are running.
2. **A request already used a connection:** the connection may remain open but idle so another request can reuse it.

An idle connection still consumes some resources at both endpoints. Clients, servers, load balancers, and proxies therefore use timeout and connection-limit policies. Eventually, either side may close it.

This is different from **TCP keepalive**, which is an optional operating-system mechanism for detecting connections whose peer is no longer reachable. HTTP connection reuse and TCP keepalive solve different problems.

### Can every request create its own TCP connection?

Yes. A client can create a connection, send one request, receive one response, and close the connection.

However, repeating that for every request adds work:

- A TCP connection must be established.
- HTTPS also requires TLS setup.
- Both endpoints allocate socket, buffer, and connection state.
- The extra round trips increase latency.

For repeated requests, clients usually keep a **connection pool** and reuse suitable idle connections.

```text
Request 1 ─┐
Request 2 ─┼── HTTP client connection pool ── existing TCP connection
Request 3 ─┘
```

With HTTP/1.1, a client may keep several reusable connections for parallel work. With HTTP/2, multiple HTTP streams can share one TCP connection.

Connection reuse is an optimization, not a guarantee. A new connection may still be required when:

- No reusable connection exists.
- The previous connection was closed.
- An idle timeout expired.
- The destination or connection settings differ.
- The pool's available connections are busy.

### Why did we not write TCP connection code?

The networking work is divided across layers:

| Component | Main responsibility |
|---|---|
| Browser, Postman, or HTTP library | Builds HTTP messages and manages connections or a connection pool |
| Operating system TCP stack | Creates sockets; performs the TCP handshake; tracks sequence numbers, acknowledgements, retransmission, and buffers |
| Uvicorn | Opens the listening socket, accepts connections, and parses HTTP messages |
| FastAPI | Matches routes, validates API inputs, runs endpoint logic, and creates application responses |

For example:

```python
import httpx

with httpx.Client(base_url="http://127.0.0.1:8000") as client:
    first_response = client.get("/products/101")
    second_response = client.get("/products/102")
```

You write HTTP-level code. HTTPX and the operating system handle the sockets and TCP details. Keeping one client open also gives HTTPX an opportunity to reuse its connection pool.

On the server side, you write:

```python
@app.get("/products/{product_id}")
def get_product(product_id: int):
    ...
```

Uvicorn and the operating system handle the socket and connection work before FastAPI executes this function.

This abstraction is valuable: backend engineers normally work at the HTTP and application layers, but understanding the hidden connection layer helps diagnose refused connections, timeouts, exhausted connection pools, and unexpectedly high latency.

---

## 🌐 HTTP — The Language of the Web

**HTTP** stands for **Hypertext Transfer Protocol**.

Let us break down the name:

| Word | Meaning |
|---|---|
| Hypertext | Originally, documents containing links to other documents |
| Transfer | Information is exchanged between applications |
| Protocol | An agreed set of rules for how messages are structured and understood |

HTTP was originally created for retrieving linked web documents. Today it is used for much more, including:

- HTML pages
- Images and videos
- JSON APIs
- File downloads
- Requests between microservices

Therefore, HTTP is not limited to transferring text. The name reflects its origin on the web.

### What problem does HTTP solve?

Suppose a client wants product `101` from a server.

TCP can reliably carry bytes between them, but TCP does not know whether those bytes mean:

- Retrieve a product
- Create an order
- Report an error
- Return JSON
- Return an image

HTTP provides the shared message format and meaning.

It allows the client to express:

> “Please retrieve product 101. I can accept JSON.”

It allows the server to respond:

> “The request succeeded. Here is the product in JSON format.”

HTTP is therefore an **application-layer request–response protocol**:

1. A client sends an HTTP request.
2. A server interprets it and performs some work.
3. The server sends an HTTP response.

The client could be a browser, Postman, a mobile app, or another backend service. The server could be Uvicorn/FastAPI, another web server, an API gateway, or a load balancer acting on behalf of an application.

---

### The components of an HTTP request

Here is a complete simplified request:

```http
GET /products/101 HTTP/1.1
Host: api.example.com
Accept: application/json
X-Correlation-ID: req-123
```

An HTTP request has these parts:

#### 1. Request line

```http
GET /products/101 HTTP/1.1
```

| Part | Meaning |
|---|---|
| `GET` | Method: the action the client wants to perform |
| `/products/101` | Request target: the resource path being requested |
| `HTTP/1.1` | HTTP version used to represent this message |

The URL may also contain a query string:

```http
GET /products?category=electronics&limit=10 HTTP/1.1
```

Here, `/products` is the path and the values after `?` are query parameters.

#### 2. Request headers

```http
Host: api.example.com
Accept: application/json
X-Correlation-ID: req-123
```

Headers carry metadata about the request.

In this example:

- `Host` identifies the target hostname.
- `Accept` says the client can process a JSON response.
- `X-Correlation-ID` helps trace the request across services.

#### 3. Blank line

A blank line separates the headers from the optional body.

#### 4. Request body

A body carries data when the request needs one. For example:

```http
POST /products HTTP/1.1
Host: api.example.com
Content-Type: application/json
Accept: application/json

{
  "name": "Keyboard",
  "price": 2500
}
```

Here:

- The method is `POST`.
- The target is `/products`.
- `Content-Type` says the request body contains JSON.
- The JSON document is the request body.

Not every request has a body. A typical `GET` request usually sends its inputs through the path, query parameters, and headers.

---

### The components of an HTTP response

The server might answer the earlier `GET /products/101` request with:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 28
X-Correlation-ID: req-123

{"id":101,"name":"Keyboard"}
```

An HTTP response has these parts:

#### 1. Status line

```http
HTTP/1.1 200 OK
```

| Part | Meaning |
|---|---|
| `HTTP/1.1` | HTTP version used for the response |
| `200` | Machine-readable status code |
| `OK` | Human-readable reason phrase |

The status code tells the client the outcome at the HTTP level. Examples include:

- `200 OK` — the request succeeded.
- `201 Created` — a resource was created.
- `404 Not Found` — the requested resource was not found.
- `422 Unprocessable Content` — the input could not be processed.
- `500 Internal Server Error` — the server encountered an unexpected failure.

#### 2. Response headers

```http
Content-Type: application/json
Content-Length: 28
X-Correlation-ID: req-123
```

These describe the response:

- `Content-Type` says the response body is JSON.
- `Content-Length` gives the body size in bytes in this example.
- `X-Correlation-ID` returns the request-tracing identifier.

#### 3. Blank line

A blank line separates the response headers from the response body.

#### 4. Response body

```json
{"id":101,"name":"Keyboard"}
```

The body contains the returned representation of the product.

A response does not always contain a body. For example, a successful `204 No Content` response must not include response content.

---

### One complete HTTP conversation

```text
Client
  │
  │  GET /products/101
  │  Accept: application/json
  ▼
Server
  │
  │  200 OK
  │  Content-Type: application/json
  │  {"id": 101, "name": "Keyboard"}
  ▼
Client
```

HTTP defines what these messages mean. TCP carries the bytes reliably for HTTP/1.1 and HTTP/2, while IP helps route them to the correct machine.

### HTTP does not do every networking job

HTTP does not itself:

- Convert a hostname into an IP address—that is DNS.
- Choose the application on a machine—that involves a port and socket.
- Guarantee ordered byte delivery—that is TCP for HTTP/1.1 and HTTP/2.
- Encrypt the conversation—that is TLS when HTTPS is used.

This separation explains why an HTTP request can be perfectly valid but still fail before reaching FastAPI because DNS resolution, connection establishment, or TLS setup failed.

### Is HTTP stateless?

HTTP is described as **stateless** because each request is an independent message. HTTP does not require the server to remember earlier requests to understand the current one.

Applications can still create stateful user experiences by building mechanisms on top of HTTP, such as:

- Cookies
- Session identifiers
- Access tokens
- Database records

For example, the browser may send a session cookie with every request. The application uses that value to find stored session state, but the HTTP request itself remains a separate request.

---

## 🔓 Plain HTTP — HTTP Without TLS

When people say **plain HTTP**, they mean that HTTP messages are being exchanged without TLS protection.

For example:

```text
http://api.example.com/products/101
└── http scheme: no TLS protection
```

The HTTP message still has its normal method, path, headers, body, status code, and response. The problem is that the message is not encrypted or protected against modification while travelling across the network.

Conceptually, an observer able to inspect plain HTTP traffic could see or alter information such as:

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

## 🧠 Technical Lead Perspective — One Production Example

Imagine this setup for our product API:

```text
Client ── HTTPS ──► Load balancer ── HTTPS ──► Uvicorn/FastAPI
```

There are **two separate connections**: client to load balancer, and load balancer to backend. The load balancer reads the incoming request, then sends it onward. Let us answer the review questions using this example.

### 1. Where does TLS terminate?

TLS *terminates* wherever an HTTPS connection is decrypted. In this example, the client’s TLS connection ends at the load balancer. The load balancer starts a **new** TLS connection to the backend, which ends at Uvicorn or another backend proxy.

Some deployments use HTTP for that second hop; others use HTTPS. The public URL saying `https://` tells us about the client-facing connection, **not automatically the backend hop**.

**What to check:** At which component is each TLS certificate configured? What protocol is used from the load balancer to the service?

### 2. Is traffic protected on every required hop?

For the example above, both hops use HTTPS, so both are protected in transit. With this alternative:

```text
Client ── HTTPS ──► Load balancer ── HTTP ──► Uvicorn/FastAPI
```

the first hop is protected; the second is not protected by TLS. Whether that meets requirements depends on the network and security policy. Do not infer end-to-end protection from the browser’s padlock alone.

**What to check:** List each hop and record whether it uses HTTP or HTTPS, including hops between internal services if any.

### 3. Who owns certificate issuance and renewal?

A certificate lets the client verify the name it connected to, such as `api.example.com`. It has an expiry date. The team responsible for the component **terminating TLS** needs a way to issue, install, monitor, and renew its certificate.

For example, a cloud platform team might manage the load balancer certificate, while an application or platform team manages certificates on the backend hop. The owner is an **operational decision**, not something HTTP or FastAPI decides automatically.

**What to check:** Who is responsible for each certificate, when does it expire, how is renewal performed, and who is alerted if renewal fails?

### 4. Which HTTP versions do the load balancer and clients support?

The HTTP version can differ across the two connections. For example, a client might use HTTP/2 with the load balancer while the load balancer uses HTTP/1.1 with Uvicorn. The load balancer translates between them while forwarding the request.

HTTP/3 requires support on the **client-facing side** to be used there. Supporting HTTP/3 at the edge does not mean the backend also speaks HTTP/3.

**What to check:** Which versions are enabled on the client-to-load-balancer hop and on the load-balancer-to-backend hop? Verify actual traffic rather than assuming both match.

### 5. Are sensitive headers and URLs redacted from logs?

Consider this request:

```http
GET /products?access_token=secret123 HTTP/1.1
Authorization: Bearer secret456
```

The request may be encrypted while travelling over HTTPS, but a load balancer or application can still write the decrypted **URL or headers into its logs**. Access tokens, passwords, session cookies, and sensitive query parameters should not be recorded in full.

Prefer sending tokens through the appropriate authentication mechanism, keep secrets out of URLs, and configure logging at **each component** to omit or redact sensitive values. Keep safe information such as the path template, status, duration, and correlation ID when useful.

**What to check:** Inspect sample load balancer, proxy, application, and tracing logs for exposed credentials or personal data.

### 6. Does the application trust forwarded headers only from known proxies?

After TLS ends at the load balancer, it may tell Uvicorn about the original request using headers such as:

```http
X-Forwarded-Proto: https
X-Forwarded-For: 203.0.113.10
```

These report the original scheme and client address. But a client can also **send a header with the same name**. If the backend trusts it from anyone, a client may falsely claim an HTTPS request or a different source IP.

Configure the server to accept proxy headers **only from trusted proxy addresses**, and make sure the network path and proxy handling support that trust boundary. Uvicorn exposes settings such as `--proxy-headers` and `--forwarded-allow-ips`.

**What to check:** Which proxies are trusted, can clients reach the backend directly, and does the proxy replace or sanitize incoming forwarded headers?

### 7. Are connection, request, and upstream timeouts defined?

These clocks measure **different waits**:

| Timeout | What it limits | Example |
|---|---|---|
| Connection timeout | Time spent establishing a connection to another component | Load balancer cannot connect to the backend |
| Idle connection timeout | Time an unused connection stays open for another request | Uvicorn’s keep-alive timeout between requests defaults to 5 seconds |
| Request/response deadline | How long a client or gateway is willing to wait for the operation or response | Client gives up while an endpoint is still working |
| Upstream response/read timeout | How long a proxy waits to receive data from its backend | Backend stops sending data and proxy times out |

These settings can exist on the client, load balancer, reverse proxy, and backend. A short gateway timeout can make a client see an error even while the FastAPI function continues running. The precise meaning of each setting depends on the component, so read that component’s documentation.

**What to check:** Draw the request path and record each component’s relevant timeout. Check that the chosen values fit the expected operation.

### 8. Can we locate the layer where a failure occurred?

Look for the **first step that did not succeed**:

| Observation | First place to investigate |
|---|---|
| Hostname does not resolve | DNS/name configuration |
| Connection refused or cannot connect | IP, port, firewall, listening server, or network path |
| Certificate validation fails | TLS certificate, hostname, trust, or expiry |
| Request gets an HTTP `404` | Routing/path or missing resource |
| FastAPI responds with `422` | Input validation |
| Request reaches the app and ends in `500` | Application code or a dependency used by it |
| Gateway times out before a backend response | Gateway timeout, backend availability, or slow work |

An HTTP `404` or `422` proves an HTTP response was received. A DNS failure or refused connection happens before FastAPI can return an HTTP status. Logs at each hop plus a correlation ID help connect observations to one request.

**At this stage:** Be able to describe the two connections, identify who handles each responsibility, and choose the first layer to inspect. We will practice configuring certificates, proxies, and timeouts in the production phase.
---

## ✅ Check Your Understanding

1. What does each word in **Hypertext Transfer Protocol** mean?
2. What are the four main parts of an HTTP request?
3. What are the four main parts of an HTTP response?
4. What does HTTP provide that TCP does not, and what does TCP provide that HTTP does not?
5. Why can one IP address host several services, and what role does a port play?
6. Does placing a token in an HTTP header encrypt it?
7. What three primary protections does TLS provide?
8. Why can TLS termination at a load balancer matter to backend security?
9. What changed from HTTP/1.1 to HTTP/2 and HTTP/3?
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
