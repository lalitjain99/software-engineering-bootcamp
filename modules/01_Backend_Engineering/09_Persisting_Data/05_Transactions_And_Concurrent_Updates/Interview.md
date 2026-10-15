# Topic 09.05 — Transactions and Concurrent Updates: Interview Guide

This guide is based on the chat-based interview practice for transactions, concurrency, locking, isolation, retries, and production diagnosis.

---

## 1. Why should order creation use one database transaction?

An order workflow may create an order row, create order items, reserve inventory, and save a payment record. These database changes represent one business operation and should normally commit together or roll back together.

If each step commits independently, partial failures can create:

- an order without inventory reservation;
- reduced inventory without a payment record;
- incomplete order data visible to other requests;
- difficult reconciliation and financial inconsistencies.

The transaction provides atomicity for the database changes.

Important qualification: an external payment-provider call cannot be rolled back by a database transaction. Use an outbox, workflow, or saga for external side effects.

---

## 2. What concurrency problem occurs when two requests reserve the last item?

This is a check-then-act race condition that can produce a lost update and overselling.

~~~text
Initial stock = 1

Request A reads stock = 1
Request B reads stock = 1

Both pass the application check.
Both attempt to reserve one item.
~~~

The reads and writes are separate database operations. Neither request coordinates with the other during the gap between checking and updating.

The database may finally show stock 0, while two successful reservations or orders exist. The important business invariant is violated.

---

## 3. Why is this code unsafe?

~~~python
product = repository.get_product(product_id)

if product.stock >= quantity:
    product.stock -= quantity
    repository.save(product)
~~~

The check occurs in Python memory, not atomically with the database update.

Each request can receive its own copy of the product with stale stock. Both requests may pass the check before either write becomes visible. The application must use an atomic conditional update, pessimistic locking, or optimistic version checking.

---

## 4. How does an atomic conditional update prevent overselling?

Use one SQL statement that checks and changes the row together:

~~~sql
UPDATE products
SET stock = stock - :quantity
WHERE id = :product_id
  AND stock >= :quantity;
~~~

Then inspect the affected-row count:

- 1 row updated → reservation succeeded;
- 0 rows updated → the product is missing or stock is insufficient.

The condition and update are evaluated atomically by the database.

If the API must distinguish “product not found” from “insufficient stock,” it may perform a follow-up read. Some APIs return a generic 409 Conflict instead.

Atomic updates still use short-lived database concurrency control internally. Their advantage is avoiding a long application-level read-check-write sequence.

---

## 5. What is pessimistic locking?

Pessimistic locking assumes a conflict is likely, so the transaction locks the row before making its decision.

~~~sql
BEGIN;

SELECT id, stock
FROM products
WHERE id = :product_id
FOR UPDATE;

-- Check stock and update it.

COMMIT;
~~~

A competing transaction attempting a compatible locking operation normally waits until the first transaction commits or rolls back. Under MVCC, an ordinary non-locking read may still see the last committed version.

Benefits:

- useful for complex multi-step decisions;
- protects a critical row while the transaction evaluates it;
- gives the application a fresh state after it obtains the lock.

Risks:

- waiting and lock contention;
- connection-pool pressure;
- deadlocks when multiple rows are locked in inconsistent order;
- long-held locks if slow work occurs inside the transaction.

Pessimistic locking does not automatically prevent every race. All relevant code paths must follow compatible locking or conditional-update rules.

---

## 6. What is optimistic locking?

Optimistic locking assumes conflicts are uncommon. The application reads a version and checks that it has not changed before saving.

Example row:

~~~text
stock = 1
version = 5
~~~

Update:

~~~sql
UPDATE products
SET stock = :new_stock,
    version = version + 1
WHERE id = :product_id
  AND version = :old_version;
~~~

If the first transaction updates version 5, the row becomes version 6.

A second transaction still using version 5 affects zero rows. This means its data is stale or the row no longer exists.

The application should:

1. end or roll back the current transaction;
2. reload the latest row;
3. re-evaluate the business rule;
4. retry if safe, or return 409 Conflict.

It must not silently overwrite the newer update.

---

## 7. Compare atomic, pessimistic, and optimistic approaches

| Approach | Competing request | Main strength | Main cost | Good fit |
|---|---|---|---|---|
| Atomic conditional update | Fails quickly when the condition is false | Efficient for simple invariants | Logic must be expressed in SQL | High-throughput stock decrement |
| Pessimistic locking | Waits for the row lock | Useful for complex multi-step decisions | Blocking and possible deadlocks | Critical multi-row workflows |
| Optimistic locking | Detects stale version and retries or fails | Good concurrency when conflicts are uncommon | Application must handle conflicts | Admin editing and low-conflict updates |

No approach is universally best. Choose based on conflict frequency, transaction duration, business criticality, retry safety, and database behavior.

---

## 8. What are Read Committed, Repeatable Read, and Serializable?

### Read Committed

Each statement sees data committed before that statement begins.

~~~text
Transaction B:
1. Reads stock = 10.

Transaction A:
1. Changes stock to 3.
2. Commits.

Transaction B:
1. Reads the same row again.
2. May now see stock = 3.
~~~

This prevents dirty reads, but repeated statements in one transaction may see different committed values. This is a non-repeatable read.

### Repeatable Read

The transaction gets a stable view of rows it has already read.

~~~text
Transaction B reads stock = 10.
Transaction A changes stock to 3 and commits.
Transaction B reads again and continues seeing stock = 10.
~~~

The exact implementation differs by database. Many databases use an MVCC snapshot rather than physically locking every row.

The application may receive a conflict if it later tries to update data changed by another transaction.

### Serializable

Serializable provides the strongest common isolation guarantee. Concurrent transactions behave as if they ran in a serial order.

~~~text
Initial stock = 1

Transaction A and B both try to reserve it.
One transaction succeeds.
The other is blocked or aborted with a serialization conflict.
~~~

The application must retry the complete transaction when the operation is safely retryable.

Trade-offs include more blocking, serialization failures, deadlocks, lower throughput, and additional retries.

---

## 9. What is a dirty read?

A dirty read occurs when a transaction reads another transaction's uncommitted change.

~~~text
Initial balance = ₹10,000

Transaction A temporarily changes balance to ₹6,000.
Transaction B reads ₹6,000.
Transaction A rolls back.
Actual balance returns to ₹10,000.
~~~

Transaction B used a value that never became permanent.

Dirty reads can cause incorrect balances, false inventory decisions, invalid reports, and customers seeing orders or payments that later disappear.

Production systems generally use Read Committed or stronger isolation. PostgreSQL does not provide true dirty reads even when Read Uncommitted is requested; it effectively uses Read Committed behavior.

---

## 10. What is lock contention?

Lock contention occurs when multiple transactions need the same locked resource and one must wait.

~~~text
Transaction A locks Product 101.
Transaction B also needs Product 101.
Transaction B waits for A to commit or roll back.
~~~

The system can still progress, but waiting increases latency and reduces throughput.

Common causes:

- long-running transactions;
- many concurrent writes to one hot row;
- locking more rows than necessary;
- slow processing while a transaction is open.

---

## 11. What is a deadlock?

A deadlock occurs when transactions wait for one another in a cycle.

~~~text
Transaction A locks Product 101.
Transaction B locks Product 202.

Transaction A requests Product 202 and waits for B.
Transaction B requests Product 101 and waits for A.
~~~

Neither transaction can continue. The database detects the cycle and aborts one transaction, releasing its locks so the other can proceed.

The application should catch the transient error and retry the complete operation in a fresh transaction, using bounded backoff and jitter when safe.

---

## 12. How can deadlocks be reduced?

Use a global lock-ordering rule.

~~~text
Always lock product IDs in ascending order.

[101, 202] is used by every transaction,
regardless of the order in the user's cart.
~~~

If every transaction locks resources in the same order, the circular-wait pattern is avoided.

Additional practices:

- keep transactions short;
- lock only required rows;
- use appropriate indexes;
- avoid external calls inside transactions;
- use atomic conditional updates for simple rules;
- use optimistic locking where conflicts are uncommon;
- set sensible lock and statement timeouts.

---

## 13. Should deadlock or serialization failures be retried?

Usually yes, because they are often transient. The retry must:

1. roll back or discard the failed transaction;
2. obtain a clean session or connection;
3. rerun the complete transaction;
4. use a limited number of attempts;
5. apply exponential backoff and jitter;
6. stop when the request deadline is reached.

Do not retry only the final SQL statement inside an aborted transaction.

The retry is unsafe when it repeats an unprotected external side effect such as charging a card or sending an email. Use idempotency keys and an outbox/workflow design for such operations.

---

## 14. Why should external calls not occur inside a database transaction?

A database rollback can undo database changes, but it cannot undo:

- a payment-provider charge;
- an email already sent;
- an HTTP request already received by another service.

Calling external services inside the transaction also holds the database connection and locks while waiting on unpredictable network I/O.

Use a transactional outbox:

~~~text
Short database transaction:
  create order
  reserve inventory
  create payment-pending state
  write PaymentRequested outbox event
  commit

Background worker:
  read outbox event
  call payment provider with an idempotency key
  save payment result
  publish email event
~~~

Use explicit states such as PENDING, SUCCEEDED, FAILED, and REFUND_REQUIRED.

---

## 15. How would you test concurrent reservations?

Create one product with:

~~~text
product_id = 101
stock = 1
~~~

Start two reservation requests concurrently using separate workers, synchronized with a barrier or event.

Expected outcome:

- exactly one request succeeds;
- the other receives a conflict response;
- final stock is 0;
- exactly one successful reservation exists;
- stock never becomes negative.

Repeat the test many times and monitor:

- successful reservations;
- conflict responses;
- deadlocks;
- serialization failures;
- retries;
- transaction duration;
- final inventory state.

For realistic results, run concurrency tests against the same database engine and transaction configuration used in production. SQLite is useful for learning but does not reproduce every PostgreSQL or MySQL concurrency behavior.

---

## 16. How would you diagnose rising latency, pool timeouts, lock waits, and deadlocks?

Correlate metrics across the API, connection pool, database, and infrastructure.

Check:

- connection acquisition time;
- SQL execution time;
- lock-wait time;
- transaction duration;
- active and idle connections;
- PoolTimeout count;
- blocked and blocking database sessions;
- deadlock and serialization errors;
- database CPU, memory, disk I/O, and connection count.

Useful PostgreSQL sources include pg_stat_activity, pg_locks, wait events, and pg_stat_statements.

Separate:

~~~text
connection acquisition time
lock-wait time
SQL execution time
application processing time
~~~

Examples:

- long SQL execution → query plan, indexes, joins, and scans;
- idle in transaction → transaction held open during application work;
- high lock wait with moderate CPU → hot rows or inconsistent lock ordering;
- pool timeouts with healthy database → pool capacity, leaks, or long connection hold time;
- high database CPU and broad latency increase → resource saturation or excessive concurrent work.

Do not increase the pool automatically. More connections may overload the database and worsen contention.

---

## 17. What happens if increasing pool size removes timeouts but saturates the database?

Increasing the pool removes an application-side limit and allows more concurrent requests to reach the database. It does not make the database faster.

The extra concurrency may cause:

- CPU thrashing;
- longer query execution;
- more lock contention;
- longer transactions;
- database connection exhaustion;
- cascading failures.

Protect the database with a safe concurrency limit, then investigate slow SQL, transaction duration, lock waits, connection leaks, and traffic volume. Use rate limiting, backpressure, or load shedding when demand exceeds capacity.

There is no universal pool-size formula. Consider database capacity, query type, number of application instances, and total connection limits.

---

## Common mistakes

- Assuming a transaction automatically prevents every concurrency race.
- Reading a value in Python and blindly overwriting it later.
- Assuming FOR UPDATE blocks every ordinary read.
- Claiming atomic updates eliminate all database locks.
- Holding a transaction open during payment, email, or other network calls.
- Retrying only the failed statement instead of the complete transaction.
- Retrying a deadlock without rollback and a fresh transaction.
- Retrying external side effects without an idempotency key.
- Treating every zero-row update as the same error without considering missing rows.
- Increasing pool size before diagnosing query time, transaction duration, or lock waits.
- Assuming stronger isolation is always better.
- Using inconsistent lock ordering across code paths.
- Assuming rollback can undo an email, payment, or message already sent.
- Returning success before the transaction commits.
