# Topic 09 — Persisting Data

> A FastAPI process can temporarily hold data in Python memory, but a production application needs data that survives restarts, is shared by application instances, and remains correct when multiple requests arrive together.

## 1. The limitation of in-memory storage

The Topic 08 repository uses a Python dictionary:

```python
products = {
    101: {"name": "Keyboard", "price": 2500}
}
```

This is useful for learning, but it has important limitations:

- Data disappears when the process restarts.
- A second application instance has its own separate copy.
- Multiple workers may see different data.
- Memory is not designed for durable querying and constraints.
- Concurrent updates can overwrite one another.
- There is no reliable transaction or recovery mechanism.

For example:

```text
Request A → Application instance 1 → products[101]
Request B → Application instance 2 → different products[101]
```

The two instances do not automatically share the dictionary.

## 2. What persistence means

Persistence means that data remains available after the application process stops and starts again.

A database provides a shared, durable place to store data:

```text
FastAPI process
      ↓
Repository
      ↓
Database connection
      ↓
Database table
```

The application should not assume that a Python object in memory is the permanent source of truth.

## 3. A relational database from first principles

A relational database stores related data in tables.

Example `products` table:

| id | name | sku | category | price |
|---:|---|---|---|---:|
| 101 | Keyboard | KEY-101 | electronics | 2500 |

Important database concepts:

- **Table** — a collection of related records
- **Row** — one record, such as one product
- **Column** — one attribute, such as `price`
- **Primary key** — uniquely identifies a row
- **Unique constraint** — prevents duplicate values, such as duplicate SKU
- **Foreign key** — connects one table to another
- **Index** — helps the database find rows efficiently

The database can enforce rules independently of the Python application.

For example:

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    price NUMERIC NOT NULL CHECK (price > 0)
);
```

The exact SQL will vary by database engine. The important idea is that data rules should not exist only in application code.

## 4. The repository's role

The service should not know whether data comes from:

- A Python dictionary
- SQLite
- PostgreSQL
- Another data service

The repository hides those details behind operations such as:

```python
product = repository.get_product(product_id)
repository.add_product(product_data)
repository.find_product_by_sku(sku)
```

The service asks for a result. It should not need to know whether the repository used SQL, an ORM, or an external API.

This allows the same service logic to be tested with an in-memory fake while production uses PostgreSQL.

## 5. Request flow with a database

For:

```http
POST /products
Content-Type: application/json
```

the flow becomes:

1. FastAPI parses and validates the request body.
2. The router calls the product service.
3. The service applies business rules.
4. The service calls the repository.
5. The repository obtains database access.
6. The repository executes an insert or query.
7. The database checks constraints.
8. The transaction commits or rolls back.
9. The repository returns the result.
10. The service returns the application result.
11. The router creates the HTTP response.

The database is the durable source of truth; the response is only a representation returned to the client.

## 6. Why application checks are not enough

Suppose the service checks whether an SKU exists before inserting it:

```text
1. Check whether KEY-101 exists
2. If absent, insert KEY-101
```

Two simultaneous requests can both pass step 1 before either reaches step 2.

Therefore, duplicate prevention needs a database-level unique constraint as the final authority. The application check can provide a friendly early response, but it cannot replace the database constraint.

## 7. Transactions in simple language

A transaction groups related database changes into one unit.

For example, creating an order may require:

1. Decrease available inventory.
2. Insert the order.
3. Insert order items.

If step 2 fails after step 1 succeeds, the database should roll back step 1. Otherwise, inventory would be lost without a corresponding order.

```text
Begin transaction
    ↓
Change data
    ↓
All operations succeed? ── Yes → Commit
                         └─ No  → Roll back
```

A transaction protects database changes. It does not automatically protect calls to unrelated external services.

## 8. API schema versus database schema

These schemas serve different purposes.

### API schema

Defines what the client may send or receive:

```python
class ProductCreate(BaseModel):
    name: str
    sku: str
    price: float
```

### Database schema

Defines how data is stored and protected:

```sql
sku TEXT NOT NULL UNIQUE
price NUMERIC NOT NULL CHECK (price > 0)
```

They may look similar, but they are not the same contract. The API may hide internal columns such as audit timestamps, while the database may contain constraints that provide a second line of protection.

## 9. What we will cover later

This first lesson intentionally does not go deep into:

- SQL syntax
- ORM design
- Connection pools
- Migrations
- Isolation levels
- Concurrent transactions
- Async database drivers
- Query performance

Those concepts will be introduced only when the capstone needs them.

## Mental model

Keep this distinction clear:

```text
Python memory  → temporary process state
Database       → durable shared source of truth
Repository     → boundary hiding storage details
Service        → business decisions
Router         → HTTP translation
```

## Interview summary

> In-memory storage is useful for a prototype but does not survive process restarts, does not naturally work across multiple application instances, and cannot reliably enforce durable constraints. A repository abstracts database access from the service, while the database provides persistence, constraints, and transactions. The service owns business decisions, and the router translates application outcomes into HTTP responses.
