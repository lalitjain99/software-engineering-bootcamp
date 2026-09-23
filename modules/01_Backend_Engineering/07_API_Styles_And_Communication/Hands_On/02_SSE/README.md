# Micro-lab 02 — Server-Sent Events (SSE)

## Learning goal

Observe one client opening **one HTTP request** and receiving multiple server updates through the response over time.

Do not focus on the `async` implementation yet. For this exercise, focus on:

1. Who opens the connection?
2. Which direction do events travel?
3. Does the response finish after the first event?
4. How is this different from a webhook?

## Scenario

A browser dashboard needs continuously updated inventory levels. The browser does not need to send messages over this live channel.

The browser opens:

```http
GET /inventory/events HTTP/1.1
Accept: text/event-stream
```

The Inventory Service keeps that response open and writes a new event every two seconds.

## The communication flow

| Question | Answer |
|---|---|
| Who initiates the connection? | The browser or `curl` client |
| Who sends the ongoing events? | The Inventory Service |
| Direction after connection opens | Server → client |
| Number of HTTP requests | One request for the event stream |
| Response lifetime | Remains open until the client, server, or network closes it |

This is still HTTP. Unlike an ordinary REST response, the response body arrives gradually instead of being completed immediately.

## 1. Start the Inventory Service

From the repository root, run this as one line in Windows Command Prompt:

```cmd
uv run uvicorn inventory_service:app --app-dir modules/01_Backend_Engineering/07_API_Styles_And_Communication/Hands_On/02_SSE --host 127.0.0.1 --port 8000
```

## 2. Observe SSE in a browser

Open:

[http://127.0.0.1:8000](http://127.0.0.1:8000)

The page creates a browser `EventSource` connected to `/inventory/events`. A new stock event should appear every two seconds without refreshing the page.

Open the browser developer tools and inspect the Network tab:

- The `/inventory/events` request remains open.
- Its response has `Content-Type: text/event-stream`.
- Several events arrive through that one response.

## 3. Observe the raw event stream

Open another Windows Command Prompt and run:

```cmd
curl.exe -N -i http://127.0.0.1:8000/inventory/events
```

`-N` tells curl not to buffer the received output.

You should first see one HTTP response:

```http
HTTP/1.1 200 OK
content-type: text/event-stream; charset=utf-8
```

Then events continue to arrive:

```text
id: 1
event: stock_changed
data: {"product_id": 101, "available": 20}

id: 2
event: stock_changed
data: {"product_id": 101, "available": 19}
```

The blank line after each `data` line marks the end of that event.

Press `Ctrl+C` to disconnect the curl client.

## 4. Understand the implementation

The endpoint returns `StreamingResponse` instead of an ordinary JSON response.

The event generator:

1. Formats an event as SSE text.
2. Yields it into the open response.
3. Waits for two seconds.
4. Yields the next event.
5. Stops when the client disconnects.

The important observation is that the client does **not** send a new GET request for every update.

## 5. Compare SSE with the webhook lab

| Characteristic | Webhook | SSE |
|---|---|---|
| Typical participants | Server → another server | Server → connected client/browser |
| Who initiates communication? | Subscriber first provides an endpoint; producer later initiates each delivery | Client opens the event-stream request |
| Connection | Separate HTTP delivery for an event | One long-lived HTTP response |
| Number of events per response | Usually one event or batch | Many events |
| Ongoing direction | Producer → receiver | Server → client |
| Receiver unavailable/disconnected | Sender may retry later | Client reconnects and may need missed-event recovery |

## Intentional limitations

This lab generates sample inventory values independently for each connection. It does not yet implement:

- Database-backed stock changes
- Broadcasting the same event to every connected client
- Persistent event IDs
- Replaying missed events with `Last-Event-ID`
- Authentication
- Proxy timeout configuration
- Multi-instance deployment

Those are production concerns. First understand the connection shape.

## Create your observations

Create `observations.md` in this folder and answer:

1. Who initiated the SSE connection?
2. How many HTTP requests did curl make while several events arrived?
3. Did the HTTP response finish after the first event?
4. In which direction did data travel after the connection was opened?
5. Could the browser send a stock-change command through the same SSE stream?
6. What is the purpose of `Content-Type: text/event-stream`?
7. What happened when you pressed `Ctrl+C` or closed the browser tab?
8. Explain the most important difference between SSE and a webhook.
9. Why might an event contain an `id` field?

Write what you observed rather than searching for polished definitions.
