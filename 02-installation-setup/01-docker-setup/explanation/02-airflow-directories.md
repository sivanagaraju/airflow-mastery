# Airflow Directories — Where Everything Lives

> **Module 02 · Topic 01 · Explanation 02** — Understanding the standard directory structure

---

## Standard Layout

```
╔══════════════════════════════════════════════════════════════╗
║  $AIRFLOW_HOME (default: /opt/airflow in Docker)            ║
║                                                              ║
║  ├── dags/                    ← Your DAG Python files       ║
║  │   ├── daily_etl.py                                       ║
║  │   ├── ml_training.py                                     ║
║  │   └── .airflowignore      ← Exclude files from parsing  ║
║  │                                                           ║
║  ├── logs/                    ← Task execution logs         ║
║  │   ├── dag_id=daily_etl/                                  ║
║  │   │   ├── run_id=scheduled__2024-03-15/                  ║
║  │   │   │   ├── task_id=extract/                           ║
║  │   │   │   │   └── attempt=1.log                          ║
║  │   │   │   └── task_id=transform/                         ║
║  │   │   │       └── attempt=1.log                          ║
║  │                                                           ║
║  ├── plugins/                 ← Custom operators & hooks    ║
║  │   ├── operators/                                         ║
║  │   │   └── custom_slack_operator.py                       ║
║  │   └── hooks/                                             ║
║  │       └── custom_api_hook.py                             ║
║  │                                                           ║
║  ├── config/                  ← Configuration overrides     ║
║  │   ├── airflow.cfg                                        ║
║  │   └── webserver_config.py                                ║
║  │                                                           ║
║  └── airflow.db               ← SQLite DB (dev only!)      ║
╚══════════════════════════════════════════════════════════════╝
```

---

## The dags/ Directory

| Rule | Why |
|------|-----|
| Every `.py` file is parsed every 30s | Keep only DAG files here |
| Use `.airflowignore` to exclude files | Pattern per line, like `.gitignore` |
| Subdirectories are parsed recursively | Organize by team or domain |
| No heavy imports at top level | Slows parsing for ALL DAGs |
| Common code in a `utils/` module | Import in tasks, not at parse time |

**.airflowignore example:**
```
__pycache__
.git
tests/
README.md
*.txt
```

---

## The logs/ Directory

Logs follow a deterministic path structure:

```
logs/
  dag_id={dag_id}/
    run_id={run_id}/
      task_id={task_id}/
        attempt={try_number}.log
```

For **production**, use remote logging:

| Storage | Config |
|---------|--------|
| S3 | `remote_logging=True`, `remote_base_log_folder=s3://my-bucket/airflow-logs` |
| GCS | `remote_base_log_folder=gs://my-bucket/airflow-logs` |
| Azure | `remote_base_log_folder=wasb://container@account.blob.core.windows.net/logs` |

---

## Interview Q&A

**Q: A data engineer adds a `helper_functions.py` utility file to the dags/ folder. What happens?**

> Airflow parses it as a potential DAG file every 30 seconds. Since it doesn't contain a DAG object, it wastes scheduler CPU. Worse, if it has expensive top-level imports (like `import pandas`), it adds latency to *every* parse cycle. Fix: Either (1) add `helper_functions.py` to `.airflowignore`, (2) move it to a separate Python package outside dags/, or (3) put it in a subdirectory and use an import instead.

---

## Self-Assessment Quiz

**Q1**: You have 50 DAG files and 30 helper Python modules in the dags/ folder. For a scheduler with `parsing_processes=2`, how many total files are parsed per cycle?
<details><summary>Answer</summary>80 files — all `.py` files in dags/ are parsed, regardless of whether they contain DAGs. Use `.airflowignore` to exclude the 30 helper files, reducing parse work by 37.5%. Or better, move helpers to a separate installed Python package with `pip install -e ./my_helpers`.</details>

### Quick Self-Rating
- [ ] I can map the standard Airflow directory structure from memory
- [ ] I can configure .airflowignore for performance
- [ ] I can set up remote logging for production
