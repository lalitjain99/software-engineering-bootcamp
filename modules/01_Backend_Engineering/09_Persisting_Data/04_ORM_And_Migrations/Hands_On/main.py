from __future__ import annotations

from pathlib import Path

from sqlalchemy import (
    DECIMAL,
    Integer,
    String,
    create_engine,
    event,
    inspect,
    select,
    text,
    update,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    joinedload,
    mapped_column,
    relationship,
    selectinload,
)


DATABASE_FILE = Path(__file__).with_name("orm_lab.db")
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"


class Base(DeclarativeBase):
    pass


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    products: Mapped[list["Product"]] = relationship(
        back_populates="store",
        lazy="select",
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    store: Mapped[Store] = relationship(
        back_populates="products",
        lazy="select",
    )


def create_engine_and_counter():
    engine = create_engine(DATABASE_URL, future=True)
    query_counter = {"count": 0}

    @event.listens_for(engine, "before_cursor_execute")
    def count_queries(
        _connection,
        _cursor,
        statement,
        parameters,
        _context,
        _executemany,
    ):
        query_counter["count"] += 1
        print(f"  SQL: {statement.strip()} | params={parameters}")

    return engine, query_counter


def reset_database(engine) -> None:
    if DATABASE_FILE.exists():
        DATABASE_FILE.unlink()

    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE stores (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL
            )
            """
        )
        connection.exec_driver_sql(
            """
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                store_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                sku VARCHAR(50) NOT NULL UNIQUE,
                price NUMERIC(10, 2) NOT NULL CHECK (price > 0),
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO stores (id, name)
            VALUES
                (1, 'Noida Store'),
                (2, 'Gurgaon Store')
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO products (id, store_id, name, sku, price)
            VALUES
                (101, 1, 'Keyboard', 'KEY-101', 2500),
                (102, 1, 'Mouse', 'MOU-102', 900),
                (103, 2, 'Monitor', 'MON-103', 12000),
                (104, 2, 'Webcam', 'WEB-104', 3500)
            """
        )


def run_schema_migration(engine) -> None:
    print("\n=== Schema migration: add category column ===")
    columns = {column["name"] for column in inspect(engine).get_columns("products")}

    if "category" not in columns:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE products ADD COLUMN category VARCHAR(50)"
            )
        print("Migration applied: category column added")
    else:
        print("Migration already applied")


def run_resumable_backfill(engine, batch_size: int = 2) -> None:
    print("\n=== Resumable category backfill ===")

    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS backfill_progress (
                job_name VARCHAR(100) PRIMARY KEY,
                last_processed_id INTEGER NOT NULL
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT OR IGNORE INTO backfill_progress
                (job_name, last_processed_id)
            VALUES ('product_category', 0)
            """
        )

    while True:
        with Session(engine) as session:
            with session.begin():
                last_id = session.execute(
                    text(
                        """
                        SELECT last_processed_id
                        FROM backfill_progress
                        WHERE job_name = 'product_category'
                        """
                    )
                ).scalar_one()

                ids = session.execute(
                    text(
                        """
                        SELECT id
                        FROM products
                        WHERE category IS NULL
                          AND id > :last_id
                        ORDER BY id
                        LIMIT :batch_size
                        """
                    ),
                    {"last_id": last_id, "batch_size": batch_size},
                ).scalars().all()

                if not ids:
                    print("Backfill complete")
                    return

                session.execute(
                    update(Product)
                    .where(Product.id.in_(ids), Product.category.is_(None))
                    .values(category="general")
                )
                session.execute(
                    text(
                        """
                        UPDATE backfill_progress
                        SET last_processed_id = :last_id
                        WHERE job_name = 'product_category'
                        """
                    ),
                    {"last_id": max(ids)},
                )
                print(f"Committed batch ids={ids}; checkpoint={max(ids)}")


def demonstrate_loading_strategies(engine, query_counter) -> None:
    print("\n=== Lazy loading: possible N+1 pattern ===")
    query_counter["count"] = 0

    with Session(engine) as session:
        products = session.scalars(select(Product).order_by(Product.id)).all()
        for product in products:
            print(f"  {product.name} belongs to {product.store.name}")

    print(f"Lazy-loading query count: {query_counter['count']}")

    print("\n=== joinedload: many-to-one relationship ===")
    query_counter["count"] = 0

    with Session(engine) as session:
        products = session.scalars(
            select(Product)
            .options(joinedload(Product.store))
            .order_by(Product.id)
        ).all()
        for product in products:
            print(f"  {product.name} belongs to {product.store.name}")

    print(f"joinedload query count: {query_counter['count']}")

    print("\n=== selectinload: one-to-many relationship ===")
    query_counter["count"] = 0

    with Session(engine) as session:
        stores = session.scalars(
            select(Store)
            .options(selectinload(Store.products))
            .order_by(Store.id)
        ).all()
        for store in stores:
            product_names = [product.name for product in store.products]
            print(f"  {store.name}: {product_names}")

    print(f"selectinload query count: {query_counter['count']}")


def demonstrate_transactions(engine) -> None:
    print("\n=== Transaction success and rollback ===")

    with Session(engine) as session:
        product = session.get(Product, 101)
        product.price = 2400
        session.commit()
        print("Committed price update for product 101")

    try:
        with Session(engine) as session:
            with session.begin():
                session.add(
                    Product(
                        store_id=1,
                        name="Duplicate Keyboard",
                        sku="KEY-101",
                        price=2500,
                        category="general",
                    )
                )
    except IntegrityError as error:
        print("Duplicate SKU failed and transaction was rolled back")
        print(f"  Database error type: {type(error).__name__}")


def print_final_state(engine) -> None:
    print("\n=== Final state ===")
    with Session(engine) as session:
        products = session.scalars(select(Product).order_by(Product.id)).all()
        for product in products:
            print(
                f"  id={product.id}, sku={product.sku}, "
                f"price={product.price}, category={product.category}"
            )

        checkpoint = session.execute(
            text(
                """
                SELECT job_name, last_processed_id
                FROM backfill_progress
                """
            )
        ).all()
        print(f"Checkpoint: {checkpoint}")


def main() -> None:
    engine, query_counter = create_engine_and_counter()
    reset_database(engine)

    print("=== Initial schema ===")
    print("The products table initially has no category column.")

    run_schema_migration(engine)
    run_resumable_backfill(engine)
    demonstrate_loading_strategies(engine, query_counter)
    demonstrate_transactions(engine)
    print_final_state(engine)

    engine.dispose()


if __name__ == "__main__":
    main()
