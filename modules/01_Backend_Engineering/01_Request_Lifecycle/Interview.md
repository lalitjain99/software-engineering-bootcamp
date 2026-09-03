# Interview Exercise — The Simplest Backend Request

> Complete this only after reading `Notes.md`. Every question is limited to concepts already introduced.

## How to Use This Exercise

1. Answer aloud before opening the answer.
2. Keep a basic answer under 30 seconds.
3. For reasoning questions, trace the request step by step.
4. Mark unclear answers and return only to the relevant notes section.

Do the sections separately if completing everything at once feels heavy.

---

## 🟢 Beginner

### 1. What is the difference between a client and a server?

<details>
<summary>Show answer</summary>

A client initiates communication by sending a request. A server is a running program that waits for requests, processes them, and returns responses. A browser, mobile application, Postman, or another backend can act as a client.

</details>

### 2. What is an API endpoint?

<details>
<summary>Show answer</summary>

An endpoint is the combination of an HTTP method and a path, such as `GET /products/101`.

</details>

### 3. What are the main parts of this URL?

```text
http://127.0.0.1:8000/products/101
```

<details>
<summary>Show answer</summary>

- `http`: protocol
- `127.0.0.1`: host or machine
- `8000`: port identifying the application on that machine
- `/products/101`: path identifying the target inside the application

</details>

### 4. Why does a request need a port?

<details>
<summary>Show answer</summary>

The host identifies the machine, but the machine can run many network applications. The port allows the operating system to deliver the request to the correct application.

</details>

---

## 🟡 Intermediate

### 5. What happens when the port is omitted from an HTTP URL?

<details>
<summary>Show answer</summary>

The client uses the protocol's default port. HTTP uses port `80`, while HTTPS uses port `443`. Omitting the port does not mean that no port is used.

</details>

### 6. Why can't `/products/101` identify the correct application without a port?

<details>
<summary>Show answer</summary>

The operating system must first use the port to select the program that will receive the connection. The path is part of the HTTP request and can be examined by FastAPI only after the request reaches the correct program.

</details>

### 7. Trace `GET /products/101` through the example FastAPI application.

<details>
<summary>Show answer</summary>

1. The client sends the request to the host and port.
2. The operating system delivers it to the listening server program.
3. FastAPI matches the method and path to a route.
4. FastAPI converts and validates `product_id`.
5. The Python function runs.
6. The function returns a dictionary.
7. FastAPI converts it to JSON and sends an HTTP response.

</details>

### 8. What happens when the client calls `/products/abc`?

<details>
<summary>Show answer</summary>

The route declares `product_id: int`. FastAPI cannot convert `"abc"` into an integer, so it returns a validation-error response without executing the function body.

</details>

---

## 🟠 Advanced

### 9. Are these the same endpoint?

```text
GET /products/101
DELETE /products/101
```

<details>
<summary>Show answer</summary>

No. An endpoint is defined by both method and path. The paths are identical, but the methods represent different operations.

</details>

### 10. Does the Python dictionary travel directly over the network?

<details>
<summary>Show answer</summary>

No. The dictionary exists inside the Python process. FastAPI converts it into a network-friendly representation—normally JSON—and constructs an HTTP response containing a status code, headers, and body.

FastAPI, using Starlette internally:

Converts the Python dictionary into JSON.
Encodes that JSON into bytes for transmission.
Chooses a status code—200 OK by default.
Adds response headers such as Content-Type.
Creates the response body.

</details>

### 11. Can two ordinary applications listen on `127.0.0.1:8000` at the same time?

<details>
<summary>Show answer</summary>

Normally, no. That host-and-port combination is already occupied by the first listening application. The second application must use a different port unless a specialized sharing arrangement exists.

</details>

---

## 🔴 Technical Lead Scenario

### 12. Your FastAPI application listens on port `8000`, but users should call:

```text
https://api.example.com/products/101
```

Why is `:8000` not visible, and what must happen to the request?

<details>
<summary>Show answer</summary>

HTTPS uses port `443` by default, so the client implicitly connects to port `443`. A public-facing component listens there and passes the request internally to the FastAPI application on port `8000`.

At this stage, the important reasoning is:

```text
Public request on 443 → internal FastAPI application on 8000
```

The detailed production components will be introduced later.

</details>

---

## 🧪 Mini Exercise

Assume Uvicorn is listening on `127.0.0.1:8000` and the application defines only:

```python
@app.get("/products/{product_id}")
def get_product(product_id: int):
    ...
```

Predict what happens in each case before opening the explanation.

### A. `http://127.0.0.1:8000/products/101`

<details>
<summary>Show explanation</summary>

The request reaches Uvicorn on port `8000`, the route matches, and FastAPI calls `get_product(101)`.

</details>

### B. `http://127.0.0.1/products/101`

<details>
<summary>Show explanation</summary>

The client tries port `80`, because the URL uses HTTP and omits the port. It will not reach Uvicorn on port `8000` unless another component on port `80` forwards the request.

</details>

### C. `http://127.0.0.1:8000/products/abc`

<details>
<summary>Show explanation</summary>

The request reaches the application and the route shape matches, but validation fails because `abc` cannot be converted to an integer.

</details>

---

## ⚠️ Common Mistakes

### Mistake 1: “The IP address identifies the application.”

The IP address identifies the machine. The port identifies the network application on that machine.

### Mistake 2: “If the port is omitted, no port is used.”

A default port is still used: `80` for HTTP or `443` for HTTPS.

### Mistake 3: “The operating system uses the URL path to find FastAPI.”

The operating system uses the port to find the listening program. FastAPI reads the path afterward.

### Mistake 4: “FastAPI sends a Python dictionary across the network.”

FastAPI serializes the dictionary—normally as JSON—and constructs an HTTP response.

### Mistake 5: “A path alone defines an endpoint.”

An endpoint requires both the HTTP method and path.

### Mistake 6: “FastAPI and Uvicorn are exactly the same thing.”

FastAPI defines the application, routes, validation, and responses. Uvicorn is the server program that listens for requests and runs the FastAPI application.

---

## ✅ Completion Check

This exercise is complete when you can explain, without notes:

- Why both host and port are required
- What happens when a port is omitted
- How FastAPI selects and runs a route
- How a Python return value becomes an HTTP response

Do not move to the next topic based on memorization. Move when the request flow feels natural.
