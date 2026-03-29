# Airflow UI & CLI

> Module 03 · Topic 01 — Master every view in the Airflow UI

---

## Sub-Topics

| # | File | What You'll Learn |
|---|------|-------------------|
| 01 | [DAG List View](./explanation/01-dag-list-view.md) | The main dashboard: pause, trigger, filter |
| 02 | [Grid View](./explanation/02-tree-view.md) | Matrix of runs × tasks (formerly Tree View) |
| 03 | [Graph View](./explanation/03-graph-view.md) | Visual DAG structure with live status |
| 04 | [Gantt Chart](./explanation/04-gantt-chart.md) | Task duration timeline for performance analysis |
| 05 | [Code View](./explanation/05-code-view.md) | Read-only DAG source code in UI |
| 06 | [Task Instance View](./explanation/06-task-instance-view.md) | Logs, XCom, rendered template, details |
| 07 | [Landing Times](./explanation/07-landing-times.md) | Trend analysis for scheduling drift |
| 08 | [Variables UI](./explanation/08-variables-ui.md) | CRUD operations for Airflow Variables |
| 09 | [Connections UI](./explanation/09-connections-ui.md) | Managing external system credentials |

---

## Study Path

1. Read explanations 01 → 09 (skim 05-09, deep-read 01-04)
2. Deploy [`demo_ui_exploration_dag.py`](./demos/demo_ui_exploration_dag.py) and explore each view
3. Challenge: Can you identify a performance bottleneck using only the Gantt chart?

---

## Pro Tips

| Tip | Why |
|-----|-----|
| Use tags to filter DAGs | At 100+ DAGs, tags are essential |
| Star frequently used DAGs | Quick access from the top |
| Use Graph View for debugging | Visual dependency + color-coded status |
| Check Gantt before optimizing | Shows which task is the bottleneck |
