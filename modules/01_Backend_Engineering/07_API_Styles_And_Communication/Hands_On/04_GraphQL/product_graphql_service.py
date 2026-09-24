import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter


@strawberry.type
class Store:
    id: int
    name: str


@strawberry.type
class Supplier:
    id: int
    name: str


@strawberry.type
class Review:
    rating: int
    comment: str


@strawberry.type
class Product:
    id: int
    name: str
    price: float
    store: Store
    supplier: Supplier
    reviews: list[Review]


central_store = Store(id=7, name="Central Store")
input_devices_supplier = Supplier(id=31, name="Input Devices Ltd")

products_by_id: dict[int, Product] = {
    101: Product(
        id=101,
        name="Keyboard",
        price=2500.0,
        store=central_store,
        supplier=input_devices_supplier,
        reviews=[
            Review(rating=5, comment="Excellent"),
            Review(rating=4, comment="Good"),
        ],
    ),
    102: Product(
        id=102,
        name="Monitor",
        price=18000.0,
        store=central_store,
        supplier=input_devices_supplier,
        reviews=[
            Review(rating=5, comment="Clear display"),
        ],
    ),
}


@strawberry.type
class Query:
    @strawberry.field
    async def product(self, id: int) -> Product | None:
        print(f"Resolving product with id={id}")
        return products_by_id.get(id)

    @strawberry.field
    async def products(self) -> list[Product]:
        print("Resolving all products")
        return list(products_by_id.values())


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_product(self, name: str, price: float) -> Product:
        if price <= 0:
            raise ValueError("price must be greater than zero")

        product_id = max(products_by_id, default=100) + 1
        product = Product(
            id=product_id,
            name=name,
            price=price,
            store=central_store,
            supplier=input_devices_supplier,
            reviews=[],
        )
        products_by_id[product_id] = product

        print(f"Created product with id={product_id}")
        return product


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema, graphql_ide="graphiql")

app = FastAPI(title="Product GraphQL Service")
app.include_router(graphql_router, prefix="/graphql")
