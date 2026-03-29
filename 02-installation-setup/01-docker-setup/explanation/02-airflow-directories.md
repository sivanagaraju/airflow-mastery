# Airflow Directories — Where Everything Lives

> **Module 02 · Topic 01 · Explanation 02** — Understanding the standard directory structure and why it matters

---

## 🎯 The Real-World Analogy: A City Hall Building

Think of `$AIRFLOW_HOME` as a **city hall building** with specialized departments:

| Directory | City Hall Department | Responsibility |
|-----------|---------------------|----------------|
| `dags/` | **Legislative chamber** | Where laws (DAGs) are written and stored |
| `logs/` | **Court records archive** | Every decision and action, permanently logged |
| `plugins/` | **City engineering dept.** | Custom tools and extensions built for this city |
| `config/` | **Mayor's policy office** | Overrides the default rules of how things run |
| `airflow.db` | **The vault** (dev only) | Quick SQLite storage for solo development |

Just as city hall departments follow strict naming conventions for filing (case number, date, department), Airflow's `logs/` directory follows a deterministic path structure you can always predict.

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
║  │   │   ├── run_id=scheduled__2024-03-15T00:00:00+00:00/  ║
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

| Rule | Why It Matters |
|------|----------------|
| Every `.py` file is parsed every 30s | Keep ONLY DAG files here — helpers slow down scheduler |
| Use `.airflowignore` to exclude files | Pattern per line, same syntax as `.gitignore` |
| Subdirectories are parsed recursively | Organize by team or domain (`/finance/`, `/marketing/`) |
| No heavy imports at top level | Pandas `import` at parse time slows ALL DAGs |
| Common code in a separate package | Install with `pip install -e ./my_utils` instead |

**.airflowignore example:**

```
__pycache__
.git
tests/
README.md
*.txt
helpers/
utils/
```

---

## The logs/ Directory

Logs follow a **deterministic, predictable** path structure that never changes:

```
logs/
  dag_id={dag_id}/
    run_id={run_id}/
      task_id={task_id}/
        attempt={try_number}.log
```

This means you can always find any log with:

```bash
# Find logs for a specific task attempt
ls /opt/airflow/logs/dag_id=daily_etl/run_id=scheduled__2024-01-15T00:00:00+00:00/task_id=extract/attempt=1.log
```

For **production**, configure remote logging to avoid disk filling:

| Cloud Storage | Config Key | Example Value |
|---------------|------------|---------------|
| AWS S3 | `remote_base_log_folder` | `s3://company-airflow-logs/` |
| Google GCS | `remote_base_log_folder` | `gs://company-airflow-logs/` |
| Azure Blob | `remote_base_log_folder` | `wasb://container@account.blob.core.windows.net/logs` |

---

## The plugins/ Directory

```python
# plugins/operators/snowflake_bulk_operator.py
from airflow.models import BaseOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

class SnowflakeBulkLoadOperator(BaseOperator):
    """Custom operator for company-specific bulk loading pattern."""
    
    def __init__(self, table: str, s3_path: str, **kwargs):
        super().__init__(**kwargs)
        self.table = table
        self.s3_path = s3_path
    
    def execute(self, context):
        hook = SnowflakeHook(snowflake_conn_id='snowflake_default')
        hook.run(f"COPY INTO {self.table} FROM '{self.s3_path}'")
        self.log.info(f"Loaded {self.table} from {self.s3_path}")
```

> **Plugin auto-discovery**: Airflow automatically imports any Python files in `plugins/operators/` and `plugins/hooks/`. No registration required.

---

## 🏢 Real Company Use Cases

**Astronomer** (the managed Airflow company) mandates a specific directory convention for all their enterprise customers: `dags/` organized by team subdirectory, `plugins/` as a formal Python package with `__init__.py` and version pinning, and `logs/` always pointed at cloud storage from day one. This prevents the "log disk full" production outage that hits teams who start with local logs.

**ING Bank** (Netherlands) runs Airflow across 40+ data teams. Their standard: every team has a `dags/<team-name>/` subdirectory, and a corresponding `.airflowignore` maintains a whitelist (not blacklist) approach — only explicitly listed paths are parsed. This reduced scheduler parse time by 70% as the number of non-DAG Python files in their monorepo grew.

**Saxo Bank** (Denmark) uses the `plugins/` directory exclusively for compliance-related operators — data masking, encryption, audit logging. Every DAG is forbidden from importing these directly; they must use the registered operators. This creates a compliance boundary enforced at the Airflow architecture level.

---

## ❌ Anti-Patterns

### Anti-Pattern 1: Putting Helper Utilities Directly in dags/

```python
# dags/helpers/data_utils.py  ← ❌ BAD: Scheduler parses this every 30s
import pandas as pd           # This import runs 2x per minute for the whole cluster!
import numpy as np            # pandas import alone takes 0.3-0.5 seconds

def clean_dataframe(df):
    return df.dropna()
```

```
# ✅ GOOD: Add to .airflowignore OR move outside dags/
# Option 1: .airflowignore
helpers/

# Option 2: Install as a package
# my_utils/setup.py → pip install -e ./my_utils
# Then in your DAG: from my_utils.data_utils import clean_dataframe
```

---

### Anti-Pattern 2: Using Local Logs in Production (Disk Fill Incident)

```python
# ❌ BAD: Default local logs in airflow.cfg
[logging]
base_log_folder = /opt/airflow/logs
remote_logging = False
```

**What happens at scale**: 1,000 DAG runs/day × 10 tasks × average log size 50KB = **500MB/day**. After 60 days: 30GB disk full. Airflow stops logging, then starts failing task execution as the worker can't write stdout.

```python
# ✅ GOOD: Enable remote logging from day one
# In docker-compose.yml environment or airflow.cfg:
AIRFLOW__LOGGING__REMOTE_LOGGING=True
AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER=s3://company-airflow-logs/
AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID=aws_default
# Keep only 7 days of local logs as fallback
AIRFLOW__LOGGING__LOG_FILE_TASK_HANDLER_NEW_FOLDER=True
```

---

### Anti-Pattern 3: Putting Custom Operators in dags/ Instead of plugins/

```python
# dags/my_dag.py  ← ❌ BAD: Custom operator defined inside DAG file
class MyCustomOperator(BaseOperator):
    # This operator is only available to this one DAG file
    # Can't be reused without copy-pasting
    def execute(self, context):
        pass

@dag
def my_pipeline():
    task = MyCustomOperator(task_id='do_thing')
```

```python
# plugins/operators/my_custom_operator.py  ← ✅ GOOD: Auto-discovered by Airflow
class MyCustomOperator(BaseOperator):
    def execute(self, context):
        pass

# dags/my_dag.py — import from plugins
from operators.my_custom_operator import MyCustomOperator
```

---

## 🎤 Senior-Level Interview Q&A

**Q1: A data engineer adds a `helper_functions.py` utility file to the dags/ folder. What happens, and what's the fix?**

> Airflow's scheduler parses every `.py` file in `dags/` every `min_file_process_interval` seconds (default 30s). `helper_functions.py` gets parsed 2 times per minute. If it has top-level imports like `import pandas`, that import runs on every parse cycle across every scheduler process. For a cluster with `parsing_processes=4`, that's 4 pandas imports every 30 seconds — pure wasted CPU. Fix options: (1) Add `helpers.py` to `.airflowignore`. (2) Move it to a separate Python package installed via `pip install -e ./my_helpers`. (3) Move it to `plugins/` and import it as `from my_helpers import helper_functions`.

**Q2: You have 50 DAG files and 30 helper Python modules in the dags/ folder. How does this affect scheduler performance and how do you fix it?**

> All 80 `.py` files are parsed every parse cycle. With `parsing_processes=2`, that's 80 files × 2 processes = 160 file opens per cycle. The 30 helper files contribute zero DAGs but consume ~37.5% of parse budget. Fix: Add the 30 helper files to `.airflowignore`. Immediate improvement: parse budget drops by 37.5%, DAG update latency decreases. Better fix: migrate helpers to a pip-installed package. Verify with `airflow dags list-import-errors` and watch `airflow_dag_processing_total_parse_time` Prometheus metric drop.

**Q3: In production, logs from 3 days ago are missing from the Airflow UI. How do you investigate?**

> Check the logging configuration chain: (1) Is `AIRFLOW__LOGGING__REMOTE_LOGGING=True`? If yes, the UI tries to fetch from remote storage. (2) `airflow config get-value logging remote_base_log_folder` — verify the S3/GCS path. (3) Check if the connection credential (`remote_log_conn_id`) is still valid — credentials expire. (4) Check if the remote storage bucket has lifecycle rules that delete logs after N days. (5) If remote logging is on, logs are still written locally but are eventually deleted by `log_processor_manager_log_retention_days`. The UI prefers remote — if remote fetch fails, sometimes it silently shows "no logs" instead of falling back to local.

---

## 🏛️ Principal-Level Interview Q&A

**Q1: Design the directory structure for 50 data teams sharing a single Airflow cluster. What conventions would you mandate?**

> **Convention 1 — Namespace by team**: `dags/<team-name>/` with a `.airflowignore` allowlist (`!finance/`, `!marketing/`). **Convention 2 — DAG ID prefix**: All DAGs in `finance/` must have `dag_id` starting with `finance_` to make the UI filterable. **Convention 3 — Shared utilities as versioned packages**: No shared code in `dags/`. Instead, `my-company-airflow-utils` pip package published to internal PyPI. **Convention 4 — Operator versioning**: `plugins/` organized as `plugins/v1/operators/` and `plugins/v2/operators/` to allow gradual migration. **Convention 5 — Remote logging from day one**: `logs/` directory always pointing to S3 with team-specific prefixes (`s3://airflow-logs/<team-name>/`). Scale enforcement: CI/CD pipeline validates DAG ID prefix and rejects PRs that violate namespace rules.

**Q2: The scheduler's DAG parse time is increasing weekly as the repository grows. At what point does it become a problem and what's the architectural solution?**

> Watch the `airflow_dag_processing_import_errors` and `airflow_dag_processing_total_parse_time` metrics. Problem threshold: when parse time exceeds `min_file_process_interval` (default 30s), some DAGs are parsed less frequently than the schedule interval — schedule drift occurs. **Short-term solutions**: (1) Increase `parsing_processes`. (2) Aggressive `.airflowignore` on non-DAG files. (3) Increase `min_file_process_interval` to reduce parse frequency. **Medium-term**: Migrate from git-sync + shared filesystem to **DAG serialization** — DAGs are serialized to the metadata DB and the scheduler only parses files that changed (git diff). **Long-term**: Multi-scheduler HA (`scheduler_heartbeat_sec` optimization) where multiple schedulers split the DAG file list. Airflow 2.x supports multiple scheduler replicas natively.

**Q3: How would you design the plugins/ directory to support 10 data engineering teams contributing operators with different release cadences?**

> Treat `plugins/` as a **versioned internal library** with a formal release process. Structure: `plugins/v1/operators/` (stable, no breaking changes), `plugins/v2/operators/` (next gen, opt-in). Each subdirectory has its own `CHANGELOG.md`, `README.md`, and version file. **Contribution process**: Teams submit PRs to the plugins repo (separate from dags repo). An operator review board (2 principal engineers) approves. CI runs operator unit tests, integration tests against a minimal Airflow environment. **Dependency management**: Each operator declares its pip dependencies in a `requirements.txt` inside its directory. A build script aggregates and deduplicates before installing into the custom Docker image. This prevents teams from adding conflicting dependencies. **Deprecation**: Operators in `v1/` get 90-day deprecation windows with `warnings.warn()` in `execute()` before removal.

---

## 📝 Self-Assessment Quiz

**Q1**: You have 50 DAG files and 30 helper Python modules in the dags/ folder. For a scheduler with `parsing_processes=2`, how many total file-parse operations happen per 30-second cycle?
<details><summary>Answer</summary>
160 operations (80 files × 2 processes). All `.py` files are parsed regardless of whether they contain DAGs. Use `.airflowignore` to exclude the 30 helper files, immediately reducing parse operations to 100 (50 files × 2 processes) — a 37.5% improvement. Better long-term: move helpers to an installed Python package, reducing dags/ to only true DAG files.
</details>

**Q2**: A production Airflow task fails and you need to find the log file on the filesystem. The dag_id is `etl_pipeline`, run_id is `scheduled__2024-01-15T00:00:00+00:00`, task_id is `transform`, and this was the second attempt. What is the exact log path?
<details><summary>Answer</summary>
`$AIRFLOW_HOME/logs/dag_id=etl_pipeline/run_id=scheduled__2024-01-15T00:00:00+00:00/task_id=transform/attempt=2.log`

Note: attempt numbers are 1-indexed, so the second attempt is `attempt=2.log`. In Docker, `$AIRFLOW_HOME` defaults to `/opt/airflow`.
</details>

**Q3**: What is the difference between putting a custom operator in `dags/my_dag.py` vs `plugins/operators/my_operator.py`?
<details><summary>Answer</summary>
**In dags/my_dag.py**: The operator is parsed on every scheduler parse cycle but is only accessible to that one DAG file. Cannot be reused without copy-pasting. Not a real Python module — harder to unit test. **In plugins/operators/**: Auto-discovered by Airflow at startup, importable by any DAG as `from operators.my_operator import MyOperator`. Can have its own unit tests, its own `requirements.txt` listing dependencies, and its own versioning. Always prefer plugins/ for operators intended for team-wide use.
</details>

**Q4**: Why should you never use SQLite (the default `airflow.db`) in production?
<details><summary>Answer</summary>
SQLite has no concurrent write support — only one writer at a time. With multiple Airflow processes (scheduler, webserver, workers) all writing to the metadata DB simultaneously, SQLite's file locking creates: (1) Deadlocks and "database is locked" errors. (2) Corrupted database under concurrent writes. (3) No high availability — single file, no replication. (4) Slow at scale — SQLite performance degrades significantly beyond a few hundred thousand rows. Always use PostgreSQL (recommended) or MySQL for anything beyond a single-developer local setup.
</details>

### Quick Self-Rating
- [ ] I can map the Airflow directory structure from memory
- [ ] I can configure `.airflowignore` to optimize scheduling performance
- [ ] I understand the deterministic log path structure
- [ ] I know when to use `plugins/` vs a separate pip package
- [ ] I can configure remote logging for production

---

## 📚 Further Reading

- [Airflow Best Practices — DAG Writing](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) — Official guidance on dags/ organization
- [Airflow Logging Configuration](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/logging-tasks.html) — Remote logging setup
- [Airflow Plugins Documentation](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/plugins.html) — How plugin discovery works
- [DAG Serialization](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-serialization.html) — Scaling parse performance at large repositories
