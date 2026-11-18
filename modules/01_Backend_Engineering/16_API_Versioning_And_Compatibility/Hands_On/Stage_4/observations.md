# Topic 16 Hands-On Observations — Stage 3

## Run information

- Date: 18-Nov-2026
- Python version: 3.14.4
- Command used: `$env:PYTHONPATH = (Get-Location).Path; uv run --group dev pytest tests -v`
- Project path: `modules\01_Backend_Engineering\16_API_Versioning_And_Compatibility\Hands_On\Stage_3`
- Test result: 8 passed, 1 third-party deprecation warning

The tests use FastAPI's `TestClient` and override `get_product_service` with a fake service. This provides predictable product data while exercising the real routers, response schemas, and HTTP headers.

## Deprecation header verification

### Deprecated v1 — existing product

Request:

    GET /api/v1/products/101

Expected response (HTTP 200):

    {
      "id": 101,
      "name": "Fan",
      "price": 4999.91
    }

Expected response headers:

    Deprecation: true
    Sunset: Thu, 31 Dec 2026 23:59:59 GMT
    Link: </api/v2/products/101>; rel="successor-version"

The v1 success test verifies the status, legacy response body, and all three headers. The `Link` value identifies the v2 product endpoint corresponding to the requested product ID.

### Deprecated v1 — missing product

Request:

    GET /api/v1/products/999

Expected response (HTTP 404):

    {
      "detail": "Product with product id 999 not found"
    }

The response includes the same `Deprecation` and `Sunset` values, with the successor link pointing to `/api/v2/products/999`. This confirms that the deprecation metadata is returned for both successful and not-found v1 responses.

### Current v2 — existing product

Request:

    GET /api/v2/products/101

Expected response (HTTP 200):

    {
      "id": 101,
      "name": "Fan",
      "price": 4999.91,
      "category": "Electronics",
      "stock": 5
    }

The v2 test verifies that `Deprecation`, `Sunset`, and `Link` are absent from the response headers.

## Compatibility test observations

The compatibility test confirms that v1 and v2 still return equal values for `id`, `name`, and `price`. Version 1 omits `category` and `stock`; version 2 includes them. The added deprecation metadata does not change the v1 response body or the v2 contract.

## Questions

### 1. Why send deprecation headers on v1 responses?

Answer: They provide machine-readable migration information to clients while v1 remains available. The `Sunset` value communicates the planned end-of-service time, and the `Link` header points to the successor-version endpoint.

### 2. Why should the successor link include the requested product ID?

Answer: Each response should point to the matching v2 resource. Using the request's `product_id` makes the header useful for any product rather than hard-coding one ID.

### 3. Why test headers on both successful and missing-product responses?

Answer: Both are v1 responses, and clients may need migration information regardless of whether the requested product exists. The tests confirm the headers are preserved on the normal response and the `HTTPException` error response.

### 4. Why assert that deprecation headers are absent from v2?

Answer: V2 is the successor API in this exercise, so it should not be marked as deprecated by the v1 migration headers. Checking absence ensures the metadata is scoped to the intended version.

### 5. What does the fake service mean these tests do not cover?

Answer: They do not validate repository lookup or real stored product data. They focus on route behavior, serialized response contracts, and deprecation headers.

## Stage 3 checklist

- [x] v1 success response includes deprecation headers
- [x] v1 404 response includes deprecation headers
- [x] Successor link uses the requested product ID
- [x] v2 response does not include v1 deprecation headers
- [x] Existing v1/v2 response compatibility remains tested
- [x] Stage 3 test suite passed (8 tests)
- [x] Observation answers completed

> Note: The implementation currently sends `Deprecation: true` as configured for this exercise. For standards-based interoperability, check the current HTTP Deprecation header specification and use its date format when appropriate.