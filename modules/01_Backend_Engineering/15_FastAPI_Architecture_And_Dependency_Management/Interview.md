# Topic 15 — FastAPI Architecture and Dependency Management

## 1. Why separate routers, services, repositories, and schemas?

Each layer has a focused responsibility:

- **Router:** HTTP entry point; parses request data and creates HTTP responses.
- **Schema:** Defines and validates request and response data.
- **Service:** Contains business rules and application use cases.
- **Repository:** Handles persistence and database queries.
- **Dependency module:** Constructs and supplies required objects.

This separation improves maintainability, testability, and reuse. For example, the same service can be called from an HTTP route, a background worker, or a GraphQL resolver.

---

## 2. What does Depends do?

Depends tells FastAPI that an endpoint requires another callable to provide a value.

For example, when a route declares a ProductService dependency:

1. FastAPI receives the request.
2. It resolves the dependency function.
3. The dependency creates the repository and service.
4. FastAPI passes the service into the route.
5. The route uses the injected service.

The route does not need to construct the service manually.

---

## 3. Why should the router not construct the service directly?

Direct construction couples the router to repository and database details.

If the router creates the service itself:

- replacing the repository becomes harder;
- tests must construct real dependencies;
- database setup can leak into HTTP tests;
- dependency lifetimes become unclear.

Dependency injection keeps construction in one place and allows tests to replace real dependencies with fakes.

---

## 4. Why should a service raise a domain exception instead of HTTPException?

A service should not depend on HTTP because it may be used by:

- a FastAPI route;
- a background worker;
- a command-line script;
- a GraphQL resolver;
- another internal application component.

The service should raise an application-level exception such as ProductNotFoundError.

The router translates that exception into the external HTTP contract:

~~~text
ProductNotFoundError
        ↓
FastAPI router
        ↓
HTTP 404 response
~~~

This keeps business logic independent of the transport protocol.

---

## 5. What should happen when a repository returns no product?

The responsibility is divided across layers:

1. The repository queries its data source.
2. If no row is found, it returns None.
3. The service interprets None as a business condition.
4. The service raises ProductNotFoundError.
5. The router converts it into HTTP 404.

The repository reports data-access results; the service makes the application-level decision.

---

## 6. What is a request-scoped dependency using yield?

A yield dependency can manage setup and cleanup around one request.

~~~text
Dependency setup
        ↓
yield object to endpoint
        ↓
Endpoint executes
        ↓
finally block performs cleanup
~~~

Typical uses include:

- database sessions;
- transactions;
- temporary files;
- request-scoped locks;
- per-request external-client resources.

The code before yield runs before the endpoint. The code in finally runs after the request, including when the endpoint raises a handled exception.

Cleanup is not guaranteed if the entire process is abruptly killed, such as by SIGKILL, a machine crash, or an out-of-memory termination.

---

## 7. Why is cleanup placed in finally?

finally runs during normal success and exception unwinding.

Therefore, resources can be released when:

- the endpoint succeeds;
- the endpoint raises HTTPException;
- the service raises a domain exception;
- the request is cancelled normally.

Without cleanup, database sessions, locks, files, or connections may remain open and eventually exhaust resources.

Production resources should still have timeouts and recovery mechanisms because abrupt process termination can bypass application cleanup.

---

## 8. What is the difference between request-scoped and application-scoped resources?

A request-scoped resource belongs to one request:

~~~text
Request starts → create or borrow resource
Request ends   → close or return resource
~~~

An application-scoped resource belongs to the application lifetime:

~~~text
Application startup  → create resource
Many requests        → reuse resource
Application shutdown → close resource
~~~

Examples:

| Resource | Typical lifetime |
|---|---|
| Database session | Request |
| Database connection pool | Application |
| Shared HTTP client | Application |
| Redis client/pool | Application |
| Temporary transaction | Request |

A connection pool should not be created for every request. A request should borrow a connection or session from the application-level pool.

---

## 9. How does FastAPI lifespan work?

A lifespan context has two phases separated by yield:

~~~text
Before yield:
    application startup
    create shared resources
    store them in app.state

During yield:
    serve requests

After yield:
    application shutdown
    close shared resources
~~~

The lifespan is appropriate for database pools, Redis clients, shared HTTP clients, and other reusable resources.

---

## 10. What is app.state?

app.state is application-owned storage for objects that should be shared by requests handled by that application instance.

During startup:

~~~python
app.state.shared_resource = resource
~~~

During a request:

~~~python
request.app.state.shared_resource
~~~

The request points to the same FastAPI application instance, so it can retrieve the object stored in that application's state.

The state is process-local. If the application runs in multiple workers or pods, each process or pod has its own application state.

---

## 11. Why use a lifespan resource instead of a module-level global?

A module-level global is usually created during Python import. That can cause:

- side effects during module import;
- connection attempts before application startup;
- unclear shutdown behavior;
- difficult testing;
- resources being created even when the application is not running.

A lifespan-managed resource has explicit startup and shutdown ownership, making its lifecycle easier to reason about and test.

---

## 12. How should router tests use dependencies?

Router tests should test the HTTP contract rather than real databases or external services.

Use app.dependency_overrides to replace the real service dependency with a fake service.

The fake service can:

- return a deterministic product for the success case;
- raise ProductNotFoundError for the failure case.

Then assert:

- HTTP status code;
- response body;
- error translation;
- response schema.

The override must be removed after each test to prevent test-order-dependent failures.

---

## 13. How does a pytest fixture with yield work?

A pytest fixture can also separate setup and cleanup:

~~~text
Before yield:
    install dependency override
    create TestClient

yield:
    test uses the client

After yield:
    remove dependency override
    close resources
~~~

The fixture's yield is conceptually similar to a FastAPI yield dependency, but the lifecycle is different:

- FastAPI dependency: one request;
- pytest fixture: one test or fixture scope.

Using TestClient as a context manager also runs application startup and shutdown events.

---

## 14. What should service tests verify?

Service tests should verify application behavior and business rules:

- correct interpretation of repository results;
- validation of business conditions;
- correct domain exception;
- correct normalization or transformation;
- correct repository method and arguments.

They should use a fake or mocked repository, not a real database.

A service test should answer:

> Was the business decision correct?

---

## 15. What should repository tests verify?

Repository tests should verify real data-access behavior:

- database connection and session handling;
- generated query behavior;
- correct inserts, updates, and reads;
- mapping database rows to application objects;
- unique and foreign-key constraints;
- transaction commit and rollback.

They should use a real isolated test database, never production data.

SQLite can be useful for simple portable SQL, but PostgreSQL integration tests are needed when production depends on PostgreSQL-specific types, SQL, locking, isolation, or constraints.

---

## 16. What should router, service, and repository tests avoid testing?

Avoid duplicating responsibilities:

| Test type | Should verify | Should avoid |
|---|---|---|
| Router | HTTP contract and exception translation | Business rules and SQL |
| Service | Business decisions and domain exceptions | HTTP formatting and real database behavior |
| Repository | Queries, persistence, and constraints | HTTP status codes |

This keeps failures localized and makes refactoring safer.

---

## 17. What happens if a dependency is unavailable during application startup?

A required lifespan resource should fail startup clearly if it cannot be initialized. The application should not silently start while its essential database pool or client is unavailable.

For request-time retrieval, a missing resource should raise an application configuration/lifecycle error, not a client error such as 400 or 404.

---

## 18. What common dependency-management mistakes should be avoided?

Common mistakes include:

- constructing services directly inside routers;
- putting database queries in route handlers;
- raising HTTPException from the service layer;
- creating a connection pool for every request;
- leaving sessions or connections unclosed;
- using module-level globals for lifecycle-managed resources;
- forgetting to clear dependency overrides in tests;
- using a real database in router unit tests;
- hiding too much behavior behind dependencies that are difficult to trace;
- creating circular imports between routers, dependencies, services, and repositories.

A good dependency graph should be explicit, acyclic, and easy to replace in tests.
