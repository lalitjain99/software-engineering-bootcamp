# Observations — Transactions and Concurrent Updates

Run the lab first:

~~~bash
python modules/01_Backend_Engineering/09_Persisting_Data/05_Transactions_And_Concurrent_Updates/Hands_On/main.py
~~~

Answer in your own words.

## 1. Lost update

What did Request A and Request B each read? What did the final stock show? Why can the final stock look valid while two reservations were accepted?

## 2. Rollback

What value did stock have after rollback? Which change was discarded?

## 3. Atomic update

Why did the first conditional update affect one row and the second affect zero rows? What should an API return for the second reservation?

## 4. Optimistic locking

Why did the second versioned update affect zero rows? What should the application do before retrying?

## 5. Pessimistic locking

Why is the SQLite output not proof that a second PostgreSQL transaction would wait? What database would you use for a realistic row-lock test?

## 6. Deadlock prevention

Why does sorting product IDs before acquiring locks prevent the Product 101/Product 202 circular wait?

## 7. Invariants

What must always be true after concurrent reservations?

- stock must not become negative;
- successful reservations must not exceed available stock;
- a failed reservation must not create a successful order.

## 8. Design decision

For a simple high-contention stock decrement, would you choose an atomic update, pessimistic locking, or optimistic locking? Explain the workload and trade-off behind your choice.

## 9. Production test improvements

What would you change to run this test against PostgreSQL? Consider:

- database URL and credentials;
- separate sessions and transactions;
- a barrier to start concurrent workers;
- transaction and lock timeouts;
- cleanup of test data;
- assertions for successful reservations and final stock.
