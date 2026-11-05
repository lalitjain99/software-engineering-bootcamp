# Topic 14 Hands-On Observations

## Run information

- Date:
- Python version:
- Command used:

## 1. Baseline metrics

Paste the `METRICS` output:

```
<!-- paste output here -->
```

- p50 latency:
- p95 latency:
- Average latency:
- Error rate:

## 2. Trace comparison

### Healthy request

- Slowest span:
- What did the trace show?

### Slow external dependency

- Slowest span:
- Why is the database not the primary bottleneck?
- What production metric would you inspect for the dependency?

### Lock contention

- Slowest spans:
- What relationship exists between lock wait and pool wait?
- Why can database CPU remain moderate while API latency rises?

## 3. Experiment changes

Record one change at a time and its effect:

| Changed delay | Before | After | Interpretation |
|---|---:|---:|---|
| External service | | | |
| Lock wait | | | |
| Pool wait | | | |
| Serialization | | | |

## 4. Observability mapping

- What information came from logs?
- What information came from metrics?
- What information came from the trace?
- Which signal would help you alert?

## 5. Production diagnosis

Write a short incident diagnosis in this format:

1. User-visible symptom:
2. Evidence:
3. Most likely bottleneck:
4. First safe mitigation:
5. Follow-up prevention:

## 6. Interview summary

Explain in 5–7 sentences how you would diagnose an API whose p95 latency increased while its error rate remained low.