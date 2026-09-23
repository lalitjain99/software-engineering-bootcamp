import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse

app = FastAPI(title="Inventory SSE Service")


DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Inventory SSE Dashboard</title>
    <style>
        body {
            max-width: 720px;
            margin: 40px auto;
            font-family: Arial, sans-serif;
        }
        #connection-status {
            font-weight: bold;
        }
        li {
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <h1>Live Inventory Updates</h1>
    <p>Connection: <span id="connection-status">connecting</span></p>
    <p>This page receives updates without refreshing or sending another GET request.</p>
    <ul id="events"></ul>

    <script>
        const statusElement = document.getElementById("connection-status");
        const eventsElement = document.getElementById("events");
        const eventSource = new EventSource("/inventory/events");

        eventSource.onopen = () => {
            statusElement.textContent = "open";
        };

        eventSource.addEventListener("stock_changed", (event) => {
            const stock = JSON.parse(event.data);
            const item = document.createElement("li");
            item.textContent =
                "Event " + event.lastEventId +
                ": product " + stock.product_id +
                " has " + stock.available + " units";
            eventsElement.prepend(item);
        });

        eventSource.onerror = () => {
            statusElement.textContent = "disconnected — browser will try to reconnect";
        };
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def show_dashboard() -> HTMLResponse:
    return HTMLResponse(DASHBOARD_HTML)


async def generate_stock_events(request: Request) -> AsyncIterator[str]:
    event_id = 1

    while not await request.is_disconnected():
        available_stock = 20 - ((event_id - 1) % 6)
        event_data = {
            "product_id": 101,
            "available": available_stock,
        }

        yield (
            f"id: {event_id}\n"
            "event: stock_changed\n"
            f"data: {json.dumps(event_data)}\n\n"
        )

        event_id += 1
        await asyncio.sleep(2)


@app.get("/inventory/events")
async def stream_inventory_events(request: Request) -> StreamingResponse:
    return StreamingResponse(
        generate_stock_events(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
