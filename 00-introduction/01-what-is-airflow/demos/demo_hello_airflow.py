"""
Demo: Hello Airflow — Your First DAG
=====================================

This is the simplest possible Airflow DAG. It demonstrates:
1. DAG definition using the @dag decorator (modern TaskFlow API)
2. Task definition using the @task decorator
3. Task dependencies via Python function calls
4. Modern Airflow 2.x+ patterns

ARCHITECTURE:
┌─────────────────────────────────────────────────────┐
│                    HELLO AIRFLOW DAG                  │
│                                                       │
│    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│    │  start   │ -> │ greet    │ -> │  end     │     │
│    │ (print)  │    │ (print)  │    │ (print)  │     │
│    └──────────┘    └──────────┘    └──────────┘     │
│                                                       │
│    Schedule: @daily                                   │
│    Start:    2024-01-01 UTC                           │
└─────────────────────────────────────────────────────┘

CONCEPTS DEMONSTRATED:
- @dag decorator replaces DAG() context manager (cleaner, modern API)
- @task decorator replaces PythonOperator (less boilerplate)
- pendulum for timezone-aware dates (never use datetime.datetime)
- Task chaining via function call return values
- catchup=False to prevent backfill on first deploy

HOW TO RUN:
    1. Place this file in your Airflow dags/ folder
    2. The scheduler will detect it within 30 seconds
    3. Enable the DAG in the UI (toggle the switch)
    4. Trigger manually via UI or CLI: airflow dags trigger demo_hello_airflow
"""

from airflow.decorators import dag, task
import pendulum


@dag(
    dag_id="demo_hello_airflow",
    description="Your very first Airflow DAG — Hello World!",
    schedule="@daily",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["module-00", "introduction", "demo"],
    doc_md=__doc__,
    default_args={
        "owner": "airflow-mastery",
        "retries": 1,
    },
)
def demo_hello_airflow():
    """
    A minimal DAG that prints messages to demonstrate core concepts.

    Learning objectives:
    - Understand DAG file structure
    - See how tasks connect via dependencies
    - Observe task logs in the Airflow UI
    """

    @task()
    def start():
        """First task: announces the pipeline has started."""
        print("=" * 50)
        print("  AIRFLOW PIPELINE STARTED")
        print("  This task runs first because it has no upstream.")
        print("=" * 50)
        return "Pipeline started successfully"

    @task()
    def greet(message: str):
        """
        Second task: receives data from the upstream task.

        Args:
            message: The return value from the start() task,
                     automatically passed via XCom.
        """
        print(f"  Received from upstream: {message}")
        print("  Hello, Airflow! 🌊")
        print("  You are now orchestrating workflows like a pro.")
        return "Greeting complete"

    @task()
    def end(message: str):
        """
        Final task: confirms pipeline completion.

        Args:
            message: The return value from greet() task.
        """
        print(f"  Received from upstream: {message}")
        print("=" * 50)
        print("  PIPELINE COMPLETE")
        print("  Check the Airflow UI to see task logs and status.")
        print("=" * 50)

    # Define the task execution order:
    # start() -> greet() -> end()
    # Return values are automatically passed via XCom
    start_result = start()
    greet_result = greet(start_result)
    end(greet_result)


# This line instantiates the DAG — required for Airflow to detect it
demo_hello_airflow()
