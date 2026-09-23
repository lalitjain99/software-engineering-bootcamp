# Micro-lab 01 — See a Webhook Working

## Learning goal

See a webhook as an ordinary HTTP request sent **from one server to another server after an event occurs**.

We will run two FastAPI applications:

| Application | Port | Role |
|---|---:|---|
| Product Service | 8000 | Creates a product and sends the webhook |
| Supplier Service | 8001 | Exposes an endpoint that receives the webhook |

The Product Service is normally a server for the original caller. During webhook delivery, it also becomes an HTTP client.

## The complete flow

1. You act as a client and send `POST /products` to the Product Service.
2. The Product Service creates the product.
3. The Product Service creates a `product.created` event.
4. The Product Service sends an HTTP `POST` request to the Supplier Service.
5. The Supplier Service stores the received event and returns `204 No Content`.
6. The Product Service returns `201 Created` to you.

There are **two separate HTTP requests**:

| Request | HTTP client | HTTP server |
|---|---|---|
| Create the product | You/Postman/curl | Product Service |
| Deliver the webhook | Product Service | Supplier Service |

## Why this version is intentionally simple

The Product Service waits for the webhook attempt to finish so the sequence is easy to observe. This is a learning implementation, not a production delivery design.

It does not yet implement:

- Background workers or message queues
- Automatic retries
- Webhook signatures
- Duplicate-event handling
- Persistent delivery records

Do not solve those problems yet. First make the direction of communication clear.

## 1. Prepare the root environment

From the repository root:

```bash
uv sync
```

This exercise uses only dependencies already managed by the root project.

## 2. Start the Supplier Service

Open terminal 1 at the repository root:

```bash
uv run uvicorn supplier_receiver:app   --app-dir modules/01_Backend_Engineering/07_API_Styles_And_Communication/Hands_On/01_Webhook   --host 127.0.0.1   --port 8001
```

This server is now waiting for webhook deliveries at:

```text
POST http://127.0.0.1:8001/webhooks/product-created
```

## 3. Start the Product Service

Open terminal 2 at the repository root:

```bash
uv run uvicorn product_service:app   --app-dir modules/01_Backend_Engineering/07_API_Styles_And_Communication/Hands_On/01_Webhook   --host 127.0.0.1   --port 8000
```

## 4. Create a product

Use Postman or run:

```bash
curl -i -X POST http://127.0.0.1:8000/products   -H "Content-Type: application/json"   -d '{"name":"Keyboard","price":2500}'
```

Expected status:

```http
HTTP/1.1 201 Created
```

The response should show that the product was created and the webhook was delivered:

```json
{
  "product": {
    "product_id": 101,
    "name": "Keyboard",
    "price": 2500.0
  },
  "webhook_delivery": {
    "status": "delivered",
    "receiver_status_code": 204
  }
}
```

Look at terminal 1. The Supplier Service prints the event that it received.

You can also inspect all events received since the Supplier Service started:

```bash
curl -i http://127.0.0.1:8001/received-events
```

## 5. Observe a delivery failure

1. Stop only the Supplier Service on port 8001.
2. Send another `POST /products` request to port 8000.
3. Inspect the Product Service response.

The product is still created, but `webhook_delivery.status` is `failed`. This exposes the first production-design question:

> What should the sender do when the receiver is temporarily unavailable?

We will answer it later with delivery records, retries, idempotency, and queues.

## Create your observations

Create `observations.md` in this folder and answer in your own words:

1. Who initiated the original product-creation request?
2. During webhook delivery, which application became the HTTP client?
3. Why is this different from the Supplier Service polling `GET /products` repeatedly?
4. What happened when the Supplier Service was unavailable?
5. Why might production webhook delivery need retries?
6. If a retry delivers the same event twice, what problem could that create?
7. Why would the Supplier Service need to verify a signature before trusting the event?

Do not search for polished definitions. Describe what you actually observed.
