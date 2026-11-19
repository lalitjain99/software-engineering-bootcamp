# Topic 16 Hands-On Observations — Stage 4

## Run information

- Date: 19-Nov-2026
- Python version: 3.14.4
- Command used: `$env:PYTHONPATH = (Get-Location).Path; uv run --group dev pytest tests -v`
- Project path: `modules\01_Backend_Engineering\16_API_Versioning_And_Compatibility\Hands_On\Stage_4`
- Test result: 10 passed

The Stage 4 suite uses FastAPI's `TestClient` and dependency overrides to test both routing behavior and the expand-and-contract response change. The v2 response schema now includes an optional `discount_percentage` field.

## Expand phase verification

The fake service for the expand-phase tests contains two products:

- Product 101 has no `discount_percentage` value.
- Product 102 has `discount_percentage: 20`.

Because the v2 schema defines `discount_percentage` as optional with a default of `None`, product 101 is serialized as:

```json
{
  "id": 101,
  "name": "Monitor",
  "price": 999.99,
  "category": "Electronics",
  "stock": 3,
  "discount_percentage": null
}
```

Product 102 is serialized with the actual value:

```json
{
  "id": 102,
  "name": "Keyboard",
  "price": 99.99,
  "category": "Electronics",
  "stock": 6,
  "discount_percentage": 20
}
```

The v1 response for product 102 remains unchanged and contains only `id`, `name`, and `price`. This confirms that the additive v2 field does not alter the legacy v1 contract.

## Compatibility test observations

The compatibility test confirms that v1 and v2 still share the original fields:

- `id`
- `name`
- `price`

Version 1 continues to omit `category`, `stock`, and `discount_percentage`. Version 2 includes `category` and `stock`, and the expanded v2 schema may also include `discount_percentage`.

## Deprecation header observations

The v1 success and 404 tests pass and continue to verify:

- `Deprecation: true`
- `Sunset: Thu, 31 Dec 2026 23:59:59 GMT`
- A successor `Link` header containing the requested product ID

The v1 and v2 route behavior tests pass for existing and missing products. The v2 404 response remains a consistent error response without v1 deprecation headers.

## Questions

### 1. What does “expand” mean in an expand-and-contract migration?

Answer: Expand means adding the new optional field to the current API contract before removing or changing the old behavior. Existing clients tolerate additive JSON fields, while the provider is able to serve the new data.

### 2. Why is `discount_percentage` optional in the v2 schema?

Answer: It allows v2 to support products that do not yet provide a discount. Pydantic returns `null` for a missing optional field, which avoids changing or rejecting existing v2 product records during expansion.

### 3. Why should v1 remain unchanged during the expand phase?

Answer: V1 represents the legacy contract and may be consumed by clients that do not understand new fields. Its schema intentionally filters out `category`, `stock`, and `discount_percentage`, preserving the established v1 response shape.

### 4. Why can the new field be added to v2 but not returned directly from every product source?

Answer: The field is optional, so the API can expose a null value when source data does not contain it. Later, data migration or backend changes can populate the field for more products without breaking the v2 response model.

### 5. What should the contract do in the final “contract” phase?

Answer: After usage is monitored and v1 consumers have migrated, v1 can be sunset and removed. The final v2 contract can then continue without legacy compatibility constraints, and the optional field can become required only if all v2 product data guarantees it.

### 6. What does the fake service mean these tests do not cover?

Answer: They do not verify repository persistence or real database migration behavior. They verify response schemas, route behavior, compatibility, deprecation metadata, and serialization of the optional field.

## Stage 4 checklist

- [x] Additive v2 field implemented in the response schema
- [x] Missing optional value serialized as `null`
- [x] Product with a discount returned the discount percentage
- [x] Existing v1 contract remains unchanged
- [x] Shared original fields remain compatible
- [x] Expand-phase tests passed
- [x] Full Stage 4 suite passes
- [x] Legacy v2 test expectation updated for `discount_percentage`
- [x] Observation answers completed

> The expand phase intentionally changes v2 while preserving v1. The API contract remains compatible for clients that tolerate additive response fields; clients with strict response parsing should be validated before rollout.