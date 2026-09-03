# Software Engineering Bootcamp — Master Index

> Core objective: develop Technical Lead-level judgment across backend design, system architecture, production delivery, and engineering leadership.

## Roadmap Constraints

- 5–8 hours per week
- Interview-ready target: 6–12 months
- Default plan: 36 weeks
- Python basics are not retaught unless the skills audit exposes a gap
- Topic depth is controlled by Tier A/B/C, not by a fixed document template
- Each lesson introduces one primary mental model
- Advanced terms are introduced only after the problem that requires them

## Status Legend

- ⚪ Planned
- 🟡 In progress
- 🟢 Complete
- 🔁 Revisiting

## Phase 0 — Skills Audit and Setup (Week 0–1)

- 🟡 Complete [Skills_Audit.md](Skills_Audit.md)
- ⚪ Assign Tier A, B, or C incrementally
- ⚪ Establish the capstone baseline and development workflow
- ⚪ Record the first leadership-journal entry

The audit does not block a topic once a clear Tier A gap has been identified.

## Phase 1 — Backend Engineering Depth (Weeks 1–14)

### Atomic Learning Sequence

The backend grows step by step. Each topic begins with the previous design and introduces one new problem.

1. 🟡 **[The simplest backend request](modules/01_Backend_Engineering/01_Request_Lifecycle/Notes.md)**
   - Client, server, request, route, Python function, and response
2. ⚪ **When one endpoint becomes too large**
   - Separate routing, business logic, and data access
3. ⚪ **Persisting data**
   - Database connection, models, queries, and transaction basics
4. ⚪ **When requests spend time waiting**
   - Blocking, synchronous execution, and the motivation for asynchronous I/O
5. ⚪ **Handling multiple tasks**
   - Event loop, threads, processes, and workload choice
6. ⚪ **When work cannot finish inside a request**
   - Background execution, workers, and queues
7. ⚪ **When operations repeat or fail**
   - Retries, idempotency, and safe state transitions
8. ⚪ **When the application becomes slow or unreliable**
   - Measurement, database diagnosis, resilience, and observability

Only after this foundation will we expand into deeper API design, security, testing, caching, messaging, and production architecture.

### Backend Capability Map

The sequence above eventually develops these capabilities:

- Production Python and dependency management
- HTTP and API engineering
- FastAPI architecture
- Application architecture and code quality
- Data modeling and persistence
- Caching, messaging, and background work
- Testing, security, performance, and reliability

**Phase output:** a production-quality FastAPI application and the ability to explain how each design decision emerged.

## Phase 2 — System Design (Weeks 15–24)

- Requirements clarification and capacity estimation
- Distributed-system foundations
- Scaling, data, caching, queues, and consistency
- High-level and low-level design practice
- Architecture Decision Records and trade-off communication

## Phase 3 — DevOps, Cloud, and Production (Weeks 25–32)

- Linux and networking foundations
- Docker and container security
- CI/CD and release strategies
- Kubernetes and GCP, with Azure mapping where useful
- Infrastructure as code
- Observability, SLOs, incident response, and rollback

## Phase 4 — Leadership and Interview Synthesis (Weeks 33–36)

- Technical decision and behavioral story bank
- Architecture reviews
- Estimation, prioritization, risk, and technical debt
- Mentoring and code-review standards
- Backend, system-design, production, and leadership mock interviews

## Deliverable Rules

### Tier A — Real gap

```text
Topic/
├── Notes.md
├── Interview.md          # Q&A plus Common Mistakes section
└── Hands_On/
    ├── README.md
    └── ... code
```

### Tier B — Rusty

```text
Topic/
├── CheatSheet.md
└── Common_Mistakes.md
```

### Tier C — Already solid

- One checklist tick in `Skills_Audit.md`
- No formal topic document
- Revisit only during interview review or when practice exposes a gap

## Weekly Operating Rhythm

| Activity | Weekly time |
|---|---:|
| Core roadmap learning | 3–4.5 hours |
| Capstone implementation | 1–1.5 hours |
| Coding practice | 30–45 minutes |
| Leadership journal | 20–30 minutes |
| Review and planning | 10–45 minutes |
| **Total** | **Approximately 5–8 hours** |

Last updated: 2026-09-03
