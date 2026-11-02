# Topic 12 Hands-On Lab — Observations

## 1. Job acceptance

- The API returns `202 Accepted`, which represents work that was accepted but not completed.
- It returns a job ID and the initial queued status.
- The API does not wait for report generation because report generation is long-running and should not block the request-response cycle.

## 2. Outbox relay

- The job record and outbox event are created together under the store lock, representing a single transaction. This helps prevent the job from existing without an associated event to publish.
- If publishing to the queue failed, a real relay could leave the event in the outbox for a later attempt.
- A real relay must retry unpublished events because temporary network, broker, or processing failures can interrupt publishing.

## 3. Atomic worker claim

- Two workers can receive the same job ID if a broker delivers duplicate messages or a message becomes visible again.
- The lock makes the `QUEUED` to `RUNNING` transition atomic, so only one worker sees the job while it is still queued and can claim it.
- The worker that loses the claim logs that the job could not be claimed and skips its processing.

## 4. Retry and dead-letter handling

- `job-retry` uses the retryable behavior. Its first attempt raises a temporary `RuntimeError`, the job is returned to `QUEUED`, and it is put back on the queue.
- The retry stops when the job succeeds. In this demonstration, the retry succeeds on the second attempt.
- If `attempts` reaches `max_attempts`, the job is marked `FAILED` and sent to the dead-letter queue.
- The dead-letter queue holds jobs that exhausted retries or encountered permanent failures. It provides a place to inspect and handle them instead of losing them or processing them indefinitely.
- Stable job and event IDs support duplicate detection and idempotent processing. They also make retries traceable and prevent repeated delivery from creating duplicate jobs or duplicate side effects.

## 5. Cancellation

- `job-cancelled` is cancelled while it is queued. It changes directly from `QUEUED` to `CANCELLED`, and the outbox relay skips it.
- A worker must check the job state after receiving a queue message because cancellation may happen between delivery and claim. Without this check, the worker might incorrectly process a cancelled job.
- If work has already started, the API changes the job to `CANCELLING`, sets `cancel_requested`, and the worker stops at its next safe checkpoint. Work that has already happened is not automatically undone, so real systems should use safe checkpoints and compensating actions where appropriate.

## 6. Backpressure

- With a maximum queue size of two, `capacity-1` and `capacity-2` are accepted. `capacity-3` cannot be added and raises `QueueFull`.
- Rejecting a third job is safer than accepting an unlimited backlog because it limits memory use and prevents downstream workers and dependencies from being overwhelmed.
- The demonstration returns `503 Service Unavailable` and includes `Retry-After: 10`. APIs may also use `429 Too Many Requests` when rejection is caused by a client rate limit rather than temporary queue capacity.

## Observed pipeline

- `job-success` ends in `SUCCEEDED`.
- `job-retry` is retried once and ends in `SUCCEEDED`; its final retry count is two attempts.
- `job-failure` ends in `FAILED` and is added to the dead-letter queue.
- `job-cancelled` ends in `CANCELLED`, and its outbox event is skipped.

The dead-letter queue contains `job-failure` in this run.

## Production requirements

This lab demonstrates control flow, but production requires:

- a database for durable jobs, state, and outbox records;
- database transactions and a concurrency-safe claim mechanism;
- a durable broker with acknowledgements and visibility timeouts;
- independent worker processes;
- retry limits and dead-letter handling;
- cancellation support and safe checkpoints;
- stable and idempotent job/event identifiers;
- metrics and logs for queue depth, failures, retries, and processing latency.
