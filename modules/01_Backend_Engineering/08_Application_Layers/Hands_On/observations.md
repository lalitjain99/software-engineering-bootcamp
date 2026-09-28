Which responsibilities were mixed in the original main.py?

Ans: The original file mixed HTTP handling, schemas, business rules, error translation, and storage.

What remained in main.py after the refactor?

Ans: main.py now creates FastAPI and includes the router.

Which HTTP details remained in the router?

Ans: Router only now only handles the URL Paths, HTTP methods Path, query, header, and body inputs ,request and response schemas and HTTP status codes.

Which rules moved into the service?

Ans: The service now handles normalization, duplicate-SKU checking, missing-product decisions, and category filtering.

Which operations moved into the repository?

Ans: Repository handle the data related operations like querying the data, adding new product etc.


Why does the service raise application exceptions instead of HTTPException?

Ans: Application exceptions keep the service independent of HTTP, allowing use from REST, GraphQL, workers, CLI code, or direct tests.


Where is a duplicate SKU converted into 409 Conflict?
Ans: The router catches DuplicateSkuError and converts it into 409 Conflict

Why can the service be tested without starting Uvicorn?

Ans: It help the developer test the behaviour of the application without hosting or executing endpoints

What would need to change when the in-memory repository is replaced with a database repository?

Ans: Replacing memory with a database requires repository query implementations, database connections/sessions, constraints, transactions, and database-error handling. The router and most service logic should remain unchanged.


Did any URL, request body, response body, or status code change during the refactor? Why is that important?

Ans: No , none of these changes as refactor is only about seperating out responsibilities for easy maintaince and scalability of the application. It does not mean to bring any behavioral change in the application