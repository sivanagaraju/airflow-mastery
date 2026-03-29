# What is Apache Airflow?

> Module 00 · Topic 01 — Your starting point for mastering workflow orchestration

---

## Why This Matters

Before writing a single DAG, you need to understand **what problem Airflow solves** and **where it fits** in the data engineering landscape. Interviewers at the Principal/Lead level expect you to articulate not just *how* to use Airflow, but *why* you would choose it over alternatives — and critically, *when NOT to use it*.

---

## Sub-Topics

| # | File | What You'll Learn |
|---|------|-------------------|
| 01 | [Workflow Orchestration](./explanation/01-workflow-orchestration.md) | What orchestration means, DAG as a concept, why manual scripts fail |
| 02 | [Why Airflow](./explanation/02-why-airflow.md) | Core strengths, community size, extensibility, use cases |
| 03 | [Airflow vs Alternatives](./explanation/03-airflow-vs-alternatives.md) | Airflow vs Luigi, Prefect, Dagster, Mage, Step Functions |
| 04 | [When NOT to Use Airflow](./explanation/04-when-not-to-use-airflow.md) | Anti-patterns, streaming limitations, sub-second latency |

---

## Study Path

1. Read explanations in order (01 → 04)
2. Run the demo DAG: [`demo_hello_airflow.py`](./demos/demo_hello_airflow.py)
3. Complete exercise: [`Ex01_FirstDAG.py`](./exercises/Ex01_FirstDAG.py)
4. Review [Company Use Cases](./use-cases/01-company-use-cases.md) (Airbnb, Uber, Lyft)
5. Test yourself with the Self-Assessment Quizzes in each explanation file

---

## Related Mini-Project

After completing Modules 00-04, take on [Mini-Project 01: Store Sales Report](../../04-dags-fundamentals/mini-project-01-store-sales-report/)
