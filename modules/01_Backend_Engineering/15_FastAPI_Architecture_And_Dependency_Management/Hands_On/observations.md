# Topic 15 Hands-On Observations — Stage 1

## Run information

- Date:
- Python version:
- Command used:

## Project structure

```
<!-- paste your final tree here -->
```

## Endpoint verification

### Existing product

- Request:
- Status code:
- Response:

### Missing product

- Request:
- Status code:
- Response:

## Dependency flow

Explain how the request reaches the repository:

1.
2.
3.
4.

## Architecture decisions

- Which module owns the data, and why?
- Where is the service constructed?
- Why does the service raise a plain exception?
- Why does the router translate it to HTTP 404?

## Review checklist

- [ ] Router does not access product data directly
- [ ] Service does not raise `HTTPException`
- [ ] Repository has no FastAPI imports
- [ ] Response schema hides internal fields
- [ ] Product service is supplied through `Depends`
- [ ] Application starts from `main.py`

## Production reflection

What would you change first if the in-memory repository were replaced with SQLite?

Answer: