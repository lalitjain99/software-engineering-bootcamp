# Topic 16 Hands-On Observations — Stage 1

## Run information

- Date: 10-Nov-2026
- Python version: 3.14.4
- Command used: python -m uvicorn main:app --reload
- Project path: modules\01_Backend_Engineering\16_API_Versioning_And_Compatibility\Hands_On\Stage_1

## Endpoint verification

### Version 1 — existing product

Request:

    GET /api/v1/products/101


Answer:

Response:

{
  "id": 101,
  "name": "Monitor",
  "price": 999.99
}

Status code:

200

### Version 2 — existing product

Request:

    GET /api/v2/products/101


Answer:

Response:

{
  "id": 101,
  "name": "Monitor",
  "price": 999.99,
  "category": "Electronics",
  "stock": 3
}

Status code:

200


### Version 1 — missing product

Request:

    GET /api/v1/products/999


Answer:

Response:

{
  "detail": "Product with product id 999 not found"
}

Status code:

404



### Version 2 — missing product

Request:

    GET /api/v2/products/999

Answer:

Response:

{
  "detail": "Product with product id 999 not found"
}

Status code:

404


## Questions

### 1. What is the main difference between the v1 and v2 response contracts?

Answer: The response contracts differ by schema. Both versions return `id`, `name`, and `price`; v2 also returns `category` and `stock`. The v1 response schema filters out those additional fields.


### 2. Which fields are intentionally hidden from v1, and why?

Answer: Version 1 omits `category` and `stock` to preserve its original response contract. Clients using v1 continue receiving the established shape, while clients that need the additional data can use v2.


### 3. Why should v1 remain available after v2 is introduced?

Answer: Existing clients may still depend on v1's routes and response format. Keeping v1 available avoids disrupting them while they migrate to v2; it should only be retired through a communicated deprecation process.


### 4. Which parts of the implementation are shared by both API versions?

Answer: Both versions use the same `ProductService`, `ProductRepository`, and `get_product_service` dependency, so they share the product lookup and underlying data. Each version has its own router and response schema to keep its API contract independent.


### 5. Why should version-specific response formatting remain in the router/schema layer instead of the service layer?

Answer: The router and response schema define the public API contract, including which fields each version returns. The service layer should provide version-independent business logic and data; putting version-specific formatting there would couple that logic to individual API versions and could affect other consumers.


### 6. What would happen if the v1 response schema were changed to require `category`?

Answer: The v1 contract would change: `category` would become part of the v1 response instead of being omitted. If the service returned a product without `category`, FastAPI response validation could fail because the field is required. Either outcome can break existing v1 clients, so v1 should retain its current schema.


### 7. How does the missing-product behavior remain compatible across both versions?

Answer: Both routers call the shared service, which raises `ProductNotFoundError` when the product is absent. Each router converts that error into the same HTTP 404 response with the same detail message, so clients receive consistent missing-product behavior in v1 and v2.


### 8. Is adding `category` and `stock` to v2 a breaking change for existing v1 clients? Explain why.

Answer: No. The v2 additions are isolated by its separate router and response schema. The v1 schema continues to return only `id`, `name`, and `price`, so existing v1 clients are unaffected.


### 9. What would be a breaking change to the v1 contract?

Answer: Removing or renaming an existing v1 field, changing a field's type or meaning, or making a previously optional field required would be breaking changes. In general, changing the documented v1 behavior in a way that existing clients rely on can break compatibility.


### 10. What would you monitor before deprecating v1 in a production system?

Answer: Monitor v1 traffic by client and endpoint, identify active clients, and track their migration progress. Also review errors and support needs, communicate a deprecation and shutdown timeline, and confirm usage has stopped (or obtain an explicit migration plan) before removing v1.


## Stage 1 checklist

- [x] Version 1 route implemented
- [x] Version 2 route implemented
- [x] Separate response schemas created
- [x] Shared service logic reused
- [x] Existing product verified for both versions
- [x] Missing product verified for both versions
- [x] Observation answers completed