# Observations — Blocking, Synchronous, and Asynchronous Calls

## 1. Coroutine function vs. coroutine object

A **coroutine function** is declared with `async def`.

A **coroutine object** is created when that function is called. It represents work that can be awaited, but its body does not start executing merely because it was called.

```python
async def fetch_data():        # coroutine function
    return "done"

work = fetch_data()            # coroutine object
result = await work
```

## 2. When does a coroutine body start executing?

The body starts when the coroutine is:

- awaited directly; or
- scheduled as a task, for example with `asyncio.create_task()` or through `asyncio.gather()`.

Calling an async function only creates the coroutine object.

## 3. `time.sleep()` vs. `await asyncio.sleep()`

- `time.sleep()` is synchronous and blocks the current thread. In an async endpoint, it blocks the event-loop thread.
- `asyncio.sleep()` is an asynchronous function. Calling it creates an awaitable coroutine, and `await asyncio.sleep(...)` pauses the current task while allowing the event loop to run other tasks.

## 4. Why was concurrent time close to the longest delay?

With sequential execution, the calls wait one after another, so total time is approximately the sum of their delays.

With concurrent execution, the independent operations overlap. `asyncio.gather()` waits for all of them, so the total is approximately the duration of the slowest operation, plus small scheduling overhead.

## 5. What does `asyncio.gather()` coordinate?

`asyncio.gather()` schedules or coordinates multiple awaitables, waits for all of them, and returns their results in the same order as the inputs.

It coordinates completion; it does not by itself limit how many operations may be active.

## 6. What does `asyncio.Semaphore(2)` limit?

It limits the number of tasks that may hold the semaphore and execute the protected section at the same time to **two**.

Other tasks may exist and wait for a permit, but they do not enter the limited section until a permit is released.

## 7. Were all tasks created and did they all run at once?

The script prepares all six coroutine calls and `gather()` schedules them for execution. However, they do **not** all execute the semaphore-protected work at the same time.

Because the semaphore capacity is two:

- at most two tasks are active inside the limited section;
- the remaining tasks wait asynchronously for a permit;
- when one task exits, another waiting task can enter.

This distinguishes **number of scheduled tasks** from **maximum active concurrency**.

## 8. What production resources could a semaphore protect?

A semaphore can protect limited capacity such as:

- downstream HTTP service concurrency;
- database or connection-pool usage;
- file descriptors and sockets;
- memory consumed by concurrent work;
- an external provider’s rate or concurrency limit.

It is a capacity-control tool, not a general performance guarantee.

## 9. Why is a semaphore not a replacement for timeouts and retries?

A semaphore only controls how many operations may be active simultaneously.

It does not:

- stop an operation that runs too long;
- decide whether a failure is retryable;
- perform retries or backoff;
- provide a circuit breaker;
- guarantee that a downstream service is healthy.

Production code may need a semaphore together with timeouts, bounded retries, backoff, and error handling.

## 10. Which lab calls represent database or HTTP calls?

The `asyncio.sleep()` calls simulate waiting for I/O. In a real FastAPI application, they could represent:

- an async HTTP request using `httpx.AsyncClient`;
- an async database query;
- an async file or object-storage operation.

The important similarity is that a real async I/O operation yields control while waiting, allowing other tasks to make progress.
