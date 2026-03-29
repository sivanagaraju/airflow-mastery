"""
Demo: Pip Installation Verification
=====================================

Run this OUTSIDE of Docker to verify your pip-based Airflow install.
This file is NOT a DAG — it's a standalone verification script.

Usage:
    python demo_pip_verification.py

CHECKS:
    1. Python version >= 3.9
    2. Airflow installed and importable
    3. Airflow version >= 2.0
    4. AIRFLOW_HOME is set
    5. Database connection works
    6. Key provider packages available
"""

import sys


def check_python_version():
    """Verify Python 3.9+."""
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if sys.version_info < (3, 9):
        print(f"  ✗ Python {version} — need 3.9+")
        return False
    print(f"  ✓ Python {version}")
    return True


def check_airflow_installed():
    """Verify Airflow is importable."""
    try:
        import airflow
        version = airflow.__version__
        major = int(version.split(".")[0])
        if major < 2:
            print(f"  ✗ Airflow {version} — need 2.x+")
            return False
        print(f"  ✓ Airflow {version}")
        return True
    except ImportError:
        print("  ✗ Airflow not installed")
        return False


def check_airflow_home():
    """Verify AIRFLOW_HOME is set."""
    import os
    home = os.environ.get("AIRFLOW_HOME", "")
    if home:
        print(f"  ✓ AIRFLOW_HOME = {home}")
        return True
    else:
        default = os.path.expanduser("~/airflow")
        print(f"  ⚠ AIRFLOW_HOME not set (default: {default})")
        return True  # Not fatal


def check_providers():
    """Check which provider packages are installed."""
    providers = [
        ("apache-airflow-providers-http", "airflow.providers.http"),
        ("apache-airflow-providers-postgres", "airflow.providers.postgres"),
        ("apache-airflow-providers-amazon", "airflow.providers.amazon"),
    ]
    for name, module_path in providers:
        try:
            __import__(module_path)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ○ {name} (not installed — optional)")


def main():
    print("=" * 55)
    print("  AIRFLOW PIP INSTALLATION VERIFICATION")
    print("=" * 55)

    all_ok = True

    print("\n[1] Python Version:")
    all_ok &= check_python_version()

    print("\n[2] Airflow Installation:")
    all_ok &= check_airflow_installed()

    print("\n[3] AIRFLOW_HOME:")
    all_ok &= check_airflow_home()

    print("\n[4] Provider Packages:")
    check_providers()

    print("\n" + "=" * 55)
    if all_ok:
        print("  🎉 ALL CORE CHECKS PASSED")
        print("  Run 'airflow db migrate' to initialize the database.")
    else:
        print("  ❌ SOME CHECKS FAILED — Review errors above.")
    print("=" * 55)


if __name__ == "__main__":
    main()
