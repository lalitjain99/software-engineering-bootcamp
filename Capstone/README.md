# Capstone — Production-Grade Enterprise Workflow Platform

## Goal

Build one evolving FastAPI-based system that demonstrates backend depth, system design, cloud deployment, and Technical Lead decision-making.

The product domain is intentionally simple: users create jobs/workflows, workers process them asynchronously, and clients track status and results. The engineering depth—not business complexity—is the focus.

## Layer 0 — Baseline

- Define functional and non-functional requirements
- Establish repository structure, coding standards, and local development workflow
- Record initial architecture and assumptions

## Layer 1 — Backend Foundation

- Modular FastAPI application
- PostgreSQL persistence and migrations
- Validation and consistent error contracts
- Configuration, structured logging, and tests

## Layer 2 — Enterprise API Concerns

- Authentication and authorization
- Idempotent job creation
- Pagination, filtering, and API versioning
- Rate limiting and audit trail

## Layer 3 — Performance and Asynchronous Work

- Async boundaries and background workers
- Queue or Pub/Sub integration
- Retry, timeout, dead-letter, and duplicate-delivery handling
- Redis caching with an explicit invalidation strategy

## Layer 4 — System Design Evolution

- Capacity estimates and service-level objectives
- Scaling and data-partitioning strategy
- Failure-mode analysis and resilience patterns
- Architecture Decision Records
- Split components only when evidence justifies the complexity

## Layer 5 — Production Delivery

- Secure multi-stage Docker image
- CI/CD with tests, scans, artifacts, and release gates
- Kubernetes deployment on GKE
- Terraform and Helm-based environment configuration
- Workload identity, secrets, resource limits, probes, and autoscaling
- Metrics, logs, traces, dashboards, and alerts
- Rollback and incident runbook

## Layer 6 — Technical Lead Narrative

- Architecture walkthrough
- Major decisions and rejected alternatives
- Production-readiness review
- Simulated incident and blameless postmortem
- Interview-ready project and leadership stories

## Definition of Done for Every Layer

- The feature works and is tested.
- The decision and alternatives are documented.
- Failure modes are identified.
- Security and observability are considered.
- The design can be explained in a Tech Lead interview.
