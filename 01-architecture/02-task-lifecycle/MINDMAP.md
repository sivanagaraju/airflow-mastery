# Task Lifecycle

```markmap
# Task Lifecycle
## States
### none (not yet queued)
### removed (disappeared from DAG)
### scheduled (dependencies met, waiting for slot)
### queued (sent to executor)
### running (worker executing)
### success (completed OK)
### failed (execution error)
### up_for_retry (failed, retries remaining)
### up_for_reschedule (sensor in reschedule mode)
### upstream_failed (upstream dependency failed)
### skipped (branch not taken)
### deferred (waiting on external trigger)
### sensing (deprecated, use deferrable)
## State Transitions
### Happy Path
#### none → scheduled → queued → running → success
### Failure Path
#### running → failed
#### running → up_for_retry → scheduled → queued → running
### Branch Skip Path
#### none → skipped (BranchPythonOperator)
### Sensor Reschedule Path
#### running → up_for_reschedule → scheduled → running
### Defer Path
#### running → deferred → scheduled → queued → running
## Debugging by State
### stuck in "scheduled"
#### Executor can't pick up tasks
#### Pool slots full
#### parallelism limit reached
### stuck in "queued"
#### Workers unavailable
#### Celery broker down
#### K8s can't create pods
### stuck in "running"
#### Task actually running (long operation)
#### Zombie: worker died mid-execution
```
