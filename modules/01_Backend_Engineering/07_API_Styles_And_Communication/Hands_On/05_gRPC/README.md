# Micro-lab 05 — gRPC

## Learning goal

See how a client calls a strongly defined remote service method using generated Python code.

The call will look similar to a local method:

```python
response = stub.ReserveStock(request, timeout=3)
```

But it is still a network operation that can fail, time out or return a remote status code.

## Scenario

An Order Service needs the Inventory Service to reserve two units of product `101`.

Instead of designing a resource URL such as:

```http
POST /products/101/reservations
```

the gRPC contract exposes a service method:

```text
InventoryService.ReserveStock(
    product_id=101,
    quantity=2
)
```

## Files in this lab

| File | Responsibility |
|---|---|
| `inventory.proto` | Language-neutral service and message contract |
| `server.py` | Implements the generated server interface |
| `client.py` | Calls the remote service through a generated stub |
| `inventory_pb2.py` | Generated Protocol Buffer message classes |
| `inventory_pb2_grpc.py` | Generated client stub and server registration code |

The final two files are generated locally. Do not edit them manually.

## 1. Synchronize the root environment

The root `pyproject.toml` now includes `grpcio` and `grpcio-tools`.

From the repository root:

```cmd
uv sync
```

This will refresh your local `uv.lock`. Include that updated lock file in your next push.

## 2. Enter the lab directory

From the repository root in Windows Command Prompt:

```cmd
cd modules/01_Backend_Engineering/07_API_Styles_And_Communication/Hands_On/05_gRPC
```

## 3. Generate Python code from the contract

Run:

```cmd
uv run python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. inventory.proto
```

This reads `inventory.proto` and generates:

```text
inventory_pb2.py
inventory_pb2_grpc.py
```

`inventory_pb2.py` contains message classes such as `ReserveStockRequest` and `ReserveStockResponse`.

`inventory_pb2_grpc.py` contains:

- `InventoryServiceStub` for the client
- `InventoryServiceServicer` for the server implementation
- Registration code connecting the service implementation to the gRPC server

These generated files are ignored by this lab's `.gitignore` because they can be reproduced from the contract.

## 4. Read the contract before the implementation

Open `inventory.proto`:

```proto
service InventoryService {
  rpc ReserveStock(ReserveStockRequest) returns (ReserveStockResponse);
}
```

This declares:

- Service: `InventoryService`
- Remote method: `ReserveStock`
- Request type: `ReserveStockRequest`
- Response type: `ReserveStockResponse`

The request message is:

```proto
message ReserveStockRequest {
  int64 product_id = 1;
  int32 quantity = 2;
}
```

The numbers `1` and `2` identify fields in the binary wire format. They are not default values or array positions.

## 5. Start the gRPC server

Open terminal 1 in the lab directory:

```cmd
uv run python server.py
```

Expected output:

```text
Inventory gRPC server listening on 127.0.0.1:50051
```

Port `50051` identifies the gRPC server application, just as port `8000` identified Uvicorn in earlier labs.

The lab uses `add_insecure_port` because it runs only on localhost. Production traffic normally requires appropriate transport security and authentication.

## 6. Make a successful remote call

Open terminal 2 in the same lab directory:

```cmd
uv run python client.py 101 2
```

Expected client output:

```text
Calling remote method: ReserveStock(product_id=101, quantity=2)
RPC succeeded
reserved: True
remaining_quantity: 8
message: Stock reserved
```

Observe terminal 1. The server logs that it received `ReserveStock`.

Although this looks like a Python method call, the generated stub:

1. Serializes the request into Protocol Buffer binary bytes.
2. Sends an RPC over the gRPC channel using HTTP/2.
3. Waits for the remote server.
4. Deserializes the response into a generated Python object.

## 7. Observe a business rejection

Run:

```cmd
uv run python client.py 101 100
```

The RPC itself succeeds, but the response contains:

```text
reserved: False
message: Insufficient stock
```

This is a valid business outcome, not a transport failure.

## 8. Observe gRPC status errors

Unknown product:

```cmd
uv run python client.py 999 1
```

Expected status:

```text
status: NOT_FOUND
```

Invalid quantity:

```cmd
uv run python client.py 101 0
```

Expected status:

```text
status: INVALID_ARGUMENT
```

gRPC uses its own status-code model rather than returning an HTTP `404` or `422` directly to the application client.

## 9. Prove that this is a network operation

Stop the server in terminal 1 and call:

```cmd
uv run python client.py 101 1
```

The generated Python method still exists, but the call fails because no server is listening:

```text
RPC failed
status: UNAVAILABLE
```

This is why a Technical Lead must not treat an RPC like an ordinary local function call. Remote calls need deadlines, error handling and careful retry decisions.

## Complete flow

```text
client.py
   ↓ creates ReserveStockRequest
generated client stub
   ↓ serializes Protocol Buffer bytes
gRPC channel over HTTP/2
   ↓ network call to 127.0.0.1:50051
generated server registration
   ↓ dispatches ReserveStock
server.py implementation
   ↓ returns ReserveStockResponse
generated code
   ↓ serializes response bytes
client stub
   ↓ returns a Python response object
client.py
```

## REST, GraphQL and gRPC comparison

| Characteristic | REST-style HTTP | GraphQL | gRPC |
|---|---|---|---|
| API model | Resources and HTTP semantics | Typed graph and client-selected fields | Services and remote methods |
| Contract | Paths, methods and representation schema | GraphQL schema | `.proto` service and messages |
| Typical payload | JSON | GraphQL document and usually JSON result | Protocol Buffer binary messages |
| Client code | HTTP client or generated SDK | GraphQL client or HTTP client | Generated stub |
| Common fit | Public/resource APIs | Flexible connected client data | Controlled internal service-to-service calls |
| Human inspection | Easy with curl/Postman | Easy with GraphiQL | Requires gRPC-aware tooling |
| Transport in these labs | HTTP/1.1 | HTTP | HTTP/2-based gRPC channel |

## Intentional limitations

This lab implements only one unary RPC: one request followed by one response.

It does not yet implement:

- TLS or mutual TLS
- Authentication and metadata
- Client, server or bidirectional streaming
- Interceptors
- Retries
- Health checking or reflection
- Load balancing
- Persistent database transactions
- Multi-instance stock consistency
- Advanced Protocol Buffer compatibility rules

The server uses a worker thread pool. Threads and concurrency will be covered later in the roadmap.

## Create your observations

Create `observations.md` in this folder and answer:

1. What contract is defined in `inventory.proto`?
2. Which two Python files did the compiler generate, and what does each contain?
3. What is the purpose of `InventoryServiceStub`?
4. Why should generated `*_pb2.py` files not be edited manually?
5. What do the field numbers `1` and `2` mean in the request message?
6. Why is `stub.ReserveStock(...)` still a network operation even though it looks like a local method call?
7. What happened when the server was stopped?
8. What was the difference between `reserved: False` and the `NOT_FOUND` status?
9. Why did the client include a timeout?
10. When might gRPC be a better fit than REST or GraphQL?

Write what you observed. Do not copy generated code into your answers.
