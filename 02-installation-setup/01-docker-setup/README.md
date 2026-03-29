# Docker Setup for Airflow

> Module 02 · Topic 01 — The recommended way to run Airflow locally and in production

---

## Why Docker?

Docker provides a **consistent, reproducible** environment identical to production. No more "works on my machine."

---

## Sub-Topics

| # | File | What You'll Learn |
|---|------|-------------------|
| 01 | [Docker Compose Explained](./explanation/01-docker-compose-explained.md) | Every service in the compose file |
| 02 | [Airflow Directories](./explanation/02-airflow-directories.md) | dags/, logs/, plugins/ structure |
| 03 | [Configuration Files](./explanation/03-configuration-files.md) | .env, airflow.cfg, webserver_config.py |
| 04 | [Custom Dockerfile](./explanation/04-dockerfile-custom.md) | Adding Python packages and system deps |

---

## Quick Start

```bash
# 1. Navigate to the config directory
cd 02-installation-setup/01-docker-setup/config/

# 2. Create required directories
mkdir -p ./dags ./logs ./plugins ./config

# 3. Set the Airflow user ID (Linux only)
echo -e "AIRFLOW_UID=$(id -u)" > .env

# 4. Initialize the database
docker compose up airflow-init

# 5. Start all services
docker compose up -d

# 6. Access the UI
# Open http://localhost:8080 (admin / admin)
```

---

## Study Path

1. Read explanations 01 → 04
2. Use the config files in `config/` to spin up Airflow
3. Run [`demo_verify_installation.py`](./demos/demo_verify_installation.py)
4. Verify: can you see your demo DAG in the UI?
