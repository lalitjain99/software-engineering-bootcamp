"""Topic 13 lab: retries, idempotency, leases, and fencing tokens."""

from __future__ import annotations

import asyncio
import hashlib
import random
import time
from dataclasses import dataclass
from typing import Any


class PermanentError(Exception):
    pass


class TransientError(Exception):
    pass


@dataclass
class IdempotencyRecord:
    fingerprint: str
    status: str
    response: dict[str, Any] | None = None
    locked_until: float = 0.0
    fencing_token: int = 0


class IdempotencyStore:
    def __init__(self) -> None:
        self.records: dict[tuple[str, str], IdempotencyRecord] = {}
        self._lock = asyncio.Lock()

    async def claim(
        self, client_id: str, key: str, fingerprint: str, lease_seconds: float
    ) -> tuple[str, IdempotencyRecord]:
        async with self._lock:
            record_key = (client_id, key)
            existing = self.records.get(record_key)
            now = time.monotonic()

            if existing is None:
                record = IdempotencyRecord(
                    fingerprint=fingerprint,
                    status='PROCESSING',
                    locked_until=now + lease_seconds,
                    fencing_token=1,
                )
                self.records[record_key] = record
                return 'CLAIMED', record

            if existing.fingerprint != fingerprint:
                return 'MISMATCH', existing

            if existing.status == 'COMPLETED':
                return 'REPLAY', existing

            if existing.status == 'PROCESSING' and existing.locked_until > now:
                return 'IN_PROGRESS', existing

            existing.status = 'PROCESSING'
            existing.locked_until = now + lease_seconds
            existing.fencing_token += 1
            return 'RECLAIMED', existing

    async def complete(
        self,
        client_id: str,
        key: str,
        fingerprint: str,
        fencing_token: int,
        response: dict[str, Any],
    ) -> bool:
        async with self._lock:
            record = self.records.get((client_id, key))
            if record is None or record.fingerprint != fingerprint:
                return False
            if record.status != 'PROCESSING' or record.fencing_token != fencing_token:
                return False
            record.status = 'COMPLETED'
            record.response = response
            record.locked_until = 0.0
            return True


async def retry(operation, attempts: int = 3, base_delay: float = 0.01):
    for attempt in range(attempts):
        try:
            return await operation()
        except PermanentError:
            raise
        except TransientError:
            if attempt == attempts - 1:
                raise
            ceiling = base_delay * (2**attempt)
            await asyncio.sleep(random.uniform(0, ceiling))


async def create_order(
    store: IdempotencyStore,
    client_id: str,
    key: str,
    payload: dict[str, Any],
    *,
    crash_before_complete: bool = False,
) -> dict[str, Any]:
    fingerprint = hashlib.sha256(repr(sorted(payload.items())).encode()).hexdigest()
    state, record = await store.claim(client_id, key, fingerprint, lease_seconds=0.05)

    if state == 'MISMATCH':
        raise ValueError('idempotency key reused with different parameters')
    if state == 'REPLAY':
        return {'outcome': 'REPLAYED', 'response': record.response}
    if state == 'IN_PROGRESS':
        return {'outcome': 'IN_PROGRESS'}

    fencing_token = record.fencing_token
    await asyncio.sleep(0.01)
    response = {'order_id': 'order-1', 'amount': payload['amount']}
    if crash_before_complete:
        return {'outcome': 'WORKER_CRASHED', 'token': fencing_token}

    accepted = await store.complete(
        client_id, key, fingerprint, fencing_token, response
    )
    if not accepted:
        return {'outcome': 'STALE_WORKER_REJECTED'}
    return {'outcome': state, 'response': response}


async def main() -> None:
    random.seed(7)
    store = IdempotencyStore()
    payload = {'amount': 100}

    results = await asyncio.gather(
        create_order(store, 'client-1', 'order-123', payload),
        create_order(store, 'client-1', 'order-123', payload),
    )
    print('duplicate requests:', results)

    replay = await create_order(store, 'client-1', 'order-123', payload)
    print('completed retry:', replay)

    try:
        await create_order(store, 'client-1', 'order-123', {'amount': 999})
    except ValueError as exc:
        print('payload mismatch:', exc)

    lease_payload = {'amount': 50}
    lease_fingerprint = hashlib.sha256(
        repr(sorted(lease_payload.items())).encode()
    ).hexdigest()
    first_state, first_record = await store.claim(
        'client-1', 'lease-demo', lease_fingerprint, lease_seconds=0.05
    )
    first_token = first_record.fencing_token
    print('initial lease:', first_state, 'token=', first_token)
    await asyncio.sleep(0.06)

    reclaim_state, reclaim_record = await store.claim(
        'client-1', 'lease-demo', lease_fingerprint, lease_seconds=0.05
    )
    print('reclaim:', reclaim_state, 'token=', reclaim_record.fencing_token)

    stale_accepted = await store.complete(
        'client-1',
        'lease-demo',
        lease_fingerprint,
        first_token,
        {'order_id': 'stale-order'},
    )
    print('stale worker accepted:', stale_accepted)

    current_accepted = await store.complete(
        'client-1',
        'lease-demo',
        lease_fingerprint,
        reclaim_record.fencing_token,
        {'order_id': 'order-2', 'amount': 50},
    )
    print('current worker accepted:', current_accepted)
    completed_retry = await create_order(
        store, 'client-1', 'lease-demo', lease_payload
    )
    print('completed retry:', completed_retry)


if __name__ == '__main__':
    asyncio.run(main())