"""
Demo: Basic Airflow Concepts — DAG, Task, Operator in Action
=============================================================

This DAG demonstrates all core terminology in one working example:
- DAG definition (with context manager AND decorator style)
- Multiple operator types (Python, Bash, Empty)
- Task dependencies (>>, <<, chain)
- XCom data passing between tasks

ARCHITECTURE:
    ┌──────────────┐
    │   start      │  (EmptyOperator — no-op placeholder)
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │  check_date  │  (PythonOperator — prints execution info)
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │  run_bash    │  (BashOperator — runs a shell command)
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │  summarize   │  (@task decorator — reads XCom)
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │    end       │  (EmptyOperator — marks completion)
    └──────────────┘

CONCEPTS:
- 3 different operator types in one DAG
- Mix of traditional operator style and TaskFlow API
- EmptyOperator as DAG entry/exit points
- Automatic XCom via task return values
"""

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
import pendulum


def _check_execution_date(**context):
    """
    Traditional PythonOperator callable.

    Uses **context to access Airflow's runtime context:
    - context['logical_date']: the date this run represents
    - context['dag_run']: the DAG Run object
    - context['task_instance']: the current Task Instance
    """
    logical_date = context["logical_date"]
    dag_run = context["dag_run"]
    ti = context["task_instance"]

    print(f"  DAG ID:        {ti.dag_id}")
    print(f"  Task ID:       {ti.task_id}")
    print(f"  Run ID:        {dag_run.run_id}")
    print(f"  Logical Date:  {logical_date}")
    print(f"  Try Number:    {ti.try_number}")
    print(f"  Hostname:      {ti.hostname}")

    # Return value is automatically pushed to XCom
    return f"Checked at {logical_date.to_iso8601_string()}"


@dag(
    dag_id="demo_basic_concepts",
    description="Demonstrates DAG, Task, Operator — all core concepts",
    schedule="@daily",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["module-00", "terminologies", "demo"],
    doc_md=__doc__,
    default_args={
        "owner": "airflow-mastery",
        "retries": 1,
        "retry_delay": pendulum.duration(minutes=1),
    },
)
def demo_basic_concepts():
    """DAG showing multiple operator types and dependencies."""

    # 1. EmptyOperator — a no-op placeholder for DAG structure
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    # 2. PythonOperator — traditional style
    check_date = PythonOperator(
        task_id="check_date",
        python_callable=_check_execution_date,
    )

    # 3. BashOperator — runs a shell command
    run_bash = BashOperator(
        task_id="run_bash",
        bash_command='echo "Current working directory: $(pwd)" && echo "Date: $(date)"',
    )

    # 4. @task decorator — modern TaskFlow style
    @task()
    def summarize(check_result: str):
        """Summarize all concepts demonstrated in this DAG."""
        print("=" * 50)
        print("  CONCEPTS DEMONSTRATED:")
        print(f"  - EmptyOperator: start/end nodes")
        print(f"  - PythonOperator: {check_result}")
        print(f"  - BashOperator: ran a shell command")
        print(f"  - @task decorator: this function!")
        print(f"  - XCom: data passed between tasks")
        print("=" * 50)

    # Define dependencies using >> operator
    start >> check_date >> run_bash >> summarize(check_date.output) >> end


demo_basic_concepts()
