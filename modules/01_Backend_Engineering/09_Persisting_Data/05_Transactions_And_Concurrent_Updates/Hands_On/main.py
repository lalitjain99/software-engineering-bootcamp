from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'transactions_lab.db'}"


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    stock: Mapped[int] = mapped_column(nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)


engine = create_engine(
    DATABASE_URL,
    future=True,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "before_cursor_execute")
def print_sql(conn, cursor, statement, parameters, context, executemany):
    compact = " ".join(statement.split())
    print(f"SQL> {compact} | params={parameters}")


def reset_database() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Product(id=101, name="Keyboard", stock=1, version=1))
        session.commit()


def read_product(session: Session) -> Product:
    product = session.get(Product, 101)
    if product is None:
        raise RuntimeError("Product 101 was not found")
    return product


def demonstrate_lost_update() -> None:
    print("\n=== 1. Lost update simulation ===")
    reset_database()

    session_a = Session(engine)
    session_b = Session(engine)

    try:
        product_a = read_product(session_a)
        product_b = read_product(session_b)

        print(f"Request A reads stock={product_a.stock}")
        print(f"Request B reads stock={product_b.stock}")

        if product_a.stock >= 1:
            product_a.stock -= 1

        if product_b.stock >= 1:
            product_b.stock -= 1

        session_a.commit()
        session_b.commit()

        with Session(engine) as verify:
            final_product = read_product(verify)
            print("Both requests accepted their reservation.")
            print(f"Final database stock={final_product.stock}")
            print("Business result: two reservations were accepted for one item.")
    finally:
        session_a.close()
        session_b.close()


def demonstrate_rollback() -> None:
    print("\n=== 2. Rollback ===")
    reset_database()

    with Session(engine) as session:
        product = read_product(session)
        product.stock = -1
        print("A failing business condition is detected.")
        session.rollback()

    with Session(engine) as verify:
        product = read_product(verify)
        print(f"Stock after rollback={product.stock}")
        print("The uncommitted change was discarded.")


def demonstrate_atomic_update() -> None:
    print("\n=== 3. Atomic conditional update ===")
    reset_database()

    with Session(engine) as session:
        result = session.execute(
            update(Product)
            .where(Product.id == 101, Product.stock >= 1)
            .values(stock=Product.stock - 1)
        )
        session.commit()
        print(f"First reservation affected rows={result.rowcount}")

    with Session(engine) as session:
        result = session.execute(
            update(Product)
            .where(Product.id == 101, Product.stock >= 1)
            .values(stock=Product.stock - 1)
        )
        session.commit()
        print(f"Second reservation affected rows={result.rowcount}")
        print("The second request must be treated as insufficient stock or conflict.")


def demonstrate_optimistic_locking() -> None:
    print("\n=== 4. Optimistic locking ===")
    reset_database()

    session_a = Session(engine)
    session_b = Session(engine)

    try:
        product_a = read_product(session_a)
        product_b = read_product(session_b)

        old_version_a = product_a.version
        old_version_b = product_b.version

        first = session_a.execute(
            update(Product)
            .where(Product.id == 101, Product.version == old_version_a)
            .values(
                stock=Product.stock - 1,
                version=Product.version + 1,
            )
        )
        session_a.commit()
        print(
            f"First versioned update affected rows={first.rowcount}; "
            "version is now 2."
        )

        second = session_b.execute(
            update(Product)
            .where(Product.id == 101, Product.version == old_version_b)
            .values(
                stock=Product.stock - 1,
                version=Product.version + 1,
            )
        )
        session_b.commit()
        print(f"Stale versioned update affected rows={second.rowcount}")
        print("Zero rows means the second request used stale data.")
    finally:
        session_a.close()
        session_b.close()


def demonstrate_pessimistic_lock_sql() -> None:
    print("\n=== 5. Pessimistic locking ===")
    statement = (
        select(Product)
        .where(Product.id == 101)
        .with_for_update()
    )
    compiled = statement.compile(
        engine,
        compile_kwargs={"literal_binds": True},
    )
    print("SQLAlchemy statement:")
    print(compiled)
    print(
        "SQLite does not enforce PostgreSQL-style row-level FOR UPDATE "
        "blocking. Test this behavior with PostgreSQL for a real lock wait."
    )


def demonstrate_lock_order() -> None:
    print("\n=== 6. Deadlock prevention by lock order ===")
    cart_a = [202, 101]
    cart_b = [101, 202]

    ordered_a = sorted(cart_a)
    ordered_b = sorted(cart_b)

    print(f"Request A locks in order: {ordered_a}")
    print(f"Request B locks in order: {ordered_b}")
    print(
        "Both requests acquire Product 101 before Product 202, so they "
        "cannot form the A-waits-for-B/B-waits-for-A cycle."
    )


def verify_invariant() -> None:
    print("\n=== 7. Final inventory invariant ===")
    reset_database()

    with Session(engine) as session:
        result = session.execute(
            update(Product)
            .where(Product.id == 101, Product.stock >= 1)
            .values(stock=Product.stock - 1)
        )
        session.commit()
        successful_reservations = result.rowcount

    with Session(engine) as session:
        product = read_product(session)
        print(f"Successful reservations={successful_reservations}")
        print(f"Final stock={product.stock}")
        assert successful_reservations == 1
        assert product.stock == 0
        assert product.stock >= 0
        print("Invariant passed: reservations do not exceed available stock.")


def main() -> None:
    demonstrate_lost_update()
    demonstrate_rollback()
    demonstrate_atomic_update()
    demonstrate_optimistic_locking()
    demonstrate_pessimistic_lock_sql()
    demonstrate_lock_order()
    verify_invariant()


if __name__ == "__main__":
    main()
