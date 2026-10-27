# Topic 11 Hands-On Lab — Observations

## 1. Async I/O

- The three simulated operations are concurrent: `asyncio.gather()` starts them together, and each `await asyncio.sleep()` yields control so the event loop can run the others.
- These operations do not create a thread per operation. They are coroutine tasks scheduled on the same event loop.
- The elapsed time should be close to the longest delay, about 1.5 seconds, rather than the sum of all delays (3.3 seconds). The operations' waiting periods overlap. Actual timing may be slightly higher due to scheduling and system overhead.

## 2. Thread pool

- With `max_workers=2`, at most two blocking jobs run at the same time in this pool.
- The five submitted jobs are all represented by futures, but jobs that cannot yet get a worker wait until one of the first two completes. They run in batches; with five one-second jobs and two workers, elapsed time should be around three seconds, plus overhead.
- A thread pool keeps blocking calls from stopping the event loop from running other coroutines. The call itself is still blocking within its worker thread; it has not become non-blocking.
- Limiting workers protects finite resources consumed by blocking work, such as database connections, downstream service capacity, memory, and the host's available threads. It also prevents an unbounded number of concurrent calls from overwhelming dependencies.

## 3. Process pool

- The pool is configured with two worker processes, so at most two calculations execute at once. Four submitted calculations therefore need multiple batches. The reported process IDs show which worker processes performed the work; scheduling may mean not every worker is necessarily visible in a particular run.
- Processes can run ordinary Python CPU work in parallel on separate CPU cores. Each process has its own Python interpreter and Global Interpreter Lock (GIL), unlike threads within one interpreter.
- A process pool adds startup and inter-process communication costs. Inputs and results generally need to be serialized and transferred, and each process uses additional memory.
- If there are more processes than the machine and workload can use effectively, the system can spend more time on scheduling and context switching, consume excessive memory, and become slower or unstable. Process counts should be chosen with CPU, memory, and workload limits in mind.

## 4. In-process worker queue

- Each worker task calls `await queue.get()`. When the queue is empty, the task suspends; adding an item makes it available to a waiting worker, which resumes and handles it.
- There are two reusable workers and five jobs. Two jobs can be processed at once; the remaining jobs wait in the queue until a worker is free.
- This `asyncio.Queue` exists only in this application's process and memory. It does not persist jobs, coordinate separate application instances, or recover work after a crash or restart.
- A production system would use a durable broker or managed queue, with persistent messages, acknowledgements, retry and dead-letter policies, and idempotent job handling. Those features help recover and safely process jobs when workers fail or messages are delivered again.

## 5. Mixed execution model

- The catalog and pricing calls use async I/O on the event loop.
- The legacy service call is blocking I/O moved to a thread pool.
- The CPU calculation runs in a process pool.
- These operations are submitted before the combined `asyncio.gather()` wait, so their work can overlap. Async tasks interleave while waiting; the thread and process do their work outside the event loop. They should not block one another, although they still share machine and dependency resources.
- This demonstration awaits all three results before it finishes, so a request using this pattern would wait for the slowest result (approximately the longest operation, plus overhead) before responding.
- Enqueue work instead of waiting when the user does not need the result immediately—for example, for report generation, email delivery, or other long-running tasks. A durable external queue and a later status/result mechanism are appropriate when the work must survive application restarts.
