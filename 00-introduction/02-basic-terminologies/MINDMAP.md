# Basic Terminologies

```markmap
# Airflow Core Terms
## DAG (Directed Acyclic Graph)
### Definition: Collection of tasks with dependencies
### Properties
#### dag_id (unique identifier)
#### schedule (when to run)
#### start_date (first execution)
#### catchup (backfill past runs?)
### DAG Run
#### One execution instance of a DAG
#### Has execution_date (logical date)
#### States: queued, running, success, failed
## Task
### Definition: Single unit of work
### Properties
#### task_id (unique within DAG)
#### operator (what to do)
#### dependencies (upstream/downstream)
### Task Instance
#### One execution of a task in a DAG Run
#### Has state: queued → scheduled → running → success/failed
#### Logs captured per instance
## Operator
### Action Operators (do something)
#### PythonOperator → run Python function
#### BashOperator → run shell command
#### EmailOperator → send email
### Transfer Operators (move data)
#### S3ToRedshiftOperator
#### GCSToBigQueryOperator
### Sensor Operators (wait for condition)
#### FileSensor → wait for file
#### HttpSensor → wait for API response
#### ExternalTaskSensor → wait for another DAG
## Scheduler
### Parses DAG files every 30s
### Creates DAG Runs based on schedule
### Assigns tasks to executors
### Monitors task states
## Executor
### Sequential (single task, dev only)
### Local (multi-process, small scale)
### Celery (distributed, production)
### Kubernetes (pod-per-task, cloud-native)
## Worker
### Actually executes the task code
### Reports state back to scheduler
### Has its own log storage
## Metadata Database
### PostgreSQL or MySQL
### Stores ALL state
#### DAG definitions
#### DAG Run history
#### Task Instance states
#### XCom values
#### Variables & Connections
```
