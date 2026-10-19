# Observations — Query Performance and Optimization

Run the lab first:

~~~bash
python modules/01_Backend_Engineering/09_Persisting_Data/06_Query_Performance_And_Optimization/Hands_On/main.py
~~~

The lab creates 2,000 products and 100 customers in SQLite. The observations
below answer the questions using the lab's code and SQLite query plans. Exact
plan wording and elapsed times can vary by SQLite version, data, and machine.

## 1. N+1 query pattern

**How many SQL statements did the N+1 version execute? How many did the batched version execute?**

**Answer:** The N+1 version executes **21 statements** for 20 products: one
product query and one customer query for each product. The batched version
executes **2 statements**: one product query and one customer query using an
`IN` predicate for the customer IDs.

**Why does the N+1 query count grow as the number of products grows?**

**Answer:** The code runs a customer lookup inside the product loop, so each
additional product adds another statement. Its count is approximately $1 + N$,
where $N$ is the number of products. The batched example uses two statements
regardless of the number of products, though very large ID sets may need to be
split into batches due to database parameter limits.

## 2. Sargability

**Compare the plan for the strftime filter with the direct date-range predicate.**

**Answer:** The `strftime` predicate scans the date index as a covering index
(`SCAN products USING COVERING INDEX idx_products_order_date`) instead of
seeking directly to the matching year. The range predicate uses an indexed
search (`SEARCH products USING COVERING INDEX idx_products_order_date
(order_date>? AND order_date<?)`).

**Why is applying a function to the date column often less index-friendly?**

**Answer:** Applying a function to each stored value changes the expression
being compared, so an ordinary index on the original column usually cannot
directly seek to the matching values. Comparing the column directly against
inclusive and exclusive bounds keeps the predicate sargable. The half-open
range from `2026-01-01` inclusive to `2027-01-01` exclusive correctly includes
all timestamps in 2026.

**What would you verify with PostgreSQL EXPLAIN ANALYZE?**

**Answer:** Use `EXPLAIN (ANALYZE, BUFFERS)` with representative parameters and
verify estimated versus actual rows, scan/index conditions, buffer hits and
reads, sort nodes, and execution time. A sequential scan may still be best when
many rows match. `ANALYZE` executes the query, so use care with statements that
modify data.

## 3. Composite index

**What changed after creating the index on `(store_id, category, price)`?**

**Answer:** Before the index, SQLite reports a table scan and a temporary B-tree
for sorting. Afterward, it searches the composite index using the `store_id`
and `category` equality predicates; the index ordering by `price` can avoid a
separate sort. Because `name` is selected but is not part of the index, this
query is not fully covered by the index.

**Why does this order match the filter and sort pattern?**

**Answer:** The first two columns match the equality filters, and the final
column matches the requested ordering. This arrangement lets the database
narrow to the matching store and category and read those entries in price order.

**Would the same index be equally useful for a query filtering only by category? Explain.**

**Answer:** No. B-tree indexes are most useful from their leftmost prefix. A
category-only filter does not constrain the leading `store_id` key, so an index
beginning with `category` may be more suitable. Index decisions should follow
measured workloads because indexes also consume storage and add write work.

## 4. Projection

**Compare loading full Product entities with selecting only id, name, and price.**

**Answer:** Loading `Product` selects all mapped columns and constructs
SQLAlchemy ORM objects, which are tracked in the session. The projection
returns only the three requested columns as row values. Both versions execute
one SQL statement in this example.

**What work can be avoided when the endpoint does not need every column?**

**Answer:** The database reads and returns less data, and SQLAlchemy avoids
constructing full entities and tracking them in the identity map. This reduces
data transfer and ORM materialization work, especially when rows or result sets
are wide or large.

## 5. Pagination

**Compare the offset and keyset query plans.**

**Answer:** The offset query scans rows in ID order and skips 1,000 rows before
returning 50. The keyset query seeks from `id > 1000` using the integer primary
key (`SEARCH products USING INTEGER PRIMARY KEY (rowid>?)`) and returns the next
50 rows.

**Why can OFFSET become more expensive as the page number increases?**

**Answer:** The database generally has to walk past all preceding rows to reach
the requested page, including rows that it will discard. That work grows with
the offset depth.

**What must be true about the ordering column for keyset pagination to be reliable?**

**Answer:** The ordering must be stable and provide an unambiguous cursor. The
example uses a unique, immutable `id`. If ordering by a non-unique field such as
`price`, add a unique tie-breaker (such as `id`) and include both values in the
cursor condition.

## 6. Query count

**Why is query count per request a useful metric even when each individual query is fast?**

**Answer:** Database round trips add latency, and N+1 behavior can make the
number of statements grow with the result size. Query count can reveal this
growth before individual queries appear slow. It is only one signal; query
plans, rows read, payload size, lock waits, and end-to-end latency also matter.

## 7. Local timing limitations

**Why should local elapsed time not be treated as a production benchmark?**

**Answer:** This lab uses a small local SQLite database, while production can
have different data volume and skew, cache state, hardware, concurrency,
database engine and statistics, and network latency. A single local timing is
not representative or stable. Use repeated measurements, representative load,
query plans, and latency percentiles such as p50, p95, and p99.

## 8. Production extension

**What would you change to repeat this lab against PostgreSQL?**

**Answer:** Configure a PostgreSQL SQLAlchemy driver and a connection URL from
environment/configuration rather than hard-coding credentials. Create the same
schema and indexes, load realistic data volume and skew, and refresh statistics
with `ANALYZE`. Use `EXPLAIN (ANALYZE, BUFFERS)` with representative query
parameters, measure application latency under repeated and concurrent runs,
and report p95/p99 as well as query plans. Account for index storage and
write-side costs, and run destructive experiments on a disposable database or
in a safely rolled-back transaction.