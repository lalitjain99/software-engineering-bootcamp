# Topic 13 Hands-On Observations

## Run information

- Date: 2026-11-04
- Python version: 3.14.4
- Command used: `C:/Users/asd/AppData/Local/Programs/Python/Python314/python.exe main.py`

## 1. Retry policy

- What failure did you classify as transient?
  - `TransientError` represents a temporary failure and is retried.
- What failure did you classify as permanent?
  - `PermanentError` represents a permanent failure and is raised immediately without retrying.
- How did backoff and jitter change retry timing?
  - The delay starts at `base_delay`, doubles with each failed attempt, and is randomized between zero and that capped delay. This produces bounded exponential backoff with jitter.
- What bounded the retry behavior?
  - The `attempts` argument bounds the number of operations, with no retry after the final attempt. The current helper does not yet enforce the README's total deadline; that should be added before production use.

## 2. Duplicate idempotent requests

Paste the output showing two concurrent requests with the same key:

```
duplicate requests: [{'outcome': 'CLAIMED', 'response': {'order_id': 'order-1', 'amount': 100}}, {'outcome': 'IN_PROGRESS'}]
```

- How many side effects were created?
  - One simulated side effect was created: the first request claimed the key and completed the order.
- Which request claimed the key?
  - The request that won the atomic claim returned `CLAIMED`; the concurrent duplicate returned `IN_PROGRESS`.
- What did the duplicate receive?
  - While the operation was still processing, the duplicate received the `IN_PROGRESS` status rather than a completed stored response.

## 3. Completed replay

- What happened when the completed request was sent again?
  - The stored completed response was returned with `outcome: REPLAYED`.
- Why is replaying the stored response safer than creating a new order?
  - Replay prevents a second side effect and returns the same result to every retry of the same logical request. This preserves both business consistency and the caller's view of the result.

## 4. Fingerprint mismatch

- What happened when the same key was reused with a different amount?
  - The store detected a fingerprint mismatch and raised `ValueError: idempotency key reused with different parameters`.
  - Run output: `payload mismatch: idempotency key reused with different parameters`
- Which status would your real API return: `409` or `422`? Why?
  - `409 Conflict` is the better fit because the key conflicts with an existing request identity. `422` is more appropriate for an invalid amount within a new request that does not conflict with another stored request.

## 5. Lease and fencing

Paste the output for the crashed worker, reclaim, and stale-worker behavior:

```
initial lease: CLAIMED token= 1
reclaim: RECLAIMED token= 2
stale worker accepted: False
current worker accepted: True
completed retry: {'outcome': 'REPLAYED', 'response': {'order_id': 'order-2', 'amount': 50}}
```

- Why could the old worker not overwrite the reclaimed result?
  - The original worker held token 1, while the reclaimer received token 2. The completion update includes the worker token, so the stale worker's update affected zero records and was rejected. The current worker with token 2 completed successfully.
- What would happen if the operation had already called a payment provider?
  - The provider could have charged the customer even if the local worker later crashed. Reconciliation and provider-side idempotency are required to determine the provider result and avoid a second charge.

## 6. Production gap

List at least five changes required before using this design in production:

1. Store idempotency keys and request fingerprints behind a database unique constraint.
2. Keep the claim, side-effect reference, response, and completion transition in appropriate transaction boundaries.
3. Store durable completed responses, including status and headers, for reliable replay.
4. Persist processing leases and update the fencing token atomically during reclaim.
5. Send the idempotency key to the downstream payment provider so provider retries cannot charge twice.
6. Run reconciliation to detect ambiguous outcomes, and alert on stuck processing records or repeated failures.

## 7. Interview summary

Idempotency is necessary when retrying operations that can change business state and may not be safely repeated. A network failure can leave a caller uncertain about whether its request reached the server or completed successfully. Without idempotency, one logical payment could create multiple orders or charges. The server claims an idempotency key and associates it with a request fingerprint so concurrent and subsequent attempts are handled safely. Duplicate requests replay a stored response instead of executing the operation again. Processing leases recover work abandoned by crashed workers, while fencing tokens prevent stale workers from overwriting newer work. Across retries, these mechanisms preserve exactly the intended logical result from the caller's point of view.