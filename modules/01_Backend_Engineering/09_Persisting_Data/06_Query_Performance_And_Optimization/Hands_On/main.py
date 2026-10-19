from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Iterator

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    event,
    func,
    select,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'performance_lab.db'}"


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(Integer, nullable=False)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    order_date: Mapped[str] = mapped_column(DateTime, nullable=False)


engine = create_engine(DATABASE_URL, future=True)


class QueryStats:
    count = 0

    @classmethod
    def reset(cls) -> None:
        cls.count = 0


@event.listens_for(engine, "before_cursor_execute")
def count_queries(conn, cursor, statement, parameters, context, executemany):
    QueryStats.count += 1


def reset_database() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE INDEX idx_products_order_date "
                "ON products(order_date)"
            )
        )

    with Session(engine) as session:
        customers = [
            Customer(id=customer_id, name=f"Customer {customer_id}")
            for customer_id in range(1, 101)
        ]
        session.add_all(customers)

        products = []
        for product_id in range(1, 2001):
            products.append(
                Product(
                    id=product_id,
                    store_id=(product_id % 10) + 1,
                    customer_id=((product_id - 1) % 100) + 1,
                    name=f"Product {product_id}",
                    category="electronics"
                    if product_id % 2 == 0
                    else "home",
                    price=(product_id % 500) + 100,
                    order_date=f"2026-01-{(product_id % 28) + 1:02d} 12:00:00",
                )
            )
        session.add_all(products)
        session.commit()


@contextmanager
def measure(label: str) -> Iterator[None]:
    QueryStats.reset()
    started = perf_counter()
    yield
    elapsed_ms = (perf_counter() - started) * 1000
    print(
        f"{label}: queries={QueryStats.count}, "
        f"elapsed_ms={elapsed_ms:.2f}"
    )


def explain(sql: str, params: dict | None = None) -> None:
    with engine.connect() as connection:
        rows = connection.execute(
            text(f"EXPLAIN QUERY PLAN {sql}"),
            params or {},
        ).all()
    for row in rows:
        print("  ", row)


def demonstrate_n_plus_one() -> None:
    print("\n=== 1. N+1 versus batched lookup ===")

    with Session(engine) as session:
        with measure("N+1 lookup"):
            products = session.scalars(
                select(Product).order_by(Product.id).limit(20)
            ).all()
            for product in products:
                session.scalar(
                    select(Customer).where(Customer.id == product.customer_id)
                )

    with Session(engine) as session:
        with measure("Batched lookup"):
            products = session.scalars(
                select(Product).order_by(Product.id).limit(20)
            ).all()
            customer_ids = {product.customer_id for product in products}
            session.scalars(
                select(Customer).where(Customer.id.in_(customer_ids))
            ).all()


def demonstrate_sargability() -> None:
    print("\n=== 2. Sargable versus non-sargable date filters ===")

    non_sargable = (
        "SELECT id FROM products "
        "WHERE strftime('%Y', order_date) = '2026'"
    )
    range_query = (
        "SELECT id FROM products "
        "WHERE order_date >= '2026-01-01' "
        "AND order_date < '2027-01-01'"
    )

    print("Function applied to the column:")
    explain(non_sargable)
    print("Direct range predicate:")
    explain(range_query)


def demonstrate_composite_index() -> None:
    print("\n=== 3. Composite index for filtering and ordering ===")

    query = (
        "SELECT id, name, price FROM products "
        "WHERE store_id = 7 AND category = 'electronics' "
        "ORDER BY price ASC"
    )

    print("Before composite index:")
    with engine.begin() as connection:
        connection.execute(text("DROP INDEX IF EXISTS idx_store_category_price"))
    explain(query)

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE INDEX idx_store_category_price "
                "ON products(store_id, category, price)"
            )
        )

    print("After composite index:")
    explain(query)


def demonstrate_projection() -> None:
    print("\n=== 4. Full entity versus projection ===")

    with Session(engine) as session:
        with measure("Full Product entities"):
            session.scalars(
                select(Product).where(Product.store_id == 7)
            ).all()

    with Session(engine) as session:
        with measure("Three-column projection"):
            session.execute(
                select(Product.id, Product.name, Product.price)
                .where(Product.store_id == 7)
            ).all()

    print("The projection asks the database and ORM for only required fields.")


def demonstrate_pagination() -> None:
    print("\n=== 5. Offset versus keyset pagination ===")

    offset_query = (
        "SELECT id, name, price FROM products "
        "ORDER BY id LIMIT 50 OFFSET 1000"
    )
    keyset_query = (
        "SELECT id, name, price FROM products "
        "WHERE id > 1000 ORDER BY id LIMIT 50"
    )

    print("Offset pagination:")
    explain(offset_query)
    print("Keyset pagination:")
    explain(keyset_query)


def demonstrate_query_count_as_signal() -> None:
    print("\n=== 6. Query count is a performance signal ===")

    with Session(engine) as session:
        QueryStats.reset()
        session.scalars(
            select(Product).where(Product.store_id == 7).limit(50)
        ).all()
        print(
            "A list endpoint should have an intentional query count. "
            f"This example executed {QueryStats.count} query."
        )


def main() -> None:
    reset_database()
    demonstrate_n_plus_one()
    demonstrate_sargability()
    demonstrate_composite_index()
    demonstrate_projection()
    demonstrate_pagination()
    demonstrate_query_count_as_signal()


if __name__ == "__main__":
    main()
