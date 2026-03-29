# DAG Commands — The Essential CLI Operations

> **Module 03 · Topic 02 · Explanation 01** — Control DAGs from the terminal with precision

---

## 🎯 The Real-World Analogy: Air Traffic Control Radio

The Airflow CLI for DAGs is like **an air traffic controller's radio commands**:

| CLI Command | ATC Equivalent |
|-------------|---------------|
| `airflow dags list` | "Tower, confirm all aircraft on roster for today" |
| `airflow dags trigger` | "Flight 447, cleared for takeoff" |
| `airflow dags pause` | "All traffic hold — runway maintenance in progress" |
| `airflow dags unpause` | "Runway clear — normal operations resumed" |
| `airflow dags backfill` | "Reroute all flights from the past 5 hours via new corridor" |
| `airflow dags test` | "Flight simulator run — same route, no passengers" |
| `airflow dags delete` | "Remove flight 447 from the flight plan manifest" |

The ATC doesn't fly the planes — they manage the schedule. CLI commands are your direct line to the Airflow scheduler without opening a browser.

---

## Complete Command Reference

```bash
# ══════════════════════════════════════════════════════════════
# LIST & INSPECT
# ══════════════════════════════════════════════════════════════
airflow dags list                          # All DAGs with status (paused/active)
airflow dags list -o table                 # Table format (cleaner output)
airflow dags list | grep -v paused         # Only active DAGs

airflow dags show <dag_id>                 # Print DAG structure (ASCII graph)
airflow dags show <dag_id> --imgcat        # Visual graph (if imgcat installed)
airflow dags report                        # Parse time per DAG file (perf check)

airflow dags list-import-errors            # DAGs with syntax/import errors
airflow dags list-runs <dag_id>            # Recent DAG runs for a specific DAG

# ══════════════════════════════════════════════════════════════
# TRIGGER & CONTROL
# ══════════════════════════════════════════════════════════════
airflow dags trigger <dag_id>                # Start a new DAG Run (manual)
airflow dags trigger <dag_id> \
    --conf '{"env": "staging", "date": "2024-03-15"}'   # With config dict
airflow dags trigger <dag_id> \
    --run-id "manual_rerun_20240315"         # With custom run ID

airflow dags pause <dag_id>                  # Stop scheduling (runs in progress continue)
airflow dags unpause <dag_id>               # Resume scheduling

# ══════════════════════════════════════════════════════════════
# TEST — Dry-run, NO DB writes, SAFE for development
# ══════════════════════════════════════════════════════════════
airflow dags test <dag_id> 2024-03-15       # Run entire DAG for a date (no executor)
# Output goes to stdout — instant feedback
# Task states NOT recorded in metadata DB

# ══════════════════════════════════════════════════════════════
# BACKFILL — Creates REAL DAG Runs in the metadata DB
# ══════════════════════════════════════════════════════════════
airflow dags backfill \
    -s 2024-01-01 \
    -e 2024-03-15 \
    --reset-dagruns \
    --max-active-runs 5 \
    <dag_id>
# --reset-dagruns: clears existing failed/skipped runs for those dates
# --max-active-runs: limits concurrent backfill runs (avoid overloading)

# ══════════════════════════════════════════════════════════════
# DELETE — Removes metadata only (not the Python file)
# ══════════════════════════════════════════════════════════════
airflow dags delete <dag_id>               # Removes from DB; file still exists
```

---

## `dags test` vs `dags trigger` vs `dags backfill`

```
╔══════════════════════════════════════════════════════════════╗
║  COMMAND COMPARISON                                          ║
║                                                              ║
║  Command        │ DB writes │ Creates run │ Use case        ║
║  ───────────────┼───────────┼─────────────┼───────────────  ║
║  dags test      │ NO        │ NO          │ Development/dev ║
║  dags trigger   │ YES       │ YES (1)     │ Manual one-time ║
║  dags backfill  │ YES       │ YES (many)  │ Historical fill ║
╚══════════════════════════════════════════════════════════════╝
```

| Command | Writes to DB? | Creates DAG Run? | Executor Used? | Use Case |
|---------|:---:|:---:|:---:|----|
| `dags test` | No | No | No | Dev: verify logic locally |
| `dags trigger` | Yes | Yes (1) | Yes | Manual one-time execution |
| `dags backfill` | Yes | Yes (many) | Yes | Reprocess historical date range |

---

## Python Integration: REST API Equivalent

```python
import requests
from datetime import datetime, timedelta

AIRFLOW_URL = "http://localhost:8080/api/v1"
AUTH = ("admin", "admin")

def trigger_dag(dag_id: str, conf: dict = None, run_id: str = None) -> dict:
    """Equivalent to: airflow dags trigger <dag_id> --conf '...'"""
    payload = {
        "dag_run_id": run_id or f"api_trigger_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "conf": conf or {},
    }
    resp = requests.post(
        f"{AIRFLOW_URL}/dags/{dag_id}/dagRuns",
        json=payload,
        auth=AUTH
    )
    resp.raise_for_status()
    return resp.json()

def pause_dag(dag_id: str, paused: bool = True) -> dict:
    """Equivalent to: airflow dags pause/unpause <dag_id>"""
    resp = requests.patch(
        f"{AIRFLOW_URL}/dags/{dag_id}",
        json={"is_paused": paused},
        auth=AUTH
    )
    return resp.json()

def list_dag_runs(dag_id: str, state: str = None, limit: int = 10) -> list:
    """Equivalent to: airflow dags list-runs <dag_id>"""
    params = {"limit": limit}
    if state:
        params["state"] = state
    resp = requests.get(
        f"{AIRFLOW_URL}/dags/{dag_id}/dagRuns",
        params=params,
        auth=AUTH
    )
    return resp.json()["dag_runs"]

# Usage:
run = trigger_dag("sales_etl", conf={"env": "staging", "force": True})
print(f"Triggered run: {run['dag_run_id']}, state: {run['state']}")

pause_dag("legacy_pipeline", paused=True)
runs = list_dag_runs("sales_etl", state="failed", limit=5)
```

---

## 🏢 Real Company Use Cases

**LinkedIn** uses `airflow dags backfill` as a standard recovery procedure after upstream data source outages. Their runbook for any data source unavailability longer than 1 day includes: (1) Wait for source to recover. (2) `airflow dags backfill -s {outage_start} -e {recovery_date} --reset-dagruns --max-active-runs 3 {dag_id}`. The `--max-active-runs 3` limit prevents the backfill from overwhelming the data source with 7 days of concurrent runs. This procedure has been used 15+ times and is fully automated via a Slack slash command.

**Airbnb** uses `airflow dags list-import-errors` in their CI/CD pipeline. After deploying new DAG files, a post-deployment script runs this command and fails the deployment if any import errors are detected. This prevents the common scenario where a DAG with a syntax error is deployed silently and only discovered when it's missing from the UI. Their CI pipeline runs this command within 60 seconds of deployment and creates an immediate rollback if errors are found.

**Klarna** uses `airflow dags trigger` via the REST API as part of their event-driven architecture. When a large payment batch finishes processing in their core system, it publishes an event to Kafka. A Kafka consumer service calls the Airflow REST API to trigger the `payments_etl` DAG with the batch metadata as `conf`. This event-driven trigger pattern means the ETL runs minutes after the source data is ready, not hours after on a fixed schedule.

---

## ❌ Anti-Patterns

### Anti-Pattern 1: Using `dags backfill` Without `--reset-dagruns` on Failed Runs

```bash
# ❌ BAD: Backfilling dates that already have FAILED DAG Runs
airflow dags backfill -s 2024-01-01 -e 2024-01-07 my_dag

# What happens:
# Dates 2024-01-01 through 2024-01-07 already have DAG Runs in "failed" state
# backfill (without --reset-dagruns) SKIPS dates that already have runs
# → No new runs created
# → No error shown — just silently does nothing
# → Engineer thinks the backfill ran but nothing was reprocessed
```

```bash
# ✅ GOOD: Always use --reset-dagruns when reprocessing historical failures
airflow dags backfill \
    -s 2024-01-01 \
    -e 2024-01-07 \
    --reset-dagruns \        # Clears failed runs so they can be re-created
    --max-active-runs 3 \    # Don't run all 7 days simultaneously
    my_dag
```

---

### Anti-Pattern 2: Using `dags test` and Expecting It to Trigger Real Downstream Effects

```bash
# ❌ BAD ASSUMPTION: "I ran dags test, so the data was written to the DB"
airflow dags test my_etl_dag 2024-03-15
# Output shows: "Task succeeded! Rows processed: 5,000"
# Engineer assumes 5,000 rows were written to the production DB

# REALITY:
# dags test does NOT write task state to the metadata DB
# The task MAY write to external systems (Postgres, S3) if the code does so
# But the DAG Run itself doesn't exist in the DB
# If the task has conn.execute("INSERT INTO..."), THAT insert DID happen
# If the task does xcom_push(), that XCom is NOT stored (no DB write)
```

```bash
# ✅ UNDERSTANDING: Use dags test ONLY for logic verification
# "Does the code run without errors for this date?"
# NOT for "Did the pipeline produce output?"
# For actual output verification: use dags trigger and check the results
```

---

### Anti-Pattern 3: Triggering a DAG Without Checking If It's Already Running

```bash
# ❌ BAD: Triggering a DAG that's already running → duplicate processing
airflow dags trigger sales_etl  # Run 1 started
# 30 seconds later...
airflow dags trigger sales_etl  # Run 2 started — parallel!
# Both runs may write to the same target table → duplicate rows!

# ✅ GOOD: Check current state before triggering
# 1. Check if a run is in progress:
airflow dags list-runs sales_etl | grep "running\|queued"
# If any output: a run is in progress — don't trigger again

# 2. Or configure max_active_runs to prevent duplicates in the DAG:
@dag(max_active_runs=1)  # Only 1 run at a time — second trigger queues or fails
def sales_etl():
    ...
```

---

## 🎤 Senior-Level Interview Q&A

**Q1: A critical pipeline failed for 7 days due to a data source issue. The source is now fixed. How do you reprocess those 7 days?**

> Use backfill with reset: `airflow dags backfill -s 2024-03-08 -e 2024-03-14 --reset-dagruns --max-active-runs 3 <dag_id>`. `--reset-dagruns` is critical — without it, backfill skips dates that already have DAG Runs (even failed ones). `--max-active-runs 3` prevents all 7 days from running simultaneously, which could overwhelm the now-recovering data source. Monitor progress: `watch "airflow dags list-runs <dag_id> | tail -10"`. If the DAG has downstream dependencies (another DAG triggered via sensor), those will trigger automatically once each backfill run succeeds.

**Q2: What is the difference between `airflow dags delete` and removing the DAG Python file?**

> `airflow dags delete <dag_id>` removes the DAG's **metadata** from the database — DAG Runs, Task Instances, history, serialized DAG — but does NOT delete the Python file. If the file still exists and the scheduler re-parses it, the DAG reappears (with no history). To fully remove a DAG: (1) Delete the Python file from the dags/ folder OR move it to `.airflowignore`. (2) Wait for the scheduler to detect the missing file (up to 30s). (3) Run `airflow dags delete <dag_id>` to clean up the metadata. If you only delete the file without `dags delete`, the DAG appears as "missing" in the UI but its history remains in the DB.

**Q3: You need to trigger a DAG with runtime parameters from an external system event. How do you implement this?**

> Use `airflow dags trigger <dag_id> --conf '{"param": "value"}'` or the REST API. In the DAG, access the conf via: `dag_run.conf["param"]` inside a task (TaskFlow: `context["dag_run"].conf["param"]`). For event-driven triggering: create an API gateway or message consumer that calls `POST /api/v1/dags/{dag_id}/dagRuns` with the event payload as `conf`. Example: an S3 event lambda calls the Airflow API when a new file arrives, passing `{"s3_path": "s3://bucket/file.csv"}` as conf. The DAG reads this path and processes exactly that file. This is the foundation of event-driven Airflow scheduling.

---

## 🏛️ Principal-Level Interview Q&A

**Q1: Design a safe automated backfill system for a production Airflow environment with 200 DAGs.**

> **Safe backfill automation**: (1) **Pre-flight checks**: verify the source data is available for the backfill date range before starting. Query the source system's data completeness view. (2) **Dependency-aware ordering**: analyze DAG dependencies (DAG A's output feeds DAG B). Backfill in topological order — parent DAGs before child DAGs. (3) **Rate limiting**: never backfill all 200 DAGs simultaneously. Group into waves by priority tier: `critical` (5 DAGs, max-active-runs=3), `standard` (50 DAGs, max-active-runs=2), `best-effort` (145 DAGs, max-active-runs=1). (4) **Metadata DB protection**: excessive backfilling creates millions of Task Instance rows quickly. Set `airflow db clean --oldest-time {backfill_start}` AFTER backfill to remove old failed instances before creating new ones. (5) **Rollback plan**: record the exact backfill command used. If results are incorrect, `airflow dags backfill --reset-dagruns` on the same date range reruns cleanly.

**Q2: How do you implement blue-green DAG deployment — switching traffic from old to new DAG version without downtime or data loss?**

> **Blue-green DAG**: (1) **Deploy blue**: rename current `sales_etl` → `sales_etl_blue` (update `dag_id` in the file). Deploy new version as `sales_etl_green`. (2) **Validation**: run `sales_etl_green` with `max_active_runs=1` on a small date range in staging. Verify output matches `sales_etl_blue` output for the same dates. (3) **Traffic switch**: pause `sales_etl_blue` (`airflow dags pause sales_etl_blue`). Unpause `sales_etl_green`. Rename green to `sales_etl` (update dag_id). (4) **Cutover**: `airflow dags backfill` any missed runs during the validation window. (5) **Rollback**: if green has issues, pause green, unpause blue — entire rollback completes in under 30 seconds. Keep blue deployed for 1 full schedule cycle (e.g., 24h for a daily DAG) before deleting.

**Q3: `airflow dags report` shows your largest DAG takes 45 seconds to parse. What are the consequences and how do you fix it?**

> **Consequences**: (1) **Scheduler lag**: with 100 DAGs and 2 parsing processes, if one file takes 45s, it blocks its parsing slot for that duration. Other DAGs in the queue wait — new DAG deployments or schedule changes take longer to take effect. (2) **UI lag**: the webserver also parses DAGs (for the Code View). A 45s parse makes the code view slow to update. (3) **Heartbeat misses**: if parsing blocks the scheduler loop too long, it may miss its own heartbeat and Airflow marks it as "dead." **Root causes**: (a) Heavy imports at the top of the file (`import tensorflow` — 10+ second library load). (b) Network calls at parse time (Variable.get, API calls in module scope). (c) Complex DAG generation (1000+ tasks generated via a loop). **Fixes**: (a) Move heavy imports inside task functions. (b) Remove all Variable.get from module scope. (c) Use `@dag` with `@task` patterns — TaskFlow API serializes faster than classic DAGs. (d) Split into multiple smaller DAG files. (e) Increase `parsing_processes` from 2 to 4.

---

## 📝 Self-Assessment Quiz

**Q1**: What's the difference between `airflow dags delete` and removing the DAG file?
<details><summary>Answer</summary>
`airflow dags delete <dag_id>` removes the DAG's METADATA from the DB (DAG Runs, Task Instances, history, serialized DAG), but does NOT delete the Python file. If the file still exists, the scheduler re-parses it and the DAG reappears (with no history). To fully remove: (1) Delete or .airflowignore the Python file, (2) Then `airflow dags delete <dag_id>` to clean the metadata. Doing only one of the two leaves artifacts.
</details>

**Q2**: A backfill for 7 failing days seems to run but creates no new DAG Runs. What's missing from your command?
<details><summary>Answer</summary>
The `--reset-dagruns` flag. Without it, `dags backfill` silently skips dates that already have DAG Runs — even if those runs are in "failed" state. The command only creates runs for dates with NO existing run. Add `--reset-dagruns` to clear the failed runs first so new ones can be created: `airflow dags backfill -s 2024-01-01 -e 2024-01-07 --reset-dagruns <dag_id>`.
</details>

**Q3**: You run `airflow dags test my_dag 2024-03-15` and see "5,000 rows processed" in the output. Were those rows written to the production database?
<details><summary>Answer</summary>
Possibly yes — this is a common confusion. `dags test` does NOT write task STATE to the Airflow metadata DB (no DAG Run, no Task Instance records). But the TASK CODE still executes fully, including any INSERT/UPDATE statements against external systems. If the task code writes to Postgres, those writes happened. `dags test` is not a sandbox — it's a local executor with no Airflow metadata writes. Use it ONLY to verify that code runs without errors; use a dev environment for safe side-effect testing.
</details>

**Q4**: How do you trigger a DAG with runtime parameters from the CLI?
<details><summary>Answer</summary>
Use the `--conf` flag with a JSON string: `airflow dags trigger my_dag --conf '{"env": "staging", "date": "2024-03-15", "force_full_refresh": true}'`. In the DAG, access via: `context["dag_run"].conf.get("env", "production")` inside any task function. With TaskFlow API: add `**context` to the task signature or use `get_current_context()` to access the dag_run conf. The conf dict is serialized to JSON and stored with the DAG Run metadata.
</details>

### Quick Self-Rating
- [ ] I can trigger, pause, unpause, and backfill DAGs from CLI
- [ ] I know `dags test` is safe (no metadata writes) but task code still executes
- [ ] I use `--reset-dagruns` when backfilling dates with existing failed runs
- [ ] I can trigger DAGs with conf parameters for runtime configuration
- [ ] I know `dags delete` removes metadata only, not the Python file

---

## 📚 Further Reading

- [Airflow CLI Reference — dags](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html#dags) — Complete CLI documentation
- [Airflow REST API — DAG Runs](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#tag/DAGRun) — Programmatic triggering and management
- [Backfill Documentation](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html#backfill) — Backfill patterns and limitations
- [DAG Params and conf](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html) — Runtime parameter passing
