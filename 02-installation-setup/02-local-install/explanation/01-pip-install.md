# Pip Install Guide — The Constraint File Pattern

> **Module 02 · Topic 02 · Explanation 01** — Installing Airflow with pip the right way, every time

---

## 🎯 The Real-World Analogy: Building a House from a Blueprint

Installing Airflow without constraints is like **building a house and letting each contractor choose their own materials**:

| Without Constraints | With Constraints |
|---------------------|-----------------|
| Plumber orders any HDPE pipe brand | Blueprint specifies "Brand X, 3/4 inch Schedule 40" |
| Electrician picks any breaker brand | Blueprint specifies "Siemens Q-series, 15A" |
| Result: pipes don't connect to fittings | Result: everything fits perfectly |

The Airflow constraints file is the **blueprint's material spec sheet** — it says exactly which version of every one of 500+ packages must be used, because the Apache team tested that exact combination together. Deviate from the spec, and something won't fit.

---

## Why Constraints Are Critical

Airflow depends on **500+ Python packages**. Without constraints, pip resolves the latest compatible version of each — which may not be tested together:

```
╔══════════════════════════════════════════════════════════════╗
║  WITHOUT CONSTRAINTS:                                        ║
║                                                              ║
║  pip install apache-airflow==2.10.4                        ║
║  → pip resolves flask==3.1 (latest)                        ║
║  → BUT Airflow 2.10.4 was tested with flask==2.3.3        ║
║  → ImportError: cannot import name 'escape' from flask     ║
║  → 🔥 BROKEN INSTALL after 2 hours of debugging           ║
║                                                              ║
║  WITH CONSTRAINTS:                                          ║
║                                                              ║
║  pip install apache-airflow==2.10.4 --constraint URL       ║
║  → pip MUST use flask==2.3.3 (pinned by constraint)       ║
║  → All 500+ dependencies pinned to tested versions         ║
║  → ✓ WORKING INSTALL in 3 minutes                         ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Constraint URL Structure

The constraint file URL is deterministic and predictable:

```
https://raw.githubusercontent.com/apache/airflow/constraints-{AIRFLOW_VERSION}/constraints-{PYTHON_VERSION}.txt

Examples:
  Airflow 2.10.4 + Python 3.11:
  https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.11.txt

  Airflow 2.9.3 + Python 3.10:
  https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.10.txt
```

```
╔══════════════════════════════════════════════════════════════╗
║  Constraint file naming convention:                          ║
║                                                              ║
║  constraints-{version}.txt    ← All packages including pip  ║
║  constraints-no-providers-{version}.txt  ← Core only       ║
║  constraints-source-providers-{version}.txt ← Dev use      ║
║                                                              ║
║  Always use: constraints-{version}.txt for production       ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Step-by-Step Installation

```bash
#!/bin/bash
# ── Step 1: Define versions ──
AIRFLOW_VERSION=2.10.4
PYTHON_VERSION="$(python3 --version | cut -d " " -f 2 | cut -d "." -f 1-2)"

echo "Installing Airflow ${AIRFLOW_VERSION} for Python ${PYTHON_VERSION}"

# ── Step 2: Build the constraint URL ──
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

echo "Using constraints: ${CONSTRAINT_URL}"

# ── Step 3: Install Airflow with constraints ──
pip install "apache-airflow==${AIRFLOW_VERSION}" \
    --constraint "${CONSTRAINT_URL}"

# ── Step 4: Install provider packages (use SAME constraint URL) ──
pip install \
    "apache-airflow-providers-postgres==5.11.2" \
    "apache-airflow-providers-amazon==8.17.0" \
    "apache-airflow-providers-snowflake==4.4.2" \
    --constraint "${CONSTRAINT_URL}"

# ── Step 5: Verify installation ──
airflow version
python -c "import airflow; print(f'Airflow {airflow.__version__} installed successfully')"
```

---

## Post-Installation Setup

```bash
# ── Set AIRFLOW_HOME (default: ~/airflow) ──
export AIRFLOW_HOME=~/airflow

# ── Initialize the metadata database ──
# Dev: SQLite (default, OK for one person)
airflow db migrate

# ── Create admin user ──
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# ── Start webserver (terminal 1) ──
airflow webserver --port 8080

# ── Start scheduler (terminal 2) ──
airflow scheduler

# ── Access UI ──
# http://localhost:8080  (admin / admin)
```

---

## Installing Extra Packages (Extras)

Airflow uses "extras" to pull in provider dependencies:

```bash
# Install with specific extras
pip install "apache-airflow[postgres,amazon,slack,celery]==${AIRFLOW_VERSION}" \
    --constraint "${CONSTRAINT_URL}"

# Available extras examples:
# amazon   → AWS S3, RDS, Glue, EMR, etc.
# google   → GCS, BigQuery, Cloud Composer, etc.
# microsoft.azure → Azure Blob, Data Factory, etc.
# snowflake → Snowflake operators and hooks
# celery   → CeleryExecutor support
# kubernetes → KubernetesPodOperator

# ⚠️ Always use the constraint file even when adding extras!
```

---

## 🏢 Real Company Use Cases

**Airbnb** (the Airflow creators) published the constraint file pattern as the canonical installation method after engineers repeatedly hit broken pip environments when pip resolved dependency conflicts differently on different machines. Their internal onboarding script is a 20-line bash script that mirrors the pattern above, pinning both the Airflow version and the constraint URL. New data engineers run a working Airflow install in under 5 minutes.

**Spotify** maintains an internal PyPI mirror that caches the Airflow constraint file and all approved packages. This serves two purposes: (1) Faster installs — packages come from the corporate network, not the public internet. (2) Security approval gating — only packages that have passed CVE scanning appear in the internal mirror. Their `pip install` command points at `https://pypi.spotify.internal/simple/` instead of pypi.org.

**Wise (TransferWise)** ran into a production incident where Airflow's `flask-login` was upgraded automatically (no constraint file in their original setup). The UI stopped working for 4 hours during peak tax season. After root-cause analysis, they migrated all environments to use constraint files and added a pre-commit hook that enforces `--constraint` in any shell script that installs Airflow.

---

## ❌ Anti-Patterns

### Anti-Pattern 1: Installing Airflow Without a Version Pin or Constraint File

```bash
# ❌ BAD: No version pin, no constraint file
pip install apache-airflow

# What happens:
# - Gets latest Airflow version (may be untested for your Python version)
# - pip resolves all 500+ dependencies freely
# - Works today, breaks tomorrow when any dependency releases a new version
# - Cannot reproduce this environment 6 months later for debugging
```

```bash
# ✅ GOOD: Always pin version AND use constraint file
AIRFLOW_VERSION=2.10.4
PYTHON_VERSION="$(python3 --version | cut -d " " -f 2 | cut -d "." -f 1-2)"

pip install "apache-airflow==${AIRFLOW_VERSION}" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
```

---

### Anti-Pattern 2: Installing Provider Packages WITHOUT the Constraint File

```bash
# ❌ BAD: Airflow installed with constraints, provider added without
pip install "apache-airflow==2.10.4" --constraint "${CONSTRAINT_URL}"
# Later...
pip install apache-airflow-providers-snowflake  # No constraint! pip upgrades shared deps
# → apache-airflow-providers-snowflake pulls pyarrow==15.0 (latest)
# → But constraint file pinned pyarrow==14.0.2
# → Conflict breaks the next Airflow restart
```

```bash
# ✅ GOOD: Always use the SAME constraint file for providers
pip install "apache-airflow-providers-snowflake==4.4.2" \
    --constraint "${CONSTRAINT_URL}"  # Same URL used for Airflow itself
```

---

### Anti-Pattern 3: Installing Airflow with `--upgrade` in an Existing Environment

```bash
# ❌ BAD: Upgrading in place without re-applying constraints
pip install --upgrade apache-airflow  # Upgrades Airflow AND resolves new deps freely
# → Airflow jumps from 2.9 to 2.10
# → 2.10 needs different flask version
# → pip upgrades flask, now 2.9-compatible operators break
# → Provider packages are now on mismatched versions
```

```bash
# ✅ GOOD: Create a NEW virtual environment for Airflow upgrades
# Never upgrade Airflow in place — always start fresh and migrate
python3 -m venv ~/airflow-2.10-venv
source ~/airflow-2.10-venv/bin/activate

pip install "apache-airflow==2.10.4" \
    --constraint "${NEW_CONSTRAINT_URL}"

# Run DB migration
airflow db migrate

# Verify all DAGs still work before switching over
airflow dags list
```

---

## 🎤 Senior-Level Interview Q&A

**Q1: A colleague installs Airflow with `pip install apache-airflow` — no version pin, no constraints. What are the risks?**

> Three concrete risks: **(1) Non-reproducibility** — different machines resolve different dependency trees because pip's resolution algorithm is non-deterministic across environments. What works on your laptop may fail on the CI machine. **(2) Future breakage** — when Flask releases 4.0 with breaking API changes, the next `pip install --upgrade` pulls it in and breaks the Airflow UI. **(3) Debug hell** — when troubleshooting, you can't tell others "use the same environment" because there is no pinned spec. Fix: always use `pip freeze > requirements.txt` after installation, and always use the official constraint file on the initial install.

**Q2: You need to add the Snowflake provider to a running Airflow environment. How do you do it safely?**

> Never `pip install apache-airflow-providers-snowflake` alone. The steps: (1) Note the running Airflow version (`airflow version`). (2) Get the constraint URL for that version and Python version. (3) Install: `pip install "apache-airflow-providers-snowflake==4.4.2" --constraint "${CONSTRAINT_URL}"`. Same constraint URL prevents pip from upgrading shared dependencies like `pyarrow` or `cryptography` that the provider and Airflow core share. (4) After install: `airflow providers list | grep snowflake` to confirm. (5) In Docker/Kubernetes: add to `requirements.txt` and rebuild the custom image — don't pip install into running containers.

**Q3: The `airflow db migrate` command fails with "table already exists." What happened?**

> This occurs when `airflow db migrate` was run before (the DB already has Airflow schema) but either: (1) The Airflow version downgraded — `db migrate` is forward-only; you can't migrate to a lower version. (2) A concurrent `db migrate` ran simultaneously, causing a race condition. (3) Manual SQL was run against the metadata DB that created unexpected table state. Fix: check `airflow db check` to see current DB status. For a dev environment, `airflow db reset` (destructive — deletes all data) then re-migrate. For production, compare the current alembic revision (`alembic current`) against the expected revision for your Airflow version.

---

## 🏛️ Principal-Level Interview Q&A

**Q1: You are setting up Airflow for 200 data engineers. How do you ensure consistent, reproducible pip installs across all machines and CI environments?**

> **Three-layer strategy**: **(1) Internal PyPI mirror** — proxy pypi.org through Nexus or Artifactory with security scanning. All installs use `--index-url https://pypi.internal.company.com/simple/`. This provides: faster installs (corporate network), security gating (CVE-blocked packages never reach engineers), and air-gap support for regulated environments. **(2) Blessed requirements file** — platform team maintains `company-airflow-requirements.txt` with every package pinned, including the full `pip freeze` output. Engineers install from this file only. CI validates the file daily against the constraint file. **(3) Standard onboarding script** — a Makefile target `make airflow-setup` that creates the venv, runs the install with the correct constraint URL, and validates the installation with a quick smoke test. No engineer installs manually.

**Q2: The team wants to move from local pip installs to Docker-based Airflow. How do you manage the transition while maintaining the constraint discipline?**

> The constraint discipline maps directly: local `pip install --constraint URL` → `COPY requirements.txt; RUN pip install --constraint URL` in the Dockerfile. Migration plan: (1) **Audit current installs** — `pip freeze` across all engineer environments to find the "union" of packages in use. (2) **Create `requirements.txt`** — add all team packages, run against the constraint file to verify compatibility. (3) **Build custom base image** — Dockerfile starting from `apache/airflow:2.10.4` with the requirements installed via constraint file. (4) **CI validation** — every PR to `requirements.txt` triggers an image build + `airflow dags list` smoke test. (5) **Parallel run period** — both local and Docker environments run for 2 weeks while engineers migrate. Document "if your DAG uses library X, verify it's in requirements.txt" in the onboarding guide.

**Q3: Airflow releases a security patch (2.10.4 → 2.10.5). How do you roll it out to 3 environments with zero data loss and minimal downtime?**

> **Staged rollout with validation gates**: **(Step 1 — Dev)**: Update `AIRFLOW_VERSION=2.10.5` in the constraint URL, rebuild the custom image, deploy to dev. Run `airflow db migrate`. Monitor for 24 hours — check DAG success rates, scheduler heartbeat, UI responsiveness. **(Step 2 — Staging)**: Same process with production-like load (restored from a recent prod DB snapshot). Automated regression: run `airflow dags list` + top-10 critical DAGs via `airflow dags trigger`. **(Step 3 — Production)**: During low-traffic window, pause the scheduler (`airflow scheduler stop` or scale to 0 in K8s). Deploy new image. Run `airflow db migrate` (2.10.x migrations are additive, backward-compatible). Restart scheduler. **Rollback plan**: Previous image tag kept in registry. If `airflow db migrate` hasn't run, rollback is instant (just repoint to old image). If migration ran, use the DB snapshot taken before the upgrade.

---

## 📝 Self-Assessment Quiz

**Q1**: A colleague installs Airflow with `pip install apache-airflow` (no version pin, no constraints). What are the two specific risks?
<details><summary>Answer</summary>
(1) **Non-reproducibility** — pip resolves different dependency versions on different machines/times, meaning the same command produces different environments. Installing today and tomorrow may produce different results. (2) **Version drift / future breakage** — when any of the 500+ dependencies releases an incompatible update, the next `pip install` or environment rebuild pulls it in and breaks Airflow. Always pin with `==` and always use the constraint file.
</details>

**Q2**: What is the exact constraint URL pattern for Airflow 2.10.4 on Python 3.11?
<details><summary>Answer</summary>
`https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.11.txt`

Pattern: `https://raw.githubusercontent.com/apache/airflow/constraints-{AIRFLOW_VERSION}/constraints-{PYTHON_VERSION}.txt`

Always use the constraint file that matches BOTH the Airflow version AND the Python version you're using.
</details>

**Q3**: You need to add the `amazon` provider after Airflow is already installed. How do you do it safely?
<details><summary>Answer</summary>
Use the SAME constraint URL that was used for the original Airflow install:

```bash
AIRFLOW_VERSION=2.10.4
PYTHON_VERSION="$(python3 --version | cut -d " " -f 2 | cut -d "." -f 1-2)"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

pip install "apache-airflow-providers-amazon==8.17.0" --constraint "${CONSTRAINT_URL}"
```

Using `--constraint` prevents pip from upgrading shared dependencies (like `boto3`, `cryptography`) to versions incompatible with the rest of the Airflow install.
</details>

**Q4**: `airflow db migrate` fails. What are the three most common causes?
<details><summary>Answer</summary>
(1) **Database not reachable** — the `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` connection string is wrong or the DB server isn't running. Check: `airflow db check`. (2) **Downgrade attempt** — `db migrate` only runs forward (newer schema versions). If you try to use Airflow 2.9 on a DB that was migrated by Airflow 2.10, it fails. Fix: use the same or newer Airflow version as what ran the migration. (3) **Concurrent migration conflict** — two `db migrate` processes ran simultaneously (race condition during parallel container startup). Fix: ensure only `airflow-init` runs `db migrate` and other services use `condition: service_completed_successfully` in `depends_on`.
</details>

### Quick Self-Rating
- [ ] I can install Airflow with the constraint file pattern from memory
- [ ] I can explain specifically why constraints are critical (not just "they pin versions")
- [ ] I can add a provider package safely to an existing Airflow install
- [ ] I can run `airflow db migrate` and troubleshoot failures
- [ ] I can set up webserver + scheduler for local development

---

## 📚 Further Reading

- [Official Airflow Installation Guide](https://airflow.apache.org/docs/apache-airflow/stable/installation/installing-from-pypi.html) — The source of truth for pip install
- [Airflow Constraints Explained](https://airflow.apache.org/docs/apache-airflow/stable/installation/installing-from-pypi.html#constraints-files) — Why constraints exist and how they work
- [Airflow Extras and Providers](https://airflow.apache.org/docs/apache-airflow/stable/installation/dependencies.html) — What each extra installs
- [pip Dependency Resolution](https://pip.pypa.io/en/stable/topics/dependency-resolution/) — How pip resolves dependencies (and why it can go wrong)
