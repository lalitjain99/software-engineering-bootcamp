# Topic 15 Hands-On Observations

## Stage 1 — Layered FastAPI Product API

### Run information

- Date: 06-Nov-2026
- Python version: 3.14
- Command used: `uvicorn app.main:app --reload`

### Project structure

```
app/
    ├── main.py
    ├── api/
    │   └── routes/products.py
    ├── schemas/products.py
    ├── services/products.py
    ├── repositories/products.py
    ├── dependencies.py
```

### Endpoint verification

#### Existing product

- Request: `/products/101`
- Status code: `200`
- Response: `{"id": 101, "name": "Monitor", "price": 5000}`

#### Missing product

- Request: `/products/999`
- Status code: `404`
- Response: `{"detail": "Product with ID 999 was not found"}`

### Dependency flow

1. The request enters through a route in `app/api/routes/products.py`, and FastAPI resolves `get_product_service()` because the route parameter uses `Depends`.
2. `get_product_service()` constructs a `ProductRepository` and injects it into a new `ProductService`.
3. The route calls `ProductService.get_product(product_id)`, which delegates the lookup to `ProductRepository.find_product(product_id)`.
4. The repository searches its in-memory `products` dictionary and returns the matching product or `None`; the service converts `None` into `ProductNotFoundError`, which the router maps to HTTP 404.

### Architecture decisions

- Which module owns the data, and why?  
  `app/repositories/products.py` owns the product data. The repository is responsible for data storage and retrieval, keeping data access separate from HTTP and business logic.

- Where is the service constructed?  
  `get_product_service()` in `app/dependencies.py` constructs the repository and service.

- Why does the service raise a plain exception?  
  `ProductService` raises `ProductNotFoundError` so that domain/business-layer behavior remains independent of FastAPI HTTP concerns. This keeps the service reusable outside the web layer.

- Why does the router translate it to HTTP 404?  
  The router translates the domain exception into an HTTP response because only the API layer knows the external HTTP contract and which status code to return to the client.

### Review checklist

- [x] Router does not access product data directly
- [x] Service does not raise `HTTPException`
- [x] Repository has no FastAPI imports
- [x] Response schema hides internal fields
- [x] Product service is supplied through `Depends`
- [x] Application starts from `main.py`

### Production reflection

What would you change first if the in-memory repository were replaced with SQLite?

Answer: I would first implement SQLite inside `ProductRepository`, adding parameterized SQL queries and safe connection/session management without changing the route or service interfaces. I would also use FastAPI dependency lifecycles to provide and close database connections so each request uses a connection reliably and database resources are not leaked.

---

## Stage 2 — Request-Scoped Dependency Lifecycle

### Run information

- Date: 08-Nov-2026
- Python version: 3.14
- Command used: `uvicorn app.main:app --reload --log-level info`
- Stage 1 implementation was preserved unchanged in its original location.
- Stage 2 uses a separate implementation under `Stage_2_Request_Scoped_Lifecycle/`.

### Lifecycle implementation

Stage 2 adds a generator-based FastAPI dependency:

1. A `ResourceLifeCycleMarker` is created before the endpoint runs.
2. The dependency constructs the repository and service.
3. The service is provided to the route at the `yield` statement.
4. FastAPI executes the endpoint.
5. Code in the `finally` block runs after the request completes.
6. The lifecycle marker is closed even when the endpoint raises a handled exception.

The dependency uses a configured logger to record setup and cleanup events.

### Successful request verification

Request:

```
GET /products/101
```

Observed logs:

```
INFO: [Lifecycle] Request scoped resource initiated
INFO: 127.0.0.1 - "GET /products/101 HTTP/1.1" 200 OK
INFO: [Lifecycle] Request scoped resource cleaned up
```

Result: the resource was initialized before the route executed and cleaned up after the successful request.

### Failed request verification

Request:

```
GET /products/999
```

Observed logs:

```
INFO: [Lifecycle] Request scoped resource initiated
INFO: [Lifecycle] Request scoped resource cleaned up
INFO: 127.0.0.1 - "GET /products/999 HTTP/1.1" 404 Not Found
```

Result: cleanup still ran even though the service raised `ProductNotFoundError` and the router returned HTTP 404.

The different log order is expected. During the error path, FastAPI unwinds the dependency and executes the `finally` block before finalizing the access log entry.

### Key learning

- A `yield` dependency is request-scoped and can manage setup and cleanup around one request.
- The code before `yield` performs setup.
- The yielded value is injected into the endpoint.
- The code in `finally` performs cleanup.
- Cleanup normally runs for successful responses, handled exceptions, and request cancellation.
- Cleanup is not guaranteed if the process is abruptly killed, such as by `SIGKILL`, a machine crash, or an out-of-memory termination.
- Application-lifetime resources, such as database connection pools or shared HTTP clients, should be created during application startup and closed during application shutdown.
- Request-scoped sessions or connections should borrow from those application-level pools and be returned after the request.
- Router tests should override `get_product_service()` with a fake service so they test HTTP behavior without creating real database or external-service dependencies.
- Dependency overrides must be cleared after each test to avoid test contamination.

### Stage 2 review checklist

- [x] Stage 1 implementation remains unchanged
- [x] Resource setup occurs before `yield`
- [x] Service is yielded to the route
- [x] Cleanup occurs in `finally`
- [x] Cleanup verified for a successful request
- [x] Cleanup verified for a not-found request
- [x] Logger is used consistently for lifecycle messages
- [x] Request-scoped and application-lifetime resources are distinguished

---

## Stage 3 — Dependency Overrides and Router Testing

### Run information

- Date: 08-Nov-2026
- Python version: 3.14.4
- Platform: Windows
- Test command: `python -m pytest app/tests/test_router.py -v`
- Stage 3 implementation path: `Stage_3_dependency_overrides_and_router_testing/`

### Test design

The router tests use a `FakeProductService` instead of the real service dependency.

The fake service:

- returns a deterministic product for product ID `1`;
- raises `ProductNotFoundError` for an unknown product ID.

The test fixture:

1. installs the fake service through `app.dependency_overrides`;
2. creates a `TestClient`;
3. yields the client to the test;
4. removes the override after the test completes.

This keeps the router test independent from repositories, databases, and external services.

### Success test

Request:

```
GET /products/1
```

Assertions:

- HTTP status is `200`;
- response contains the expected product ID;
- response contains the expected product name;
- response contains the expected price.

### Failure test

Request:

```
GET /products/999
```

Assertions:

- HTTP status is `404`;
- response detail is `Product with ID 999 was not found`.

### Test result

```
collected 2 items

test_get_product_success PASSED
test_get_product_failure PASSED

2 passed in 0.44s
```

### Warnings

Two dependency warnings were reported from the installed FastAPI/Starlette/AnyIO stack:

- Starlette reported an `httpx` compatibility deprecation warning.
- AnyIO reported a deprecated `BlockingPortal` alias.

These warnings did not fail the tests and are separate from the router implementation. They can be addressed later by aligning package versions.

### Key learning

- Router tests should verify HTTP behavior, not service business logic or database queries.
- `app.dependency_overrides` allows a real dependency to be replaced with a fake dependency.
- A pytest fixture can use `yield` to separate test setup from cleanup.
- Overrides must be removed after each test to prevent test-order-dependent failures.
- A service test should use a fake repository.
- A repository test should use a real isolated test database.

### Stage 3 review checklist

- [x] Real service dependency is overridden
- [x] Fake service returns deterministic data
- [x] Successful route behavior is tested
- [x] Domain error to HTTP 404 conversion is tested
- [x] Dependency override is removed after each test
- [x] Tests pass without a real database


---

## Stage 4 — Application Lifespan Resources

### Run information

- Date: 09-Nov-2026
- Python version: 3.14.4
- Platform: Windows
- Stage 4 implementation path: `Stage_4_application_lifespan/`
- Test command: `python -m pytest app/tests/test_lifetime.py -v`

### Lifespan implementation

The application uses FastAPI's lifespan context to manage an application-scoped resource:

1. `ApplicationResources` is created during application startup.
2. The resource is stored in `app.state.shared_resource`.
3. Requests retrieve the existing resource through `get_shared_resource()`.
4. The application continues serving requests while the lifespan is active.
5. When the application shuts down, execution continues after the lifespan `yield`.
6. The resource's `close()` method marks it inactive.

This resource is created once per application process, not once per request.

### Manual verification

Before restarting the application, two requests returned the same resource ID:

```
GET /products/resource-status
{"active":true,"resource_id":"c3110fae-49fb-4003-8698-fe8ea059377f"}

GET /products/resource-status
{"active":true,"resource_id":"c3110fae-49fb-4003-8698-fe8ea059377f"}
```

After restarting the application, a new resource ID was returned:

```
GET /products/resource-status
{"active":true,"resource_id":"b6df8ce4-ff0a-4bf7-825b-d2fefb27a7a1"}
```

This proves that requests within one application lifetime reuse the same resource, while a new application startup creates a new resource.

### Startup and shutdown verification

Observed startup logs:

```
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Waiting for application startup.
INFO: Application starting up
INFO: Application startup complete.
```

Observed shutdown logs:

```
INFO: Shutting down
INFO: Waiting for application shutdown.
INFO: Application shutting down
INFO: Application shutdown complete.
```

### Test design

`test_lifetime.py` verifies:

- the resource is active while `TestClient` is running;
- two requests receive the same `resource_id`;
- the response reports `active: true`;
- the resource becomes inactive after the `TestClient` context exits.

### Test result

```
collected 2 items

test_application_resource_lifecycle PASSED
test_resource_closes_when_client_exits PASSED

2 passed in 0.45s
```

### Warnings

The test run reported two dependency warnings from the installed FastAPI/Starlette/AnyIO stack:

- Starlette reported an `httpx` compatibility deprecation warning.
- AnyIO reported a deprecated `BlockingPortal` alias.

The warnings did not fail the tests and are separate from the lifespan implementation.

### Key learning

- Application lifespan is appropriate for shared resources such as database pools, Redis clients, and HTTP clients.
- `app.state` stores application-owned objects that can be retrieved from a request through `request.app.state`.
- A request-scoped dependency can retrieve an application-scoped resource without creating a new one.
- `TestClient` used as a context manager runs application startup and shutdown events.
- Application state is local to one process. Multiple workers or pods have separate application-state objects.

### Stage 4 review checklist

- [x] Lifespan context manager creates the shared resource
- [x] Resource is stored in `app.state`
- [x] Request dependency retrieves the existing resource
- [x] Diagnostic endpoint reports resource status and ID
- [x] Same resource ID verified across requests
- [x] New resource ID verified after application restart
- [x] Shutdown cleanup verified with `TestClient`
- [x] Two lifecycle tests pass
