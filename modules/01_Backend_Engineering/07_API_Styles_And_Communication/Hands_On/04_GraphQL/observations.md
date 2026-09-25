# GraphQL Micro-lab Observations

## 1. Which HTTP endpoint handled all GraphQL operations?

`/graphql` was the endpoint, while `POST` was the HTTP method used for the operations executed in our lab.

All GraphQL queries and mutations were handled by the `/graphql` endpoint. GraphiQL sent our operations using HTTP `POST`. Opening the GraphiQL interface itself used `GET /graphql`.

## 2. What changed when you requested only `name` instead of all product fields?

The response contained only the information selected by the client—in this case, the product's `name`.

The product resolver still returned the complete in-memory product object, but GraphQL shaped the response according to the client's selection set.

## 3. Did selecting store, supplier and reviews require additional client HTTP requests?

No. The client requested the product, store, supplier and reviews in one GraphQL operation.

The GraphQL server interpreted the nested selection set and generated the corresponding response through a single client HTTP request.

## 4. What is the difference between the schema and a resolver?

The schema defines which types, fields, arguments, queries and mutations clients are allowed to use.

A resolver is a Python function responsible for obtaining or changing the data for a particular schema field.

## 5. What is a selection set?

A selection set is the group of fields requested inside a query, mutation or subscription.

It allows the client to specify the response fields it needs, helping avoid unnecessary response data.

## 6. What is the difference between a GraphQL query and mutation?

A GraphQL query reads data and should not cause business-state changes.

A mutation requests a server-side change, such as creating, updating or deleting data.

They are GraphQL operation types, not HTTP methods. In our lab, both were transported using HTTP `POST /graphql`.

## 7. Does GraphQL replace HTTP in this lab?

No. GraphQL does not replace HTTP. It uses HTTP as the communication channel for sending operations and receiving results.

The HTTP request supplies the method, path, headers and body transport. GraphQL defines the operation contained inside that request body.

## 8. Why can the client not request any arbitrary Python attribute?

The client can request only fields published by the GraphQL schema.

An attribute that exists on a Python object but is not exposed through the schema is not part of the GraphQL API contract.

## 9. Does selecting fewer GraphQL fields guarantee less database work? Why or why not?

Selecting fewer fields guarantees a smaller GraphQL response, but it does not automatically guarantee less database work.

A resolver might still load the complete database row, perform a large join or call another service that returns the entire object. Backend work is reduced only when resolvers and the data-access layer are designed to fetch data according to the selected fields.

In our lab, the `product` resolver returned the complete in-memory `Product` object even when the client selected only `name`.

## 10. When might a REST-style API be simpler than GraphQL?

A REST-style API may be simpler when the system has:

- Straightforward resource operations
- Predictable response formats
- Simple HTTP caching requirements
- Clients that do not need flexible nested-data selection

In such cases, GraphQL could add schema, resolver, authorization and query-complexity concerns without providing enough benefit.
