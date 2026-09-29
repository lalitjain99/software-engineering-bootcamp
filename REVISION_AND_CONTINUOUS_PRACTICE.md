# Revision and Continuous Practice Plan

> The roadmap does not move forward only by adding new topics. Revision, capstone implementation, coding practice, and leadership reflection run throughout the journey.

## Weekly Time Budget

The plan remains within the target of 5–8 hours per week.

| Activity | Weekly time |
|---|---:|
| Current core topic | 2.5–3.5 hours |
| Hands-on work or capstone evolution | 1–1.5 hours |
| Closed-book revision | 30–45 minutes |
| Light coding practice | 30–45 minutes |
| Leadership journal | 20–30 minutes |
| Planning and progress update | 10–20 minutes |
| **Total** | **Approximately 5–7.5 hours** |

A consolidation checkpoint may temporarily reduce new-topic time and increase revision time.

## Three Revision Levels

### 1. Weekly recall

Every week:

1. Close the notes.
2. Explain two recent concepts aloud or in chat.
3. Use one concrete example for each.
4. Record anything that required prompting.
5. Revisit only those weak sections.

### 2. Consolidation checkpoint

After approximately three or four substantial topics:

- Pause large new lessons.
- Revisit earlier concepts through mixed scenarios.
- Review one implementation for responsibility and failure handling.
- Answer interview questions without reading the notes.
- Update the weak-area list.
- Add the completed concepts to the capstone.

### 3. Phase review

At the end of Backend Engineering, System Design, and Production/Cloud:

- Run a mixed mock interview.
- Review the capstone architecture.
- Revisit weak topics.
- Connect technical decisions to leadership stories.

## Interview Answer Structure

Use this structure when it improves clarity:

1. **Decision or definition** — answer the question directly.
2. **Reason** — explain why.
3. **Example or flow** — make the idea concrete.
4. **Trade-off or failure case** — show engineering judgment.
5. **Conclusion** — restate the recommendation when needed.

Not every answer needs five sections. A simple factual question may need only the first two or three.

## Current Consolidation Checkpoint 01 — Topics 01–08

This checkpoint happens before Topic 09.

### Part A — Closed-book foundations

Answer one question at a time in chat without opening the notes:

1. Trace a product request from client URL to FastAPI response.
2. Explain method, path, query, body, headers, status, and response body as one HTTP contract.
3. Diagnose whether a failure occurred at DNS, TCP, TLS, HTTP routing, validation, or application logic.
4. Explain why HTTPS protects transport but does not protect secrets written into logs.
5. Choose between REST, GraphQL, gRPC, SSE, WebSocket, and webhook for a scenario.
6. Explain router, service, repository, and database responsibilities.
7. Explain why a timeout or retry can create duplicate work.
8. Explain why API regression tests matter during refactoring.

### Part B — Integrated request journey

Trace this single scenario:

> A mobile client sends <code>POST /products</code> over HTTPS. The load balancer terminates TLS. FastAPI validates the body, the service rejects duplicate SKUs, and the repository stores an accepted product.

Explain:

- Network and HTTP journey
- Validation boundary
- Business-rule boundary
- Storage boundary
- Successful response
- Duplicate-SKU response
- What must not be logged

### Part C — Code review

Revisit the Topic 08 application and check:

- The router contains no storage access.
- The service contains no FastAPI exceptions.
- The repository contains no HTTP decisions.
- Expected exceptions are translated at the router.
- Unexpected errors are not converted into <code>404</code>.
- API behaviour remains protected by tests.

### Part D — Weak-area record

After the checkpoint, record only items that needed help. Each weak area must have:

- The confusing question
- The corrected mental model
- One example
- A date for the next short review

## Capstone Thread

The Topic 08 layered Product API becomes the baseline for one evolving capstone system.

| Roadmap topic | Capstone evolution |
|---|---|
| Topic 08 | Router, service, repository, schemas, tests |
| Topic 09 | Replace in-memory storage with a database |
| Topic 10 | Identify blocking operations and decide where async helps |
| Topic 11 | Handle concurrent work safely |
| Topic 12 | Move suitable long-running work to a worker and queue |
| Topic 13 | Add retries, idempotency, and safe state transitions |
| Topic 14 | Add measurement, resilience, logging, and observability |
| System Design phase | Scale and redesign the same product platform |
| Cloud/Production phase | Containerize, deploy, monitor, and operate it |

New topic labs may remain isolated when needed for learning, but the important capability is later integrated into the capstone.

## Light Coding Thread

Spend 30–45 minutes each week on one focused problem.

Prefer problems connected to the current topic:

- Transform and validate collections
- Group, filter, and aggregate data
- Exception handling
- Class design
- Dependency injection
- SQL queries after Topic 09
- Async and concurrency after Topics 10–11

The goal is consistent reasoning practice, not a large daily problem count.

## Leadership Journal Thread

Spend 20–30 minutes per week recording one real example:

- Design decision
- Production incident
- Code-review disagreement
- Mentoring moment
- Risk raised early
- Trade-off communicated
- Technical debt decision
- Cross-team coordination

Use this private template:

~~~text
Situation:
What decision or problem occurred?

My responsibility:
What was I expected to own?

Options:
What alternatives were considered?

Decision:
What did I recommend or do?

Trade-off:
What did we gain and what did we accept?

Outcome:
What happened?

Learning:
What would I repeat or change?
~~~

### Privacy rule

The GitHub repository is public. Store real journal entries privately and anonymize:

- Employer and client names
- People
- Internal systems
- Credentials
- Production identifiers
- Confidential business information

Only reusable, sanitized interview narratives should eventually be added to the public roadmap.

## Planned Checkpoints

| Checkpoint | Timing | Focus |
|---|---|---|
| 01 | Now, after Topic 08 | API journey, protocols, communication choices, application layers |
| 02 | After Topic 11 | Persistence, blocking I/O, async, and concurrency |
| 03 | After Topic 14 | Complete backend engineering phase |
| 04 | Mid-system-design phase | Requirements, scaling, data, caching, messaging |
| 05 | End of system-design phase | Full design mock interview |
| 06 | Mid-production phase | Containers, CI/CD, cloud, Kubernetes |
| 07 | Before final interview synthesis | Mixed backend, design, production, and leadership review |

Checkpoint timing may move when a genuine gap needs more practice.

## Completion Rule

A topic is not considered retained merely because its notes and lab are complete.

It is considered retained when the learner can:

1. Explain the central mental model without reading.
2. Apply it to a new scenario.
3. Identify one trade-off or failure mode.
4. Connect it to the capstone.
5. Revisit it successfully during a later checkpoint.
