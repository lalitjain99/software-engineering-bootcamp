Which HTTP endpoint handled all GraphQL operations?

Ans: post /graphql handles all the graphQL operations

What changed when you requested only name instead of all product fields?

Ans: It only provided the information asked by the client i.e name

Did selecting store, supplier and reviews require additional client HTTP requests?

Ans: No, client can ask all of the information in single query, server (GraphQL) will interpret the query and generate the response accordingly

What is the difference between the schema and a resolver?

Ans: In GraphQL, the schema and the resolver work hand-in-hand, but they serve completely different purposes. Think of the schema as the blueprint (what data is possible to request) and the resolvers as the construction crew (how to actually fetch that data).
The schema defines the structure and contract of your API using GraphQL's Schema Definition Language (SDL).A resolver is a collection of functions that actually fulfill the data requested by the schema

What is a selection set?

Ans: a selection set is the set of fields requested inside a query, mutation, or subscription. It is the core mechanism that allows clients to specify precisely what data they want back, preventing over-fetching and under-fetching.

What is the difference between a GraphQL query and mutation?

Ans: A query is used to fetch data from the server. It acts as a read-only operation and should never change the server's state or database. Its REST Equivalent is An HTTP GET request. A mutation is used to modify data on the server. This includes creating new records, updating existing ones, or deleting data. Its REST Equivalent: An HTTP POST, PUT, PATCH, or DELETE request.

Does GraphQL replace HTTP in this lab?

Ans No , GraphQL does not replace HTTP rather it uses HTTP as communication channel to send and receieve data.


Why can the client not request any arbitrary Python attribute?

Ans: GraphQL uses schema. Client can only request fields that are defined in the schema


Does selecting fewer GraphQL fields guarantee less database work? Why or why not?

Ans: I don't have much clearity on this

When might a REST-style API be simpler than GraphQL?

Ans: When you have fixed request and response format