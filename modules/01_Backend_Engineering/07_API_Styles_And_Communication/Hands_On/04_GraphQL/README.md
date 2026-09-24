# Micro-lab 04 — GraphQL

## Learning goal

See how a client can select the exact fields and nested relationships it wants while continuing to call one GraphQL endpoint.

This lab focuses on three ideas:

1. The server publishes a typed schema.
2. A query reads data and selects the response shape.
3. A mutation changes data and selects what should be returned.

GraphQL is not a database. The resolvers in this lab read from and write to an in-memory Python dictionary.

## REST baseline

With REST-style HTTP, we might expose:

```http
GET /products/101
GET /products/101/reviews
GET /stores/7
GET /suppliers/31
```

The server normally decides the JSON representation returned by each endpoint.

In this GraphQL lab, the client sends operations to one endpoint:

```http
POST /graphql
```

The query selects which product fields and nested objects should appear in the response.

## 1. Synchronize the root environment

The root `pyproject.toml` now includes Strawberry's FastAPI integration.

From the repository root, run:

```cmd
uv sync
```

This may update `uv.lock` in your local repository. Commit that updated lock file when you push your observations.

## 2. Start the GraphQL service

Run this as one line in Windows Command Prompt:

```cmd
uv run uvicorn product_graphql_service:app --app-dir modules/01_Backend_Engineering/07_API_Styles_And_Communication/Hands_On/04_GraphQL --host 127.0.0.1 --port 8000
```

## 3. Open GraphiQL

Open:

[http://127.0.0.1:8000/graphql](http://127.0.0.1:8000/graphql)

GraphiQL is an interactive client for exploring the schema and executing GraphQL operations.

The **Docs** or schema explorer shows the fields made available by the server. The client cannot request arbitrary Python attributes; it can request only fields defined by the GraphQL schema.

## 4. Request one field

Execute:

```graphql
query {
  product(id: 101) {
    name
  }
}
```

Expected response:

```json
{
  "data": {
    "product": {
      "name": "Keyboard"
    }
  }
}
```

Although the server's product object contains more data, GraphQL returns only `name` because that is the field the client selected.

## 5. Request a larger nested shape

Execute:

```graphql
query {
  product(id: 101) {
    id
    name
    price
    store {
      id
      name
    }
    supplier {
      name
    }
    reviews {
      rating
      comment
    }
  }
}
```

Now the response follows this larger shape. The client selected related store, supplier and review fields in one operation.

Compare the two queries:

- Both called `/graphql`.
- Both requested product `101`.
- The selected fields changed.
- The response shape changed to match the selection.

## 6. Request a list with a small representation

Execute:

```graphql
query {
  products {
    id
    name
  }
}
```

The list contains only the two selected fields for each product.

## 7. Create a product with a mutation

Execute:

```graphql
mutation {
  createProduct(name: "Mouse", price: 1200) {
    id
    name
    price
    store {
      name
    }
  }
}
```

A mutation requests a server-side change. It also contains a selection set describing the fields that should be returned after the change.

Strawberry converts the Python resolver name `create_product` to the GraphQL field name `createProduct`.

Run the product-list query again to confirm that the in-memory product was added.

## 8. Inspect the HTTP request

Open browser developer tools and inspect the GraphQL network request.

You should observe:

- The URL is `/graphql`.
- The operation is transported through HTTP.
- The request body contains a GraphQL document.
- The response has a top-level `data` property.
- Selecting different fields does not require creating different HTTP paths.

GraphQL changes the API operation and data-selection model; it does not remove HTTP from this implementation.

## Schema and resolver mental model

| Part | Meaning in this lab |
|---|---|
| Schema | The typed contract describing available queries, mutations and object fields |
| Query | A read operation such as `product` or `products` |
| Mutation | A write operation such as `createProduct` |
| Resolver | Python function that obtains or changes the data for a schema field |
| Selection set | Fields inside braces that the client wants returned |
| GraphQL endpoint | The HTTP entry point at `/graphql` |

The schema says what is allowed. Resolvers decide where the data comes from and how operations are performed.

## REST versus GraphQL in this lab

| Characteristic | REST-style example | GraphQL example |
|---|---|---|
| Entry points | Several resource URLs | One `/graphql` endpoint |
| Response fields | Server usually defines the representation | Client selects fields from the schema |
| Nested relationships | May require several requests or an aggregation endpoint | Can be selected in one operation |
| Contract | HTTP resources plus an OpenAPI-style schema | GraphQL type schema |
| Read | Usually `GET` | GraphQL query, commonly transported over HTTP |
| Write | Usually `POST/PATCH/DELETE` | GraphQL mutation, commonly transported over HTTP |

This comparison does not mean GraphQL is always better. A conventional resource API may be simpler when clients need predictable representations and normal HTTP caching.

## Intentional limitations

This lab does not yet implement:

- A database or ORM
- Authentication and field-level authorization
- Pagination
- Query-depth or query-complexity limits
- DataLoader or N+1 query prevention
- Typed business-error results
- Subscriptions
- Production schema ownership and compatibility practices

The client selecting fewer fields does not automatically guarantee less database work. Resolver and data-access design still determine what the backend fetches.

## Create your observations

Create `observations.md` in this folder and answer:

1. Which HTTP endpoint handled all GraphQL operations?
2. What changed when you requested only `name` instead of all product fields?
3. Did selecting store, supplier and reviews require additional client HTTP requests?
4. What is the difference between the schema and a resolver?
5. What is a selection set?
6. What is the difference between a GraphQL query and mutation?
7. Does GraphQL replace HTTP in this lab?
8. Why can the client not request any arbitrary Python attribute?
9. Does selecting fewer GraphQL fields guarantee less database work? Why or why not?
10. When might a REST-style API be simpler than GraphQL?

Write what you observed in the running application rather than copying definitions.
