1. Who initiated the SSE connection?
Ans: a browser or curl client initiates a SSE connection
2. How many HTTP requests did curl make while several events arrived?
Ans: One request for the one event stream
3. Did the HTTP response finish after the first event?
Ans: No , HTTP reponse does not finish after first event. it only close when client or server or network is closed
4. In which direction did data travel after the connection was opened?
Ans: Data travels from server to client 
5. Could the browser send a stock-change command through the same SSE stream?
Ans: No. SSE only sends data from server to client. If the browser needs to change the stock, it must make a separate HTTP request such as POST or PATCH. It cannot send the command through the open SSE response.

A new SSE connection is not required. Different kinds of server events can share the same stream.

6. What is the purpose of `Content-Type: text/event-stream`?
Ans: Content-Type: text/event-stream is a response header that tells the client that the response body is formatted as an SSE event stream.
7. What happened when you pressed `Ctrl+C` or closed the browser tab?
Ans: It will end the connect and stream will be ended
8. Explain the most important difference between SSE and a webhook.
Ans: A webhook normally sends an individual HTTP request from one server to another server for an event. With SSE, the client opens one long-lived HTTP response, and the server sends multiple events through that response.
9. Why might an event contain an `id` field?
Ans The id uniquely identifies an event. If the SSE connection breaks, the browser can send the last received ID using the Last-Event-ID header while reconnecting. The server can then replay events that the client missed.