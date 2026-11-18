# Topic 16 Hands-On Observations — Stage 2

## Run information

- Date: 18-Nov-2026
- Python version: 3.14.4
- Command used: `$env:PYTHONPATH = (Get-Location).Path; python -m pytest tests -v`
- Project path: `modules\01_Backend_Engineering\16_API_Versioning_And_Compatibility\Hands_On\Stage_2`
- Test result: 5 passed

The tests use FastAPI's `TestClient` and replace `get_product_service` with a fake service. This keeps the API contract tests independent of the in-memory repository while exercising the real routers and response schemas.

## Compatibility test observations

### Existing product — version 1

Request:

    GET /api/v1/products/101

Test service data:

    {
      "id": 101,
      "name": "Fan",
      "price": 4999.91
      "category": "Electronics",
      "stock": 5
    }

Expected response (HTTP 200):

    {
      "id": 101,
      "name": "Fan",
      "price": 4999.91
    }

The v1 response schema omits `category` and `stock`, even though the shared service returns them.

### Existing product — version 2

Request:

    GET /api/v2/products/101

Expected response (HTTP 200):

    {
      "id": 101,
      "name": "Shirt",
      "price": 499.96,
      "category": "Electronics",
      "stock": 5
    }

The v2 response includes the additional fields. The tests also compare `id`, `name`, and `price` across both responses to verify that those shared fields retain the same values.

### Missing product — both versions

Requests:

    GET /api/v1/products/999
    GET /api/v2/products/999

Expected response for each (HTTP 404):

    {
      "detail": "Product with product id 999 not found"
    }

Both version-specific tests confirm the status and detail message.

## Questions

### 1. What does the compatibility test verify beyond testing each router separately?

Answer: It requests the same product through both versions, verifies that `id`, `name`, and `price` are equal, and confirms that v1 excludes `category` and `stock` while v2 includes them. This directly checks that the new response contract has not changed the legacy v1 shape.

### 2. Why does the test override `get_product_service` with a fake service?

Answer: The fake service supplies predictable product data and a predictable missing-product error. The test therefore focuses on HTTP routing, response serialization, and version-specific schemas without depending on repository state.

### 3. What behavior is shared between the versions?

Answer: Both routes use the `get_product_service` dependency and the same service behavior. They return matching values for the shared fields and the same 404 detail for a missing product.

### 4. What is the version-specific behavior?

Answer: Each route uses its own response schema. The v1 schema returns only `id`, `name`, and `price`; v2 also returns `category` and `stock`.

### 5. What does this test suite not verify?

Answer: Because the service is replaced with a fake, these tests do not verify repository lookup or the production product data. Those concerns should be covered separately; these tests specifically protect the API contracts and their compatibility.

## Stage 2 checklist

- [x] v1 success and missing-product behavior tested
- [x] v2 success and missing-product behavior tested
- [x] Shared response fields compared across versions
- [x] v1 omission of v2-only fields verified
- [x] Stage 2 test suite passed (5 tests)
- [x] Observation answers completed