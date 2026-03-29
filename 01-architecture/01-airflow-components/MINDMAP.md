# Airflow Components

```markmap
# Airflow Architecture
## Webserver
### Flask + Gunicorn
### Reads from Metadata DB only
### DAG Serialization
#### JSON in serialized_dag table
#### No filesystem access needed
### Views
#### Grid (formerly Tree)
#### Graph
#### Gantt
#### Code
#### Calendar
### Authentication
#### Flask-AppBuilder
#### RBAC (Role-Based Access Control)
### Caching
#### DAG bag cached in memory
#### Configurable refresh interval
## Scheduler
### Core Loop
#### Parse DAG files (min_file_process_interval=30s)
#### Create DAG Runs per schedule
#### Check task dependencies
#### Queue ready tasks
#### Update task states
### High Availability (2.0+)
#### Multiple schedulers supported
#### Distributed locking via DB
#### Row-level locks on task_instance
### Performance Tuning
#### parallelism (max concurrent tasks)
#### max_active_runs_per_dag
#### max_active_tasks_per_dag
#### parsing_processes
### DAG File Processor
#### Separate process per DAG file
#### Configurable process count
#### .airflowignore support
## Executor
### SequentialExecutor (dev only)
#### Single task at a time
#### Same process as scheduler
#### SQLite compatible
### LocalExecutor
#### Multiple local processes
#### Limited by machine CPU/RAM
#### PostgreSQL required
### CeleryExecutor
#### Redis/RabbitMQ broker
#### Distributed worker pool
#### Persistent workers
#### Flower monitoring UI
### KubernetesExecutor
#### Pod per task
#### Perfect isolation
#### Auto-scaling
#### Cold start latency (10-30s)
### CeleryKubernetesExecutor
#### Hybrid approach
#### Default: Celery
#### Per-task override to K8s
## Workers
### Task Execution
#### Import DAG file
#### Run operator.execute()
#### Capture logs
#### Update state in DB
### Resource Management
#### CPU/memory limits
#### Pool-based throttling
### Log Storage
#### Local filesystem
#### Remote (S3, GCS, Azure Blob)
## Metadata Database
### PostgreSQL (recommended)
### MySQL (supported)
### SQLite (dev only)
### Key Tables
#### dag, dag_run, task_instance
#### xcom, variable, connection
#### serialized_dag, log
### Maintenance
#### airflow db clean
#### PgBouncer for connection pooling
## Triggerer (2.2+)
### Deferrable Operators
### asyncio event loop
### Frees worker slots
### ExternalTaskSensor → deferrable
```
