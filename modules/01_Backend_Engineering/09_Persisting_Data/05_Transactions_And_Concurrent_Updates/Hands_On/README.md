# Hands-on Lab — Transactions and Concurrent Updates

This lab demonstrates how database transactions behave when requests update the same inventory record.

The lab uses SQLAlchemy with SQLite so it can run locally without a database server. SQLite is suitable for demonstrating transactions, rollback, atomic updates, and optimistic version checks. Its behavior for row-level pessimistic locking differs from PostgreSQL and MySQL, so the limitation is documented in the exercise.

## Learning objectives

You will observe:

1. A lost-update race caused by read-then-write logic.
2. Rollback after a failed transaction.
3. An atomic conditional inventory update.
4. Optimistic locking with a version column.
5. Why row-lock syntax needs a database engine with row-level locking.
6. Why a consistent lock order helps prevent deadlocks.
7. How to test the final inventory invariant.

## Prerequisites

From the repository root:

~~~bash
uv sync
~~~

Run the lab:

~~~bash
python modules/01_Backend_Engineering/09_Persisting_Data/05_Transactions_And_Concurrent_Updates/Hands_On/main.py
~~~

The script creates a local SQLite file named transactions_lab.db in the hands-on directory and recreates the demo data on each run.

## What to inspect

The script prints:

- the result of the lost-update simulation;
- rollback behavior;
- the affected-row count for an atomic update;
- optimistic-lock success and stale-version failure;
- the generated pessimistic-locking SQL;
- the final inventory invariant.

## Important SQLite limitation

SQLite does not provide PostgreSQL-style row-level SELECT FOR UPDATE behavior. SQLAlchemy may compile the clause, but SQLite will not make concurrent requests wait on one specific row in the same way PostgreSQL does.

For a production-style pessimistic-locking experiment, run the equivalent code against PostgreSQL and verify that a second transaction waits until the first transaction commits or rolls back.

## Observation exercise

After running the script, answer these questions in observations.md:

1. What happened in the lost-update simulation?
2. Why can the final stock look valid while two reservations were accepted?
3. How did the atomic update use the affected-row count?
4. What happened when the optimistic version was stale?
5. Why is SQLite not enough to demonstrate PostgreSQL row-lock behavior?
6. How does consistent ordering prevent the Product 101/Product 202 deadlock?
7. Which invariant must always hold for a stock reservation?
8. Which approach would you choose for a simple high-contention stock decrement, and why?
