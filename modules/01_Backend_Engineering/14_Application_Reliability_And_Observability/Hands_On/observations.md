# Topic 14 Hands-On Observations

## Run information

- Date: 2026-11-05
- Python version: 3.14.4
- Command used: `C:/Users/asd/AppData/Local/Programs/Python/Python314/python.exe main.py`

## 1. Baseline metrics

Paste the `METRICS` output:

```
METRICS
  request_count: 3
  p50_latency_ms: 201.52
  p95_latency_ms: 333.07
  average_latency_ms: 196.78
  error_rate: 0.0%
  diagnosis_hint: inspect dependency spans and pool/lock wait before changing SQL
```

- p50 latency: 201.52 ms
- p95 latency: 333.07 ms
- Average latency: 196.78 ms
- Error rate: 0.0%

## 2. Trace comparison

### Healthy request

- Slowest span: `inventory.http` at 20.28 ms
- What did the trace show? The request took 41.12 ms in total. Its external inventory call was the largest single span, followed by SQL at 10.26 ms. Pool checkout, lock wait, and serialization remained small.

### Slow external dependency

- Slowest span: `inventory.http` at 180.59 ms
- Why is the database not the primary bottleneck? The database query took only 10.18 ms and the pool checkout took 5.19 ms, while the external inventory call alone took 180.59 ms. It accounts for most of the 201.52 ms total.
- What production metric would you inspect for the dependency? Inspect the inventory dependency's latency histogram or p95/p99, success/error rate, timeout rate, in-flight request count, saturation, and downstream service health.

### Lock contention

- Slowest spans: `db.lock.wait` at 220.51 ms, followed by `db.pool.checkout` at 90.61 ms
- What relationship exists between lock wait and pool wait? Lock contention can keep database work active longer and occupy connections. While those transactions hold resources, later requests wait longer for a connection from the pool. In this simulated trace, both waits are directly visible before the short SQL query.
- Why can database CPU remain moderate while API latency rises? Most time is spent waiting for a lock and connection, not actively executing SQL. Wait state consumes request threads and capacity without creating much database CPU work, so low CPU does not mean the request is healthy.

## 3. Experiment changes

Record one change at a time and its effect:

| Changed delay | Before | After | Interpretation |
|---|---:|---:|---|
| External service | 20 ms span / 41.12 ms total | 180 ms span / 201.52 ms total | The inventory span increased by approximately 160 ms and account for nearly the entire total latency increase. |
| Lock wait | 0 ms span / 127.18 ms total with the lock scenario's 90 ms pool wait | 220 ms span / 347.69 ms total | Lock wait directly raised request latency while the SQL span remained about 10 ms; the lock owner was more likely than SQL execution to be the bottleneck. |
| Pool wait | 5 ms span / 262.08 ms total with lock wait fixed at 220 ms | 90 ms span / 347.69 ms total | Additional connection-checkout wait was added nearly directly to request total; connection capacity or connection lifetime should be investigated. |
| Serialization | 5 ms / 347.69 ms total with pool wait at 90 ms and lock wait at 220 ms | 80 ms / 422.69 ms estimated total | Increasing serialization from 5 ms to 80 ms adds approximately 75 ms; database and dependency spans should remain unchanged, so response payload size and serialization efficiency become the primary suspects. |

For precise values after changing lock, pool, or serialization, rerun `main.py` and replace the inferred totals above with the new measured output.

## 4. Observability mapping

- What information came from logs? The structured JSON logs identified the event, route, scenario, status code, trace ID, request duration, and duration of each span.
- What information came from metrics? The metrics summarized overall request volume, latency percentiles, average latency, error rate, and provided a diagnosis hint.
- What information came from the trace? The trace decomposed each request into pool checkout, lock wait, SQL, external HTTP, and serialization spans, making the slowest stage visible.
- Which signal would help you alert? Metrics are best for paging and alerting, especially error rate and latency histograms/percentiles. Logs provide searchable context, while traces support investigation after an alert fires.

## 5. Production diagnosis

Write a short incident diagnosis in this format:

1. User-visible symptom: Order requests are unusually slow, but the application is still returning successful responses.
2. Evidence: The p95 is 333.07 ms, while the error rate remains 0.0%; traces show either an external inventory dependency delay or, in the contention scenario, 220.51 ms of lock wait and 90.61 ms of pool wait.
3. Most likely bottleneck: Database lock and connection-pool waits for the lock-contention scenario, or slow inventory-service latency in the slow-external scenario.
4. First safe mitigation: Use dependency timeouts and graceful degradation where possible; for lock contention, identify the blocking transaction, verify whether it is stale or legitimate, reduce transaction scope, and terminate it only through an approved incident procedure when safe.
5. Follow-up prevention: Add dependency timeouts and retries with bounded backoff, optimize transaction boundaries, monitor active/idle connections, checkout time, transaction duration, and pool capacity rather than increasing pool size blindly, investigate lock holders, and add latency/error dashboards and alerts.

## 6. Interview summary

An API can see its p95 latency rise while its error rate stays low because tail latency reflects slow successful requests rather than failed responses. First, examine latency metrics by route and recent deployment or configuration changes. Then compare traces for healthy and slow requests to identify whether one stage dominates total time. Check dependency spans and dependency health before assuming SQL is slow. If database time is short, inspect lock wait and connection pool checkout time, because waiting is caused by contention rather than CPU execution. Pool saturation may also arise when lock holders keep connections occupied. Logs provide request and error context, while traces show where time is spent. The mitigation should address the observed bottleneck, followed by pooling, timeout, transaction, dependency, and alerting improvements.