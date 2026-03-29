# Docker Compose Explained — Every Service Dissected

> **Module 02 · Topic 01 · Explanation 01** — Understanding every line of the Airflow docker-compose.yml

---

## 🎯 The Real-World Analogy: A Restaurant Kitchen

Think of Docker Compose as a **full-service restaurant** where each container is a specialized staff role:

| Container | Restaurant Role | Responsibility |
|-----------|----------------|----------------|
| `postgres` | The **filing cabinet** / records room | Stores every order, every action, every state |
| `airflow-webserver` | The **front-of-house manager** | Shows order status to customers via the UI |
| `airflow-scheduler` | The **executive chef** | Decides WHEN to cook what, and in what order |
| `airflow-triggerer` | The **expediter** (expo station) | Waits for delivery drivers without blocking the kitchen |
| `airflow-init` | The **morning prep crew** | Sets up before the restaurant opens (runs exactly once) |

Just as you can't serve food without prep crew finishing setup, you can't run Airflow without `airflow-init` completing first. The `depends_on` in docker-compose is equivalent to: "don't open doors until the chef says the kitchen is ready."

---

## Architecture Overview

```mermaid
graph TB
    subgraph "Docker Compose Stack"
        WS[airflow-webserver<br/>Port 8080] -->|reads state| DB[(postgres<br/>Port 5432)]
        SCHED[airflow-scheduler<br/>Parses DAGs] -->|reads/writes| DB
        TRIG[airflow-triggerer<br/>Deferrable tasks] -->|reads/writes| DB
        INIT[airflow-init<br/>One-time setup] -->|migrates schema| DB

        SCHED -->|local processes| TASKS[Task Execution<br/>LocalExecutor]
    end

    BROWSER[Browser] --> WS
    DAGS[dags/ folder<br/>mounted volume] --> SCHED

    style WS fill:#FF9800,color:#fff
    style SCHED fill:#4CAF50,color:#fff
    style TRIG fill:#2196F3,color:#fff
    style DB fill:#017CEE,color:#fff
    style INIT fill:#607D8B,color:#fff
```

```
Startup Sequence (depends_on chain):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [1] postgres ─► healthy?
  [2] airflow-init ─► runs db migrate + user create ─► exits 0
  [3] airflow-webserver ─► starts only after init exits cleanly
  [3] airflow-scheduler ─► starts only after init exits cleanly
  [3] airflow-triggerer ─► starts only after init exits cleanly
```

---

## The YAML Anchor Pattern

The compose file uses a YAML anchor (`&airflow-common`) to avoid repeating config:

```yaml
# Define shared config once
x-airflow-common:
  &airflow-common          # ← Anchor declaration
  image: apache/airflow:2.10.4
  environment:
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
  volumes:
    - ./dags:/opt/airflow/dags

# Reuse it in each service
services:
  airflow-webserver:
    <<: *airflow-common     # ← Merge the anchor (all keys copied here)
    command: webserver
    ports:
      - "8080:8080"
```

> **Key pattern**: The `x-` prefix makes it an extension field — Docker Compose ignores it during service creation but YAML processes it. The `<<: *airflow-common` syntax merges all keys from the anchor into the service, with service-specific keys taking precedence.

---

## Service-by-Service Breakdown

### 1. postgres (Metadata Database)

```
╔══════════════════════════════════════════════════════════════╗
║  SERVICE: postgres                                           ║
║                                                              ║
║  Image:     postgres:16                                      ║
║  Port:      5432 (exposed for debugging — remove in prod)   ║
║  Volume:    postgres-db-volume (named, persistent)          ║
║  Health:    pg_isready -U airflow                           ║
║                                                              ║
║  WHY:                                                        ║
║  The metadata DB stores ALL Airflow state. Uses a named     ║
║  volume so data persists across docker compose down/up.      ║
║  In production: use RDS, Cloud SQL, or Azure Database.      ║
╚══════════════════════════════════════════════════════════════╝
```

### 2. airflow-webserver

| Config | Value | Why |
|--------|-------|-----|
| `command` | `webserver` | Starts the Flask/Gunicorn UI server |
| `port` | `8080:8080` | UI accessible at `localhost:8080` |
| `healthcheck` | `curl /health` | Docker monitors webserver liveness |
| `depends_on` | `postgres`, `airflow-init` | Wait for DB init to complete first |

### 3. airflow-scheduler

The **most important** service. It:
- Scans `dags/` folder for Python files every `min_file_process_interval` seconds
- Parses each DAG and stores metadata in postgres
- Creates DAG Runs on schedule or on trigger
- Submits tasks to the executor (LocalExecutor forks subprocess)

### 4. airflow-triggerer (Airflow 2.2+)

Handles **deferrable operators** — tasks that wait for external events (S3 object upload, Snowflake query finish) without blocking a worker slot. Uses Python's `asyncio` event loop to multiplex thousands of waits on a single thread.

### 5. airflow-init (One-Time Setup)

Runs once to:
1. `airflow db migrate` — create/upgrade metadata database schema
2. `airflow users create` — create the default admin user
3. Writes `_AIRFLOW_DB_MIGRATE: 'true'` flag so other services know it's done

---

## Volume Mounts

| Local Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./dags/` | `/opt/airflow/dags/` | Your DAG Python files |
| `./logs/` | `/opt/airflow/logs/` | Task execution logs |
| `./plugins/` | `/opt/airflow/plugins/` | Custom operators, hooks |
| `./config/` | `/opt/airflow/config/` | airflow.cfg overrides |

---

## Environment Variables Pattern

Airflow uses a specific naming convention for env var overrides:

```
AIRFLOW__<SECTION>__<KEY>=<VALUE>

Examples:
AIRFLOW__CORE__EXECUTOR=LocalExecutor
  → maps to airflow.cfg [core] executor = LocalExecutor

AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://...
  → maps to airflow.cfg [database] sql_alchemy_conn = ...

AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL=30
  → maps to airflow.cfg [scheduler] min_file_process_interval = 30
```

Double underscores (`__`) separate the section from the key. This lets you override **any** airflow.cfg setting via environment variables with no file mounting required.

---

## 🏢 Real Company Use Cases

**Lyft** runs Airflow in a docker-compose-based environment for local developer onboarding. Their trick: the production stack (KubernetesExecutor + RDS) maps to LocalExecutor + postgres for local dev. Every engineer runs `docker compose up` and has an identical Airflow environment within minutes. This eliminated "works on my machine" bugs for data pipeline development.

**Booking.com** famously contributed improvements to the official `apache/airflow` Docker image. Their pattern: a separate postgres container per developer environment; Fernet keys managed via a `docker-compose.secrets.yml` file that is git-ignored and only present on provisioned machines. This approach ensures secrets are never in the repository while keeping the compose file fully functional.

**DataStax** uses the official docker-compose as a training environment for enterprise Airflow onboarding. Their innovation: parameterized the compose file so teams can switch from `LocalExecutor` (training) to `CeleryExecutor` (production simulation) by changing a single environment variable and uncommenting a Redis service block.

---

## ❌ Anti-Patterns

### Anti-Pattern 1: Using `_PIP_ADDITIONAL_REQUIREMENTS` in Production

```yaml
# ❌ BAD: pip install runs on EVERY container restart
environment:
  _PIP_ADDITIONAL_REQUIREMENTS: "pandas==2.1.0 scikit-learn==1.3.0 torch==2.1.0"
```

**Why it's bad**: 30-second to 5-minute startup delay per restart. PyPI must be reachable or container fails entirely. Subdependency version drift causes different behavior across restarts.

```dockerfile
# ✅ GOOD: Bake dependencies into a custom image — built once, fast always
FROM apache/airflow:2.10.4
USER airflow
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

```yaml
# docker-compose.yml — reference the custom image
services:
  airflow-webserver:
    image: my-org/airflow:2.10.4-custom  # No _PIP_ADDITIONAL_REQUIREMENTS
```

---

### Anti-Pattern 2: Hardcoding Secrets in docker-compose.yml

```yaml
# ❌ BAD: Password committed to Git forever
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: mypassword123   # Now in git history
  airflow-webserver:
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:mypassword123@postgres/airflow
```

```yaml
# ✅ GOOD: Reference variables from a .env file (add .env to .gitignore)
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  airflow-webserver:
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: ${AIRFLOW_DB_CONN}
```

```bash
# .env (NEVER commit this file)
POSTGRES_PASSWORD=mypassword123
AIRFLOW_DB_CONN=postgresql+psycopg2://airflow:mypassword123@postgres/airflow
AIRFLOW__CORE__FERNET_KEY=yourbase64fernetkey==
```

---

### Anti-Pattern 3: No Healthchecks — Race Condition on Startup

```yaml
# ❌ BAD: Only waits for container START, not postgres READY
services:
  airflow-init:
    depends_on:
      - postgres  # postgres container started, but DB not accepting connections yet!
```

**Why it fails**: postgres takes 2-5 seconds to become ready after starting. `airflow-init` starts immediately, tries to `db migrate`, and fails with "could not connect to server."

```yaml
# ✅ GOOD: Wait for healthcheck to pass before starting dependent services
services:
  airflow-init:
    depends_on:
      postgres:
        condition: service_healthy  # Waits for pg_isready to succeed

  postgres:
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 5s
```

---

## 🎤 Senior-Level Interview Q&A

**Q1: Why does the default docker-compose use LocalExecutor instead of CeleryExecutor?**

> LocalExecutor is simpler — it forks local Python subprocesses without requiring Redis, RabbitMQ, or Celery worker infrastructure. For local development and small production deployments (<100 concurrent tasks on a single machine), LocalExecutor is the right choice: fewer moving parts, simpler debugging, no message broker to configure. The trade-off: no horizontal scaling. Switch to CeleryExecutor when you need tasks distributed across multiple machines, or to KubernetesExecutor when you need task-level pod isolation.

**Q2: A DAG file was updated but the change isn't visible in the UI after 5 minutes. The scheduler is running. Walk me through your debugging process.**

> Systematic five-step debug: (1) **Volume check** — `docker compose exec airflow-scheduler ls /opt/airflow/dags/` to confirm the file is mounted. (2) **Parse error check** — `docker compose logs airflow-scheduler | grep -iE "error|import|syntax"`. (3) **Force parse** — `docker compose exec airflow-scheduler airflow dags list`. (4) **Timing check** — `min_file_process_interval` defaults to 30s; check `AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL`. (5) **DAG ID collision** — if another file has the same `dag_id`, one silently wins. Check `airflow dags list | grep dag_id`.

**Q3: An Airflow container shows `unhealthy` status and keeps restarting. How do you diagnose?**

> Start with inspection: `docker inspect <container_id> | jq '.[0].State.Health'` to see the last N healthcheck results and exit codes. Then `docker compose logs <service> --tail=100` for the service error. Common causes: (1) **postgres not ready** — webserver/scheduler can't connect to metadata DB; check if postgres is healthy first. (2) **Fernet key mismatch** — if the Fernet key changed after encrypted connections were stored, Airflow fails to decrypt and crashes. (3) **Port conflict** — another process using port 8080. (4) **Insufficient memory** — Docker Desktop RAM limit too low, OOM kill.

---

## 🏛️ Principal-Level Interview Q&A

**Q1: How would you evolve a single docker-compose.yml to support a team of 20 engineers with different customization needs?**

> Layer compose files using overrides. **Base file** (`docker-compose.yml`, committed): shared services, network definitions. **Developer override** (`docker-compose.override.yml`, git-ignored): local port mappings, debug flags, personal postgres credentials. **Team override** (`docker-compose.team.yml`, committed): shared provider packages, team-specific environment variables. Unify with a `Makefile`: `make dev` runs `docker compose -f docker-compose.yml -f docker-compose.override.yml up`. Add pre-commit hooks that run `docker compose config` to validate the merged config. Key principle: never put secrets in committed files, never put mandatory config in git-ignored files.

**Q2: This docker-compose setup handles 5 engineers fine but breaks at 50 concurrent DAG runs. What's the upgrade path?**

> The bottleneck is LocalExecutor — single machine, limited parallelism. Graduated upgrade path: **(1) Tune first**: increase `parallelism`, `max_active_tasks_per_dag`, allocate more Docker Desktop memory. **(2) CeleryExecutor**: add Redis or RabbitMQ to the compose file, add `airflow-worker` services (can run multiple), add Celery Flower for worker monitoring. Now you can run multiple scheduler replicas. **(3) KubernetesExecutor**: retire the compose file for production, move to Helm chart. Each task gets its own Kubernetes pod — true horizontal scale. **(4) Managed Airflow**: Amazon MWAA, Google Cloud Composer, or Astronomer for teams who want zero infra management. The postgres container also needs replacing with managed RDS/Cloud SQL at scale.

**Q3: Security audit flags that postgres port 5432 is exposed in your docker-compose.yml. How do you fix it and what broader security conversation should follow?**

> **Immediate fix**: remove `ports: - "5432:5432"` from the postgres service. Containers on the same Docker network communicate without host-port exposure. **Broader security posture**: (1) **Network segmentation** — create dedicated `airflow-backend` network with `internal: true`, only attach postgres and scheduler to it; webserver only on the frontend network. (2) **Secret management** — replace env var secrets with Docker secrets (`secrets:` block) or HashiCorp Vault via the secrets backend. (3) **Fernet key rotation** — implement a Fernet key rotation policy (Airflow supports `fernet_key_cmd` for dynamic retrieval). (4) **Image CVEs** — run `docker scout cves apache/airflow:2.10.4` in CI and block deployments with critical CVEs. (5) **Read-only DAGs** — mount the DAGs volume as `read_only: true` in all services except CI/CD deployment.

---

## 📝 Self-Assessment Quiz

**Q1**: You update a DAG file but the change doesn't appear in the UI. The scheduler container is running. What is the FIRST thing you check?
<details><summary>Answer</summary>
Whether the file is visible inside the container: `docker compose exec airflow-scheduler ls /opt/airflow/dags/`. If the file isn't there, it's a volume mount problem (e.g., the file is in the wrong directory on the host). If it is there, check for parse errors: `docker compose logs airflow-scheduler | grep ERROR`. If no errors, wait up to 30 seconds (the default re-parse interval).
</details>

**Q2**: What does `condition: service_healthy` do in `depends_on`, and why is it better than plain `depends_on: postgres`?
<details><summary>Answer</summary>
Plain `depends_on` only waits for the container to *start* (the process is launched). `condition: service_healthy` waits until the healthcheck command defined in the service passes. For postgres, this means `pg_isready` returns 0 before any dependent service starts. Without it, airflow-init frequently fails with "could not connect to server" because postgres needs 2-5 seconds after container start to accept connections.
</details>

**Q3**: Why is `airflow-init` an ephemeral service that exits instead of a long-running one?
<details><summary>Answer</summary>
`airflow-init` performs one-time setup tasks (db migrate, user create) that must run exactly once before other services start, and then stop. Making it ephemeral means: (1) It doesn't consume resources after setup. (2) `restart: on-failure` makes it retry on DB connection issues, but exit cleanly on success. (3) Other services can use `condition: service_completed_successfully` to know setup finished. If it were long-running, you'd have no clear "setup is done" signal.
</details>

**Q4**: You need to add CeleryExecutor to this docker-compose.yml. List every change required.
<details><summary>Answer</summary>
Six changes: (1) Add `redis` service (`image: redis:7-alpine` with healthcheck). (2) Change `AIRFLOW__CORE__EXECUTOR` to `CeleryExecutor`. (3) Add `AIRFLOW__CELERY__BROKER_URL: redis://redis:6379/0`. (4) Add `AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow`. (5) Add `airflow-worker` service with `command: celery worker` (can add multiple). (6) Optionally add `flower` service for Celery monitoring UI on port 5555. All YAML anchor services need `depends_on: redis` added.
</details>

### Quick Self-Rating
- [ ] I can explain every service in the docker-compose.yml from memory
- [ ] I can explain the YAML anchor (`&`) and merge (`<<:`) pattern
- [ ] I can override any airflow.cfg setting via environment variables
- [ ] I can debug a DAG not appearing in the UI systematically
- [ ] I can explain the security implications of the default docker-compose setup

---

## 📚 Further Reading

- [Official Airflow Docker Compose Guide](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html) — The source of truth for setup
- [Docker Compose Override Files](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/) — Team customization patterns
- [Airflow Docker Stack Documentation](https://airflow.apache.org/docs/docker-stack/index.html) — Production-ready image customization
- [CeleryExecutor Setup Guide](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/celery.html) — Scaling beyond LocalExecutor
- [Docker Healthcheck Best Practices](https://docs.docker.com/engine/reference/builder/#healthcheck) — Designing robust startup sequences
