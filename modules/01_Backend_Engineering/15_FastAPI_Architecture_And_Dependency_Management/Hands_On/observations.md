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
