# Interview Review — Sending Input to an API

> Completed interactively on 2026-09-07. These model answers combine the original answers with the refinements identified during review.

## How to Use This File

1. Answer each question aloud before opening the model answer.
2. Keep direct answers under 30–60 seconds.
3. For design scenarios, explain the meaning of each input before choosing its location.
4. Use the common-mistakes section for quick revision.

---

## 🟢 Beginner

### 1. Where should these inputs go when creating a product inside a store?

- `store_id`
- Product details such as `name`, `category`, and `price`
- Optional `notify_supplier` behaviour

<details>
<summary>Show model answer</summary>

I would place `store_id` in the path because it identifies the store under which the product will be created. The product fields belong in the request body because they collectively describe the structured resource being created. I would use `notify_supplier` as an optional query parameter because it modifies the operation's behaviour but is not part of the product itself.

```http
POST /stores/7/products?notify_supplier=true
```

```json
{
  "name": "Keyboard",
  "category": "electronics",
  "price": 2500
}
```

</details>

### 2. What is the difference between these requests?

```http
GET /products/101
GET /products?id=101
```

<details>
<summary>Show model answer</summary>

`GET /products/101` treats product 101 as the specific resource being addressed. I would use it when retrieving one known product.

`GET /products?id=101` treats `id=101` as a filter applied to the products collection. This style fits an endpoint that supports one or more filtering conditions and may return a collection.

</details>

### 3. Are query parameters always optional?

<details>
<summary>Show model answer</summary>

No. A query parameter without a default value is required:

```python
def search_products(search: str):
    ...
```

A default value allows the client to omit it:

```python
def list_products(limit: int = 10):
    ...
```

A parameter can also explicitly allow `None` when omitted:

```python
def list_products(category: str | None = None):
    ...
```

Input location and requiredness are separate decisions.

</details>

---

## 🟡 Intermediate

### 4. How does FastAPI determine where each parameter comes from?

```python
@app.post("/stores/{store_id}/products")
def create_product(
    store_id: int,
    product: ProductCreate,
    notify_supplier: bool = False,
):
    ...
```

<details>
<summary>Show model answer</summary>

FastAPI treats `store_id` as a path parameter because its name appears inside `{store_id}` in the route.

It treats `product` as the request body because `ProductCreate` is a Pydantic model.

It treats `notify_supplier` as a query parameter because it is a simple typed value that is not present in the path. Its default value of `False` makes it optional.

</details>

### 5. What fails validation in each request, and does the function execute?

```http
GET /stores/abc/products/101
GET /stores/7/products?max_price=cheap
```

```http
POST /stores/7/products
```

```json
{
  "name": "Keyboard",
  "category": "electronics"
}
```

<details>
<summary>Show model answer</summary>

| Request | Failed location | Reason | Function executes? |
|---|---|---|:---:|
| `/stores/abc/products/101` | Path | `store_id` cannot be converted to `int` | No |
| `?max_price=cheap` | Query | `max_price` cannot be converted to `float` | No |
| Body without `price` | Body | Required `ProductCreate.price` is missing | No |

FastAPI's error details also identify the location, such as `["path", "store_id"]`, `["query", "max_price"]`, or `["body", "price"]`.

</details>

### 6. Why use a Pydantic model instead of a plain dictionary for a request body?

<details>
<summary>Show model answer</summary>

A Pydantic model defines and validates the request-body contract before the endpoint function executes. It can enforce required fields and types, apply defaults, perform supported conversions, produce structured errors, and generate an API schema.

With `product: dict`, FastAPI can parse a JSON object, but it does not know that fields such as `name` and `price` are required or what their types should be. The function must perform that validation manually.

</details>

### 7. Why should sensitive values not be sent through query parameters?

Does placing them in the body automatically make them secure?

<details>
<summary>Show model answer</summary>

URLs may be stored in browser history, access logs, proxy logs, monitoring tools, analytics systems, bookmarks, shared links, and sometimes referrer information. Sensitive values therefore should not be placed in the query string.

A request body is less visible in the URL but is not automatically secure. HTTPS is still needed to protect the request in transit, and applications must avoid logging sensitive body data. Access tokens are normally carried in the `Authorization` header rather than the URL or business body.

HTTPS protects data in transit; authentication establishes and verifies the caller. They solve different problems.

</details>

---

## 🟠 Advanced

### 8. Can a GET request contain a body?

What should an API use for simple and complex searches?

<details>
<summary>Show model answer</summary>

A GET request can technically carry content, but HTTP does not define generally applicable semantics for it. Clients, proxies, caches, and API-documentation tools may ignore or reject it.

Use query parameters for ordinary filters:

```http
GET /products?category=keyboard&max_price=5000
```

For unusually complex structured search criteria, an API may deliberately use a POST search endpoint with a JSON body:

```http
POST /products/search
```

A GET body should not be used as a normal replacement for query parameters.

</details>

### 9. Can a path parameter be optional?

Design endpoints for all products and products belonging to one store.

<details>
<summary>Show model answer</summary>

Path parameters are required because they form part of the route's identity. If a path segment is optional, the API normally needs separate explicit routes.

Use:

```http
GET /products
```

for the global product collection, and:

```http
GET /stores/{store_id}/products
```

for the product collection scoped to one store.

This is clearer than pretending `store_id` is optional inside one path template.

</details>

---

## 🔴 Technical Lead Scenario

### 10. Review this proposed creation endpoint

```http
POST /products?store_id=7&name=Keyboard&category=electronics&price=2500&notify_supplier=true
```

<details>
<summary>Show model answer</summary>

I would redesign it as:

```http
POST /stores/7/products?notify_supplier=true
```

```json
{
  "name": "Keyboard",
  "category": "electronics",
  "price": 2500
}
```

Reasoning:

- `POST` is appropriate because the client is creating a product in a collection and the server assigns its identifier.
- `store_id` belongs in the path because it identifies the store that owns the collection.
- `name`, `category`, and `price` belong in the body because they describe the product representation.
- `notify_supplier` can remain an optional query parameter because it changes operation behaviour rather than product state.

Query parameters are not limited to GET requests. They may accompany other methods as operation modifiers.

If supplier notification is mandatory, the API should remove the flag and enforce the rule internally. Whether notification is synchronous or queued is a separate implementation decision.

</details>

---

## ⚠️ Common Mistakes

### Mistake 1: “Path means required; query means optional.”

Path parameters are required, but query parameters can be either required or optional. Meaning determines location; defaults determine optionality.

### Mistake 2: “Query parameters are only for GET requests.”

Query parameters can accompany any HTTP method. They often express filters or operation options.

### Mistake 3: “All creation data can go in the query string.”

Fields describing a structured resource belong in the request body. This provides a clearer contract and avoids an unwieldy URL.

### Mistake 4: “A plain dictionary gives the same contract as a Pydantic model.”

A dictionary does not define required business fields, their types, or defaults.

### Mistake 5: “A validation error happens inside the endpoint function.”

FastAPI validates declared path, query, and body inputs before calling the function.

### Mistake 6: “A request body is automatically secure.”

The body still needs HTTPS in transit and careful logging practices at every application and infrastructure layer.

### Mistake 7: “A GET body is a normal alternative to query parameters.”

Its meaning and ecosystem support are unreliable. Prefer query parameters or a deliberately designed search endpoint.

### Mistake 8: “A path parameter can be made optional with a default.”

The route still requires the path segment. Use separate routes when the API addresses different resource scopes.

### Mistake 9: “Optional operation settings must be part of the resource body.”

An option such as `notify_supplier` is not necessarily product state. It can be a query parameter, or part of a separately modelled command when requirements justify that design.

---

## ✅ Completion Check

Topic 03 is complete when you can explain without notes:

- The identity/options/representation decision rule
- How FastAPI infers path, query, and body inputs
- Required versus optional query parameters
- Validation failures for each input location
- The contract benefits of Pydantic models
- Why input location alone does not provide security
- Why path parameters are not optional
- How to redesign an unclear endpoint and defend the trade-offs

The chat interview demonstrated all of these capabilities.
