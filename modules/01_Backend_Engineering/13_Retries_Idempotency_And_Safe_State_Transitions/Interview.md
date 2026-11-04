# Topic 13 Interview Guide

## Retries, Idempotency, and Safe State Transitions

This guide consolidates the reviewed interview discussion for Topic 13. Focus on explaining the reasoning and trade-offs, not memorizing status-code lists.

## 1. Why is a timeout ambiguous?

A timeout only tells the client that it did not receive a response before its deadline. It does not prove that the server did nothing. The request may not have arrived, may still be processing, may have completed with a lost response, or may have failed after an external side effect.

For a payment or order, the client must treat the result as unknown until it retries safely or reconciles the operation.

## 2. Why can blind retries be dangerous?

Non-idempotent operations such as `POST /payments` or order creation can create duplicate business effects. If the first request succeeded but its response was lost, a blind retry can charge the customer twice or create two orders.

Do not solve this by simply telling clients never to retry. Networks fail; instead, make retries safe with idempotency and bounded retry policies.

## 3. How does an idempotency key work?

An idempotency key identifies one logical operation across all attempts. The server stores the key with:

- client or account scope;
- endpoint or operation;
- request fingerprint;
- processing status;
- final response or result reference;
- timestamps and expiry information.

Typical flow:

```
NEW -> PROCESSING -> COMPLETED
                 └-> FAILED
```

A completed key replays the stored response. A key currently being processed may return `409 Conflict`, `202 Accepted`, or a status response, depending on the API contract.

Retries must reuse the same key. A new key means a new logical operation.

## 4. What if the same key is reused with a different body?

Reject it. Compare a fingerprint of the method, path, and relevant request body with the stored fingerprint. Return `409 Conflict` or `422 Unprocessable Content` with a clear error such as:

```
Idempotency key already used with different parameters
```

Never process the new body and never replay the old response for a different operation.

## 5. Why is check-then-insert unsafe?

This sequence is racy:

```
if key_not_found(key):
    create_order()
    insert_key(key)
```

Two requests can both observe that the key is absent before either inserts it. This is a time-of-check to time-of-use race. A transaction alone does not automatically fix the race under common isolation levels.

Use a database unique constraint and make the claim itself atomic:

```
INSERT INTO idempotency_keys (...)
VALUES (...)
ON CONFLICT (client_id, key) DO NOTHING;
```

One inserted row means the caller won the claim. Zero rows means another request already owns the key.

## 6. What should concurrent duplicate requests receive?

| Key state | Typical behavior |
|---|---|
| New | Atomically claim and process |
| Processing | Return conflict/status, or wait briefly according to the contract |
| Completed | Replay the original status and response |
| Same key, different fingerprint | Reject with `409` or `422` |

Replaying the original response is important: a client retry should converge on the same order or payment result.

## 7. Why are permanent `PROCESSING` records dangerous?

If a worker crashes after claiming a key, every later request may see `PROCESSING` forever. The operation becomes stuck, clients cannot know whether it succeeded, and external effects may remain uncertain.

Use a lease with an expiry time and heartbeat renewal. A recovery worker may reclaim an expired lease only after an atomic compare-and-set operation.

Use the database clock for lease comparisons to avoid machine clock skew.

## 8. What are fencing tokens?

A lease can expire while the old worker is merely paused rather than dead. A fencing token is a monotonically increasing ownership number issued on every claim or reclaim.

Every state update includes the worker's token. A stale worker's update affects zero rows because the database now contains a newer token. This prevents a zombie worker from overwriting the new owner's result.

Fencing protects your database state. It cannot undo an external call already sent, so downstream idempotency and reconciliation are still required.

## 9. Which failures should be retried?

| Failure | Default decision |
|---|---|
| `400`, validation error | Do not retry; fix the request |
| `401` | Refresh credentials, then retry only if appropriate |
| `403` | Usually do not retry without a permission change |
| `404` | Usually do not retry; eventual-consistency cases may justify a short bounded retry |
| `429` | Retry after `Retry-After` or bounded backoff |
| `503`/`504` | Retry with backoff if the operation is safe and the deadline allows |
| Database deadlock/serialization failure | Roll back and retry the complete transaction, bounded |
| Network timeout | Treat outcome as ambiguous; use idempotency or reconcile first |

Status code alone is not enough. Ask both: can the failure recover, and is repeating the operation safe?

## 10. Retry storms and failure containment

A retry storm occurs when failures trigger enough retries to keep the dependency overloaded. Retries can also multiply across service layers.

Use:

- exponential backoff to slow attempts;
- jitter to avoid synchronized retry waves;
- retry budgets to cap aggregate retry volume;
- maximum attempts and an overall deadline;
- one retrying layer where possible;
- circuit breakers to fail fast when a dependency is clearly unhealthy;
- rate limiting, bulkheads, and load shedding to protect capacity.

Backoff controls timing, jitter spreads timing, retry budgets control volume, and circuit breakers stop calls during an outage.

## 11. Database transactions versus external side effects

A database rollback can undo database writes, but it cannot undo a payment, email, webhook, or upload automatically.

Keep database transactions short. Use idempotent downstream calls, transactional outbox events, compensating actions, and reconciliation for uncertain external outcomes. Model uncertainty explicitly, for example with `PAYMENT_UNKNOWN`, rather than falsely reporting failure.

## Common mistakes

- Retrying every exception.
- Generating a new idempotency key for every retry.
- Treating a timeout as proof that no work happened.
- Using an in-memory idempotency dictionary in a multi-instance service.
- Checking and inserting the idempotency record in separate unsafe steps.
- Ignoring a request-body mismatch for a reused key.
- Retrying after the deadline has expired.
- Retrying only one statement inside an aborted transaction.
- Assuming a database rollback reverses an external side effect.
- Using leases without fencing or downstream idempotency.

## Interview answer structure

When answering a production failure question, use this sequence:

1. Classify the failure as transient, permanent, or ambiguous.
2. State whether the operation is safe to repeat.
3. Explain the idempotency or deduplication mechanism.
4. Define bounded retries, backoff, jitter, and deadlines.
5. Explain reconciliation or recovery when the outcome is uncertain.
6. State what happens after the retry budget is exhausted.