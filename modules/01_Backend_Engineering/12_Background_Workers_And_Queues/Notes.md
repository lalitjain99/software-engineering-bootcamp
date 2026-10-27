# When Work Cannot Finish Inside a Request

## Why this topic matters

An HTTP request is a temporary interaction:

1. The client sends a request.
2. The server performs work.
3. The server returns a response.
4. The request ends.

This model is appropriate for short, bounded operations. It becomes a poor fit when the work:

- takes several minutes;
- depends on a slow or unreliable service;
- needs retries;
- should continue if the client disconnects;
- should survive an application restart;
- needs to be processed at a controlled rate.

The central design question is:

> Should this work finish before the HTTP response, or should the API hand it off and let another worker finish it later?

## 1. Request-time work versus background work

### Request-time work

The API keeps the request open until the required result is ready.

Use this when:

- the client needs the result immediately;
- the operation fits comfortably within request and gateway timeouts;
- the work has a predictable duration;
- the required resources can handle the concurrency.

Example:

    POST /products/101/price
    -> validate request
    -> calculate price
    -> return 200 OK with the price

### Background work

The API accepts the request, creates a job, and returns before the work finishes.

Typical response:

    HTTP/1.1 202 Accepted

    {
      "job_id": "job-123",
      "status": "queued"
    }

The client can later call:

    GET /jobs/job-123

The job may eventually be:

- queued;
- running;
- completed;
- failed;
- cancelled.

Returning 202 means the request was accepted for processing. It does not mean the background work has succeeded.

## 2. What is a worker?

A worker is a process or task that consumes a job and performs the work.

    API -> job queue -> worker -> database or external service

The API handles short request-time responsibilities:

- validate input;
- create a job record;
- publish a job message;
- return a job ID.

The worker handles the long-running operation independently.

A worker may be:

- an asyncio task inside the API process;
- a thread;
- a separate process;
- a separate container or deployment;
- a managed cloud worker.

These choices have different failure and durability properties.

## 3. In-process background tasks

An in-process background task runs inside the same application instance after the response is sent.

FastAPI provides BackgroundTasks for small tasks such as:

- writing a small audit record;
- sending a lightweight notification;
- performing simple cleanup.

### Important limitations

An in-process task:

- is tied to the API process;
- consumes the API process's CPU, memory, or thread capacity;
- can be lost if the process crashes or restarts;
- is not automatically coordinated across multiple replicas;
- does not provide a durable queue;
- may compete with request traffic.

It is not a replacement for a production task queue.

Use it only when losing the task is acceptable and the task is short and lightweight.

## 4. Durable queues

A durable queue stores jobs outside the API process.

    API -> durable broker -> worker
                         -> worker
                         -> worker

The broker can provide features such as:

- persistent messages;
- acknowledgement;
- redelivery after worker failure;
- delayed delivery;
- retry support;
- dead-letter queues;
- visibility into queue depth;
- multiple independent workers.

Examples include RabbitMQ, Redis-based queues, cloud task services, Google Pub/Sub, Azure Service Bus, and AWS SQS.

The exact guarantees depend on configuration. A queue should not be described as “exactly once” without understanding its delivery semantics. Many systems provide at-least-once delivery, meaning a job may be delivered more than once.

## 5. Acknowledgement and redelivery

A worker normally follows this sequence:

1. Receive a job.
2. Perform the work.
3. Acknowledge successful processing.

If the worker crashes before acknowledgement, the broker may make the job available again.

This improves reliability but creates a requirement:

> Job processing should be idempotent or should use a deduplication strategy.

For example, a worker should not create two invoices merely because the same message was delivered twice.

Detailed retry and idempotency design will be covered in Topic 13.

## 6. Job status and result storage

For a user-facing background operation, the system usually stores job state in a database or durable job store.

Example:

    jobs
    ├── id
    ├── status
    ├── created_at
    ├── started_at
    ├── completed_at
    ├── result_location
    ├── error_code
    └── attempt_count

The API can expose:

    POST /reports
    -> 202 Accepted, job_id

    GET /jobs/job-123
    -> queued, running, completed, or failed

Large results should usually be stored in object storage or a database, with the job status containing a reference rather than the complete result.

## 7. Why not keep the HTTP request open?

Keeping a request open for a long operation can cause:

- load-balancer or gateway timeouts;
- client timeouts;
- occupied worker threads or event-loop tasks;
- held database connections;
- wasted work after a client disconnects;
- poor user experience;
- difficulty retrying or recovering after failure.

A queue separates the client's request lifetime from the work's execution lifetime.

## 8. Choosing the right pattern

| Situation | Suitable approach |
|---|---|
| Small work that may be lost safely | In-process background task |
| Short result required immediately | Complete during the request |
| Long-running or CPU-heavy work | Worker process or task queue |
| Work requiring retries and durability | Durable task queue |
| Scheduled or delayed work | Scheduler plus durable queue |
| Large report or file generation | Queue job and store result externally |
| Many jobs competing for limited dependency capacity | Queue with bounded workers |

## 9. Backpressure and queue capacity

A queue absorbs bursts, but it does not remove the work.

If jobs arrive faster than workers can finish them:

- queue depth grows;
- job wait time increases;
- memory or broker storage can fill;
- users receive stale results;
- downstream dependencies may still be overwhelmed.

Production controls include:

- maximum queue length;
- rate limiting at the API;
- bounded worker concurrency;
- separate queues by workload;
- job expiration;
- priority rules;
- alerts on queue age and depth;
- graceful rejection with 429 or 503 when capacity is exhausted.

## 10. A practical request flow

    Client
      |
      | POST /reports
      v
    API
      | validate and create job
      | publish message
      v
    Queue
      |
      v
    Worker
      | generate report
      | store result
      | update job status
      v
    Client polls GET /jobs/{job_id}

The API should not claim success for the final business operation until the worker has completed it. The initial response only confirms that the job was accepted.

## Common mistakes

- Treating FastAPI BackgroundTasks as a durable queue.
- Returning 200 OK when work has only been accepted; 202 is usually clearer.
- Keeping database connections open while waiting for a long job.
- Assuming a queue guarantees exactly-once processing.
- Forgetting idempotency when messages can be redelivered.
- Creating unlimited workers and overwhelming a dependency.
- Storing large job results directly in queue messages.
- Providing no way for the client to check job status.
- Ignoring queue depth, job age, and failed-job metrics.
- Starting long work in the API process merely because it can be scheduled.

## Mental model

Remember the boundary:

> The API accepts and records the work. The worker performs the work. The queue connects them and provides controlled handoff.

Use an in-process task only for small, non-critical work. Use a durable queue when the work must survive restarts, be retried, or be processed independently of request traffic.
