# Topic 12 Hands-On Lab — Background Workers and Queues

## Objective

Simulate the lifecycle of a long-running report job:

1. API accepts a request and returns a job ID.
2. Job and outbox event are recorded together.
3. A relay publishes the outbox event to a queue.
4. A worker atomically claims the job.
5. Successful work completes the job.
6. Retryable failures are retried.
7. Permanent failures go to a dead-letter queue.
8. Cancellation is recorded before work starts.
9. Queue capacity creates backpressure.

The lab uses only Python's standard library.

## Important limitation

This lab uses in-memory dictionaries, lists, and asyncio.Queue. It demonstrates control flow, but it is not durable:

- process restart loses jobs;
- the in-memory outbox is not a real transactional outbox;
- the queue does not survive a crash;
- the lock is local to one process;
- there is no real broker acknowledgement or visibility timeout.

Production systems would use a database, a durable broker, and independent worker processes.

## Run

From this directory, run:

    python main.py

On Windows:

    py main.py

## What to observe

### 1. Job acceptance

- Which response status represents accepted-but-not-completed work?
- What job information does the API return?
- Why does the API not wait for report generation?

### 2. Outbox relay

- Why are the job record and outbox event created together?
- What would happen if publishing to the queue failed?
- Why must a real relay be able to retry an unpublished event?

### 3. Atomic worker claim

- What happens when two workers receive the same job ID?
- Why can only one worker move the job from QUEUED to RUNNING?
- What does the losing worker do?

### 4. Retry and dead-letter handling

- Which job is retried?
- When does the retry stop?
- What is the purpose of the dead-letter queue?
- Why should a retried job have a stable job or event ID?

### 5. Cancellation

- What happens when a queued job is cancelled before a worker claims it?
- Why does the worker still need to check the job state after receiving a queue message?
- How would cancellation differ after work has already started?

### 6. Backpressure

- What happens when the queue is full?
- Why is rejecting work safer than accepting an unlimited backlog?
- Which status codes could an API return when capacity is temporarily exhausted?

## Suggested observations

Record:

- the order in which API, relay, and workers print messages;
- final status of every job;
- retry count for the retryable job;
- contents of the dead-letter queue;
- behavior of the cancelled job;
- the difference between queue capacity and worker processing capacity;
- which parts would need a real database or broker in production.
