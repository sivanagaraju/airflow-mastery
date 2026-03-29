"""
Demo: Task States — Observing the Task Lifecycle in Action
============================================================

This DAG creates tasks that intentionally succeed, fail, retry,
and get skipped so you can observe all major task states in the UI.

ARCHITECTURE:
    ┌──────────┐
    │  start   │
    └──┬───┬───┘
       │   │
       ▼   ▼
    ┌─────┐ ┌──────────┐
    │pass │ │fail_retry│ (fails once, succeeds on retry)
    └──┬──┘ └──┬───────┘
       │       │
       ▼       ▼
    ┌─────────────┐
    │  branch     │ (chooses path_a or path_b)
    └──┬──────┬───┘
       │      │
       ▼      ▼
    ┌──────┐ ┌──────┐
    │path_a│ │path_b│ (one will be SKIPPED)
    └──┬───┘ └──┬───┘
       │        │
       ▼        ▼
    ┌──────────────┐
    │    finish    │
    └──────────────┘

STATES YOU'LL SEE:
    - success (pass_task, the chosen branch)
    - up_for_retry then success (fail_then_retry)
    - skipped (the branch NOT chosen)
"""

from airflow.decorators import dag, task
from airflow.operators.empty import EmptyOperator
import pendulum
import random


@dag(
    dag_id="demo_task_states",
    description="Observe different task states: success, retry, skip",
    schedule=None,  # Manual trigger only
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["module-01", "task-lifecycle", "demo"],
    doc_md=__doc__,
    default_args={
        "owner": "airflow-mastery",
        "retries": 0,
    },
)
def demo_task_states():
    """
    Trigger this DAG manually, then check the Grid View to see:
    - Green (success) tasks
    - Orange (up_for_retry) then green (succeeded on retry) tasks
    - Pink (skipped) tasks from branching
    """

    start = EmptyOperator(task_id="start")
    finish = EmptyOperator(
        task_id="finish",
        trigger_rule="none_failed_min_one_success",
    )

    @task()
    def pass_task():
        """This task always succeeds — state will be SUCCESS (green)."""
        print("✓ This task succeeds immediately.")
        print("  State transition: none → scheduled → queued → running → success")
        return "passed"

    @task(retries=2, retry_delay=pendulum.duration(seconds=5))
    def fail_then_retry(**context):
        """
        This task fails on the first attempt and succeeds on retry.
        Watch the state: running → up_for_retry → scheduled → running → success
        """
        ti = context["task_instance"]
        attempt = ti.try_number

        if attempt == 1:
            print(f"  Attempt {attempt}: Simulating failure...")
            print("  State will become: up_for_retry")
            raise ValueError("Intentional failure on first attempt!")

        print(f"  Attempt {attempt}: Succeeding this time!")
        print("  State transition: up_for_retry → scheduled → running → success")
        return "retried_and_passed"

    @task.branch()
    def branch_task():
        """
        BranchPythonOperator: chooses one path.
        The other path's tasks will be SKIPPED (pink in UI).
        """
        choice = random.choice(["path_a", "path_b"])
        print(f"  Choosing: {choice}")
        print(f"  The other path will be SKIPPED (state=skipped)")
        return choice

    @task()
    def path_a():
        """If chosen: SUCCESS. If not chosen: SKIPPED."""
        print("  Path A was chosen!")

    @task()
    def path_b():
        """If chosen: SUCCESS. If not chosen: SKIPPED."""
        print("  Path B was chosen!")

    # Wire up the DAG
    pass_result = pass_task()
    retry_result = fail_then_retry()
    branch = branch_task()
    a = path_a()
    b = path_b()

    start >> [pass_result, retry_result]
    pass_result >> branch >> [a, b] >> finish
    retry_result >> finish


demo_task_states()
