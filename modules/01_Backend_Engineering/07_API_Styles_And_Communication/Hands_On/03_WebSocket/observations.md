Who initiated the WebSocket connection?
Ans The browser created a WebSocket connection to ws://127.0.0.1:8000/ws/inventory. More generally, any WebSocket-capable client can initiate it.

What happened during the initial HTTP handshake?
Ans: After the initial handshake, The browser sent an HTTP upgrade request. Uvicorn accepted it with 101 Switching Protocols. The same underlying TCP connection remained open, but communication switched from HTTP messages to WebSocket frames.

After the connection was established, did each message create a new HTTP request?
Ans: No, once the connection is established no new HTTP request is required. Connection is upgraded to Websocket which setup a two way communication using websockt protocol

Which messages travelled from server to client?
Ans: message starting with server travelled from server to client. for example Server  → {"type": "scan_acknowledged", "available": 18}
Which message travelled from client to server?
Ans: message starting with client/rowser travelled from client to server . for example Browser → {"type": "scan", "quantity": 2}

Why could the scanner command use the same WebSocket connection but not the SSE stream?
Ans Websocket is a two way connection i.e. message can be sent from either direction without starting a new HTTP connection while in SSE is one-way from server to client. Therefore, the scanner would need a separate POST or PATCH HTTP request. It would not need another SSE connection.

What happened when the Uvicorn server stopped?
Ans: Websocket connection will break. Neither client nor server can send the message

Who is responsible for reconnecting a WebSocket client?
Ans: The client application must implement WebSocket reconnection logic. Unlike the browser’s SSE EventSource, the browser WebSocket API does not automatically provide a complete reconnection and missed-message recovery strategy.

When would SSE be simpler than WebSocket?
Ans SSE is simpler when only server-to-client updates are required. It remains an HTTP response, has a standard text event format, and the browser’s EventSource API provides reconnection behavior. WebSocket requires a protocol upgrade, a two-way message contract, and application-managed reconnection.

Explain the most important difference between WebSocket and webhook.
Ans: WebSocket maintains a persistent two-way connection where the client and server can exchange many messages. A webhook is a server-to-server event notification delivered through a separate HTTP request for each event or batch. The event producer temporarily acts as the HTTP client during delivery.