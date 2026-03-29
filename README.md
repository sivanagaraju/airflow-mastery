# 🌊 Apache Airflow Mastery

> **From Zero to Principal Data Engineer** — A deep-practitioner learning path covering Apache Airflow from fundamentals to production-grade pipeline architecture.

```
╔══════════════════════════════════════════════════════════════╗
║                    AIRFLOW MASTERY                          ║
║                                                              ║
║   26 Modules · 120+ Demo DAGs · 25+ Exercises               ║
║   4 Real-World Projects · Interview Prep                     ║
║                                                              ║
║   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   ║
║   │ Explain  │→ │  Demo    │→ │ Exercise │→ │ Project  │   ║
║   │   .md    │  │   .py    │  │   .py    │  │  DAGs    │   ║
║   └──────────┘  └──────────┘  └──────────┘  └──────────┘   ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 📚 Module Index

| # | Module | Topics | Level |
|---|--------|--------|-------|
| 00 | [Introduction](./00-introduction/) | What is Airflow, basic terminologies | 🟢 Beginner |
| 01 | [Architecture](./01-architecture/) | Components, task lifecycle, state machine | 🟢 Beginner |
| 02 | [Installation & Setup](./02-installation-setup/) | Docker, pip, config files, Dockerfile | 🟢 Beginner |
| 03 | [UI & CLI](./03-airflow-ui-cli/) | All views (Tree/Graph/Gantt), CLI commands | 🟢 Beginner |
| 04 | [DAGs Fundamentals](./04-dags-fundamentals/) | DAG structure, TaskFlow API, decorators | 🟢 Beginner |
| 05 | [Operators In-Depth](./05-operators-in-depth/) | Python, Bash, DB, HTTP, providers | 🟡 Intermediate |
| 06 | [Scheduling Deep Dive](./06-scheduling-deep-dive/) | Cron, backfill, timetables, assets | 🟡 Intermediate |
| 07 | [XComs, Variables, Connections](./07-xcoms-variables-connections/) | Data passing, config, secrets | 🟡 Intermediate |
| 08 | [Executors](./08-executors/) | Sequential, Local, Celery, Kubernetes | 🟡 Intermediate |
| 09 | [Hooks & Sensors](./09-hooks-sensors/) | Built-in hooks, file/HTTP/external sensors | 🟡 Intermediate |
| 10 | [Branching & Conditional Logic](./10-branching-conditional-logic/) | BranchPythonOperator, ShortCircuit | 🟡 Intermediate |
| 11 | [Task Dependencies & Trigger Rules](./11-task-dependencies-trigger-rules/) | Trigger rules, depends_on_past | 🟡 Intermediate |
| 12 | [Pools, Priority & Concurrency](./12-pools-priority-concurrency/) | Pools, parallelism config | 🟡 Intermediate |
| 13 | [SLA, Retries & Callbacks](./13-sla-retries-callbacks-notifications/) | SLAs, retry strategies, alerting | 🟡 Intermediate |
| 14 | [Task Groups & Dynamic Tasks](./14-task-groups-dynamic-tasks/) | TaskGroup, expand/map | 🔴 Advanced |
| 15 | [DAG Dependencies & Cross-DAG](./15-dag-dependencies-cross-dag/) | SubDAGs, TriggerDagRun, ExternalTaskSensor | 🔴 Advanced |
| 16 | [Macros & Jinja Templating](./16-macros-jinja-templating/) | Template variables, custom macros | 🔴 Advanced |
| 17 | [Plugins & Custom Components](./17-plugins-custom-components/) | Custom operators, sensors, hooks | 🔴 Advanced |
| 18 | [Testing DAGs](./18-testing-dags/) | pytest, DAG integrity, CI/CD | 🔴 Advanced |
| 19 | [Monitoring & Observability](./19-monitoring-logging-observability/) | StatsD, Prometheus, Grafana | 🔴 Advanced |
| 20 | [Security & RBAC](./20-security-rbac/) | Fernet, LDAP, Vault, RBAC | 🔴 Advanced |
| 21 | [Containers & Cloud](./21-containers-cloud/) | DockerOperator, K8sPodOperator, MWAA | 🔴 Advanced |
| 22 | [Airflow 3 Features](./22-airflow-3-features/) | Assets, AI integration, event-driven | 🔴 Advanced |
| 23 | [Production Best Practices](./23-production-best-practices/) | airflow.cfg, zombies, migration guide | 🔴 Advanced |
| 24 | [Real-World Projects](./24-real-world-projects/) | Medallion, Flight Data, NYC Taxi | 🏗️ Project |
| 25 | [Interview Preparation](./25-interview-preparation/) | Q&A for Principal/Lead/Senior DE | 📝 Interview |

---

## 🗂️ File Types in Every Module

Each learning module follows a consistent structure:

| File Type | Purpose | Format |
|-----------|---------|--------|
| `README.md` | Module overview, study path, sub-topic index | Markdown |
| `MINDMAP.md` | Visual concept map (VS Code Markmap extension) | markmap |
| `explanation/*.md` | Deep-dive explanations with Mermaid diagrams, ASCII art, code snippets, interview Q&A, self-assessment quizzes | Markdown |
| `demos/*.py` | Runnable DAG files demonstrating concepts | Python (Airflow 2.x+) |
| `exercises/*.py` | Hands-on coding challenges | Python |
| `exercises/solutions/*.py` | Complete solutions | Python |
| `use-cases/*.md` | Real company use cases (Airbnb, Uber, etc.) | Markdown |
| `mini-project/` | Integrative challenge combining multiple concepts | Full DAG project |

---

## 🎯 Learning Path

```
┌─────────────────────────────────────────────────────────┐
│                    LEARNING PATH                         │
├──────────────┬──────────────┬───────────────────────────┤
│  PHASE 1     │  PHASE 2     │  PHASE 3                  │
│  Foundation  │  Core Skills │  Production Mastery       │
│  Module 00-04│  Module 05-13│  Module 14-25             │
│              │              │                           │
│  ┌────────┐  │  ┌────────┐  │  ┌────────┐  ┌────────┐  │
│  │Mini    │  │  │Mini    │  │  │Mini    │  │Real    │  │
│  │Project │  │  │Project │  │  │Project │  │World   │  │
│  │  01    │  │  │ 02-03  │  │  │  04    │  │Projects│  │
│  └────────┘  │  └────────┘  │  └────────┘  └────────┘  │
└──────────────┴──────────────┴───────────────────────────┘
```

### Phase 1 — Foundation (Modules 00-04)
Start here. Understand what Airflow is, how it works architecturally, set up your environment, and write your first DAGs.

### Phase 2 — Core Skills (Modules 05-13)
Master operators, scheduling, XComs, executors, hooks, sensors, branching, trigger rules, pools, and error handling.

### Phase 3 — Production Mastery (Modules 14-25)
Advanced patterns: dynamic tasks, cross-DAG dependencies, macros, custom plugins, testing, monitoring, security, cloud deployment, and real-world projects.

---

## 🔧 Prerequisites

- **Python 3.9+** installed
- **Docker Desktop** (recommended for Airflow setup)
- **VS Code** with extensions:
  - Markmap (for MINDMAP.md files)
  - Python
  - Markdown All in One

---

## 📊 Progress Tracking

See [PROGRESS_TRACKER.md](./PROGRESS_TRACKER.md) for a per-module checklist.

---

## ⚙️ API Standards

All code uses **modern Airflow 2.x+ API**. No deprecated imports:

| Deprecated | Modern |
|------------|--------|
| `from airflow.operators.python_operator import ...` | `from airflow.operators.python import ...` |
| `DummyOperator` | `EmptyOperator` |
| `airflow.utils.dates.days_ago(2)` | `pendulum.today('UTC').add(days=-2)` |
| `provide_context=True` | Not needed (always available in 2.x) |
