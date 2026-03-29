"""
Solution 01: Identify and Label Airflow Components
====================================================

SOLUTION for: exercises/Ex01_IdentifyComponents.py

ARCHITECTURE:
    ┌────────────┐   ┌─────────────┐   ┌────────────┐   ┌────────────┐
    │ dag_entry  │ → │ show_context│ → │ bash_action│ → │ explain_ti │
    │ (Empty)    │   │ (Python)    │   │ (Bash)     │   │ (@task)    │
    └────────────┘   └─────────────┘   └────────────┘   └────────────┘

KEY LEARNINGS:
    - EmptyOperator is an Action Operator (does nothing, just marks a point)
    - PythonOperator is an Action Operator (runs a Python callable)
    - BashOperator is an Action Operator (runs a bash command)
    - @task decorator creates a PythonOperator under the hood
"""

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
import pendulum


def _show_context(**context):
    """
    Action Operator (PythonOperator).

    Demonstrates accessing the Airflow runtime context to understand
    the difference between a Task (definition) and Task Instance (execution).
    """
    ti = context["task_instance"]
    logical_date = context["logical_date"]

    print("=" * 50)
    print("  AIRFLOW COMPONENT IDENTIFICATION")
    print("=" * 50)
    print(f"  DAG ID (DAG):            {ti.dag_id}")
    print(f"  Task ID (Task):          {ti.task_id}")
    print(f"  Run ID (DAG Run):        {context['dag_run'].run_id}")
    print(f"  Logical Date:            {logical_date}")
    print(f"  Try Number (Instance):   {ti.try_number}")
    print(f"  Operator:                PythonOperator")
    print(f"  Category:                Action Operator")
    print("=" * 50)

    return f"Context shown for {ti.task_id} at {logical_date}"


@dag(
    dag_id="ex01_identify_components",
    description="Exercise: Identify and label all Airflow components",
    schedule="@daily",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["exercise", "module-00"],
    default_args={
        "owner": "airflow-mastery",
        "retries": 1,
    },
)
def ex01_identify_components():
    """Demonstrates all core Airflow components in one DAG."""

    # Task 1: EmptyOperator — marks the DAG entry point
    dag_entry_point = EmptyOperator(
        task_id="dag_entry_point",
        doc="EmptyOperator: Action Operator that does nothing. "
            "Used as a structural placeholder in DAG design.",
    )

    # Task 2: PythonOperator — shows runtime context
    show_context = PythonOperator(
        task_id="show_context",
        python_callable=_show_context,
        doc="PythonOperator: Action Operator that runs a Python function. "
            "Accesses **context to read task metadata.",
    )

    # Task 3: BashOperator — echoes its identity
    bash_action = BashOperator(
        task_id="bash_action",
        bash_command=(
            'echo "================================" && '
            'echo "  I am a BashOperator" && '
            'echo "  Category: Action Operator" && '
            'echo "  I run shell commands" && '
            'echo "================================"'
        ),
        doc="BashOperator: Action Operator that runs bash commands.",
    )

    # Task 4: @task decorator — explains Task vs Task Instance
    @task()
    def explain_task_instance(context_output: str):
        """
        @task decorator: Creates a PythonOperator under the hood.
        Category: Action Operator.
        """
        print("=" * 50)
        print("  TASK vs TASK INSTANCE")
        print("=" * 50)
        print("  TASK (Definition):")
        print("    - Lives in the DAG file (Python code)")
        print("    - Has a task_id, operator type, dependencies")
        print("    - Exists once per DAG")
        print()
        print("  TASK INSTANCE (Execution):")
        print("    - Created when a DAG Run is triggered")
        print("    - Tied to a specific logical_date")
        print("    - Has state: queued → running → success/failed")
        print("    - Many instances per Task (one per DAG Run)")
        print()
        print(f"  Previous task said: {context_output}")
        print("=" * 50)

    # Define the dependency chain
    dag_entry_point >> show_context >> bash_action >> explain_task_instance(
        show_context.output
    )


ex01_identify_components()
