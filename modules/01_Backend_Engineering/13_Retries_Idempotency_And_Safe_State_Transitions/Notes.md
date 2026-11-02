# When Operations Repeat or Fail

## Why this topic matters

Distributed operations can fail in ambiguous ways:

- a network connection can break after the server processed the request;
- a dependency can time out even though it is still working;
- a worker can crash after a side effect but before acknowledging the message;
- a response can be lost after a database commit.

The caller often cannot immediately know whether the operation happened.

This creates the central production question:

> Should the application retry, and how can it retry without duplicating a business action?

## 1. Failure types

### Transient failures

A transient failure may succeed if attempted again later.

Examples:

- temporary network failure;
- connection reset;
- service temporarily unavailable;
- rate limiting;
- database deadlock;
- serialization failure;
- overloaded dependency.

Retries may be appropriate, but should be bounded and delayed.

### Permanent failures

A permanent failure will probably produce the same result if repeated.

Examples:

- invalid input;
- authentication failure;
- authorization failure;
- resource does not exist;
- unsupported operation;
- violated business rule.

Do not retry these blindly.

### Ambiguous outcomes

A timeout does not always mean the operation failed.

For example:

1. Client sends a payment request.
2. Payment service charges the card.
3. Network response is lost.
4. Client receives a timeout.
5. Client does not know whether the charge succeeded.

Blindly sending the payment request again could charge the customer twice.

## 2. What is a retry?

A retry is another attempt to perform the same logical operation after a failure.

A production retry policy should define:

- which errors are retryable;
- maximum attempts;
- total time or deadline;
- delay between attempts;
- exponential backoff;
- random jitter;
- what happens when attempts are exhausted.

A retry should repeat the **complete logical operation**, not just an arbitrary statement inside a failed transaction.

## 3. Backoff and jitter

Retrying immediately can create a retry storm. Many clients may fail together and retry together, producing even more load.

### Exponential backoff

Increase the delay after each failed attempt:

    attempt 1 -> wait 100 ms
    attempt 2 -> wait 200 ms
    attempt 3 -> wait 400 ms

The exact values depend on the operation and SLA.

### Jitter

Add a small random delay so clients do not retry at exactly the same time.

    delay = exponential_backoff + random_jitter

Backoff gives the dependency time to recover. Jitter prevents synchronized retries.

## 4. What is idempotency?

An operation is idempotent when repeating the same logical request produces the same business result as performing it once.

Examples:

- setting an address to a specific value can be idempotent;
- deleting an already-deleted resource can be treated as idempotent;
- creating an order is not naturally idempotent because repeating it may create two orders;
- charging a payment is not naturally idempotent.

HTTP method semantics can help, but HTTP method alone does not guarantee application-level idempotency. A POST operation can be made safely repeatable with an idempotency key.

## 5. Idempotency keys

An idempotency key is a client-generated or server-generated unique identifier for one logical operation.

Example:

    POST /payments
    Idempotency-Key: payment-attempt-8f2c

The server stores the key together with:

- operation or endpoint;
- request fingerprint;
- processing status;
- response or result reference;
- timestamps;
- expiry;
- error information when appropriate.

### Typical behavior

1. First request arrives with a new key.
2. Server records the key as PROCESSING.
3. Server performs the operation.
4. Server stores the final result as COMPLETED or FAILED.
5. Repeated request with the same key returns the stored result instead of executing the side effect again.

A repeated key with a different request body should be rejected because the key must represent one logical operation.

## 6. Idempotency state machine

    NEW -> PROCESSING -> COMPLETED
                     └-> FAILED
                     └-> EXPIRED

If another request arrives while the key is PROCESSING, the server may:

- return a conflict;
- wait briefly for the original operation;
- return the current operation status.

If the key is COMPLETED, return the original response or result reference.

The key and result record must be stored in a shared durable store when multiple application instances are involved. An in-memory dictionary is insufficient because it disappears on restart and is not shared across replicas.

## 7. Safe retry decision

Before retrying, ask:

1. Is the failure likely transient?
2. Is the operation safe to repeat?
3. Is there an idempotency key or another deduplication guarantee?
4. Is the deadline still valid?
5. Could the dependency already have completed the operation?
6. Will the retry increase overload?
7. Is the request within the retry budget?

### Examples

| Operation | Failure | Retry decision |
|---|---|---|
| Read product | temporary connection failure | Usually retry with bounded backoff |
| Create order with idempotency key | timeout | Retry using the same key |
| Charge payment without idempotency support | timeout | Do not blindly retry; reconcile first |
| Invalid request | validation error | Do not retry |
| Database deadlock | transaction aborted | Retry the complete transaction if bounded |
| HTTP 429 | rate limit | Retry after the server's guidance if deadline allows |
| HTTP 404 | resource absent | Usually do not retry |

## 8. Safe state transitions

Business state should move through explicit valid transitions.

Example order flow:

    CREATED -> PAYMENT_PENDING -> PAID -> FULFILLING -> COMPLETED
                  └-> PAYMENT_FAILED
                  └-> CANCELLED

A worker should update state conditionally:

    UPDATE orders
    SET status = 'PAID'
    WHERE id = :order_id
      AND status = 'PAYMENT_PENDING';

If no row is updated, another worker may have already changed the order or the transition is no longer valid.

This prevents stale workers from overwriting newer business state.

## 9. Transactions and external side effects

A database transaction can roll back database changes, but it cannot roll back an external payment, email, or webhook automatically.

Avoid this unsafe pattern:

    open database transaction
    call payment provider
    call email provider
    commit database transaction

If the database commit fails after payment succeeds, the systems disagree.

Safer designs include:

- short database transactions;
- transactional outbox for reliable event publication;
- idempotent external calls;
- compensating actions such as refunds;
- reconciliation jobs for uncertain outcomes;
- explicit states such as PAYMENT_UNKNOWN.

## 10. Retry budgets and failure containment

Retries consume resources. A production system should limit:

- attempts per operation;
- total retry time;
- concurrent retries;
- queue retry depth;
- retry rate per dependency.

After the retry budget is exhausted:

- return or record a clear failure;
- send the job to a dead-letter queue when applicable;
- expose a correlation ID;
- alert operators when the failure rate is abnormal.

Retries should be combined with timeouts, circuit breakers, rate limits, and bulkheads so one failing dependency does not consume all application capacity.

## Common mistakes

- Retrying every exception.
- Retrying a non-idempotent operation without a key.
- Generating a new idempotency key for every retry.
- Retrying immediately with no backoff or jitter.
- Retrying only one SQL statement inside an already-aborted transaction.
- Treating a timeout as proof that the operation did not happen.
- Storing idempotency keys only in process memory.
- Ignoring request-body mismatches for reused keys.
- Retrying after the deadline has already expired.
- Assuming a database rollback can undo an external side effect.

## Mental model

Use this order:

1. Classify the failure: transient, permanent, or ambiguous.
2. Check whether the operation is safe to repeat.
3. Reuse the same idempotency key when retrying one logical operation.
4. Retry the complete transaction or workflow with bounded backoff and jitter.
5. Reconcile uncertain external outcomes.
6. Stop after the retry budget and expose a recoverable state.
