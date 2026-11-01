# Interview Guide — Background Execution, Workers, and Queues

## 1. Why return 202 for a long-running report?

A five-minute report should usually not keep the HTTP request open. Return 202 Accepted with a job ID and queued status. The client polls GET /jobs/{job_id} or receives a notification. 202 means the job was accepted, not completed.

Keeping the request open can cause gateway and client timeouts, occupied workers, held connections, poor user experience, and wasted work after disconnects.

## 2. BackgroundTasks versus a durable queue

FastAPI BackgroundTasks run inside the API process. They are suitable for short, non-critical work where losing the task during restart is acceptable.

A durable queue decouples producers from workers and is suitable for important, long-running, retryable, scheduled, or independently scalable work. It can provide persistent messages, acknowledgements, redelivery, retries, dead-letter handling, and multiple worker consumers.

Durability and redelivery depend on broker configuration, persistence, acknowledgements, replication, and retention. No queue should be described as providing an absolute zero-loss or exactly-once guarantee without qualification.

## 3. At-least-once delivery and duplicate work

If a worker completes an email but crashes before acknowledging the message, the broker may redeliver it. At-least-once delivery prioritizes avoiding message loss, so duplicate processing is possible.

Consumers should use stable event IDs, unique business keys, provider idempotency keys, and deduplication records. A database check alone cannot make an external email operation perfectly atomic because sending the email and updating the database are separate systems.

## 4. Preventing two workers from claiming one job

Use an atomic conditional update:

    UPDATE jobs
    SET status = 'PROCESSING', worker_id = :worker_id
    WHERE id = :job_id AND status = 'PENDING';

If one row is affected, the worker owns the job. If zero rows are affected, another worker already claimed it and this worker should not process it.

The losing worker can acknowledge a duplicate message when another worker clearly owns the job. Lease expiry and stale-processing recovery are needed to handle a worker that claimed a job and then crashed.

## 5. Recovering a job stuck in PROCESSING

Use a lease or visibility timeout. A claim stores lease_expires_at and the worker renews it through heartbeats. If the worker crashes and the lease expires, another worker may reclaim the job.

Reclaiming should use an atomic condition and preferably a version or fencing token. The token prevents a delayed old worker from overwriting the state of the newer owner.

## 6. Queue backlogs and capacity

If jobs arrive faster than workers can process them, queue depth and job wait time grow continuously. A queue absorbs temporary bursts but cannot create processing capacity.

Controls include:

- scaling workers using queue depth and oldest-job age;
- maximum queue length;
- rate limiting and per-tenant quotas;
- priority or separate queues;
- job expiry;
- bounded worker concurrency;
- workload optimization.

Reject new work when capacity is exhausted or the estimated wait violates the service-level objective. Use 429 for client or tenant quota violations and 503 for temporary service capacity problems. Retry-After may be included.

## 7. Job-status API

GET /jobs/{job_id} can return 200 when the job resource exists, regardless of whether its state is queued, running, completed, failed, or cancelled. Return 404 if the job does not exist.

A consistent schema may contain:

- job_id;
- status;
- created_at, started_at, completed_at, or failed_at;
- progress or current stage when available;
- machine-readable error code;
- result URL and expiry when completed.

A signed result URL should have a short lifetime and must not be logged.

## 8. Queue observability

Monitor:

- queue depth, oldest message age, and backlog growth;
- queue wait, processing, and end-to-end latency percentiles;
- active and idle workers, heartbeats, and restarts;
- failure, retry, and dead-letter rates;
- database, storage, downstream API, and connection-pool pressure;
- lease expiry and job reclamation.

Alert on sustained backlog growth, excessive oldest-job age, worker crash loops, high failure rate, DLQ growth, and dependency saturation.

## 9. Database and queue dual-write problem

Writing a job row and publishing a queue message as separate operations can create:

- a database job with no message;
- a queue message with no database job;
- either state after an API crash between operations.

Use a transactional outbox:

1. In one database transaction, write the job and an unpublished outbox event.
2. A relay publishes the outbox event to the queue.
3. The relay marks it published after successful publication.
4. Failed publication remains retryable.

The relay can itself publish successfully and crash before marking the row published, so consumers must be idempotent and deduplicate by a stable event ID. Idempotency keys also help if the client retries after the API commits but crashes before returning its response.

## 10. Job cancellation

Cancellation should be modeled as a durable request, for example POST /jobs/{job_id}/cancel.

A useful state flow is:

    queued -> running -> succeeded | failed
    queued -> cancelled
    running -> cancelling -> cancelled | succeeded | failed

For queued work, atomically transition queued to cancelled. For running work, set a cancellation flag and let the worker stop at safe checkpoints, clean up, and mark the job cancelled.

Cancellation is cooperative and best-effort. It cannot undo an external email, payment, or upload that already occurred. For uncertain external effects, use idempotency keys, reconciliation, compensating actions, and honest final states such as partial-effect or cancellation-failed.

## Common Mistakes

- Keeping long-running work inside an HTTP request.
- Treating BackgroundTasks as a durable queue.
- Assuming queues provide exactly-once processing.
- Acknowledging before the business work is safely completed.
- Forgetting idempotency for redelivered messages.
- Leaving jobs permanently in PROCESSING after worker failure.
- Reclaiming a lease without a version or fencing check.
- Accepting unlimited jobs without queue limits or load shedding.
- Returning 200 as if a report completed when only the job was accepted.
- Claiming cancellation can undo external side effects.
