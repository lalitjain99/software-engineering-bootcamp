import asyncio
from dataclasses import dataclass, field
from typing import Literal


JobStatus = Literal[
    "QUEUED",
    "RUNNING",
    "CANCELLING",
    "SUCCEEDED",
    "FAILED",
    "CANCELLED",
]


@dataclass
class Job:
    job_id: str
    behavior: str = "success"
    status: JobStatus = "QUEUED"
    attempts: int = 0
    cancel_requested: bool = False
    error: str | None = None


@dataclass
class InMemoryJobStore:
    jobs: dict[str, Job] = field(default_factory=dict)
    outbox: list[str] = field(default_factory=list)
    dead_letter_queue: list[str] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def create_job(self, job_id: str, behavior: str) -> Job:
        async with self.lock:
            job = Job(job_id=job_id, behavior=behavior)
            self.jobs[job_id] = job
            self.outbox.append(job_id)
            print(f"[db] created job={job_id} and outbox event in one simulated transaction")
            return job

    async def claim(self, job_id: str, worker_name: str) -> bool:
        async with self.lock:
            job = self.jobs[job_id]
            if job.status != "QUEUED":
                print(
                    f"[{worker_name}] could not claim {job_id}; "
                    f"current_status={job.status}"
                )
                return False

            job.status = "RUNNING"
            job.attempts += 1
            print(f"[{worker_name}] claimed job={job_id}; attempt={job.attempts}")
            return True

    async def request_cancel(self, job_id: str) -> str:
        async with self.lock:
            job = self.jobs[job_id]

            if job.status == "QUEUED":
                job.cancel_requested = True
                job.status = "CANCELLED"
                print(f"[api] job={job_id} cancelled while queued")
                return job.status

            if job.status == "RUNNING":
                job.cancel_requested = True
                job.status = "CANCELLING"
                print(f"[api] cancellation requested for running job={job_id}")
                return job.status

            print(f"[api] job={job_id} already in terminal state={job.status}")
            return job.status

    async def mark_success(self, job_id: str) -> None:
        async with self.lock:
            self.jobs[job_id].status = "SUCCEEDED"

    async def mark_retryable_failure(self, job_id: str, error: str) -> None:
        async with self.lock:
            job = self.jobs[job_id]
            job.status = "QUEUED"
            job.error = error

    async def mark_failed(self, job_id: str, error: str) -> None:
        async with self.lock:
            job = self.jobs[job_id]
            job.status = "FAILED"
            job.error = error
            self.dead_letter_queue.append(job_id)

    async def mark_cancelled(self, job_id: str) -> None:
        async with self.lock:
            self.jobs[job_id].status = "CANCELLED"


async def submit_report(store: InMemoryJobStore, job_id: str, behavior: str) -> dict[str, str]:
    await store.create_job(job_id, behavior)
    response = {
        "status_code": "202 Accepted",
        "job_id": job_id,
        "status": "queued",
    }
    print(f"[api] response={response}")
    return response


async def relay_outbox(store: InMemoryJobStore, queue: asyncio.Queue[str]) -> None:
    print("[relay] publishing outbox events")

    while store.outbox:
        job_id = store.outbox.pop(0)
        job = store.jobs[job_id]

        if job.status == "CANCELLED":
            print(f"[relay] skipping cancelled job={job_id}")
            continue

        await queue.put(job_id)
        print(f"[relay] published job={job_id} to queue")


async def process_job(
    store: InMemoryJobStore,
    queue: asyncio.Queue[str],
    worker_name: str,
    max_attempts: int = 2,
) -> None:
    while True:
        job_id = await queue.get()

        if job_id == "__STOP__":
            queue.task_done()
            print(f"[{worker_name}] stopped")
            return

        try:
            claimed = await store.claim(job_id, worker_name)
            if not claimed:
                continue

            job = store.jobs[job_id]

            if job.cancel_requested:
                await store.mark_cancelled(job_id)
                print(f"[{worker_name}] cancelled job={job_id} before work")
                continue

            await asyncio.sleep(0.2)

            if job.cancel_requested:
                await store.mark_cancelled(job_id)
                print(f"[{worker_name}] stopped job={job_id} at a safe checkpoint")
                continue

            if job.behavior == "retry_once" and job.attempts == 1:
                raise RuntimeError("temporary downstream timeout")

            if job.behavior == "always_fail":
                raise ValueError("invalid report input")

            await store.mark_success(job_id)
            print(f"[{worker_name}] completed job={job_id}")

        except RuntimeError as exc:
            job = store.jobs[job_id]
            if job.attempts < max_attempts:
                await store.mark_retryable_failure(job_id, str(exc))
                await queue.put(job_id)
                print(f"[{worker_name}] retrying job={job_id}")
            else:
                await store.mark_failed(job_id, str(exc))
                print(f"[{worker_name}] sent job={job_id} to DLQ")

        except Exception as exc:
            await store.mark_failed(job_id, str(exc))
            print(f"[{worker_name}] sent job={job_id} to DLQ")

        finally:
            queue.task_done()


async def demonstrate_backpressure() -> None:
    print("\n=== Backpressure demonstration ===")
    queue: asyncio.Queue[str] = asyncio.Queue(maxsize=2)

    for job_id in ("capacity-1", "capacity-2", "capacity-3"):
        try:
            queue.put_nowait(job_id)
            print(f"[api] accepted {job_id}")
        except asyncio.QueueFull:
            print(f"[api] rejected {job_id}: 503 Service Unavailable")
            print("[api] Retry-After: 10")


async def run_pipeline() -> None:
    print("=== Background report pipeline ===")
    store = InMemoryJobStore()
    queue: asyncio.Queue[str] = asyncio.Queue(maxsize=10)

    await submit_report(store, "job-success", "success")
    await submit_report(store, "job-retry", "retry_once")
    await submit_report(store, "job-failure", "always_fail")
    await submit_report(store, "job-cancelled", "success")

    await store.request_cancel("job-cancelled")
    await relay_outbox(store, queue)

    workers = [
        asyncio.create_task(process_job(store, queue, "worker-1")),
        asyncio.create_task(process_job(store, queue, "worker-2")),
    ]

    await queue.join()

    for _ in workers:
        await queue.put("__STOP__")
    await asyncio.gather(*workers)

    print("\nFinal job states:")
    for job in store.jobs.values():
        print(
            f"  {job.job_id}: status={job.status}, "
            f"attempts={job.attempts}, error={job.error}"
        )

    print(f"Dead-letter queue: {store.dead_letter_queue}")


async def main() -> None:
    await run_pipeline()
    await demonstrate_backpressure()


if __name__ == "__main__":
    asyncio.run(main())
