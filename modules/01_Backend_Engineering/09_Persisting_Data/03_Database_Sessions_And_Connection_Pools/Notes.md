# Topic 09.03 — Database Sessions and Connection Pools

> A database connection is a live communication channel to the database. A connection pool keeps a managed set of reusable connections so requests can use them without creating a new network connection every time.

## 1. What is a database connection?

When an application connects to PostgreSQL or another database, several things happen:

1. The application opens a network connection to the database.
2. The database authenticates the client.
3. The database creates server-side resources for that connection.
4. The application can send SQL and receive results.

The connection is not just a Python object. It represents a live client-server relationship.

~~~text
FastAPI process ── database connection ──> Database server
~~~

## 1.1 Is a database connection also TCP?

When the database is on another machine, the database connection is usually a TCP connection to the database host and port. PostgreSQL commonly listens on port 5432.

The flow is:

~~~text
FastAPI application
    ↓
Database driver
    ↓
TCP connection to database:5432
    ↓
PostgreSQL server
~~~

A local database may instead use a Unix domain socket, but TCP is the common choice for a remote database.

A database connection does not use HTTP. It uses the database engine's own wire protocol.

## 1.2 How does a SQL query travel?

The application does not manually convert SQL into bytes. The database driver does this:

~~~text
SQL statement + parameter values
    ↓
Database wire-protocol messages
    ↓
Bytes
    ↓
TCP socket
    ↓
Database server
~~~

The database response follows the reverse path:

~~~text
Database result bytes
    ↓
Driver parses the response
    ↓
Python rows or objects
~~~

For a database connection without TLS, database-protocol bytes travel over TCP. With database TLS enabled:

~~~text
Database protocol message
    ↓
TLS encryption
    ↓
TCP carries encrypted TLS records
~~~

This is similar to HTTPS at the transport level, but the application protocol is different:

~~~text
HTTPS:   HTTP message → TLS → TCP
Database: database protocol → optional TLS → TCP
~~~

## 1.3 How database authentication works

A database does not use an HTTP Authorization header. The database driver authenticates when it creates a physical connection.

A typical sequence is:

1. TCP connection is established.
2. Optional TLS negotiation occurs.
3. The client sends startup information such as database name and username.
4. The database requests authentication.
5. The client proves its identity using a password, token, certificate, or another configured mechanism.
6. The database creates an authenticated session.
7. SQL operations can begin.

Common mechanisms include:

- Username and password
- SCRAM or another password challenge mechanism
- Client TLS certificates
- Kerberos or enterprise identity
- Cloud IAM tokens
- Unix socket or peer authentication
- A database proxy or connector

Authentication and authorization are different:

~~~text
Authentication → Who is this client?
Authorization  → What may this client do?
~~~

For example, a database role may be allowed to read and insert products but not drop tables.

Credentials should come from secret management, environment configuration, or a cloud identity mechanism. They should not be placed in HTTP headers for database use or written to logs.

## 1.4 What server-side resources does a connection use?

A database connection is not only a Python object. The database server may allocate:

- A backend process or worker
- A connection slot counted against the database limit
- Memory for connection and session state
- A network socket and buffers
- The authenticated role
- Transaction state
- Session settings
- Temporary tables or prepared statements
- Locks held by the session
- Query execution memory while SQL is running

Some resources are used even while the connection is idle.

For example:

~~~text
5 application pods × 20 pool connections each
≈ 100 database sessions
~~~

This is why pool sizes must be planned together with the database's maximum connection limit.

Closing a connection releases connection-specific resources. Returning a connection to a pool keeps it reusable, but the connection must be cleaned so unfinished transactions, locks, or session settings do not affect the next request.

## 2. Why not create a new connection for every request?

This approach is simple conceptually:

~~~text
Request arrives
    ↓
Open database connection
    ↓
Run query
    ↓
Close connection
    ↓
Return response
~~~

But under load it can cause:

- Connection setup overhead
- More authentication work
- Too many database server processes or resources
- Slow response times
- Connection storms when traffic increases
- Exhaustion of the database's maximum connection limit

The application and database both have finite resources.

## 2.1 Connection pooling versus HTTP connection reuse

The concepts are related but belong to different protocols.

Normal HTTP/1.1 connections are usually persistent and may be reused for multiple sequential requests. HTTP/2 can multiplex multiple requests over one TCP connection. SSE is different because one HTTP response remains open continuously.

A database pool maintains several reusable database-protocol connections:

~~~text
Pool
 ├── DB connection 1: idle
 ├── DB connection 2: in use
 └── DB connection 3: idle
~~~

For each database operation:

~~~text
Request arrives
    ↓
Borrow an idle database connection
    ↓
Send SQL over the existing connection
    ↓
Receive the database response
    ↓
Commit or roll back
    ↓
Return the connection to the pool
~~~

The connection is returned to the pool, not closed. If the pool has no available connection, the request waits or reaches the checkout timeout.

The pool does not necessarily send a query continuously to keep every connection alive. It manages connection lifetime, health checks, keepalive probes, and replacement of broken or expired connections.

## 3. What is a connection pool?

A connection pool creates and manages a limited number of database connections.

~~~text
Application startup
    ↓
Pool opens a controlled set of connections
    ↓
Request borrows one connection
    ↓
Request runs database work
    ↓
Request returns the connection to the pool
~~~

The connection is usually not closed after every request. It is reset and made available for another request.

A pool is therefore a shared resource manager, not a single database connection.

## 4. Pool checkout and return

A request should borrow a connection for the shortest safe period:

~~~text
Pool
 ├── Connection 1: available
 ├── Connection 2: in use
 └── Connection 3: available

Request A → borrows Connection 2
Request A → executes SQL
Request A → commits or rolls back
Request A → returns Connection 2
~~~

The connection must be returned even when an exception occurs. Context managers or framework-managed dependencies are normally used for this.

If all connections are busy, a new request waits until:

- A connection becomes available, or
- The pool checkout timeout expires

## 5. Pool size is not unlimited concurrency

Suppose:

- Pool size = 10
- Concurrent requests needing the database = 100

Only a limited number can use the database at the same time. The others wait.

This is intentional. Allowing 100 requests to create 100 database connections could overwhelm the database.

Pool sizing must consider:

- Database maximum connections
- Number of application instances
- Expected concurrent database work
- Query duration
- Other database clients
- Safety margin for administrative access

If there are 5 application pods and each pool allows 20 connections, the database may receive up to approximately 100 connections before considering other clients.

## 6. Connection versus session

The word session can mean different things depending on the library.

### Database connection

A physical or logical communication channel to the database server.

### Database session

The database server's state associated with a connection, including transaction state and session settings.

### ORM session

Some ORM libraries use Session for an application-level unit of work. It may borrow a physical connection from a pool only when database work begins.

Do not automatically assume that an ORM Session is the same thing as a physical TCP connection.

## 7. Transaction scope

A connection can have transaction state:

~~~text
Borrow connection
    ↓
Begin transaction
    ↓
Run related statements
    ↓
Commit or roll back
    ↓
Return clean connection to pool
~~~

A connection returned to the pool must not retain an unfinished transaction. Otherwise, the next request could inherit uncommitted changes, locks, or an unexpected transaction state.

The application should define clearly:

- Where a transaction begins
- Which operations belong to it
- Where it commits
- How it rolls back on failure
- When the connection is returned

## 8. Pool lifecycle in a FastAPI application

A common lifecycle is:

~~~text
Application startup
    ↓
Create or open the pool
    ↓
Requests use the pool
    ↓
Application shutdown
    ↓
Close the pool gracefully
~~~

The pool should normally be created once per application process, not once inside every endpoint call.

Each worker process generally has its own pool. Therefore, pool limits must be calculated across all workers and pods.

## 9. What pool settings generally control

Different libraries use different names, but common settings include:

| Setting | General meaning |
|---|---|
| Minimum size | Connections kept ready or created as the pool grows |
| Maximum size | Maximum connections this pool may hold |
| Checkout timeout | How long a request waits for an available connection |
| Maximum lifetime | Maximum age of a connection before replacement |
| Idle timeout | How long an unused connection may remain |
| Health check | Whether a connection is tested before use or while maintained |
| Keepalive | Mechanism for detecting or keeping network connections alive |

These settings improve connection management, but they do not make a failed database available. If the database is down, the pool can only wait, discard bad connections, retry pool maintenance, or raise an error according to its configuration.

## 10. Pooling does not solve every database problem

A connection pool does not automatically solve:

- Slow SQL queries
- Missing indexes
- Deadlocks
- Incorrect transactions
- Too many concurrent requests
- Database overload
- Application retry duplication
- Long-running transactions
- Poor connection limits
- Incorrect error handling

Pooling improves connection reuse and limits, but the application still needs query diagnosis, transaction design, and backpressure.

## 11. Request-level database dependency

Conceptually, a request dependency might work like this:

~~~python
async def get_connection():
    async with pool.connection() as connection:
        yield connection
~~~

The framework can then inject the connection into a repository or service for that request.

The exact code depends on the driver or ORM. The important lifecycle is:

~~~text
Borrow → use → commit/rollback → return
~~~

## 12. What happens when the database is unavailable?

Several failure points are possible:

1. The pool cannot open a new connection.
2. A checked-out connection is broken.
3. The pool waits for a connection and reaches its checkout timeout.
4. A query fails after the connection is obtained.
5. A transaction fails and must roll back.

The client may receive an application error such as 503 Service Unavailable when the dependency is temporarily unavailable, but the exact mapping belongs at the HTTP boundary.

Do not automatically retry every database operation. A read may often be retried under carefully defined conditions. A write needs much more caution because the database may have committed the change before the connection failed.

## Mental model

~~~text
Pool     → manages reusable database connections
Request  → temporarily borrows one
Session  → library-dependent unit of database work
Service  → decides business operation and transaction intent
Repository → executes database interaction
Database → durable state and constraint authority
~~~

## What comes next

This subtopic intentionally does not yet cover:

- A specific ORM
- SQLAlchemy Session implementation
- Async driver configuration
- Migration tooling
- Isolation levels
- Detailed pool sizing calculations
- Query performance diagnosis

Those will be introduced in separate subtopics or labs.
