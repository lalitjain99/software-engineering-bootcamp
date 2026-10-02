# Hands-on Lab — Data Modeling and SQL

## Goal

Use SQLite to create a small store/product database and observe how database constraints behave.

This lab uses Python's built-in `sqlite3` module, so no new dependency is required.

## Exercise

Create a `main.py` file that:

1. Opens a SQLite database.
2. Enables foreign-key enforcement.
3. Creates `stores` and `products` tables.
4. Inserts two stores.
5. Inserts products belonging to valid stores.
6. Attempts to insert a product with a duplicate SKU.
7. Attempts to insert a product with a non-existent `store_id`.
8. Lists all products for store `1`.
9. Uses a `JOIN` to display each product with its store name.
10. Attempts to delete a store that still has products.
11. Closes the database connection.

Use this schema:

```sql
CREATE TABLE stores (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    store_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    price NUMERIC NOT NULL CHECK (price > 0),
    FOREIGN KEY (store_id)
        REFERENCES stores(id)
        ON DELETE RESTRICT
);
```

## Important SQLite detail

SQLite does not enforce foreign keys unless they are enabled for the connection:

```python
connection.execute("PRAGMA foreign_keys = ON")
```

Without this statement, the invalid `store_id` and store-deletion tests may appear to succeed.

## Use parameterized queries

Use placeholders instead of string concatenation:

```python
connection.execute(
    "INSERT INTO stores (name) VALUES (?)",
    ("Central Store",),
)
```

The placeholder syntax for SQLite is `?`. Other database drivers may use a different placeholder style.

## Capture observations

Record:

- What happens when the duplicate SKU is inserted?
- What happens when the `store_id` does not exist?
- What happens when a store with products is deleted?
- What does the `JOIN` return?
- Which errors come from the database rather than from FastAPI or Pydantic?
- What changes when `PRAGMA foreign_keys = ON` is removed?

## Completion exercise

Share:

1. Your `main.py`
2. The output from each constraint test
3. The result of the store/product `JOIN`
4. One paragraph explaining why database constraints are still needed even when the service validates input
