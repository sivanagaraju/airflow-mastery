"""
Exercise 01: Build Your First DAG with 3 Print Tasks
=====================================================

OBJECTIVE:
    Create a DAG called "ex01_first_dag" with exactly three tasks:
    1. extract  — prints "Extracting data from source"
    2. transform — prints "Transforming data" (depends on extract)
    3. load      — prints "Loading data to warehouse" (depends on transform)

REQUIREMENTS:
    - Use the @dag and @task decorators (TaskFlow API)
    - Set schedule to "@daily"
    - Set start_date to January 1, 2024 UTC using pendulum
    - Set catchup=False
    - Use the tag "exercise" for easy filtering in the UI
    - Each task must print its step name

ARCHITECTURE:
    ┌──────────┐    ┌───────────┐    ┌──────────┐
    │ extract  │ -> │ transform │ -> │   load   │
    └──────────┘    └───────────┘    └──────────┘

DIFFICULTY: Guided (follow the pattern from demo_hello_airflow.py)

HINTS:
    1. Import: from airflow.decorators import dag, task
    2. Import: import pendulum
    3. The @dag decorator replaces the DAG() context manager
    4. Connect tasks by calling them and passing return values

WHEN YOU'RE DONE:
    - Place in your dags/ folder
    - Check the UI: does the DAG appear?
    - Trigger it manually and check all 3 task logs
    - Compare with solutions/Sol01_FirstDAG.py
"""

# YOUR CODE STARTS HERE
# =====================

# Step 1: Import the required modules
# from airflow.decorators import ...
# import ...

# Step 2: Define the DAG with @dag decorator
# @dag(
#     dag_id="ex01_first_dag",
#     ...
# )
# def ex01_first_dag():

    # Step 3: Define the three tasks using @task
    # @task()
    # def extract():
    #     ...

    # @task()
    # def transform(...):
    #     ...

    # @task()
    # def load(...):
    #     ...

    # Step 4: Chain the tasks together
    # extract_result = extract()
    # transform_result = transform(extract_result)
    # load(transform_result)

# Step 5: Instantiate the DAG
# ex01_first_dag()

# YOUR CODE ENDS HERE
