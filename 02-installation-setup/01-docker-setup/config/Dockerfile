# ============================================================
# Dockerfile — Custom Airflow Image
# ============================================================
# Use this when you need additional Python packages or system
# dependencies beyond what _PIP_ADDITIONAL_REQUIREMENTS provides.
#
# Build: docker build -t airflow-mastery .
# Then update docker-compose.yml to use:
#   build:
#     context: .
#     dockerfile: Dockerfile
# ============================================================

FROM apache/airflow:2.10.4-python3.11

# Switch to root for system package installation
USER root

# Install system dependencies (if needed)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user for pip installs
USER airflow

# Install Python dependencies from requirements.txt
COPY requirements.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt
