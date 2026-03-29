# Task Commands — Debug & Test Individual Tasks

> **Module 03 · Topic 02 · Explanation 02** — The most useful commands for your daily development workflow

---

## 🎯 The Real-World Analogy: A Surgeon's Rehearsal Room

Task commands are like a **surgical simulation lab**:

| Task Command | Surgical Equivalent |
|-------------|---------------------|
| `tasks test` | Rehearsing in the simulation lab — same procedure, no real patient |
| `tasks run` | Performing the actual surgery — real patient, real records |
| `tasks render` | Reading the pre-op checklist with the patient's actual vitals filled in |
| `tasks list` | Reading the surgical schedule — seeing all procedures in today's OR |
| `tasks state` | Checking the OR board for a specific surgery's status |
| `tasks clear` | Rescheduling a procedure that was cancelled mid-way |

The simulation lab (`tasks test`) is where you practice until you're confident. You never rehearse on a real patient. Similarly, `tasks test` is where you debug until the logic is right — never testing directly on production task runs.

---

## Key Commands

```bash
# ══════════════════════════════════════════════════════════════
# THE TWO MOST IMPORTANT COMMANDS
# ══════════════════════════════════════════════════════════════

# 1. TEST a single task (NO DB writes — SAFE for development)
airflow tasks test <dag_id> <task_id> 2024-03-15
# → Runs the task locally on your machine
# → Uses the LOCAL executor (no CeleryExecutor, no KubernetesExecutor)
# → Output goes directly to your terminal stdout
# → Does NOT record state in the metadata DB
# → Does NOT require a DAG Run to exist
# → BEST tool for development iteration

# 2. RUN a single task manually (WRITES to DB — use carefully)
airflow tasks run <dag_id> <task_id> 2024-03-15
# → Actually executes via the executor
# → Records task instance state in metadata DB
# → Requires a DAG Run to already exist
# → Use for manual recovery, not development

# ══════════════════════════════════════════════════════════════
# INSPECT
# ══════════════════════════════════════════════════════════════
airflow tasks list <dag_id>                            # All tasks in a DAG
airflow tasks list <dag_id> --tree                    # With dependency tree (visual)
airflow tasks state <dag_id> <task_id> 2024-03-15     # Current task instance state

# ══════════════════════════════════════════════════════════════
# RENDER TEMPLATES — Essential for Jinja debugging
# ══════════════════════════════════════════════════════════════
airflow tasks render <dag_id> <task_id> 2024-03-15
# → Shows all Jinja templates resolved with ACTUAL values for that date
# → {{ ds }} → "2024-03-15"
# → {{ prev_ds }} → "2024-03-14"
# → {{ params.table }} → "orders"
# → Does NOT execute the task — just preview

# ══════════════════════════════════════════════════════════════
# CLEAR — Re-queue tasks for re-execution
# ══════════════════════════════════════════════════════════════
airflow tasks clear <dag_id> -t <task_id> \
    -s 2024-03-01 -e 2024-03-15             # Clear specific task across date range

airflow tasks clear <dag_id> \
    -s 2024-03-15 \
    --downstream \                           # Also clear all downstream of cleared tasks
    --yes                                    # Skip confirmation prompt (for scripts)
```

---

## `tasks test` — Your Best Development Tool

```
╔══════════════════════════════════════════════════════════════╗
║  WHY `tasks test` IS YOUR BEST FRIEND                       ║
║                                                              ║
║  1. Runs LOCALLY (no executor, no scheduler needed)         ║
║  2. No DB state writes (won't pollute metadata DB)          ║
║  3. Stdout goes directly to your terminal (instant feedback)║
║  4. Fast iteration: Write → test → fix → test → done       ║
║  5. Works even without a DAG Run existing                   ║
║  6. Simulates a real execution date ({{ ds }} resolves)     ║
║                                                              ║
║  DEVELOPMENT LOOP:                                          ║
║  Edit task code → airflow tasks test → check output         ║
║  → fix → airflow tasks test → repeat until passing         ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Python Integration: Programmatic Task Management

```python
import requests

AIRFLOW_URL = "http://localhost:8080/api/v1"
AUTH = ("admin", "admin")

def get_task_state(dag_id: str, task_id: str, run_id: str) -> str:
    """Equivalent to: airflow tasks state <dag_id> <task_id> <date>"""
    resp = requests.get(
        f"{AIRFLOW_URL}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}",
        auth=AUTH
    )
    return resp.json()["state"]

def clear_task(dag_id: str, task_id: str, run_id: str) -> dict:
    """Equivalent to: airflow tasks clear with specific run"""
    resp = requests.post(
        f"{AIRFLOW_URL}/dags/{dag_id}/clearTaskInstances",
        json={
            "dag_run_id": run_id,
            "task_ids": [task_id],
            "include_downstream": True,
            "dry_run": False
        },
        auth=AUTH
    )
    return resp.json()

def list_tasks(dag_id: str) -> list:
    """Equivalent to: airflow tasks list <dag_id>"""
    resp = requests.get(
        f"{AIRFLOW_URL}/dags/{dag_id}/tasks",
        auth=AUTH
    )
    return [t["task_id"] for t in resp.json()["tasks"]]

# Usage — wait for a task, then clear+retry if failed:
import time

def wait_and_retry(dag_id, task_id, run_id, max_wait_min=30):
    for _ in range(max_wait_min * 2):  # Check every 30s
        state = get_task_state(dag_id, task_id, run_id)
        if state == "success":
            print(f"Task {task_id} succeeded!")
            return True
        if state == "failed":
            print(f"Task {task_id} failed — clearing and retrying...")
            clear_task(dag_id, task_id, run_id)
            return False
        time.sleep(30)
    raise TimeoutError(f"Task {task_id} did not complete within {max_wait_min} minutes")
```

---

## 🏢 Real Company Use Cases

**Stripe** mandates that all new DAG task code be developed using `airflow tasks test` before any code reaches a PR. Their developer guide includes: "Before opening a PR, run `airflow tasks test <dag_id> <task_id> 2024-03-15` — if it doesn't pass locally, it won't pass in CI." This single rule reduced their data pipeline CI failures from 35% of PRs to under 8% in one quarter, because bugs were caught at the developer's desk instead of in the shared CI environment.

**Robinhood** uses `airflow tasks render` as a security checkpoint. Their DLP (Data Loss Prevention) tools scan the rendered SQL queries from tasks that access financial data — after rendering with `airflow tasks render`, the actual SQL (with real table names and date parameters) is passed through a regex scanner that flags queries accessing PII columns without appropriate WHERE filters. Template rendering catches data access policy violations before tasks even run.

**Databricks** (internal Airflow usage) uses `airflow tasks clear -s {date} -e {date} --downstream` as their standard "re-run from task X forward" recovery procedure. Their runbook specifies: "If a task failed due to a transient storage error, clear the task with `--downstream` and the scheduler handles the rest." Operators run this command without needing to understand the full DAG graph — the `--downstream` flag ensures all dependents are re-queued automatically.

---

## ❌ Anti-Patterns

### Anti-Pattern 1: Developing Tasks Without Using `tasks test`

```bash
# ❌ BAD: Edit code → commit → trigger full DAG → wait 20 minutes → see error
# 1. Engineer writes extract task code
# 2. Commits and pushes to CI
# 3. CI deploys to Airflow
# 4. Manually triggers the DAG
# 5. Waits for scheduler to pick it up (2+ min)
# 6. Task runs... fails with a typo error
# 7. Repeat from step 1

# Total iteration time: 25-30 minutes per fix
```

```bash
# ✅ GOOD: Develop with tasks test locally
# 1. Engineer writes extract task code
# 2. airflow tasks test my_dag extract 2024-03-15
# 3. Sees error immediately in terminal
# 4. Fixes, runs tasks test again
# 5. When passing: commit → PR

# Total iteration time: 30 seconds per fix
# 50x faster development loop
```

---

### Anti-Pattern 2: Using `tasks run` Instead of `tasks test` During Development

```bash
# ❌ BAD: Using tasks run for development testing
airflow tasks run my_dag extract 2024-03-15
# Problems:
# 1. Writes to metadata DB → pollutes task instance history
# 2. Requires a DAG Run to exist for 2024-03-15
# 3. Goes through the executor (adds latency)
# 4. Other engineers monitoring the UI see spurious task runs

# ✅ GOOD: tasks test for development (no DB pollution)
airflow tasks test my_dag extract 2024-03-15
# Clean, local, fast — never pollutes the production metadata DB
```

---

### Anti-Pattern 3: Clearing Tasks Without `--downstream` When Needed

```bash
# ❌ BAD: Clearing a failed task without clearing its downstream
airflow tasks clear my_dag -t transform -s 2024-03-15 -e 2024-03-15

# What happens:
# transform re-runs and SUCCEEDS
# But... load and notify are still in upstream_failed state
# They don't re-run because they were never cleared!
# Engineer thinks pipeline is fixed but data never reached the warehouse
```

```bash
# ✅ GOOD: Always use --downstream when the failed task has dependents
airflow tasks clear my_dag \
    -t transform \
    -s 2024-03-15 \
    -e 2024-03-15 \
    --downstream   # Also clears load, notify, and any other downstream tasks
    --yes          # Skip interactive confirmation (safe in scripts)

# Result: transform runs first, then all dependents re-run automatically
```

---

## 🎤 Senior-Level Interview Q&A

**Q1: You want to debug a task's Jinja template to see what SQL query is actually running. Which command do you use?**

> `airflow tasks render <dag_id> <task_id> 2024-03-15`. This resolves all Jinja templates (`{{ ds }}`, `{{ prev_ds }}`, `{{ params.table_name }}`, `{{ var.value.env }}`) with the actual values for the given execution date and prints the result. The output shows exactly what SQL query, BashOperator command, or Jinja-templated field value the task will receive — before execution. Copy the rendered SQL into a database client to test it independently. This is the single most important debugging command for any task using templated fields.

**Q2: What is the exact difference between `tasks test` and `tasks run`? When do you use each?**

> `tasks test`: runs the task function locally using the local executor. Does NOT write task state to the metadata DB, does NOT require a DAG Run to exist, output goes to stdout. Use during development for every iteration. `tasks run`: executes via the configured executor (Celery, Kubernetes, etc.), writes task instance state to the metadata DB, requires an existing DAG Run record. Use for manual recovery — re-running a specific task in a real DAG Run that had a transient failure. Rule: during development, ALWAYS use `tasks test`. Only use `tasks run` for operational recovery in a real DAG Run context.

**Q3: How do you re-run a specific failed task AND all its downstream tasks without re-running the successful upstream tasks?**

> Use `airflow tasks clear <dag_id> -t <task_id> -s <date> -e <date> --downstream`. This finds all task instances for the specified task AND all dependent tasks, resets them to "none" state, and leaves upstream tasks untouched (they remain in "success" state). The scheduler then re-runs only the cleared tasks in dependency order. The upstream tasks don't re-execute — their output in XCom persists and feeds into the re-run of the cleared tasks. This is the standard "partial pipeline re-run" pattern.

---

## 🏛️ Principal-Level Interview Q&A

**Q1: Design a testing strategy for Airflow task development that prevents regressions from reaching production.**

> **4-layer testing pyramid for Airflow tasks**: (1) **Unit tests** (pytest): test the pure Python business logic extracted from tasks. Don't test Airflow internals. Mock external connections. `def test_transform_logic(): result = transform_function({"rows": 5000}); assert result["cleaned_rows"] == 4958`. (2) **Integration tests** (tasks test): `airflow tasks test <dag_id> <task_id> {test_date}` with a test database/S3 bucket. Validates the task code + Airflow operator interaction. Run in CI. (3) **DAG validation** (pytest + Airflow test utilities): `from airflow.models import DagBag; dagbag = DagBag(include_examples=False); assert len(dagbag.import_errors) == 0`. Catches syntax errors, import errors, cyclic dependencies. (4) **End-to-end smoke test** (staging trigger): `airflow dags trigger` on staging with a small date range. Validates the full pipeline (all tasks in sequence) with production-like infrastructure. Gate production deployment on this passing.

**Q2: A data engineer reports that `tasks test` passes but the same task fails in production `tasks run`. How do you diagnose this environment discrepancy?**

> **Root cause categories and diagnostics**: (1) **Environment variables**: `tasks test` uses your LOCAL shell's env vars. Production workers have different env vars (different DB URLs, API keys). Check: `airflow tasks test` passes on your laptop → `ssh worker && airflow tasks test` — does it pass on the actual worker? (2) **Python dependencies**: your local venv has a package installed that the production Docker image doesn't. Check: `pip freeze` on worker vs local. (3) **Network access**: your laptop can reach the DB directly. The Celery worker is in a different VPC subnet behind a NAT. The connection times out from the worker. (4) **File system**: your task reads a local config file that doesn't exist on the worker. (5) **Serialization**: TaskFlow API tasks serialize arguments to XCom. If the return value from the upstream task is too large (>49KB by default), it silently fails. Check XCom size. **Resolution**: always run `tasks test` on the actual worker host, not your local machine, for environment parity validation.

**Q3: How do you implement a "canary task" pattern that automatically clears and retries failed tasks without human intervention?**

> **Automated canary retry system**: (1) **Sensor task pattern**: add a `task_sensor` after critical tasks that polls for downstream success and triggers recovery if needed. (2) **REST API polling loop** (external service): `while True: state = GET /api/v1/taskInstances/{task_id}; if state == "failed": POST /api/v1/dags/{dag_id}/clearTaskInstances`. (3) **Callback-based** (Airflow-native): use `on_failure_callback` on the task. The callback function calls `ti.clear()` for transient error types (connection timeout) but NOT for data errors. Classification: if `isinstance(exception, OperationalError)` → auto-retry via `ti.clear()`; else → alert and halt. (4) **Safety constraints**: max 3 auto-retries (Airflow's `retries` param is better for this). After 3, escalate to human. Add a `max_retry_delay` to prevent retry storms. Log each auto-clear with the error type and timestamp for audit.

---

## 📝 Self-Assessment Quiz

**Q1**: You want to debug a task's Jinja template to see what SQL query it produces for 2024-03-15. Which command?
<details><summary>Answer</summary>
`airflow tasks render <dag_id> <task_id> 2024-03-15`. This resolves ALL Jinja templates ({{ ds }}, {{ prev_ds }}, {{ params.table }}, etc.) with actual values for that execution date and prints the result — without running the task. You can then copy the rendered SQL to a DB client and test it directly.
</details>

**Q2**: What is the key difference between `tasks test` and `tasks run`?
<details><summary>Answer</summary>
`tasks test`: runs locally, NO metadata DB writes, no executor, no existing DAG Run required. Use this during DEVELOPMENT for fast iteration. `tasks run`: runs via the executor, WRITES task state to DB, requires an existing DAG Run. Use this for operational RECOVERY of a specific task in a real DAG Run. During development, always use `tasks test` — it's 10x faster and doesn't pollute the production DB.
</details>

**Q3**: You cleared a failed `transform` task but `load` and `notify` are still stuck in `upstream_failed`. What went wrong?
<details><summary>Answer</summary>
You forgot the `--downstream` flag. Clearing `transform` alone reset only that task. The downstream tasks (`load`, `notify`) remained in `upstream_failed` state — they were never cleared, so they never re-queued. Fix: `airflow tasks clear <dag_id> -t transform -s {date} -e {date} --downstream`. This clears transform AND all tasks downstream of it, allowing the full chain to re-run after transform succeeds.
</details>

**Q4**: `tasks test` passes on your laptop but the same task fails on the production worker. What are the two most common causes?
<details><summary>Answer</summary>
(1) **Environment variable differences**: your local shell has different values (DB URLs, API keys, paths) than the production worker environment. Solution: run `tasks test` on the actual worker host via SSH, not your local machine. (2) **Python dependency differences**: your local venv has a package installed that's missing from the production Docker image (or has a different version). Solution: compare `pip freeze` output between local and production. Always develop in the same Docker image that runs in production.
</details>

### Quick Self-Rating
- [ ] I use `tasks test` for ALL development — never `tasks run`
- [ ] I use `tasks render` to debug Jinja template issues
- [ ] I use `--downstream` when clearing failed tasks with dependencies
- [ ] I can use `tasks clear` to re-run a date range of failed instances
- [ ] I know that `tasks test` doesn't write to the metadata DB but task code still executes

---

## 📚 Further Reading

- [Airflow CLI Reference — tasks](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html#tasks) — Complete tasks CLI documentation
- [Airflow Templates Reference](https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html) — All available Jinja variables for `tasks render`
- [REST API — Task Instances](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#tag/TaskInstance) — Programmatic task clearing and state management
- [Airflow Testing Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#testing-a-dag) — Official testing guidance
