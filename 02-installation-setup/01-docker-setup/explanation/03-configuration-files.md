# Configuration Files — airflow.cfg and Environment Variables

> **Module 02 · Topic 01 · Explanation 03** — How Airflow reads its configuration and the 3-tier priority system

---

## 🎯 The Real-World Analogy: A Car's ECU (Engine Control Unit)

Think of Airflow's configuration system as a **car's engine control unit**:

| Config Layer | Car Equivalent | Behavior |
|--------------|---------------|----------|
| **Built-in defaults** | Factory ECU settings | "This engine runs at 6,000 RPM max by default" — compiled into code |
| **airflow.cfg** | Custom ECU tune file | Mechanic edits a tuning file: "Set max RPM to 7,500" |
| **Environment variables** | Real-time override dial | Driver turns a boost knob: "Override to 8,000 NOW" — highest priority |

The **boost knob always wins**. No matter what the tuning file says, the real-time override dial controls the final value. This is exactly how Airflow's config priority works — environment variables always beat the file, which always beats the defaults.

---

## Configuration Hierarchy

```mermaid
graph TD
    ENV[Environment Variables<br/>AIRFLOW__SECTION__KEY] -->|highest priority| FINAL[Final Config Value]
    CFG[airflow.cfg file<br/>in $AIRFLOW_HOME] -->|medium priority| FINAL
    DEFAULT[Built-in Defaults<br/>compiled in code] -->|lowest priority| FINAL

    style ENV fill:#4CAF50,color:#fff
    style CFG fill:#FF9800,color:#fff
    style DEFAULT fill:#607D8B,color:#fff
    style FINAL fill:#017CEE,color:#fff
```

```
Priority Resolution (highest wins):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [1] AIRFLOW__CORE__EXECUTOR=CeleryExecutor    ← ENV VAR  (wins)
  [2] executor = LocalExecutor                  ← airflow.cfg
  [3] executor = SequentialExecutor             ← code default
  
  Final value: CeleryExecutor ✓
```

> **Key insight**: Environment variables ALWAYS override airflow.cfg. This is the recommended approach in Docker/Kubernetes because you don't need to mount config files — every setting is injectable at runtime.

---

## Critical Configuration Sections

| Section | Key Settings | Impact |
|---------|-------------|--------|
| `[core]` | `executor`, `parallelism`, `dags_folder` | Runtime behavior |
| `[database]` | `sql_alchemy_conn` | Which DB to use |
| `[scheduler]` | `min_file_process_interval`, `parsing_processes` | DAG parsing speed |
| `[webserver]` | `web_server_port`, `workers` | UI performance |
| `[logging]` | `remote_logging`, `remote_base_log_folder` | Log storage |
| `[core]` | `fernet_key` | Encryption of DB secrets |

---

## Environment Variable Naming Convention

```
AIRFLOW__<SECTION>__<KEY>=<VALUE>
         ↑↑         ↑↑
         Double underscores separate section from key

Section      Key                           Env Variable
──────────────────────────────────────────────────────────────────────
[core]       executor                   →  AIRFLOW__CORE__EXECUTOR
[core]       parallelism                →  AIRFLOW__CORE__PARALLELISM
[core]       fernet_key                 →  AIRFLOW__CORE__FERNET_KEY
[database]   sql_alchemy_conn           →  AIRFLOW__DATABASE__SQL_ALCHEMY_CONN
[scheduler]  min_file_process_interval  →  AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL
[scheduler]  parsing_processes          →  AIRFLOW__SCHEDULER__PARSING_PROCESSES
[webserver]  web_server_port            →  AIRFLOW__WEBSERVER__WEB_SERVER_PORT
[logging]    remote_logging             →  AIRFLOW__LOGGING__REMOTE_LOGGING
[secrets]    backend                    →  AIRFLOW__SECRETS__BACKEND
```

```bash
# Inspect the final resolved configuration
airflow config list

# Get a specific value (shows which source it came from)
airflow config get-value core executor

# Validate your env var naming
airflow config get-value scheduler min_file_process_interval
```

---

## The Fernet Key — Critical Security Setting

The Fernet key encrypts sensitive values stored in the metadata DB (connection passwords, variable values):

```bash
# Generate a new Fernet key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Output: XoqSSr-iq_4A_pLNBqeIEMqNqW8rJNf_pL4bBvBCy2s=

# Set it via environment variable (preferred)
AIRFLOW__CORE__FERNET_KEY=XoqSSr-iq_4A_pLNBqeIEMqNqW8rJNf_pL4bBvBCy2s=
```

> **Warning**: If you change the Fernet key after connections are stored, Airflow cannot decrypt them. This causes cryptic `InvalidToken` errors. Always rotate keys using `airflow rotate-fernet-key` command.

---

## Secrets Backend Configuration

For enterprise deployments, configure a secrets backend instead of storing secrets in the metadata DB:

```python
# airflow.cfg or environment variables

# ---- HashiCorp Vault ----
AIRFLOW__SECRETS__BACKEND=airflow.providers.hashicorp.secrets.vault.VaultBackend
AIRFLOW__SECRETS__BACKEND_KWARGS={"connections_path": "airflow/connections", "variables_path": "airflow/variables", "url": "http://vault:8200", "token": "root"}

# ---- AWS Secrets Manager ----
AIRFLOW__SECRETS__BACKEND=airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
AIRFLOW__SECRETS__BACKEND_KWARGS={"connections_prefix": "airflow/connections", "variables_prefix": "airflow/variables"}

# ---- GCP Secret Manager ----
AIRFLOW__SECRETS__BACKEND=airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend
AIRFLOW__SECRETS__BACKEND_KWARGS={"connections_prefix": "airflow-connections", "variables_prefix": "airflow-variables"}
```

---

## 🏢 Real Company Use Cases

**Airbnb** (the company that created Airflow) uses environment variables exclusively for config in their Kubernetes deployments — zero airflow.cfg files mounted in pods. This enables GitOps: all config is stored as Kubernetes ConfigMaps and Secrets, deployed via Helm, and auditable in Git without any file mounting complexity.

**Robinhood** manages 3 separate Airflow environments (dev, staging, prod) by maintaining a single `airflow.cfg` with sensible defaults and using environment-specific Kubernetes Secrets to override connection strings, Fernet keys, and executor settings per environment. Their CI pipeline validates that no secrets appear in the cfg file using a grep-based pre-commit hook.

**Stripe** integrates Airflow with HashiCorp Vault as the secrets backend for all production deployments. DAG authors write connection IDs in code (e.g., `snowflake_prod`), and the actual credentials are resolved at runtime from Vault — never stored in the Airflow metadata DB. This allows zero-downtime secret rotation: update the Vault secret, and the next task execution picks it up automatically.

---

## ❌ Anti-Patterns

### Anti-Pattern 1: Storing the Fernet Key in airflow.cfg (Committed to Git)

```ini
# ❌ BAD: airflow.cfg committed to git with the Fernet key
[core]
fernet_key = XoqSSr-iq_4A_pLNBqeIEMqNqW8rJNf_pL4bBvBCy2s=
```

**Why it's bad**: Anyone with read access to the repository can decrypt every Airflow connection password. The key can rotate accidentally when someone regenerates the file.

```bash
# ✅ GOOD: Inject Fernet key via environment variable from secrets manager
AIRFLOW__CORE__FERNET_KEY=${VAULT_SECRET_FERNET_KEY}

# Or use fernet_key_cmd (reads from command output)
# airflow.cfg:
# fernet_key_cmd = aws secretsmanager get-secret-value --secret-id airflow/fernet_key --query SecretString --output text
```

---

### Anti-Pattern 2: Ignoring Config Priority — "I changed airflow.cfg but nothing happened"

```ini
# developer sets in airflow.cfg:
[core]
executor = CeleryExecutor
```

```bash
# ❌ But docker-compose.yml already has:
AIRFLOW__CORE__EXECUTOR=LocalExecutor

# The env var ALWAYS wins. executor stays LocalExecutor.
# Developer is confused for hours.
```

```bash
# ✅ GOOD: Always check the resolved config first
airflow config get-value core executor
# Output: LocalExecutor  ← source: environment variable

# To actually change executor, update the environment variable:
AIRFLOW__CORE__EXECUTOR=CeleryExecutor
```

---

### Anti-Pattern 3: Using Default SQLite sql_alchemy_conn in Production

```ini
# ❌ BAD: Default config — nobody changed this from the SQLite default
[database]
sql_alchemy_conn = sqlite:////opt/airflow/airflow.db
```

**Why it breaks at scale**: SQLite allows only 1 writer at a time. With scheduler + webserver + 4 workers all writing to the metadata DB, SQLite's file lock causes "database is locked" errors, task state corruption, and scheduler crashes.

```ini
# ✅ GOOD: Always use PostgreSQL for anything beyond solo development
# airflow.cfg
[database]
sql_alchemy_conn = postgresql+psycopg2://airflow:${DB_PASSWORD}@postgres:5432/airflow

# Or via env var (preferred):
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:${DB_PASSWORD}@postgres:5432/airflow
```

---

## 🎤 Senior-Level Interview Q&A

**Q1: How do you manage Airflow secrets (database passwords, API keys) in production?**

> Three approaches by security tier: **(1) Environment variables** — set via Kubernetes Secrets or docker-compose `.env` file (git-ignored). Simple but credentials exist as plaintext strings in memory. **(2) Airflow Connections/Variables** — stored in the metadata DB, encrypted with the Fernet key. Good for credentials accessed from DAGs via `BaseHook.get_connection()`. **(3) Secrets Backend** — integrate with HashiCorp Vault, AWS Secrets Manager, or GCP Secret Manager via `AIRFLOW__SECRETS__BACKEND`. Credentials are never stored in the metadata DB — resolved at task execution time from the external system. Best for enterprise compliance requirements. Robinhood uses approach 2; Stripe uses approach 3.

**Q2: You set `AIRFLOW__CORE__EXECUTOR=CeleryExecutor` as an env var, but airflow.cfg has `executor=LocalExecutor`. Which executor runs?**

> `CeleryExecutor` — the environment variable always wins. Airflow's config resolution is: env vars > airflow.cfg > built-in defaults. This is by design: containers should be configuration-agnostic, with runtime behavior injected via environment variables rather than baked-in files. You can verify with `airflow config get-value core executor` which will show `CeleryExecutor`.

**Q3: A developer reports "my Airflow connection passwords are showing as `***` in the UI but tasks fail with decryption errors." What's happening?**

> This is a Fernet key mismatch. The UI masks the password (shows `***`) regardless of whether the stored encrypted value is valid. But when a task tries to retrieve the connection, Airflow decrypts the stored ciphertext using the current Fernet key — if the key changed since the connection was saved, decryption fails with `cryptography.fernet.InvalidToken`. Fix: (1) Check if `AIRFLOW__CORE__FERNET_KEY` changed recently. (2) Run `airflow connections export /tmp/connections.json` — if it fails, confirm the key mismatch. (3) Use `airflow rotate-fernet-key` with both old and new keys to re-encrypt existing connections.

---

## 🏛️ Principal-Level Interview Q&A

**Q1: Design a configuration management strategy for 3 Airflow environments (dev, staging, prod) with different executors, databases, and log destinations.**

> **Layered configuration approach**: One `airflow.cfg` with sensible shared defaults (DAG folder, logging format, timezone) committed to the repository. Per-environment overrides delivered exclusively via environment variables — no per-environment cfg files. **Implementation**: Use Kubernetes Secrets for sensitive values (Fernet key, DB connection strings) and ConfigMaps for non-sensitive overrides (executor type, parallelism). A Helm `values.yaml` per environment defines the override set. **CI enforcement**: A pipeline job runs `airflow config list` with each environment's variables and validates key settings are correct (e.g., prod must have `remote_logging=True`, must not have `expose_config=True`, parallelism must be ≥ 32). **Config drift detection**: Weekly automated job dumps `airflow config list` for each environment and diffs against the expected state in Git.

**Q2: A security team requires that all Airflow connection credentials are rotated every 90 days with zero downtime. How do you architect this?**

> The answer is the **secrets backend pattern with versioned secrets**. Architecture: (1) Move all connections to HashiCorp Vault or AWS Secrets Manager — `AIRFLOW__SECRETS__BACKEND` configured on all environments. (2) Secrets stored at versioned paths: `airflow/connections/snowflake_prod/v42`. (3) Rotation process: security team creates `v43`, updates the "current" pointer in Vault. Next task execution reads `v43`. Zero downtime — in-flight tasks use `v42`, new tasks use `v43`. (4) The Fernet key in the metadata DB becomes irrelevant for connection credentials (they're resolved from Vault at runtime). Only Variables and XCom would use Fernet. (5) Audit log: Vault audit logs show every secret read, by which Airflow host, at what time — full audit trail for compliance.

**Q3: `airflow config list` shows thousands of settings. How do you audit the non-default settings in a production environment for a security review?**

> Build a **configuration baseline comparison tool**: (1) Run `airflow config list --defaults` to get the compiled-in defaults as JSON. (2) Run `airflow config list` in the production environment. (3) Diff the two — every override is a non-default setting. (4) Focus the security review on the delta: check `expose_config` (must be False), `hide_sensitive_variable_fields` (must be True), `allow_raw_html_descriptions` (must be False), `webserver_secret_key` (must be set, not default), `fernet_key` (must not be the default placeholder). (5) Automate this into a CI job that red-lights any config that matches a list of known-dangerous defaults (SQLite connection string, `SequentialExecutor`, `expose_config=True`).

---

## 📝 Self-Assessment Quiz

**Q1**: You set `AIRFLOW__CORE__EXECUTOR=CeleryExecutor` as an env var, but `airflow.cfg` has `executor=LocalExecutor`. Which one takes effect?
<details><summary>Answer</summary>
`CeleryExecutor` — the environment variable wins. Priority order: env vars > airflow.cfg > built-in defaults. This is by design so you can override behavior at runtime without touching files. Verify with: `airflow config get-value core executor`.
</details>

**Q2**: How do you translate the airflow.cfg setting `[scheduler] min_file_process_interval = 60` to its environment variable equivalent?
<details><summary>Answer</summary>
`AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL=60`

Pattern: `AIRFLOW__` + section in UPPERCASE + `__` + key in UPPERCASE. Section `[scheduler]` → `SCHEDULER`, key `min_file_process_interval` → `MIN_FILE_PROCESS_INTERVAL`.
</details>

**Q3**: A task fails with `cryptography.fernet.InvalidToken`. What is the most likely cause?
<details><summary>Answer</summary>
The Fernet key was changed after the Airflow connection credentials were saved. Airflow encrypted the connection password with the old Fernet key, but now tries to decrypt with the new key — which fails. Fix: use `airflow rotate-fernet-key` with access to both the old and new Fernet keys to re-encrypt all stored secrets. Then update to the new key only.
</details>

**Q4**: Why is the secrets backend pattern (Vault, AWS Secrets Manager) superior to storing credentials in the Airflow metadata DB?
<details><summary>Answer</summary>
Four advantages: (1) **Zero-downtime rotation** — update the secret in Vault; next task read gets the new value without Airflow restart. (2) **Centralized audit** — Vault logs every secret access with timestamp and requester identity, satisfying compliance requirements. (3) **No Fernet key dependency** — secrets are resolved at runtime from the backend, not decrypted from the DB. (4) **Cross-system secret sharing** — the same Vault secret can be used by Airflow, Kubernetes pods, and other services, with a single rotation point. The trade-off: added latency per secret read (typically 5-50ms per secret fetch from Vault).
</details>

### Quick Self-Rating
- [ ] I can translate any `airflow.cfg` setting to its env var equivalent
- [ ] I can explain the 3-tier configuration priority with a concrete example
- [ ] I understand what the Fernet key does and how to rotate it safely
- [ ] I can configure a secrets backend for production use
- [ ] I can audit non-default config settings in a running Airflow environment

---

## 📚 Further Reading

- [Airflow Configuration Reference](https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html) — Complete list of all settings
- [Secrets Backend Setup](https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/index.html) — Vault, AWS, GCP integration
- [Fernet Key Management](https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/fernet.html) — Key generation, rotation, and `rotate-fernet-key`
- [Airflow Security Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/security/index.html) — Official security hardening guide
