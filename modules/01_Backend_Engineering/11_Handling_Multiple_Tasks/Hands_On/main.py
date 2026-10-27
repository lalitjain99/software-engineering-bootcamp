import asyncio
import os
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Callable


async def simulated_async_io(name: str, delay: float) -> str:
    print(f"[async] {name} started")
    await asyncio.sleep(delay)
    print(f"[async] {name} finished")
    return f"{name} result"


def simulated_blocking_io(name: str, delay: float) -> str:
    print(f"[thread] {name} started")
    time.sleep(delay)
    print(f"[thread] {name} finished")
    return f"{name} result"


def cpu_heavy_calculation(number: int) -> tuple[int, int]:
    # Deliberately simple CPU work for demonstration.
    total = 0
    for value in range(1, number + 1):
        total += value * value
    return os.getpid(), total


async def demonstrate_async_io() -> None:
    print("\n=== 1. Async I/O on the event loop ===")
    started = time.perf_counter()

    results = await asyncio.gather(
        simulated_async_io("products", 1.0),
        simulated_async_io("inventory", 1.5),
        simulated_async_io("reviews", 0.8),
    )

    elapsed = time.perf_counter() - started
    print(f"results={results}")
    print(f"elapsed={elapsed:.2f}s; expected close to 1.5s")


async def demonstrate_thread_pool() -> None:
    print("\n=== 2. Blocking I/O in a bounded thread pool ===")
    loop = asyncio.get_running_loop()
    started = time.perf_counter()

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="worker") as pool:
        futures = [
            loop.run_in_executor(
                pool,
                simulated_blocking_io,
                f"legacy-call-{index}",
                1.0,
            )
            for index in range(5)
        ]
        results = await asyncio.gather(*futures)

    elapsed = time.perf_counter() - started
    print(f"results={results}")
    print(f"elapsed={elapsed:.2f}s; five jobs with two workers run in batches")


async def demonstrate_process_pool() -> None:
    print("\n=== 3. CPU work in a process pool ===")
    loop = asyncio.get_running_loop()
    started = time.perf_counter()

    with ProcessPoolExecutor(max_workers=2) as pool:
        futures = [
            loop.run_in_executor(pool, cpu_heavy_calculation, 1_000_000 + index * 100_000)
            for index in range(4)
        ]
        results = await asyncio.gather(*futures)

    elapsed = time.perf_counter() - started
    process_ids = sorted({process_id for process_id, _ in results})
    print(f"worker process IDs={process_ids}")
    print(f"result count={len(results)}")
    print(f"elapsed={elapsed:.2f}s; four jobs with two processes run in batches")


async def queue_worker(
    worker_name: str,
    queue: asyncio.Queue[tuple[int, float] | None],
) -> None:
    while True:
        job = await queue.get()

        if job is None:
            queue.task_done()
            print(f"[queue] {worker_name} stopped")
            return

        job_id, delay = job
        print(f"[queue] {worker_name} processing job {job_id}")
        await asyncio.sleep(delay)
        print(f"[queue] {worker_name} completed job {job_id}")
        queue.task_done()


async def demonstrate_worker_queue() -> None:
    print("\n=== 4. In-process worker queue ===")
    queue: asyncio.Queue[tuple[int, float] | None] = asyncio.Queue()
    workers = [
        asyncio.create_task(queue_worker(f"worker-{index}", queue))
        for index in range(2)
    ]

    for job_id in range(1, 6):
        await queue.put((job_id, 0.5))

    await queue.join()

    for _ in workers:
        await queue.put(None)

    await asyncio.gather(*workers)
    print("Five jobs were handled by two reusable workers.")


async def demonstrate_mixed_models() -> None:
    print("\n=== 5. Mixed execution models ===")
    loop = asyncio.get_running_loop()
    started = time.perf_counter()

    async_results = asyncio.gather(
        simulated_async_io("catalog", 1.0),
        simulated_async_io("pricing", 1.2),
    )

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="legacy") as thread_pool, \
        ProcessPoolExecutor(max_workers=1) as process_pool:
        blocking_result = loop.run_in_executor(
            thread_pool,
            simulated_blocking_io,
            "legacy-service",
            1.0,
        )
        cpu_result = loop.run_in_executor(
            process_pool,
            cpu_heavy_calculation,
            1_000_000,
        )

        async_result, blocking_result, cpu_result = await asyncio.gather(
            async_results,
            blocking_result,
            cpu_result,
        )

    elapsed = time.perf_counter() - started
    print(f"async result={async_result}")
    print(f"blocking result={blocking_result}")
    print(f"CPU worker process ID={cpu_result[0]}")
    print(f"elapsed={elapsed:.2f}s")


async def main() -> None:
    await demonstrate_async_io()
    await demonstrate_thread_pool()
    await demonstrate_process_pool()
    await demonstrate_worker_queue()
    await demonstrate_mixed_models()


if __name__ == "__main__":
    asyncio.run(main())
