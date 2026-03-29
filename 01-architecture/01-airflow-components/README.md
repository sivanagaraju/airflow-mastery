# Airflow Architecture — Components Deep Dive

> Module 01 · Topic 01 — Understanding every component that makes Airflow work

---

## Why This Matters

Understanding Airflow's architecture is the difference between *using* Airflow and *mastering* it. When tasks get stuck, when the scheduler is slow, when the UI shows stale data — knowing the architecture tells you exactly where to look.

---

## Sub-Topics

| # | File | What You'll Learn |
|---|------|-------------------|
| 01 | [Webserver](./explanation/01-webserver.md) | Flask-based UI, what it reads, caching |
| 02 | [Scheduler](./explanation/02-scheduler.md) | The DAG parsing loop, HA mode, tuning |
| 03 | [Executor](./explanation/03-executor.md) | Sequential → Local → Celery → Kubernetes |
| 04 | [Workers](./explanation/04-workers.md) | Task execution lifecycle, logging, resource limits |
| 05 | [Metadata DB](./explanation/05-metadata-db.md) | Schema, connections, maintenance, scaling |

---

## Study Path

1. Read explanations 01 → 05 in order
2. Run [`demo_component_check.py`](./demos/demo_component_check.py) — queries architecture info at runtime
3. Complete [`Ex01_ArchitectureDAG.py`](./exercises/Ex01_ArchitectureDAG.py)
4. Draw the complete architecture diagram from memory (whiteboard challenge)

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER / BROWSER                           │
│                    http://localhost:8080                          │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼───────────────────────────────────────┐
│                        WEBSERVER                                  │
│  Flask (Gunicorn) │ Reads serialized DAGs from DB │ Read-only    │
└──────────────────────────┬───────────────────────────────────────┘
                           │ SQL queries
┌──────────────────────────▼───────────────────────────────────────┐
│                      METADATA DATABASE                            │
│  PostgreSQL │ dag_run │ task_instance │ xcom │ connection │ var  │
└────────┬─────────────────────────────────────────────┬───────────┘
         │ read/write                                  │ read/write
┌────────▼─────────┐                          ┌────────▼─────────┐
│    SCHEDULER     │                          │     TRIGGERER    │
│ Parses dags/     │                          │ Async deferrable │
│ Creates DAG Runs │                          │ task monitoring  │
│ Queues tasks     │                          └──────────────────┘
└────────┬─────────┘
         │ task queue
┌────────▼─────────┐
│     EXECUTOR     │
│ (Strategy Layer) │
└────────┬─────────┘
    ┌────┼────┐
    ▼    ▼    ▼
 Worker Worker Worker
```

---

## Related

- Previous: [Module 00 — Introduction](../../00-introduction/)
- Next: [Module 02 — Installation & Setup](../../02-installation-setup/)
