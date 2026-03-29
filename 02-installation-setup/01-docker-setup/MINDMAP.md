# Docker Setup

```markmap
# Docker Setup for Airflow
## Docker Compose Services
### postgres (Metadata DB)
#### PostgreSQL 16
#### Named volume for persistence
#### Port 5432
### airflow-webserver
#### Flask + Gunicorn
#### Port 8080
#### Healthcheck: /health endpoint
### airflow-scheduler
#### DAG file parsing
#### DAG Run creation
#### Task scheduling
### airflow-triggerer
#### Deferrable operator support
#### asyncio event loop
### airflow-init
#### One-time database migration
#### Admin user creation
## Volume Mounts
### ./dags/ → /opt/airflow/dags/
### ./logs/ → /opt/airflow/logs/
### ./plugins/ → /opt/airflow/plugins/
### ./config/ → /opt/airflow/config/
## Configuration
### Environment Variables
#### AIRFLOW__SECTION__KEY=VALUE pattern
#### Override any airflow.cfg setting
### YAML Anchors
#### x-airflow-common shared config
#### <<: *airflow-common merging
### .env File
#### AIRFLOW_UID for permissions
#### _PIP_ADDITIONAL_REQUIREMENTS
## Dockerfile Custom
### FROM apache/airflow:2.10.4-python3.11
### System deps as root
### Python deps as airflow user
### requirements.txt install
## Commands
### docker compose up airflow-init
### docker compose up -d
### docker compose down
### docker compose logs -f
### docker compose exec airflow-scheduler bash
```
