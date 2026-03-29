# Maintenance Commands — Keep Your Airflow Cluster Healthy

> **Module 03 · Topic 02 · Explanation 04** — DB cleanup, version management, scheduler health, and user administration

---

## 🎯 The Real-World Analogy: A Hospital Maintenance Department

Airflow maintenance commands are like a **hospital's facilities and maintenance team**:

| Maintenance Command | Hospital Facilities Equivalent |
|--------------------|-------------------------------|
| `airflow db migrate` | Upgrading the hospital's electronic records system |
| `airflow db clean` | Shredding old patient records past the retention policy |
| `airflow db check` | Testing that the records system is operational |
| `airflow scheduler` | The hospital's central dispatch running 24/7 |
| `airflow users create` | Issuing a new staff ID badge |
| `airflow users list` | Directory of all staff members |
| `airflow info` | The hospital's system status board |
| `airflow version` | Checking which software release is installed |

Just as a hospital's maintenance team runs behind the scenes to ensure the building operates correctly — without maintenance, lights go out and records become inaccessible.

---

## Complete Maintenance Command Reference

```bash
# ══════════════════════════════════════════════════════════════
# DATABASE MANAGEMENT
# ══════════════════════════════════════════════════════════════

# Check database connection and version
airflow db check                          # Tests metadata DB connectivity
airflow db check-migrations               # Verifies DB schema is current

# Initialize a fresh database (first-time setup only)
airflow db migrate                        # Creates/upgrades metadata DB schema
# ⚠️  In Airflow 2.7+: replaces the old 'airflow db init' and 'airflow db upgrade'

# Clean up old data (CRITICAL for production health)
airflow db clean \
    --clean-before-timestamp "2024-01-01T00:00:00+00:00" \
    --tables task_instance,dag_run,log \
    --verbose
# Removes: task instances, dag runs, logs older than the timestamp
# Does NOT remove: DAG definitions, connections, variables

# Reset (DESTRUCTIVE — development only!)
airflow db reset --yes                    # Drops and recreates all tables
# WARNING: Permanently deletes ALL DAG runs, task instances, connections, variables

# ══════════════════════════════════════════════════════════════
# SCHEDULER HEALTH
# ══════════════════════════════════════════════════════════════
airflow scheduler                         # Start the scheduler
airflow scheduler -n 10                   # Run 10 scheduler loops then exit (useful for k8s)
airflow jobs check --job-type SchedulerJob # Check if scheduler is alive

# Check if scheduler is responsive:
airflow jobs list --job-type SchedulerJob --limit 5

# ══════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ══════════════════════════════════════════════════════════════
# Create a new admin user:
airflow users create \
    --username admin \
    --password secretpassword \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@company.com

# List all users:
airflow users list

# Available roles:
# Admin, Op, User, Viewer, Public (least privileged → most)
airflow users add-role --username john.doe --role User
airflow users delete --username old.employee

# ══════════════════════════════════════════════════════════════
# SYSTEM INFO
# ══════════════════════════════════════════════════════════════
airflow version                           # Airflow version
airflow info                             # Full system info (Python, DB, executor, paths)
airflow config list                      # All config values (includes env overrides)
airflow config get-value core executor   # Get a specific config value

# ══════════════════════════════════════════════════════════════
# VARIABLES & CONNECTIONS BULK OPERATIONS
# ══════════════════════════════════════════════════════════════
airflow variables export vars.json        # Export all variables
airflow variables import vars.json        # Import variables from JSON
airflow connections export conns.json     # Export all connections
airflow connections import conns.json     # Import connections from JSON
```

---

## Why `db clean` is Critical for Production

```
╔══════════════════════════════════════════════════════════════════╗
║  METADATA DB GROWTH without airflow db clean                     ║
║                                                                   ║
║  100 DAGs × 10 tasks × 3 retries × 365 days =                   ║
║  100 × 10 × 3 × 365 = 1,095,000 task instance rows/year         ║
║                                                                   ║
║  Plus: dag_run rows, xcom rows, log rows, job rows              ║
║  Total: 5-10 million rows per year                               ║
║                                                                   ║
║  Without cleanup:                                                 ║
║  → UI becomes slow (queries scan huge tables)                    ║
║  → Scheduler loop slows (more rows to update)                   ║
║  → Backup times grow (more data to backup)                      ║
║  → Storage costs increase                                        ║
║                                                                   ║
║  WITH airflow db clean (quarterly, keep 90 days):               ║
║  → Steady-state: ~2-3 months of data in the DB                  ║
║  → Fast UI, fast scheduler, predictable storage costs           ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Python: Automating Maintenance Operations

```python
import subprocess
import requests
from datetime import datetime, timedelta

AIRFLOW_URL = "http://localhost:8080/api/v1"
AUTH = ("admin", "admin")

def check_scheduler_health() -> bool:
    """Verify scheduler is alive via the health endpoint."""
    resp = requests.get(f"{AIRFLOW_URL}/health", auth=AUTH, timeout=10)
    health = resp.json()
    scheduler_status = health.get("scheduler", {}).get("status")
    metadatabase_status = health.get("metadatabase", {}).get("status")

    print(f"Scheduler: {scheduler_status}")
    print(f"Metadata DB: {metadatabase_status}")

    return scheduler_status == "healthy" and metadatabase_status == "healthy"

def run_db_clean(days_to_keep: int = 90) -> bool:
    """Run airflow db clean to remove data older than N days."""
    cutoff = (datetime.utcnow() - timedelta(days=days_to_keep)).strftime(
        "%Y-%m-%dT%H:%M:%S+00:00"
    )
    result = subprocess.run(
        [
            "airflow", "db", "clean",
            "--clean-before-timestamp", cutoff,
            "--tables", "task_instance,dag_run,log,xcom",
            "--yes",
            "--verbose"
        ],
        capture_output=True,
        text=True
    )
    success = result.returncode == 0
    if not success:
        print(f"db clean FAILED: {result.stderr}")
    else:
        print(f"db clean SUCCESS: {result.stdout[-200:]}")  # Last 200 chars
    return success

def get_user_list() -> list:
    """List all Airflow users via REST API."""
    resp = requests.get(f"{AIRFLOW_URL}/users", auth=AUTH)
    return resp.json()["users"]

def create_user(username: str, password: str, role: str, email: str) -> dict:
    """Create a user via REST API."""
    resp = requests.post(
        f"{AIRFLOW_URL}/users",
        auth=AUTH,
        json={
            "username": username,
            "password": password,
            "first_name": username.split(".")[0].capitalize(),
            "last_name": username.split(".")[-1].capitalize() if "." in username else "",
            "roles": [{"name": role}],
            "email": email
        }
    )
    resp.raise_for_status()
    return resp.json()

# Health check example (use in monitoring scripts):
if check_scheduler_health():
    print("✅ Airflow cluster is healthy")
else:
    print("❌ Airflow cluster has issues — investigate immediately")
    # Fire PagerDuty alert here
```

---

## 🏢 Real Company Use Cases

**Shopify** runs `airflow db clean` as a weekly scheduled Kubernetes Job. Their cleanup policy: keep 60 days of task instances and DAG runs, 30 days of logs, 14 days of XCom entries. This keeps their metadata DB (PostgreSQL on AWS RDS) at a predictable ~15GB across 400+ DAGs. Without cleanup, they estimated their DB would grow to 200GB+ within a year, requiring expensive DB tier upgrades. The cleanup job runs on Sunday 3am UTC and takes ~20 minutes.

**PayPal** uses `airflow info` and `airflow version` as the first step in any support ticket. All engineers debugging Airflow issues run `airflow info > airflow_info.txt` and attach the output to their ticket — it captures Python version, DB type, executor type, dags folder, plugins folder, and all relevant environment variables. This eliminates 80% of the "what version are you on?" back-and-forth in support conversations.

**Nubank** (Brazilian fintech) uses the `/health` API endpoint instead of CLI commands for automated monitoring. Their Datadog integration polls `GET /api/v1/health` every 60 seconds and alerts if the scheduler status changes from "healthy" to "unhealthy." The health endpoint is richer than `airflow jobs check` — it returns both scheduler status AND metadata DB connectivity status in one JSON response, enabling them to distinguish "scheduler crashed" from "scheduler can't reach DB."

---

## ❌ Anti-Patterns

### Anti-Pattern 1: Never Running `db clean` Until the DB Is Full

```
# ❌ BAD: No cleanup policy → metadata DB grows unbounded
# Year 1: DB is 10GB (fast)
# Year 2: DB is 40GB (starting to slow)
# Year 3: DB is 100GB (UI is slow, scheduler lags)
# Year 4: DB is 200GB (CRISIS — out of storage, upgrade emergency)
#
# At this point, running db clean takes HOURS (scanning 200GB tables)
# and the scheduler slows to a crawl during cleanup
#
# ✅ GOOD: Run db clean quarterly with 90-day retention
# Steady state: DB stays at 15-25GB
# Each cleanup run takes 15-30 minutes (manageable)
# Weekly or monthly is even better for large, busy clusters
```

---

### Anti-Pattern 2: Running `db reset` Against Production

```bash
# ❌ CATASTROPHIC MISTAKE:
airflow db reset --yes  # Drops ALL tables, recreates empty schema

# What is permanently deleted:
# → All DAG Run history
# → All Task Instance records
# → All XCom values
# → All connections (passwords gone)
# → All variables
# → All users and roles
# → All scheduler job records

# This command exists for development environments ONLY
# There is NO RECOVERY without a DB backup

# ✅ SAFEGUARDS for production:
# 1. Never run db reset on production (obvious)
# 2. Restrict CLI access on production servers to ops team only
# 3. Make sure production never has the same $AIRFLOW_HOME as dev
# 4. Use db clean (non-destructive, date-ranged) instead
# 5. Always have a DB backup before ANY maintenance command
```

---

### Anti-Pattern 3: Creating Users with Admin Role for All Engineers

```bash
# ❌ BAD: Give everyone Admin to avoid permission questions
airflow users create --username john --role Admin
airflow users create --username jane --role Admin
airflow users create --username bob --role Admin
# Now every engineer can:
# → Delete any connection (🔥 production outage risk)
# → Reset any variable (🔥 pipeline config corruption)
# → Pause any DAG (🔥 data pipeline halted)
# → Read all encrypted connection passwords (security risk)
```

```bash
# ✅ GOOD: Least-privilege roles
# Data engineers who write DAGs: User role (can trigger, view logs, clear tasks)
airflow users create --username john --role User

# Data engineers who monitor: Viewer role (read-only)
airflow users create --username jane --role Viewer

# On-call engineers who need to manage connections: Op role
airflow users create --username oncall --role Op

# Platform team only: Admin role
airflow users create --username platform.admin --role Admin
```

---

## 🎤 Senior-Level Interview Q&A

**Q1: Your metadata DB is growing rapidly and the UI is getting slow. How do you diagnose and fix this?**

> **Diagnosis**: (1) Run `airflow db check` — confirms DB connectivity. (2) Direct DB query: `SELECT COUNT(*) FROM task_instance;` — if >10 million rows, cleanup is overdue. (3) Check table sizes: `SELECT pg_size_pretty(pg_total_relation_size('task_instance'));`. (4) `airflow dags list-runs --limit 100` — are there thousands of runs for old DAGs that no longer exist? **Fix**: (1) `airflow db clean --clean-before-timestamp "2024-01-01T00:00:00+00:00" --yes` — removes old records. (2) For XCom bloat: check if any tasks push large blobs — reduce XCom size or use S3 backend. (3) Set a cleanup schedule going forward: weekly cron job running `db clean --clean-before-timestamp "{90_days_ago}"`.

**Q2: What's the difference between `airflow db migrate` and `airflow db reset`? When do you use each?**

> `db migrate`: applies schema migrations to bring the DB to the current Airflow version's expected schema. It's **non-destructive** — adds new columns and tables, never deletes data. Use this every time you upgrade Airflow. Run it before starting the scheduler after an upgrade. `db reset`: drops ALL tables and recreates them empty. It's **destructive** — permanently deletes all data (runs, connections, variables, users). Use ONLY in development to start fresh. NEVER in production. Rule: "migrate = upgrade, reset = nuke."

**Q3: How do you check if the Airflow scheduler is healthy without opening the UI?**

> Three CLI methods in order of richness: (1) `airflow jobs check --job-type SchedulerJob` — exits 0 if a heartbeat was received within `scheduler_health_check_threshold` (default 30s). Exits 1 if scheduler appears dead. (2) `airflow jobs list --job-type SchedulerJob --limit 1` — shows the latest scheduler job with its `latest_heartbeat` timestamp. (3) REST API: `curl http://airflow:8080/api/v1/health | python -m json.tool` — returns JSON with `scheduler.status` and `metadatabase.status`. Best for monitoring systems because it's structured and machine-parseable.

---

## 🏛️ Principal-Level Interview Q&A

**Q1: Design a complete Airflow operational health monitoring system for a 24/7 production cluster.**

> **Multi-layer health monitoring**: (1) **Real-time health endpoint** (every 60s): `GET /api/v1/health` → alert if scheduler or metadatabase status ≠ "healthy." PagerDuty page if down >3 minutes. (2) **Scheduler heartbeat** (every 5m): `airflow jobs check --job-type SchedulerJob` → alert if check fails. This catches the case where the process is running but not processing DAGs. (3) **Metadata DB health** (every 5m): `SELECT 1` query with 5s timeout. Separate from Airflow health endpoint. (4) **Business metrics** (every 15m): count of DAG runs in `running` state > 4 hours (stale) → investigate. Count of `failed` runs in the last hour > threshold → alert. (5) **Capacity metrics** (hourly): task queue depth (queued task instances), worker CPU/memory via Prometheus. Alert if queue depth > 200 (workers can't keep up). (6) **DB health** (daily): metadata DB size, table row counts, auto_analyze status. Alert if DB > 80% of storage limit. (7) **Dashboards**: Grafana board with all metrics, 7-day trends, and SLA compliance charts.

**Q2: Your team wants to upgrade Airflow from 2.7 to 2.10 with zero downtime. Walk through the database migration strategy.**

> **Zero-downtime upgrade strategy**: (1) **Pre-upgrade**: `airflow db check-migrations` to confirm current DB schema matches Airflow 2.7. Take a full metadata DB backup. (2) **Test migration**: apply `airflow db migrate` using Airflow 2.10 binary against a restored DB COPY (not production). Verify migration completes without errors. Record migration duration (plan downtime window accordingly). (3) **Rolling upgrade** (if your executor supports it): deploy new Airflow 2.10 webservers alongside 2.7 webservers. Airflow 2.7 scheduler continues running. Run `airflow db migrate` with the 2.10 binary — the schema migrations are backward-compatible for one minor version. (4) **Scheduler cutover**: pause the 2.7 scheduler, start the 2.10 scheduler. This is the actual downtime window (seconds, not minutes). (5) **Verify**: `airflow dags list`, `airflow jobs list`, check UI. (6) **Rollback plan**: if issues occur within 1 hour: restore the DB backup, restart 2.7 scheduler. Migration duration determines maximum rollback window.

**Q3: You join a company and discover their Airflow has 47 Admin users. How do you implement least-privilege access control?**

> **RBAC remediation project**: (1) **Audit**: `airflow users list -o json` + `airflow users list-roles` — identify who has Admin vs what they actually need. Interview team leads about what each user genuinely does in Airflow. (2) **Role matrix**: define roles by job function: `DE_Standard` (User role + dag:can_trigger), `DE_Senior` (Op role — can manage variables/connections), `DE_Lead` (Op role + read connections), `Platform_Admin` (Admin — connection CRUD, user management). (3) **Gradual downgrade**: start with removing Admin from users who only trigger and monitor DAGs (move to User). Announce change 2 weeks ahead. Monitor for access complaints — evidence for actual permissions needed. (4) **Custom roles**: if built-in roles don't fit, define custom roles via the Airflow permissions system: `airflow roles add-perms`. (5) **Break-glass**: keep 2 Admin accounts in a vault for emergency access — rotate password after each use. (6) **Ongoing governance**: quarterly access review, `airflow users list` to detect new Admins, remove Admin from engineers who no longer need it.

---

## 📝 Self-Assessment Quiz

**Q1**: Why should you run `airflow db clean` on a schedule in production?
<details><summary>Answer</summary>
The metadata DB grows continuously with task instances, DAG runs, XCom values, and logs. Without cleanup: (1) UI queries slow down as they scan millions of rows. (2) The scheduler loop takes longer processing larger tables. (3) DB storage costs grow unboundedly. (4) Backups take longer. `airflow db clean` with a 90-day retention policy keeps the DB at a stable, manageable size. Run it weekly or monthly on a schedule — don't wait until performance degrades.
</details>

**Q2**: What is the difference between `airflow db migrate` and `airflow db reset`?
<details><summary>Answer</summary>
`db migrate`: **non-destructive** schema upgrade. Adds new columns/tables for the current Airflow version. Run this after every Airflow upgrade. No data is lost. `db reset`: **destructive** — drops ALL tables and recreates them empty. Permanently deletes all task instances, connections, variables, users, and DAG run history. Use ONLY in development. NEVER in production. If you mean to upgrade, use `migrate`. If you ran `reset` on production accidentally, you need a DB backup to recover.
</details>

**Q3**: How do you check if the Airflow scheduler is healthy from the command line?**
<details><summary>Answer</summary>
`airflow jobs check --job-type SchedulerJob` — exits 0 if a scheduler heartbeat was received recently, exits 1 if the scheduler appears dead (no heartbeat within `scheduler_health_check_threshold`, default 30s). For programmatic monitoring: `curl http://airflow-host:8080/api/v1/health` returns JSON with `scheduler.status` ("healthy" or "unhealthy") and `metadatabase.status`. The REST API is preferred for automated monitoring systems.
</details>

**Q4**: Why is giving all data engineers the Admin role an anti-pattern?
<details><summary>Answer</summary>
The Admin role allows: deleting any connection (causing production outages), modifying/deleting any variable (corrupting pipeline configs), pausing any DAG (halting data flows), reading all encrypted connection passwords (security risk), and creating/deleting users. These capabilities should be restricted. Most engineers only need: User (trigger DAGs, view logs, clear tasks) or Viewer (read-only monitoring). Use least-privilege: grant the minimum role needed for each engineer's actual job function. Restrict Admin to the platform team only.
</details>

### Quick Self-Rating
- [ ] I run `db clean` on a schedule — never let the metadata DB grow unbounded
- [ ] I know `db migrate` is for upgrades and `db reset` is for development only
- [ ] I can check scheduler health from the CLI and REST API
- [ ] I create users with the least-privilege role needed for their job
- [ ] I can use `airflow info` to quickly gather system information for debugging

---

## 📚 Further Reading

- [Airflow CLI Reference — db](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html#db) — Complete database CLI documentation
- [Airflow CLI Reference — users](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html#users) — User management CLI
- [Airflow RBAC Documentation](https://airflow.apache.org/docs/apache-airflow/stable/security/access-control.html) — Roles and permissions system
- [Airflow Health Check API](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/get_health) — `/api/v1/health` endpoint reference
- [Metadata DB Maintenance](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/metadata-db-cleanup.html) — Official db clean guide
