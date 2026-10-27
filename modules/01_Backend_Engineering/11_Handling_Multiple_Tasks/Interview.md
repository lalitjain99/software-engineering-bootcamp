# Interview Guide — Handling Multiple Tasks

## 1. Sync client inside async route

A synchronous call inside async def runs on the event-loop thread and blocks other coroutines on that loop. Changing the route to regular def makes FastAPI run it in a bounded thread pool, but the operation remains blocking and can exhaust threads.

## 2. CPU-heavy work inside async route

async def does not make CPU work asynchronous. CPU-heavy synchronous code occupies the event-loop thread. Use a process pool for request-time CPU work or a worker queue for long-running work.

## 3. Sync database client

Adding await to a synchronous database call does not make it async and usually raises TypeError after the call returns. Use a native async database client, a regular def route, or explicitly move the sync call to a bounded thread.

## 4. Sequential versus concurrent I/O

Awaiting independent operations one after another is sequential. asyncio.gather() can overlap independent awaitable operations and usually reduces total waiting time to approximately the slowest operation.

## 5. Why gather needs limits

Unbounded gather can overwhelm downstream services, connection pools, sockets, memory, and rate limits. Use asyncio.Semaphore, timeouts, bounded retries, rate limiting, batching, and circuit breakers where appropriate.

## 6. Process pool versus worker queue

A process pool suits CPU-heavy work whose result is needed during the current request and fits the request deadline. A worker queue suits long-running, retryable, durable, or scheduled work. Queue durability depends on broker and acknowledgement configuration.

## 7. Choosing models by workload

- Async HTTP or database I/O: event loop with native async client.
- Blocking synchronous I/O: bounded thread pool.
- CPU-heavy Python: process pool.
- Long-running or durable work: task queue and worker processes.

## 8. Thread-pool exhaustion

If a pool has ten workers and each blocking call takes thirty seconds, only ten calls actively run. Other requests wait in the queue and may experience high latency, request timeouts, gateway timeouts, or rejected work.

## 9. Process-pool capacity

A process pool with four workers can execute four CPU-heavy tasks concurrently. Additional tasks wait or may be rejected if the queue is bounded. Too many processes can cause memory exhaustion, CPU oversubscription, context switching, cache contention, and slower throughput.

## 10. Mixed-workload request

For a request containing multiple kinds of work:

1. Run independent async HTTP calls concurrently with gather, using limits when needed.
2. Run the synchronous legacy library in a bounded thread pool.
3. Run CPU-heavy work in a process pool if its result is required immediately.
4. Enqueue long-running report generation to a durable worker queue and return a job ID or 202 Accepted when the result is not needed immediately.

The exact order depends on dependencies. Independent operations can overlap. A report can be enqueued as soon as its required input is known; the request should not wait for the report to finish.

## Common Mistakes

- Treating async def as automatic parallelism.
- Adding await to a synchronous function.
- Calling blocking clients directly on the event loop.
- Using threads for ordinary Python CPU parallelism.
- Creating unlimited tasks, threads, or processes.
- Using asyncio.gather() as a concurrency limit.
- Treating a queue as equivalent to an in-process background task.
- Assuming a process pool survives an application restart.
- Assuming a queue is durable without configuring persistence and acknowledgement behavior.
