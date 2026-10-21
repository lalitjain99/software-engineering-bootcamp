# Topic 10 Hands-on Lab — Async Execution and Bounded Concurrency

## Objective

This lab demonstrates what happens when Python code waits, and how asynchronous code can improve concurrency without creating unbounded load.

You will observe:

1. coroutine creation and execution;
2. blocking `time.sleep()` versus cooperative `asyncio.sleep()`;
3. sequential versus concurrent I/O-style work;
4. `asyncio.gather()` for coordination;
5. `asyncio.Semaphore` for bounded concurrency.

The lab uses simulated delays instead of real database or HTTP calls, so it is reproducible and does not require external services.

## Prerequisites

- Python 3.11 or newer
- No additional dependency is required

Run from this directory:

```bash
python main.py
```

On Windows, use `py main.py` if `python` is not mapped to your Python installation.

## Lab sections

The script runs five demonstrations:

### 1. Coroutine lifecycle

Observe that calling an `async def` function creates a coroutine object. The body runs only when the coroutine is awaited or scheduled.

### 2. Blocking versus cooperative waiting

A ticker task prints timestamps while another task waits. Compare:

- `time.sleep()` — blocks the event loop;
- `await asyncio.sleep()` — yields control to the event loop.

### 3. Sequential versus concurrent work

Three simulated I/O operations each wait for a different duration. Compare total elapsed time when they are awaited one after another versus coordinated with `asyncio.gather()`.

### 4. Bounded concurrency with a semaphore

Several simulated downstream calls are launched, but an `asyncio.Semaphore` allows only two calls to be active at the same time. Observe the active count and verify that it never exceeds the configured limit.

### 5. Combined pattern

The final demonstration combines `asyncio.gather()` and a semaphore:

- `gather()` coordinates and collects results;
- the semaphore protects downstream capacity.

## Your observations

After running the script, create `observations.md` in this directory and answer:

1. What is the difference between a coroutine function and a coroutine object?
2. When does the body of a coroutine start executing?
3. What difference did you observe between `time.sleep()` and `await asyncio.sleep()`?
4. Why is the concurrent elapsed time close to the longest individual delay rather than the sum of all delays?
5. What does `asyncio.gather()` coordinate?
6. What does `asyncio.Semaphore(2)` limit?
7. Did the script create all tasks at once, and did all of them run at the same time? Explain the difference.
8. What production resources could be protected with a semaphore?
9. Why is a semaphore not a replacement for timeouts and retries?
10. In a real FastAPI application, which parts of this lab would correspond to database or HTTP calls?

## Expected learning outcome

You should be able to explain:

```text
async def       → defines a coroutine function
function()      → creates a coroutine object
await           → runs/waits for an awaitable
create_task     → schedules work with the event loop
gather          → coordinates multiple awaitables
Semaphore       → limits active concurrency
```

This lab intentionally does not cover client disconnects, cancellation, or graceful shutdown. Those will be handled as a separate request-lifecycle topic.

