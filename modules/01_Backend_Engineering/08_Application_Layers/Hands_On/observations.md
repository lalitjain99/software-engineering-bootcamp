# Topic 08 Hands-On Observations

## 1. Which responsibilities were mixed in the original <code>main.py</code>?

The original file mixed HTTP handling, request and response schemas, business rules, error translation, and data storage.

## 2. What remained in <code>main.py</code> after the refactor?

<code>main.py</code> now creates the FastAPI application and includes the product router.

## 3. Which HTTP details remained in the router?

The router handles URL paths, HTTP methods, path and query inputs, request and response schemas, HTTP status codes, and the translation of application exceptions into HTTP responses.

It no longer accesses product storage or implements product business rules directly.

## 4. Which rules moved into the service?

The service handles name, SKU, and category normalization; duplicate-SKU checking; missing-product decisions; and optional category filtering.

It performs these operations without deciding which HTTP status code should represent the outcome.

## 5. Which operations moved into the repository?

The repository handles data-related operations such as retrieving products, finding a product by SKU, listing products, assigning the next product ID, and adding a new product.

## 6. Why does the service raise application exceptions instead of <code>HTTPException</code>?

Application exceptions keep the service independent of HTTP. This allows the same service logic to be called from REST, GraphQL, background workers, command-line code, or direct tests.

The HTTP router decides how an application outcome should be represented to an HTTP client.

## 7. Where is a duplicate SKU converted into <code>409 Conflict</code>?

The service raises <code>DuplicateSkuError</code>. The router catches that application exception and translates it into an HTTP <code>409 Conflict</code> response.

## 8. Why can the service be tested without starting Uvicorn?

The service is an ordinary Python class. A test can construct it with a repository and call its methods directly.

It does not require an HTTP request, FastAPI routing, the ASGI protocol, or a running Uvicorn server to execute its business rules.

## 9. What would change when the in-memory repository is replaced with a database repository?

The repository would need database query implementations, database connections or sessions, database constraints, transaction handling, and translation of database failures.

If the repository continues to provide the operations required by the service, the router and most service logic should remain unchanged.

## 10. Did any external API behaviour change during the refactor?

No URL, request body, response body, or status code changed.

This is important because refactoring improves the internal code structure without breaking existing clients. The regression tests protect that external contract while the implementation is reorganized.
