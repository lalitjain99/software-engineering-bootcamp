# Topic 09.05 — Transactions and Concurrent Updates

## Learning goal

Understand how a database keeps related changes consistent when requests succeed, fail, or run at the same time.

This topic builds on:

- SQL and database constraints;
- ORM sessions;
- connection pools;
- commits and rollbacks;
- production API request handling.

---

## 1. Why transactions are needed

Many business operations involve more than one database change.

For example, creating an order may require:

1. creating an order row;
2. creating order-item rows;
3. reducing inventory;
4. recording a payment attempt.

These changes belong to one business operation. If inventory is reduced but the order is not saved, the database is inconsistent.

A transaction groups related database operations:

~~~text
Begin transaction
    ↓
Create order
    ↓
Create order items
    ↓
Reduce inventory
    ↓
Commit all changes
~~~

If one operation fails:

~~~text
Begin transaction
    ↓
Some operations succeed
    ↓
One operation fails
    ↓
Rollback all uncommitted changes
~~~

The purpose is to prevent partial work from becoming committed state.

---

## 2. The four transaction properties: ACID

### Atomicity

All operations in the transaction succeed together, or none of them become committed.

~~~text
All changes commit
or
all changes roll back
~~~

Atomicity does not mean that every operation in the entire application is automatically included. The application must define the transaction boundary.

### Consistency

A committed transaction must preserve database rules and constraints.

Examples:

- foreign keys remain valid;
- unique values remain unique;
- CHECK constraints remain satisfied;
- application invariants enforced by the transaction remain valid.

Consistency depends on both database constraints and correct application logic.

### Isolation

Concurrent transactions should not interfere with each other in unsafe ways.

Isolation controls what one transaction can observe while another transaction is running.

Isolation does not always mean that transactions behave as if only one request exists. Different isolation levels provide different guarantees and trade-offs.

### Durability

After a successful commit, the database is responsible for preserving the committed changes despite normal process or machine failures, according to its durability configuration.

A commit response means the database accepted the transaction as committed. It does not mean every external system has also completed its work.

---

## 3. Transaction lifecycle

A simplified transaction lifecycle is:

~~~text
Connection/session obtained
    ↓
Begin transaction
    ↓
Execute one or more statements
    ↓
Commit on success
    ↓
Rollback on failure
    ↓
Release connection/session
~~~

Important rules:

- keep the transaction as short as practical;
- do not hold a database transaction while waiting for an external service unless the design explicitly requires it;
- always roll back after a database error before reusing the session;
- return the connection to the pool only after the transaction is complete.

---

## 4. Transaction boundary in an API

Suppose an API creates an order.

A reasonable transaction boundary may be:

~~~text
Request enters service
    ↓
Validate application input
    ↓
Begin database transaction
    ↓
Check customer
    ↓
Reserve inventory
    ↓
Create order
    ↓
Commit
    ↓
Return HTTP response
~~~

Validation that does not require the database should happen before opening the transaction.

External calls such as sending an email or calling a supplier should generally not occur inside the database transaction. If the external action must be coordinated with the database change, use a deliberate pattern such as an outbox or workflow rather than holding locks indefinitely.

---

## 5. What is a concurrent update?

A concurrent update occurs when two or more requests read or modify overlapping data at the same time.

Example:

~~~text
Initial stock = 10

Request A reads stock = 10
Request B reads stock = 10

Request A calculates 10 - 7 = 3
Request B calculates 10 - 6 = 4

Request A writes stock = 3
Request B writes stock = 4
~~~

The final value is 4, but 13 units were requested. The database has accepted both writes even though the business result is incorrect.

This is a **lost update**: one update overwrote the effect of another.

---

## 6. Why application-only checks are unsafe

This code is unsafe under concurrency:

~~~python
product = repository.get_product(product_id)

if product.stock >= quantity:
    product.stock -= quantity
    repository.save(product)
~~~

Two requests can both pass the stock check before either one saves the update.

The problem is not only Python code. The read and write are separate database actions, and another transaction can change the row between them.

A transaction alone may not solve this at the default isolation level. The application may also need a locking or conditional-update strategy.

---

## 7. Atomic conditional update

One approach is to make the condition and update a single database statement:

~~~sql
UPDATE products
SET stock = stock - :quantity
WHERE id = :product_id
  AND stock >= :quantity;
~~~

Then inspect the affected-row count:

- one row updated → reservation succeeded;
- zero rows updated → product does not exist or stock was insufficient.

This is often efficient because the database evaluates the condition and update atomically.

The application should not calculate the new stock value from an old Python object and then blindly overwrite the row.

---

## 8. Pessimistic locking

Pessimistic locking means:

> “Conflicting work is likely, so lock the row before changing it.”

Imagine that Product 101 has one item left.

~~~text
Transaction A locks Product 101.
Transaction B also wants Product 101, so B waits.
Transaction A updates the stock and commits.
Transaction B can then read the latest value.
~~~

The database lock is commonly acquired with:

~~~sql
SELECT id, stock
FROM products
WHERE id = :product_id
FOR UPDATE;
~~~

The selected row stays locked until the transaction commits or rolls back.

A second transaction may wait, time out, fail immediately with a no-wait option, or skip the row if the database supports that option.

Use pessimistic locking when:

- conflicting updates are likely;
- the operation is critical;
- waiting is safer than allowing both requests to proceed.

Cost:

- requests may wait;
- lock contention can reduce throughput;
- inconsistent lock order can create deadlocks.

Keep the transaction short. Do not call a slow external service while holding the lock.

---

## 9. Optimistic locking

Optimistic locking means:

> “Conflicts are probably uncommon, so do not lock while reading. Check for a conflict when saving.”

Add a version number to the row:

~~~text
Product 101
stock = 1
version = 5
~~~

Two transactions may both read version 5. When updating, each says:

> “Update this row only if it is still version 5.”

~~~sql
UPDATE products
SET stock = :new_stock,
    version = version + 1
WHERE id = :product_id
  AND version = :old_version;
~~~

The first update succeeds and changes the version from 5 to 6.

The second update affects zero rows because the version is no longer 5. The application detects the conflict and can reload the latest data, retry safely, or return a conflict response.

Interpret the affected-row count:

- one row updated → the version matched and the update succeeded;
- zero rows updated → another transaction changed the row first, or the row does not exist.

Use optimistic locking when:

- conflicts are uncommon;
- waiting would be undesirable;
- the application can handle a conflict explicitly.

Cost:

- the application must check for conflicts;
- a failed update may need a retry;
- it is not enough to silently overwrite the newer value.

---

## 10. Pessimistic versus optimistic locking

| Strategy | Simple meaning | What happens to the second request? | Main cost |
|---|---|---|---|
| Pessimistic locking | Lock first because a conflict may happen | It waits or fails while the row is locked | Blocking and possible deadlocks |
| Optimistic locking | Assume no conflict and check the version when saving | It fails safely if another request changed the row | Application must handle the conflict |
| Atomic conditional update | Put the condition and update into one SQL statement | The database reports success or zero affected rows | Best for simple rules, less suitable for complex workflows |

Memory aid:

> **Pessimistic locking prevents conflict by making other requests wait.**  
> **Optimistic locking detects conflict after another request has changed the row.**

The right choice depends on:

- conflict frequency;
- transaction duration;
- business criticality;
- acceptable client behavior;
- database capabilities;
- expected traffic.

## 11. Isolation levels

An isolation level controls what concurrent transactions can observe.

Common levels include:

- Read Uncommitted;
- Read Committed;
- Repeatable Read;
- Serializable.

Names and behavior vary slightly by database engine.

### Read Uncommitted

Read Uncommitted may allow a transaction to read changes made by another transaction before those changes are committed.

This creates a **dirty read**.

Example:

~~~text
Initial account balance = ₹10,000

Transaction A:
1. Withdraws ₹4,000.
2. Temporary balance becomes ₹6,000.
3. Has not committed yet.

Transaction B:
1. Reads the balance.
2. Sees ₹6,000.

Transaction A:
1. Encounters an error.
2. Rolls back.
3. Actual balance returns to ₹10,000.
~~~

Transaction B used a value that never became permanent.

Dirty reads are unsafe for production business decisions because they can cause:

- a customer to see a payment or order that later disappears;
- inventory logic to believe stock was reduced when the reservation is rolled back;
- a transfer service to make a decision using a temporary balance;
- reports to include values that never become real;
- a valid order to be rejected because another transaction temporarily changed the stock.

Production systems generally use Read Committed or stronger isolation so decisions are based on committed data.

Many modern databases do not provide true dirty reads even when Read Uncommitted is requested. For example, PostgreSQL effectively uses Read Committed behavior instead.

### Read Committed

Read Committed allows a transaction to read only data that other transactions have committed.

Example:

~~~text
Initial stock = 10

Transaction A:
1. Changes stock to 3.
2. Has not committed yet.

Transaction B:
1. Reads stock.
2. Cannot see A's uncommitted value.
3. Sees the last committed value: 10.

Transaction A:
1. Commits.
2. Stock is now officially 3.

Transaction B:
1. Reads the same product again.
2. May now see stock = 3.
~~~

This prevents dirty reads. However, the same transaction can see different values in two separate reads if another transaction commits between those reads. This is a **non-repeatable read**.

Read Committed is a common production default because it provides useful safety without the full cost of the strongest isolation.

### Repeatable Read

Repeatable Read gives a transaction a stable view of rows it has already read.

Example:

~~~text
Initial stock = 10

Transaction B:
1. Starts.
2. Reads stock = 10.

Transaction A:
1. Changes stock to 3.
2. Commits.

Transaction B:
1. Reads the same product again.
2. Continues seeing its transaction snapshot, stock = 10.
~~~

This prevents a previously read row from changing underneath Transaction B during its transaction.

The trade-off is that Transaction B may be working with an older snapshot. When it tries to update data that another transaction changed, the database may reject the update or the application may need to retry, depending on the database engine.

Repeatable Read is useful when several reads in one transaction must be consistent with one another.

### Serializable

Serializable provides the strongest common isolation guarantee. Concurrent transactions behave as if they had run one after another, rather than at the same time.

Example:

~~~text
Initial stock = 1

Transaction A and Transaction B both try to reserve the last item.

The database serializes the conflicting work:
1. One transaction reserves the item and commits.
2. The other transaction then runs against the latest state.
3. It finds stock = 0 and fails safely.
~~~

Serializable prevents dirty reads, non-repeatable reads, phantoms, and lost-update-style outcomes caused by unsafe interleaving. The database may achieve this by blocking, detecting conflicts, or aborting a transaction.

The cost may include:

- more waiting;
- serialization failures;
- deadlocks;
- lower throughput;
- application retries.

A serializable transaction failure is usually transient. The application should retry the complete transaction from the beginning, with a limit and backoff, when the operation is safe.

### Isolation level comparison

| Isolation level | Simple view | Main protection | Main trade-off |
|---|---|---|---|
| Read Uncommitted | May see temporary changes | Very little | Dirty reads |
| Read Committed | Sees committed data at each statement | Prevents dirty reads | Repeated reads may differ |
| Repeatable Read | Keeps a stable view of rows already read | Prevents many read changes during the transaction | Stale snapshot and possible conflicts |
| Serializable | Makes concurrent work behave like a serial order | Strongest consistency | More blocking, failures, and retries |

## 12. Common concurrency anomalies

### Dirty read

A transaction reads data written by another transaction that has not committed.

### Non-repeatable read

A transaction reads the same row twice and gets different committed values because another transaction committed a change between the reads.

### Phantom read

A repeated query returns a different set of rows because another transaction inserted or deleted rows matching the query.

### Lost update

One transaction overwrites another transaction's update.

Isolation levels and locking strategies determine which anomalies are possible.

---

## 13. Lock contention and deadlocks

### Lock contention

Lock contention occurs when multiple transactions need the same database resource, but one transaction already holds its lock.

Example:

~~~text
Transaction A locks Product 101 to update stock.
Transaction B also wants to update Product 101.
Transaction B waits until A commits or rolls back.
~~~

The system can still make progress, but waiting increases response time. Excessive contention can cause timeouts and reduce throughput.

Common causes include:

- long-running transactions;
- many concurrent writes to the same rows;
- locking more rows than necessary;
- slow processing while a transaction is open.

### Deadlock

A deadlock occurs when transactions wait for one another in a cycle, so none can continue.

Example:

~~~text
Transaction A locks Product 101.
Transaction B locks Product 202.

Transaction A requests Product 202 and waits for B.
Transaction B requests Product 101 and waits for A.
~~~

The database usually detects this cycle and aborts one transaction, allowing the other to continue.

### Difference

| Lock contention | Deadlock |
|---|---|
| One transaction waits for another | Transactions wait for each other |
| Usually resolves when the first transaction finishes | Cannot resolve without aborting one transaction |
| Causes delay | Causes a transaction failure and usually requires retry |

### Reducing contention and deadlocks

- keep transactions short;
- acquire locks in a consistent order;
- lock only the rows that are necessary;
- avoid network calls or slow processing inside transactions;
- use appropriate indexes;
- retry transient deadlock errors with bounded backoff.

A retry must recreate the complete transaction from the beginning. Do not continue using a transaction that the database has already aborted.

---

## 14. Transaction retries

Some transaction failures are transient:

- deadlock detected;
- serialization failure;
- temporary connection failure;
- lock timeout.

A safe retry should:

1. discard or roll back the failed transaction;
2. obtain a clean session or connection;
3. rerun the complete transaction;
4. limit attempts;
5. use backoff and jitter;
6. stop at the request deadline.

Do not retry only the final statement if earlier statements in the transaction have already been rolled back or if the transaction state is invalid.

For non-idempotent operations, use an idempotency key or another deduplication strategy before retrying.

---

## 15. Transactions and external side effects

A database transaction cannot automatically roll back an email, payment request, message, or HTTP call that has already reached another system.

Example:

~~~text
Database transaction commits
    ↓
Email sending fails
~~~

or:

~~~text
Email is sent
    ↓
Database transaction rolls back
~~~

The two systems now disagree.

Common patterns include:

- outbox pattern: commit an event record in the same database transaction, then publish it asynchronously;
- workflow or saga: coordinate multiple steps with explicit compensation;
- idempotent external operations;
- retryable message delivery with deduplication.

Do not assume database rollback reverses external side effects.

---

## 16. Testing concurrent updates

A concurrency test should:

1. create known initial data;
2. start multiple workers at the same time;
3. make them update the same row or related rows;
4. wait for all workers;
5. inspect the final state;
6. verify that business invariants still hold.

Test more than a successful response:

- final stock or balance;
- number of successful reservations;
- number of conflicts;
- deadlock or serialization errors;
- transaction rollback behavior;
- retry count;
- response status codes.

---

## Common mistakes

- Assuming a transaction automatically prevents every race condition.
- Reading a value in Python and blindly overwriting it later.
- Holding a transaction open while calling an external service.
- Retrying a failed transaction without starting a fresh transaction.
- Treating a deadlock as a permanent application error.
- Ignoring affected-row counts for conditional updates.
- Using pessimistic locks without a consistent lock order.
- Choosing Serializable isolation without measuring contention and retry behavior.
- Assuming rollback can undo an email, payment, or message already sent.
- Updating related rows in inconsistent order across different code paths.
- Returning a success response before the transaction commits.
- Treating database constraints and application checks as interchangeable.
