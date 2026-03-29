# Local Install

```markmap
# Local Airflow Install (pip)
## Prerequisites
### Python 3.9+ (3.11 recommended)
### pip 21+
### Virtual environment (mandatory)
## Constraint Files (CRITICAL)
### Why: Airflow has 500+ dependencies
### Constraint URL pins compatible versions
### Without constraints: dependency hell
### Format: constraints-{VERSION}-{PYTHON}.txt
## Installation Steps
### Step 1: Create venv
#### python3 -m venv airflow-venv
### Step 2: Set AIRFLOW_HOME
#### export AIRFLOW_HOME=~/airflow
### Step 3: Install with constraints
#### pip install apache-airflow==2.10.4 --constraint URL
### Step 4: Initialize database
#### airflow db migrate
### Step 5: Create admin user
#### airflow users create
### Step 6: Start services
#### airflow webserver -p 8080
#### airflow scheduler
## Virtual Environments
### Why mandatory
#### Prevents system Python conflicts
#### Isolates Airflow dependencies
#### Reproducible setup
### Tools
#### venv (built-in, recommended)
#### virtualenv (pip install)
#### conda (data science teams)
#### pyenv (multiple Python versions)
## Docker vs pip
### Docker: Consistent, production-like, team standard
### pip: Faster startup, easier debugging, IDE integration
### Recommendation: Docker for projects, pip for learning
```
