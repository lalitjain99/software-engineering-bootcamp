# Topic 12 — Background Job End-to-End Flow

This diagram connects the request, database, outbox, queue, worker, client polling, retry, cancellation, idempotency, and backpressure decisions.

```mermaid
flowchart TD
    A["Client: POST /reports"] --> B["Validate request"]
    B --> C{"Can work finish within request limits?"}
    C -->|"Yes"| D["Perform bounded request-time work"]
    D --> E["Return 200/201 result"]
    C -->|"No"| F["Begin database transaction"]
    F --> G["Insert job: QUEUED"]
    G --> H["Insert outbox event: UNPUBLISHED"]
    H --> I{"Transaction commits?"}
    I -->|"No"| J["Return error; no job is accepted"]
    I -->|"Yes"| K["Return 202 Accepted + job_id"]
    K --> L["Client polls GET /jobs/{job_id}"]
    H --> M["Outbox relay reads unpublished event"]
    M --> N{"Publish to durable queue succeeds?"}
    N -->|"No"| O["Keep event retryable; backoff and retry"]
    O --> M
    N -->|"Yes"| P["Mark outbox event published"]
    P --> Q["Worker receives message"]
    Q --> R["Atomic claim: QUEUED -> PROCESSING"]
    R --> S{"Claim succeeded?"}
    S -->|"No"| T["Another worker owns it; acknowledge duplicate"]
    S -->|"Yes"| U["Start or renew lease"]
    U --> V{"Cancellation requested?"}
    V -->|"Yes"| W["Stop at safe checkpoint; clean up"]
    W --> X["Set job CANCELLED; acknowledge"]
    V -->|"No"| Y["Perform job stages"]
    Y --> Z{"External side effect?"}
    Z -->|"Yes"| AA["Use idempotency key and record outcome"]
    Z -->|"No"| AB["Continue processing"]
    AA --> AB
    AB --> AC{"Work completed?"}
    AC -->|"Yes"| AD["Store result; set SUCCEEDED; acknowledge"]
    AC -->|"Retryable failure"| AE["Retry with bounded backoff"]
    AE --> AF{"Attempts exhausted?"}
    AF -->|"No"| Q
    AF -->|"Yes"| AG["Set FAILED; send to DLQ; acknowledge"]
    AC -->|"Worker crash or lease expires"| AH["Reclaim with lease/version check"]
    AH --> Q
    K --> AI{"Queue capacity available?"}
    AI -->|"No"| AJ["Reject new job: 429 or 503 + Retry-After"]
    AI -->|"Yes"| M
    L --> AK{"Current job state"}
    AK -->|"QUEUED/RUNNING"| AL["Return 200 + current state"]
    AK -->|"SUCCEEDED"| AM["Return 200 + result URL"]
    AK -->|"FAILED"| AN["Return 200 + error code"]
    AK -->|"CANCELLED"| AO["Return 200 + cancellation state"]
    AK -->|"Unknown job_id"| AP["Return 404 Not Found"]
```

## Main guarantees and limits

| Concern | Design response | Important limit |
|---|---|---|
| API request timeout | Return 202 Accepted with a job ID | 202 means accepted, not completed |
| Database and queue dual write | Transactional outbox | Relay may publish a duplicate |
| Duplicate delivery | Stable event ID and idempotent consumer | Exactly-once side effects are difficult |
| Worker crash | Lease or visibility timeout | Reclaim requires version or fencing checks |
| Queue overload | Backpressure, quotas, scaling, and load shedding | A queue cannot create processing capacity |
| Cancellation | Durable cancel request and cooperative checkpoints | External side effects may not be reversible |
| Failed processing | Bounded retry and dead-letter queue | Permanent failures require investigation |
| Client visibility | Job-status endpoint and result reference | Progress may not always be measurable |

## State transition summary

```text
QUEUED
  ├──> RUNNING ───> SUCCEEDED
  │       ├───────> FAILED
  │       ├───────> CANCELLING ───> CANCELLED
  │       └───────> lease expires ───> reclaim or retry
  └──> CANCELLED
```
