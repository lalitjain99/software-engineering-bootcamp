# Observations

## 1. Pool maximum

The pool's maximum number of connections is **2**.

This is configured with:

```python
SimulatedPool(min_size=2, max_size=2, checkout_timeout=0.15)
```

## 2. Why does one worker receive a checkout timeout?

Two requests already checked out both available connections and held them for longer than the configured checkout timeout.

The third request waited for an available connection. Because neither connection was returned within 0.15 seconds, the request failed with a `PoolTimeout`.

## 3. Idle versus in-use connections

An **idle connection** is an open, healthy connection that is currently available in the pool for another request.

An **in-use connection** has been checked out by a request. It may be actively executing SQL or may be temporarily waiting while the request still holds it.

The important distinction is whether the connection is available for other requests.

## 4. Commit and rollback behavior

The transaction in `request-A` is committed. It:

1. Starts a transaction.
2. Executes `UPDATE products SET price = 2400 WHERE id = 101`.
3. Calls `commit()`.

The transaction in `request-B` is rolled back. It:

1. Starts a transaction.
2. Attempts to insert `KEY-101`.
3. Raises a simulated `ValueError`.
4. Is rolled back by the pool context manager before the connection is returned.

This demonstrates the rule:

```text
Success → commit
Failure → rollback
```

## 5. What happens to the broken connection?

The pool does not return the broken connection to the available pool.

It discards the broken connection and creates a replacement connection, while maintaining the configured pool limit.

## 6. Why does the replacement connection receive a new ID?

The ID is only a teaching aid used by the simulation to show that a new physical connection was created.

In a real application, a replacement connection would also represent a new database session and would need to authenticate again. Application code normally does not depend on a connection ID.

## 7. What happens if the checkout timeout is increased?

Requests can wait longer for an available connection before receiving a `PoolTimeout`.

This may help when a connection will become available shortly. However, it does not increase pool capacity or database performance. If the pool remains exhausted, increasing the timeout only makes requests wait longer and increases their latency.

## 8. What production behavior does this simulation simplify?

The simulation demonstrates:

1. A pool enforcing a maximum connection limit.
2. Requests waiting when all connections are busy.
3. A checkout timeout when no connection is returned in time.
4. Commit on success and rollback on failure.
5. Broken-connection disposal and replacement.
6. Connections becoming available again after the request finishes.

A real pool also handles database authentication, TCP/TLS, database-protocol messages, health checks, connection lifetime, transaction reset, and database-specific errors.

## 9. Why should application code avoid holding a connection while calling an external service?

A database connection is a scarce shared resource. If application code keeps a connection checked out while waiting for an external API or another slow dependency:

- the connection remains unavailable to other requests;
- pool utilization increases;
- request latency increases;
- other requests may receive `PoolTimeout`.

The application should perform the required database work, release the connection as soon as it is safe, and then call the external service where possible. If the database transaction and external call must be coordinated, the design needs an explicit reliability pattern rather than holding the connection indefinitely.

## 10. Why would increasing `max_size` not necessarily improve performance?

Increasing `max_size` only permits more concurrent database work. It does not make each query faster.

If the database, application, or network is already saturated, additional connections can cause:

- higher CPU and memory usage;
- lock contention;
- more context switching;
- increased query latency;
- database connection exhaustion.

In production, pool size should be increased only after checking database capacity, query performance, transaction duration, and the total number of connections across all pods.

## Key learning

A connection pool provides reusable connections and controls database concurrency. It is not an unlimited performance booster.

The basic lifecycle is:

```text
Borrow → use → commit/rollback → reset → return
```
