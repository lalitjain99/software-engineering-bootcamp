# Topic 16 Hands-On — API Versioning and Compatibility

## Goal

Build a small versioned Product API and demonstrate that a new contract can be introduced without breaking existing clients.

Do not modify the Topic 15 implementation. Create this exercise in a separate directory.

## Stage 1 — Two API versions

Create a new layered Product API using the existing in-memory product data.

Expose:

GET /api/v1/products/{product_id}
GET /api/v2/products/{product_id}

### Version 1 contract

Return the legacy response shape:

    {
      "id": 101,
      "name": "Monitor",
      "price": 5000
    }

Do not expose internal fields such as stock or category.

### Version 2 contract

Return the new response shape:

    {
      "id": 101,
      "name": "Monitor",
      "price": 5000,
      "category": "electronics",
      "stock": 5
    }

Version 2 may add fields, but it must preserve the meaning of the existing fields.

### Required structure

- Use separate routers or clearly separated route modules for v1 and v2.
- Create separate response schemas for v1 and v2.
- Keep product retrieval logic in the shared service.
- Keep product data access in the repository.
- Do not put version-specific HTTP response formatting in the service.

### Required behavior

- Existing product 101 returns HTTP 200 in both versions.
- Missing product 999 returns HTTP 404 in both versions.
- The error response remains consistent.
- Both versions reuse the same underlying service behavior.

### Verification

Run and record the results for:

GET /api/v1/products/101
GET /api/v2/products/101
GET /api/v1/products/999
GET /api/v2/products/999

Record the status code, response body, fields that differ, and whether the v1 response remains unchanged after adding v2.

## Constraints

- Do not change the Topic 15 implementation.
- Do not duplicate business logic between v1 and v2.
- Do not make the service return HTTP responses.
- Do not add deprecation headers yet.
- Do not write tests yet; we will add compatibility tests after reviewing the implementation.

## Stage 1 checklist

- [ ] Separate Topic 16 hands-on directory created
- [ ] Version 1 route implemented
- [ ] Version 2 route implemented
- [ ] Separate response schemas created
- [ ] Shared service logic reused
- [ ] Existing and missing-product behavior verified for both versions
- [ ] v1 response contract remains stable
- [ ] Observations recorded

Later stages will add compatibility tests, deprecation headers, expand-and-contract schema changes, and monitoring by API version.