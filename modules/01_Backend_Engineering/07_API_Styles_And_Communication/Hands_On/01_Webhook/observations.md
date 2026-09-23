# Webhook Micro-lab Observations

## 1. Who initiated the original product-creation request?

The user initiated the product-creation request using `curl`. In this request, `curl` was the HTTP client and the Product Service running on port `8000` was the HTTP server.

## 2. During webhook delivery, which application became the HTTP client?

During webhook delivery, the Product Service became the HTTP client. It sent an HTTP `POST` request to the Supplier Service running on port `8001`.

## 3. Why is this different from the Supplier Service polling `GET /products` repeatedly?

With polling, the Supplier Service would repeatedly ask the Product Service whether any product data had changed, including times when there was nothing new.

With a webhook, the Product Service sends a notification to the Supplier Service only after the `product.created` event occurs.

## 4. What happened when the Supplier Service was unavailable?

The Product Service still executed its product-creation logic, so the product was created. The webhook delivery failed because the Supplier Service was unavailable.

This behaviour is specific to our implementation: product creation and webhook delivery were treated as separate outcomes.

## 5. Why might production webhook delivery need retries?

The receiver may be temporarily unavailable because of a network failure, timeout, deployment, overload, or other temporary server problem. Retrying later gives the event another opportunity to reach the receiver.

A production system should define which failures are retryable, how often to retry, and when to stop.

## 6. If a retry delivers the same event twice, what problem could that create?

The receiver might perform the same business action twice.

For example, the Supplier Service could successfully process a product-created event, but its acknowledgement might be lost. The Product Service could then retry the same event, causing inventory to be updated or a notification to be sent twice.

The receiver should therefore process events idempotently. It can use the `event_id` to recognize an event it has already processed.

## 7. Why would the Supplier Service need to verify a signature before trusting the event?

The Supplier Service needs to confirm that:

- The event came from the expected Product Service (**authenticity**).
- The event payload was not changed after it was sent (**integrity**).

A valid webhook signature helps provide these checks. It does not encrypt the payload; HTTPS protects the payload while it travels across the network.
