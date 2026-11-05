# FastAPI Architecture and Dependency Management

## Why this topic matters

A small FastAPI file can be easy to understand. As the service grows, the same file can start containing routes, validation, business rules, database access, authentication, configuration, and external clients.

The goal is not to create folders for their own sake. The goal is to make responsibilities, dependencies, lifetimes, and tests clear.

## 1. The request flow

A typical FastAPI request flows through these boundaries:

    client
      -> middleware
      -> router
      -> dependency resolution
      -> endpoint handler
      -> service
      -> repository or external client
      -> response

Each layer should have a clear responsibility:

- **Router:** HTTP path, method, parameter extraction, status code, and response contract.
- **Dependency:** supplies a required capability such as a database session, authenticated user, settings object, or client.
- **Service:** business use case and business rules.
- **Repository/client:** database or external-system communication.
- **Schema:** request and response data shape and validation.

## 2. A practical project structure

One reasonable structure is:

    app/
    ├── main.py
    ├── api/
    │   ├── router.py
    │   └── routes/
    ├── schemas/
    ├── services/
    ├── repositories/
    ├── dependencies/
    ├── clients/
    ├── config/
    └── db/

This is a starting point, not a law. A small service may use fewer modules. Split code when a responsibility, ownership boundary, or test boundary becomes meaningful.

## 3. What dependency injection means

Dependency injection means that a function receives the capability it needs instead of constructing that capability internally.

Without injection:

    def create_order(data):
        session = create_database_session()
        repository = OrderRepository(session)
        ...

With injection:

    def create_order(data, repository):
        ...

The caller or framework supplies the repository. This makes the function easier to test and keeps construction separate from business logic.

## 4. FastAPI's `Depends`

FastAPI uses `Depends` to declare dependencies:

    from fastapi import Depends, FastAPI

    app = FastAPI()

    def get_settings():
        return Settings()

    @app.get('/health')
    def health(settings: Settings = Depends(get_settings)):
        return {'environment': settings.environment}

The endpoint declares what it needs. FastAPI resolves the dependency before calling the endpoint and passes the result as an argument.

`Depends` is not a service locator that should hide all application behavior. Use it mainly for cross-cutting capabilities and request-bound resources.

## 5. Dependency graphs

Dependencies can depend on other dependencies:

    endpoint
      -> current_user
          -> bearer_token
      -> database_session
          -> connection_pool
      -> settings

FastAPI resolves the graph before the endpoint runs. If a dependency fails, the endpoint body is not executed.

Examples:

- missing or invalid authentication can produce `401`;
- a missing permission can produce `403`;
- invalid request data can produce `422`;
- a database-session dependency can fail before business logic begins.

Keep dependency graphs understandable. Deep hidden graphs make failures and tests difficult to reason about.

## 6. Common dependency types

### Configuration

Settings should be created from environment variables or a configuration source, validated once, and shared safely. Do not read environment variables repeatedly throughout business logic.

### Database session

A request-scoped database dependency commonly:

1. obtains a session from the pool;
2. yields it to the request;
3. commits or rolls back according to the transaction policy;
4. closes or returns it to the pool.

Do not create a new pool inside every request.

### Authentication and authorization

Authentication identifies the caller. Authorization decides whether the caller may perform an action.

A dependency can decode or validate a token and return a `CurrentUser`. A separate authorization dependency can check a role or permission.

Do not put all business authorization rules into one generic dependency. Resource-specific rules usually belong in the service layer.

### External clients

HTTP, Redis, or cloud-storage clients should usually be created at application lifespan and reused through a dependency or application state. Constructing a new client per request prevents connection reuse and can leak resources.

## 7. Resource lifetime and scopes

Every dependency has a lifetime:

| Lifetime | Example |
|---|---|
| Application | HTTP client, connection pool, settings |
| Request | database session, current user, correlation context |
| Function call | temporary calculation or small helper |

Match the lifetime to the resource. A pool should live with the application. A transaction/session should normally be bounded to a request or explicit use case. A request-specific user must not be stored in global mutable state.

## 8. `yield` dependencies and cleanup

A dependency can use `yield` to define setup and cleanup:

    def get_session():
        session = session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

The code before `yield` prepares the resource. The endpoint uses the yielded value. The `finally` block runs during cleanup even when the request fails, subject to process termination.

Cleanup is essential for sessions, locks, temporary files, and clients.

## 9. Routers and application composition

`main.py` should normally compose the application rather than contain every endpoint:

    app = FastAPI(lifespan=lifespan)
    app.include_router(order_router, prefix='/orders')
    app.include_router(health_router)

The composition root is the place where concrete implementations are connected:

- production database repository;
- real payment client;
- settings;
- middleware;
- routers.

Services should depend on interfaces or clear contracts rather than importing application globals.

## 10. Testing with dependency overrides

FastAPI allows tests to replace dependencies:

    app.dependency_overrides[get_session] = get_test_session

This lets an API test use a test database or fake repository without changing production code.

Good override targets include:

- database sessions;
- authentication/current-user dependencies;
- external HTTP clients;
- clocks and ID generators;
- feature-flag providers.

Always clear overrides after the test or fixture so one test does not leak configuration into another.

## 11. Avoiding common architecture problems

### Hidden global state

Module-level mutable clients, caches, locks, or current-user values can behave incorrectly across workers and tests. If state must be shared, define its ownership and lifecycle explicitly.

### Circular imports

Routes importing services that import routes usually indicate unclear ownership. Keep dependencies flowing in one direction, for example:

    router -> service -> repository/client

### Business logic in dependencies

Dependencies are useful for authentication and resource setup. Do not hide the entire order workflow inside a dependency merely because it can be called with `Depends`.

### Constructing heavy resources per request

Creating pools, HTTP clients, or SDK clients in every endpoint wastes connection setup time and can exhaust resources.

### Over-abstraction

Do not create interfaces, factories, and packages without a real substitution, ownership, or testing benefit. Architecture should reduce cognitive load, not increase it.

## 12. Configuration and environment separation

Configuration should be explicit and environment-specific:

- local development settings;
- test settings;
- staging settings;
- production settings.

Secrets should come from a secret manager or protected environment configuration, not source control or logs.

Validate required configuration at startup when possible. A service that starts without a required payment URL or database URL should fail clearly rather than discover the problem during a user request.

## 13. Error handling boundaries

Keep error translation near the boundary:

- repository/client raises technical or provider errors;
- service raises domain/application errors;
- router or global exception handlers translate them into HTTP responses.

Do not make the service layer depend on `HTTPException` if the same use case may later be called by a worker, GraphQL resolver, or command-line process.

## Common mistakes

- Treating `Depends` as a replacement for all application architecture;
- creating a database pool or HTTP client inside every request;
- storing request-specific data in module globals;
- putting business workflows in authentication dependencies;
- overriding dependencies in tests and not clearing the override;
- making dependencies too deep or circular;
- hiding transaction commit and rollback policy;
- using the same session across concurrent tasks;
- logging secrets from settings or headers;
- introducing abstractions before a real substitution is needed.

## Mental model

Design FastAPI applications in this order:

1. Define the HTTP contract in the router and schemas.
2. Identify capabilities the endpoint needs.
3. Supply those capabilities through explicit dependencies.
4. Keep business decisions in the service layer.
5. Keep storage and provider details behind repositories/clients.
6. Assign each resource a clear lifetime.
7. Make dependencies replaceable in tests.
8. Compose the real application in one clear place.