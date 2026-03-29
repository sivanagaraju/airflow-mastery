# Basic Airflow Terminologies

> Module 00 · Topic 02 — Master the vocabulary before writing code

---

## Why This Matters

Every Airflow concept builds on core terminology. If you confuse "DAG Run" with "Task Instance" or "Operator" with "Task," you'll struggle with debugging and design decisions.

---

## Sub-Topics

| # | File | What You'll Learn |
|---|------|-------------------|
| 01 | [DAG, Task, Operator](./explanation/01-dag-task-operator.md) | The three pillars of Airflow's data model |
| 02 | [Scheduler, Executor, Worker](./explanation/02-scheduler-executor-worker.md) | The three components that run your tasks |
| 03 | [Metadata Database](./explanation/03-metadata-database.md) | Where all state lives — the source of truth |

---

## Study Path

1. Read explanations 01 → 03 in order
2. Run [`demo_basic_concepts.py`](./demos/demo_basic_concepts.py)
3. Complete [`Ex01_IdentifyComponents.py`](./exercises/Ex01_IdentifyComponents.py)
4. Quiz yourself: can you draw the full Airflow architecture from memory?

---

## Related

- Next: [Module 01 — Architecture](../../01-architecture/) goes deeper into each component
- Demo: [`demo_basic_concepts.py`](./demos/demo_basic_concepts.py) shows all concepts in action
