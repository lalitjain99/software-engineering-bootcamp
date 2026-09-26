# Topic 07 — Interview Questions: API Styles and Communication

These answers were developed from the hands-on labs and reviewed in chat. The goal is not to memorize technology definitions. The goal is to select a communication mechanism from the interaction requirements and explain its trade-offs.

## 1. A browser dashboard needs one-way live stock updates. What would you choose?

I would begin with **Server-Sent Events (SSE)**.

The browser initiates an HTTP request to the SSE endpoint. The server responds with <code>Content-Type: text/event-stream</code> and keeps the HTTP response open. Whenever inventory changes, the server sends another event through the same response.

Data travels from server to client until the client disconnects, the server closes the stream, a timeout closes it, or the network fails. The server sends events when updates or keep-alive messages are available; it does not need to send data continuously.

Why the alternatives are less suitable:

- **REST polling** repeatedly creates requests, including when nothing has changed. It may still be acceptable when updates are infrequent and delay is tolerable.
- **WebSocket** can solve the problem but adds two-way messaging and connection-management complexity that this requirement does not need.
- **Webhook** is mainly a server-to-server callback. A browser normally does not expose a stable public endpoint for receiving webhook requests.

## 2. A warehouse client must send scanner events and receive live commands. What would you choose?

I would choose **WebSocket** because both the warehouse client and server must send messages independently at any time.

SSE is insufficient for this channel because it sends events only from server to client. The client could send separate HTTP requests, but WebSocket is more natural when both directions require frequent live communication through the same connection.

In the HTTP/1.1 handshake model used in the lab, the client sends an HTTP upgrade request:

~~~http
GET /ws/inventory HTTP/1.1
Connection: Upgrade
Upgrade: websocket
~~~

The server accepts it with:

~~~http
HTTP/1.1 101 Switching Protocols
Connection: Upgrade
Upgrade: websocket
~~~

After the handshake, the same underlying TCP connection remains open, but communication switches from HTTP request-response messages to WebSocket frames. Each scanner event or stock update does not create a new HTTP request.

The connection lasts until one side closes it, a timeout closes it, or the network fails.

## 3. How would you notify an external supplier after a product is created?

I would use a **webhook**. The event-producing Product Service becomes the HTTP client and sends a request to the Supplier Service's registered endpoint whenever the event occurs.

A permanent connection is not required. Each event or batch is normally delivered through a separate HTTP request.

If the Supplier Service is unavailable, the Product Service should use a defined delivery policy:

- Store the event durably before or while scheduling delivery.
- Retry temporary failures using exponential backoff and jitter.
- Limit the attempts or retry duration.
- Record delivery status for investigation.
- Move repeatedly failing events to a dead-letter or manual-recovery flow when appropriate.

Retries can create duplicate deliveries. For example, the supplier may process an event but its successful response may be lost. The Product Service then cannot know whether processing occurred and may retry.

The receiver should process events idempotently:

1. Read a stable event identifier.
2. Check whether that identifier has already been processed.
3. If it has, return success without repeating the business action.
4. Otherwise, process the event and record the identifier atomically with the result.

The supplier should verify authenticity. A common design is to send a timestamp and an HMAC signature calculated from the timestamp and raw request body using a shared secret:

~~~http
X-Webhook-ID: evt-734
X-Webhook-Timestamp: 1790420000
X-Webhook-Signature: sha256=...
~~~

The receiver calculates the expected signature and compares it securely. The timestamp can also help reject replayed requests outside an allowed time window. HTTPS is still required to protect the request in transit.

## 4. When is GraphQL useful, and how does it work with HTTP?

GraphQL is useful when different clients need different combinations of connected data. For example, a product page may need product details, store information, supplier information, and only the latest two reviews.

Instead of defining a separate endpoint for every data shape, the server exposes a typed GraphQL schema. The client sends an operation that selects the required fields.

GraphQL is commonly exposed through an endpoint such as <code>/graphql</code>. A query can be transported inside a normal HTTP request:

~~~http
POST /graphql HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json
Accept: application/json

{
  "query": "query { product(id: 101) { name price } }"
}
~~~

The result is returned in an HTTP response:

~~~http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "product": {
      "name": "Keyboard",
      "price": 2500
    }
  }
}
~~~

HTTP provides the transport envelope: method, URL, headers, request body, status, and response delivery. GraphQL defines the schema, operations, selected fields, validation, and execution rules.

GraphQL is not a database. Resolvers decide how fields are obtained. Data can come from databases, REST APIs, gRPC services, caches, or other sources.

A major performance risk is excessive resolver work. A list resolver followed by one related-data query for every item can create the N+1 query problem. Deeply nested lists can also create an enormous result and high database or CPU cost.

Controls include:

- DataLoader-style batching
- Appropriate joins, eager loading, or prefetching
- Pagination and maximum page sizes
- Query-depth and complexity limits
- Deadlines and rate limits
- Persisted or allow-listed queries where appropriate
- Field-level authorization
- Resolver latency and database-query monitoring

GraphQL queries can sometimes use HTTP <code>GET</code>, while mutations normally use <code>POST</code>. In the lab, operations were sent using <code>POST</code>.

## 5. Why might internal services use gRPC?

gRPC can be a good fit when controlled internal services need a strongly typed, language-neutral contract and generated integration code.

A <code>.proto</code> file defines:

- Services
- Remote procedure names
- Request and response message types
- Field names, types, and wire identifiers

For Python, code generation produces:

- <code>*_pb2.py</code> — generated Protocol Buffer message classes and serialization support
- <code>*_pb2_grpc.py</code> — generated client stubs, server interfaces, and service-registration code

When the client calls:

~~~python
response = stub.ReserveStock(request, timeout=3)
~~~

the generated stub serializes the request into Protobuf binary data, sends the gRPC call using HTTP/2, waits for the remote server, and deserializes the response into a generated Python object.

Although the syntax resembles a local method call, it is a network operation. It has latency and can fail because of DNS, connection, TLS, authentication, load balancer, server, dependency, or deadline problems.

A deadline prevents the caller from waiting without a defined bound. Without bounded waiting, many stalled calls can consume threads, connections, memory, and request capacity, eventually degrading the service.

A Python client and Java server can generate compatible code from the same contract, provided both use compatible versions of the <code>.proto</code> definition.

## 6. Should a timed-out gRPC stock reservation be retried?

It should not be retried blindly.

A <code>DEADLINE_EXCEEDED</code> status means the client stopped waiting. It does not prove that the server performed no work. The server may have reserved the stock before the response was delayed or lost.

A blind retry could reserve or deduct the stock twice.

A safer design uses a unique reservation ID as an idempotency key. The Inventory Service should atomically store the reservation result against that ID. If the same ID and request are received again, it returns the stored result instead of repeating the reservation. Reusing the same ID with a different payload should be rejected.

General retry guidance:

| gRPC status | Guidance |
|---|---|
| <code>UNAVAILABLE</code> | Potentially retry with backoff, but only when repetition is safe or protected against duplicates |
| <code>DEADLINE_EXCEEDED</code> | Completion is ambiguous; retry only with appropriate idempotency protection |
| <code>INVALID_ARGUMENT</code> | Do not retry without changing the request |
| <code>NOT_FOUND</code> | Usually do not retry unchanged; it may be temporary only under known eventual-consistency conditions |

Retries should also use exponential backoff, jitter, maximum attempts, and an overall retry budget or deadline.

## 7. Which mechanism fits each product-platform requirement?

| Requirement | Natural starting point | Reason |
|---|---|---|
| Mobile product CRUD | REST-style HTTP | Resource-oriented operations and standard HTTP semantics |
| Flexible product, store, supplier, and review fields | GraphQL | Clients select connected fields through a typed schema |
| Order Service calls Inventory Service | gRPC | Strong internal service contract and generated stubs |
| Browser receives one-way stock updates | SSE | Long-lived server-to-client HTTP event stream |
| Warehouse sends scanner events and receives commands | WebSocket | Persistent full-duplex messages |
| Product Service notifies an external supplier | Webhook | Event-driven server-to-server HTTP callback |

Using one mechanism for everything is not necessarily simpler. Each requirement has a different communication direction, connection lifecycle, client type, and contract requirement.

Forcing one mechanism everywhere can create poor fits—for example, WebSocket for ordinary CRUD, GraphQL for a simple callback, or native gRPC for browser clients.

At the same time, every additional mechanism adds development, security, deployment, monitoring, testing, and learning costs. The goal is the smallest set of mechanisms that clearly solves the requirements.

## 8. Are these six mechanisms the same kind of technology?

No.

| Mechanism | Technical category |
|---|---|
| REST | Architectural style for distributed systems |
| GraphQL | Query language, typed schema, and execution model |
| gRPC | Remote Procedure Call framework, commonly using Protobuf and HTTP/2 |
| WebSocket | Application-layer protocol for persistent, full-duplex communication |
| SSE | HTTP-based mechanism and event format for server-to-client streaming |
| Webhook | Application integration pattern in which one server calls another after an event |

They are compared because they all help applications communicate or expose capabilities. They operate at different conceptual layers and solve different interaction problems.

Their relationship with HTTP is also different:

- GraphQL is commonly transported over HTTP.
- Native gRPC commonly uses HTTP/2.
- WebSocket commonly begins with an HTTP upgrade handshake.
- SSE is a long-lived HTTP response.
- Webhooks ordinarily use separate HTTP requests.
- REST is an architectural style; REST-style APIs commonly use HTTP, but REST is not itself a wire protocol.

## 9. Should four REST calls for one screen cause a migration to GraphQL?

No. Replacing an entire API is a high-risk response to one screen's performance complaint.

I would first investigate:

- Which data each request retrieves
- Whether calls are sequential or parallel
- Actual latency of each request
- Payload sizes and unused data
- Database and downstream-service work
- Whether caching is effective
- How many clients have the same problem
- Whether client data requirements change frequently

REST-based improvements may include:

- Running independent calls in parallel
- Creating a purpose-built aggregation endpoint
- Supporting controlled related-resource expansion
- Supporting field selection where useful
- Improving caching, payloads, database queries, or downstream calls
- Using HTTP/2 to reduce connection-level overhead for concurrent requests

An endpoint such as <code>/products/{id}/details</code> is an aggregation endpoint. It is specifically a Backend for Frontend when it belongs to a client-specific backend layer, such as a Web BFF or Mobile BFF.

HTTP/2 multiplexing can reduce transport overhead, but it does not remove database work, oversized payloads, or sequential dependencies.

GraphQL becomes more compelling when multiple clients need different and frequently changing subsets of a highly connected domain. Its benefits must justify new costs:

- Schema design and governance
- Resolver implementation and N+1 risks
- Query-depth and complexity controls
- Field-level authorization
- Less direct HTTP caching
- Observability and cost attribution
- New tooling, testing, and team learning

## Common Mistakes

### Choosing from popularity instead of interaction requirements

Start with who communicates, which direction data travels, whether the connection stays open, what contract is needed, and which parties control the clients and servers.

### Treating polling as always wrong

Polling may be the simplest choice for infrequent updates where delay is acceptable. Its cost depends on frequency, client count, response size, and freshness requirements.

### Saying WebSocket is required for every real-time feature

For one-way browser updates, SSE may be simpler. WebSocket is valuable when both sides need independent live messaging.

### Saying SSE prevents the client from communicating at all

SSE is one-way on the event stream. The client can still send commands through separate HTTP requests.

### Treating a webhook as a persistent connection

A webhook normally creates an HTTP delivery when an event occurs. It does not keep the subscriber connected continuously.

### Assuming a webhook is reliable because HTTPS succeeded

HTTPS protects data in transit. Reliable delivery still needs durable event handling, retries, duplicate protection, and monitoring. Authenticity normally needs a signature or another authentication mechanism.

### Treating GraphQL as a database

GraphQL defines the client-facing schema and execution model. Resolvers still need efficient data access and downstream service calls.

### Assuming GraphQL always uses POST or must have one endpoint

Those are common conventions, not the complete definition of GraphQL.

### Treating a gRPC stub call as local

Generated code hides serialization and transport details, but the call still has network latency, partial-failure possibilities, and deadlines.

### Retrying every <code>UNAVAILABLE</code> or timed-out RPC

A failure response does not always prove that the server made no state change. Retry only when repetition is safe or idempotency protection exists.

### Calling every aggregation endpoint a BFF

A BFF is a client-specific backend layer. A combined response inside a general API is an aggregation endpoint but not automatically a BFF.

### Standardizing one communication mechanism for the entire platform

Standardization reduces operational cost, but forcing one mechanism into incompatible interaction shapes can increase application complexity. Prefer the smallest sufficient set.
