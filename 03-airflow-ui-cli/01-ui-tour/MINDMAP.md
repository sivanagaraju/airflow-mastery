# UI Tour

```markmap
# Airflow UI Views
## DAG List View (Main Dashboard)
### Toggle DAG on/off
### Filter by tag, owner, status
### Quick actions: trigger, delete
### Columns: runs, schedule, last run, next run
### Star DAGs for quick access
## Grid View (formerly Tree View)
### Matrix: DAG Runs (columns) × Tasks (rows)
### Color-coded status per task instance
#### Dark green: success
#### Red: failed
#### Orange: up_for_retry
#### Light green: running
#### Pink: skipped
### Click task → Instance Details
### Filter by run state
## Graph View
### Visual DAG structure
### Nodes = tasks, Edges = dependencies
### Real-time color status
### Click node → Task Instance Details
### Best for dependency debugging
## Gantt Chart
### Horizontal timeline
### Bar per task showing duration
### Identifies bottleneck tasks
### Shows parallel vs sequential execution
### Key for performance optimization
## Code View
### Read-only DAG source
### Syntax highlighted
### Shows the parsed version (may differ from file)
## Task Instance Details
### Log tab (stdout/stderr)
### XCom tab (return values)
### Rendered Template tab
### Task Details (dates, duration, try number)
### Actions: Clear, Mark Success, Mark Failed
## Landing Times
### Historical trend of task completion
### Detects scheduling drift
### Shows if tasks are getting slower
## Variables UI
### Admin → Variables
### CRUD key-value pairs
### JSON support for complex values
### Import/Export as JSON
## Connections UI
### Admin → Connections
### Credential management
### Connection types (Postgres, HTTP, S3, etc.)
### Test connection button
```
