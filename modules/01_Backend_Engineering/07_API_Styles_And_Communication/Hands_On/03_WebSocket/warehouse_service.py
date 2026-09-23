import asyncio
from contextlib import suppress

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI(title="Warehouse WebSocket Service")


WAREHOUSE_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Warehouse WebSocket Screen</title>
    <style>
        body {
            max-width: 760px;
            margin: 40px auto;
            font-family: Arial, sans-serif;
        }
        #connection-status {
            font-weight: bold;
        }
        input, button {
            padding: 8px;
        }
        li {
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <h1>Warehouse Scanner</h1>
    <p>Connection: <span id="connection-status">connecting</span></p>

    <label>
        Quantity:
        <input id="quantity" type="number" value="1" min="1">
    </label>
    <button id="send-scan">Send scan</button>

    <h2>Messages</h2>
    <ul id="messages"></ul>

    <script>
        const statusElement = document.getElementById("connection-status");
        const messagesElement = document.getElementById("messages");
        const sendButton = document.getElementById("send-scan");
        const quantityInput = document.getElementById("quantity");

        const websocketProtocol =
            window.location.protocol === "https:" ? "wss" : "ws";
        const socket = new WebSocket(
            websocketProtocol + "://" + window.location.host + "/ws/inventory"
        );

        function addMessage(direction, message) {
            const item = document.createElement("li");
            item.textContent = direction + ": " + JSON.stringify(message);
            messagesElement.prepend(item);
        }

        socket.onopen = () => {
            statusElement.textContent = "open";
        };

        socket.onmessage = (event) => {
            addMessage("server → browser", JSON.parse(event.data));
        };

        socket.onclose = () => {
            statusElement.textContent = "closed";
            sendButton.disabled = true;
        };

        socket.onerror = () => {
            statusElement.textContent = "error";
        };

        sendButton.addEventListener("click", () => {
            if (socket.readyState !== WebSocket.OPEN) {
                addMessage("browser", {"error": "WebSocket is not open"});
                return;
            }

            const scanMessage = {
                "type": "scan",
                "product_id": 101,
                "quantity": Number(quantityInput.value)
            };

            socket.send(JSON.stringify(scanMessage));
            addMessage("browser → server", scanMessage);
        });
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def show_warehouse_screen() -> HTMLResponse:
    return HTMLResponse(WAREHOUSE_HTML)


async def run_inventory_session(websocket: WebSocket) -> None:
    available_stock = 20
    receive_task = asyncio.create_task(websocket.receive_json())

    try:
        while True:
            completed, _ = await asyncio.wait(
                {receive_task},
                timeout=3,
            )

            if not completed:
                await websocket.send_json(
                    {
                        "type": "stock_snapshot",
                        "product_id": 101,
                        "available": available_stock,
                    }
                )
                continue

            message = receive_task.result()
            receive_task = asyncio.create_task(websocket.receive_json())

            if message.get("type") != "scan":
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Unsupported message type",
                    }
                )
                continue

            product_id = message.get("product_id")
            quantity = message.get("quantity")

            if (
                not isinstance(product_id, int)
                or not isinstance(quantity, int)
                or quantity <= 0
            ):
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "product_id and positive quantity are required",
                    }
                )
                continue

            if quantity > available_stock:
                await websocket.send_json(
                    {
                        "type": "scan_rejected",
                        "product_id": product_id,
                        "requested": quantity,
                        "available": available_stock,
                    }
                )
                continue

            available_stock -= quantity
            await websocket.send_json(
                {
                    "type": "scan_acknowledged",
                    "product_id": product_id,
                    "removed": quantity,
                    "available": available_stock,
                }
            )
    finally:
        if not receive_task.done():
            receive_task.cancel()
            with suppress(asyncio.CancelledError):
                await receive_task


@app.websocket("/ws/inventory")
async def inventory_websocket(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        await run_inventory_session(websocket)
    except WebSocketDisconnect:
        print("Warehouse client disconnected")
