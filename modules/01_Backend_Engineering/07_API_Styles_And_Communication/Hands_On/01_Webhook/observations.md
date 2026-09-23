## 1. Who initiated the original product-creation request?

Ans: Using curl user initiated the product creation request to the server hosted at 8000 port

## 2. During webhook delivery, which application became the HTTP client?
Ans During the webhook delivery product_service became the http client

## 3. Why is this different from the Supplier Service polling `GET /products` repeatedly?
Ans: in polling mechanism a service continously poll at particular endpoint or service whether it send a event or not while in this case the service it self notifying the supplier service the a product create event has occured
## 4. What happened when the Supplier Service was unavailable?
Ans: Product service will execute its product create logic and product will be created but webhook delivery will fail.

## 5. Why might production webhook delivery need retries?
Ans: It need retries as webhook delivery server might be temporarily not working.

## 6. If a retry delivers the same event twice, what problem could that create?
Ans: It may take the same action twice. for example in food delivery app if a customer click order button and subsequent service was not available and on retry same order can be placed twice
## 7. Why would the Supplier Service need to verify a signature before trusting the event?
Ans: It has to now the it has come from the right source like in HTTP API calls. Server needs to first confirm the valid client similarly here supplier service need to know that it had come from the right product service