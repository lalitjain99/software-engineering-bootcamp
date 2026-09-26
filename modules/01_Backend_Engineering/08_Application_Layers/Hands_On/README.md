# Hands-On Exercise — Refactor a Mixed FastAPI Endpoint

> **Time:** approximately 60–90 minutes  
> **Goal:** Separate HTTP handling, business logic, and in-memory storage without changing the API's observable behaviour.

## What You Are Starting With

The provided [<code>main.py</code>](main.py) works, but it mixes several responsibilities:

- Pydantic request and response schemas
- FastAPI routes and HTTP exceptions
- Input normalization
- Duplicate-SKU business rules
- In-memory storage
- ID generation
- Filtering

Your task is to refactor this working application into:

~~~text
HTTP request
    ↓
Router
    ↓
Service
    ↓
Repository
    ↓
In-memory storage
~~~

This is a refactoring exercise. Do not add a database, authentication, async code, or new API features.

## Behaviour Contract

The external API must remain unchanged:

| Operation | Method and path | Expected behaviour |
|---|---|---|
| Create product | <code>POST /products</code> | Return <code>201</code> and the created product |
| Duplicate SKU | <code>POST /products</code> | Return <code>409</code> |
| Get product | <code>GET /products/{product_id}</code> | Return the product or <code>404</code> |
| List products | <code>GET /products</code> | Return all products |
| Filter products | <code>GET /products?category=...</code> | Match a normalized category |
| Invalid request body | <code>POST /products</code> | Let FastAPI return <code>422</code> |

The supplied [<code>test_api.py</code>](test_api.py) protects this behaviour while you move code.

## 1. Synchronize the Root Environment

From the repository root:

~~~cmd
uv sync
~~~

The root project now includes the test tools required by this lab. Include the refreshed <code>uv.lock</code> in your next push.

## 2. Enter the Lab Directory

In Windows Command Prompt:

~~~cmd
cd modules\01_Backend_Engineering\08_Application_Layers\Hands_On
~~~

## 3. Run the Application Before Refactoring

Start the current application:

~~~cmd
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
~~~

Open:

~~~text
http://127.0.0.1:8000/docs
~~~

Try these operations:

~~~cmd
curl -i http://127.0.0.1:8000/products/101
~~~

~~~cmd
curl -i "http://127.0.0.1:8000/products?category=FURNITURE"
~~~

For Windows Command Prompt, create a product with:

~~~cmd
curl -i -X POST http://127.0.0.1:8000/products -H "Content-Type: application/json" -d "{\"name\":\"Mouse\",\"sku\":\"MOU-103\",\"category\":\"electronics\",\"price\":1200}"
~~~

Stop the server before running the automated tests.

## 4. Run the Baseline Tests

From the lab directory:

~~~cmd
uv run pytest -v
~~~

All six tests should pass before you change the structure.

These tests verify external behaviour. They do not require your internal code to remain in one file.

## 5. Identify the Mixed Responsibilities

Before moving code, examine each part of <code>main.py</code> and classify it:

| Code | Responsibility |
|---|---|
| FastAPI decorators and <code>HTTPException</code> | Router / HTTP |
| <code>ProductCreate</code> and <code>ProductResponse</code> | API schemas |
| Duplicate-SKU decision | Service / business |
| Name, SKU, and category normalization | Service / use-case behaviour |
| Product dictionary lookup and mutation | Repository / storage |
| Product ID generation | Repository / storage |

Write this classification in your eventual <code>observations.md</code> before comparing it with the final structure.

## 6. Create the Target Structure

Refactor toward:

~~~text
Hands_On/
├── main.py
├── test_api.py
└── app/
    ├── __init__.py
    ├── exceptions.py
    ├── schemas.py
    ├── repository.py
    ├── service.py
    └── router.py
~~~

You will create the files inside <code>app/</code>. Do not create a second FastAPI application inside that package.

## 7. Move the Schemas First

Move <code>ProductCreate</code> and <code>ProductResponse</code> into:

~~~text
app/schemas.py
~~~

Import them where needed.

Run the tests:

~~~cmd
uv run pytest -v
~~~

The behaviour should still pass before continuing.

## 8. Extract the Repository

Create <code>app/repository.py</code>.

Move the in-memory product dictionary and storage operations into a <code>ProductRepository</code> class.

The router and service should not directly read or modify the dictionary.

A reasonable repository needs operations equivalent to:

- Get one product by ID
- Find one product by SKU
- List products
- Add a product and assign its ID

You may choose the exact method names.

Repository rules:

- Do not import FastAPI.
- Do not raise <code>HTTPException</code>.
- Do not decide whether duplicate SKUs are allowed.
- Keep the initial products <code>101</code> and <code>102</code> so the tests remain valid.

Run the tests again.

## 9. Extract Application Exceptions

Create <code>app/exceptions.py</code> with application-specific exceptions for:

- Duplicate SKU
- Product not found

These exceptions should describe application outcomes without containing HTTP status codes.

## 10. Extract the Service

Create <code>app/service.py</code> with a <code>ProductService</code> class.

The service should receive a repository through its constructor.

Move these decisions into the service:

- Normalize name, SKU, and category
- Reject duplicate SKUs
- Decide what to do when a product is missing
- Coordinate repository calls
- Apply the optional category filter

Service rules:

- Do not import FastAPI.
- Do not raise <code>HTTPException</code>.
- Do not directly access the repository's internal dictionary.
- Raise the application exceptions when a business outcome requires it.

Run the tests again.

## 11. Extract the Router

Create <code>app/router.py</code> with an <code>APIRouter</code>.

Move the three route functions into it.

The router should:

- Define methods, paths, schemas, and status codes
- Receive validated HTTP inputs
- Call the service
- Translate <code>DuplicateSkuError</code> into <code>409 Conflict</code>
- Translate <code>ProductNotFoundError</code> into <code>404 Not Found</code>
- Return the service result

The router should not:

- Inspect the product dictionary
- Search for duplicate SKUs
- Generate product IDs
- Contain product business rules

For this first exercise, create one repository and one service instance in <code>app/router.py</code>. FastAPI dependency injection and application factories will be introduced later when they solve a concrete testing or lifecycle problem.

Run the tests again.

## 12. Reduce <code>main.py</code> to Application Setup

After the refactor, <code>main.py</code> should only be responsible for:

- Creating the FastAPI application
- Including the product router

It should no longer contain product schemas, product rules, or product storage.

Run the full tests one last time:

~~~cmd
uv run pytest -v
~~~

## 13. Verify the Dependency Direction

Check your imports:

~~~text
main.py
   ↓
router
   ↓
service
   ↓
repository
~~~

The repository must not import the service or router. The service must not import the router.

Schemas and application exceptions may be imported where needed, but avoid circular imports.

## 14. Manual Regression Check

Start the refactored API:

~~~cmd
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
~~~

Confirm in Swagger and curl that the paths, bodies, response shapes, and status codes have not changed.

Refactoring means improving the internal structure while preserving observable behaviour.

## Intentional Constraints

Do not add:

- A database or ORM
- Async functions
- Abstract base classes or Protocol interfaces
- Dependency-injection containers
- A Unit of Work
- Generic base repositories
- Microservices
- New endpoints or fields

Those additions would hide the responsibility boundaries that this lab is designed to practise.

## Create Your Observations

Create:

~~~text
modules/01_Backend_Engineering/08_Application_Layers/Hands_On/observations.md
~~~

Answer in your own words:

1. Which responsibilities were mixed in the original <code>main.py</code>?
2. What remained in <code>main.py</code> after the refactor?
3. Which HTTP details remained in the router?
4. Which rules moved into the service?
5. Which operations moved into the repository?
6. Why does the service raise application exceptions instead of <code>HTTPException</code>?
7. Where is a duplicate SKU converted into <code>409 Conflict</code>?
8. Why can the service be tested without starting Uvicorn?
9. What would need to change when the in-memory repository is replaced with a database repository?
10. Did any URL, request body, response body, or status code change during the refactor? Why is that important?

## Completion Check

After finishing:

1. Run <code>uv run pytest -v</code>.
2. Push the refactored code, <code>observations.md</code>, and refreshed root <code>uv.lock</code>.
3. Tell me that the changes are pushed.

I will review both the responsibility boundaries and the preserved API behaviour. After the implementation is correct, we will conduct the Topic 08 interview in chat and create <code>Interview.md</code> from the reviewed answers.
