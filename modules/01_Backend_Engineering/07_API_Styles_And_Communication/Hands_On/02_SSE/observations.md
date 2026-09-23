# Server-Sent Events Micro-lab Observations

## 1. Who initiated the SSE connection?

A browser or curl client initiated the SSE connection to the server.

## 2. How many HTTP requests did curl make while several events arrived?

Curl made one HTTP request for one event stream. Multiple events arrived through the response to that same request.

## 3. Did the HTTP response finish after the first event?

No. The HTTP response did not finish after the first event. It remained open until the client disconnected, the server closed it, or the network connection failed.

## 4. In which direction did data travel after the connection was opened?

After the connection was opened, event data travelled from the server to the client.

## 5. Could the browser send a stock-change command through the same SSE stream?

No. SSE only sends data from the server to the client. If the browser needs to change the stock, it must make a separate HTTP request such as `POST` or `PATCH`. It cannot send the command through the open SSE response.

A new SSE connection is not required for different kinds of server events. Multiple event types can share one SSE stream.

## 6. What is the purpose of `Content-Type: text/event-stream`?

`Content-Type: text/event-stream` is a response header. It tells the client that the response body is formatted as a Server-Sent Events stream.

## 7. What happened when you pressed `Ctrl+C` or closed the browser tab?

Pressing `Ctrl+C` disconnected the curl client and ended its stream. Closing the browser tab closed that browser's SSE connection.

If the tab remains open but the connection fails, the browser's `EventSource` API normally attempts to reconnect.

## 8. What is the most important difference between SSE and a webhook?

A webhook normally sends an individual HTTP request from one server to another server for an event.

With SSE, the client opens one long-lived HTTP response, and the server sends multiple events through that response.

## 9. Why might an event contain an `id` field?

The `id` uniquely identifies an event. If the SSE connection breaks, the browser can send the last received ID using `Last-Event-ID` while reconnecting.

A server that stores events and supports replay can use that ID to send events the client missed. Our simple lab assigns IDs but does not implement persistent storage or replay.
