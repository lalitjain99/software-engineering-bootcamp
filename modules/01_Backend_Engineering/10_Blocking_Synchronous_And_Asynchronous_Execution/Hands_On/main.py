from __future__ import annotations

import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable
from time import perf_counter


async def simulated_io(name: str, delay: float) -> str:
    """Simulate an I/O operation without blocking the event loop."""
    print(f"[{name}] started; waiting {delay:.1f}s")
    await asyncio.sleep(delay)
    print(f"[{name}] completed")
    return f"result-{name}"


async def demonstrate_coroutine_lifecycle() -> None:
    print("\n=== 1. Coroutine lifecycle ===")

    coroutine = simulated_io("coroutine", 0.1)
    print(f"Created object type: {type(coroutine).__name__}")
    print(f"Is coroutine: {inspect.iscoroutine(coroutine)}")
    print("The body has not started before await.")

    result = await coroutine
    print(f"Result after await: {result}")


async def ticker(label: str, duration: float = 0.8) -> None:
    """Print regularly so event-loop pauses are visible."""
    started = perf_counter()
    tick = 0
    while perf_counter() - started < duration:
        print(f"[{label}] tick {tick} at {perf_counter() - started:.2f}s")
        tick += 1
        await asyncio.sleep(0.1)


async def blocking_wait() -> None:
    await asyncio.sleep(0.1)
    print("[blocking] entering time.sleep(0.5)")
    time.sleep(0.5)
    print("[blocking] finished")


async def cooperative_wait() -> None:
    await asyncio.sleep(0.1)
    print("[cooperative] entering await asyncio.sleep(0.5)")
    await asyncio.sleep(0.5)
    print("[cooperative] finished")


async def demonstrate_blocking_vs_cooperative() -> None:
    print("\n=== 2. Blocking versus cooperative waiting ===")
    print("Blocking version: ticker pauses while time.sleep() owns the event loop.")
    await asyncio.gather(ticker("blocking-ticker"), blocking_wait())

    print("\nCooperative version: ticker continues during asyncio.sleep().")
    await asyncio.gather(ticker("cooperative-ticker"), cooperative_wait())


async def run_sequential() -> list[str]:
    results = []
    for name, delay in (("products", 0.4), ("inventory", 0.3), ("reviews", 0.2)):
        results.append(await simulated_io(name, delay))
    return results


async def run_concurrent() -> list[str]:
    return list(
        await asyncio.gather(
            simulated_io("products", 0.4),
            simulated_io("inventory", 0.3),
            simulated_io("reviews", 0.2),
        )
    )


async def measure(label: str, operation: Callable[[], Awaitable[list[str]]]) -> None:
    started = perf_counter()
    results = await operation()
    elapsed = perf_counter() - started
    print(f"{label}: {elapsed:.2f}s; results={results}")


async def demonstrate_sequential_vs_concurrent() -> None:
    print("\n=== 3. Sequential versus concurrent work ===")
    await measure("Sequential", run_sequential)
    await measure("Concurrent with gather", run_concurrent)


async def demonstrate_semaphore() -> None:
    print("\n=== 4. Bounded concurrency with a semaphore ===")
    semaphore = asyncio.Semaphore(2)
    active = 0
    maximum_active = 0
    state_lock = asyncio.Lock()

    async def limited_call(call_number: int) -> str:
        nonlocal active, maximum_active

        async with semaphore:
            async with state_lock:
                active += 1
                maximum_active = max(maximum_active, active)
                print(f"call {call_number} entered; active={active}")

            try:
                await asyncio.sleep(0.25)
                return f"call-{call_number}-done"
            finally:
                async with state_lock:
                    active -= 1
                    print(f"call {call_number} leaving; active={active}")

    results = await asyncio.gather(
        *(limited_call(call_number) for call_number in range(1, 7))
    )
    print(f"Results: {results}")
    print(f"Maximum active calls observed: {maximum_active}")
    print("Expected: maximum active calls should not exceed 2.")


async def demonstrate_combined_pattern() -> None:
    print("\n=== 5. gather plus semaphore ===")
    semaphore = asyncio.Semaphore(2)

    async def limited_fetch(item: int) -> str:
        async with semaphore:
            print(f"fetching item {item}")
            await asyncio.sleep(0.2)
            return f"item-{item}"

    results = await asyncio.gather(
        *(limited_fetch(item) for item in range(1, 7))
    )
    print(f"Collected results: {results}")
    print("gather coordinated result collection; semaphore bounded active work.")


async def main() -> None:
    await demonstrate_coroutine_lifecycle()
    await demonstrate_blocking_vs_cooperative()
    await demonstrate_sequential_vs_concurrent()
    await demonstrate_semaphore()
    await demonstrate_combined_pattern()


if __name__ == "__main__":
    asyncio.run(main())
