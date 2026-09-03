# Software Engineering Bootcamp — Master Index

> Core objective: develop Technical Lead-level judgment across backend design, system architecture, production delivery, and engineering leadership.

## Roadmap Constraints

- 5–8 hours per week
- Interview-ready target: 6–12 months
- Default plan: 36 weeks
- Python basics are not retaught unless the skills audit exposes a gap
- Topic depth is controlled by Tier A/B/C, not by a fixed document template

## Status Legend

- ⚪ Planned
- 🟡 In progress
- 🟢 Complete
- 🔁 Revisiting

## Phase 0 — Skills Audit and Setup (Week 0–1)

- 🟡 Complete [Skills_Audit.md](Skills_Audit.md)
- ⚪ Assign Tier A, B, or C to each topic
- ⚪ Establish the capstone baseline and development workflow
- ⚪ Record the first leadership-journal entry

**Exit outcome:** a personalized backlog that spends time on genuine gaps rather than revisiting every Python basic.

## Phase 1 — Backend Engineering Depth (Weeks 1–14)

### 1. Production Python

- Runtime and object model relevant to production
- Type hints, contracts, exceptions, logging, configuration, and dependency management
- Threads, processes, the GIL, asyncio, cancellation, and backpressure
- Profiling, memory, and performance reasoning

### 2. HTTP and API Engineering

- HTTP lifecycle, methods, headers, status codes, TLS, proxies, and gateways
- REST resource modeling, versioning, pagination, filtering, idempotency, and compatibility
- Validation and consistent error contracts
- Authentication, authorization, rate limiting, and API security

### 3. FastAPI at Technical Lead Depth

- Dependency injection, middleware, lifespan, background work, and async boundaries
- Modular project structure and separation of concerns
- Configuration, observability, exception strategy, and OpenAPI governance
- When FastAPI is appropriate—and when it is not

### 4. Application Architecture and Code Quality

- Layered, clean, hexagonal, and modular-monolith architectures
- SOLID and design patterns as decision tools
- Domain boundaries, coupling, cohesion, and dependency direction
- Refactoring strategy, code reviews, and technical-debt decisions

### 5. Data and Persistence

- Data modeling and schema evolution
- Transactions, isolation levels, locking, and concurrency control
- Indexes, query plans, connection pools, ORMs, and migrations
- SQL versus NoSQL decision-making

### 6. Backend Building Blocks

- Caching strategies, invalidation, Redis, and cache failure modes
- Background jobs, schedulers, retries, and dead-letter handling
- Queues, Pub/Sub, event-driven architecture, delivery semantics, and idempotent consumers
- File and object-storage workflows

### 7. Testing, Security, and Reliability

- Unit, integration, contract, end-to-end, and load testing
- Test doubles and testable architecture
- Secrets, common web vulnerabilities, dependency and container scanning
- Timeouts, retries, circuit breakers, graceful degradation, and failure budgets

**Phase output:** a production-quality FastAPI application and the ability to defend its architectural decisions.

## Phase 2 — System Design (Weeks 15–24)

### 1. Design Method

- Clarify functional and non-functional requirements
- Estimate scale, storage, throughput, and latency
- Identify constraints and define measurable success
- Compare alternatives through explicit trade-offs

### 2. Distributed-System Foundations

- Processes, networks, partial failure, clocks, and coordination
- Availability, consistency, partition tolerance, and replication
- Stateless services, horizontal scaling, load balancing, and service discovery
- Synchronous versus asynchronous communication

### 3. Data and Scale

- Partitioning, replication, read/write paths, and hot partitions
- Distributed caching, CDN, queues, streams, and search
- Consistency models, eventual consistency, and conflict handling
- Reliability patterns and observability

### 4. Design Practice

- Reusable system-design building blocks
- High-level design case studies
- Low-level design and component boundaries
- Architecture Decision Records (ADRs)
- Communicating trade-offs in Tech Lead interviews

**Phase output:** multiple timed design exercises plus an architecture evolution of the capstone.

## Phase 3 — DevOps, Cloud, and Production (Weeks 25–32)

- Linux processes, signals, filesystems, and production debugging
- Networking, DNS, TLS, reverse proxies, ingress, and service communication
- Docker images, layers, multi-stage builds, supply-chain security, and runtime limits
- CI/CD pipelines, quality gates, artifacts, release controls, and rollback
- Kubernetes workloads, services, probes, resources, configuration, secrets, autoscaling, and disruption
- GCP as the primary cloud, with Azure service mapping where useful
- IAM, workload identity, networking, storage, managed databases, messaging, and secrets
- Terraform, Helm, environment promotion, and configuration strategy
- Metrics, logs, traces, SLOs, alerts, incident response, and postmortems
- Rolling, blue-green, and canary deployments

**Phase output:** containerized capstone deployed through CI/CD with infrastructure as code, observability, security controls, and a rollback strategy.

## Phase 4 — Leadership and Interview Synthesis (Weeks 33–36)

- Converting technical work into clear STAR and engineering-leadership stories
- Architecture reviews and decision facilitation
- Estimation, prioritization, risk management, and technical debt
- Mentoring, delegation, code-review standards, and conflict handling
- Incident ownership and blameless postmortems
- Senior/Tech Lead backend interviews
- High-level and low-level system-design interviews
- Production, cloud, and troubleshooting interviews
- Behavioral and leadership mock interviews

**Phase output:** an interview story bank, architecture walkthrough, resume-aligned project narrative, and mock-interview feedback loop.

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
