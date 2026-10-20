# Topic 10 — When Requests Spend Time Waiting

## 1. The Core Question

When an API request is being processed, the application may spend time:

- doing CPU work;
- waiting for a database;
- waiting for another HTTP service;
- waiting for a file or object store;
- waiting for a queue or socket;
- waiting for a lock or connection from a pool.

The important question is not only **how long the operation takes**, but also:

> **What is the application doing while it waits?**

A thread or event-loop worker that is blocked cannot make useful progress on other work. Good backend design keeps waiting from unnecessarily occupying execution capacity.

---

## 2. A Simple Analogy

Imagine one employee serving customers.

### Blocking approach

The employee calls a warehouse and waits beside the phone until the warehouse answers. During that time, the employee serves nobody else.

### Non-blocking approach

The employee calls the warehouse, records that the answer is pending, and serves another customer. When the warehouse responds, the employee returns to the first task.

The warehouse still takes the same amount of time. The difference is whether the employee is stuck doing nothing while waiting.

In software:

- the warehouse is a database, HTTP service, file system, or socket;
- the employee is a thread or event-loop worker;
- the waiting operation is I/O.

---

## 3. Synchronous Execution

Synchronous code executes one step at a time. The next line waits until the current line returns.

```python

def get_product():
    product = database.fetch_product()  # waits here
    return product                     # runs after the query returns
```

If `fetch_product()` takes 300 ms, this function cannot continue during those 300 ms.

Synchronous code is not automatically wrong. It is often simple and appropriate when:

- the workload is small;
- the operation is CPU-bound;
- the framework is already using a worker thread;
- the dependency has only a synchronous client;
- simplicity is more valuable than maximum concurrency.

The risk appears when blocking synchronous work runs on a shared execution resource, especially an event-loop thread.

---

## 4. Blocking

An operation is **blocking** when it prevents the current execution unit from doing other useful work until the operation completes.

Examples:

```python
import time


def endpoint():
    time.sleep(2)  # blocks the current thread for two seconds
    return {"status": "done"}
```

Other common blocking operations include:

- synchronous database calls;
- `requests.get(...)` inside an async function;
- synchronous file reads of large files;
- CPU-heavy loops;
- waiting on a lock;
- calling a process synchronously.

Blocking does not mean that the entire machine stops. It means that the current thread or event-loop worker is unavailable for other work.

---

## 5. Asynchronous Execution

Asynchronous code allows an operation to pause while it is waiting and lets the runtime run other ready work.

```python
import asyncio


async def get_product():
    product = await database.fetch_product()  # pauses while I/O is pending
    return product
```

The `await` does not make the database faster. It tells the runtime:

> “This task cannot make progress right now. Run another ready task, and resume me when the result is available.”

This is especially useful for I/O-bound workloads where many requests spend time waiting.

---

## 6. The Event Loop

An **event loop** is the scheduler that manages asynchronous tasks. It repeatedly checks:

1. Which task is ready to run?
2. Which task is waiting for I/O?
3. Has any waiting I/O completed?
4. Which paused task should resume?

For example:

```python
async def fetch_data():
    print("Start")
    await database_call()
    print("Database result received")
```

When execution reaches `await database_call()`, the event loop pauses `fetch_data()` and runs another ready task instead of keeping the thread idle. When the database responds, the event loop resumes `fetch_data()` from the same point.

```text
Task A starts
   ↓
Task A waits for database
   ↓
Event loop runs Task B
   ↓
Task B waits for HTTP service
   ↓
Database responds
   ↓
Event loop resumes Task A
```

At the application level, the event loop is started and managed by the runtime:

```python
import asyncio


async def main():
    await fetch_data()


asyncio.run(main())
```

`asyncio.run(main())` creates and runs an event loop. In FastAPI, Uvicorn manages the event loop for you.

The event loop allows many requests to share an execution thread when those requests are waiting on async-compatible I/O. It does not execute all tasks simultaneously on the same thread; it switches between tasks when they cooperatively pause.

This still blocks the event loop:

```python
async def endpoint():
    import time

    time.sleep(5)  # blocks the event loop
```

Although the function is declared `async`, `time.sleep()` does not yield control. During those five seconds, other asynchronous tasks may be delayed.

A useful memory aid is:

> The event loop is a traffic controller for asynchronous tasks: it gives the CPU to work that is ready and returns later to work that is waiting.

---

## 7. Coroutine Functions and Coroutine Objects

A **coroutine function** is a function defined with `async def`:

```python
async def fetch_data():
    print("Function body is running")
    return {"value": 1}
```

Because it is defined with `async def`, `fetch_data` is a coroutine function.

When you call it:

```python
result = fetch_data()
```

Python creates a **coroutine object**. The function body does not run immediately. The object represents asynchronous work that is ready to be awaited or scheduled.

If the coroutine is never awaited or scheduled, Python may report a warning such as `coroutine was never awaited`.

### Awaiting a coroutine

`await` tells Python to run or continue the coroutine and wait for its result:

```python
async def main():
    result = await fetch_data()
    print(result)
```

`await` is normally used inside another `async def` function. While the awaited operation is waiting for compatible I/O, the event loop can run other ready tasks.

### Scheduling a coroutine

Scheduling means handing the coroutine to the event loop as a task:

```python
import asyncio


async def main():
    task = asyncio.create_task(fetch_data())

    print("Other work can run here")

    result = await task
    print(result)
```

`asyncio.create_task()` schedules `fetch_data()` so it can run when the event loop gets an opportunity. Awaiting `task` later waits for its result.

This is sequential:

```python
result_a = await fetch_a()
result_b = await fetch_b()
```

`fetch_b()` starts only after `fetch_a()` finishes.

This allows the waiting periods to overlap:

```python
task_a = asyncio.create_task(fetch_a())
task_b = asyncio.create_task(fetch_b())

result_a = await task_a
result_b = await task_b
```

The tasks are concurrent from the event loop's perspective, but this does not necessarily mean they execute simultaneously on multiple CPU cores.

### In FastAPI

When FastAPI sees an async route such as:

```python
@app.get("/products")
async def list_products():
    return await repository.list_products()
```

FastAPI and Uvicorn invoke and await the route coroutine as part of handling the HTTP request. Application code usually does not call the route function directly.

Memory aid:

```text
async def       → defines a coroutine function
function()      → creates a coroutine object
await coroutine → run/wait for its result
create_task()   → schedule it to run concurrently
```

---

## 8. What `async` and `await` Mean

### `async def`

An `async def` function creates a coroutine function. Calling it does not immediately execute the body in the same way as a normal function; it produces a coroutine that must be awaited or scheduled.

```python
async def fetch_data():
    return {"value": 1}
```

### `await`

`await` pauses the current coroutine until another awaitable operation is ready to complete.

```python
result = await fetch_data()
```

`await` only helps when the operation being awaited cooperates with asynchronous execution. Putting a blocking function inside `await` does not make it non-blocking.

This is still blocking:

```python
async def bad_endpoint():
    time.sleep(2)  # blocking call; async syntax does not change it
    return {"status": "done"}
```

A cooperative version is:

```python
async def good_endpoint():
    await asyncio.sleep(2)  # yields control while waiting
    return {"status": "done"}
```

---

## 9. FastAPI: `async def` and `def`

FastAPI supports both styles.

### Async route

```python
@app.get("/products/{product_id}")
async def get_product(product_id: int):
    product = await async_repository.get_product(product_id)
    return product
```

This is appropriate when the libraries used inside the route are asynchronous, such as an async database driver or async HTTP client.

### Synchronous route

```python
@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = sync_repository.get_product(product_id)
    return product
```

FastAPI can execute ordinary synchronous path functions in a worker thread so that they do not directly block the event-loop thread.

This does not make the operation asynchronous. It moves the blocking work to a thread, and the application still has a finite number of threads. Too many slow synchronous operations can exhaust that thread capacity.

### Important rule

Use a consistent stack:

- `async def` + async database/HTTP/file clients for cooperative I/O;
- `def` + synchronous libraries when using a synchronous stack;
- do not call blocking synchronous clients directly inside `async def` unless you deliberately offload them.

---

## 10. Async Does Not Mean Parallel CPU Execution

Async I/O improves concurrency while tasks are waiting. It does not make CPU-heavy work run simultaneously on multiple CPU cores.

```python
async def bad_cpu_endpoint():
    for _ in range(100_000_000):
        expensive_calculation()
    return {"done": True}
```

The loop does not reach an `await`, so it can occupy the event loop for a long time.

For CPU-bound work, consider:

- optimizing the algorithm;
- moving work to a process pool;
- using a background worker or task queue;
- scaling separate worker processes;
- using a library that releases the Python GIL where appropriate.

Threads are usually more useful for blocking I/O than for Python CPU-bound work. Processes provide separate CPU execution but add serialization and operational overhead.

---

## 11. Async Is End-to-End

Changing only the route declaration is not enough.

```python
@app.get("/products")
async def list_products():
    return requests.get("https://inventory.example.com/products")
```

This route is declared async, but `requests.get()` is synchronous and blocks the event loop.

A genuinely asynchronous path uses an async-compatible client:

```python
import httpx


@app.get("/products")
async def list_products():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://inventory.example.com/products")
    return response.json()
```

The same principle applies to database access, cache clients, message brokers, and file operations.

---

## 12. Waiting at Different Layers

A request may wait in several places:

| Waiting point | Example | Typical concern |
|---|---|---|
| Connection pool | No database connection is free | Pool exhaustion or checkout timeout |
| Database lock | Another transaction owns a row lock | Lock contention or deadlock |
| SQL execution | Query scans or sorts a large dataset | Slow query or missing index |
| External service | Payment or inventory API is slow | Timeout and retry policy |
| Event loop | Blocking code runs in async route | Other async requests stall |
| Thread pool | All worker threads are occupied | Request queueing and timeouts |
| CPU | Serialization or calculation is expensive | High CPU and poor throughput |

Async I/O can help with cooperative waiting, but it cannot fix slow SQL, a held database lock, an exhausted pool, or an overloaded dependency by itself.

---

## 13. Choosing the Execution Model

| Workload | Suitable starting point |
|---|---|
| Fast request validation and ordinary CRUD | Synchronous or asynchronous stack, used consistently |
| Many concurrent database/HTTP waits | Async I/O with async-compatible clients |
| Blocking library that cannot be replaced | Synchronous route or deliberate thread offload |
| Heavy Python computation | Process worker or task queue |
| Long-running work beyond request timeout | Background worker and queue |
| Multiple independent I/O calls | Async concurrency such as `asyncio.gather`, with limits |

The choice is based on the bottleneck and operational constraints, not on the idea that async is always superior.

---

## 14. Common Mistakes

### Mistake 1: “`async def` makes every function faster”

It does not. Async helps a task yield during compatible I/O waits.

### Mistake 2: Calling blocking libraries from async code

Examples include `time.sleep`, `requests`, synchronous database drivers, and large blocking file operations.

### Mistake 3: Using async for CPU-heavy work

A CPU-bound coroutine can still monopolize the event loop.

### Mistake 4: Assuming synchronous code is always unsafe

A synchronous route can be a reasonable choice when FastAPI runs it in a worker thread and the workload is bounded.

### Mistake 5: Creating unbounded concurrency

Launching thousands of async requests at once can overload the database or downstream service. Use connection limits, semaphores, rate limits, and timeouts.

### Mistake 6: Ignoring cancellation and timeouts

When a client disconnects or a dependency times out, the application should stop or clean up work where safe. Never let abandoned work consume resources indefinitely.

---

## 15. Mental Model to Remember

```text
CPU work      → execution is busy
I/O wait      → execution can yield if the stack is async-aware
Blocking wait → current thread/event-loop worker is stuck
Async await   → cooperative pause, not automatic speedup
```

The technical-lead question is:

> What is this request waiting for, which execution resource is occupied while it waits, and what happens under peak concurrency?

Last updated: 2026-10-19
