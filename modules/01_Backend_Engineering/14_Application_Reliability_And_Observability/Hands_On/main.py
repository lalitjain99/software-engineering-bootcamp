"""Topic 14 lab: a small observability and diagnosis simulation."""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Span:
    name: str
    start_ms: float
    end_ms: float
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return round(self.end_ms - self.start_ms, 2)


@dataclass
class RequestResult:
    scenario: str
    total_ms: float
    spans: list[Span]
    status_code: int = 200


def percentile(values: list[float], percentage: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    rank = (len(ordered) - 1) * percentage / 100
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction, 2)


def emit_log(event: str, **fields: Any) -> None:
    record = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'level': 'INFO',
        'event': event,
        **fields,
    }
    print(json.dumps(record, sort_keys=True))


def simulate_request(
    scenario: str,
    *,
    pool_wait_ms: float = 5,
    lock_wait_ms: float = 0,
    sql_ms: float = 10,
    external_ms: float = 20,
    serialization_ms: float = 5,
) -> RequestResult:
    spans: list[Span] = []
    started = time.perf_counter()

    def stage(name: str, duration_ms: float, **attributes: Any) -> None:
        stage_start = (time.perf_counter() - started) * 1000
        time.sleep(duration_ms / 1000)
        stage_end = (time.perf_counter() - started) * 1000
        spans.append(Span(name, stage_start, stage_end, attributes))

    stage('db.pool.checkout', pool_wait_ms, pool_state='waiting')
    stage('db.lock.wait', lock_wait_ms, lock_owner='transaction-42' if lock_wait_ms else None)
    stage('db.query', sql_ms, rows=20)
    stage('inventory.http', external_ms, dependency='inventory-service')
    stage('response.serialization', serialization_ms, payload_bytes=2400)

    total_ms = round((time.perf_counter() - started) * 1000, 2)
    emit_log(
        'request.completed',
        scenario=scenario,
        route='/orders',
        status_code=200,
        duration_ms=total_ms,
        trace_id=f'trace-{scenario}',
    )
    for span in spans:
        emit_log(
            'trace.span',
            trace_id=f'trace-{scenario}',
            span=span.name,
            duration_ms=span.duration_ms,
            **span.attributes,
        )
    return RequestResult(scenario, total_ms, spans)


def print_trace(result: RequestResult) -> None:
    print(f'\nTRACE: {result.scenario} ({result.total_ms} ms total)')
    for span in result.spans:
        print(f'  {span.name:<28} {span.duration_ms:>7.2f} ms')


def main() -> None:
    scenarios = [
        ('healthy', dict()),
        ('slow-external', dict(external_ms=180)),
        ('lock-contention', dict(pool_wait_ms=90, lock_wait_ms=220)),
    ]
    results: list[RequestResult] = []
    for scenario, options in scenarios:
        results.append(simulate_request(scenario, **options))

    for result in results:
        print_trace(result)

    latencies = [result.total_ms for result in results]
    print('\nMETRICS')
    print(f'  request_count: {len(results)}')
    print(f'  p50_latency_ms: {percentile(latencies, 50)}')
    print(f'  p95_latency_ms: {percentile(latencies, 95)}')
    print(f'  average_latency_ms: {round(statistics.mean(latencies), 2)}')
    print('  error_rate: 0.0%')
    print('  diagnosis_hint: inspect dependency spans and pool/lock wait before changing SQL')


if __name__ == '__main__':
    main()