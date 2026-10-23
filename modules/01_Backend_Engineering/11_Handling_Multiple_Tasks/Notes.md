# Handling Multiple Tasks

## Why this topic matters

An application may need to handle many kinds of work:

- waiting for an HTTP response;
- waiting for a database query;
- running blocking library code;
- performing CPU-heavy calculations;
- processing a task that should continue after the API response.

These workloads should not all use the same execution model. The central question is:

> Where should this work run so that it does not block unrelated work and does not exhaust resources?

## 1. The event loop

The event loop coordinates Python asynchronous execution.

It runs ready coroutine tasks on an event-loop thread. When a task reaches an await for non-blocking I/O, it pauses and gives the event loop an opportunity to run another ready task.

    Task A: start -> await network ----------------> resume -> finish
    Task B:          start -> await database -> resume -> finish
    Event loop:      runs whichever task is ready

The event loop is efficient for many tasks that spend most of their time waiting, but it is not a second CPU. A blocking function or long CPU calculation on the event-loop thread prevents other tasks from progressing.

## 2. Async tasks: I/O-bound and short-lived work

Use native async code when:

- the library provides an async API;
- the work is mostly waiting for network, database, or other I/O;
- the operation should finish as part of the current request.

    async def get_product():
        response = await http_client.get("/products/101")
        return response.json()

The await keyword does not make arbitrary code asynchronous. The called operation must itself be awaitable and must cooperate with the event loop.

## 3. Threads: blocking I/O or synchronous libraries

A thread is another execution path inside the same process. It has access to the process's shared memory.

Use a thread when:

- a required library is synchronous;
- the work is mostly waiting on blocking I/O;
- the work is short enough to complete within the request or bounded task lifetime.

    def read_from_legacy_client():
        return sync_client.fetch()

FastAPI runs ordinary def endpoints in a thread pool, so a synchronous endpoint does not directly block the async event-loop thread. However, each concurrent operation occupies a thread while it waits.

Threads do not remove the blocking; they move it to a worker thread. A limited thread pool can still become exhausted.

### Thread cautions

- Shared mutable state needs synchronization.
- Thread-safe database clients and libraries must be used correctly.
- Creating unlimited threads is unsafe.
- In CPython, the GIL generally prevents Python bytecode from achieving true CPU parallelism through ordinary threads.

## 4. Processes: CPU-bound work

A process has its own Python interpreter and memory space. Multiple processes can execute CPU-heavy Python code in parallel on different CPU cores.

Use a process pool or dedicated worker process when:

- the work is CPU-bound;
- it is too expensive to run on the event-loop thread;
- the result is needed synchronously and the work is small enough to fit within a request deadline.

Examples include image or document transformation, large data parsing, CPU-heavy model inference, and expensive compression.

Processes have more overhead than coroutines or threads because inputs and results usually need to be serialized and transferred between processes.

## 5. Background workers and queues: long-running or reliable work

Use a task queue and worker process when work:

- may run longer than an HTTP request should remain open;
- needs retries, delayed execution, or scheduling;
- should survive an API process restart;
- must be rate-limited or processed independently;
- should not consume request-time threads or event-loop capacity.

Typical flow:

    API request -> validate and enqueue job -> return 202 Accepted
                                             |
                                             v
                                      worker consumes job
                                             |
                                             v
                               updates database or emits result

A queue is not simply another thread. It provides a managed handoff, independent workers, retry policy, and operational visibility, depending on the technology.

## 6. Practical decision table

| Workload | Preferred model | Main reason |
|---|---|---|
| Async HTTP or database wait | Async task/event loop | Many waits can overlap efficiently |
| Blocking synchronous HTTP or database client | Bounded thread pool | Keeps blocking off the event loop |
| CPU-heavy Python calculation | Process pool or worker process | Uses multiple CPU cores |
| Long-running, retryable, or durable work | Task queue and workers | Decouples work from request lifetime |
| Very small immediate operation | Current request thread/event loop | Avoids unnecessary scheduling overhead |

## 7. Combining models

A production request may use more than one model:

1. The async endpoint receives and validates the request.
2. It performs independent async I/O concurrently with gather.
3. It limits downstream calls with a semaphore.
4. It sends blocking library work to a bounded thread pool.
5. It enqueues long-running work for a background worker.
6. It returns only when required request-time work is complete.

Each boundary should have an explicit timeout, cancellation and cleanup behavior, and resource limit.

## 8. Common mistakes

- Assuming async def automatically makes CPU work parallel.
- Calling time.sleep or a synchronous client inside an async route.
- Creating unlimited tasks, threads, or processes.
- Using a thread pool for work that should be durable and retryable.
- Using a process pool for simple I/O waits.
- Running long work inside an HTTP request only because it can technically be awaited.
- Forgetting that every execution model has finite capacity.

## Mental model

Remember the choice in this order:

1. Mostly waiting and an async library is available? Use async I/O.
2. Mostly waiting but the library is synchronous? Use a bounded thread pool.
3. Mostly CPU work? Use processes.
4. Long-running, retryable, or durable? Use a queue and workers.
