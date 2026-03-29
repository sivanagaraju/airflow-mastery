# CLI Commands

```markmap
# Airflow CLI
## DAG Commands
### airflow dags list
### airflow dags trigger <dag_id>
### airflow dags trigger <dag_id> --conf '{"key":"val"}'
### airflow dags pause <dag_id>
### airflow dags unpause <dag_id>
### airflow dags delete <dag_id>
### airflow dags show <dag_id>
### airflow dags backfill -s START -e END <dag_id>
### airflow dags test <dag_id> <logical_date>
## Task Commands
### airflow tasks list <dag_id>
### airflow tasks test <dag_id> <task_id> <date>
#### No DB writes — safe for development
### airflow tasks run <dag_id> <task_id> <date>
#### Actually executes and writes to DB
### airflow tasks clear <dag_id> -t <task_id>
### airflow tasks state <dag_id> <task_id> <date>
### airflow tasks render <dag_id> <task_id> <date>
#### Shows rendered Jinja templates
## Connection Commands
### airflow connections list
### airflow connections add 'conn_id' --conn-type ...
### airflow connections delete 'conn_id'
### airflow connections export connections.json
### airflow connections import connections.json
## Variable Commands
### airflow variables list
### airflow variables get <key>
### airflow variables set <key> <value>
### airflow variables delete <key>
### airflow variables import variables.json
### airflow variables export variables.json
## Maintenance Commands
### airflow db migrate
### airflow db clean --clean-before-timestamp
### airflow db check
### airflow pools list
### airflow pools set <pool> <slots> <description>
### airflow users list
### airflow users create --role Admin
### airflow config list
### airflow config get-value core executor
## Debugging Commands
### airflow dags report
### airflow cheat-sheet
### airflow info
### airflow version
```
