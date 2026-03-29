# Metadata Database — Schema & Operations

> **Module 01 · Topic 01 · Explanation 05** — Production database management for Airflow

---

## What the Metadata Database Is

The metadata database is Airflow's source of truth. Every DAG definition, every task execution, every XCom value, every connection string, every variable — persisted here. Without it, Airflow is stateless: you'd lose all history of what ran, what succeeded, and what failed the moment the process restarts.

Think of it as the **central ledger of a financial institution**. Bankers (the scheduler, workers, webserver) constantly read from and write to the ledger. The ledger records every transaction — every task that was attempted, every result, every retry. Auditors (the webserver) can look up any historical entry. Risk managers (the scheduler) check the ledger to know which transactions are pending before initiating new ones. If the ledger becomes unavailable, the entire institution freezes. If it becomes corrupted, you lose the audit trail. The ledger must be fast, reliable, and well-maintained — old entries must be regularly archived to keep the active ledger small and performant.

The most important operational reality: **the metadata database grows unboundedly if you don't clean it**. Large XCom values, old task instance rows, and historical DAG runs accumulate silently. A 500 GB metadata database with millions of rows causes scheduler queries to slow from milliseconds to minutes — which degrades the entire platform.

---

## Core Schema

```mermaid
erDiagram
    DAG ||--o{ DAG_RUN : "has many"
    DAG_RUN ||--o{ TASK_INSTANCE : "contains"
    TASK_INSTANCE ||--o{ XCOM : "produces"
    DAG ||--o{ SERIALIZED_DAG : "serialized as"

    DAG {
        string dag_id PK
        boolean is_paused
        string schedule_interval
        string owner
        timestamp last_parsed_time
    }

    DAG_RUN {
        int id PK
        string dag_id FK
        string run_id
        date logical_date
        string state
        timestamp start_date
        timestamp end_date
    }

    TASK_INSTANCE {
        string task_id PK
        string dag_id PK
        int map_index PK
        string run_id FK
        string state
        int try_number
        float duration
        timestamp start_date
    }

    XCOM {
        string key PK
        string dag_id PK
        string task_id PK
        string run_id PK
        blob value
        timestamp timestamp
    }
```

---

## Production Operations

### Database Sizing

| Scale | Rows (90-day retention) | DB Size | Recommended |
|-------|------------------------|---------|-------------|
| 50 DAGs, 10 tasks each | ~135K task instances | 1-5 GB | Small RDS |
| 500 DAGs, 20 tasks each | ~2.7M task instances | 10-50 GB | Medium RDS |
| 5,000 DAGs, 30 tasks each | ~40M task instances | 100-500 GB | Large RDS + PgBouncer |

### Maintenance Commands

```bash
# Clean old data (CRITICAL for production stability)
airflow db clean --clean-before-timestamp "2024-01-01" --yes

# Check database schema version
airflow db check

# Upgrade schema after Airflow version upgrade
airflow db migrate

# Export current connections (for migration)
airflow connections export connections.json
```

---

## Real Company Use Cases

**LinkedIn — Metadata DB Overload from XCom Abuse**

LinkedIn runs one of the largest Airflow deployments in the world for their data lake ETL, model training pipelines, and metrics computation. They ran into a metadata database performance cliff when their XCom table grew to 50 GB. The root cause: engineers were returning large Pandas DataFrames from tasks (via `return df`), which TaskFlow API automatically serialised and stored in the XCom table as blobs. A single DataFrame can be 50-500 MB. With hundreds of runs daily, the XCom table became the dominant consumer of database storage. The fix required a two-phase approach: immediate — run `airflow db clean` to purge XCom data, enforce `AIRFLOW__CORE__ALLOW_LARGE_XCOMS=False` to reject large XCom values at write time. Structural — implement a "custom XCom backend" that stores large values in S3 and saves only the S3 URI in the metadata DB. This reduced XCom table size from 50 GB to under 500 MB while maintaining the same TaskFlow API developer experience.

**Uber — PgBouncer as a Non-Negotiable at Scale**

Uber's Airflow platform runs 4,000+ DAGs for pricing, driver routing, trip analytics, and ML model scoring. Their metadata database is Aurora PostgreSQL (highly available, multi-AZ). At this DAG count, they run 20+ scheduler processes, 300+ Celery workers, and multiple webserver instances — all making concurrent SQL connections. PostgreSQL has a hard connection limit (max_connections, default: 100). Without connection pooling, new connection requests are rejected with "FATAL: remaining connection slots are reserved" — a platform-wide outage. Uber's solution is PgBouncer in transaction mode between all Airflow components and Aurora PostgreSQL. PgBouncer maintains a pool of 50 real database connections and multiplexes thousands of application requests across them. The result: Airflow components can request connections freely (PgBouncer handles queuing), and PostgreSQL never sees more than 50 concurrent connections regardless of how many Airflow processes are running.

---

## Anti-Patterns and Common Mistakes

**1. Storing large objects in XCom**

XCom values are serialised to the database. A pandas DataFrame, a large JSON response, or an image returned from a task function gets stored as a blob in the `xcom` table. This bloats the database and slows all scheduler queries.

```python
# ✗ WRONG: returning a large DataFrame via XCom
@task()
def extract_sales_data() -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM sales", connection)  # 500MB DataFrame
    return df  # Serialised into the xcom table! Database fills up quickly.

@task()
def transform_data(df: pd.DataFrame):  # 500MB read from xcom table every DAG run
    return df.groupby("region").sum()

# ✓ CORRECT: pass references (S3 paths), not data
@task()
def extract_sales_data() -> str:
    df = pd.read_sql("SELECT * FROM sales", connection)
    s3_path = f"s3://my-bucket/tmp/sales/{context['run_id']}.parquet"
    df.to_parquet(s3_path)  # Store data in S3
    return s3_path  # Pass only the reference via XCom (tiny string)

@task()
def transform_data(s3_path: str) -> str:
    df = pd.read_parquet(s3_path)  # Read from S3, not from the DB
    result_path = s3_path.replace("sales", "sales_transformed")
    df.groupby("region").sum().to_parquet(result_path)
    return result_path
```

**2. No automated database cleanup in production**

Airflow accumulates task instance rows, DAG run rows, and XCom entries indefinitely. Without automated cleanup, a 500-DAG instance running daily generates ~15,000 task instance rows per day. After 2 years, this is 10 million rows. Scheduler queries that join `task_instance` and `dag_run` go from 5ms to 5 seconds.

```python
# ✓ CORRECT: a maintenance DAG that cleans up old data automatically
from airflow.decorators import dag, task
import pendulum

@dag(
    dag_id="airflow_db_maintenance",
    schedule="0 2 * * 0",  # Weekly on Sunday at 2 AM
    start_date=pendulum.datetime(2024, 1, 1),
    catchup=False,
    tags=["platform", "maintenance"],
)
def airflow_db_maintenance():
    @task()
    def cleanup_old_data():
        from airflow.utils.db import clean
        import pendulum
        # Remove data older than 90 days
        clean(
            clean_before_timestamp=pendulum.now().subtract(days=90),
            tables=["task_instance", "dag_run", "xcom", "log"],
            dry_run=False,
        )
    cleanup_old_data()

airflow_db_maintenance()

# Also set in airflow.cfg:
# [core]
# max_db_retries = 3
```

**3. Not using PgBouncer when running CeleryExecutor with 10+ workers**

Each Celery worker opens multiple connections to the metadata DB (for state updates, XCom reads, heartbeats). At 20 workers, you hit PostgreSQL's default `max_connections=100`. New connection requests fail with a fatal error that looks like a scheduler crash: "FATAL: remaining connection slots are reserved for non-replication superuser connections".

```ini
; ✗ WRONG: Direct connection from all Airflow components to PostgreSQL
; airflow.cfg
[database]
sql_alchemy_conn = postgresql+psycopg2://airflow:pass@postgres-host:5432/airflow
; 20 workers * 4 connections each + scheduler + webserver = 90+ connections
; This approaches or exceeds max_connections=100

; ✓ CORRECT: Route through PgBouncer (transaction pooling mode)
[database]
sql_alchemy_conn = postgresql+psycopg2://airflow:pass@pgbouncer:6432/airflow
; pgbouncer.ini:
; [airflow]
; host = postgres-host
; port = 5432
; dbname = airflow
; pool_mode = transaction
; max_client_conn = 200   <- Airflow components connect here (unlimited-ish)
; default_pool_size = 20  <- Only 20 real DB connections to PostgreSQL
```

---

## Interview Q&A

### Senior Data Engineer Level

**Q: Your Airflow metadata database is running out of storage. What do you do?**

Immediate: run `airflow db clean --clean-before-timestamp $(date -d '90 days ago' +%Y-%m-%d) --yes` to purge old task instances, DAG runs, and XCom data. Diagnose: run the PostgreSQL table size query to find which tables are consuming the most space — `SELECT relname, pg_size_pretty(pg_total_relation_size(oid)) FROM pg_class WHERE relkind = 'r' ORDER BY pg_total_relation_size(oid) DESC LIMIT 10`. Typically, either `task_instance` (no cleanup policy) or `xcom` (large XCom values) is the culprit. Structural fix: (1) Deploy a maintenance DAG that runs `airflow db clean` weekly, (2) If `xcom` is large, identify which tasks return large values and implement a custom XCom backend or switch to S3 URI pattern, (3) Set `AIRFLOW__CORE__ALLOW_LARGE_XCOMS=False` to block future large XCom writes.

**Q: What happens if the metadata database becomes unavailable (e.g., planned maintenance, network partition)?**

Airflow's entire operational capacity pauses: (1) The scheduler cannot create new DAG Runs or update task states — it enters a retry loop. (2) Workers completing tasks cannot write their results (SUCCESS/FAILED state) — they also retry but may time out. (3) The webserver cannot display DAG status or task logs that come from the DB. (4) New connections from Airflow components fail immediately. When the database comes back: the scheduler resumes its loop, re-reads state from the DB, and continues from where it left off. Tasks that were RUNNING when the outage started may appear as zombies (RUNNING state with no active process) — the zombie detection mechanism resolves these within one zombie detection interval.

**Q: Why does Airflow prefer PostgreSQL over MySQL for large deployments?**

Three technical reasons: (1) `SELECT FOR UPDATE SKIP LOCKED` — used by the scheduler HA mechanism. Available in PostgreSQL since 9.5; only added to MySQL in 8.0. Many production MySQL versions are still pre-8.0. (2) Better JSONB support — Airflow stores serialised DAGs as JSON in the `serialized_dag` table. PostgreSQL's native JSONB type allows indexed queries on JSON fields; MySQL's JSON type is less performant for complex queries. (3) PgBouncer ecosystem — PgBouncer is a battle-tested, performant PostgreSQL connection pooler. MySQL's connection pooling story (ProxySQL) is more complex to operate.

### Lead / Principal Data Engineer Level

**Q: Design a metadata database architecture for a 5,000 DAG Airflow instance with 99.9% SLA.**

Four-layer architecture: (1) Compute layer: Aurora PostgreSQL in multi-AZ configuration (writer + 2 read replicas). Writer handles all scheduler/worker writes, read replicas handle webserver queries (route read traffic via `sql_alchemy_conn_cmd` with a read replica URL). Automatic failover to read replica on writer failure — Aurora completes this in under 30 seconds. (2) Connection pooling: PgBouncer in transaction mode between Airflow components and Aurora. Pool size of 50 real connections handles 500 Airflow processes at peak. (3) Performance optimisation: Aurora's auto-vacuum settings tuned for Airflow's write pattern (high insert rate, frequent updates, periodic bulk deletes from db clean). Add indices on frequently queried columns: `task_instance(dag_id, state, execution_date)`. (4) Maintenance automation: dedicated maintenance DAGs running `airflow db clean` for 90-day retention, plus weekly VACUUMs and ANALYZE on the largest tables. Monitoring: alert on table sizes exceeding thresholds and on p99 scheduler query latency exceeding 100ms.

**Q: Explain the custom XCom backend pattern and when you would implement it.**

the custom XCom backend replaces Airflow's default XCom storage (metadata DB rows) with an external store (typically S3 or GCS). When a task returns a value, instead of serialising it to the `xcom` table, Airflow writes it to S3 and stores only the S3 URI in the DB. When a downstream task reads the XCom, Airflow fetches from S3. Implementation: create a class that inherits from `BaseXCom` and overrides `serialize_value()` (writes to S3, returns URI) and `deserialize_value()` (reads from S3, deserialises). Set `AIRFLOW__CORE__XCOM_BACKEND=mypackage.xcom_backend.S3XComBackend`. When to implement: (1) when your XCom table exceeds 10 GB, (2) when tasks routinely return DataFrames or ML model outputs, (3) when you need XCom data to outlive Airflow's 90-day retention policy (S3 has its own lifecycle management). The developer experience remains identical — engineers still use `return value` and `upstream.output` in TaskFlow API.

---

## Self-Assessment Quiz

**Q1**: Explain why PgBouncer is critical at scale. What problem does it solve?
<details><summary>Answer</summary>PostgreSQL has a hard connection limit (default: 100). At scale, each Airflow scheduler, webserver instance, and worker process opens multiple connections. With 20+ workers and connection pooling disabled, you easily exceed 100 connections and receive "FATAL: too many connections" errors, freezing the entire Airflow instance. PgBouncer sits between Airflow and PostgreSQL, multiplexing many application connections over a smaller pool of real database connections. Transaction mode pooling (recommended) allows a connection to be returned to the pool at the end of each SQL transaction, enabling high connection reuse at the application level with minimal actual DB connections.</details>

**Q2**: A task uses `Variable.get("api_key")` inside a TaskFlow function. This is called 1000 times per day. What's the database impact and how do you optimise it?
<details><summary>Answer</summary>Each `Variable.get()` call executes a SQL `SELECT` query against the `variable` table. 1000 calls per day = 1000 DB roundtrips, each adding 1-5ms latency to the task and load to the scheduler's DB connection pool. Optimisation options: (1) Cache the Variable in a module-level variable inside the task: `api_key = Variable.get("api_key")` once at task startup and reuse throughout the function, (2) Use environment variables (`AIRFLOW_VAR_API_KEY=secret`) which are read from the process environment with zero DB overhead, (3) For DAG-level Variables, use `{{var.value.api_key}}` in templated fields, which batchs the Variable fetch with other context values at the start of the task.</details>

**Q3**: What's the difference between `logical_date` and `data_interval_start`? When are they the same?
<details><summary>Answer</summary>In Airflow 2.2+, `logical_date` and `data_interval_start` are always equal by design — it was a renaming/unification. In Airflow 2.1 and earlier, `execution_date` (now called `logical_date`) was the start of the data interval. The terminology changed to be more explicit: `data_interval_start` = beginning of the data window, `data_interval_end` = end of the data window, `logical_date` = same as `data_interval_start` (the DAG's logical execution reference point). The run actually happens at or after `data_interval_end`. The key point: `logical_date` is NOT the actual time the DAG ran — it's a label for the data interval being processed.</details>

### Quick Self-Rating
- [ ] I can draw the ER diagram of Airflow's core tables from memory
- [ ] I can size and architect a metadata database for a 5,000 DAG instance
- [ ] I can implement automated database maintenance with the correct retention policy
- [ ] I can explain and implement the custom XCom backend pattern
- [ ] I can configure PgBouncer for high-scale Airflow deployments

---

## Further Reading

- [Airflow Docs — Database Setup](https://airflow.apache.org/docs/apache-airflow/stable/howto/set-up-database.html)
- [Airflow Docs — Custom XCom Backends](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html#custom-xcom-backends)
- [Airflow Docs — DB Maintenance](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/scheduler.html#database-clean-up)
- [PgBouncer Documentation](https://www.pgbouncer.org/config.html)
- [Airbnb Engineering: Scaling Airflow MetaDB](https://medium.com/airbnb-engineering/airflow-at-airbnb-f4e0e375c2aa)
