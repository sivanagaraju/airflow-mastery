# CLI Commands

> Module 03 · Topic 02 — Master Airflow operations from the command line

---

## Sub-Topics

| # | File | What You'll Learn |
|---|------|-------------------|
| 01 | [DAG Commands](./explanation/01-dag-commands.md) | List, trigger, pause, unpause, delete |
| 02 | [Task Commands](./explanation/02-task-commands.md) | Test, clear, state, render |
| 03 | [Connection Commands](./explanation/03-connection-commands.md) | Add, delete, list, export |
| 04 | [Maintenance Commands](./explanation/04-maintenance-commands.md) | DB clean, pools, users, config |

---

## Quick Reference

```bash
# Most-used commands
airflow dags list                    # List all DAGs
airflow dags trigger <dag_id>        # Manual trigger
airflow tasks test <dag> <task> <date>  # Test single task (no DB)
airflow dags backfill -s START -e END <dag>  # Backfill date range
```
