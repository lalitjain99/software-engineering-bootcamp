# Topic 07 — API Styles and Communication Mechanisms

> **Single learning goal:** Choose a communication approach by first identifying who initiates communication, who must send data, and how long the interaction lasts.

## 🪜 How to Study This Topic

Do **not** try to learn all six mechanisms from this comparison document in one pass. REST is our known baseline; the others will be learned through small implementations, one at a time.

Use this sequence:

1. **REST baseline** — recall the request-response model you already know.
2. **Webhook** — ordinary HTTP, but one server becomes the client of another server.
3. **Server-Sent Events (SSE)** — keep one HTTP response open so the server can send a stream of updates.
4. **WebSocket** — keep a connection open so either side can send messages.
5. **GraphQL** — change how the client asks for and shapes data.
6. **gRPC** — call strongly defined service methods using a generated contract.

For each mechanism:

1. Read only its short section in this document.
2. Run its focused micro-lab.
3. Draw or explain who initiates communication, which direction data travels, and when the connection closes.
4. Compare it with the REST request-response flow.
5. Answer interview questions only after the implementation makes sense.

The rest of this file is a **reference**, not a lecture that must be memorized before touching code.

---

## 🌱 One Product System, Different Communication Problems

Our Product API currently uses operations such as:

```http
GET /products/101
POST /products
DELETE /products/101
```

This works well when a client requests or changes a resource and receives a response.

Now the system grows:

1. A mobile client wants normal product operations.
2. A dashboard wants products, stores, and suppliers in one custom-shaped response.
3. An internal inventory service needs a strongly defined service contract.
4. A warehouse screen must both send and receive live messages.
5. A browser needs only a continuous stream of stock updates.
6. An external supplier must be notified when a product is created.

These are different interaction problems. Choosing one technology for all six would create unnecessary difficulty.

---

## 🧭 Start With the Direction of Communication

Before choosing a technology, ask:

1. **Who starts the interaction?**
2. **Does data need to travel in one direction or both directions?**
3. **Does the connection end after one response or remain open?**
4. **Is the other side a browser, mobile app, internal service, or external company?**
5. **Does the caller need resource operations, flexible data selection, remote methods, or event notifications?**

A first mental model is:

| Need | Natural starting point |
|---|---|
| Client requests or changes resources | REST-style HTTP API |
| Client chooses a custom data shape | GraphQL |
| Internal service calls a strongly typed remote method | gRPC |
| Client and server exchange live messages | WebSocket |
| Server continuously pushes updates to a client | Server-Sent Events |
| One server notifies another server after an event | Webhook |

This table is a starting point, not an automatic decision. Operational constraints and existing infrastructure still matter.

---

## 🧩 These Terms Are Not the Same Kind of Thing

| Name | What it is |
|---|---|
| REST | An architectural style with constraints for distributed systems |
| GraphQL | A query language and execution model built around a typed schema |
| gRPC | A Remote Procedure Call framework, commonly using Protocol Buffers and HTTP/2 |
| WebSocket | A protocol for persistent, two-way communication |
| Server-Sent Events | An HTTP mechanism for a server to stream text events to a client |
| Webhook | An application pattern in which one server calls another server’s HTTP endpoint after an event |

For practical backend work, people often compare them because each can connect applications. A Technical Lead should also recognize that they solve different categories of problems.

---

## 1. REST-Style HTTP — Work With Resources

### The problem

A mobile application needs to:

- Read product `101`
- List products
- Create a product
- Change a product
- Delete a product

A resource-oriented HTTP interface is a natural fit:

```http
GET    /products/101
GET    /products?category=electronics
POST   /products
PATCH  /products/101
DELETE /products/101
```

Here:

- The URI identifies the resource or collection.
- The HTTP method expresses the operation’s semantics.
- Headers provide metadata.
- The body carries a representation.
- The status code communicates the result.

### What does REST mean?

REST stands for **Representational State Transfer**. It is an architectural style, not a wire protocol and not simply “JSON over HTTP.”

One central idea is that clients interact with **resources through representations**. Product `101` is the resource; the JSON document returned by the server is one representation of its state.

Full REST includes architectural constraints such as a uniform interface, stateless interactions, cacheability, client-server separation, layered systems, and optional code-on-demand. Many production APIs called “REST APIs” are more accurately described as **REST-style or resource-oriented HTTP APIs** because they apply only part of the full style.

For this roadmap, our immediate design skill is resource-oriented HTTP: meaningful resource paths, standard HTTP methods, accurate status codes, and predictable representations.

### Strengths

- Familiar to browsers, mobile clients, API tools, gateways, and developers
- Uses standard HTTP semantics and caching mechanisms
- Easy to inspect with tools such as curl and Postman
- Works well for public APIs and conventional resource operations
- Each request can be handled independently

### Costs and design risks

- A client may need several requests to assemble a complex screen.
- Fixed responses may return fields a particular client does not need.
- Poor endpoint design can create action-heavy paths such as `/doSomething` everywhere.
- API evolution and compatibility still require discipline.

Several requests or a large response do not automatically justify replacing REST. Pagination, filters, field selection, aggregation endpoints, and caching may solve the actual issue more simply.

---

## 2. GraphQL — Let the Client Select the Data Shape

### The problem

A product-details screen needs:

- Product name and price
- Store name
- Supplier name
- Only the last two reviews

A resource API might require multiple calls or an endpoint designed specifically for that screen.

With GraphQL, the client describes the fields it needs:

```graphql
query {
  product(id: 101) {
    name
    price
    store {
      name
    }
    supplier {
      name
    }
    reviews(limit: 2) {
      rating
      comment
    }
  }
}
```

A GraphQL response follows the requested shape:

```json
{
  "data": {
    "product": {
      "name": "Keyboard",
      "price": 2500,
      "store": {"name": "Central Store"},
      "supplier": {"name": "Input Devices Ltd"},
      "reviews": [
        {"rating": 5, "comment": "Excellent"},
        {"rating": 4, "comment": "Good"}
      ]
    }
  }
}
```

### What GraphQL changes

Instead of designing a separate URL for every data shape, the server exposes a **typed schema**. Clients send operations against that schema.

The principal operation types are:

- **Query** — read data
- **Mutation** — request a change
- **Subscription** — receive ongoing results, using a supported transport

GraphQL is not a database. The server decides how each field is resolved. Data may come from databases, REST APIs, gRPC services, caches, or other sources.

GraphQL is commonly served through an HTTP endpoint such as `POST /graphql`, but GraphQL and HTTP are separate layers.

### Strengths

- Clients can request a precise, nested data shape.
- The schema provides a discoverable, typed contract.
- It can reduce client-side coordination across related data.
- It can support several client types whose field needs differ.

### Costs and design risks

- A simple-looking query can trigger many backend calls or N+1 database queries.
- Authorization must be enforced at the appropriate object and field boundaries.
- Query depth, breadth, aliases, and complexity may need limits.
- HTTP caching and observability can be less direct than with distinct resource URLs.
- The schema can become difficult to govern if ownership is unclear.

Choose GraphQL because clients genuinely need flexible, connected data. Do not choose it only to avoid designing HTTP endpoints.

---

## 3. gRPC — Call a Strongly Defined Remote Service Method

### The problem

An internal Order Service needs the Inventory Service to reserve stock. The interaction is naturally expressed as a service operation:

```text
ReserveStock(product_id=101, quantity=2)
```

With gRPC, the contract is commonly defined in a `.proto` file:

```proto
service InventoryService {
  rpc ReserveStock (ReserveStockRequest) returns (ReserveStockResponse);
}

message ReserveStockRequest {
  int64 product_id = 1;
  int32 quantity = 2;
}

message ReserveStockResponse {
  bool reserved = 1;
}
```

Tools generate client and server code from this contract. Client code calls a generated stub that looks similar to a local method, while the framework performs the network exchange.

### What gRPC provides

gRPC is an RPC framework. It commonly uses:

- Protocol Buffers for the service definition and binary message format
- Generated client and server code
- HTTP/2 as its transport
- Unary calls and several streaming patterns

A **unary call** has one request and one response. gRPC also supports server streaming, client streaming, and bidirectional streaming.

### Strengths

- Strong, language-neutral service contracts
- Generated clients reduce manual serialization code
- Compact binary messages
- Efficient HTTP/2 connections and streaming support
- Useful for controlled service-to-service environments

### Costs and design risks

- Payloads are less convenient for humans to read directly.
- Browsers generally need gRPC-Web and supporting infrastructure rather than using native gRPC directly.
- Schema evolution requires Protocol Buffer compatibility discipline.
- Debugging and gateway support require appropriate tooling.
- Treating remote calls like local methods can hide network latency, failure, and retry consequences.

gRPC is often a good internal-service choice when teams control both ends and value generated contracts and streaming. It is not automatically faster or better for every API.

---

## 4. WebSocket — Keep a Two-Way Conversation Open

### The problem

A warehouse screen must:

- Receive live inventory changes
- Send scanner events immediately
- Receive acknowledgements and commands

Repeated request-response polling adds delay and unnecessary traffic. Both client and server need to send messages whenever they have something to say.

WebSocket establishes a persistent, full-duplex communication channel:

```text
Warehouse client ◄────────────► Inventory server
                  live messages
```

The communication begins with an HTTP-based handshake. After the WebSocket connection is established, both sides exchange WebSocket messages over the persistent connection rather than creating a normal HTTP request for every message.

### Is WebSocket another communication language like HTTP?

Broadly, yes. HTTP and WebSocket are both **application-layer protocols**: agreed rulebooks that applications follow when exchanging data.

Using the letter-and-conversation analogy:

- **HTTP** defines a formal request-and-response letter format.
- **WebSocket** defines an ongoing two-way conversation format.

HTTP defines request methods, paths, headers, bodies, status codes, and responses:

```http
POST /products HTTP/1.1
Content-Type: application/json

{"name": "Keyboard"}
```

After a WebSocket connection is established, applications no longer create a new HTTP request for every message. They exchange **WebSocket frames**:

```text
Browser → {"type": "scan", "quantity": 2}

Server  → {"type": "scan_acknowledged", "available": 18}

Server  → {"type": "stock_snapshot", "available": 18}
```

The WebSocket protocol defines transport-level messaging rules such as:

- Where a message begins and ends
- Whether a message contains text or binary data
- Ping and pong control messages
- How either side closes the connection
- How both sides can send messages over the persistent connection

WebSocket does **not** define the business meaning of this message:

```json
{
  "type": "scan",
  "product_id": 101,
  "quantity": 2
}
```

Our application defines what `scan`, `product_id`, and `quantity` mean. Therefore, a WebSocket application has two related contracts:

| Contract | Responsibility |
|---|---|
| WebSocket protocol | Transports and separates text or binary messages |
| Application message contract | Defines message types, fields, validation, and business meaning |

### How HTTP changes into WebSocket

The browser first sends an HTTP upgrade request:

```http
GET /ws/inventory HTTP/1.1
Connection: Upgrade
Upgrade: websocket
```

The server accepts it:

```http
HTTP/1.1 101 Switching Protocols
Connection: Upgrade
Upgrade: websocket
```

The same underlying TCP connection remains open, but communication switches from HTTP request-response messages to WebSocket frames:

```text
HTTP handshake
      ↓
101 Switching Protocols
      ↓
Same TCP connection
      ↓
WebSocket messages in both directions
```

For the local lab, the layers are:

```text
JSON application message
        ↓
WebSocket frame
        ↓
TCP bytes
        ↓
IP network
```

A secure WebSocket connection adds TLS:

```text
JSON application message
        ↓
WebSocket frame
        ↓
TLS encryption
        ↓
TCP bytes
        ↓
IP network
```

The URL scheme shows whether TLS is used:

- `ws://` — WebSocket without TLS
- `wss://` — WebSocket protected by TLS

### Strengths

- Two-way, low-latency message exchange
- Server can push without waiting for a new HTTP request
- Suitable for chat, collaborative editing, games, and interactive control
- Supports text and binary messages

### Costs and design risks

- Each live connection consumes resources and has a lifecycle.
- Clients need reconnect and missed-message strategies.
- Authentication may need renewal during long connections.
- Load balancers and proxies need WebSocket support and suitable idle timeouts.
- Scaling across server instances may require shared messaging or connection routing.
- The application must define its own message types and error contract.

Use WebSocket when **both sides** need frequent, independent communication. A single occasional server notification does not necessarily require it.

---

## 5. Server-Sent Events — Stream Updates From Server to Client

### The problem

A browser dashboard needs live stock counts. The browser sends no messages over the live channel; it only needs the server’s updates.

The browser opens an HTTP connection:

```http
GET /inventory/events HTTP/1.1
Accept: text/event-stream
```

The server keeps the response open and sends events:

```text
event: stock_changed
id: 842
data: {"product_id":101,"available":18}

event: stock_changed
id: 843
data: {"product_id":102,"available":7}

```

Each blank line ends an event.

In a browser, `EventSource` provides an API for receiving the stream and includes reconnection behaviour. If the client must send a command, it uses a separate HTTP request.

### How can we identify SSE versus a normal HTTP response?

SSE is itself an HTTP response. The difference is that it uses a specific content type and event format, and the response normally remains open so more events can arrive.

#### 1. Check the response `Content-Type`

The clearest signal is:

```http
Content-Type: text/event-stream
```

This tells the client to interpret the response body using the Server-Sent Events format.

A normal JSON API response commonly uses:

```http
Content-Type: application/json
```

The request may contain:

```http
Accept: text/event-stream
```

but `Accept` only describes what the client wants. The server's response `Content-Type` identifies what it actually sent.

#### 2. Inspect the response body format

An SSE body follows a line-based format:

```text
id: 842
event: stock_changed
data: {"product_id":101,"available":18}

id: 843
event: stock_changed
data: {"product_id":101,"available":17}

```

Common SSE fields include:

- `event:` — the event type
- `id:` — the event identifier
- `data:` — the event payload
- A blank line — the end of one event

The `data:` value may contain JSON text, but the complete response body is not one JSON document.

A normal JSON response usually arrives as one complete value:

```json
{
  "product_id": 101,
  "available": 18
}
```

#### 3. Observe the response lifetime

With a normal API response:

1. The server sends the status line, headers, and complete body.
2. The response finishes.
3. The TCP connection may close or remain idle for reuse.

With SSE:

1. The server sends the status line and headers.
2. It sends one event as part of the response body.
3. It keeps the response unfinished.
4. It sends more events through the same response later.

For example:

```cmd
curl.exe -N -i http://127.0.0.1:8000/inventory/events
```

The `-N` option only disables curl's output buffering. The server keeps the stream open by not completing the response.

#### 4. Inspect it in browser developer tools

In the Network tab, the SSE request normally:

- Has `Content-Type: text/event-stream`
- Remains open or pending
- Receives additional event data over time
- Does not create a new request for each event

A browser `EventSource` object is another strong indication that the client expects SSE.

#### Signals that do not prove it is SSE

| Observation | Why it is not sufficient |
|---|---|
| `Connection: keep-alive` | Normal HTTP connections can also remain available for reuse |
| No `Content-Length` | Other streaming or dynamically generated responses may also omit it |
| `Transfer-Encoding: chunked` | HTTP/1.1 can use chunking for many kinds of streaming responses; HTTP/2 does not use this header |
| The endpoint uses `StreamingResponse` | A generic stream becomes SSE only when it uses `text/event-stream` and valid SSE event formatting |

The most reliable identification is therefore:

```text
Content-Type: text/event-stream
          +
SSE-formatted event lines
          +
An HTTP response that stays open for additional events
```

### Strengths

- Simple server-to-client streaming over HTTP
- Natural browser support through `EventSource`
- Automatic reconnection behaviour in the browser API
- Text format is easy to inspect
- Fits notifications, progress, monitoring, and live feeds

### Costs and design risks

- The event stream is one-way: server to client.
- The standard event format is UTF-8 text; binary data needs encoding or another mechanism.
- Long-lived connections require proxy timeout and capacity planning.
- Reconnection raises questions about event IDs, retention, and missed events.
- Browser authentication constraints must be considered when designing the endpoint.

Choose SSE when the server pushes updates and the client can send any commands through ordinary HTTP requests.

---

## 6. Webhooks — Notify Another Server After an Event

### The problem

When a product is created, an external supplier system must be notified. The supplier does not want to poll:

```http
GET /products/changes
```

every few seconds.

Instead, the supplier registers an HTTPS endpoint. When the event occurs, our application sends an HTTP request to that endpoint:

```http
POST /supplier-events HTTP/1.1
Content-Type: application/json
X-Webhook-ID: evt-734
X-Webhook-Signature: <signature>

{
  "type": "product.created",
  "product_id": 101
}
```

This callback is a **webhook**.

### What makes webhook delivery different

A normal API call is initiated by the client that wants data. With a webhook, the event-producing server becomes the HTTP client and calls the subscriber’s server.

```text
Normal API:
Mobile client ── request ──► Product API

Webhook:
Product system ── event callback ──► Supplier endpoint
```

### Strengths

- Event-driven communication without constant polling
- Works across organizations using ordinary HTTPS
- The receiver can react shortly after an event
- Sender and receiver do not need one persistent connection

### Costs and design risks

- The receiver may be unavailable when delivery occurs.
- Senders need a defined retry and failure policy.
- Duplicate delivery is possible, so receivers should process events idempotently.
- Receivers must verify authenticity, commonly using a signature based on a shared secret.
- Event identifiers help detect duplicates and support investigation.
- Delivery logs must avoid leaking secrets or sensitive payloads.

A `2xx` response usually means the receiver accepted the delivery at the HTTP level. It does not necessarily prove that every downstream business action finished successfully.

Webhook retry behaviour is defined by the provider; there is no universal retry policy shared by every webhook system.

---

## 🔄 Do We Have to Choose Only One?

No. A single product system might use:

```text
Mobile app ── REST ──► Product API
Admin UI ── GraphQL ──► Product data layer
Order Service ── gRPC ──► Inventory Service
Warehouse screen ◄── WebSocket ──► Inventory Service
Browser dashboard ◄── SSE ── Inventory Service
Product system ── Webhook ──► Supplier system
```

The architecture should use the smallest set of mechanisms that clearly solves the actual interaction problems. Every additional mechanism adds deployment, security, testing, monitoring, and developer-learning costs.

---

## ⚖️ Side-by-Side Comparison

| Approach | Typical direction | Connection shape | Contract/data style | Natural fit |
|---|---|---|---|---|
| REST-style HTTP | Client request → server response | Usually one exchange on a reusable HTTP connection | Resources, HTTP methods, representations | Public and conventional CRUD-style APIs |
| GraphQL | Client operation → server result | Usually HTTP request-response; subscriptions may remain active | Typed schema and client-selected fields | Flexible, connected UI data |
| gRPC | Client invokes server method | HTTP/2 connection; unary or streaming RPC | `.proto` service and messages | Controlled internal services |
| WebSocket | Both directions independently | Persistent two-way connection | Application-defined messages | Interactive real-time communication |
| SSE | Server continuously pushes to client | Long-lived HTTP response | UTF-8 event stream | Browser notifications and live feeds |
| Webhook | Event producer calls subscriber | Separate HTTP delivery per event or batch | Provider-defined event payload | Server-to-server event notification |

---

## 🧠 A Technical Lead’s Selection Process

### Step 1: State the interaction

Avoid beginning with “Should we use GraphQL or gRPC?” Start with a sentence such as:

> When stock changes, the server must update an open browser dashboard within two seconds. The browser does not send messages on that channel.

That points toward SSE more clearly than a technology-first discussion.

### Step 2: Identify the parties and direction

- Browser, mobile app, internal service, or external partner?
- Client-to-server request-response?
- Server-to-client stream?
- Independent messages in both directions?
- Event callback between servers?

### Step 3: Define the contract

- Resource and HTTP semantics?
- Client-selected graph of fields?
- Strong RPC method and generated types?
- Application-defined live messages?
- Versioned event payload?

### Step 4: Check operational fit

- Do gateways and clients support it?
- How are authentication and authorization applied?
- How are timeouts, reconnects, retries, and duplicates handled?
- Can the team observe and debug it?
- How will the contract evolve without breaking consumers?
- What happens when either side is slow or unavailable?

### Step 5: Prefer the simplest sufficient mechanism

Examples:

- A normal product catalogue does not need WebSocket merely because “real time” sounds modern.
- A one-way browser notification feed may use SSE instead of a two-way WebSocket protocol.
- One external event callback may use a webhook instead of maintaining a permanent connection.
- An internal typed RPC requirement may justify gRPC, while a public partner API may remain REST-style HTTP.

---

## 🚫 Common Selection Mistakes

### “REST means JSON over HTTP”

JSON over HTTP can ignore REST constraints completely. Focus on resources, representations, HTTP semantics, stateless interaction, cacheability, and the other architectural constraints relevant to the design.

### “GraphQL replaces the database”

GraphQL defines the client-facing schema and execution model. Resolvers still need well-designed database queries and service calls.

### “gRPC is a local function call”

It looks like a method call, but it crosses a network. It can be slow, time out, fail partially, or be retried. Deadlines and idempotency still matter.

### “WebSocket is always the real-time choice”

If communication is one-way, SSE may be simpler. If updates are infrequent, polling may be sufficient.

### “SSE supports two-way messaging”

The event stream sends data from server to client. Client commands require separate requests.

### “A successful webhook response means business processing finished”

A `2xx` confirms HTTP-level acceptance according to the receiver’s contract. The receiver may queue the actual work for later.

---

## ✅ Check Your Understanding

1. Why are REST, GraphQL, gRPC, WebSocket, SSE, and webhooks not six versions of the same thing?
2. Which approach would you begin with for conventional product CRUD operations, and why?
3. When can GraphQL reduce client coordination?
4. Why should a gRPC call still be treated as a network operation?
5. When would SSE be simpler than WebSocket?
6. Why must webhook receivers handle duplicate events?
7. Can one system use REST for its public API and gRPC internally?
8. What questions should be answered before choosing any communication mechanism?

---

## 🛑 Intentional Stop Point

This lesson does not yet implement:

- Full REST constraints and hypermedia controls
- GraphQL schemas, resolvers, subscriptions, or query-cost enforcement
- Protocol Buffer compatibility rules and gRPC interceptors
- WebSocket authentication, fan-out, backpressure, and multi-instance scaling
- SSE replay storage and `Last-Event-ID` recovery
- Webhook signing, retry scheduling, and dead-letter handling

Those details will be introduced through hands-on work or later architecture, security, reliability, and messaging topics.

## ➡️ Next Step

The [Webhook micro-lab](Hands_On/01_Webhook/README.md), [SSE micro-lab](Hands_On/02_SSE/README.md), and [WebSocket micro-lab](Hands_On/03_WebSocket/README.md) are complete.

Now complete the focused [GraphQL micro-lab](Hands_On/04_GraphQL/README.md). Observe how different client selection sets change the response shape while every operation continues to use the same GraphQL endpoint.

Do not study gRPC yet. After the GraphQL implementation is clear, we will build the final gRPC micro-lab.

After all focused labs, answer interview questions one at a time in chat. We will create `Interview.md` only after reviewing the answers.

## 📚 References

- [Roy Fielding — Representational State Transfer](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)
- [RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [GraphQL Specification](https://spec.graphql.org/)
- [gRPC Introduction](https://grpc.io/docs/what-is-grpc/introduction/)
- [RFC 6455 — The WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455.html)
- [WHATWG HTML — Server-Sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [GitHub Webhooks Documentation — example of the webhook pattern](https://docs.github.com/en/webhooks)
