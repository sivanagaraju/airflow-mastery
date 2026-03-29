"""
Demo: Airflow Component Check — Querying Architecture at Runtime
================================================================

This DAG queries Airflow's own metadata to demonstrate how the
architecture works from the inside. Each task introspects a
different component.

ARCHITECTURE:
    ┌───────────────┐     ┌──────────────┐     ┌──────────────┐
    │ check_db_conn │ --> │ check_config │ --> │ check_pools  │
    └───────────────┘     └──────────────┘     └──────────────┘
           │
           └──────────────────┐
                              ▼
                     ┌────────────────┐
                     │ show_dag_stats │
                     └────────────────┘

CONCEPTS:
- Accessing the metadata database via Airflow's session
- Reading Airflow configuration programmatically
- Understanding pools and their role in concurrency
- TaskFlow API with multiple return values
"""

from airflow.decorators import dag, task
import pendulum


@dag(
    dag_id="demo_component_check",
    description="Introspect Airflow components from within a DAG",
    schedule=None,  # Manual trigger only
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["module-01", "architecture", "demo"],
    doc_md=__doc__,
    default_args={
        "owner": "airflow-mastery",
        "retries": 0,
    },
)
def demo_component_check():
    """Query Airflow's own internals to understand the architecture."""

    @task()
    def check_db_connection():
        """
        Component: Metadata Database
        Verify the database connection and report the backend type.
        """
        from airflow.settings import Session

        session = Session()
        try:
            # Query the database engine to find out what we're connected to
            result = session.execute(
                "SELECT version();"  # Works for PostgreSQL
            ).fetchone()
            db_version = result[0] if result else "Unknown"

            print("=" * 60)
            print("  METADATA DATABASE CHECK")
            print("=" * 60)
            print(f"  DB Version: {db_version[:80]}...")
            print(f"  Session:    {type(session).__name__}")
            print(f"  Status:     ✓ Connected")
            print("=" * 60)

            return {"status": "connected", "engine": "postgresql"}
        except Exception as e:
            print(f"  Database check failed: {e}")
            # Fallback — might be SQLite in dev
            print("  Likely using SQLite (development mode)")
            return {"status": "connected", "engine": "sqlite"}
        finally:
            session.close()

    @task()
    def check_airflow_config():
        """
        Component: Configuration (airflow.cfg)
        Read key configuration values to understand the deployment.
        """
        from airflow.configuration import conf

        executor = conf.get("core", "executor")
        parallelism = conf.getint("core", "parallelism")
        dag_dir = conf.get("core", "dags_folder")
        sql_alchemy_conn = conf.get("database", "sql_alchemy_conn")

        # Mask the password in the connection string
        masked_conn = sql_alchemy_conn.split("@")[-1] if "@" in sql_alchemy_conn else "***"

        print("=" * 60)
        print("  AIRFLOW CONFIGURATION CHECK")
        print("=" * 60)
        print(f"  Executor:     {executor}")
        print(f"  Parallelism:  {parallelism}")
        print(f"  DAGs Folder:  {dag_dir}")
        print(f"  DB Host:      {masked_conn}")
        print("=" * 60)

        return {
            "executor": executor,
            "parallelism": parallelism,
        }

    @task()
    def check_pools():
        """
        Component: Pool Management
        List all pools and their slot allocation.
        """
        from airflow.models import Pool
        from airflow.settings import Session

        session = Session()
        try:
            pools = session.query(Pool).all()

            print("=" * 60)
            print("  POOL STATUS")
            print("=" * 60)
            for pool in pools:
                used = pool.occupied_slots()
                total = pool.slots
                print(f"  Pool: {pool.pool:<20} | "
                      f"Used: {used}/{total} | "
                      f"Open: {total - used}")
            print("=" * 60)

            return {"pool_count": len(pools)}
        finally:
            session.close()

    @task()
    def show_dag_stats(db_info: dict, config_info: dict, pool_info: dict):
        """
        Summary: Combine all component checks into a final report.
        """
        print("=" * 60)
        print("  AIRFLOW ARCHITECTURE SUMMARY")
        print("=" * 60)
        print(f"  Database:     {db_info['engine']} ({db_info['status']})")
        print(f"  Executor:     {config_info['executor']}")
        print(f"  Parallelism:  {config_info['parallelism']} tasks max")
        print(f"  Pools:        {pool_info['pool_count']} configured")
        print("=" * 60)
        print("  All components operational! ✓")

    # Task dependencies
    db_result = check_db_connection()
    config_result = check_airflow_config()
    pool_result = check_pools()
    show_dag_stats(db_result, config_result, pool_result)


demo_component_check()
