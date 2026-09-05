# Interview Exercise — HTTP Methods and Their Meaning

> Complete this after reading `Notes.md` and finishing the Product API hands-on exercise. Every question stays focused on choosing methods and reasoning about their behaviour.

## How to Use This Exercise

1. Answer aloud before opening the answer.
2. Keep a definition answer under 30 seconds.
3. For a scenario, explain the client's intention before naming the method.
4. Mark uncertain answers and revisit only the relevant notes section.

---

## 🟢 Beginner

### 1. What does an HTTP method communicate?

<details>
<summary>Show answer</summary>

An HTTP method communicates what the client intends to do with a resource.

A useful mental model is:

```text
Path identifies the resource.
Method identifies the intended operation.
```

For example, `/products/101` identifies a product, while `GET`, `PUT`, `PATCH`, or `DELETE` describes the requested operation.

</details>

### 2. Which methods would you use for these product operations?

- Retrieve product 101
- Create a product and let the server assign its ID
- Replace product 101 completely
- Change only the price of product 101
- Delete product 101

<details>
<summary>Show answer</summary>

```http
GET    /products/101
POST   /products
PUT    /products/101
PATCH  /products/101
DELETE /products/101
```

</details>

### 3. What is the difference between `PUT` and `PATCH`?

<details>
<summary>Show answer</summary>

`PUT` normally replaces the complete representation of a resource at a known location. The request therefore contains all required fields.

`PATCH` applies a partial change. Fields that are not included remain unchanged.

</details>

### 4. Why does a successful `DELETE` commonly return `204 No Content`?

<details>
<summary>Show answer</summary>

The deletion succeeded, but the server has no response representation to return. A `204` response must not contain a response body.

Other success codes can also be appropriate when the API deliberately returns information, but the Product API exercise uses `204`.

</details>

---

## 🟡 Intermediate

### 5. What is a safe HTTP method?

<details>
<summary>Show answer</summary>

A method is safe when the client is asking only to retrieve information and is not requesting a business-state change.

Among the methods covered here, `GET` is safe. Logging the request or recording metrics does not make it unsafe because those are internal side effects rather than the client's requested business operation.

</details>

### 6. What does idempotent mean?

<details>
<summary>Show answer</summary>

An operation is idempotent when repeating the same request has the same intended final effect as performing it once.

For example, repeatedly setting a product's price to `5000` leaves the price at `5000`.

</details>

### 7. Why is `DELETE` idempotent if the second request can return `404 Not Found`?

<details>
<summary>Show answer</summary>

After either one deletion or repeated deletions, the intended final state is the same: the resource is absent.

Idempotency concerns the intended final effect. It does not require every repeated request to return the same response.

</details>

### 8. Why is `POST /products` not idempotent by default?

<details>
<summary>Show answer</summary>

Each repeated request can create a separate product with a new identifier. If the client sends the same request twice, two resources may be created.

</details>

### 9. Is `PATCH` always idempotent?

<details>
<summary>Show answer</summary>

No. It depends on the change being applied.

This can be idempotent:

```text
Set the price to 4300.
```

This is not idempotent:

```text
Increase the price by 100.
```

Repeating the second operation changes the price again.

</details>

---

## 🟠 Advanced

### 10. Can a `GET` request contain a body?

<details>
<summary>Show answer</summary>

A `GET` request can technically carry a body, but its meaning is not generally defined and many clients, proxies, caches, and documentation tools may not handle it reliably.

Use path or query parameters for normal retrieval. For a complex search request that needs structured input, an API commonly uses a `POST` search endpoint with a JSON body.

</details>

### 11. Why is this endpoint dangerous?

```http
GET /products/101/delete
```

<details>
<summary>Show answer</summary>

`GET` communicates a safe, read-only operation. Browsers, crawlers, caches, and other systems may repeat or prefetch it because they do not expect it to delete data.

The clearer design is:

```http
DELETE /products/101
```

</details>

### 12. A client sends a request, the server processes it, but the response is lost. Why does method idempotency matter?

<details>
<summary>Show answer</summary>

The client cannot tell whether the server completed the operation and may retry.

Repeating an idempotent request such as “set this product to this complete representation” has the same intended final effect. Repeating a non-idempotent request such as “create a new product” may create a duplicate.

</details>

---

## 🔴 Technical Lead Scenario

### 13. Review and redesign these endpoints

```http
POST /getProduct/101
POST /createProduct
POST /updateProduct/101
GET  /deleteProduct/101
```

Assume the update changes only the product's price.

<details>
<summary>Show answer</summary>

A clearer resource-oriented design is:

```http
GET    /products/101
POST   /products
PATCH  /products/101
DELETE /products/101
```

Reasoning:

- The path identifies the product resource or product collection.
- The method communicates the operation.
- `PATCH` fits because only one part of the product changes.
- `DELETE` expresses deletion without violating the safe meaning of `GET`.

The goal is not merely cleaner naming. Correct methods communicate expectations about safety, retries, and resource changes to clients and infrastructure.

</details>

---

## 🧪 Hands-On Reflection

Answer these using the Product API you implemented.

### A. Why did the incomplete `PUT` request fail?

<details>
<summary>Show explanation</summary>

`PUT` represented complete replacement in this exercise, so both required product fields had to be provided.

</details>

### B. Why did the same partial data work with `PATCH`?

<details>
<summary>Show explanation</summary>

`PATCH` applies only the supplied changes. The omitted product fields remain unchanged.

</details>

### C. Why did the `DELETE` function return a `Response` without a dictionary?

<details>
<summary>Show explanation</summary>

The endpoint returned `204 No Content`. That status confirms success and explicitly requires an empty response body.

</details>

---

## ⚠️ Common Mistakes

### Mistake 1: “The path alone defines the operation.”

The path identifies the resource. The method and path together define the endpoint and communicate the requested operation.

### Mistake 2: “Safe means the server performs no internal writes.”

A safe method can still produce logs and metrics. It must not be used when the client is requesting a business-state change.

### Mistake 3: “Idempotent means every response is identical.”

Idempotency concerns the intended final effect. Repeated responses can have different status codes or bodies.

### Mistake 4: “`POST` only means create.”

Creating a collection resource is a common use, but `POST` more broadly means submitting information for processing or initiating an operation.

### Mistake 5: “`PUT` and `PATCH` are interchangeable.”

`PUT` communicates complete replacement, while `PATCH` communicates a partial modification.

### Mistake 6: “Every `PATCH` request is idempotent.”

A patch that sets a value can be idempotent. A patch that increments or appends may change the result every time it is repeated.

### Mistake 7: “A `GET` body is a normal replacement for query parameters.”

Although technically possible, a `GET` body is poorly supported and has no generally agreed meaning. Prefer query parameters or a deliberately designed search endpoint.

### Mistake 8: “A `204 No Content` response can include a success message.”

A `204` response cannot contain a body. Use another successful status if the API needs to return a representation or message.

---

## ✅ Completion Check

This exercise is complete when you can explain without notes:

- How the method and path work together
- When to choose `GET`, `POST`, `PUT`, `PATCH`, or `DELETE`
- The difference between safe and idempotent
- Why repeated `POST` requests can be risky
- Why `PUT` and `PATCH` communicate different intentions
- Why `DELETE` can be idempotent even when repeated responses differ

Do not memorize only the method table. Practice explaining the intention and expected behaviour behind each choice.
