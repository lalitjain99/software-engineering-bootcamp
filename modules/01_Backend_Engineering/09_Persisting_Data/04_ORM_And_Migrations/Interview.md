# Interview Guide: ORM and Database Migrations

## 1. Why do we need SQL knowledge if we use an ORM?

An ORM reduces repetitive application code, but the database still executes SQL.

SQL knowledge is needed to:

- inspect generated queries;
- identify expensive joins or missing filters;
- diagnose N+1 queries;
- understand indexes, constraints, transactions, and locks;
- compare query plans and performance;
- use database-specific features when necessary.

A short ORM expression can still generate inefficient SQL.

## 2. How does an ORM map Python concepts to database concepts?

| Python or ORM concept | Database concept |
|---|---|
| Class | Table |
| Object instance | Row |
| Attribute | Column |
| Object identifier | Primary key |
| Relationship | Foreign key plus ORM relationship configuration |
| ORM query | SQL statement |

The foreign key connects tables at the database level. ORM relationship configuration controls how the application navigates that connection.

## 3. What happens when an object is added to an ORM session?

~~~python
product = Product(name="Keyboard", sku="KEY-101", price=2500)
session.add(product)
~~~

The object is attached to the ORM session and becomes pending. The ORM tracks it in its unit of work, but an INSERT may not have been sent yet.

The row is not necessarily persisted merely because add was called.

## 4. What is flush?

Flush sends pending ORM changes to the database inside the current transaction.

For example:

~~~text
session.add(product)
       ↓
session.flush()
       ↓
INSERT is sent to the database
~~~

The transaction is still uncommitted and can still be rolled back. Flush may also happen automatically before certain queries or during commit.

A generated primary key may be populated on the Python object after flush, depending on the ORM and database configuration.

## 5. What is the difference between flush, commit, and rollback?

- Flush sends pending SQL to the database inside the current transaction.
- Commit finalizes the transaction and makes successful changes durable.
- Rollback discards uncommitted changes and releases transaction-held locks.

After a flush or commit failure, rollback is usually required before the ORM session can be used again.

## 6. What happens when a database constraint fails?

Suppose a duplicate SKU violates a UNIQUE constraint.

The application should:

1. catch the database or ORM integrity exception;
2. roll back the failed transaction;
3. translate it into an application-level error;
4. return a suitable HTTP response.

A duplicate resource commonly maps to:

~~~text
409 Conflict
~~~

The raw database error should not be exposed to the client.

## 7. What is an ORM session?

An ORM session is a stateful, library-level unit of work. It can track:

- loaded objects;
- pending changes;
- transaction state;
- identity-map state;
- a borrowed database connection.

An ORM session is not automatically the same as a physical database connection. It may borrow a connection from the pool only when database communication is required.

## 8. Why should an ORM session not be shared globally?

A global session can allow concurrent requests to share:

- pending changes;
- transactions;
- object identity-map state;
- rollback and commit operations;
- locks and connections.

Request B could accidentally commit Request A's changes, or one request could roll back another request's work.

The usual lifecycle is:

~~~text
Create session
   ↓
Perform one unit of work
   ↓
Commit on success
   ↓
Rollback on failure
   ↓
Close or reset
~~~

The session should normally be scoped to one request or one deliberate unit of work.

## 9. What is lazy loading?

Lazy loading fetches a related object only when the application accesses it.

~~~python
orders = session.query(Order).all()

for order in orders:
    print(order.customer.name)
~~~

The ORM first loads the orders. Accessing order.customer may then trigger another query for each customer.

## 10. What is the N+1 query problem?

The N+1 pattern occurs when the application executes:

~~~text
1 query for the parent records
+ N queries for related records
~~~

For 100 orders, this could become 101 queries.

It can cause:

- high database load;
- increased network round trips;
- high endpoint latency;
- connection pool exhaustion.

The exact number may be lower when related objects are shared and already present in the ORM identity map, but the pattern remains dangerous.

## 11. How do you detect N+1 queries?

Look for:

- high query count per endpoint request;
- query count increasing linearly with page size;
- repeated SQL statements with different IDs;
- database QPS increasing without proportional user traffic;
- high connection hold time;
- slow endpoint traces containing many database spans.

During development:

- enable ORM SQL logging;
- count statements in tests;
- inspect the generated SQL;
- compare a request with 10 records and 100 records.

There is no universal threshold such as 50 or 200 queries. The expected query count depends on the endpoint.

## 12. What is eager loading?

Eager loading fetches related data deliberately before the application accesses it.

### joinedload

joinedload commonly uses one query with a JOIN. It is often suitable for many-to-one or one-to-one relationships:

~~~text
Product → one Store
~~~

### selectinload

selectinload commonly uses two controlled queries:

~~~text
1. Fetch parent rows
2. Fetch related rows with WHERE foreign_key IN (...)
~~~

It is often a good choice for one-to-many collections:

~~~text
Store → many Products
~~~

A one-to-many join repeats parent columns for each child row. Joining multiple collections can multiply rows significantly, so the choice should be validated using result size and query plans.

## 13. What are alternatives to eager loading?

Other approaches include:

- explicit joins with a projection when only selected fields are needed;
- batch loading with an IN query;
- a request-scoped DataLoader for GraphQL or complex service layers;
- changing the response shape to avoid unnecessary relationships;
- database-level aggregation for summary or read-model endpoints.

The general principle is:

> Fetch only the data required, in as few well-designed queries as possible.

DataLoader caching should usually be scoped to a request to avoid stale or cross-user data.

## 14. When should raw SQL be used instead of an ORM?

Raw SQL is useful for:

- complex reports;
- CTEs and window functions;
- database-specific features;
- bulk operations and migrations;
- performance-critical queries;
- situations where explicit query control is clearer.

ORM and raw SQL can coexist. Raw SQL must still use parameter binding.

## 15. What is a database migration?

A migration is a versioned, ordered, repeatable change to the database schema.

Examples include:

- creating a table;
- adding a column;
- adding an index;
- adding a foreign key;
- changing a constraint.

Changing the Python model alone does not safely alter an existing production table.

## 16. Why should migration files be committed to version control?

Migration files provide:

- schema history;
- reproducible environments;
- reviewable changes;
- controlled deployment order;
- an audit trail;
- a basis for recovery planning.

A migration is not always automatically reversible. Dropped or transformed data may require a corrective migration or backup restore.

## 17. What is expand-and-contract?

Expand-and-contract separates a breaking schema change into compatible phases.

For a column rename:

1. Add the new column.
2. Deploy code that can read both columns.
3. Dual-write to both columns.
4. Backfill existing data.
5. Switch all reads and writes to the new column.
6. Remove the old column in a later migration.

This supports rolling deployments where old and new application versions run simultaneously.

## 18. Why are immediate column removals risky?

Old application instances may still issue queries referencing the old column. If it is removed immediately, those instances fail with database errors.

Keep the old schema until all application instances no longer depend on it.

## 19. What is the difference between a schema migration and a data backfill?

A schema migration changes database structure using DDL:

~~~sql
ALTER TABLE products ADD COLUMN category TEXT;
~~~

A data backfill changes existing row contents using DML:

~~~sql
UPDATE products
SET category = 'General'
WHERE category IS NULL;
~~~

Schema changes are often short structural operations. Backfills may run for a long time and need batching, throttling, progress tracking, and monitoring.

## 20. Why is a million-row backfill in one transaction risky?

A very large transaction can cause:

- high WAL or transaction-log volume;
- long-lived row versions and table bloat;
- lock contention;
- replication lag;
- long rollback time;
- all-or-nothing loss if the final step fails.

Smaller batches reduce lock duration, limit resource usage, allow progress to be committed, and make retries easier.

## 21. How do you make a backfill resumable?

Use:

- a stable indexed ordering such as an ID;
- bounded batches;
- a checkpoint table or progress record;
- one commit per batch;
- an idempotent update condition;
- monitoring and retry handling.

A typical flow is:

~~~text
Read next batch
   ↓
Update batch
   ↓
Commit batch and checkpoint together
   ↓
Repeat
~~~

Avoid relying only on large OFFSET values because they become slower and can behave poorly when data changes during processing.

## 22. How should migration risks be assessed?

Before production execution, evaluate:

- migration duration;
- table and row locks;
- blocking reads and writes;
- database CPU, memory, I/O, and disk usage;
- replication lag;
- compatibility with old and new application versions;
- concurrent migration execution;
- partial-failure behavior;
- rollback or forward-repair strategy;
- backup and recovery plan.

## 23. What should be monitored during a backfill?

Monitor:

- rows processed and remaining;
- batch duration;
- rows per second;
- failed batches and retries;
- database CPU, memory, I/O, and disk;
- lock waits;
- replication lag;
- application latency and error rate;
- final data-validation results.

## Common mistakes

- Assuming the ORM removes the need to understand SQL.
- Treating ORM sessions as physical database connections.
- Sharing one ORM session globally across requests.
- Forgetting rollback after a flush or commit failure.
- Assuming add permanently stores a row.
- Confusing flush with commit.
- Triggering N+1 queries through lazy relationship access.
- Assuming joined loading is always faster.
- Using raw SQL without parameter binding.
- Changing a model without creating a migration.
- Dropping a column before all application versions stop using it.
- Running a million-row backfill in one transaction.
- Updating the backfill checkpoint separately from the batch data.
- Trusting generated migrations without reviewing the SQL.
