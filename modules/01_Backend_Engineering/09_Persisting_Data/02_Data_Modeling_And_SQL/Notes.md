# Topic 09.02 — Data Modeling and SQL

> Data modeling decides how application information is represented and related in the database. SQL is the language used to create, read, update, and delete that data.

## 1. From API model to database model

The API accepts a product representation:

```json
{
  "name": "Keyboard",
  "sku": "KEY-101",
  "category": "electronics",
  "price": 2500
}
```

A database stores that information as a row in a table:

| id | name | sku | category | price |
|---:|---|---|---|---:|
| 101 | Keyboard | KEY-101 | electronics | 2500 |

The API model and database model are related, but they are not identical:

- The API may not expose internal fields such as `created_at`.
- The database needs a primary key.
- The database can enforce uniqueness and valid ranges.
- The API may use different names or nested structures.

## 2. Designing the products table

A simple relational design could be:

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    price NUMERIC NOT NULL CHECK (price > 0)
);
```

### Why each rule exists

- `id` identifies one product.
- `PRIMARY KEY` makes the identifier unique and non-null.
- `NOT NULL` prevents required fields from being absent.
- `UNIQUE` prevents two products from using the same SKU.
- `CHECK (price > 0)` protects a business/data invariant.
- A database type such as `NUMERIC` represents a price more deliberately than an unrestricted string.

Application validation improves the client experience. Database constraints remain the final protection for stored data.

## 3. Keys and relationships

### Primary key

A primary key identifies one row:

```text
products.id = 101
```

It should be stable and unique. The API may expose it as a resource identifier.

### Foreign key

Suppose each product belongs to a store:

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
    FOREIGN KEY (store_id) REFERENCES stores(id)
);
```

The foreign key prevents a product from referring to a store that does not exist.

### Natural and surrogate keys

- A **surrogate key** is a generated identifier such as an integer or UUID.
- A **natural key** comes from the business domain, such as SKU.

A product may use a generated `id` as its primary key while still placing a unique constraint on `sku`.

## 4. Basic SQL operations

### Insert

```sql
INSERT INTO products (name, sku, category, price)
VALUES ('Keyboard', 'KEY-101', 'electronics', 2500);
```

### Read one product

```sql
SELECT id, name, sku, category, price
FROM products
WHERE id = 101;
```

### Filter a collection

```sql
SELECT id, name, sku, category, price
FROM products
WHERE category = 'electronics'
ORDER BY name;
```

### Update

```sql
UPDATE products
SET price = 2400
WHERE id = 101;
```

Always include a carefully chosen `WHERE` clause. An accidental update without a condition may modify every row.

### Delete

```sql
DELETE FROM products
WHERE id = 101;
```

Deletion also requires an intentional condition. Production systems often use soft deletion when history or auditability matters.

## 5. Query parameters safely

Never build SQL by concatenating user input:

```python
# Unsafe
query = f"SELECT * FROM products WHERE sku = '{sku}'"
```

An attacker could change the meaning of the query through the input.

Use parameterized queries:

```python
query = "SELECT * FROM products WHERE sku = %s"
cursor.execute(query, (sku,))
```

The database driver sends the SQL structure and the value separately. This helps prevent SQL injection and handles escaping correctly.

The exact placeholder syntax depends on the database driver. The safety principle remains the same.

## 6. Query result versus application result

A database returns database-oriented data:

```text
row: (101, "Keyboard", "KEY-101", "electronics", 2500)
```

The repository converts that result into an application-oriented object:

```python
{
    "id": 101,
    "name": "Keyboard",
    "sku": "KEY-101",
    "category": "electronics",
    "price": 2500.0,
}
```

The service applies business decisions, and the API response schema decides what the client receives.

## 7. Relationships without forcing everything into one table

Suppose a product can have multiple suppliers. Repeating supplier columns inside `products` would become difficult to maintain.

A relational design might use:

```text
products
suppliers
product_suppliers
```

The `product_suppliers` table represents the many-to-many relationship:

```sql
CREATE TABLE product_suppliers (
    product_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    PRIMARY KEY (product_id, supplier_id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);
```

This keeps each fact in an appropriate place and avoids repeating groups of columns.

## 8. The repository boundary

The service should ask for domain operations:

```python
repository.get_product(product_id)
repository.list_products(category=category)
repository.add_product(product_data)
```

The repository translates those operations into SQL.

```text
Service intent
    ↓
Repository method
    ↓
Parameterized SQL
    ↓
Database result
    ↓
Application object
```

The service should not contain SQL strings, and the router should not know table names.

## 9. Common mistakes

- Treating API models and database tables as the same contract
- Relying only on Pydantic for uniqueness or referential integrity
- Building SQL with string concatenation
- Forgetting the `WHERE` clause in `UPDATE` or `DELETE`
- Using a natural business value as the only identifier without considering change
- Returning raw database rows directly from the API
- Adding indexes without understanding the query patterns
- Putting unrelated repeated data into one table
- Assuming an early duplicate check prevents concurrent duplicates

## Mental model

```text
API schema      → what clients send and receive
Database schema → how data is stored and protected
SQL             → how the repository communicates with the database
Repository      → hides SQL and database details
Service         → applies business meaning and rules
```

## What comes next

This subtopic does not yet cover:

- Database sessions and connection lifecycle
- Connection pools
- ORM syntax
- Migrations
- Transaction isolation
- Query plans and performance diagnosis

Those will be covered separately.
