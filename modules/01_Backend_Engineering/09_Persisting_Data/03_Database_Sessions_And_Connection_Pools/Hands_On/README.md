# Hands-on: Simulating a Database Connection Pool

## Goal

Observe how a connection pool behaves when requests borrow and return reusable connections.

This lab does not connect to PostgreSQL. It uses Python's standard library and an asynchronous simulation so the pool behavior is easy to observe.

## Run

From this directory:

```bash
python main.py
```

Python 3.10+ is recommended.

## Scenarios

The script demonstrates:

1. Borrowing and returning connections.
2. Successful work with commit.
3. Failed work with rollback.
4. Requests waiting for a busy pool.
5. A checkout timeout when no connection becomes available.
6. Discarding a broken connection and creating a replacement.
7. Why a request should not hold a connection while doing unrelated work.

## Observe

While running the script, note:

- Which connection each request receives.
- When a request waits.
- Which request receives a checkout timeout.
- Whether a failed transaction is rolled back.
- Whether a broken connection is reused.
- How the pool creates a replacement connection.

## Exercises

After running the script, answer in `observations.md`:

1. What is the pool's maximum number of connections?
2. Why does one worker receive a checkout timeout?
3. What is the difference between an idle and an in-use connection?
4. Which transaction is committed and which is rolled back?
5. What happens to the broken connection?
6. Why is the replacement connection given a new ID?
7. What would happen if `checkout_timeout` were increased?
8. What production behavior does this simulation simplify?
9. Why should application code avoid holding a database connection while calling an external service?
10. Why would increasing `max_size` not necessarily improve performance?

## Important limitation

This is a teaching simulation, not a production connection pool. A real driver or pool also handles authentication, TCP/TLS, database protocol messages, health checks, connection lifetime, transaction reset, and database-specific errors.
