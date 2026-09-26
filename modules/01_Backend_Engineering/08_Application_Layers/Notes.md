# Topic 08 — When One Endpoint Becomes Too Large

> **Single learning goal:** Separate HTTP handling, business decisions, and data storage so that each part of the application has one clear responsibility.

## Start With the Problem

A small FastAPI endpoint often begins like this:

~~~python
products: list[dict] = []


@app.post("/products", status_code=201)
def create_product(product: ProductCreate):
    for existing_product in products:
        if existing_product["sku"] == product.sku:
            raise HTTPException(
                status_code=409,
                detail="SKU already exists",
            )

    new_product = {
        "id": len(products) + 1,
        "name": product.name,
        "sku": product.sku,
        "price": product.price,
    }

    products.append(new_product)
    return new_product
~~~

This is not automatically bad code. For a small learning example, keeping everything together makes the complete request easy to see.

The endpoint currently does three different jobs:

1. It handles HTTP.
2. It applies a business rule.
3. It stores and retrieves data.

As the application grows, each job becomes more complicated.

## How the Endpoint Grows

Imagine that product creation now requires:

- Validating the HTTP request body
- Rejecting a duplicate SKU
- Applying a category-specific pricing rule
- Checking whether the supplier is active
- Saving the product in a database
- Recording an audit event
- Notifying another component
- Returning the correct HTTP status and response shape

If all of this remains inside one route function, the function becomes difficult to read, test, and change:

~~~python
@app.post("/products", status_code=201)
def create_product(product: ProductCreate):
    # HTTP input handling
    # duplicate-SKU query
    # supplier query
    # pricing rules
    # database insert
    # transaction handling
    # audit record
    # notification
    # HTTP error mapping
    # response construction
    ...
~~~

The problem is not simply that the function has many lines. The deeper problem is that it has **multiple reasons to change**.

For example:

- Changing the URL or status code changes HTTP handling.
- Changing a pricing rule changes business logic.
- Replacing in-memory storage with PostgreSQL changes data access.

When unrelated changes affect the same function, development becomes risky.

---

## First Principle: Separate Responsibilities

For this topic, we will divide the application into three parts:

| Part | Main question |
|---|---|
| Router | How does this operation appear over HTTP? |
| Service | What business action should the application perform? |
| Repository | How is the required data stored and retrieved? |

The request flows in one direction:

~~~text
HTTP request
    ↓
Router
    ↓
Service
    ↓
Repository
    ↓
Storage
~~~

The result returns in the opposite direction:

~~~text
Storage result
    ↓
Repository
    ↓
Service
    ↓
Router
    ↓
HTTP response
~~~

All three parts can still run inside the same FastAPI process. Separating responsibilities does **not** mean creating three microservices.

---

## 1. Router — The HTTP Boundary

The router is where the outside HTTP world enters the application.

It should understand HTTP concepts such as:

- URL paths
- HTTP methods
- Path, query, header, and body inputs
- Request and response schemas
- HTTP status codes
- Authentication dependencies
- Converting application outcomes into HTTP responses

For example:

~~~python
@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=201,
)
def create_product(
    product: ProductCreate,
) -> ProductResponse:
    try:
        return product_service.create_product(
            name=product.name,
            sku=product.sku,
            price=product.price,
        )
    except DuplicateSkuError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error
~~~

The router does not decide how duplicate SKUs are detected. It asks the service to perform the use case.

The router does decide that a duplicate-SKU business failure should become an HTTP <code>409 Conflict</code> response.

A useful rule is:

> The router translates between HTTP and the application.

### What should normally stay out of the router?

Avoid placing these directly in a route function once the application has grown:

- Database queries
- Pricing calculations
- Multi-step business workflows
- Decisions about whether an operation is allowed
- Calls to several repositories
- Retry or transaction rules

The goal is not to make the router empty. Its meaningful responsibility is the HTTP contract.

---

## 2. Service — The Business Use Case

A service represents an application action such as:

- Create a product
- Reserve stock
- Cancel an order
- Approve a refund

In this topic, “service” means a Python class or function inside the application. It does not mean a separately deployed microservice.

Our product service might look like this:

~~~python
class DuplicateSkuError(Exception):
    pass


class ProductService:
    def __init__(self, product_repository):
        self.product_repository = product_repository

    def create_product(
        self,
        name: str,
        sku: str,
        price: float,
    ) -> dict:
        existing_product = self.product_repository.get_by_sku(sku)

        if existing_product is not None:
            raise DuplicateSkuError(
                f"Product with SKU {sku} already exists"
            )

        return self.product_repository.add(
            name=name,
            sku=sku,
            price=price,
        )
~~~

The service contains the rule:

> Two products cannot be created with the same SKU.

The service does not raise <code>HTTPException</code>. A duplicate SKU is a business problem, not inherently an HTTP problem.

The same service may later be called from:

- A REST endpoint
- A GraphQL mutation
- A background worker
- A command-line tool
- A test

If the service raised HTTP-specific exceptions, all those callers would become coupled to HTTP.

A useful rule is:

> The service decides what the application should do, without deciding how that result is represented over HTTP.

### Is every helper function a service?

No. A service should usually represent a meaningful use case or business operation.

A class containing only pass-through methods adds little value:

~~~python
class ProductService:
    def get_product(self, product_id):
        return repository.get_product(product_id)
~~~

This may become useful when rules or orchestration appear, but adding layers mechanically can create unnecessary code.

---

## 3. Repository — The Storage Boundary

In this topic, “repository” does not mean a GitHub repository.

A repository is application code responsible for storing and retrieving data.

For the first example, storage remains in memory:

~~~python
class ProductRepository:
    def __init__(self):
        self.products: list[dict] = []
        self.next_id = 1

    def get_by_sku(self, sku: str) -> dict | None:
        for product in self.products:
            if product["sku"] == sku:
                return product

        return None

    def add(
        self,
        name: str,
        sku: str,
        price: float,
    ) -> dict:
        product = {
            "id": self.next_id,
            "name": name,
            "sku": sku,
            "price": price,
        }

        self.next_id += 1
        self.products.append(product)
        return product
~~~

The service does not need to know whether the repository uses:

- An in-memory list
- PostgreSQL
- Another service
- A test double

For now, the repository answers storage-oriented questions:

- Find a product by SKU
- Add a product
- Find a product by ID
- List stored products

A useful rule is:

> The repository knows how to access data, but it should not decide business policy.

For example, the repository can report that a product with the SKU already exists. The service decides that the new product must therefore be rejected.

---

## The Same Use Case, Separated

### Request and response schemas

~~~python
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    price: float = Field(gt=0)


class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    price: float
~~~

These schemas define the HTTP request and response shapes.

### Repository

~~~python
class ProductRepository:
    def __init__(self):
        self.products: list[dict] = []
        self.next_id = 1

    def get_by_sku(self, sku: str) -> dict | None:
        return next(
            (
                product
                for product in self.products
                if product["sku"] == sku
            ),
            None,
        )

    def add(
        self,
        name: str,
        sku: str,
        price: float,
    ) -> dict:
        product = {
            "id": self.next_id,
            "name": name,
            "sku": sku,
            "price": price,
        }

        self.next_id += 1
        self.products.append(product)
        return product
~~~

### Service

~~~python
class DuplicateSkuError(Exception):
    pass


class ProductService:
    def __init__(
        self,
        product_repository: ProductRepository,
    ):
        self.product_repository = product_repository

    def create_product(
        self,
        name: str,
        sku: str,
        price: float,
    ) -> dict:
        if self.product_repository.get_by_sku(sku):
            raise DuplicateSkuError(
                f"Product with SKU {sku} already exists"
            )

        return self.product_repository.add(
            name=name,
            sku=sku,
            price=price,
        )
~~~

### Router

~~~python
from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/products", tags=["products"])

product_repository = ProductRepository()
product_service = ProductService(product_repository)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=201,
)
def create_product(
    product: ProductCreate,
) -> ProductResponse:
    try:
        created_product = product_service.create_product(
            name=product.name,
            sku=product.sku,
            price=product.price,
        )
    except DuplicateSkuError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    return ProductResponse(**created_product)
~~~

### Application entry point

~~~python
from fastapi import FastAPI

from app.routers.products import router as product_router


app = FastAPI()
app.include_router(product_router)
~~~

The complete journey is now:

1. FastAPI matches <code>POST /products</code>.
2. Pydantic validates the request body.
3. The router passes the required values to <code>ProductService</code>.
4. The service checks the duplicate-SKU business rule.
5. The service asks <code>ProductRepository</code> to store the product.
6. The repository returns the stored product.
7. The service returns the use-case result.
8. The router converts it into the response schema.
9. FastAPI sends <code>201 Created</code> with JSON.

---

## Where Should Validation Live?

“Validation” is not one single activity. Place it according to what is being checked.

| Validation type | Example | Natural location |
|---|---|---|
| Request structure | <code>price</code> must be a number | Pydantic schema / HTTP boundary |
| Basic field constraint | <code>price</code> must be greater than zero | Pydantic schema when it is part of the API contract |
| Business rule | SKU must be unique | Service |
| Authorization rule | Only a manager may approve a refund | Service or authorization policy invoked by it |
| Storage constraint | Database unique index on SKU | Database, handled through repository/data-access code |

Some important rules should be enforced in more than one place for different reasons.

For example:

- The service checks duplicate SKU to return a meaningful business outcome.
- The database later needs a unique constraint to prevent a race condition between simultaneous requests.

The application check improves the response. The database constraint protects the data.

---

## Error Flow Between the Parts

Errors should also cross boundaries deliberately.

For a duplicate SKU:

~~~text
Repository finds existing SKU
          ↓
Service raises DuplicateSkuError
          ↓
Router maps it to HTTP 409
          ↓
Client receives Conflict response
~~~

Why not raise <code>HTTPException</code> from the repository?

Because the repository's job is data access. It should not decide whether a storage outcome becomes HTTP <code>404</code>, <code>409</code>, a skipped background job, or something else.

This separation becomes valuable when the same business action has multiple entry points.

---

## Suggested File Structure

A small, understandable first structure is:

~~~text
app/
├── main.py
├── schemas.py
├── exceptions.py
├── repositories/
│   └── products.py
├── services/
│   └── products.py
└── routers/
    └── products.py
~~~

Responsibilities:

| File | Responsibility |
|---|---|
| <code>main.py</code> | Create FastAPI and include routers |
| <code>schemas.py</code> | HTTP request and response models |
| <code>exceptions.py</code> | Application-specific exceptions |
| <code>routers/products.py</code> | Product HTTP contract |
| <code>services/products.py</code> | Product use cases and business rules |
| <code>repositories/products.py</code> | Product storage access |

This is a learning structure, not a universal production standard.

A large application may organize files by feature instead:

~~~text
app/
└── products/
    ├── router.py
    ├── schemas.py
    ├── service.py
    ├── repository.py
    └── exceptions.py
~~~

Organization by technical layer and organization by feature can both work. Consistent ownership and dependency direction matter more than the folder names.

---

## Why This Structure Helps Testing

With an all-in-one endpoint, testing a duplicate SKU may require making an HTTP request and preparing the complete application.

With a separated service, the business rule can be tested directly:

~~~python
def test_duplicate_sku_is_rejected():
    repository = ProductRepository()
    service = ProductService(repository)

    service.create_product(
        name="Keyboard",
        sku="KEY-101",
        price=2500,
    )

    with pytest.raises(DuplicateSkuError):
        service.create_product(
            name="Another Keyboard",
            sku="KEY-101",
            price=3000,
        )
~~~

Different tests can focus on different responsibilities:

| Test | Main concern |
|---|---|
| Router/API test | Path, status code, validation, and response body |
| Service test | Business decisions and workflows |
| Repository test | Storage queries and persistence behaviour |

This does not mean every method needs a mocked unit test. Use the separation to make important behaviour easier to test.

---

## What Has Actually Improved?

### Before

~~~text
Route function
├── understands HTTP
├── contains business decisions
└── manipulates storage
~~~

### After

~~~text
Router
└── translates HTTP

Service
└── performs the business use case

Repository
└── accesses storage
~~~

Benefits include:

- A database change does not require rewriting the HTTP contract.
- A status-code change does not require changing business rules.
- Business logic can be tested without starting the API.
- The same use case can support another entry point.
- Code review becomes easier because responsibilities are clearer.
- Ownership boundaries become more visible as the team grows.

---

## What This Separation Does Not Guarantee

Creating three folders does not automatically produce good architecture.

Problems can still occur if:

- The router continues to contain all business logic.
- The service merely forwards every call without adding meaning.
- The repository contains pricing or authorization rules.
- Every tiny operation gets several unnecessary classes.
- Modules import each other in both directions.
- Exceptions leak from the database directly to API clients.
- The code is split into files but responsibilities remain mixed.

The goal is separation of decisions, not a particular number of files.

---

## Technical Lead Decision Guide

Before introducing or changing layers, ask:

1. What responsibility is making this endpoint difficult to change?
2. Which business rules need testing without HTTP?
3. Is data access repeated across use cases?
4. Will another entry point reuse the same operation?
5. Which failures are business outcomes, and which are infrastructure failures?
6. Can the team understand and consistently follow the proposed structure?
7. Does the added abstraction solve a present problem or only a hypothetical future problem?

A useful starting principle is:

> Keep simple code together until it contains responsibilities that change for different reasons. Then separate those responsibilities at clear boundaries.

---

## Common Mistakes

### “Every endpoint needs three classes”

Small read-only or trivial endpoints may not require every layer. Introduce structure where it clarifies real responsibilities.

### “The service is another deployed service”

In this topic, the service is ordinary Python application code. It runs in the same process as FastAPI.

### “Repository means GitHub repository”

Here, repository means a data-access abstraction.

### “The router should contain no logic”

The router still handles HTTP-specific decisions: inputs, outputs, status codes, dependencies, and error translation.

### “Pydantic validation replaces business validation”

Pydantic can validate structure and field constraints. It does not know whether a SKU already exists or whether a user may approve a refund.

### “The database can be added later without affecting design”

A repository can reduce the spread of database code, but transactions, concurrency, constraints, and failure handling still require deliberate design.

### “More layers always mean better architecture”

Every layer has a learning and maintenance cost. Use the smallest structure that makes responsibilities clear.

---

## Check Your Understanding

1. What three responsibilities were mixed inside the original endpoint?
2. Which part should know about HTTP status codes?
3. Which part should decide whether duplicate SKUs are allowed?
4. Which part should know how products are stored?
5. Why should a service normally avoid raising <code>HTTPException</code>?
6. Is a service layer the same as a separately deployed microservice?
7. Where should request-shape validation and business-rule validation live?
8. Why might both the service and database enforce SKU uniqueness?
9. How does separation make testing easier?
10. When would adding a repository or service layer be unnecessary?

---

## Intentional Stop Point

This first lesson does not yet introduce:

- A real database or ORM
- Database sessions and transactions
- Abstract repository interfaces
- Dependency inversion
- Domain entities
- Unit of Work
- Event publishing
- Async repositories
- Separate microservices

Those ideas should be introduced only when the application develops the problem that requires them.

## Next Step

Read this note with one question in mind:

> Which responsibility is making the endpoint change?

After that, the hands-on exercise will begin with one deliberately mixed FastAPI endpoint. We will first observe its problems and then refactor it into router, service, and repository code without changing its external API behaviour.
