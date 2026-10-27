# Topic 11 Hands-On Lab — Handling Multiple Tasks

## Objective

Observe how different workloads should use different execution models:

- async I/O on the event loop;
- blocking I/O in a bounded thread pool;
- CPU-heavy work in a process pool;
- queued work handled by worker tasks.

The lab is intentionally local and uses simulated work. It does not call a real database or external HTTP service.

## Run

From this directory:

```bash
python main.py
```

On Windows, `py main.py` also works.

The process-pool example must remain protected by the `if __name__ == "__main__"` guard. This is required for Windows process creation.

## Exercises

Run the program and record observations for each demonstration.

### 1. Async I/O

Observe how several waiting operations overlap on the event loop.

Questions:

- Are the operations sequential or concurrent?
- Is a new thread created for each operation?
- Why is the elapsed time close to the longest delay?

### 2. Thread pool

The lab submits blocking functions to a thread pool with a fixed worker count.

Questions:

- How many blocking jobs can run at the same time?
- What happens to jobs beyond the worker count?
- Why does a thread pool move blocking work away from the event loop but not make it non-blocking?
- What production resource does the worker limit protect?

### 3. Process pool

The lab submits CPU-heavy calculations to a process pool.

Questions:

- How many calculations can run concurrently?
- Why can processes provide CPU parallelism for ordinary Python code?
- What overhead does a process pool introduce?
- What can happen if the process count is larger than the available CPU and memory capacity?

### 4. In-process worker queue

The lab places jobs on an `asyncio.Queue` and has worker tasks consume them.

Questions:

- How does a worker know that work is available?
- What happens when there are more jobs than workers?
- Why is this queue not a durable production queue?
- What would a production system add to survive process restarts?

### 5. Mixed execution model

The final demonstration combines:

- concurrent async I/O;
- a blocking function moved to a thread;
- CPU work moved to a process.

Questions:

- Which operation uses which execution model?
- Which operations can overlap safely?
- Which result must the request wait for?
- When would you enqueue the work instead of waiting?

## Important distinction

This lab demonstrates concurrency and scheduling, not production durability.

- A thread pool is local to one process.
- A process pool is local to one application instance.
- An `asyncio.Queue` loses its jobs if the process exits.
- A production queue requires a separate broker or managed messaging system, acknowledgement, retry policy, and idempotent job handling.
