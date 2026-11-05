# Topic 14 Interview Guide

## Application Reliability and Observability

## 1. A request takes 800 ms, but the database query takes 10 ms. What do you investigate?

Start with a distributed trace and decompose the request into measurable stages:

- database-pool checkout;
- database lock wait;
- SQL execution;
- external HTTP calls;
- application CPU or blocking code;
- response serialization;
- network transfer.

Compare a fast p50 trace with a slow p95 or p99 trace. Inspect event-loop lag, thread-pool wait, downstream connection pools, payload size, and middleware. Do not optimize the database merely because the endpoint uses a database.

## 2. Explain logs, metrics, and traces

| Signal | Best question it answers |
|---|---|
| Logs | What event happened and what context surrounded it? |
| Metrics | How often and how severely is a behavior occurring? |
| Traces | Where did one request spend time or fail across components? |

For `POST /orders`, structured logs may contain route, status, duration, trace ID, error code, and bounded business context. Metrics should include request rate, error rate, latency percentiles, dependency latency, and saturation. A trace can show that 700 ms was spent in a payment provider even though the database took 10 ms.

Never log bearer tokens, passwords, connection strings, or unnecessary sensitive payload data. Avoid unbounded metric labels such as raw order IDs.

## 3. Liveness versus readiness

- **Liveness:** Is the process alive and making progress? Failure may cause a restart.
- **Readiness:** Should this instance receive traffic? Failure removes it from routing while leaving it available for recovery and debugging.

If the database is unavailable, readiness may fail when the API cannot serve its required operations. The liveness probe should usually remain independent of the database; putting the dependency check only in liveness can create a restart storm.

Health checks should be lightweight, bounded by timeouts, and limited to dependencies required for the promised behavior. Do not make a peripheral analytics service capable of taking the core API out of rotation.

## 4. SLI, SLO, and error budget

- **SLI:** The measured behavior, such as successful valid requests divided by total valid requests.
- **SLO:** The target, such as 99.9% successful valid requests in a defined window.
- **Error budget:** The allowed unreliability left by the target. A 99.9% SLO leaves a 0.1% budget.

An error budget turns reliability into an operational decision. If the budget is healthy, a risky release may be acceptable with safeguards. If it is being consumed rapidly, prioritize reliability work, reduce release risk, or require stronger rollout controls.

An SLO is more useful than saying “be reliable” because it is measurable, reviewable, and tied to user-visible behavior.

## 5. Diagnose high latency with lock waits and pool waits

Suppose traffic is normal, p95 latency is rising, error rate is low, database CPU is 35%, lock-wait time is high, and application requests are waiting for connections.

The likely chain is:

    long transaction holds lock
        -> other queries wait
        -> connections remain checked out
        -> pool becomes exhausted
        -> new requests wait
        -> tail latency rises

Investigate:

1. blocked sessions and the blocking transaction;
2. transaction age and sessions `idle in transaction`;
3. pool utilization, checkout wait, and `PoolTimeout` errors;
4. recent deployments or code paths holding transactions across network calls;
5. deadlocks, slow SQL, and connection leaks.

Pool exhaustion is often a downstream symptom, not the root cause.

## 6. Timeouts and dependency protection

Every network and database operation needs an intentional timeout. Combine timeouts with bounded retries, backoff, jitter, circuit breakers, concurrency limits, and load shedding.

Use an end-to-end deadline so an inner operation does not continue after the caller has already timed out. Avoid increasing connection pools or retry counts before identifying the bottleneck.

## Common mistakes

- Looking only at average latency;
- treating a trace gap as proof of one specific cause;
- putting all dependency checks in liveness;
- restarting healthy processes because a database is temporarily unavailable;
- increasing a connection pool without checking database saturation;
- logging sensitive headers or request bodies;
- using high-cardinality metric labels;
- adding retries without measuring retry volume;
- alerting on CPU alone;
- changing multiple production variables before collecting evidence.

## Interview answer pattern

Use this sequence:

1. State the user-visible symptom.
2. Identify the relevant observability signals.
3. Decompose the request into stages.
4. Form a hypothesis from the evidence.
5. Verify it with targeted metrics, traces, logs, or database views.
6. Apply the safest mitigation.
7. Verify recovery and record the prevention measure.