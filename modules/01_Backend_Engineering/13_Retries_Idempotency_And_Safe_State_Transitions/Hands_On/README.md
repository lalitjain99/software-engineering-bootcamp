# Topic 13 Hands-On Lab

## Retries, Idempotency, and Safe State Transitions

Build a small Python simulation of a payment/order operation that can be retried safely.

## Learning objectives

- classify transient, permanent, and ambiguous failures;
- calculate bounded exponential backoff with jitter;
- claim an idempotency key atomically;
- replay a completed response instead of repeating a side effect;
- reject reuse of a key with a different request fingerprint;
- model a stuck `PROCESSING` record and lease recovery;
- use a fencing token to prevent stale workers from completing work.

## Setup

Requirements: Python 3.11+ and the standard library only.

```
cd modules/01_Backend_Engineering/13_Retries_Idempotency_And_Safe_State_Transitions/Hands_On
python main.py
```

No real payment provider or network call is used. The lab deliberately uses an in-memory store to make the concurrency behavior visible. In production, replace it with a shared durable store and database constraints.

## Exercise 1 — Retry policy

Implement or inspect a retry helper that:

1. retries only transient failures;
2. uses exponential backoff plus jitter;
3. stops after a maximum attempt count and total deadline;
4. does not retry validation or authorization failures.

Record at least one example of a retryable and non-retryable failure.

## Exercise 2 — Duplicate requests

Run two concurrent calls with the same idempotency key. Verify:

- only one request performs the simulated side effect;
- the duplicate does not create a second order/payment;
- a completed duplicate receives the stored response;
- a duplicate with a different payload is rejected.

## Exercise 3 — Lease recovery

Simulate a worker that claims a key and crashes before completion. Verify:

- the key does not remain blocked forever;
- a lease expires;
- a recovery worker can reclaim it atomically;
- the reclaim increments the fencing token;
- a stale worker cannot write the final result.

## Exercise 4 — Explain the production gap

After running the simulation, write down which parts would need a real database or queue in production:

- unique constraint;
- transaction boundary;
- durable idempotency response storage;
- lease and fencing update;
- downstream provider idempotency;
- reconciliation and alerting.

## Expected evidence

Capture the following in `observations.md`:

- command used to run the lab;
- output showing one side effect for duplicate requests;
- output showing mismatch rejection;
- output showing lease reclaim and stale-worker rejection;
- explanation of how the simulation differs from production;
- one design decision you would make for a payment API.