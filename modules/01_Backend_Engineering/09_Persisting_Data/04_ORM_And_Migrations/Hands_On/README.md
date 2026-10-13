# Hands-on: ORM and Database Migrations

## Goal

Use SQLAlchemy with SQLite to observe:

- ORM model-to-table mapping;
- ORM-generated SQL;
- transaction commit and rollback;
- eager loading with joined loading and select-in loading;
- query counts and the N+1 pattern;
- a schema migration;
- a resumable, batched data backfill.

This lab is intentionally local and self-contained. It does not require PostgreSQL.

## Setup

From the repository root:

~~~bash
uv sync
~~~

Or install the project dependencies with your usual Python environment.

## Run

From this directory:

~~~bash
python main.py
~~~

The script creates a local SQLite file named orm_lab.db. It recreates the lab database on each run so the output is repeatable.

## What to observe

1. The initial schema is created without the category column.
2. A migration adds the category column.
3. A backfill populates category values in small batches.
4. joinedload retrieves products and stores using a join.
5. selectinload retrieves stores and their products using a controlled second query.
6. A duplicate SKU causes an integrity error and rollback.
7. Query-count output shows how loading strategy affects database calls.
8. A checkpoint table records backfill progress.

## Exercises

After running the script, create observations.md and answer:

1. What SQL does the ORM generate for the joined-loading example?
2. How many queries does the select-in loading example execute?
3. Why is a duplicate SKU an ORM/database error rather than only a Python validation error?
4. What changes when the transaction is rolled back?
5. Why is the category column added by a migration instead of only by changing the model?
6. How does the backfill checkpoint make the job resumable?
7. What would happen if the script stopped after one batch committed?
8. Why should you inspect generated SQL when using an ORM?
9. When would raw SQL be preferable to an ORM expression?
10. How could this lab be changed to use PostgreSQL in a production-like environment?

## Important limitation

SQLite and this local script simplify production behavior. A production system also needs migration tooling, deployment coordination, connection pooling, locking analysis, observability, backups, and a database-specific rollout strategy.
