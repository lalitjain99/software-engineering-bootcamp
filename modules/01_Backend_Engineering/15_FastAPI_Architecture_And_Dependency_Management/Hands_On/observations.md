# Topic 15 Hands-On Observations — Stage 1

## Run information

- Date: 06-Nov-2026
- Python version: 3.14
- Command used: uvicorn app.main:app --reload

## Project structure

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

## Endpoint verification

### Existing product

- Request: /products/101
- Status code: 200
- Response: {"id": 101, "name": "Monitor", "price": 5000}

### Missing product

- Request: /products/999
- Status code: 404
- Response: {"detail": "Product with ID 999 was not found"}

## Dependency flow

Explain how the request reaches the repository:

1. The request enters through a route in `app/api/routes/products.py`, and FastAPI resolves `get_product_service()` because the route parameter uses `Depends`.
2. `get_product_service()` constructs a `ProductRepository` and injects it into a new `ProductService`.
3. The route calls `ProductService.get_product(product_id)`, which delegates the lookup to `ProductRepository.find_product(product_id)`.
4. The repository searches its in-memory `products` dictionary and returns the matching product or `None`; the service converts `None` into `ProductNotFoundError`, which the router maps to HTTP 404.

## Architecture decisions

- Which module owns the data, and why?  
  `app/repositories/products.py` owns the product data. The repository is responsible for data storage and retrieval, keeping data access separate from HTTP and business logic.

- Where is the service constructed?  
  `get_product_service()` in `app/dependencies.py` constructs the repository and service.

- Why does the service raise a plain exception?  
  `ProductService` raises `ProductNotFoundError` so that domain/business-layer behavior remains independent of FastAPI HTTP concerns. This keeps the service reusable outside the web layer.

- Why does the router translate it to HTTP 404?  
  The router translates the domain exception into an HTTP response because only the API layer knows the external HTTP contract and which status code to return to the client.

## Review checklist

- [x] Router does not access product data directly
- [x] Service does not raise `HTTPException`
- [x] Repository has no FastAPI imports
- [x] Response schema hides internal fields
- [x] Product service is supplied through `Depends`
- [x] Application starts from `main.py`

## Production reflection

What would you change first if the in-memory repository were replaced with SQLite?

Answer: I would first implement SQLite inside `ProductRepository`, adding parameterized SQL queries and safe connection/session management without changing the route or service interfaces. I would also use FastAPI dependency lifecycles to provide and close database connections so each request uses a connection reliably and database resources are not leaked.