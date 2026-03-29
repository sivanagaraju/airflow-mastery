"""
Solution 01: First DAG with 3 Print Tasks
==========================================

SOLUTION for: exercises/Ex01_FirstDAG.py

ARCHITECTURE:
    ┌──────────┐    ┌───────────┐    ┌──────────┐
    │ extract  │ -> │ transform │ -> │   load   │
    └──────────┘    └───────────┘    └──────────┘

KEY LEARNINGS:
    - @dag replaces DAG() context manager
    - @task replaces PythonOperator
    - Return values auto-pass via XCom
    - pendulum for timezone-aware dates
"""

from airflow.decorators import dag, task
import pendulum


@dag(
    dag_id="ex01_first_dag",
    description="Exercise 01 — Simple ETL pipeline with 3 tasks",
    schedule="@daily",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["exercise", "module-00"],
    default_args={
        "owner": "airflow-mastery",
        "retries": 1,
    },
)
def ex01_first_dag():
    """A simple 3-step ETL pipeline demonstrating task dependencies."""

    @task()
    def extract():
        """Extract: Simulate pulling data from a source system."""
        print("Extracting data from source...")
        print("  → Connected to PostgreSQL database")
        print("  → Fetched 1,000 records from sales table")
        return {"records_extracted": 1000, "source": "postgresql"}

    @task()
    def transform(extract_data: dict):
        """Transform: Process the extracted data."""
        records = extract_data["records_extracted"]
        print(f"Transforming {records} records...")
        print("  → Removed duplicates: 50 records dropped")
        print("  → Applied currency conversion")
        print("  → Added computed columns")
        return {"records_transformed": records - 50}

    @task()
    def load(transform_data: dict):
        """Load: Send processed data to the data warehouse."""
        records = transform_data["records_transformed"]
        print(f"Loading {records} records to warehouse...")
        print("  → Connected to Snowflake data warehouse")
        print("  → Inserted into analytics.daily_sales table")
        print("  → Pipeline complete! ✓")

    # Chain the tasks: extract → transform → load
    extract_result = extract()
    transform_result = transform(extract_result)
    load(transform_result)


ex01_first_dag()
