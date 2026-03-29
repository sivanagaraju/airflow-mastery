# Connections UI — External System Credentials

> **Module 03 · Topic 01 · Explanation 09** — Admin → Connections — the encrypted credential store

---

## 🎯 The Real-World Analogy: A Hotel Key Card System

Think of Airflow Connections as a **hotel key card system**:

| Connections Concept | Hotel Key Card Equivalent |
|--------------------|--------------------------|
| **Connection ID** | Key card label ("Room 412", "Gym", "Pool") |
| **Connection type** | Door lock type (room deadbolt, gym swipe, pool fob) |
| **Host/Port/Login/Password** | Key card programming — the actual access credentials |
| **Fernet encryption** | The card is chip-encrypted — you can't read the data off the card |
| **UI masking** | Cards at the front desk have the room number printed, not the magnetic data |
| **Environment variables for prod** | Master key stored in the hotel safe — not on the front desk |
| **Multiple tasks sharing a connection** | Any door with the same lock type accepts the same card |

The front desk staff can issue key cards (create connections) and see which rooms cards open (connection ID), but cannot read the magnetic data (encrypted password). That's exactly how Airflow Connections work.

---

## What a Connection Contains

```mermaid
graph LR
    CONN[Airflow Connection] --> CONNID["conn_id<br/>(your identifier)"]
    CONN --> TYPE["conn_type<br/>(postgres, http, aws...)"]
    CONN --> HOST["host / URL"]
    CONN --> PORT["port"]
    CONN --> LOGIN["login / username"]
    CONN --> PASS["password<br/>(Fernet encrypted)"]
    CONN --> SCHEMA["schema<br/>(database name)"]
    CONN --> EXTRA["extra<br/>(JSON: api_key, role, region...)"]

    style CONN fill:#017CEE,color:#fff
    style PASS fill:#f44336,color:#fff
```

```
╔══════════════════════════════════════════════════════════════════╗
║  CONNECTIONS UI (Admin → Connections)                            ║
║                                                                   ║
║  Conn ID           │ Type       │ Host              │ Actions    ║
║  ──────────────────┼────────────┼──────────────────┼──────────  ║
║  postgres_default  │ postgres   │ db.company.com    │ ✎ ✗ Test  ║
║  s3_default        │ aws        │ s3.amazonaws.com  │ ✎ ✗ Test  ║
║  slack_alerts      │ slack      │ hooks.slack.com   │ ✎ ✗ Test  ║
║  snowflake_prod    │ snowflake  │ xy12345.snowflake │ ✎ ✗ Test  ║
║                                                                   ║
║  [+ Add Connection]                                               ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Connection Types (Most Common)

| Type | Use Case | Typical conn_id |
|------|----------|----------------|
| `postgres` | PostgreSQL database | `postgres_default` |
| `mysql` | MySQL database | `mysql_warehouse` |
| `sqlite` | SQLite (dev only) | `sqlite_default` |
| `http` | REST APIs | `api_default` |
| `aws` | AWS services (S3, RDS, Glue) | `aws_default` |
| `google_cloud_platform` | GCP (BigQuery, GCS) | `gcp_default` |
| `snowflake` | Snowflake DWH | `snowflake_prod` |
| `slack` | Slack webhooks | `slack_alerts` |
| `ssh` | SSH tunnel | `ssh_bastion` |

---

## Three Ways to Create Connections

```python
# ─────────────────────────────────────────────────────────────────
# METHOD 1: CLI (good for scripting, local dev, CI/CD)
# ─────────────────────────────────────────────────────────────────
# airflow connections add 'my_postgres' \
#     --conn-type 'postgres' \
#     --conn-host 'db.example.com' \
#     --conn-port '5432' \
#     --conn-login 'airflow_user' \
#     --conn-password 'secret123' \
#     --conn-schema 'analytics'
#
# airflow connections get my_postgres          # Verify it was created
# airflow connections test my_postgres         # Test the connection

# ─────────────────────────────────────────────────────────────────
# METHOD 2: Environment Variables (BEST for production — no DB storage)
# ─────────────────────────────────────────────────────────────────
# Format: AIRFLOW_CONN_{CONN_ID_UPPERCASE}
#
# PostgreSQL URI format:
# export AIRFLOW_CONN_MY_POSTGRES='postgresql://airflow_user:secret123@db.example.com:5432/analytics'
#
# JSON format (for complex connections):
# export AIRFLOW_CONN_SNOWFLAKE_PROD='{
#   "conn_type": "snowflake",
#   "login": "svc_airflow",
#   "password": "secret",
#   "schema": "ANALYTICS",
#   "extra": {"account": "xy12345", "warehouse": "COMPUTE_WH", "role": "AIRFLOW_ROLE"}
# }'

# ─────────────────────────────────────────────────────────────────
# METHOD 3: REST API (for programmatic creation)
# ─────────────────────────────────────────────────────────────────
import requests

requests.post(
    "http://localhost:8080/api/v1/connections",
    auth=("admin", "admin"),
    json={
        "connection_id": "my_postgres",
        "conn_type": "postgres",
        "host": "db.example.com",
        "port": 5432,
        "login": "airflow_user",
        "password": "secret123",
        "schema": "analytics"
    }
)
```

---

## Using Connections in Code

```python
from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime

@dag(dag_id="connection_usage_demo", schedule="@daily",
     start_date=datetime(2024, 1, 1), catchup=False)
def pipeline():

    @task()
    def extract_with_hook() -> int:
        """Standard practice: use provider hooks, not manual connection parsing."""
        # PostgresHook reads 'postgres_default' connection from metadata DB
        # Handles connection pooling, retries, and SSL automatically
        hook = PostgresHook(postgres_conn_id="postgres_default")
        records = hook.get_records("SELECT COUNT(*) FROM orders WHERE date = %s",
                                   parameters=[("2024-03-15",)])
        return records[0][0]

    @task()
    def get_connection_details():
        """Access raw connection fields when needed."""
        conn = BaseHook.get_connection("postgres_default")
        print(f"Host: {conn.host}")
        print(f"Port: {conn.port}")
        print(f"Schema: {conn.schema}")
        # conn.password is returned but masked in logs if sensitive=True
        
        # For extra/JSON fields:
        extra = conn.extra_dejson  # Parses extra field as dict
        role = extra.get("role")
        return {"host": conn.host, "schema": conn.schema}

    count = extract_with_hook()
    get_connection_details()

pipeline()
```

---

## 🏢 Real Company Use Cases

**Uber** manages 300+ Airflow connections across their data platform using Kubernetes Secrets as the Airflow secrets backend. All connections are defined as K8s Secrets in the `airflow-secrets` namespace — NEVER stored in the Airflow metadata DB. The `AIRFLOW_CONN_*` pattern means connections work identically in dev (local variables) and production (K8s secrets), zero code changes needed. Their infra team manages connection rotation as K8s secret updates, with Airflow picking up changes on each new task execution.

**Deliveroo** uses the `Test Connection` button in the UI as part of their connection onboarding workflow. Before any new data source goes live, a data engineer must: create the connection in staging, click "Test Connection" to verify it resolves, screenshot the green "Connection successfully tested" result, and attach it to the data source onboarding ticket. This prevents the common failure mode where a connection is created but forgotten — discovered only when a task fails in production at midnight.

**Spotify** implemented a custom connection secrets backend using HashiCorp Vault. All Airflow connections are stored in Vault at `secret/airflow/connections/{conn_id}`. Access is controlled by Vault policies tied to team namespaces — the Ads team can only read `ads_*` connection IDs, the Core Data team can read all connections. Vault provides a full audit trail: who accessed which connection credential and when. This satisfies their SOC 2 compliance requirements without changing any DAG code.

---

## ❌ Anti-Patterns

### Anti-Pattern 1: Hardcoding Credentials In DAG Code

```python
# ❌ WORST — credentials hardcoded in DAG file (in Git!)
@task()
def connect_to_db():
    import psycopg2
    conn = psycopg2.connect(
        host="db.example.com",
        port=5432,
        user="admin",           # 🔴 In Git forever
        password="secret123",   # 🔴 In Git forever, security incident!
        database="analytics"
    )

# Security risks:
# → Credentials in Git history (cannot be fully removed once pushed)
# → Anyone with repo access sees production passwords
# → Rotating credentials requires a code change, PR, and deployment
```

```python
# ✅ GOOD — credentials in Connection, accessed via Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook

@task()
def connect_to_db():
    # Credentials stored encrypted in metadata DB (or Secrets Manager)
    # No credentials in code, no credentials in Git
    hook = PostgresHook(postgres_conn_id="postgres_analytics")
    records = hook.get_records("SELECT * FROM orders LIMIT 10")
    return records
```

---

### Anti-Pattern 2: Storing Credentials in Variables Instead of Connections

```python
# ❌ BAD — using Variables for credentials
from airflow.models import Variable

@task()
def extract():
    # Variables are NOT encrypted by default
    # Appear as plaintext in the UI for all admins to see
    db_password = Variable.get("db_password")
    api_key = Variable.get("stripe_key")
    # Anyone with Airflow Admin role can read "stripe_key" value in clear text
```

```python
# ✅ GOOD — use Connections for credentials (always Fernet-encrypted)
from airflow.hooks.base import BaseHook

@task()
def extract():
    # Password stored encrypted, masked in UI
    conn = BaseHook.get_connection("postgres_analytics")
    password = conn.password   # Decrypted at runtime, never exposed in UI

    stripe_conn = BaseHook.get_connection("stripe_api")
    api_key = stripe_conn.extra_dejson.get("api_key")  # In Extra JSON field
```

---

### Anti-Pattern 3: Using UI-Managed Connections in Production (Not Infrastructure-as-Code)

```
# ❌ BAD: Production connections managed entirely via UI
# Problems:
# 1. No version control — who changed the Snowflake password and when?
# 2. Not reproducible — setting up a new environment requires manual clicking
# 3. No audit trail — security team can't see who accessed credentials
# 4. DR failure — if metadata DB is lost, all connections are lost too

# ✅ GOOD: Production connections via environment variables or secrets backend
# 
# Option A: Environment variables (K8s Secrets, Docker secrets)
# AIRFLOW_CONN_POSTGRES_PROD='postgresql://user:pass@host:5432/db'
#
# Option B: Secrets Manager backend
# All connections live in AWS Secrets Manager / HashiCorp Vault
# Airflow reads from there, never writes to metadata DB
#
# Benefits:
# → Rotation handled by secrets manager (no manual update needed)
# → Full audit trail in secrets manager access logs
# → DR: redeploy Airflow → connections immediately available from secrets manager
# → Separate access controls: DE team reads secrets, infra team manages them
```

---

## 🎤 Senior-Level Interview Q&A

**Q1: Why should you prefer environment variables over the UI for production connections?**

> Three production-critical reasons: (1) **Version control and auditing**: env vars managed via K8s Secrets or Secrets Manager have an audit trail (who changed what, when). UI changes leave no consistent audit trail — problematic for SOC 2 / ISO 27001 compliance. (2) **No single point of failure**: if the Airflow metadata DB is corrupted or lost, all UI-managed connections are gone. Env var connections survive DB failures and are immediately available after a DB restore. (3) **Reproducibility**: standing up a new environment or DR deployment is automated — `kubectl apply -f secrets.yaml` vs manually clicking "Add Connection" 50 times. UI connections are appropriate for development only.

**Q2: A task fails with "connection refused" to PostgreSQL. Walk through your debugging approach using the Connections UI.**

> Step 1: Admin → Connections → find `postgres_default` → click "Test Connection." This immediately tells you if the issue is the connection config (wrong host/port/credentials) or the task code. Step 2: If test passes → the task itself has a bug (bad SQL, wrong schema name, permission issue). Check task logs for the specific SQL error. Step 3: If test fails → the connection config is wrong or the database is unreachable. Check: (a) Is the host resolvable from the Airflow worker network? (b) Is port 5432 open (firewall)? (c) Are credentials correct? Try: `airflow connections test postgres_default` from the CLI on the worker host to test from the exact network context where tasks run.

**Q3: Explain how Fernet encryption works for Connection passwords and what key management looks like.**

> Airflow uses **Fernet symmetric encryption** (AES-128 in CBC mode) for Connection passwords. The Fernet key is set via `AIRFLOW__CORE__FERNET_KEY` environment variable — a 32-byte base64-encoded key. When a password is stored via UI or API: `encrypted_value = Fernet(fernet_key).encrypt(password.encode())`. The encrypted bytes are stored in the `connection` table. When a task reads the connection: `decrypted_password = Fernet(fernet_key).decrypt(encrypted_value).decode()`. **Key management**: (1) The Fernet key must be the SAME across all Airflow components (webserver, scheduler, workers). (2) If the key is lost, encrypted passwords are permanently unrecoverable. (3) Rotate by: generating a new key → re-encrypting all Connection passwords → deploying the new key. `airflow rotate-fernet-key` automates this. Store the key in AWS KMS or Vault, not in a .env file.

---

## 🏛️ Principal-Level Interview Q&A

**Q1: Design a connection management strategy for a team of 50 data engineers with 200+ connections across dev/staging/production.**

> **Tiered connection management**: (1) **Dev**: local env vars or UI-managed. Engineers own their dev connections. No governance required. (2) **Staging**: connections managed as K8s Secrets via GitOps (Flux/ArgoCD). Staging secrets are auto-rotated monthly. Only the platform team has write access. Engineers request new connections via a self-service PR template. (3) **Production**: AWS Secrets Manager backend for all connections. Engineers never see production passwords. Connection requests go through change management (JIRA ticket → security review → infra team creates the secret). (4) **Audit**: all production secret accesses logged in CloudTrail. Monthly review: which connections had zero accesses in 30 days? (can be deleted). (5) **Rotation**: production DB passwords rotate automatically via AWS Secrets Manager — Airflow always reads the current version without any config changes.

**Q2: Your Airflow cluster has 500 tasks running simultaneously, all potentially creating new DB connections via the same `postgres_prod` connection. How do you prevent connection exhaustion?**

> **Connection pool management**: (1) **SQLAlchemy pool in hooks**: Airflow's PostgresHook uses SQLAlchemy's connection pool. Configure `engine_kwargs={"pool_size": 5, "max_overflow": 10}` in the connection's `extra` JSON field. Per-worker: max 15 connections (pool_size + max_overflow). (2) **Airflow Pools**: create a pool `postgres_prod_pool` with `pool_slots=100` (matching your Postgres `max_connections - 20` buffer). Set `pool="postgres_prod_pool"` on all tasks that use this connection. Tasks queue for a pool slot instead of creating unlimited connections. (3) **Connection string parameters**: append `?pool_pre_ping=true` to detect stale connections and `?connect_timeout=10` to fail fast on unavailable connections. (4) **PgBouncer**: put a connection pooler between Airflow and Postgres. Airflow tasks connect to PgBouncer (which allows 500 connections), PgBouncer multiplexes to Postgres (which allows 100).

**Q3: How do you implement connection credential rotation with zero downtime in a production Airflow cluster?**

> **Zero-downtime rotation for env-var-based connections**: (1) **Dual-credential window**: the database or API service supports BOTH old and new credentials simultaneously for a 30-minute window. (2) **Blue-green secret update**: update the K8s Secret / Secrets Manager value to the new credential. K8s Secrets mounts update within 30s-2m. Running tasks use the old credential from their existing connections. New tasks (starting after the update propagates) use the new credential. (3) **Airflow Secrets Manager backend**: Airflow reads credentials on each task start. Once the Secrets Manager value is updated, the next task start automatically uses the new credential — no Airflow restart needed. (4) **Rollback plan**: keep the old credential version in Secrets Manager for 48 hours. If tasks fail with new credential, revert the Secrets Manager value to the previous version. (5) **Monitoring**: track connection error rates during rotation. Alert if the rate increases >1% during the rotation window.

---

## 📝 Self-Assessment Quiz

**Q1**: Why should you prefer environment variables over the UI for production connections?
<details><summary>Answer</summary>
Three key reasons: (1) **Version control & audit trail** — env vars managed via K8s Secrets or Secrets Manager have full audit trails (who changed what, when). UI changes have no consistent audit trail. (2) **No single point of failure** — if the metadata DB is lost, UI-managed connections are gone. Env var connections survive DB failures. (3) **Reproducibility** — standing up a new environment is automated (apply secrets) not manual (click 50 times in UI). UI connections are appropriate for development only.
</details>

**Q2**: What is the difference between storing credentials in Variables vs Connections?
<details><summary>Answer</summary>
**Connections**: always Fernet-encrypted in the DB. Passwords are masked (`***`) in the UI even for Admins. Designed for structured credentials (host, port, login, password, schema, extra). **Variables**: stored as plaintext by default (marked "sensitive" only masks in logs, not in the UI edit form). Anyone with Admin access can read the value in clear text. Use Connections for ALL credentials; Variables for non-sensitive config values like endpoint URLs, feature flags, and thresholds.
</details>

**Q3**: A task fails with "connection refused" to PostgreSQL. What is your first debugging step using the UI?
<details><summary>Answer</summary>
Go to Admin → Connections → find the connection used by the task → click "Test Connection". This immediately tells you: if it passes → the issue is in the task code (wrong SQL, permission problem). If it fails → the connection config is wrong or the DB is unreachable (wrong host, port blocked by firewall, wrong credentials). The Test Connection button runs from the webserver's network context — for worker-specific network issues, use `airflow connections test <conn_id>` from the CLI on the worker host.
</details>

**Q4**: How do you create connections programmatically in CI/CD without using the UI?
<details><summary>Answer</summary>
Three methods: (1) **Environment variable**: `AIRFLOW_CONN_MY_POSTGRES='postgresql://user:pass@host:5432/db'` — Airflow auto-creates the connection from this env var. Best for K8s deployments via Secrets. (2) **CLI**: `airflow connections add my_postgres --conn-type postgres --conn-host db.example.com --conn-port 5432 --conn-login user --conn-password pass --conn-schema db`. (3) **REST API**: `POST /api/v1/connections` with the connection JSON. For production, the environment variable approach is preferred — no DB write required, works with secrets managers.
</details>

### Quick Self-Rating
- [ ] I know all connection fields and when each is used
- [ ] I use Connections for credentials, not Variables
- [ ] I can create connections via CLI and env vars (not just UI)
- [ ] I understand Fernet encryption and why it's required
- [ ] I know when to use Secrets Manager backend vs UI-managed connections

---

## 📚 Further Reading

- [Airflow Connections Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html) — Official guide
- [Secrets Backend Configuration](https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/index.html) — AWS Secrets Manager, HashiCorp Vault
- [Fernet Key Setup](https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/fernet.html) — Encryption key management
- [Connection URI Format](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html#uri-format) — Environment variable connection strings
- [REST API — Connections](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#tag/Connection) — Programmatic connection management
