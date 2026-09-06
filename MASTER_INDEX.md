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
- A topic is not automatically one week; Tier B refreshers may take only one short session

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

The application grows step by step. Each topic starts from the previous design and introduces one new problem.

### Track 1A — Journey of an API Endpoint

1. 🟢 **[The simplest backend request](modules/01_Backend_Engineering/01_Request_Lifecycle/Notes.md)**
   - Client, server, host, port, request, route, Python function, and response
   - Notes, interview exercise, and hands-on exercise complete
2. 🟢 **[HTTP methods and their meaning](modules/01_Backend_Engineering/02_HTTP_Methods/Notes.md)**
   - `GET`, `POST`, `PUT`, `PATCH`, and `DELETE`
   - Safe operations, idempotent operations, and choosing the correct method
   - Notes, interview exercise, and hands-on exercise complete
3. 🟡 **[Sending input to an API](modules/01_Backend_Engineering/03_API_Input/Notes.md)**
   - Path parameters, query parameters, and request body
   - How to decide where each input belongs
4. ⚪ **HTTP headers**
   - Request versus response headers
   - `Content-Type`, `Accept`, `Authorization`, correlation IDs, and custom headers
5. ⚪ **Status codes and error responses**
   - Success, client-error, and server-error families
   - Designing consistent error contracts
6. ⚪ **HTTP, HTTPS, and protocol foundations**
   - The roles of IP, TCP, TLS, HTTP, and HTTPS
   - Why encryption changes HTTP into HTTPS
   - A gradual introduction to HTTP/1.1, HTTP/2, and HTTP/3
7. ⚪ **API styles and communication mechanisms**
   - REST, GraphQL, gRPC, WebSocket, Server-Sent Events, and webhooks
   - These are not all the same kind of protocol; compare the problems they solve
   - Choosing based on communication direction, latency, compatibility, and contract needs

**Checkpoint:** trace an API request, explain its complete HTTP contract, and choose an appropriate communication mechanism without discussing internal application architecture yet.

### Track 1B — Growing the Application

8. ⚪ **When one endpoint becomes too large**
   - Separate routing, business logic, and data access
9. ⚪ **Persisting data**
   - Database connection, models, queries, and transaction basics
10. ⚪ **When requests spend time waiting**
    - Blocking, synchronous execution, and the motivation for asynchronous I/O
11. ⚪ **Handling multiple tasks**
    - Event loop, threads, processes, and workload choice
12. ⚪ **When work cannot finish inside a request**
    - Background execution, workers, and queues
13. ⚪ **When operations repeat or fail**
    - Retries, idempotency, and safe state transitions
14. ⚪ **When the application becomes slow or unreliable**
    - Measurement, database diagnosis, resilience, and observability

### Track 1C — Production Backend Depth

After the foundations above, focused topics will deepen:

- FastAPI architecture and dependency management
- API versioning and compatibility
- Authentication and authorization
- Caching and messaging
- Testing strategy and code quality
- Application security
- Performance and reliability

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

Last updated: 2026-09-06
