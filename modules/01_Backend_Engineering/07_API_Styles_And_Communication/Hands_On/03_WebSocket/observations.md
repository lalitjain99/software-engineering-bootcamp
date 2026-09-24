Who initiated the WebSocket connection?
Ans a http client e.g. curl initiate a websocket connection
What happened during the initial HTTP handshake?
Ans: After the initial handshake connection is upgraded to Websocket
After the connection was established, did each message create a new HTTP request?
Ans: No, once the connection is established no new HTTP request is required. Connection is upgraded to Websocket which setup a two way communication using websockt framework
Which messages travelled from server to client?
Ans: message starting with server travelled from server to client. for example Server  → {"type": "scan_acknowledged", "available": 18}
Which message travelled from client to server?
Ans: message starting with client/rowser travelled from client to server . for example Browser → {"type": "scan", "quantity": 2}
Why could the scanner command use the same WebSocket connection but not the SSE stream?
Ans Websocket is a two way connection i.e. message can be sent from either direction without starting a new HTTP connection while in SSE server send the message based on some event over same connection. Scanner commands need to intiate a new request in case of SSE
What happened when the Uvicorn server stopped?
Ans: Websocket connection will break. Neither client nor server can send the message
Who is responsible for reconnecting a WebSocket client?
Ans: Since client is responsible for initial HTTP handshake so client is responsible for reconnecting a websocket client
When would SSE be simpler than WebSocket?
Ans Server-Sent Events (SSE) are simpler than WebSockets whenever your application architecture only requires one-way communication (server-to-client).   Because SSE rides on top of standard HTTP rather than establishing a completely separate protocol layer (like WebSockets do with TCP handshakes), it eliminates a significant amount of boilerplate code and infrastructure complexity. 
Explain the most important difference between WebSocket and webhook.
Ans: WebSocket is like live streaming of message  where both client and server can exchange message without making a new Http conection after initial handshake while webhook is a event based message communication when server turn into a client after the event has occured. Each http request server a single event 