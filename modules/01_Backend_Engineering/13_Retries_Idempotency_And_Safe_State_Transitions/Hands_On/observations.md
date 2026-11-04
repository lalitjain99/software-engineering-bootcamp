# Topic 13 Hands-On Observations

## Run information

- Date:
- Python version:
- Command used:

## 1. Retry policy

- What failure did you classify as transient?
- What failure did you classify as permanent?
- How did backoff and jitter change retry timing?
- What bounded the retry behavior?

## 2. Duplicate idempotent requests

Paste the output showing two concurrent requests with the same key:

```
<!-- paste output here -->
```

- How many side effects were created?
- Which request claimed the key?
- What did the duplicate receive?

## 3. Completed replay

- What happened when the completed request was sent again?
- Why is replaying the stored response safer than creating a new order?

## 4. Fingerprint mismatch

- What happened when the same key was reused with a different amount?
- Which status would your real API return: `409` or `422`? Why?

## 5. Lease and fencing

Paste the output for the crashed worker, reclaim, and stale-worker behavior:

```
<!-- paste output here -->
```

- Why could the old worker not overwrite the reclaimed result?
- What would happen if the operation had already called a payment provider?

## 6. Production gap

List at least five changes required before using this design in production:

1.
2.
3.
4.
5.

## 7. Interview summary

Explain in 5–7 sentences why idempotency is necessary for retrying non-idempotent operations.