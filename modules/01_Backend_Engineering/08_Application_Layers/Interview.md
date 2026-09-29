# Topic 08 — Interview Questions: Application Layers

These answers were developed from the hands-on refactor and reviewed in chat. The goal is to separate responsibilities deliberately without creating layers that add no value.

## 1. How would you divide an order endpoint into router, service, and repository responsibilities?

Consider an operation that finds a customer, calculates a discount, saves an order, and returns an HTTP response.

### Router

The router defines the HTTP contract:

- Method and path, such as <code>POST /orders</code>
- Request and response schemas
- Path, query, header, and body inputs
- Success status code
- Translation of application exceptions into HTTP responses

It should call the service rather than query storage or calculate discounts itself.

### Service

The service performs the business use case:

- Ask the repository for the customer
- Decide what a missing customer means
- Calculate the discount
- Calculate the final order total
- Ask the repository to store the order

The service decides that a missing customer is an application failure and raises <code>CustomerNotFoundError</code>.

### Repository

The repository performs data-access operations:

- Find a customer
- Insert an order
- Read or update stored records
- Translate storage-specific results or errors where appropriate

The missing-customer flow is:

~~~text
Repository returns no customer
          ↓
Service raises CustomerNotFoundError
          ↓
Router catches the application exception
          ↓
Router returns HTTP 404
~~~

The service identifies the application outcome. The router decides its HTTP representation.

## 2. Why should a service avoid raising <code>HTTPException</code>?

A service may be called from a REST endpoint, GraphQL mutation, administration script, direct test, or another non-HTTP entry point.

If the service raises <code>HTTPException</code>, its business logic becomes coupled to FastAPI and HTTP. A normal Python caller would receive a transport-specific error that has no useful meaning outside an HTTP request.

The service should raise an application exception:

~~~python
raise CustomerNotFoundError("Customer not found")
~~~

Each caller handles it according to its own interface:

~~~text
FastAPI router → convert to HTTP 404
GraphQL layer  → return a GraphQL error
Python script  → log, report, skip, or stop
Test           → assert that the exception is raised
~~~

The service reports what happened. The caller decides how to present or process it.

## 3. Where should different kinds of validation live?

| Rule | Primary location | Reason |
|---|---|---|
| <code>"price": "expensive"</code> | Pydantic/request schema | The request value has the wrong structure or type |
| Price must be greater than zero | Pydantic schema when it is an API field constraint; service when context-dependent | Placement depends on whether it is structural or a business decision |
| Duplicate SKU is forbidden | Service | The service decides the business meaning of an existing SKU |
| Find an existing SKU | Repository | The repository retrieves current stored data |
| SKU must remain unique under concurrency | Database unique constraint | The database provides the final integrity guarantee |
| Only managers may approve refunds | Service or an authorization policy invoked by it | The rule must apply even when the caller is not the REST router |

A service-level duplicate check provides a clear expected outcome, but it cannot guarantee uniqueness under concurrency:

~~~text
Request A checks → not found
Request B checks → not found
Request A inserts
Request B inserts
~~~

A database unique constraint rejects the competing insert. The data-access layer handles the database-specific failure, and the application translates it into the appropriate application and HTTP outcome.

## 4. How would you test the router, service, and repository separately?

### Router/API tests

Verify the HTTP boundary:

- Methods and paths
- Request validation
- Path and query inputs
- Response schemas
- Status codes
- Translation of application exceptions into HTTP errors

For example, configure the service to raise <code>ProductNotFoundError</code> and verify that the client receives <code>404 Not Found</code>.

### Service tests

Verify business behaviour:

- Normalization
- Discount and pricing rules
- Duplicate-SKU decisions
- Missing-resource decisions
- Repository interactions
- Application exceptions

The service can be tested with an in-memory or fake repository containing controlled data.

### Repository tests

Verify storage behaviour:

- Queries return the correct records
- Inserts and updates persist correctly
- Parameters map correctly
- Unique and foreign-key constraints work
- Transactions commit and roll back
- Database errors are handled appropriately

A database repository test may require a test database, but it does not require Uvicorn.

FastAPI's <code>TestClient</code> sends HTTP-like requests directly to the ASGI application in the test process. It does not need a listening port or real network connection. A separate end-to-end test against a deployed application may use real networking.

## 5. Does every endpoint require every layer?

No. Layers should separate meaningful responsibilities, not satisfy a folder template.

A basic health endpoint may remain in the router:

~~~python
@router.get("/health")
def health():
    return {"status": "ok"}
~~~

Adding a service, repository, and custom exceptions would create pass-through code without solving a problem.

Order creation may justify separation because it coordinates customer validation, discount calculation, inventory reservation, persistence, and audit work.

Layering primarily improves:

- Maintainability
- Testability
- Reuse
- Change isolation
- Clarity of ownership

It does not automatically improve runtime scalability or performance.

A useful principle is:

> Add a boundary when it separates responsibilities that change for different reasons.

## 6. What changes when an in-memory repository is replaced with PostgreSQL?

Repository implementations change from dictionary operations to database operations:

- Database queries
- Connections, sessions, or pool usage
- Inserts and updates
- Transaction handling
- Storage-error translation

Database schema creation is normally managed through ORM models, migrations, and deployment processes rather than by recreating tables inside the repository constructor.

A repository should not normally hold one permanently checked-out connection created in its constructor. It should receive an appropriately scoped session or connection, or acquire resources through a managed pool.

The HTTP route functions should remain unchanged. Business decisions such as normalization and “duplicate SKUs are forbidden” should also remain unchanged if the repository provides the same required operations.

Application wiring must change to construct the PostgreSQL repository and provide its session or connection.

New concerns include:

- Connection and session lifecycle
- Connection pooling
- Transactions, commit, and rollback
- Migrations
- Unique and foreign-key constraints
- Indexes and query performance
- Concurrent requests
- Timeouts and temporary failures
- Secure parameterized queries
- Database integration testing

A database connection only makes the database reachable. It does not implement schemas, queries, constraints, transactions, or failure handling.

## 7. Why should the repository be provided to the service?

Compare:

~~~python
class ProductService:
    def __init__(self):
        self.repository = ProductRepository()
~~~

with:

~~~python
class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository
~~~

In the first design, the service controls which repository is created. Testing, replacing storage, and managing database resources become difficult.

In the second design, the caller supplies the dependency:

~~~python
repository = ProductRepository(initial_products=test_products)
service = ProductService(repository)
~~~

A production application can instead supply a PostgreSQL implementation:

~~~python
repository = PostgresProductRepository(database_session)
service = ProductService(repository)
~~~

This is constructor injection: instead of creating its dependency internally, the service receives it from outside.

Benefits include:

- Tests control their starting data
- Storage implementations can be replaced
- Database lifecycle remains outside business logic
- The service focuses on the use case
- Object creation is explicit

The duplicate-SKU rule remains in the service. Only the repository's method implementation changes.

A shared interface or Python <code>Protocol</code> can later formalize the operations required from different repository implementations.

## 8. What does behaviour-preserving refactoring mean?

A behaviour-preserving refactor improves internal structure without changing externally observable behaviour.

Changing any of the following is not behaviour-preserving:

- <code>409 Conflict</code> to <code>400 Bad Request</code>
- <code>/products/{product_id}</code> to <code>/items/{product_id}</code>
- Removing <code>category</code> from the response

Even if the router, service, and repository boundaries become cleaner, these changes can break existing clients.

An API's external contract includes:

- HTTP methods and paths
- Path and query parameters
- Required and optional headers
- Request-body schema
- Response-body schema
- Status codes
- Error response format
- Authentication and authorization expectations
- Documented operation semantics and side effects

API regression tests are valuable because they protect that contract while internal code is moved or reorganized.

An intentional client-visible change should be handled as a separate feature or API change. It may require compatibility analysis, API versioning, documentation, client migration, and a deprecation plan.

A database implementation can change during an internal refactor if observable behaviour remains stable. Changing business behaviour is normally a feature or policy change, not a refactor.

## Common Mistakes

### Equating behaviour with internal layer responsibilities

Behaviour-preserving refers to observable outcomes, not whether the internal code still uses the same files or classes.

### Putting storage operations in the service

The service decides what should happen. The repository performs the actual read or write.

### Raising <code>HTTPException</code> from the service or repository

This couples application and storage logic to HTTP and FastAPI.

### Treating a pre-insert duplicate query as a concurrency guarantee

Two requests can pass the check simultaneously. A database constraint provides the final guarantee.

### Catching every exception and returning <code>404</code>

Unexpected programming or infrastructure errors are not “not found.” Catch only expected application exceptions at the boundary that can handle them meaningfully.

### Creating database connections secretly inside business services

Resource creation and lifecycle should remain outside business logic.

### Assuming every endpoint needs every layer

Unnecessary pass-through classes increase maintenance cost without adding separation.

### Assuming layers automatically improve scalability

Layering improves code organization and changeability. Runtime scalability requires separate capacity, concurrency, storage, and infrastructure decisions.

### Calling every combined endpoint a Backend for Frontend

A combined response is an aggregation endpoint. It becomes a BFF when it belongs to a client-specific backend layer.

### Mixing API changes into a refactor

Client-visible contract changes should be reviewed, tested, documented, and released deliberately.
