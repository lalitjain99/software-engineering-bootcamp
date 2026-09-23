# Micro-lab 03 — WebSocket

## Learning goal

Observe a browser and a server sending messages in **both directions over the same persistent connection**.

Do not try to master the asynchronous implementation yet. Focus on the visible communication behaviour.

## Scenario

A warehouse screen needs to:

- Receive current stock information from the server.
- Send barcode-scan events to the server.
- Receive acknowledgements immediately.

With SSE, the warehouse screen could receive stock updates, but it could not send scanner events through the same stream. WebSocket provides a two-way channel.

## The connection flow

1. The browser starts an HTTP-based WebSocket handshake.
2. The server accepts the upgrade.
3. The connection becomes a WebSocket connection.
4. The server sends stock snapshots periodically.
5. The browser sends scan messages when you click the button.
6. The server sends acknowledgements over the same connection.

After the handshake, these messages are WebSocket messages—not separate HTTP requests.

| Question | Answer |
|---|---|
| Who initiates the connection? | The browser |
| Initial handshake | HTTP upgrade request |
| Successful handshake status | `101 Switching Protocols` |
| Ongoing direction | Client ↔ server |
| Connection lifetime | Remains open until one side or the network closes it |
| New HTTP request per message? | No |

## 1. Start the WebSocket service

From the repository root, run this as one line in Windows Command Prompt:

```cmd
uv run uvicorn warehouse_service:app --app-dir modules/01_Backend_Engineering/07_API_Styles_And_Communication/Hands_On/03_WebSocket --host 127.0.0.1 --port 8000
```

## 2. Open the warehouse screen

Open:

[http://127.0.0.1:8000](http://127.0.0.1:8000)

Wait without clicking anything. The server sends a `stock_snapshot` message every three seconds.

This proves that the server can send a message without waiting for a new HTTP request.

## 3. Send a scanner message

Enter a quantity and click **Send scan**.

The browser sends a message similar to:

```json
{
  "type": "scan",
  "product_id": 101,
  "quantity": 2
}
```

The server updates the stock for this demonstration and sends an acknowledgement:

```json
{
  "type": "scan_acknowledged",
  "product_id": 101,
  "removed": 2,
  "available": 18
}
```

Both messages use the same WebSocket connection.

## 4. Inspect the connection

Open the browser developer tools:

1. Select the **Network** tab.
2. Filter by **WS**.
3. Select the `/ws/inventory` connection.
4. Open the **Messages** view.

Observe:

- One WebSocket connection remains open.
- Server `stock_snapshot` messages travel toward the browser.
- Browser `scan` messages travel toward the server.
- Server acknowledgements return through the same connection.
- Clicking **Send scan** does not create a new HTTP request.

## 5. Test disconnection

Stop the Uvicorn server.

The page shows that the WebSocket connection is closed. Unlike the browser `EventSource` API used for SSE, the browser WebSocket API does not automatically provide a complete reconnection strategy. The application must decide when and how to reconnect and recover missed messages.

Restart the server and refresh the browser page to connect again.

## SSE versus WebSocket

| Characteristic | SSE | WebSocket |
|---|---|---|
| Connection begins from | Client | Client |
| Ongoing direction | Server → client | Client ↔ server |
| Underlying interaction | Long-lived HTTP response | HTTP handshake, then WebSocket protocol |
| Client sends commands on same channel | No | Yes |
| Browser API | `EventSource` | `WebSocket` |
| Automatic browser reconnection | Built into `EventSource` behaviour | Application must implement it |
| Natural fit | Notifications, progress and live feeds | Chat, collaboration, games and interactive control |

## WebSocket versus webhook

| Characteristic | WebSocket | Webhook |
|---|---|---|
| Connection | Persistent | Separate HTTP delivery |
| Direction | Both sides can send | Event producer sends to receiver |
| Typical participants | Interactive client and server | Server and another server |
| Receiver unavailable | Connection/reconnection problem | Delivery/retry problem |

## What the code is doing

The service keeps one pending receive operation while periodically sending stock snapshots. When it receives a scan message, it validates the basic fields, changes the demonstration stock value and sends an acknowledgement.

The `asyncio` coordination is supporting code for the lab. Event-loop and task internals belong to a later roadmap topic.

## Intentional limitations

Each browser connection has its own in-memory stock value. This keeps the lab focused, but it is not a production inventory design.

The lab does not yet implement:

- Authentication or authorization
- Input schemas and a versioned message contract
- Persistent stock storage
- Shared state across connections or server instances
- Reconnection and missed-message recovery
- Heartbeats, idle timeouts or stale-connection cleanup
- Backpressure for slow clients
- Cross-instance message broadcasting

## Create your observations

Create `observations.md` in this folder and answer:

1. Who initiated the WebSocket connection?
2. What happened during the initial HTTP handshake?
3. After the connection was established, did each message create a new HTTP request?
4. Which messages travelled from server to client?
5. Which message travelled from client to server?
6. Why could the scanner command use the same WebSocket connection but not the SSE stream?
7. What happened when the Uvicorn server stopped?
8. Who is responsible for reconnecting a WebSocket client?
9. When would SSE be simpler than WebSocket?
10. Explain the most important difference between WebSocket and webhook.

Write what you observed rather than searching for polished definitions.
