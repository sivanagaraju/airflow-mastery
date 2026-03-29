# Pip Install Guide — The Constraint File Pattern

> **Module 02 · Topic 02 · Explanation 01** — Installing Airflow with pip the right way

---

## Why Constraints Are Critical

Airflow depends on **500+ Python packages**. Without constraints, pip resolves the latest compatible version of each — which may not be tested together:

```
╔══════════════════════════════════════════════════════════════╗
║  WITHOUT CONSTRAINTS:                                        ║
║                                                              ║
║  pip install apache-airflow==2.10.4                         ║
║  → pip resolves flask==3.1 (latest)                         ║
║  → BUT Airflow 2.10.4 was tested with flask==2.3.3         ║
║  → ImportError: cannot import name 'escape' from flask      ║
║  → 🔥 BROKEN INSTALL                                       ║
║                                                              ║
║  WITH CONSTRAINTS:                                           ║
║                                                              ║
║  pip install apache-airflow==2.10.4 --constraint URL        ║
║  → pip MUST use flask==2.3.3 (pinned by constraint)        ║
║  → All 500+ dependencies pinned to tested versions          ║
║  → ✓ WORKING INSTALL                                       ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Step-by-Step Installation

```bash
# 1. Define versions
AIRFLOW_VERSION=2.10.4
PYTHON_VERSION="$(python3 --version | cut -d " " -f 2 | cut -d "." -f 1-2)"

# 2. Build the constraint URL
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# 3. Install Airflow with constraints
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# 4. Install provider packages (optional)
pip install "apache-airflow-providers-postgres" --constraint "${CONSTRAINT_URL}"

# 5. Verify installation
airflow version
```

---

## Post-Installation Setup

```bash
# Initialize the metadata database (SQLite by default)
airflow db migrate

# Create admin user
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Start webserver (in terminal 1)
airflow webserver --port 8080

# Start scheduler (in terminal 2)
airflow scheduler

# Access UI: http://localhost:8080
```

---

## Self-Assessment Quiz

**Q1**: A colleague installs Airflow with `pip install apache-airflow` (no constraints, no version pin). What could go wrong?
<details><summary>Answer</summary>Two problems: (1) No version pin — they get the latest Airflow version, which might not be compatible with their Python version or other installed packages, (2) No constraint file — pip resolves dependencies freely, potentially installing incompatible versions of Flask, SQLAlchemy, or Werkzeug. This leads to ImportErrors, AttributeErrors, or subtler bugs where tests pass but production fails. Always pin the Airflow version AND use the matching constraint file.</details>

### Quick Self-Rating
- [ ] I can install Airflow with the constraint file pattern
- [ ] I can explain why constraints are critical
- [ ] I can set up webserver + scheduler for local development
