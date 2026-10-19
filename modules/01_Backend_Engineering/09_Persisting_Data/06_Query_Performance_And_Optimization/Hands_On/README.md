# Hands-on Lab — Query Performance and Optimization

This lab uses SQLAlchemy and SQLite to make common query-performance problems visible.

SQLite is useful for learning query shape and query-count behavior. Its execution-plan output differs from PostgreSQL, so the lab also explains what should be verified with PostgreSQL in production.

## Learning objectives

You will observe:

1. The N+1 query pattern and a batched alternative.
2. A non-sargable date filter and a range-based filter.
3. A composite index for filtering and ordering.
4. The difference between selecting full entities and narrow projections.
5. Offset pagination and keyset pagination.
6. Query plans using SQLite EXPLAIN QUERY PLAN.
7. Query count and timing as performance signals.

## Run the lab

From the repository root:

~~~bash
uv sync
python modules/01_Backend_Engineering/09_Persisting_Data/06_Query_Performance_And_Optimization/Hands_On/main.py
~~~

The script creates a local SQLite database named performance_lab.db in this folder and recreates its data on every run.

## What the script prints

- query count and elapsed time for the N+1 and batched customer lookups;
- query plans for date filtering;
- query plans before and after the composite index;
- query plans for offset and keyset pagination;
- projection examples.

Query timings on a local laptop are not production benchmarks. Focus on the number of statements, plan shape, rows examined, and the reason one query form is more scalable.

## SQLite and production differences

SQLite uses EXPLAIN QUERY PLAN, while PostgreSQL and other production databases provide richer EXPLAIN and EXPLAIN ANALYZE output.

For production validation, repeat the important experiments against the same database engine, schema, statistics, data volume, and representative workload used in production.

## Observation exercise

Record your answers in observations.md:

1. How many queries did the N+1 version execute? How many did the batched version execute?
2. Why does query count grow with the number of products?
3. Which date predicate is more index-friendly and why?
4. What changed in the plan after adding the composite index?
5. Why does selecting specific columns reduce work?
6. Why can a deep OFFSET become more expensive than a keyset cursor?
7. Which measurements are more useful than a single local execution time?
8. What would you repeat differently against PostgreSQL?
