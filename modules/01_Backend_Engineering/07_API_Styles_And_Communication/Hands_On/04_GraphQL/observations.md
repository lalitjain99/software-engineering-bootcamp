Which HTTP endpoint handled all GraphQL operations?

Ans: /graphql is the endpoint, while POST is the HTTP method used for the operations executed in our lab.
All GraphQL queries and mutations were handled by the /graphql endpoint. GraphiQL sent our operations using HTTP POST. Opening the GraphiQL interface itself used GET /graphql.

What changed when you requested only name instead of all product fields?

Ans: It only provided the information asked by the client i.e name

Did selecting store, supplier and reviews require additional client HTTP requests?

Ans: No, client can ask all of the information in single query, server (GraphQL) will interpret the query and generate the response accordingly

What is the difference between the schema and a resolver?

Ans: The schema defines which types, fields, arguments, queries and mutations clients are allowed to use. A resolver is a Python function responsible for obtaining or changing the data for a particular schema field.

What is a selection set?

Ans: a selection set is the set of fields requested inside a query, mutation, or subscription. It is the core mechanism that allows clients to specify precisely what data they want back, preventing over-fetching and under-fetching.

What is the difference between a GraphQL query and mutation?

Ans: A GraphQL query reads data and should not cause business-state changes. A mutation requests a server-side change, such as creating, updating or deleting data. They are GraphQL operation types, not HTTP methods. In our lab, both were transported using HTTP POST /graphql.

Does GraphQL replace HTTP in this lab?

Ans No , GraphQL does not replace HTTP rather it uses HTTP as communication channel to send and receieve data.


Why can the client not request any arbitrary Python attribute?

Ans: GraphQL uses schema. Client can only request fields that are defined in the schema


Does selecting fewer GraphQL fields guarantee less database work? Why or why not?

Ans: Selecting fewer fields guarantees a smaller GraphQL response, but it does not automatically guarantee less database work. The resolver might still load the complete database row, perform a large join, or call another service that returns the entire object. Backend work is reduced only when resolvers and the data-access layer are designed to fetch data according to the selected fields.

When might a REST-style API be simpler than GraphQL?

Ans: A REST-style API may be simpler when the system has straightforward resource operations, predictable response formats, simple caching requirements and clients that do not need flexible nested data selection. GraphQL would add schema, resolver, security and query-complexity concerns without providing enough benefit.