# Custom Dockerfile — Extending the Airflow Image

> **Module 02 · Topic 01 · Explanation 04** — When and how to build custom Airflow images for production

---

## 🎯 The Real-World Analogy: Building Construction

Think of Docker image layering as **construction on a prefab foundation**:

| Build Stage | Construction Equivalent | Role |
|-------------|--------------------------|------|
| `FROM apache/airflow:2.10.4` | Buying a prefab structural frame | Apache already built the foundation, walls, and wiring |
| `USER root` | Calling licensed contractors (electrician, plumber) | Only licensed contractors (root) can modify building infrastructure |
| `RUN apt-get install` | Installing structural systems (HVAC, electrical) | System-level dependencies must be installed with elevated access |
| `USER airflow` | Handing building to the tenant | Day-to-day operations (running Airflow, installing Python packages) done as normal user |
| `COPY requirements.txt` + `RUN pip install` | Tenant furnishing their apartment | Airflow-specific packages installed in the user's space, not the building's |

Multi-stage builds are like **modular construction**: build the heavy lifting (compiling C extensions) in a construction warehouse, then deliver only the finished furniture to the apartment — not the scaffolding.

---

## When You Need a Custom Dockerfile

| Scenario | `_PIP_ADDITIONAL_REQUIREMENTS` | Custom Dockerfile |
|----------|-------------------------------|-------------------|
| 1–2 pip packages, dev only | ✓ Acceptable for local hacking | Not needed |
| 5+ pip packages | Slow startup every restart | ✓ Use this (baked in) |
| System packages (`gcc`, `git`, `libpq-dev`) | ❌ Cannot do this | ✓ Required |
| Custom compiled libraries (`psutil`, `cryptography`) | ❌ Cannot do this | ✓ Required |
| Production deployments | ❌ Never — too slow & risky | ✓ Always |
| Team-shared environment | ❌ Version drift between restarts | ✓ Always |

---

## Dockerfile Anatomy

```dockerfile
# ── Stage 1: Start from official image (NEVER use python:3.x as base) ──
FROM apache/airflow:2.10.4-python3.11

# ── Stage 2: System packages (requires root permissions) ──
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \    # C compiler — needed to compile C-extension Python packages
        git \               # For pip packages installed from git URLs
        libpq-dev \         # PostgreSQL client library — required by psycopg2
    && rm -rf /var/lib/apt/lists/*  # Clean cache to minimize image size

# ── Stage 3: Python packages (must run as 'airflow' user, not root) ──
USER airflow
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.11.txt" \
    -r requirements.txt
```

```
╔══════════════════════════════════════════════════════════════╗
║  CRITICAL RULES FOR AIRFLOW DOCKERFILES                      ║
║                                                              ║
║  1. ALWAYS use official apache/airflow as base image        ║
║     Never use python:3.x — you'd miss 500+ Airflow deps    ║
║                                                              ║
║  2. Install system packages as ROOT                         ║
║     Then IMMEDIATELY switch back to 'airflow' for pip       ║
║                                                              ║
║  3. Pin ALL versions in requirements.txt                    ║
║     Unpinned deps = unreproducible builds = 3am incidents   ║
║                                                              ║
║  4. Use --no-cache-dir with pip                             ║
║     Saves ~100MB in image size per package set              ║
║                                                              ║
║  5. Clean up apt cache in the SAME RUN command              ║
║     Each RUN creates a layer — clean must be in same layer  ║
║                                                              ║
║  6. Use the Airflow constraints file during pip install     ║
║     Prevents provider dependency conflicts                  ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Requirements File Best Practices

```
# requirements.txt — production example
# ── Airflow Providers ──
apache-airflow-providers-snowflake==4.4.2
apache-airflow-providers-amazon==8.17.0
apache-airflow-providers-slack==8.4.0
apache-airflow-providers-postgres==5.11.2

# ── Data Processing ──
pandas==2.1.4
pyarrow==14.0.2
numpy==1.26.3

# ── Internal packages ──
my-company-utils==1.3.0  # Installed from internal PyPI

# ── DO NOT add: ──
# apache-airflow  ← already in base image
# celery          ← managed by Airflow's constraint file
# flask           ← version conflicts likely
```

---

## Multi-Stage Build (Advanced)

```dockerfile
# Stage 1: Build environment — has build tools, larger image
FROM apache/airflow:2.10.4-python3.11 AS builder

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev

USER airflow
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.11.txt" \
    --target /tmp/packages \
    -r requirements.txt

# Stage 2: Runtime image — no build tools, minimal size
FROM apache/airflow:2.10.4-python3.11

# Copy only the installed packages from the builder stage
COPY --from=builder /tmp/packages /home/airflow/.local/lib/python3.11/site-packages/
```

> **Why multi-stage?** `build-essential` alone adds ~200MB. `libpq-dev` adds another ~30MB. Multi-stage builds keep the final runtime image slim by copying only the compiled packages — not the compilers used to build them. Typical size reduction: 30–50% smaller final image.

---

## Build and Deploy Pattern

```bash
# Build the custom image
docker build \
  -t my-org/airflow:2.10.4-v$(date +%Y%m%d) \
  -f Dockerfile \
  .

# Tag for CI/CD
docker tag my-org/airflow:2.10.4-v20240315 my-registry.azurecr.io/airflow:2.10.4-v20240315

# Push to registry
docker push my-registry.azurecr.io/airflow:2.10.4-v20240315

# Update docker-compose.yml to reference the new image
# image: my-registry.azurecr.io/airflow:2.10.4-v20240315
```

---

## 🏢 Real Company Use Cases

**DoorDash** maintains a custom Airflow image that includes their internal Python libraries (`doordash-data-utils`, `doordash-quality`) pre-installed. This means every DAG author can import `from doordash_data.metrics import calculate_delivery_rate` without any additional setup. Their build pipeline produces a new custom image on every merged PR to the platform repo, pushing to ECR and automatically updating the Kubernetes deployment.

**Lyft** builds custom Airflow images with `geopy`, `shapely`, and `rtree` (geospatial libraries with C extensions) pre-compiled. Because these packages require `libgeos-dev` at compile time but not at runtime, they use multi-stage builds to keep the final image 40% smaller. Their build takes 8 minutes on a CI machine vs. `_PIP_ADDITIONAL_REQUIREMENTS` which would add 5+ minutes to every container restart.

**Shopify** versions their custom Airflow images semantically: `shopify/airflow:2.10.4-20240315-v42`. The last segment (`v42`) is the internal capabilities version — Shopify-specific providers and operators. Airflow version upgrades and Shopify package upgrades are tracked separately, allowing independent release cadences. This means Shopify can ship new internal operators weekly without waiting for an Airflow version bump.

---

## ❌ Anti-Patterns

### Anti-Pattern 1: Using `_PIP_ADDITIONAL_REQUIREMENTS` in Production

```yaml
# ❌ BAD: Runs pip install on EVERY container restart — 2–8 minute delay
environment:
  _PIP_ADDITIONAL_REQUIREMENTS: >-
    pandas==2.1.0
    scikit-learn==1.3.0
    apache-airflow-providers-snowflake==4.4.2
    my-company-utils==1.3.0
```

**What goes wrong**:
- Production container restart takes 5 minutes instead of 10 seconds
- PyPI unavailability causes container startup failure
- Subdependency versions resolve differently on different restarts (drift)
- No reproducibility guarantee between environments

```dockerfile
# ✅ GOOD: Bake all packages into the image — instant startup, reproducible
FROM apache/airflow:2.10.4

USER airflow
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.11.txt" \
    -r requirements.txt
```

---

### Anti-Pattern 2: Running pip as Root in the Dockerfile

```dockerfile
# ❌ BAD: pip install as root breaks Airflow's security model
FROM apache/airflow:2.10.4
USER root
RUN pip install pandas==2.1.0  # Installs to /usr/lib/python3.11 — wrong location
```

**Why it breaks**: Airflow's container runs as `airflow` user (UID 50000). Packages installed as root go to system Python paths. When the `airflow` user runs tasks, it uses its own pip-managed paths (`/home/airflow/.local/lib/`), not the root-installed system paths. Result: `ModuleNotFoundError: No module named 'pandas'` at task runtime even though the image has pandas.

```dockerfile
# ✅ GOOD: System packages as root, Python packages as airflow user
FROM apache/airflow:2.10.4

USER root
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev \
    && rm -rf /var/lib/apt/lists/*

USER airflow        # ← Switch BEFORE pip install
RUN pip install --no-cache-dir pandas==2.1.0
```

---

### Anti-Pattern 3: Using `python:3.11` as the Base Image Instead of the Official Airflow Image

```dockerfile
# ❌ BAD: Using generic Python image as base
FROM python:3.11-slim

# Now you must install Airflow AND all its system dependencies manually
RUN apt-get update && apt-get install -y \
    gcc libpq-dev libffi-dev libssl-dev  # Just the beginning...

RUN pip install apache-airflow==2.10.4  # No constraint file — dependency hell
```

**Why it fails**: The official Airflow image already has 15+ system packages pre-installed with the exact versions tested by the Apache Airflow team. Starting from `python:3.11` means you're responsible for replicating all of that yourself — and missing even one causes subtle bugs. The official image is also pre-configured with the correct Airflow user, home directory, and environment variables.

```dockerfile
# ✅ GOOD: Always start from the official image
FROM apache/airflow:2.10.4-python3.11
# Everything is pre-configured. Just add YOUR packages on top.
```

---

## 🎤 Senior-Level Interview Q&A

**Q1: Why is `_PIP_ADDITIONAL_REQUIREMENTS` bad for production?**

> Because it runs `pip install` on EVERY container restart. Three concrete failure modes: (1) **Startup latency** — 5+ packages means 2–8 minute container startup, causing health check timeouts and container restart loops in Kubernetes. (2) **PyPI dependency** — if your corporate network is down or PyPI is unreachable, the container fails to start entirely. (3) **Version drift** — without a constraint file, pip may resolve different package versions on different restarts, causing "worked yesterday, broken today" incidents. Custom Dockerfile bakes packages in at build time — container start is instant, no network needed.

**Q2: A data engineer's custom operator works locally but fails in production with `ModuleNotFoundError`. The package IS in the Dockerfile. How do you debug?**

> Four-step debug: (1) **Check USER at pip install time** — `docker inspect <image> | jq '.[].Config.User'`. If `root`, packages installed to system Python, not Airflow's user Python. (2) **Verify installation path** — `docker run --rm <image> python -c "import pandas; print(pandas.__file__)"` to confirm pandas is importable as `airflow` user. (3) **Check constraints conflict** — the package version may conflict with Airflow's constraint file; look for `ERROR: Cannot install X because Y requires Z`. (4) **Test in isolation** — `docker run --rm <image> airflow tasks test dag_id task_id 2024-01-01` to reproduce the exact execution environment.

**Q3: The build pipeline CI takes 25 minutes to build the custom Airflow image. How do you speed it up?**

> Layer caching strategy: (1) **Order Dockerfile layers by change frequency** — `apt-get install` (changes rarely) before `COPY requirements.txt` (changes monthly) before `COPY dags/` (changes daily). Docker layer cache reuses unchanged layers. (2) **Use BuildKit** — `DOCKER_BUILDKIT=1 docker build` enables parallel layer builds and better caching. (3) **Separate system and Python packages** — if system packages haven't changed, their layer is cached even when requirements.txt changes. (4) **Use a build cache registry** — `docker build --cache-from my-registry/airflow:cache` pulls cached layers from the registry, enabling cache reuse across CI agents. (5) **Multi-stage with dependency caching** — a dedicated "deps" stage that only rebuilds when requirements.txt changes.

---

## 🏛️ Principal-Level Interview Q&A

**Q1: How do you design a custom Airflow image build pipeline that supports 20 teams, each with different Python package requirements, without creating image sprawl?**

> **The Shared Base + Team Overlay pattern**: **(1) Shared base image** — `company/airflow-base:2.10.4` contains Airflow core, all company-wide providers (Snowflake, Databricks, Slack), and internal SDK packages. Built weekly or on Airflow version bump. **(2) Team overlay images** — each team's `Dockerfile` starts `FROM company/airflow-base:2.10.4` and adds only team-specific packages. Teams own their own build. **(3) Governance** — base image team owns `base-requirements.txt`. Adding packages to the base requires a PR reviewed by the platform team. **(4) CI validation** — each team image build runs `pip check` to catch conflicts, `docker scout cves` to fail on critical CVEs, and a smoke test that imports all key packages. **(5) Registry cleanup** — automated policy deletes images older than 90 days except tagged versions marked "stable".

**Q2: A security audit requires all container images to have no HIGH or CRITICAL CVEs within 72 hours of discovery. How do you implement this for the Airflow base image?**

> **Automated CVE response pipeline**: (1) **Daily scan** — CI cron job runs `grype company/airflow-base:latest` (Anchore Grype) or `docker scout cves` against all published image tags. Results pushed to a security dashboard. (2) **Alert routing** — HIGH CVEs create incidents in PagerDuty/JIRA within 1 hour of detection via webhook from the scan tool. (3) **Automated patch** — if the CVE is patched by updating the base image tag (e.g., `postgres:16.1` → `16.2`), a bot PR is auto-created, CI validates, and auto-merged if tests pass. (4) **Unpatchable CVEs** — if the CVE is in a system package with no patch yet, document the exception with exploitability assessment, apply compensating controls (network policy, read-only filesystem), and re-check daily. (5) **Image immutability** — never update a published tag; rebuild with the same version + a patch suffix (`2.10.4-p1`) so rollback is possible.

**Q3: Design a zero-downtime Airflow upgrade strategy from 2.9 to 2.10 using custom Docker images.**

> **Blue-Green image deployment**: **(Phase 1 — Parallel build)**: Build `company/airflow:2.10.4` image alongside the running `2.9.x` environment. Run the 2.10 image in a staging environment with a copy of production data. Run all existing DAGs in staging for 48 hours — flag any failures. **(Phase 2 — Database migration)**: `airflow db upgrade` is backward-compatible (2.9 scheduler can read 2.10 DB schema). Run `airflow db upgrade` against production while 2.9 is still running. **(Phase 3 — Canary)**: Update 10% of worker pods to the 2.10 image (via Kubernetes rolling update). Monitor task success rate for 4 hours. **(Phase 4 — Full cutover)**: Roll out 2.10 to all pods — scheduler last. Scheduler downtime during its restart: typically <30 seconds. **(Phase 5 — Rollback plan)**: Keep 2.9 image in registry. If critical failure, `kubectl set image deployment/scheduler airflow=company/airflow:2.9.3`. Note: if DB migration ran, the 2.9 scheduler can still run since Airflow migrations are backward-compatible within major versions.

---

## 📝 Self-Assessment Quiz

**Q1**: Why is `_PIP_ADDITIONAL_REQUIREMENTS` bad for production?
<details><summary>Answer</summary>
Because it runs `pip install` on EVERY container restart. Problems: (1) Startup delay of 2–8 minutes depending on packages. (2) Container fails to start if PyPI is unreachable. (3) Version drift — different subdependency versions resolved on different restarts. (4) No reproducibility — can't guarantee the same environment between dev and prod. Always bake packages into a custom Docker image using a Dockerfile for production.
</details>

**Q2**: Why must you switch from `USER root` back to `USER airflow` before running `pip install`?
<details><summary>Answer</summary>
The Airflow process runs as the `airflow` user (UID 50000). When pip runs as root, packages are installed to system Python paths (`/usr/lib/python3.11/`). When the Airflow task runs as `airflow` user, it looks for packages in `airflow` user's paths (`/home/airflow/.local/lib/python3.11/site-packages/`). Result: `ModuleNotFoundError` even though the package appears to be installed. Always run `pip install` as the `airflow` user so packages install to the correct user-accessible paths.
</details>

**Q3**: What is the advantage of multi-stage Docker builds for Airflow images?
<details><summary>Answer</summary>
Multi-stage builds produce a smaller final image by separating the build environment from the runtime environment. The builder stage has `build-essential`, `gcc`, `libpq-dev` etc. needed to compile C-extension packages. The final stage copies only the compiled Python packages (`.so` files + pure Python) — not the compilers. Result: 30–50% smaller images, faster container pulls, reduced attack surface (no compiler tools in production).
</details>

**Q4**: You need to add `libgeos-dev` (a system library) to the Airflow image. What is the exact Dockerfile pattern?
<details><summary>Answer</summary>

```dockerfile
FROM apache/airflow:2.10.4

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgeos-dev && \
    rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir shapely==2.0.2
```

Key points: (1) `apt-get install` as root. (2) `--no-install-recommends` keeps image smaller. (3) `rm -rf /var/lib/apt/lists/*` in the SAME RUN command to avoid a separate cleanup layer. (4) Switch back to `airflow` before pip install.
</details>

### Quick Self-Rating
- [ ] I can decide when to use `_PIP_ADDITIONAL_REQUIREMENTS` vs a custom Dockerfile
- [ ] I can write a correct Dockerfile with the root → airflow user pattern
- [ ] I can write a multi-stage Dockerfile for Airflow
- [ ] I know why to always use the official `apache/airflow` base image
- [ ] I can explain the Airflow constraints file and why to use it in pip install

---

## 📚 Further Reading

- [Official Airflow Docker Image Documentation](https://airflow.apache.org/docs/docker-stack/index.html) — Customization patterns and best practices
- [Airflow Constraints Files](https://github.com/apache/airflow/tree/main/constraints) — Understanding dependency pinning
- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/) — Minimizing image size
- [Docker BuildKit Documentation](https://docs.docker.com/build/buildkit/) — Faster builds with BuildKit cache
- [Grype CVE Scanner](https://github.com/anchore/grype) — Container vulnerability scanning
