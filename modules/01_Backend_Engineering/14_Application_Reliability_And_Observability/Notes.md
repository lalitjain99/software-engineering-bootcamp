# When the Application Becomes Slow or Unreliable

## Why this topic matters

A production problem is rarely solved well by guessing or immediately increasing capacity. A technical lead must first answer:

> Where is the request spending time, and where is the failure occurring?

An API request may spend time waiting for:

- a connection from the database pool;
- a database lock;
- SQL execution;
- an external service;
- application code or CPU;
- response serialization or network transfer.

Observability gives us evidence about these stages.

## 1. Reliability and performance are different

### Performance

Performance describes how quickly and efficiently the system works.

Examples:

- request latency;
- database query duration;
- throughput;
- CPU and memory usage.

### Reliability

Reliability describes whether the system continues to provide correct service when components fail or traffic changes.

Examples:

- error rate;
- successful request percentage;
- recovery after a dependency outage;
- safe retries;
- data consistency.

A system can be fast but unreliable, or reliable but too slow for its users.

## 2. The three observability signals

### Logs

Logs are timestamped records of events.

Useful structured fields include:

- timestamp;
- log level;
- service and environment;
- route and HTTP method;
- status code;
- duration;
- correlation or trace ID;
- error type;
- dependency name.

Do not log passwords, bearer tokens, connection strings, or complete sensitive request bodies.

### Metrics

Metrics are numerical measurements collected over time. They are useful for dashboards, thresholds, and alerts.

Examples:

- request count;
- error count;
- latency percentiles;
- active requests;
- pool utilization;
- queue depth;
- CPU and memory;
- dependency failure rate.

### Traces

A trace follows one request across services and dependencies. It is made of spans.

Example:

    API request: 800 ms
    ├── database connection wait: 300 ms
    ├── SQL query: 20 ms
    ├── inventory HTTP call: 400 ms
    └── serialization: 80 ms

Tracing helps identify where the time went instead of showing only the total.

## 3. The four golden signals

A useful starting dashboard tracks four signals:

| Signal | Question it answers |
|---|---|
| Latency | How long do successful and failed requests take? |
| Traffic | How much work is the system receiving? |
| Errors | How often does the system fail? |
| Saturation | Which resource is close to its limit? |

Saturation can involve CPU, memory, database connections, worker threads, queue capacity, disk, or an external service rate limit.

## 4. Percentiles matter more than averages

An average can hide a bad user experience.

Suppose nine requests take 20 ms and one request takes 2,000 ms. The average may look acceptable while one user experiences a severe delay.

Common percentiles:

- p50: median request;
- p95: 95% of requests are faster than this value;
- p99: 99% are faster; useful for tail latency.

Monitor latency by endpoint, status code, dependency, and important request type.

## 5. Decomposing a slow request

Start with the total request duration, then split it into spans or measured sections:

    total latency
    = queue or worker wait
    + database connection wait
    + database lock wait
    + SQL execution
    + external dependency time
    + application computation
    + serialization and response transfer

The numbers do not need to add perfectly because instrumentation itself has overhead, but they should explain most of the request.

### Example

If a request takes 800 ms and the SQL query takes 10 ms, do not immediately optimize SQL. Investigate the remaining 790 ms:

- pool checkout;
- lock wait;
- hidden N+1 queries;
- external HTTP calls;
- CPU-heavy processing;
- oversized response serialization;
- blocking code on an async event loop.

## 6. Diagnosing common bottlenecks

### Waiting for a database connection

Evidence:

- high pool utilization;
- active connections near the pool maximum;
- increasing checkout wait time;
- `PoolTimeout` errors;
- database itself may still have spare CPU.

Investigate slow transactions, connection leaks, long queries, and whether pool sizes match traffic and database capacity.

### Waiting for a database lock

Evidence:

- high lock-wait duration;
- blocked queries;
- low or moderate database CPU while requests remain slow;
- deadlock events.

Investigate long transactions, hot rows, inconsistent lock ordering, and external calls inside transactions.

### Executing slow SQL

Evidence:

- database span consumes most of the request;
- slow-query logs show long execution time;
- `EXPLAIN ANALYZE` shows scans, bad joins, sorting, or inaccurate estimates;
- database CPU or disk I/O is high.

Optimize the query, indexes, projections, pagination, statistics, or data model before increasing connection counts.

### Application processing

Evidence:

- database and external calls are fast;
- application CPU is high;
- traces show a large gap outside dependency spans;
- profiling shows expensive loops, transformations, serialization, or blocking calls.

Use profiling and move CPU-heavy work to an appropriate process or background worker when necessary.

### Response serialization

Evidence:

- query completes quickly;
- response body is large;
- serialization spans are long;
- clients receive only a small subset of the returned data.

Use explicit response projections, pagination, compression where appropriate, and avoid serializing unnecessary ORM relationships.

## 7. Health, readiness, and liveness

### Liveness

Liveness asks whether the process is alive. A failed liveness check may cause the platform to restart the instance.

It should be lightweight. It usually should not depend on every downstream service, because a temporary database failure should not necessarily restart every application process.

### Readiness

Readiness asks whether the instance should receive new traffic. A service may be alive but not ready because it cannot serve requests safely.

Readiness may check required dependencies or initialization state, but checks must have timeouts and clear ownership.

### Startup

Startup checks allow a slow-starting process time to initialize before liveness and readiness rules become strict.

Do not use one endpoint for every health decision without understanding the consequence. Restarting an unhealthy process and removing it from traffic are different actions.

## 8. SLI, SLO, and error budget

### SLI

A Service Level Indicator is the measured behavior.

Examples:

- successful request ratio;
- p95 latency for `POST /orders`;
- percentage of jobs completed within 10 minutes.

### SLO

A Service Level Objective is the target for an SLI.

Example:

> 99.9% of valid order requests complete successfully each month, and p95 latency remains below 500 ms.

### Error budget

If the SLO allows 0.1% failures, that allowed failure amount is the error budget. Teams can use it to balance feature delivery against reliability work.

When the budget is being consumed too quickly, pause risky changes and prioritize reliability improvements.

## 9. Timeouts and dependency protection

Every network or database operation should have an intentional timeout. Without a timeout, a stuck dependency can hold connections, threads, memory, and request slots indefinitely.

Use separate budgets where appropriate:

- connection timeout;
- pool checkout timeout;
- TLS or network connect timeout;
- read timeout;
- total request deadline.

Timeouts must be compatible across layers. An inner operation should not normally outlive the caller's remaining deadline.

Combine timeouts with:

- bounded retries;
- exponential backoff and jitter;
- circuit breakers;
- bulkheads or concurrency limits;
- fallback or graceful degradation;
- load shedding.

## 10. Structured incident diagnosis

When an incident starts, use a consistent sequence:

1. Confirm the symptom: latency, errors, traffic, or saturation.
2. Identify the affected endpoint, dependency, region, and release.
3. Check traces for where request time is spent.
4. Check metrics for capacity and failure patterns.
5. Inspect logs using correlation or trace IDs.
6. Compare the timing with deployments, traffic changes, or dependency incidents.
7. Mitigate safely: rollback, reduce traffic, disable a feature, scale a bounded resource, or open a circuit.
8. Fix the root cause and verify recovery.
9. Record the incident, evidence, and follow-up actions.

## 11. What not to do first

- Do not increase every connection pool without checking database saturation.
- Do not add retries to every exception.
- Do not restart all pods before identifying whether the problem is downstream.
- Do not rely only on average latency.
- Do not log sensitive credentials for easier debugging.
- Do not declare recovery just because one request succeeded.
- Do not change several variables at once when diagnosing a production issue.

## Common mistakes

- Treating logs, metrics, and traces as interchangeable;
- measuring only total latency and not dependency spans;
- using a health check that causes unnecessary restarts;
- alerting on CPU alone without traffic and error context;
- using high-cardinality metric labels such as raw user IDs;
- setting timeouts without considering the end-to-end deadline;
- optimizing a fast SQL query while the request waits on an external service;
- hiding failures with retries instead of measuring retry volume;
- ignoring p95 and p99 tail latency;
- logging authorization headers or sensitive URLs.

## Mental model

Use this order when an application is slow or unreliable:

1. Observe the user-visible symptom.
2. Decompose the request into measurable stages.
3. Find the saturated or failing boundary.
4. Mitigate without creating a larger failure.
5. Fix and verify using the same signals.
6. Convert the learning into an SLO, alert, test, or design rule.