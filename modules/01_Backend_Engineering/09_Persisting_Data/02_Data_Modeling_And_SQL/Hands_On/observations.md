# Observations

## 1. Duplicate SKU

### Test

A product was inserted with an SKU that already exists:

```text
MS-901
```

### Observation

SQLite rejected the operation with a unique-constraint error:

```text
UNIQUE constraint failed: products.sku
```

### Meaning

The database prevented two products from using the same SKU. This is a database-level guarantee, independent of application-level checks.

## 2. Non-existent store ID

### Test

A product was inserted with a `store_id` that does not exist in the `stores` table:

```text
store_id = 999
```

### Observation

SQLite rejected the operation with:

```text
FOREIGN KEY constraint failed
```

### Meaning

The foreign-key constraint prevented an orphan product from being created.

## 3. Deleting a store with products

### Test

A store with existing products was deleted.

### Observation

SQLite rejected the operation with:

```text
FOREIGN KEY constraint failed
```

### Meaning

`ON DELETE RESTRICT` prevented deletion of the store while dependent products still existed.

## 4. JOIN result

The query joined products with their stores and returned:

```text
Wireless Mouse (MS-901) is sold at Tech Superstore
Mechanical Keyboard (KB-202) is sold at Tech Superstore
Cotton T-Shirt (TS-505) is sold at Fashion Hub
Denim Jeans (DJ-404) is sold at Fashion Hub
```

This demonstrates that `products.store_id` connects each product to `stores.id`.

## 5. Which errors come from the database?

These failures occurred at the database layer, not in FastAPI or Pydantic:

1. Duplicate SKU → unique-constraint violation
2. Non-existent `store_id` during product insertion → foreign-key violation
3. Deleting a store with existing products → foreign-key restriction violation

The repository would later translate these low-level database errors into application-level exceptions. The router could then translate those exceptions into HTTP responses.

## 6. What changes when foreign-key enforcement is disabled?

SQLite stores the foreign-key definition in the table schema, but enforcement is connection-specific. It must be enabled for every connection:

```python
connection.execute("PRAGMA foreign_keys = ON")
```

If enforcement is disabled:

- A product with a non-existent `store_id` can be inserted.
- A store can be deleted while products still reference it.
- The resulting products become orphan records.
- The tables can still be created successfully; this is not a syntax error.

The important distinction is:

```text
Foreign-key definition exists
        ≠
Foreign-key rule is enforced for this connection
```

## 7. Key learning

Application validation improves the user-facing error, but database constraints provide the final protection. They also protect data written by other services, scripts, workers, or concurrent requests.

