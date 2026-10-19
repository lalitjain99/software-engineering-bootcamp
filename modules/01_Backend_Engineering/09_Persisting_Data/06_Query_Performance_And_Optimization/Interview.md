# Topic 09.06 — Query Performance and Optimization: Interview Guide

This guide is based on the reviewed interview practice for diagnosing slow queries, designing indexes, reading execution plans, and measuring production improvements.

---

## 1. How would you investigate a slow API endpoint?

Break total request latency into separate stages:

~~~text
connection-pool acquisition
    ↓
database lock wait
    ↓
SQL execution
    ↓
application processing
    ↓
response serialization
    ↓
network transfer
~~~

Inspect:

- total request latency and p50, p95, and p99;
- connection checkout duration and pool timeouts;
- all database spans, not only the main query;
- lock waits and blocked sessions;
- SQL execution time;
- query count per request;
- application CPU and profiling data;
- external calls;
- response serialization time and payload size.

Use APM traces, pool metrics, database wait events, slow-query logs, query plans, and application profiling before changing code.

Do not assume that a slow API automatically means slow SQL.

---

## 2. What is the N+1 query problem?

An endpoint may execute one query for the parent records and one additional query for each related record.

Example:

~~~text
1 query to load 20 products
+ 20 queries to load each product's customer
= 21 queries
~~~

This is an N+1 query problem. Query count grows linearly with the number of returned records.

Signals include:

- high query count per request;
- query count increasing with page size;
- repeated SQL statements with different IDs;
- many database spans in one trace;
- database QPS increasing without proportional user traffic;
- long connection hold time.

Confirm it using ORM SQL logging, query-count instrumentation, tests with different page sizes, and APM traces.

Solutions include:

- eager loading with joinedload or selectinload;
- an explicit join and projection;
- a batch IN query;
- a request-scoped DataLoader.

GraphQL alone does not solve N+1. GraphQL resolvers can produce the same problem unless batching is implemented.

---

## 3. Why is applying a function to an indexed column often inefficient?

This query may be non-sargable:

~~~sql
SELECT *
FROM orders
WHERE YEAR(order_date) = 2026;
~~~

The database may need to evaluate YEAR for many rows before deciding whether each row matches. This can prevent efficient use of a normal index on order_date.

Rewrite it as a range:

~~~sql
SELECT *
FROM orders
WHERE order_date >= '2026-01-01'
  AND order_date < '2027-01-01';
~~~

The column remains unwrapped, so the database can perform an index range scan when that is cheaper than a sequential scan.

The optimizer may still choose a sequential scan if most rows match, the table is small, or statistics indicate that the index is not beneficial. Confirm with EXPLAIN.

Functional indexes are another option in some database engines, but they are database-specific.

---

## 4. Why does a composite index help this query?

Query:

~~~sql
SELECT id, name, price
FROM products
WHERE store_id = 7
  AND category = 'electronics'
ORDER BY price ASC;
~~~

Candidate index:

~~~sql
CREATE INDEX idx_products_store_category_price
ON products(store_id, category, price);
~~~

The index is aligned with:

1. equality filtering on store_id;
2. equality filtering on category;
3. ordering by price within that filtered subset.

The B-tree can locate the store and category range, then scan the matching entries in price order.

Column order matters because composite indexes follow a left-to-right structure. An index beginning with store_id is generally useful for:

- store_id;
- store_id and category;
- store_id, category, and price.

It is not usually equally useful for filtering only by category or price.

Always confirm the chosen plan with EXPLAIN. The optimizer may prefer a sequential scan when most rows match.

---

## 5. Why is more indexing not always better?

Indexes improve selective reads, but they add write and operational cost.

### SELECT

Benefit:

- fewer rows may need to be examined;
- filters, joins, and ordering may become faster.

Cost:

- the optimizer may still choose another plan;
- index access can cause random table lookups;
- extra indexes increase planning choices and maintenance.

### INSERT

Each insert may need to update every relevant index. This adds CPU, I/O, and page-split work.

A unique index may still be necessary to enforce a business constraint such as unique SKU.

### UPDATE

An index can speed up locating rows through the WHERE clause. If an indexed column changes, the database must maintain the old and new index entries.

### DELETE

The database must remove the row's entries from each index, adding work to the deletion.

### Storage and memory

Indexes consume disk space and buffer-pool memory. Too many indexes can cause memory pressure, increase maintenance work, and affect replication or backup size.

Add indexes based on measured query patterns and execution plans. Remove redundant or unused indexes carefully.

---

## 6. What does a large estimate-versus-actual mismatch mean?

Suppose the plan estimates 100 rows but processes 100,000 rows.

This may indicate:

- stale or missing statistics;
- data skew;
- correlation between filter columns that the optimizer does not understand;
- a parameter value that is very different from the average.

Consequences include:

- choosing an index scan when a sequential or bitmap scan would be better;
- choosing an unsuitable join method;
- underestimated sort or hash memory;
- disk spills;
- excessive random I/O.

Investigate:

- estimated rows versus actual rows at every plan node;
- rows removed by filters;
- scan and join methods;
- loops;
- buffer usage;
- sort or hash spill;
- data distribution;
- statistics freshness.

Refresh statistics where appropriate:

~~~sql
ANALYZE products;
~~~

PostgreSQL extended statistics can help with correlated columns:

~~~sql
CREATE STATISTICS stats_store_category
ON store_id, category
FROM products;

ANALYZE products;
~~~

EXPLAIN ANALYZE executes the query, so use caution with write statements.

---

## 7. Why can deep OFFSET pagination become slow?

Query:

~~~sql
SELECT id, name, price
FROM products
ORDER BY id
LIMIT 50 OFFSET 50000;
~~~

The database must locate and skip a large number of earlier entries before returning 50 rows. Even with an index, the work grows with the offset.

Keyset pagination uses the last value from the previous page:

~~~sql
SELECT id, name, price
FROM products
WHERE id > :last_seen_id
ORDER BY id ASC
LIMIT 50;
~~~

With an index on id, the database can seek near the cursor and fetch the next limited set.

Keyset pagination provides approximately:

~~~text
index seek + requested page size
~~~

It is usually more stable for deep pages, but the order must be deterministic. If created_at is not unique, use a tie-breaker:

~~~sql
ORDER BY created_at, id;
~~~

The cursor must contain both values.

Offset pagination is still useful when users need direct page-number navigation and the dataset is small or shallow.

---

## 8. Why can SELECT star hurt performance?

If an endpoint needs only id, name, and price, this is unnecessarily broad:

~~~sql
SELECT *
FROM products
WHERE store_id = 7;
~~~

Selecting unused columns can increase:

- disk reads;
- network transfer;
- driver parsing;
- ORM object creation;
- application memory;
- response serialization time.

Prefer an explicit projection:

~~~sql
SELECT id, name, price
FROM products
WHERE store_id = 7;
~~~

At the ORM layer, select specific columns or use a projection rather than loading a full entity when the endpoint does not need it.

At the API layer, define a narrow response schema. An index may be designed to cover a frequent projection, but covering-index syntax and index-only behavior are database-specific and plan-dependent.

---

## 9. How should a store and its 10,000 products be returned?

A flat join can return 10,000 rows and repeat the store columns in every row. This creates database, network, application, and client-side costs.

A clearer API design is:

~~~text
GET /stores/7
GET /stores/7/products?limit=50&cursor=...
~~~

The product query can use keyset pagination:

~~~sql
SELECT id, name, price
FROM products
WHERE store_id = 7
  AND id > :last_seen_id
ORDER BY id ASC
LIMIT 50;
~~~

Support it with an index such as:

~~~sql
CREATE INDEX idx_products_store_id_id
ON products(store_id, id);
~~~

If the client needs one response, a composite endpoint can execute one focused query for store details and one paginated query for products, then combine them server-side.

Return 404 if the store does not exist. Return an empty collection if the store exists but has no products.

---

## 10. What should you inspect when a query uses an index but remains slow?

Inspect:

- the selected scan type: Index Scan, Index Only Scan, Bitmap Scan, or Sequential Scan;
- estimated rows versus actual rows;
- loops and rows removed by filters;
- Index Cond versus post-fetch Filter;
- buffer hits and reads using EXPLAIN with BUFFERS;
- heap access and heap fetches;
- join method and join cardinality;
- sort and hash operations;
- whether sorts or hashes spill to disk;
- actual execution time for each plan node.

An index is not automatically beneficial. A query returning a large percentage of the table may be faster with a sequential scan.

Heap Fetches are especially relevant to PostgreSQL Index Only Scan. A normal Index Scan inherently needs table access for row data.

---

## 11. Why can an index help in testing but hurt in production?

Compare:

- data volume;
- data distribution and skew;
- actual parameter values;
- cache warmth;
- concurrent read and write workload;
- database hardware;
- memory and I/O configuration;
- statistics freshness;
- table and index bloat;
- prepared-statement or plan-cache behavior;
- replication, backup, and storage workload.

A test query may run against a small, uniform, warm dataset. Production may have millions of rows, cold pages, skewed values, and heavy concurrent writes.

Do not trust a benchmark unless its data and workload resemble production.

---

## 12. How should an index be added to a large production table?

Assess:

- table-lock behavior;
- expected build duration;
- CPU and I/O impact;
- disk headroom;
- replication lag;
- long-running transactions;
- application latency during the build.

Use online or concurrent index creation where the database engine supports it.

For PostgreSQL, consider:

~~~sql
CREATE INDEX CONCURRENTLY idx_products_store_id_id
ON products(store_id, id);
~~~

Concurrent creation still has caveats:

- it cannot run inside a normal transaction block;
- it can take longer;
- long-running transactions can delay it;
- a failed build may leave an invalid index;
- brief lock acquisition phases can still occur.

Run during a controlled period, monitor CPU, I/O, latency, and replication, then validate the target query plan. Remove redundant indexes separately and cautiously.

---

## 13. How do you determine whether an index helped production?

Compare equivalent workloads before and after the change.

Database evidence:

- index usage statistics;
- actual execution time;
- estimated and actual rows;
- buffers and disk reads;
- scan method;
- sorting and filtering work;
- write latency;
- replication lag;
- storage growth.

Application evidence:

- endpoint p50, p95, and p99 latency;
- timeout and error rates;
- database time in APM traces;
- connection-pool utilization;
- request throughput;
- database CPU, memory, and I/O.

Index usage statistics show that an index is being used, but they do not prove that it is helping. A frequently used index can still produce a poor plan.

A sequential scan is not automatically a regression if it is cheaper for the actual result size.

---

## 14. What if SQL takes 10 ms but the API takes 800 ms?

The measured SQL execution may be only one part of the request. Investigate:

- connection-pool acquisition;
- all database queries, including hidden lazy loads;
- database lock wait;
- application-to-database network time;
- ORM hydration;
- Python transformations and loops;
- external HTTP or storage calls;
- middleware, authorization, logging, and tracing;
- response serialization;
- payload size and network transfer;
- blocking synchronous work inside an async application.

Use a distributed trace or stage-level timing to separate these components. Do not assume the remaining latency belongs to the database.

---

## Common mistakes

- Assuming every slow API is caused by slow SQL.
- Assuming an index must always be used.
- Adding an index to every filtered column.
- Treating index usage statistics as proof of improvement.
- Ignoring data skew and actual production parameters.
- Applying functions to indexed columns without considering sargability.
- Using SELECT star when a narrow projection is sufficient.
- Assuming a composite index works equally well for every column order.
- Assuming keyset pagination is strictly O(1) or immune to all data changes.
- Ignoring a deterministic tie-breaker in cursor pagination.
- Treating a sequential scan as automatically bad.
- Running EXPLAIN ANALYZE on writes without a safe execution plan.
- Increasing work memory globally to fix one sort spill.
- Creating an index without checking disk space and replication impact.
- Changing indexes, query shape, pool size, and application code simultaneously.
- Measuring only average latency instead of p95 and p99.
- Assuming GraphQL automatically solves N+1.
