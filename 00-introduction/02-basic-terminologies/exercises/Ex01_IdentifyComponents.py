"""
Exercise 01: Identify and Label Airflow Components
====================================================

OBJECTIVE:
    Create a DAG called "ex01_identify_components" that demonstrates
    your understanding of core Airflow terminology by creating tasks
    that log information about themselves.

REQUIREMENTS:
    1. Create a DAG with at least 4 tasks:
       - task_1: Uses EmptyOperator (name it "dag_entry_point")
       - task_2: Uses PythonOperator that prints its own task_id,
                 dag_id, and logical_date from context
       - task_3: Uses BashOperator that echoes "I am an Action Operator"
       - task_4: Uses @task decorator that explains the difference
                 between a Task and a Task Instance

    2. Dependencies: task_1 >> task_2 >> task_3 >> task_4

    3. Set appropriate tags: ["exercise", "module-00"]

BONUS CHALLENGE:
    - Add a 5th task that reads the return value of task_2 via XCom
    - Add docstrings to each task explaining which operator type it is
      (Action, Transfer, or Sensor)

DIFFICULTY: Guided

HINTS:
    - EmptyOperator: from airflow.operators.empty import EmptyOperator
    - PythonOperator uses **context to access runtime info
    - context['task_instance'].task_id gives you the task's ID
    - context['logical_date'] gives you the execution date
"""

# YOUR CODE HERE
