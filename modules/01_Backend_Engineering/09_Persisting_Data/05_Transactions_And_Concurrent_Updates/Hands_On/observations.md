# Observations — Transactions and Concurrent Updates

Run the lab first:

~~~bash
python modules/01_Backend_Engineering/09_Persisting_Data/05_Transactions_And_Concurrent_Updates/Hands_On/main.py
~~~

## 1. Lost update

Request A and Request B both read the same starting value: stock = 1. Each request subtracts 1 from its own in-memory copy, so both decide the reservation is valid.

In this SQLite simulation, both requests write stock = 0. The final database value therefore looks numerically reasonable, but two reservations were accepted even though only one item existed. This is the important business failure: the inventory value alone does not reveal that the item was sold twice.

The problem is a classic check-then-act race and lost-update pattern. Both transactions read the same state before either write was committed. The second write overwrote the first write's effect instead of detecting that another request had already reserved the item.

The script interleaves two sessions manually to make the race visible. A production concurrency test should use separate workers and synchronize their start with a barrier or event.

## 2. Rollback

After the rollback, stock returns to 1. The change that set stock to -1 was never committed, so the transaction was discarded and the original value was restored when the session rolled back.

## 3. Atomic update

The first conditional update succeeds because the row still meets the condition stock >= 1. It updates one row and returns a rowcount of 1. The second conditional update runs after the first has committed, so the stock is now 0 and the WHERE clause no longer matches. Its rowcount is 0.

For the second reservation, the API should treat this as a conflict or insufficient-stock result, not a successful reservation. In practice, it should return a 409 Conflict or a business error such as “insufficient stock,” because the row was already depleted.

## 4. Optimistic locking

The second versioned update affects zero rows because the version value no longer matches the database row. The first transaction increments version from 1 to 2, so the stale version check fails and the update is skipped.

The application should reload the current product state, confirm the newest version, and then either retry the operation with fresh data or return a concurrency conflict to the client. A retry should happen only after the system has re-read the latest values.

## 5. Pessimistic locking

The SQLAlchemy output is not proof that SQLite would block a second transaction. SQLite does not provide the same row-level locking semantics as PostgreSQL or MySQL. Depending on the SQLite dialect and generated SQL, the FOR UPDATE clause may be omitted or have no row-locking effect.

In other words, seeing a SQLAlchemy locking expression is not the same as observing real database lock behavior.

For a realistic row-locking test, use PostgreSQL or another engine with row-level locks. Run concurrent transactions and measure whether the second session waits until the first transaction commits or rolls back.

## 6. Deadlock prevention

Sorting product IDs before acquiring locks makes both transactions request the same lock order. In the example, both Request A and Request B sort [101, 202], so they attempt to lock Product 101 before Product 202. That prevents the circular wait pattern where A holds 101 and waits on 202 while B holds 202 and waits on 101.

With a consistent order, the lock graph cannot form a cycle, so deadlock is avoided.

## 7. Invariants

After concurrent reservations, these conditions must always hold:

- stock must never become negative;
- successful reservations must not exceed available stock;
- a failed reservation must not create a successful order.

In other words, the application must preserve the business invariant that the number of accepted reservations is never greater than the stock available at the time the reservation is processed.

## 8. Design decision

For a simple high-contention stock decrement, I would choose an atomic conditional update as the default design. It is concise, efficient, and enforced by the database itself: the UPDATE only succeeds when stock >= 1, and the rowcount tells us whether the reservation was accepted.

Optimistic locking is a good fit when conflicts are rare and retrying is acceptable. Pessimistic locking is useful when a short, multi-step decision needs exclusive control of a row, but it increases contention and complexity. The transaction should remain as short as possible. For a straightforward inventory decrement, the atomic update is usually the best balance of correctness and performance.

## 9. Production test improvements

To run this against PostgreSQL, I would change several things:

- use a PostgreSQL connection string with the correct host, port, database name, user, and password;
- create separate sessions and transactions for each worker so they do not share state in memory;
- add a barrier so both workers begin the reservation attempt at the same time;
- configure transaction and lock timeouts to avoid hanging tests;
- clean up test data before and after each run to keep the environment deterministic;
- assert both the successful reservation count and the final stock so the test proves the invariant holds.

A production-style test should verify that the final stock equals the starting stock minus the number of successful reservations, and that no reservation is counted as successful after a failed update.

