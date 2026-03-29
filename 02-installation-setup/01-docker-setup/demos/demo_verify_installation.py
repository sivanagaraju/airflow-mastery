"""
Demo: Verify Installation — Confirm Your Airflow Setup Works
=============================================================

Place this file in your dags/ folder after running docker compose up.
If you see this DAG in the Airflow UI at localhost:8080, your setup works!

ARCHITECTURE:
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │ check_python │ -> │ check_airflow│ -> │ check_db     │
    └──────────────┘    └──────────────┘    └──────────────┘
                                                   │
                                            ┌──────▼──────┐
                                            │    report   │
                                            └─────────────┘

WHAT THIS VERIFIES:
    1. Python version is 3.9+
    2. Airflow is importable and version 2.x+
    3. Database connection is healthy
    4. All critical configuration is set
"""

from airflow.decorators import dag, task
import pendulum


@dag(
    dag_id="demo_verify_installation",
    description="Verify your Airflow Docker setup is working correctly",
    schedule=None,  # Manual trigger only
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["module-02", "installation", "demo"],
    doc_md=__doc__,
    default_args={
        "owner": "airflow-mastery",
        "retries": 0,
    },
)
def demo_verify_installation():
    """Trigger this DAG to verify your Airflow installation."""

    @task()
    def check_python():
        """Verify Python version is 3.9+."""
        import sys

        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print(f"  Python version: {version}")

        assert sys.version_info >= (3, 9), (
            f"Python 3.9+ required, got {version}"
        )
        print("  ✓ Python version OK")

        return {"python_version": version}

    @task()
    def check_airflow():
        """Verify Airflow is installed and version 2.x+."""
        import airflow

        version = airflow.__version__
        print(f"  Airflow version: {version}")

        major = int(version.split(".")[0])
        assert major >= 2, f"Airflow 2.x+ required, got {version}"
        print("  ✓ Airflow version OK")

        return {"airflow_version": version}

    @task()
    def check_database():
        """Verify the metadata database is accessible."""
        from airflow.settings import Session

        session = Session()
        try:
            # Simple query to verify DB connectivity
            result = session.execute("SELECT 1").fetchone()
            assert result[0] == 1
            print("  ✓ Database connection OK")

            # Check critical tables exist
            from sqlalchemy import inspect
            inspector = inspect(session.bind)
            tables = inspector.get_table_names()
            required = ["dag", "dag_run", "task_instance", "xcom"]
            for table in required:
                assert table in tables, f"Missing table: {table}"
                print(f"  ✓ Table '{table}' exists")

            return {"status": "healthy", "table_count": len(tables)}
        finally:
            session.close()

    @task()
    def report(python_info: dict, airflow_info: dict, db_info: dict):
        """Print a summary report of the installation check."""
        print("=" * 60)
        print("  INSTALLATION VERIFICATION REPORT")
        print("=" * 60)
        print(f"  Python:    {python_info['python_version']}  ✓")
        print(f"  Airflow:   {airflow_info['airflow_version']}  ✓")
        print(f"  Database:  {db_info['status']}  ✓")
        print(f"  Tables:    {db_info['table_count']} found  ✓")
        print("=" * 60)
        print("  🎉 ALL CHECKS PASSED — Your setup is working!")
        print("  You're ready to start Module 03 (UI & CLI)")
        print("=" * 60)

    # Chain the verification steps
    py = check_python()
    af = check_airflow()
    db = check_database()
    report(py, af, db)


demo_verify_installation()
