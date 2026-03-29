# Local Install (pip)

> Module 02 · Topic 02 — Installing Airflow directly on your machine

---

## Sub-Topics

| # | File | What You'll Learn |
|---|------|-------------------|
| 01 | [Pip Install Guide](./explanation/01-pip-install.md) | Step-by-step pip installation with constraint files |
| 02 | [Virtual Environments](./explanation/02-virtual-environments.md) | Why you MUST use venv for Airflow |

---

## Quick Start

```bash
# Create virtual environment
python3 -m venv airflow-venv
source airflow-venv/bin/activate  # Linux/Mac
# airflow-venv\Scripts\activate   # Windows

# Set the home directory
export AIRFLOW_HOME=~/airflow

# Install Airflow with constraints (CRITICAL)
AIRFLOW_VERSION=2.10.4
PYTHON_VERSION="3.11"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# Initialize and start
airflow db migrate
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com
airflow webserver -p 8080 -D
airflow scheduler -D
```

---

## Study Path

1. Read 01-pip-install.md → 02-virtual-environments.md
2. Run [`demo_pip_verification.py`](./demos/demo_pip_verification.py)
3. Decision: Docker vs pip — use Docker for consistency, pip for debugging
