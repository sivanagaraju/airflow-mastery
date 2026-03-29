"""
Demo: UI Exploration DAG — Designed to Showcase All UI Views
==============================================================

Deploy this DAG and use it to explore every Airflow UI view:
- Grid View: see the task matrix
- Graph View: see the dependency structure
- Gantt Chart: identify the bottleneck task
- Task Instance: check logs, XCom, rendered templates

ARCHITECTURE:
    ┌──────────┐
    │  start   │
    └──┬───┬───┘
       │   │
       ▼   ▼
    ┌────┐ ┌────────┐
    │fast│ │ slow   │ (intentionally slow for Gantt demo)
    └─┬──┘ └──┬─────┘
      │       │
      ▼       ▼
    ┌────────────┐
    │   merge    │ (reads XCom from both)
    └─────┬──────┘
          │
    ┌─────▼──────┐
    │   branch   │ (BranchPythonOperator)
    └──┬─────┬───┘
       │     │
       ▼     ▼
    ┌────┐ ┌────┐
    │ ok │ │skip│ (one will be skipped)
    └─┬──┘ └─┬──┘
      │      │
      ▼      ▼
    ┌────────────┐
    │   finish   │ (trigger_rule: none_failed_min_one_success)
    └────────────┘
"""

from airflow.decorators import dag, task
from airflow.operators.empty import EmptyOperator
import pendulum
import time
import random


@dag(
    dag_id="demo_ui_exploration",
    description="Explore all Airflow UI views with this demo DAG",
    schedule="@daily",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["module-03", "ui-tour", "demo"],
    doc_md=__doc__,
    default_args={
        "owner": "airflow-mastery",
        "retries": 1,
        "retry_delay": pendulum.duration(seconds=10),
    },
)
def demo_ui_exploration():
    """Trigger this DAG and explore each UI view."""

    start = EmptyOperator(task_id="start")
    finish = EmptyOperator(
        task_id="finish",
        trigger_rule="none_failed_min_one_success",
    )

    @task()
    def fast_task():
        """Completes quickly — useful for Gantt chart comparison."""
        print("  Fast task: processing 100 records")
        time.sleep(2)  # 2 seconds
        return {"task": "fast", "records": 100, "duration_sec": 2}

    @task()
    def slow_task():
        """
        Intentionally slow — Gantt chart will show this as the bottleneck.
        Check the Gantt view to see this bar is longest.
        """
        duration = random.randint(8, 15)
        print(f"  Slow task: processing 10,000 records (simulating {duration}s)")
        time.sleep(duration)
        return {"task": "slow", "records": 10000, "duration_sec": duration}

    @task()
    def merge_results(fast_data: dict, slow_data: dict):
        """
        Merges data from both upstream tasks.
        Check <XCom tab> in Task Instance to see the input values.
        """
        total = fast_data["records"] + slow_data["records"]
        print(f"  Merged: {total} total records")
        print(f"  Fast took {fast_data['duration_sec']}s")
        print(f"  Slow took {slow_data['duration_sec']}s")
        return {"total_records": total}

    @task.branch()
    def decide_path():
        """
        Check Graph View to see which path is chosen (green) 
        and which is skipped (pink).
        """
        choice = random.choice(["path_ok", "path_skip"])
        print(f"  Decision: {choice}")
        return choice

    @task()
    def path_ok():
        """This path runs if chosen by the branch."""
        print("  OK path executed!")

    @task()
    def path_skip():
        """This path runs if chosen by the branch."""
        print("  Skip path executed!")

    # Wire the DAG
    fast = fast_task()
    slow = slow_task()
    merged = merge_results(fast, slow)
    branch = decide_path()
    ok = path_ok()
    skip = path_skip()

    start >> [fast, slow]
    merged >> branch >> [ok, skip] >> finish


demo_ui_exploration()
