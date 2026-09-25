# gRPC Micro-lab Observations

## 1. What contract is defined in `inventory.proto`?

The contract defines the `inventory` package and an `InventoryService` with one unary RPC, `ReserveStock`. The method accepts a `ReserveStockRequest` containing a product ID and quantity, and returns a `ReserveStockResponse` containing whether the reservation succeeded, the remaining quantity, and a message.

## 2. Which two Python files did the compiler generate, and what does each contain?

The compiler generates `inventory_pb2.py` and `inventory_pb2_grpc.py` from `inventory.proto`.

- `inventory_pb2.py` contains generated Protocol Buffer message classes, including `ReserveStockRequest` and `ReserveStockResponse`.
- `inventory_pb2_grpc.py` contains the generated gRPC client stub, server interface, and service-registration code.

## 3. What is the purpose of `InventoryServiceStub`?

`InventoryServiceStub` gives the client a generated interface for calling methods on the remote `InventoryService`. In this lab, the client creates the stub with its gRPC channel and calls `stub.ReserveStock(...)` to send a request and receive a response.

## 4. Why should generated `*_pb2.py` files not be edited manually?

They are compiler outputs derived from `inventory.proto`. Manual changes can be overwritten the next time the files are generated and can make the generated code inconsistent with the contract. Changes should be made to the `.proto` source and regenerated instead.

## 5. What do the field numbers `1` and `2` mean in the request message?

They are the field identifiers used in Protocol Buffer's binary wire format for `product_id` and `quantity`, respectively. They are not default values or positions in a list. The identifiers are part of the serialized contract, so they should be preserved when evolving the message.

## 6. Why is `stub.ReserveStock(...)` still a network operation even though it looks like a local method call?

The generated stub serializes the request into Protocol Buffer bytes, sends it through a gRPC channel over HTTP/2 to the server, and waits for a response to deserialize. The server then dispatches the RPC to the `ReserveStock` implementation. The method syntax is local-looking, but the work depends on a remote process and network availability.

## 7. What happened when the server was stopped?

The client could still construct the stub and request, but there was no server listening at `127.0.0.1:50051` to handle the call. The RPC failed with the gRPC status `UNAVAILABLE`. This demonstrates that an RPC can fail independently of whether the client-side method exists.

## 8. What was the difference between `reserved: False` and the `NOT_FOUND` status?

`reserved: False` with the message `Insufficient stock` was a valid response: the RPC completed successfully, but the business operation could not reserve the requested amount. `NOT_FOUND` was instead a gRPC error status used when the requested product ID did not exist. The former is a business outcome in a normal response; the latter indicates the RPC ended with an error.

## 9. Why did the client include a timeout?

The client set a three-second deadline so it would not wait indefinitely if the server or network failed to respond. Remote calls can be delayed or unavailable, so deadlines help bound how long the caller waits. The client also catches `grpc.RpcError` and reports the status and details.

## 10. When might gRPC be a better fit than REST or GraphQL?

gRPC can be a good fit for controlled service-to-service communication when teams want a strongly defined `.proto` contract, generated client and server code, compact Protocol Buffer messages, and RPC calls over HTTP/2. REST may be simpler for resource-oriented APIs with straightforward HTTP semantics, while GraphQL may fit clients that need flexible selection of connected data. The best choice depends on client needs, interoperability, tooling, and operational requirements.
