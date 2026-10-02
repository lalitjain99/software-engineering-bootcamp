# Topic 09.02 — Data Modeling and SQL Interview Guide

## 1. Why should a production application not use a Python dictionary as its source of truth?

A dictionary is process-local and temporary. Its data disappears when the process restarts, is not automatically shared across multiple workers or instances, and does not provide durable constraints, transactions, concurrency control, or recovery.

A database provides a shared and durable source of truth.

## 2. How is an API schema different from a database schema?

An API schema defines what clients may send and receive. A database schema defines how data is stored and protected.

The API may hide internal fields such as audit timestamps, while the database may add primary keys, foreign keys, unique constraints, indexes, and checks that are not visible in the API contract.

## 3. What constraints would you define for a products table?

For a typical product table:

- id — primary key
- name — required if every product must have a name
- sku — required and unique
- category — required if every product must belong to a category
- price — numeric, required, and checked to be greater than zero
- store_id — required foreign key if every product belongs to a store

Example:

~~~sql
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
~~~

## 4. Which columns should be indexed?

The primary key is normally indexed automatically. A unique constraint on sku normally creates a unique index.

An index on category may help if the application frequently filters by category. An index on price may help for frequent price filtering or sorting. Indexes should be based on query patterns rather than added to every column because they consume storage and add write overhead.

## 5. Write common SQL operations for products.

~~~sql
-- Insert
INSERT INTO products (name, sku, category, price)
VALUES ('Keyboard', 'KEY-101', 'electronics', 2500);

-- Read one
SELECT id, name, sku, category, price
FROM products
WHERE id = 101;

-- Filter and sort
SELECT id, name, sku, category, price
FROM products
WHERE category = 'electronics'
ORDER BY price ASC;

-- Update
UPDATE products
SET price = 2400
WHERE id = 101;

-- Delete
DELETE FROM products
WHERE id = 101;
~~~

An UPDATE or DELETE without a WHERE clause can affect every row in the table. It does not remove the table itself; DROP TABLE removes the table definition.

## 6. Why should a product reference store_id instead of repeating the store name?

store_id is a stable identifier that can reference the store's primary key. Store names may be duplicated, changed, or misspelled. Storing the relationship through an ID avoids repeated data and allows the database to enforce referential integrity.

## 7. What is a foreign key?

A foreign key ensures that a value in one table refers to an existing row in another table.

~~~sql
FOREIGN KEY (store_id) REFERENCES stores(id)
~~~

It prevents a product from referring to a store that does not exist.

If an invalid store_id is inserted, the database rejects the operation with a foreign-key constraint error. The repository or application layer can translate that low-level error into an application exception, and the HTTP boundary can return the agreed response.

## 8. What should happen when deleting a store that still has products?

If every product must belong to a store, deletion should be rejected:

~~~sql
FOREIGN KEY (store_id)
    REFERENCES stores(id)
    ON DELETE RESTRICT
~~~

Other policies are possible:

- CASCADE deletes dependent products and can be dangerous.
- SET NULL keeps products but requires nullable store_id.
- Soft deletion can mark the store inactive without removing historical data.

The correct choice depends on the business meaning.

## 9. Write a query to list products for store 7.

~~~sql
SELECT id, name, sku, category, price
FROM products
WHERE store_id = 7;
~~~

## 10. Write a join that returns the product name and store name.

~~~sql
SELECT
    p.name AS product_name,
    s.name AS store_name
FROM products AS p
JOIN stores AS s
    ON p.store_id = s.id;
~~~

## 11. What is SQL injection?

SQL injection occurs when untrusted input is concatenated into a SQL string and is interpreted as part of the SQL syntax.

Unsafe code:

~~~python
query = f"SELECT * FROM products WHERE sku = '{sku}'"
~~~

If the input is:

~~~text
' OR '1'='1
~~~

the query may become:

~~~sql
SELECT * FROM products
WHERE sku = '' OR '1'='1';
~~~

The attacker has changed the meaning of the condition, potentially causing unintended rows to be returned. Depending on permissions and the query, injection can also expose, modify, or delete data.

## 12. How do parameterized queries prevent SQL injection?

Use a parameterized query:

~~~python
query = "SELECT id, name, sku, price FROM products WHERE sku = %s"
cursor.execute(query, (sku,))
~~~

For SQLite:

~~~python
connection.execute(
    "SELECT id, name, sku, price FROM products WHERE sku = ?",
    (sku,),
)
~~~

The database driver treats the SQL statement and the user value separately. Quote characters and SQL keywords in the value remain data instead of becoming executable SQL syntax.

Manual escaping is not a reliable replacement because escaping rules vary by database and context. Parameter binding should be used for values, and dynamic identifiers should come from a server-controlled allowlist.

## 13. What is the role of a repository?

A repository hides storage details from the service. The service asks for operations such as:

~~~python
repository.get_product(product_id)
repository.list_products(category=category)
repository.add_product(product_data)
~~~

The repository translates those operations into SQL or another storage mechanism and converts database results into application-oriented objects.

## 14. Why are database constraints still needed when the service validates input?

Application validation improves the client experience, but it cannot fully protect against:

- Concurrent requests
- Other applications writing to the same database
- Administrative scripts
- Bugs in another code path
- Direct database access

The database remains the final authority for constraints such as uniqueness, foreign keys, required values, and valid ranges.

## Common Mistakes

- Treating the API schema and database schema as identical
- Assuming a service-level duplicate check prevents concurrent duplicates
- Forgetting NOT NULL alongside UNIQUE for required business identifiers
- Confusing DELETE FROM products with DROP TABLE products
- Omitting WHERE from an update or delete
- Building SQL with f-strings or string concatenation
- Believing manual escaping is equivalent to parameter binding
- Assuming a foreign-key failure returns an empty query result
- Adding indexes to every column without checking query patterns
- Returning raw database rows directly as the public API response
- Using CASCADE without understanding the amount of dependent data it can delete
- Treating database errors as HTTP exceptions inside the repository
