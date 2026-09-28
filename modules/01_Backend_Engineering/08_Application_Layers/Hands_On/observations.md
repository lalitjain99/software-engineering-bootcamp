Which responsibilities were mixed in the original main.py?

Ans: Orginal main.py was handling all 4 major responsibilities i.e. endpoints creation, model schema, business logic , error handling and data storage

What remained in main.py after the refactor?

Ans: now main.py is only handling the router to be included 

Which HTTP details remained in the router?

Ans: Router only now only handles the URL Paths, HTTP methods Path, query, header, and body inputs ,request and response schemas and HTTP status codes.

Which rules moved into the service?

Ans: Service layer handles the main business logic like how to create a product, list all product without dealing with the HTTP response of the outcome

Which operations moved into the repository?

Ans: Repository handle the data related operations like querying the data, adding new product etc.


Why does the service raise application exceptions instead of HTTPException?

Ans: service is only responsible for business logic hence it should only create about what error application is generating and how to handle it.


Where is a duplicate SKU converted into 409 Conflict?
Ans: It should be converted at route level.

Why can the service be tested without starting Uvicorn?

Ans: It help the developer test the behaviour of the application without hosting or executing endpoints

What would need to change when the in-memory repository is replaced with a database repository?

Ans: We just need to add a database connection function inside the repository file


Did any URL, request body, response body, or status code change during the refactor? Why is that important?

Ans: No , none of these changes as refactor is only about seperating out responsibilities for easy maintaince and scalability of the application. It does not mean to bring any behavioral change in the application