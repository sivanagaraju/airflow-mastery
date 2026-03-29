# What is Airflow?

```markmap
# Apache Airflow
## What It Is
### Workflow Orchestrator
#### Schedules tasks
#### Manages dependencies
#### Monitors execution
### Open Source (Apache Foundation)
#### Started at Airbnb (2014)
#### Top-level Apache project (2019)
#### 35,000+ GitHub stars
### Python-Based
#### DAGs as Python code
#### Full programmatic control
#### Extensible via plugins
## Core Concepts
### DAG (Directed Acyclic Graph)
#### No cycles allowed
#### Defines task order
#### Version controlled
### Task
#### Unit of work
#### Runs independently
#### Has states (queued, running, success, failed)
### Operator
#### Action Operators (do something)
#### Transfer Operators (move data)
#### Sensor Operators (wait for condition)
## Why Choose Airflow
### Mature & Battle-Tested
#### Used by 10,000+ companies
#### Fortune 500 adoption
### Rich Ecosystem
#### 80+ provider packages
#### Cloud-native (MWAA, Composer)
### Community
#### Largest orchestrator community
#### Active development
### Extensibility
#### Custom operators
#### Custom hooks
#### Plugin system
## When NOT to Use
### Real-Time Streaming → Use Kafka/Flink
### Sub-Second Latency → Wrong tool
### Simple Cron Jobs → Overkill
### Event-Driven Only → Consider Prefect
## Alternatives Comparison
### Luigi (Spotify)
### Prefect (Prefect Technologies)
### Dagster (Elementl)
### Mage (Mage AI)
### AWS Step Functions
```
