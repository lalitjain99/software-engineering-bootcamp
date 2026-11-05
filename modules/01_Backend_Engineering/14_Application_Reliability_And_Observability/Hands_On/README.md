# Topic 14 Hands-On Lab

## Application Reliability and Observability

Build and inspect a small standard-library simulation of a production API. It emits structured logs, records metrics, and creates a trace-like waterfall for several request scenarios.

## Learning objectives

- distinguish logs, metrics, and traces;
- calculate p50 and p95 latency;
- decompose total request time into stages;
- identify a database lock-wait and connection-pool symptom;
- compare a healthy request with a slow request;
- practice forming a diagnosis from evidence.

## Setup

Requirements: Python 3.11+ and the standard library only.

```
cd modules/01_Backend_Engineering/14_Application_Reliability_And_Observability/Hands_On
python main.py
```

## Exercise 1 — Run the baseline

Run the program and identify:

- total request duration;
- database-pool wait;
- SQL duration;
- external dependency duration;
- serialization duration;
- p50 and p95 latency.

## Exercise 2 — Diagnose the scenarios

The simulation includes:

1. a healthy request;
2. a request slowed by an external dependency;
3. a request slowed by database lock wait and pool checkout.

For each scenario, use the trace and metrics to answer:

- Where was most of the time spent?
- Was database CPU necessarily the bottleneck?
- What evidence distinguishes slow SQL from lock waiting?
- Which mitigation would you try first?

## Exercise 3 — Change the experiment

Modify one delay at a time:

- increase `external_ms`;
- increase `lock_wait_ms`;
- increase `pool_wait_ms`;
- increase `serialization_ms`.

Run the program again and observe how the trace and percentile summary change.

## Exercise 4 — Production mapping

For each simulated signal, identify its production equivalent:

| Simulation | Production equivalent |
|---|---|
| trace spans | OpenTelemetry/APM spans |
| JSON log line | structured application log |
| pool wait | SQLAlchemy/driver pool metrics |
| lock wait | database lock views and wait metrics |
| latency summary | histogram and percentile dashboard |

## Expected evidence

Record the command, Python version, important output, diagnosis for the slow scenario, and production mitigations in `observations.md`.