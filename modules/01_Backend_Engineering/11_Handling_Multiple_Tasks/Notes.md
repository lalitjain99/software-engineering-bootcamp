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

## 3. Processes, threads, workers, and thread pools

### What is a process?

A **process** is a running instance of a program.

For example, when you start a FastAPI server, the operating system creates a process for it. A process has:

- its own Python interpreter;
- its own memory address space;
- its own file handles, sockets, and other operating-system resources.

Because processes normally have separate memory, one process cannot directly read or change another process's Python variables. Data must be passed through a mechanism such as pipes, queues, sockets, or specially configured shared memory.

### What is shared memory?

In this section, **shared memory** means memory shared by threads inside the same process.

For example, if one process contains a list called products, all threads in that process can potentially access that same list:

    Process
    ├── Thread A ──┐
    ├── Thread B ──┼── shared Python objects
    └── Thread C ──┘

This makes communication convenient, but it also creates race conditions. If two threads update the same object at the same time, a lock or another synchronization strategy may be required.

This is different from processes: separate processes do not automatically share Python objects.

### What is a thread?

A **thread** is a path of execution inside a process. A process can contain several threads.

Threads in the same process share the process's memory, but each thread has its own execution position and call stack. This allows one thread to wait for blocking I/O while another thread performs useful work.

Use a thread when:

- a required library is synchronous;
- the work is mostly waiting on blocking I/O;
- the work is short enough to complete within the request or bounded task lifetime.

    def read_from_legacy_client():
        return sync_client.fetch()

Threads do not remove the blocking; they move it to a worker thread. In CPython, ordinary threads generally do not execute Python CPU-bound bytecode truly in parallel because of the GIL.

### What is a worker?

A **worker** is an execution unit assigned to perform jobs. The word describes its role, not one particular technology.

A worker could be:

- a worker thread;
- a worker process;
- a queue consumer;
- a background service.

### What is a worker thread?

A **worker thread** is a thread dedicated to taking jobs from a queue and executing them.

    job queue -> worker thread 1
              -> worker thread 2
              -> worker thread 3

A normal thread may be created for one specific purpose and controlled directly by application code. A worker thread usually waits for jobs, processes one job, and then becomes available for another job.

### What is a thread pool?

A **thread pool** is a managed collection of reusable worker threads.

Instead of creating a new thread for every request:

1. the application submits a job to the pool;
2. an idle worker thread takes the job;
3. the thread executes the blocking function;
4. the thread returns to the pool and waits for another job.

    requests -> thread-pool queue -> [worker 1, worker 2, worker 3]

The pool has a finite size. If all worker threads are busy, new jobs wait in the pool queue or fail after a configured limit. This protects the process from creating unlimited threads, but a pool that is too small increases waiting and a pool that is too large can overload downstream systems.

FastAPI runs ordinary def endpoints in a managed thread pool, so a synchronous endpoint does not directly block the async event-loop thread. However, each concurrent operation occupies a thread while it waits, so thread-pool exhaustion is still possible.

### Thread cautions

- Shared mutable state needs synchronization.
- Thread-safe database clients and libraries must be used correctly.
- Creating unlimited threads is unsafe.
- A thread pool controls the number of concurrent blocking jobs; it does not make the underlying library non-blocking.

## 4. Processes: CPU-bound work

A process has its own Python interpreter and private memory space. Multiple processes can execute CPU-heavy Python code in parallel on different CPU cores. Because their memory is separate, passing inputs and results between processes usually requires serialization or an explicit inter-process communication mechanism.

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
