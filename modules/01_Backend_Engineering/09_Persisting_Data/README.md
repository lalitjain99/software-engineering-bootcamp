# Topic 09 — Persisting Data

> This topic is divided into focused subtopics so each concept remains readable, practical, and independently revisable.

## Subtopics

| Status | Subtopic | Focus |
|:---:|---|---|
| 🟢 | [09.01 Database Fundamentals](01_Database_Fundamentals/Notes.md) | Persistence, relational concepts, repositories, constraints, and basic transactions |
| 🟢 | [09.02 Data Modeling and SQL](02_Data_Modeling_And_SQL/Notes.md) | Tables, keys, relationships, joins, inserts, updates, and queries |
| 🟡 | [09.03 Database Sessions and Connection Pools](03_Database_Sessions_And_Connection_Pools/Notes.md) | Sessions, connections, pooling, lifecycle, and FastAPI integration |
| ⚪ | 09.04 ORM and Migrations | Mapping Python models, migrations, schema evolution, and trade-offs |
| ⚪ | 09.05 Transactions and Concurrent Updates | Atomicity, isolation, locking, race conditions, and safe updates |
| ⚪ | 09.06 Query Performance and Optimization | Indexes, query plans, N+1 queries, pagination, and diagnosis |

## Topic workflow

Each Tier A subtopic will follow the normal learning flow:

```text
Chat explanation
    ↓
Your answer and questions
    ↓
Refined subtopic Notes.md
    ↓
Hands-on exercise
    ↓
Interview questions in chat
    ↓
Interview.md
```

The current subtopic introduces why a production application needs durable storage. Later subtopics will add SQL, database sessions, ORM usage, migrations, concurrency, and performance without making one document unnecessarily large.

## Core mental model

```text
Python memory  → temporary process state
Database       → durable shared source of truth
Repository     → storage boundary
Service        → business decisions
Router         → HTTP translation
```

## Capstone direction

The Topic 08 Product API remains the capstone baseline. Topic 09 will gradually replace its in-memory repository with durable database storage while keeping the router and service responsibilities clear.

## Revision note

Do not try to memorise all database concepts at once. Complete one subtopic, apply it, and revisit it during the weekly recall and planned consolidation checkpoints.
