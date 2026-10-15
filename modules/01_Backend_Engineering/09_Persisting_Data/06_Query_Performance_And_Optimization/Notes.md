# Topic 09.06 — Query Performance and Optimization

## Learning goal

Understand why a database query becomes slow, how to investigate it, and how to improve it without guessing.

The goal is not to memorize database tuning tricks. The goal is to build a repeatable diagnosis process:

~~~text
Observe the latency
    ↓
Identify where time is spent
    ↓
Inspect the SQL and query plan
    ↓
Change one thing
    ↓
Measure again
~~~

---

## 1. What does “a slow API” mean?

An API request can spend time in several places:

~~~text
Client/network time
    ↓
Application processing
    ↓
Connection-pool acquisition
    ↓
Database lock wait
    ↓
SQL execution
    ↓
Response serialization
~~~

A slow API does not automatically mean the SQL is slow.

For example:

- the request may wait for a database connection;
- the query may wait for another transaction's lock;
- the query may execute slowly because it scans too many rows;
- the database may be fast but response serialization may be expensive.

Measure the stages separately whenever possible.

Useful measurements include:

- total request latency;
- connection acquisition time;
- lock-wait time;
- SQL execution time;
- transaction duration;
- response serialization time;
- number of SQL statements per request.

---

## 2. Start with the actual SQL

ORM code is not the database operation itself. The database receives SQL.

Example ORM code:

~~~python
products = session.query(Product).filter(
    Product.category == "electronics"
).all()
~~~

The generated SQL may look like:

~~~sql
SELECT id, name, category, price
FROM products
WHERE category = 'electronics';
~~~

Before optimizing, inspect:

- the exact SQL;
- bound parameters;
- number of rows returned;
- number of rows examined;
- execution time;
- whether the query runs once or repeatedly.

Do not optimize an imagined query. Optimize the query the database actually receives.

---

## 3. What is an execution plan?

An execution plan is the database's chosen method for answering a query.

It may decide to:

- scan every row in a table;
- use an index;
- perform an index lookup followed by a table lookup;
- join tables using nested loops;
- sort rows;
- build a hash table for a join or aggregation.

Use tools such as:

~~~sql
EXPLAIN
SELECT id, name, price
FROM products
WHERE category = 'electronics';
~~~

For actual runtime behavior, databases often provide an analyze option:

~~~sql
EXPLAIN ANALYZE
SELECT id, name, price
FROM products
WHERE category = 'electronics';
~~~

Be careful with ANALYZE commands on writes because some databases execute the statement while measuring it.

Important plan information includes:

- estimated rows versus actual rows;
- sequential scans;
- index scans;
- join method;
- sort operations;
- temporary disk usage;
- actual execution time.

A plan is a hypothesis until it is compared with observed execution metrics.

---

## 4. Sequential scan versus index lookup

Suppose products has one million rows.

A sequential scan reads the table looking for matches:

~~~text
Read row 1
Read row 2
Read row 3
...
Read row 1,000,000
~~~

An index stores an additional searchable structure, such as a tree, allowing the database to find matching values more directly.

~~~sql
CREATE INDEX idx_products_category
ON products(category);
~~~

The database may then use the index for:

~~~sql
SELECT id, name, price
FROM products
WHERE category = 'electronics';
~~~

An index can reduce reads, but it is not free. It consumes:

- storage;
- memory and cache space;
- write time during INSERT, UPDATE, and DELETE;
- maintenance work.

Do not create an index for every column automatically.

---

## 5. When is an index useful?

An index is usually useful when a query frequently filters, joins, sorts, or enforces uniqueness using a column.

Common candidates:

- foreign-key columns used in joins;
- columns used in frequent selective filters;
- columns used in ordering for pagination;
- unique business identifiers such as SKU;
- columns used in common lookup operations.

An index may be less useful when:

- the table is very small;
- the column has very few distinct values;
- most rows match the filter;
- the query applies a function that prevents normal index use;
- the index is never used but still adds write cost.

The database optimizer decides whether an index is cheaper than scanning the table. An index existing does not guarantee that it will be chosen.

---

## 6. Selectivity

Selectivity describes how much a filter narrows the result.

Example:

~~~text
WHERE id = 101
→ likely returns one row
→ highly selective

WHERE status = 'active'
→ may return most rows
→ less selective
~~~

Highly selective filters are often good index candidates. A low-cardinality column such as a boolean flag may not benefit from a simple index when a large percentage of the table matches.

The correct decision depends on table size, data distribution, query shape, and the database optimizer.

---

## 7. Composite indexes and column order

A composite index contains multiple columns:

~~~sql
CREATE INDEX idx_products_store_category
ON products(store_id, category);
~~~

This may help a query such as:

~~~sql
SELECT id, name, price
FROM products
WHERE store_id = 7
  AND category = 'electronics';
~~~

Column order matters. An index beginning with store_id is generally more useful for:

- store_id;
- store_id plus category.

It may not be equally useful for a query filtering only by category.

Choose the order based on real query patterns and selectivity. Do not assume that adding more columns always improves performance.

---

## 8. Sargability: write filters the database can search

A predicate is often called sargable when the database can use an index efficiently to find matching values.

Potentially inefficient form:

~~~sql
SELECT *
FROM orders
WHERE YEAR(order_date) = 2026;
~~~

The database may need to apply the function to many rows.

A range predicate is usually more index-friendly:

~~~sql
SELECT *
FROM orders
WHERE order_date >= '2026-01-01'
  AND order_date < '2027-01-01';
~~~

Other common problems include:

- applying functions to indexed columns;
- leading wildcards such as LIKE '%keyboard';
- implicit type conversions;
- arithmetic on the indexed column;
- mismatched data types between joined columns.

Always confirm the actual plan for the database engine in use.

---

## 9. Avoid selecting more data than needed

This query requests every column:

~~~sql
SELECT *
FROM products
WHERE store_id = 7;
~~~

If the API only needs three fields, request three fields:

~~~sql
SELECT id, name, price
FROM products
WHERE store_id = 7;
~~~

This can reduce:

- database I/O;
- network transfer;
- Python object creation;
- memory usage;
- response serialization time.

This is called projection: selecting only the columns required by the use case.

It does not mean that SELECT star is always wrong. It means that the data shape should be intentional, especially for large tables and public APIs.

---

## 10. Query count and the N+1 problem

One request that executes many small queries can be slower than one well-designed query.

Example:

~~~python
orders = session.query(Order).all()

for order in orders:
    print(order.customer.name)
~~~

This may execute:

~~~text
1 query for orders
+ N queries for customers
= N+1 queries
~~~

Possible solutions include:

- eager loading;
- a join and explicit projection;
- a batch IN query;
- a request-scoped DataLoader;
- changing the response shape.

Measure query count per request. There is no universal number that proves an N+1 problem, but repeated structurally similar queries and query count growing linearly with returned records are strong signals.

---

## 11. Pagination

Returning every row from a large table creates increasing work for the database, application, and client.

Offset pagination:

~~~sql
SELECT id, name, price
FROM products
ORDER BY id
LIMIT 50 OFFSET 5000;
~~~

It is simple, but the database may still scan or skip many earlier rows as the offset grows. Results can also shift when rows are inserted or deleted between requests.

Keyset pagination uses a stable cursor:

~~~sql
SELECT id, name, price
FROM products
WHERE id > :last_seen_id
ORDER BY id
LIMIT 50;
~~~

Keyset pagination is often more stable and efficient for large ordered datasets. The ordering column should be indexed and deterministic.

---

## 12. Joins and indexes

A join connects rows from related tables.

~~~sql
SELECT p.name, s.name AS store_name
FROM products p
JOIN stores s ON s.id = p.store_id
WHERE p.store_id = 7;
~~~

Useful considerations:

- primary keys are normally indexed;
- foreign-key columns should often be indexed when used for joins or parent lookups;
- return only required columns;
- inspect the join plan;
- watch for row multiplication when joining one-to-many relationships;
- aggregate or paginate child rows deliberately.

An index on one table does not automatically make every join fast. The plan depends on filters, data distribution, statistics, and join cardinality.

---

## 13. Transactions and query performance

Transactions and performance are connected.

A long transaction can:

- hold locks;
- keep a connection checked out;
- prevent cleanup of old row versions;
- increase contention;
- make connection-pool timeouts more likely.

A slow query inside a transaction is especially harmful because the transaction may remain open while the query runs.

Keep transactions short, but do not split a business operation into independent commits merely to reduce latency. Preserve the correct atomic boundary.

---

## 14. A practical diagnosis workflow

When an endpoint is slow:

### Step 1: Measure the request

Record:

- total latency;
- request volume;
- error rate;
- p50, p95, and p99 latency.

### Step 2: Break down the time

Measure:

- pool checkout;
- lock wait;
- SQL execution;
- application processing;
- response serialization.

### Step 3: Identify the SQL

Capture:

- query shape;
- parameters safely;
- query count;
- rows returned;
- slow-query frequency.

Do not log secrets or sensitive values.

### Step 4: Inspect the plan

Use EXPLAIN and, where safe, EXPLAIN ANALYZE. Compare estimates with actual row counts and execution time.

### Step 5: Check the data model

Review:

- indexes;
- foreign keys;
- data distribution;
- statistics freshness;
- table size;
- pagination behavior.

### Step 6: Change one thing and measure again

Examples:

- add or adjust an index;
- rewrite a non-sargable predicate;
- reduce selected columns;
- batch related lookups;
- replace offset pagination with a cursor;
- shorten the transaction.

Do not make many changes at once because you will not know which change helped or harmed.

---

## 15. Common performance mistakes

- Assuming every slow API is caused by slow SQL.
- Adding indexes without checking real query plans.
- Creating indexes on every column.
- Selecting all columns for every endpoint.
- Ignoring N+1 queries.
- Using large offsets for deep pagination.
- Applying functions to indexed columns in filters.
- Ignoring row multiplication in joins.
- Holding transactions open during slow work.
- Increasing the connection pool before fixing slow queries or lock waits.
- Optimizing for average latency while p95 and p99 are failing.
- Logging complete SQL with sensitive parameter values.
- Trusting estimated query plans without measuring actual execution.
- Changing multiple performance variables at once.
