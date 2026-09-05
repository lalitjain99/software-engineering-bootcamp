# Software Engineering Bootcamp

> Move from building features to making sound engineering decisions.

A focused, first-principles roadmap for an experienced IT professional building deeper backend, architecture, production, and technical-lead capability.

## 👤 Starting Point

- Close to 10 years of overall IT experience
- 1–2 years of hands-on Python backend experience
- Comfortable with Python variables, data types, classes, exceptions, modules, packages, and APIs
- Experience building enterprise applications with FastAPI
- Goal: become interview-ready for Technical Lead and Senior Technical Lead roles

This is therefore **not a beginner Python course**. Familiar concepts will be audited and compressed; the time will go into design reasoning, production engineering, and leadership-level trade-offs.

## 🎯 Priority Order

1. Backend engineering depth
2. System design
3. DevOps, cloud, and production engineering
4. Leadership and interview narrative

## ⏱️ Timebox

- **Weekly commitment:** 5–8 hours
- **Target window:** 6–12 months
- **Core plan:** approximately 36 weeks (9 months), with room to accelerate or pause

## 🧭 Learning Method

Each new concept follows a connected engineering story:

**Problem → Simple Solution → Limitations → Design Alternatives → Trade-offs → Implementation → Production Failure Modes → Interview Explanation**

Material should be concise, visually engaging, non-repetitive, and proportional to the topic.

## 📦 Deliverable Tiers

Not every topic deserves the same documentation.

| Tier | When to use | Deliverables |
|---|---|---|
| **A** | A real knowledge or experience gap | `Notes.md`, `Interview.md` with common mistakes, and hands-on code |
| **B** | Familiar but rusty | `CheatSheet.md` and `Common_Mistakes.md` |
| **C** | Already solid | Checklist confirmation only; revisit before mock interviews |

The tier is assigned through [Skills_Audit.md](Skills_Audit.md) and can change as understanding improves.

## 🔄 Continuous Weekly Threads

These run alongside every phase instead of waiting until the end:

- **Leadership and behavioral journal:** 20–30 minutes/week
- **Light coding practice:** 30–45 minutes/week
- **Evolving capstone:** add one production layer during each phase

See [Continuous_Threads/README.md](Continuous_Threads/README.md) and [Capstone/README.md](Capstone/README.md).

## 🗺️ Roadmap

| Phase | Focus | Indicative window |
|---|---|---:|
| 0 | Skills audit and setup | Week 0–1 |
| 1 | Backend engineering depth | Weeks 1–14 |
| 2 | System design | Weeks 15–24 |
| 3 | DevOps, cloud, and production | Weeks 25–32 |
| 4 | Leadership and interview synthesis | Weeks 33–36 |

See [MASTER_INDEX.md](MASTER_INDEX.md) for the detailed sequence.

## 📁 Repository Structure

```text
software-engineering-bootcamp/
├── README.md
├── pyproject.toml
├── uv.lock
├── .gitignore
├── MASTER_INDEX.md
├── Skills_Audit.md
├── Progress_Tracker.md
├── CHANGELOG.md
├── Continuous_Threads/
│   └── README.md
├── Capstone/
│   └── README.md
└── modules/
    └── ... topic folders created after tier assignment
```

## 🛠️ Shared Python Environment

Python hands-on exercises use one environment managed from the repository root.

```bash
uv sync
```

Run each exercise with `uv run` from the root, using the command documented in that exercise's `README.md`. Add dependencies to the root `pyproject.toml`; do not create a separate environment for every topic.

## 🚦 Current Status

🟡 **Skills audit and roadmap validation**

## 👤 Maintainer

[Lalit Jain](https://github.com/lalitjain99)
