# Interview Questions — Database Sessions and Connection Pools

This file focuses on production reasoning rather than memorising driver-specific APIs.

## 1. What is a database connection?

A database connection is a live communication channel between an application and a database. For a remote database, it commonly includes a network connection such as TCP, database-protocol messages exchanged as bytes, authentication state, and server-side resources.

A connection is not the same as an HTTP connection. The database driver speaks the database wire protocol, not HTTP.

## 2. What is a database session?

A database session is the database-side context associated with an authenticated connection. It may remember the authenticated role, selected database, transaction state, session settings, temporary tables, prepared statements, and locks held by the session.

A simple analogy: connection = telephone line; session = the conversation and context held over that line.

## 3. What is a connection pool?

A connection pool is a managed set of reusable database connections. A request generally checks out a connection, performs database work, commits or rolls back, resets request-specific state, and returns the connection to the pool.

Pooling avoids creating a new network connection for every request and provides a concurrency limit for database work.

## 4. What happens when all pool connections are busy?

The request waits for a connection until the configured checkout timeout expires. If no connection becomes available, the pool raises a pool-specific error such as PoolTimeout.

Possible causes include traffic exceeding pool capacity, long-running queries or transactions, connections not being returned, a pool that is too small, or slow replacement of broken connections.

A pool timeout is different from a database connection failure and from a slow query:

- pool timeout: the request could not obtain a connection;
- connection failure: a connection could not be created or became unusable;
- slow query: the request obtained a connection, but SQL execution is taking too long.

## 5. What is the correct request/connection lifecycle?

1. The request checks out a connection.
2. The driver sends SQL and receives the result.
3. A successful write transaction is committed.
4. An exception causes a rollback attempt.
5. The connection is reset and returned to the pool.
6. A broken or expired connection is discarded instead of being reused.

Never return a connection while it has an unfinished transaction or request-specific state.

## 6. Why is returning a connection with an open transaction dangerous?

Suppose Request A updates a product and fails before committing, then returns the connection without rollback. Request B receives that connection.

Request B may accidentally commit Request A's changes, observe Request A's uncommitted state on the same connection, inherit locks that cause blocking or deadlocks, or inherit session settings and temporary state.

The pool contract requires each returned connection to be clean and neutral.

## 7. What is the difference between min_size and max_size?

- min_size is the baseline number of connections the pool tries to keep available.
- max_size is the maximum number of connections the pool may use.

A small min_size reduces idle resource usage but may cause connection creation during a traffic spike. A large min_size consumes database resources even during low traffic.

A large max_size does not necessarily create that many connections immediately; many pools create connections lazily. However, it allows that many connections to exist under load.

Setting min_size equal to max_size creates a mostly fixed-size pool: if the value is too small, requests wait during spikes; if it is too large, every pod may keep unnecessary idle connections.

## 8. How should pool size be calculated across pods?

Pool capacity is per application instance, while the database limit is global.

    maximum application connections =
    maximum pod count × max_size per pod

For example, 10 pods × 6 connections = 60 application connections.

The calculation must also leave capacity for other services, background workers, migrations, monitoring, administrative access, database-reserved connections, and operational headroom.

Do not size only for the current replica count if autoscaling can add more pods.

## 9. Why does a connection need a maximum lifetime?

A maximum lifetime retires a connection after a configured age, even if it appears healthy. This limits problems caused by stale firewall, NAT, proxy, or load-balancer state; database restarts or failovers; accumulated session state; long-lived driver or network problems; and credential or certificate rotation.

Pools normally retire connections gradually after they are returned, rather than interrupting an active query. Jitter can prevent every pod from reconnecting at the same time.

## 10. What is the purpose of a health check?

A health check helps the pool detect a broken idle connection before handing it to a request. If the check fails, the pool discards the connection and replaces it.

However, a health check is only a point-in-time observation. The database can fail immediately after the check and before the next SQL statement.

If a connection fails while in use:

1. the driver reports the error;
2. the application attempts rollback if possible;
3. the pool discards the broken connection;
4. the application retries only if the operation is safely retryable.

The pool cannot transparently repair an active connection in the middle of a query.

## 11. Does a pool automatically retry a failed SQL query?

Usually, no. A pool manages connection lifecycle; it should not blindly repeat SQL because a write may already have executed before the response was lost.

The application or data-access layer decides whether the error is retryable, whether the operation is idempotent, how many attempts are allowed, the backoff and deadline, and what response to return after exhaustion.

The pool may provide another healthy connection, but the application must explicitly retry the operation.

## 12. How should an idempotent operation be retried?

If a connection fails before SQL is sent, the operation probably did not execute.

If the connection fails after SQL was sent, the result is ambiguous: the database may have committed the operation even though the client did not receive the response.

For a safely idempotent read or write:

- obtain a new connection;
- retry a bounded number of times;
- use exponential backoff with jitter;
- enforce an overall request deadline;
- stop and return a temporary failure if recovery fails.

For non-idempotent writes, use an idempotency key, a unique business key, or another deduplication mechanism before retrying.

## 13. What should happen when max_size is increased but the database reaches 100% CPU?

This indicates that the database, not the application pool, is the bottleneck. Increasing the pool removed application-side waiting but added more concurrent work to the database.

Recommended actions:

1. reduce or cap pool size to restore backpressure;
2. inspect query plans, indexes, N+1 queries, and transaction scope;
3. check locks, database sessions, CPU, memory, and I/O;
4. consider caching, batching, read replicas, or workload shedding;
5. scale the database vertically only after confirming the workload is efficient.

A connection pool is also a concurrency-control mechanism. A larger pool does not make the database faster.

## 14. Which production metrics should be monitored?

### Pool capacity

- active/in-use connections;
- idle connections;
- waiting requests;
- pool utilization;
- min_size and max_size.

### Acquisition

- connection checkout latency;
- PoolTimeout count;
- connection creation failures;
- replacement count.

### Connection health

- health-check failures;
- broken or expired connections;
- connection age;
- database connection errors;
- total database sessions.

### Query and transaction behavior

- query execution latency;
- slow-query count;
- transaction duration;
- rollback count;
- lock-wait time;
- deadlocks.

Compare SQL execution time with connection-hold time. A request may hold a connection for a long time while doing non-database work.

## 15. How would you investigate increasing PoolTimeout errors?

Do not immediately increase max_size. First investigate:

1. whether all connections are active;
2. whether requests hold connections longer than expected;
3. whether transactions remain open;
4. whether queries or lock waits are slow;
5. whether traffic is unevenly distributed across pods;
6. whether the database has capacity for more connections;
7. whether connections are leaking or failing replacement.

If the pool is saturated but the database is already at high CPU, increasing the pool may worsen the outage.

## Common mistakes

- Treating a pool as an unlimited performance improvement.
- Assuming max_size means that many connections are opened immediately.
- Confusing a pool checkout timeout with a slow SQL query.
- Returning a connection without commit or rollback.
- Retrying every failed SQL statement automatically.
- Assuming a successful health check guarantees the next query will succeed.
- Sizing each pod independently without calculating the global maximum.
- Setting every pool to the database's entire connection limit.
- Holding a database connection while calling a slow external service.
- Ignoring non-application consumers of database connections.
- Assuming the pool can redirect an already-running request away from a broken connection.
