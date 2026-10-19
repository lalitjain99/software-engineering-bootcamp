# Observations — Query Performance and Optimization

Run the lab first:

~~~bash
python modules/01_Backend_Engineering/09_Persisting_Data/06_Query_Performance_And_Optimization/Hands_On/main.py
~~~

Record the output and answer in your own words.

## 1. N+1 query pattern

How many SQL statements did the N+1 version execute? How many did the batched version execute?

Why does the N+1 query count grow as the number of products grows?

## 2. Sargability

Compare the plan for the strftime filter with the direct date-range predicate.

Why is applying a function to the date column often less index-friendly?

What would you verify with PostgreSQL EXPLAIN ANALYZE?

## 3. Composite index

What changed after creating the index on:

~~~text
(store_id, category, price)
~~~

Why does this order match the filter and sort pattern?

Would the same index be equally useful for a query filtering only by category? Explain.

## 4. Projection

Compare loading full Product entities with selecting only id, name, and price.

What work can be avoided when the endpoint does not need every column?

## 5. Pagination

Compare the offset and keyset query plans.

Why can OFFSET become more expensive as the page number increases?

What must be true about the ordering column for keyset pagination to be reliable?

## 6. Query count

Why is query count per request a useful metric even when each individual query is fast?

## 7. Local timing limitations

Why should local elapsed time not be treated as a production benchmark?

Consider:

- dataset size;
- cache warmth;
- hardware;
- concurrent requests;
- database engine;
- statistics;
- network latency.

## 8. Production extension

What would you change to repeat this lab against PostgreSQL?

Consider:

- connection URL and credentials;
- EXPLAIN ANALYZE and BUFFERS;
- realistic data volume and skew;
- representative query parameters;
- p95 and p99 latency;
- write-side index cost;
- cleanup and rollback.
