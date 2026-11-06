# Topic 15 Hands-On Lab

## Stage 1 — A small, testable Product API

Implement a small FastAPI service that demonstrates basic architecture and one explicit dependency. Do not add a database, authentication, lifespan client, or background worker yet. Those will be added in later stages.

## Goal

Build a read-only product endpoint with this flow:

    HTTP request
      -> router
      -> dependency
      -> service
      -> in-memory repository
      -> response

## Functional requirements

### Endpoint

Implement:

```
GET /products/{product_id}
```

Success response:

```
HTTP 200 OK
Content-Type: application/json

{
  "id": 101,
  "name": "Keyboard",
  "price": 2500
}
```

If the product does not exist, return:

- HTTP `404 Not Found`;
- a small JSON error response;
- do not expose repository implementation details.

### Product data

Use an in-memory collection with at least three products. Keep the data inside the repository, not inside the router.

Define separate schemas for:

- path/input expectations if needed;
- the response returned by the API.

The response schema must expose only `id`, `name`, and `price`.

## Architecture requirements

Create a small package structure similar to:

```
app/
├── main.py
├── api/
│   └── routes/
│       └── products.py
├── schemas/
│   └── products.py
├── services/
│   └── products.py
├── repositories/
│   └── products.py
└── dependencies.py
```

You may adjust the names slightly, but preserve these responsibilities:

### Router

- declare the HTTP method and path;
- receive `product_id`;
- obtain the service through `Depends`;
- return the response model;
- translate `ProductNotFoundError` into HTTP 404.

The router must not search the in-memory collection directly.

### Service

- contain the `get_product` use-case method;
- call the repository;
- raise a plain Python `ProductNotFoundError` when no product is found;
- contain no `HTTPException` and no FastAPI-specific response code.

### Repository

- own the in-memory product collection;
- provide a method to find a product by ID;
- contain no HTTP logic.

### Dependency

Create a dependency that supplies the product service to the router. The router should depend on the service, not construct the repository itself.

## Minimum acceptance checks

Verify these manually or with tests:

1. `GET /products/101` returns `200` and the expected product.
2. `GET /products/999` returns `404`.
3. The router contains no product-search logic.
4. The service contains no `HTTPException`.
5. The repository contains no FastAPI imports.
6. The response does not expose internal fields such as SKU or stock.
7. The application starts through `main.py` and includes the product router.

## Optional Stage 1 test

Add one API test using FastAPI's test client. It should verify the successful response and the not-found response.

Do not add dependency overrides yet unless you want an extra challenge. We will use overrides deliberately in Stage 2.

## Design questions to answer after coding

- Which module owns the in-memory data?
- Where is the service object constructed?
- Why should the service raise a domain exception instead of `HTTPException`?
- What would you replace first if the repository moved to SQLite?
- Which dependency would you override in a unit test?

## Scope boundary

Do not implement these yet:

- database sessions;
- authentication;
- application lifespan;
- external HTTP clients;
- generic repository frameworks;
- global exception handlers;
- complex configuration systems.

The purpose of this stage is to make one small dependency flow understandable before adding more moving parts.

## Completion evidence

Record in `observations.md`:

- your final project tree;
- sample success and not-found responses;
- one explanation of the dependency flow;
- one design decision you made;
- one thing you would change in production.