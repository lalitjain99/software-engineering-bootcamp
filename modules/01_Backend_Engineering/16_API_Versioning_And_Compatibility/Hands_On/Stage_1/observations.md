# Topic 16 Hands-On Observations — Stage 1

## Run information

- Date:
- Python version:
- Command used:
- Project path:

## Endpoint verification

### Version 1 — existing product

Request:

    GET /api/v1/products/101

Response:

    

Status code:

Answer:


### Version 2 — existing product

Request:

    GET /api/v2/products/101

Response:

    

Status code:

Answer:


### Version 1 — missing product

Request:

    GET /api/v1/products/999

Response:

    

Status code:

Answer:


### Version 2 — missing product

Request:

    GET /api/v2/products/999

Response:

    

Status code:

Answer:


## Questions

### 1. What is the main difference between the v1 and v2 response contracts?

Answer:


### 2. Which fields are intentionally hidden from v1, and why?

Answer:


### 3. Why should v1 remain available after v2 is introduced?

Answer:


### 4. Which parts of the implementation are shared by both API versions?

Answer:


### 5. Why should version-specific response formatting remain in the router/schema layer instead of the service layer?

Answer:


### 6. What would happen if the v1 response schema were changed to require `category`?

Answer:


### 7. How does the missing-product behavior remain compatible across both versions?

Answer:


### 8. Is adding `category` and `stock` to v2 a breaking change for existing v1 clients? Explain why.

Answer:


### 9. What would be a breaking change to the v1 contract?

Answer:


### 10. What would you monitor before deprecating v1 in a production system?

Answer:


## Stage 1 checklist

- [x] Version 1 route implemented
- [x] Version 2 route implemented
- [x] Separate response schemas created
- [x] Shared service logic reused
- [x] Existing product verified for both versions
- [x] Missing product verified for both versions
- [ ] Observation answers completed