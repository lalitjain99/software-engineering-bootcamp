# Topic 10 Interview Guide — Blocking, Synchronous Execution, and Asynchronous I/O

This guide consolidates the Topic 10 chat-based interview questions and the refined answers.

## 1. A blocking call inside an async endpoint

### Question

```python
@app.get("/products")
async def list_products():
    time.sleep(5)
    return {"products": []}
```

Is this endpoint truly asynchronous? What happens to the event loop, how are other requests affected, and how would you fix it?

### Answer

The endpoint is declared with `async def`, but it is not truly non-blocking because `time.sleep()` is a synchronous blocking call. It occupies the event-loop thread for five seconds. Other tasks assigned to the same event loop cannot make progress during that period.

If the delay represents asynchronous waiting, use an awaitable operation:

```python
import asyncio


@app.get("/products")
async def list_products():
    await asyncio.sleep(5)
    return {"products": []}
```

Without `await`, `asyncio.sleep(5)` only creates a coroutine and does not execute it properly.

### Key distinction

```text
time.sleep(5)       → blocks the event loop
await asyncio.sleep(5) → pauses this task and lets other tasks run
```

---

## 2. A synchronous HTTP client inside `async def`

### Question

```python
@app.get("/products")
async def list_products():
    response = requests.get("https://inventory.example.com/products")
    return response.json()
```

Why is this problematic, and how would you improve it?

### Answer

`requests.get()` is synchronous. While it waits for the external service, it does not yield control to the event loop. Other tasks using that event loop may be delayed.

Use an async-compatible HTTP client:

```python
import httpx


@app.get("/products")
async def list_products():
    response = await client.get(
        "https://inventory.example.com/products",
        timeout=5.0,
    )
    return response.json()
```

In production, reuse a shared `httpx.AsyncClient` instead of creating one for every request so that connections can be pooled and reused.

### Interview-ready explanation

> Declaring a route with `async def` does not make every operation asynchronous. The libraries used inside the route must also support asynchronous execution.

---

## 3. A synchronous route with a synchronous HTTP client

### Question

```python
@app.get("/products")
def list_products():
    response = requests.get("https://inventory.example.com/products")
    return response.json()
```

Is it still blocking? Why might it be safer for the event loop, and what limitation remains?

### Answer

The endpoint is still blocking because `requests.get()` blocks the thread while waiting for the external service.

However, FastAPI/Starlette executes ordinary synchronous path functions in a worker thread rather than directly on the main event-loop thread. Therefore, the blocking call does not directly freeze the event loop.

Changing `async def` to `def` does not make the HTTP call asynchronous. It only changes where the synchronous code executes.

The remaining limitation is finite thread capacity. If many requests wait on a slow dependency, the worker thread pool can become exhausted. New requests may queue, experience high latency, or time out.

### Design judgment

A synchronous route can be a reasonable choice when the application uses synchronous libraries consistently and concurrency is bounded. For high-concurrency I/O-heavy APIs, an async-compatible client is often more efficient.

---

## 4. CPU-heavy work inside an async endpoint

### Question

```python
@app.get("/report")
async def generate_report():
    total = 0

    for number in range(100_000_000):
        total += number

    return {"total": total}
```

Why does `async def` not solve this problem, and what execution model would you consider?

### Answer

This function is syntactically asynchronous but not cooperatively asynchronous. It performs CPU-bound work and does not reach an `await`, so it can occupy the event-loop thread for a long time. Other tasks on that event loop may be delayed.

First, check whether the calculation can be optimized. For substantial CPU-bound work, consider:

- a process pool;
- a dedicated background worker;
- a task queue such as Celery or RQ;
- separate worker processes.

Threads are usually not the best solution for heavy Python CPU work because of the Global Interpreter Lock (GIL), although they can be useful for blocking I/O.

### Important distinction

FastAPI `BackgroundTasks` may postpone work, but it does not automatically provide a separate CPU worker process. It should not be treated as a complete solution for expensive CPU computation.

---

## 5. Sequential versus concurrent independent I/O calls

### Question

```python
@app.get("/dashboard")
async def dashboard():
    products = await get_products()
    inventory = await get_inventory()
    reviews = await get_reviews()

    return {
        "products": products,
        "inventory": inventory,
        "reviews": reviews,
    }
```

How are these calls executed, and how can the waiting time be reduced?

### Answer

The calls are sequential:

```text
get_products → get_inventory → get_reviews
```

If each call takes one second, the total waiting time may be close to three seconds.

If the calls are independent, run them concurrently:

```python
import asyncio


@app.get("/dashboard")
async def dashboard():
    products, inventory, reviews = await asyncio.gather(
        get_products(),
        get_inventory(),
        get_reviews(),
    )

    return {
        "products": products,
        "inventory": inventory,
        "reviews": reviews,
    }
```

The total waiting time may now be close to the slowest individual call rather than the sum of all calls.

### Production caution

Concurrency must be bounded. Uncontrolled parallel calls can overload databases, downstream services, connection pools, memory, and rate limits.

---

## 6. A synchronous database client inside `async def`

### Question

```python
@app.get("/products")
async def list_products():
    products = sync_database_client.fetch_all()
    return products
```

Why is this problematic, would `await` fix it, and what are two valid solutions?

### Answer

The synchronous database call blocks the event-loop thread while waiting for the database.

Adding `await` does not fix it:

```python
await sync_database_client.fetch_all()
```

A normal synchronous function does not return an awaitable, so this raises a type error.

Two valid solutions are:

1. Use a native async database driver, such as `asyncpg` or async SQLAlchemy.
2. Change the route to `def` so FastAPI runs the blocking operation in its worker thread pool.

For a high-concurrency I/O-heavy API, an async database driver is usually preferable because the event loop can serve other requests while database I/O is pending. However, the async database pool must still be bounded and configured according to database capacity.

---

## 7. Timeouts for slow downstream services

### Question

An inventory service sometimes takes 60 seconds to respond. What risks does this create, why should the call have a timeout, and why should timeouts not be retried blindly?

### Answer

Even asynchronous requests consume resources while they remain open, including:

- memory;
- sockets and file descriptors;
- outbound connection-pool capacity;
- request slots;
- downstream service capacity.

Without a timeout, a request may wait indefinitely for an unhealthy dependency. A timeout creates a bounded failure window.

On timeout, the application should clean up the downstream call, log the dependency failure, and return an appropriate response. Common choices are:

- `504 Gateway Timeout` when the service timed out waiting for an upstream dependency;
- `503 Service Unavailable` when the dependency or service is unavailable.

Blind retries can create a retry storm: an already overloaded dependency receives even more traffic. Retries should use:

- safe or idempotent operations only;
- exponential backoff;
- jitter;
- a small attempt limit;
- an overall retry budget;
- circuit breaking or rate limiting where appropriate.

---

## 8. Reusing an asynchronous HTTP client

### Question

Why is this pattern inefficient?

```python
@app.get("/products")
async def list_products():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://inventory.example.com/products",
            timeout=5.0,
        )

    return response.json()
```

How should it be improved?

### Answer

Creating and closing a client for every request prevents effective connection reuse. It may require repeated connection setup, including TCP and TLS negotiation, and increases CPU, latency, socket, and ephemeral-port usage. DNS may be cached, so a new DNS lookup is not guaranteed every time, but the connection pool is still lost.

A shared client can reuse keep-alive connections and reduce connection setup overhead.

FastAPI lifespan is a suitable place to create and close it:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import httpx


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=5.0)
    yield
    await app.state.http_client.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/products")
async def list_products(request: Request):
    response = await request.app.state.http_client.get(
        "https://inventory.example.com/products"
    )
    return response.json()
```

The client must be closed during application shutdown to release active connections and sockets.

---

## 9. Exception handling with `asyncio.gather()`

### Question

Suppose three independent calls are made with `asyncio.gather()`, but `get_inventory()` raises an exception. What happens, and how can partial failures be handled?

### Answer

By default, `asyncio.gather()` uses `return_exceptions=False`. The first exception is propagated to the caller, so an unhandled exception in a FastAPI route generally becomes a `500 Internal Server Error`.

Other already-running awaitables are not automatically cancelled merely because one call failed. They may continue executing even though their results are no longer needed.

For partial failures, use:

```python
results = await asyncio.gather(
    get_products(),
    get_inventory(),
    get_reviews(),
    return_exceptions=True,
)
```

Then inspect each result and decide whether to:

- return fallback data;
- mark one field as unavailable;
- return a degraded response;
- fail the entire request.

Do not automatically return `200 OK` for every partial failure. The status code and response shape should match the endpoint contract.

---

## 10. Limiting concurrent tasks

### Question

An endpoint receives 1,000 product IDs and calls an external service once for each ID. What problem can this create, and how can it be controlled?

### Answer

Creating 1,000 tasks immediately can:

- overwhelm the downstream service;
- trigger rate limits such as HTTP `429`;
- exhaust local sockets and file descriptors;
- consume excessive memory;
- create cascading timeouts.

`asyncio.gather()` provides coordination but does not provide application-level flow control. Use a semaphore to bound active operations:

```python
import asyncio

semaphore = asyncio.Semaphore(20)


async def limited_fetch(product_id: int):
    async with semaphore:
        return await get_product_details(product_id)


results = await asyncio.gather(
    *(limited_fetch(product_id) for product_id in product_ids)
)
```

Additional production controls include:

- batching IDs through a bulk endpoint;
- per-call timeouts;
- exponential backoff and jitter;
- circuit breakers;
- rate limits;
- HTTP connection-pool limits;
- maximum request size and pagination.

### Key principle

> Async concurrency improves throughput only when it is bounded by the capacity of the application and its dependencies.

---

## Common Mistakes

### Mistake 1: “`async def` makes every operation asynchronous”

It does not. A blocking call inside `async def` can still block the event loop.

### Mistake 2: Adding `await` to any function

`await` works only with an awaitable. It cannot be used to convert a normal synchronous function into async code.

### Mistake 3: Confusing a coroutine function with a coroutine object

`async def` defines a coroutine function. Calling it creates a coroutine object that must be awaited or scheduled.

### Mistake 4: Using `time.sleep()` in async code

Use `await asyncio.sleep()` for an asynchronous delay.

### Mistake 5: Assuming async means parallel CPU execution

Async improves concurrency during cooperative I/O waits. CPU-heavy Python work may still monopolize the event loop.

### Mistake 6: Calling synchronous clients from `async def`

Examples include `requests`, synchronous database drivers, and blocking file operations. Use async-compatible clients, a synchronous route, or deliberate offloading.

### Mistake 7: Creating an HTTP client per request

This loses connection pooling and keep-alive reuse. Prefer an application-lifetime client with graceful shutdown.

### Mistake 8: Launching unbounded concurrency

`asyncio.gather()` does not automatically protect downstream services. Use semaphores, batching, pool limits, timeouts, and rate limits.

### Mistake 9: Retrying every timeout or exception

Retries can amplify an outage. Retry only when the operation is safe and use bounded backoff and jitter.

### Mistake 10: Treating `BackgroundTasks` as a solution for all heavy work

Background tasks may still execute inside the application process. Long-running or CPU-heavy work usually needs a dedicated worker or process-based system.

## Interview Summary

A strong technical-lead answer should connect the code-level choice to production capacity:

> What is the operation waiting for? Which execution resource is occupied while it waits? Is the client or dependency bounded by timeouts? Can the work be retried safely? What happens under peak concurrency?

Last updated: 2026-10-21
