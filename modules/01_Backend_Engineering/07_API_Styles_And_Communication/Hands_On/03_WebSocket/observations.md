# WebSocket Micro-lab Observations

## 1. Who initiated the WebSocket connection?

The browser created a WebSocket connection to `ws://127.0.0.1:8000/ws/inventory`. More generally, any WebSocket-capable client can initiate the connection.

## 2. What happened during the initial HTTP handshake?

The browser sent an HTTP upgrade request. Uvicorn accepted it with `101 Switching Protocols`.

The same underlying TCP connection remained open, but communication switched from HTTP request-response messages to WebSocket frames.

## 3. After the connection was established, did each message create a new HTTP request?

No. After the connection was upgraded, messages travelled as WebSocket frames over the same underlying TCP connection. A new HTTP request was not created for every message.

## 4. Which messages travelled from server to client?

The lab sent the following message types from the server to the browser:

- `stock_snapshot`
- `scan_acknowledged`
- `scan_rejected`
- `error`

For example:

```json
{
  "type": "scan_acknowledged",
  "product_id": 101,
  "available": 18
}
```

The periodic `stock_snapshot` also demonstrated that the server could send a message without waiting for a new client request.

## 5. Which message travelled from client to server?

The browser sent the `scan` message to the server:

```json
{
  "type": "scan",
  "product_id": 101,
  "quantity": 2
}
```

## 6. Why could the scanner command use the same WebSocket connection but not the SSE stream?

WebSocket supports two-way communication, so either side can send messages over the established connection.

SSE is one-way from server to client. Therefore, with SSE the browser would need to send the scanner command through a separate HTTP request such as `POST` or `PATCH`. It would not need another SSE connection.

## 7. What happened when the Uvicorn server stopped?

The WebSocket connection broke. Neither the client nor the server could continue sending messages through that connection.

The browser detected that the connection had closed.

## 8. Who is responsible for reconnecting a WebSocket client?

The client application must implement WebSocket reconnection logic.

Unlike the browser's SSE `EventSource` API, the browser WebSocket API does not automatically provide a complete reconnection and missed-message recovery strategy.

## 9. When would SSE be simpler than WebSocket?

SSE is simpler when the application only requires server-to-client updates.

It remains an HTTP response, uses a standard text event format, and the browser's `EventSource` API provides reconnection behaviour. WebSocket requires a protocol upgrade, a two-way application message contract, and application-managed reconnection.

## 10. What is the most important difference between WebSocket and webhook?

WebSocket maintains a persistent two-way connection through which the client and server can exchange many messages.

A webhook is a server-to-server event notification delivered through a separate HTTP request for each event or batch. During delivery, the event producer temporarily acts as the HTTP client.
