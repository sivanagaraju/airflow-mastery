# Custom Dockerfile — Extending the Airflow Image

> **Module 02 · Topic 01 · Explanation 04** — When and how to build custom Airflow images

---

## When You Need a Custom Dockerfile

| Scenario | `_PIP_ADDITIONAL_REQUIREMENTS` | Custom Dockerfile |
|----------|-------------------------------|-------------------|
| 1-2 pip packages | ✓ Use this (simpler) | Not needed |
| 5+ pip packages | Slow startup every restart | ✓ Use this (baked in) |
| System packages (gcc, git) | Can't do this | ✓ Required |
| Custom compiled libraries | Can't do this | ✓ Required |
| Production deployments | Never — too slow | ✓ Always |

---

## Dockerfile Anatomy

```dockerfile
# ── Stage 1: Start from official image ──
FROM apache/airflow:2.10.4-python3.11

# ── Stage 2: System packages (requires root) ──
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \    # C compiler for pip packages
        git \               # For git-based pip installs
    && rm -rf /var/lib/apt/lists/*

# ── Stage 3: Python packages (as airflow user) ──
USER airflow
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

```
╔══════════════════════════════════════════════════════════════╗
║  CRITICAL RULES FOR AIRFLOW DOCKERFILES                      ║
║                                                              ║
║  1. ALWAYS use official apache/airflow as base image        ║
║     Never use python:3.x — you'd miss Airflow dependencies ║
║                                                              ║
║  2. Install system packages as ROOT                         ║
║     Then switch back to 'airflow' for pip                   ║
║                                                              ║
║  3. Pin ALL versions in requirements.txt                    ║
║     Unpinned deps = unreproducible builds                   ║
║                                                              ║
║  4. Use --no-cache-dir with pip                             ║
║     Saves ~100MB in image size                              ║
║                                                              ║
║  5. Clean up apt cache                                      ║
║     rm -rf /var/lib/apt/lists/* saves ~50MB                 ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Multi-Stage Build (Advanced)

```dockerfile
# Stage 1: Build dependencies with system packages
FROM apache/airflow:2.10.4-python3.11 AS builder

USER root
RUN apt-get update && apt-get install -y build-essential

USER airflow
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image (smallest possible)
FROM apache/airflow:2.10.4-python3.11

COPY --from=builder /home/airflow/.local /home/airflow/.local
```

> Multi-stage builds reduce the final image size by excluding build tools (gcc, make) from the runtime image. Only the compiled Python packages are copied.

---

## Self-Assessment Quiz

**Q1**: Why is `_PIP_ADDITIONAL_REQUIREMENTS` bad for production?
<details><summary>Answer</summary>Because it runs `pip install` EVERY TIME the container starts. This means: (1) Slow container startup (30s-5min depending on packages), (2) PyPI must be reachable — if the network is down, the container fails to start, (3) Version drift — unpinned versions might resolve differently on different starts, (4) No reproducibility guarantee. In production, always bake dependencies into a custom Docker image.</details>

### Quick Self-Rating
- [ ] I can decide when to use PIP_ADDITIONAL_REQUIREMENTS vs custom Dockerfile
- [ ] I can write a multi-stage Dockerfile for Airflow
- [ ] I can explain the USER directive pattern (root → airflow)
