# Observations: ORM and Database Migrations

## 1. What SQL does the ORM generate for the joined-loading example?

The joined-loading example uses `joinedload(Product.store)`, so SQLAlchemy loads the `Product` rows and joins to the related `stores` table in the same query.

Example SQL shape:

```sql
SELECT
    products.id,
    products.store_id,
    products.name,
    products.sku,
    products.price,
    products.category,
    stores.id AS stores_1_id,
    stores.name AS stores_1_name
FROM products
LEFT OUTER JOIN stores ON stores.id = products.store_id
ORDER BY products.id
```

This is a single query, which is why it is efficient for a many-to-one relationship like `Product -> Store`.

## 2. How many queries does the select-in loading example execute?

The `selectinload(Store.products)` example runs 2 queries total:

1. One query to fetch the stores.
2. One query to fetch all products for those stores using `IN (...)`.

The second query is shaped like:

```sql
SELECT products.id, products.store_id, products.name, products.sku, products.price, products.category
FROM products
WHERE products.store_id IN (?, ?)
```

This is the classic select-in pattern: fetch the parent rows first, then fetch the related rows in one batch.

## 3. Why is a duplicate SKU an ORM/database error rather than only a Python validation error?

Because the database itself enforces uniqueness on `sku`.

In the model, `sku` is defined as a non-null string and the table was created with a unique constraint. The ORM does not magically validate uniqueness before issuing the `INSERT`; it hands the insert to the database. When SQLite tries to insert a second row with the same `sku`, the database raises an `IntegrityError`.

This is why the error shows up as a database-level exception during `session.commit()`, not as a simple Python value check.

## 4. What changes when the transaction is rolled back?

When a transaction is rolled back, all uncommitted changes inside that transaction are discarded.

In this lab:

- The update to product 101 is committed successfully.
- The attempt to insert a product with `sku='KEY-101'` triggers an integrity error.
- The `with session.begin():` block rolls back automatically.
- No duplicate row remains in the database after the rollback.

The database returns to the last committed state.

## 5. Why is the category column added by a migration instead of only by changing the model?

Because the database schema already exists and the application is running against a real database. Changing the ORM model alone does not automatically alter the existing SQLite table.

A migration is a controlled, repeatable change to the schema. It updates the database structure in a safe way and preserves data while adding the `category` column. This is essential in production because the code and the database must evolve together.

## 6. How does the backfill checkpoint make the job resumable?

The backfill stores its progress in a table named `backfill_progress`:

```sql
CREATE TABLE IF NOT EXISTS backfill_progress (
    job_name VARCHAR(100) PRIMARY KEY,
    last_processed_id INTEGER NOT NULL
)
```

Each batch:

1. Reads the current `last_processed_id`.
2. Picks only products with `id > last_id` and `category IS NULL`.
3. Updates those rows in a batch.
4. Writes the newest processed ID back to `backfill_progress`.

If the script stops after a batch, it can resume from that stored checkpoint instead of starting over from the beginning.

## 7. What would happen if the script stopped after one batch committed?

The script would resume from the checkpoint stored in `backfill_progress`.

It would continue from the last processed `id`, not reprocess earlier rows. That means the completed rows would stay updated, and only the remaining `NULL` category rows would be processed next.

This makes a long-running backfill safe and resumable.

## 8. Why should you inspect generated SQL when using an ORM?

Even with an ORM, the database still executes SQL directly. Inspecting the generated statements helps you:

- catch the N+1 problem,
- confirm joins and filters are correct,
- see whether the ORM is producing unexpected queries,
- compare performance across lazy vs eager loading,
- debug data issues that are not obvious from Python code alone.

This lab includes a SQL event listener that prints each statement, which is a great habit when tuning ORM queries.

## 9. When would raw SQL be preferable to an ORM expression?

Raw SQL is useful when:

- the query is highly database-specific,
- you need a complex query that is awkward in ORM syntax,
- you want to use advanced SQL features like window functions, CTEs, or hints,
- you are doing data migration or schema-changing work,
- you need maximum control over performance and query execution.

ORMs are great for common application patterns, but raw SQL remains valuable for performance tuning and database-specific operations.

## 10. How could this lab be changed to use PostgreSQL in a production-like environment?

To use PostgreSQL instead of SQLite, you would:

1. install a PostgreSQL driver such as `psycopg`,
2. change the connection string to something like:

```python
DATABASE_URL = "postgresql+psycopg://username:password@localhost:5432/orm_lab"
```

3. run PostgreSQL in Docker or a managed service,
4. use a migration tool such as Alembic for schema updates,
5. configure environment variables for host, port, username, and password,
6. test locking, connection pooling, and transaction behavior in a real DB environment.

This would make the lab closer to a real production system, while still keeping the same ORM concepts.

## Summary

This lab demonstrates how SQLAlchemy maps Python objects to database tables, how eager loading changes query count, how the database enforces integrity constraints, how migrations preserve schema changes, and how resumable backfills can safely process large data updates.
