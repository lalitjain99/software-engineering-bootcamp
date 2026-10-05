import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass


class PoolTimeout(Exception):
    """Raised when no connection becomes available before the deadline."""


class ConnectionBroken(Exception):
    """Raised when a simulated connection cannot communicate with the database."""


@dataclass
class SimulatedConnection:
    connection_id: int
    broken: bool = False
    transaction_open: bool = False

    async def begin(self) -> None:
        self._ensure_healthy()
        self.transaction_open = True
        print(f"  [conn-{self.connection_id}] transaction started")

    async def execute(self, sql: str) -> None:
        self._ensure_healthy()
        if not self.transaction_open:
            raise RuntimeError("execute() called without an active transaction")
        print(f"  [conn-{self.connection_id}] execute: {sql}")

    async def commit(self) -> None:
        self._ensure_healthy()
        self.transaction_open = False
        print(f"  [conn-{self.connection_id}] COMMIT")

    async def rollback(self) -> None:
        if self.transaction_open:
            self.transaction_open = False
            print(f"  [conn-{self.connection_id}] ROLLBACK")

    def _ensure_healthy(self) -> None:
        if self.broken:
            raise ConnectionBroken(f"conn-{self.connection_id} is broken")


class SimulatedPool:
    def __init__(
        self,
        *,
        min_size: int,
        max_size: int,
        checkout_timeout: float,
    ) -> None:
        if not 0 < min_size <= max_size:
            raise ValueError("Require 0 < min_size <= max_size")

        self.min_size = min_size
        self.max_size = max_size
        self.checkout_timeout = checkout_timeout
        self._available: asyncio.Queue[SimulatedConnection] = asyncio.Queue()
        self._total_connections = 0
        self._next_connection_id = 1

        for _ in range(min_size):
            self._available.put_nowait(self._new_connection())

    def _new_connection(self) -> SimulatedConnection:
        if self._total_connections >= self.max_size:
            raise RuntimeError("Pool has reached max_size")

        connection = SimulatedConnection(self._next_connection_id)
        self._next_connection_id += 1
        self._total_connections += 1
        print(f"[pool] created conn-{connection.connection_id}")
        return connection

    async def acquire(self) -> SimulatedConnection:
        try:
            connection = await asyncio.wait_for(
                self._available.get(),
                timeout=self.checkout_timeout,
            )
        except asyncio.TimeoutError as error:
            raise PoolTimeout(
                f"no connection available after {self.checkout_timeout:.2f}s"
            ) from error

        print(f"[pool] checked out conn-{connection.connection_id}")
        return connection

    async def release(self, connection: SimulatedConnection) -> None:
        if connection.broken:
            self._total_connections -= 1
            print(f"[pool] discarded broken conn-{connection.connection_id}")

            if self._total_connections < self.min_size:
                replacement = self._new_connection()
                self._available.put_nowait(replacement)
                print(
                    f"[pool] replacement conn-{replacement.connection_id} "
                    "is available"
                )
            return

        if connection.transaction_open:
            # A pool must never expose an unfinished transaction to another request.
            await connection.rollback()

        self._available.put_nowait(connection)
        print(f"[pool] returned conn-{connection.connection_id}")

    @asynccontextmanager
    async def connection(self):
        connection = await self.acquire()
        try:
            yield connection
        except Exception:
            # Rollback may itself fail for a broken connection. The broken
            # connection is discarded by release().
            await connection.rollback()
            raise
        finally:
            await self.release(connection)

    def stats(self) -> str:
        idle = self._available.qsize()
        in_use = self._total_connections - idle
        return (
            f"[pool] total={self._total_connections}, "
            f"in_use={in_use}, idle={idle}, max={self.max_size}"
        )


async def successful_request(pool: SimulatedPool, name: str) -> None:
    print(f"\n{name}: starting")
    async with pool.connection() as connection:
        await connection.begin()
        await connection.execute("UPDATE products SET price = 2400 WHERE id = 101")
        await asyncio.sleep(0.10)
        await connection.commit()
    print(f"{name}: completed")


async def failed_request(pool: SimulatedPool, name: str) -> None:
    print(f"\n{name}: starting")
    try:
        async with pool.connection() as connection:
            await connection.begin()
            await connection.execute("INSERT product (sku) VALUES ('KEY-101')")
            raise ValueError("simulated business error")
    except ValueError as error:
        print(f"{name}: failed safely: {error}")


async def long_request(pool: SimulatedPool, name: str, duration: float) -> None:
    print(f"\n{name}: starting")
    try:
        async with pool.connection() as connection:
            await connection.begin()
            await connection.execute("SELECT * FROM products")
            print(f"{name}: holding the connection for {duration:.2f}s")
            await asyncio.sleep(duration)
            await connection.commit()
            print(f"{name}: completed")
    except PoolTimeout as error:
        print(f"{name}: checkout timeout: {error}")


async def broken_connection_request(pool: SimulatedPool) -> None:
    print("\nBroken connection scenario: starting")
    try:
        async with pool.connection() as connection:
            await connection.begin()
            connection.broken = True
            await connection.execute("SELECT * FROM products")
    except ConnectionBroken as error:
        print(f"request: database connection error: {error}")
        print("request: application would decide whether a retry is safe")


async def main() -> None:
    pool = SimulatedPool(min_size=2, max_size=2, checkout_timeout=0.15)

    print("\n=== 1. Initial pool ===")
    print(pool.stats())

    print("\n=== 2. Commit and rollback ===")
    await successful_request(pool, "request-A")
    await failed_request(pool, "request-B")
    print(pool.stats())

    print("\n=== 3. Checkout timeout ===")
    await asyncio.gather(
        long_request(pool, "request-C", 0.40),
        long_request(pool, "request-D", 0.40),
        long_request(pool, "request-E", 0.05),
    )
    print(pool.stats())

    print("\n=== 4. Broken connection replacement ===")
    await broken_connection_request(pool)
    print(pool.stats())

    print("\n=== 5. Pool remains usable ===")
    await successful_request(pool, "request-F")
    print(pool.stats())


if __name__ == "__main__":
    asyncio.run(main())
