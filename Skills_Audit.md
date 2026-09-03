# Skills Audit

> Purpose: classify each topic by evidence, not confidence alone, so the roadmap focuses on real gaps.

## Tier Definitions

- **Tier A — Gap:** cannot explain the concept deeply, make design decisions, or implement/debug it independently.
- **Tier B — Rusty:** has used or understood it before but needs a compact refresh.
- **Tier C — Solid:** can explain trade-offs, use it independently, and handle follow-up questions.

## How to Audit a Topic

For every topic, test four dimensions:

1. **Explain:** Can I explain it clearly without notes?
2. **Decide:** Can I choose when to use it and defend the trade-offs?
3. **Build:** Can I implement or configure it independently?
4. **Operate:** Can I debug its failure modes in production?

- 0–1 strong dimensions → Tier A
- 2–3 strong dimensions → Tier B
- 4 strong dimensions → Tier C

## Known Baseline

| Area | Current evidence | Initial treatment |
|---|---|---|
| Python syntax, variables, and data types | Familiar | Candidate Tier C |
| Classes and exception handling | Familiar | Candidate Tier B/C |
| Modules and packages | Familiar | Candidate Tier B/C |
| API development | Practical experience | Candidate Tier B |
| FastAPI | Enterprise application experience | Tier A for architecture depth |
| Backend design decisions | Development goal | Tier A |
| System design | Development goal | Candidate Tier A |
| Production deployment and cloud decisions | Some practical exposure; depth required | Audit by capability |
| Technical leadership and interview narrative | Target capability | Candidate Tier A |

A topic becomes Tier C only after it passes the explain/decide/build/operate test.

## Detailed Audit

| Topic | Explain | Decide | Build | Operate | Tier | Evidence / gap |
|---|:---:|:---:|:---:|:---:|:---:|---|
| Python object/runtime model | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Typing and interface contracts | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Packaging and dependency management | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Asyncio, threading, multiprocessing, GIL | ❌ | ❌ | 🟡 | ❌ | A | Has used async/await; execution internals and model-selection trade-offs are unclear |
| HTTP and request lifecycle | ❌ | ❌ | 🟡 | ❌ | A | Can implement endpoints but is not yet sure how to divide synchronous request work and durable background work |
| REST API design and evolution | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| FastAPI architecture and internals | ❌ | ❌ | 🟡 | ❌ | A | Can build APIs within an existing structure; needs architecture ownership and production reasoning |
| Authentication and authorization | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Clean/hexagonal/modular architecture | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| SOLID and design patterns | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| SQL modeling, transactions, and indexes | ❌ | ❌ | 🟡 | ❌ | A | Can use SQL/ORM; needs diagnostics, indexing, transactions, locking, and concurrent-update depth |
| ORM, migrations, and connection pooling | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Caching and Redis | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Messaging and event-driven systems | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Testing strategy | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Application security | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Performance and resilience | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Distributed systems | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| High-level system design | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Low-level design | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Docker and image engineering | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Kubernetes | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| CI/CD and release strategy | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| GCP/Azure architecture and IAM | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Infrastructure as code | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Observability and incident response | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Architecture communication and ADRs | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| Mentoring, estimation, and prioritization | ⬜ | ⬜ | ⬜ | ⬜ | — | |

## Audit Completion Criteria

- Every row has evidence and a tier.
- Tier A topics form the main learning backlog.
- Tier B topics are scheduled as short refreshers.
- Tier C topics are removed from the teaching queue.
- Tiers are reviewed after each phase and after mock interviews.

## Audit Log

### 2026-09-03 — Backend Round 1 Finalized

- FastAPI architecture: Tier A
- Database performance and transactions: Tier A
- Concurrency and asyncio: Tier A
- HTTP request lifecycle and workload boundaries: Tier A
- Validation result: unable to design the integrated production scenario yet
- Decision: start with first-principles request lifecycle and architecture notes

Last updated: 2026-09-03
