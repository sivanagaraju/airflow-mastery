# Virtual Environments — Why They're Mandatory for Airflow

> **Module 02 · Topic 02 · Explanation 02** — Never install Airflow in your system Python

---

## The Problem Without venv

```
╔══════════════════════════════════════════════════════════════╗
║  DISASTER SCENARIO (system Python):                          ║
║                                                              ║
║  System Python 3.11                                          ║
║  ├── flask 2.3.3 (required by Airflow)                      ║
║  ├── flask 3.0.0 (required by your web app)  ← CONFLICT!   ║
║  ├── sqlalchemy 1.4.51 (required by Airflow)                ║
║  ├── sqlalchemy 2.0.25 (required by FastAPI) ← CONFLICT!   ║
║  └── 498 more packages fighting for dominance              ║
║                                                              ║
║  Result: Something breaks — maybe Airflow, maybe your app.  ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Virtual Environment Options

| Tool | Install | Best For |
|------|---------|---------|
| **venv** (built-in) | `python3 -m venv myenv` | Standard, no extra tools |
| **virtualenv** | `pip install virtualenv` | Faster, more features |
| **conda** | `conda create -n myenv` | Data science teams |
| **pyenv + venv** | `pyenv install 3.11` | Multiple Python versions |

---

## Recommended Setup

```bash
# Create dedicated Airflow environment
python3.11 -m venv ~/airflow-venv

# Activate (every time you work with Airflow)
source ~/airflow-venv/bin/activate    # Linux/Mac
# ~/airflow-venv/Scripts/activate      # Windows

# Your prompt changes:
# (airflow-venv) user@host:~$

# Set AIRFLOW_HOME
export AIRFLOW_HOME=~/airflow

# Install Airflow here
pip install "apache-airflow==2.10.4" --constraint "${CONSTRAINT_URL}"

# Deactivate when done
deactivate
```

---

## Self-Assessment Quiz

**Q1**: Can you have two different Airflow versions installed simultaneously?
<details><summary>Answer</summary>Yes — using separate virtual environments. Create `venv-2.9` with Airflow 2.9 and `venv-2.10` with Airflow 2.10. Activate the one you need. This is useful for testing DAG compatibility during version upgrades.</details>

### Quick Self-Rating
- [ ] I understand why system Python + Airflow = disaster
- [ ] I can create and manage virtual environments
- [ ] I can maintain multiple Airflow versions side by side
