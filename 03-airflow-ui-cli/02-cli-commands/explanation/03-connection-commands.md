# Connection Commands — Manage Credentials from the CLI

> **Module 03 · Topic 02 · Explanation 03** — Create, test, export, and manage connections without the UI

---

## 🎯 The Real-World Analogy: A Bank Vault Key Management Console

Think of Airflow connection CLI commands as the **bank vault's key management console**:

| Connection Command | Vault Console Equivalent |
|--------------------|------------------------|
| `connections add` | Program a new key card — define which vault rooms it opens |
| `connections get` | Look up a key card's access permissions |
| `connections test` | Verify the key card actually opens the door (live test) |
| `connections list` | Print the directory of all programmed key cards |
| `connections delete` | Deactivate and shred a key card |
| `connections export` | Backup the vault access configuration |
| `connections import` | Restore the vault access configuration in a new location |

The vault console doesn't store the vault's contents — it stores the credentials to access them. Similarly, Airflow connection commands manage access credentials, not the data itself.

---

## Complete Command Reference

```bash
# ══════════════════════════════════════════════════════════════
# LIST & INSPECT
# ══════════════════════════════════════════════════════════════
airflow connections list                          # All connections
airflow connections list -o table                 # Table format (cleaner)
airflow connections list | grep postgres          # Filter by type/name

airflow connections get my_postgres               # Details for one connection
airflow connections get my_postgres -o json       # JSON format (for scripting)

# ══════════════════════════════════════════════════════════════
# CREATE — Add new connections
# ══════════════════════════════════════════════════════════════

# PostgreSQL connection:
airflow connections add 'postgres_analytics' \
    --conn-type 'postgres' \
    --conn-host 'db.example.com' \
    --conn-port '5432' \
    --conn-login 'airflow_user' \
    --conn-password 'secret_password' \
    --conn-schema 'analytics'

# AWS connection (using extra JSON for region):
airflow connections add 'aws_data_lake' \
    --conn-type 'aws' \
    --conn-extra '{"region_name": "us-east-1", "role_arn": "arn:aws:iam::123:role/AirflowRole"}'

# HTTP/REST API connection:
airflow connections add 'stripe_api' \
    --conn-type 'http' \
    --conn-host 'api.stripe.com' \
    --conn-schema 'https' \
    --conn-extra '{"api_key": "sk_prod_xxx", "api_version": "2024-01-01"}'

# Snowflake connection:
airflow connections add 'snowflake_prod' \
    --conn-type 'snowflake' \
    --conn-login 'svc_airflow' \
    --conn-password 'vault_secret' \
    --conn-schema 'ANALYTICS' \
    --conn-extra '{"account": "xy12345.us-east-1", "warehouse": "COMPUTE_WH", "role": "AIRFLOW_ROLE", "database": "PROD_DB"}'

# ══════════════════════════════════════════════════════════════
# TEST — Verify a connection actually works
# ══════════════════════════════════════════════════════════════
airflow connections test postgres_analytics
# Output on success: "Connection successfully tested"
# Output on failure: "Connection failed: [specific error]"

# ══════════════════════════════════════════════════════════════
# DELETE
# ══════════════════════════════════════════════════════════════
airflow connections delete my_old_connection       # Remove from metadata DB

# ══════════════════════════════════════════════════════════════
# IMPORT / EXPORT — Migrate connections between environments
# ══════════════════════════════════════════════════════════════
airflow connections export connections_backup.json  # Export all to JSON
airflow connections import connections_backup.json  # Import from JSON file

# ⚠️  WARNING: exported JSON contains PLAINTEXT passwords!
# → Encrypt the file before storing or transmitting
# → Never commit to Git
# → Delete after import
```

---

## Connection URI Format

```bash
# Connections can also be set via environment variables using URI syntax:
# Format: AIRFLOW_CONN_{CONN_ID_UPPERCASE}='<scheme>://<login>:<password>@<host>:<port>/<schema>'

# PostgreSQL:
export AIRFLOW_CONN_POSTGRES_ANALYTICS='postgresql://airflow_user:secret@db.example.com:5432/analytics'

# MySQL:
export AIRFLOW_CONN_MYSQL_DWH='mysql://user:pass@mysql.example.com:3306/warehouse'

# HTTP with extra:
export AIRFLOW_CONN_STRIPE_API='http://api.stripe.com/?api_key=sk_prod_xxx'

# AWS (JSON format for complex connections):
export AIRFLOW_CONN_AWS_DEFAULT='{
    "conn_type": "aws",
    "extra": {
        "region_name": "us-east-1",
        "role_arn": "arn:aws:iam::123456:role/AirflowRole"
    }
}'
```

---

## Python: Testing and Validating Connections Programmatically

```python
import subprocess
import json
import requests

def test_connection_cli(conn_id: str) -> bool:
    """Test a connection via CLI subprocess."""
    result = subprocess.run(
        ["airflow", "connections", "test", conn_id],
        capture_output=True,
        text=True,
        timeout=30
    )
    success = "Connection successfully tested" in result.stdout
    if not success:
        print(f"FAILED: {result.stdout} {result.stderr}")
    return success

def export_connections_to_dict() -> list:
    """Export all connections as a dict (same as UI Export)."""
    result = subprocess.run(
        ["airflow", "connections", "export", "/dev/stdout", "--file-format", "json"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

def add_connection_via_api(
    conn_id: str,
    conn_type: str,
    host: str,
    port: int,
    login: str,
    password: str,
    schema: str,
    extra: dict = None
) -> dict:
    """Add connection via REST API (equivalent to CLI add command)."""
    resp = requests.post(
        "http://localhost:8080/api/v1/connections",
        auth=("admin", "admin"),
        json={
            "connection_id": conn_id,
            "conn_type": conn_type,
            "host": host,
            "port": port,
            "login": login,
            "password": password,
            "schema": schema,
            "extra": json.dumps(extra) if extra else None
        }
    )
    resp.raise_for_status()
    return resp.json()

# CI/CD usage: validate all connections after deployment
def validate_connections_post_deploy(required_conn_ids: list) -> bool:
    all_passed = True
    for conn_id in required_conn_ids:
        passed = test_connection_cli(conn_id)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {conn_id}")
        if not passed:
            all_passed = False
    return all_passed

# Example:
required = ["postgres_analytics", "aws_data_lake", "snowflake_prod"]
if not validate_connections_post_deploy(required):
    raise SystemExit("Connection validation failed — deployment blocked")
```

---

## 🏢 Real Company Use Cases

**Deliveroo** includes `airflow connections test` for all critical connections as the final step of their deployment pipeline. Their CI/CD script runs the test command against each newly deployed connection immediately after deployment and fails the pipeline if any test fails. This catches credential rotation mismatches (new password in secrets manager but old password still in Airflow connection) before they cause task failures in production.

**ASOS** (UK e-commerce) uses `airflow connections export` as part of their disaster recovery (DR) procedure. Every night, a cron job exports all connections to an encrypted S3 object (via `airflow connections export | gpg --encrypt > connections.json.gpg`). The S3 object is replicated cross-region. In a DR scenario, importing the connections file into the recovered Airflow cluster takes under 5 minutes — no manual recreation of 80+ connections.

**Zalando** automated their connection provisioning using a Terraform Airflow provider. Each team's connection requirements are declared as Terraform HCL, reviewed via PR, and applied by a service account. New connections appear in Airflow within 2 minutes of PR merge — no tickets to the platform team, no UI clicking. The `connections list` CLI command is used in their compliance scripts to verify that no undeclared connections exist (drift detection).

---

## ❌ Anti-Patterns

### Anti-Pattern 1: Exporting Connections and Storing the Output in Git

```bash
# ❌ CRITICAL SECURITY MISTAKE
airflow connections export > connections.json
git add connections.json
git commit -m "backup connections"
git push origin main

# The exported JSON contains PLAINTEXT passwords!
# Even if the repository is private:
# - Git history is permanent (even after "deletion")
# - Anyone with repo clone has the passwords
# - If repo is ever made public or leaked: credential compromise

# ✅ GOOD: Encrypt immediately, store in secrets manager
airflow connections export /tmp/connections.json
# Encrypt with GPG or store in AWS Secrets Manager:
aws secretsmanager put-secret-value \
    --secret-id "airflow/connections-backup" \
    --secret-string file:///tmp/connections.json
rm /tmp/connections.json   # Delete plaintext immediately
```

---

### Anti-Pattern 2: Using `connections add` in Production Without Infrastructure-as-Code

```bash
# ❌ BAD: Manually clicking or running CLI in production
airflow connections add 'new_db' --conn-type 'postgres' \
    --conn-host 'new-db.company.com' --conn-password 'secret'

# Problems:
# 1. No audit trail — who added this connection and why?
# 2. Not reproducible — if Airflow is rebuilt, this connection is gone
# 3. Not version-controlled — can't see history of changes
# 4. Security — password in bash history on the server
```

```bash
# ✅ GOOD: Connections via environment variables (K8s Secrets) or Secrets Manager
# In Kubernetes:
kubectl create secret generic airflow-connections \
    --from-literal=AIRFLOW_CONN_NEW_DB='postgresql://user:secret@new-db.company.com:5432/mydb'
# Applied via GitOps — PR required, audit trail in Git

# Or via Terraform:
resource "aws_secretsmanager_secret_version" "airflow_conn_new_db" {
  secret_id     = "airflow/connections/new_db"
  secret_string = "postgresql://user:${var.db_password}@new-db.company.com:5432/mydb"
}
```

---

### Anti-Pattern 3: Never Testing Connections After Addition

```bash
# ❌ BAD: Add connection → assume it works → deploy DAG → task fails at 3am
airflow connections add 'snowflake_prod' \
    --conn-type 'snowflake' --conn-login 'svc_airflow' \
    --conn-password 'wrongpassword'  # Typo in password
# No test → fail discovered at 3am when the ETL runs

# ✅ GOOD: ALWAYS test immediately after adding
airflow connections add 'snowflake_prod' \
    --conn-type 'snowflake' --conn-login 'svc_airflow' \
    --conn-password 'correctpassword' \
    --conn-extra '{"account": "xy12345", "warehouse": "WH"}'

# Immediately test:
airflow connections test snowflake_prod
# → "Connection successfully tested" → safe to deploy DAG
# → "Connection failed: ..." → fix now, not at 3am
```

---

## 🎤 Senior-Level Interview Q&A

**Q1: How do you safely migrate 50 connections from dev Airflow to production without manually re-entering each one?**

> Controlled export-import with security handling: (1) `airflow connections export connections_export.json` on dev. (2) Audit the JSON — remove any dev-specific connections, remove any test credentials. (3) For production: replace all plaintext passwords in the JSON with production secrets before importing, OR better: don't import passwords at all — use environment variables (`AIRFLOW_CONN_*`) managed by your secrets manager for connection credentials. (4) `airflow connections import connections_prod.json` on production. (5) Run `airflow connections test <conn_id>` for each critical connection. (6) Delete the JSON file immediately. Never commit the export file to Git.

**Q2: A team member accidentally deleted a production connection using `connections delete`, and a critical pipeline is now failing. What's your immediate recovery?**

> Recovery procedure: (1) **Immediate**: pause the affected DAG(s): `airflow dags pause <dag_id>` to stop new failures accumulating. (2) **Reconstruct**: check if the connection was created via infrastructure-as-code (Terraform, K8s secrets) — apply the IaC and it's restored in minutes. If not: check your disaster recovery export (nightly backup) or get the credentials from your password manager/secrets manager. (3) **Recreate**: `airflow connections add <conn_id> ...` with the recovered credentials. (4) **Test**: `airflow connections test <conn_id>`. (5) **Unpause**: `airflow dags unpause <dag_id>`. (6) **Backfill**: if runs failed during the outage, `airflow dags backfill --reset-dagruns` for the affected dates. (7) **Post-mortem**: this incident should motivate moving to infrastructure-as-code for all connections.

**Q3: You need to rotate credentials for a database connection with zero downtime to running tasks. How do you do it?**

> Zero-downtime rotation: (1) **Dual-write window**: coordinate with the DBA to add the new credentials alongside the old ones (if DB supports multiple passwords per user, e.g., PostgreSQL `ALTER USER ... PASSWORD`). (2) **Update the connection**: `airflow connections delete old_postgres && airflow connections add old_postgres --conn-password 'newpassword' ...`. Or via env var: update the `AIRFLOW_CONN_*` env var value. (3) **Test**: `airflow connections test old_postgres`. (4) **Running tasks**: tasks that already acquired a connection from the pool will use the old credentials until their connection is closed. New tasks pick up the new credentials. The overlap period (dual-write window) ensures both work simultaneously. (5) **Revoke old**: after 15-30 minutes, revoke the old credentials from the DB (DBA action). Any task still holding an old connection will get a connection error on next use and retry with the new credentials.

---

## 🏛️ Principal-Level Interview Q&A

**Q1: Design a connection lifecycle management system for an enterprise with 200+ connections across 5 Airflow deployments.**

> **Centralized connection management platform**: (1) **Single source of truth**: HashiCorp Vault stores ALL connections. Airflow uses the Vault secrets backend: `AIRFLOW__SECRETS__BACKEND=airflow.providers.hashicorp.secrets.vault.VaultBackend`. (2) **Connection catalog**: a database (or Vault metadata) tracks: conn_id, description, owner team, last_rotated, rotation_schedule, service_account. (3) **Self-service provisioning**: teams submit connection requests via a web form → triggers a Terraform apply via GitOps → creates the Vault secret → available in all 5 Airflow clusters immediately. (4) **Automated rotation**: Vault handles automatic password rotation for supported DB types (RDS, Postgres) on a 90-day schedule. Airflow reads the current version on each task start — zero code changes. (5) **Drift detection**: nightly job queries `GET /api/v1/connections` from each cluster and compares to the Vault catalog. Any connections present in Airflow but not in the catalog are flagged as "shadow connections" for investigation. (6) **Audit**: all Vault reads (from Airflow task executions) are logged with the entity (cluster+task+run_id) and timestamp — full audit trail.

**Q2: `airflow connections test` passes but tasks still fail with connection errors. How do you diagnose this discrepancy?**

> **Root cause analysis**: `connections test` runs from the WEBSERVER's network context. The task runs from the WORKER's network context. These can be different: (1) **Network segmentation**: webserver is in a public subnet; workers are in a private subnet. The DB is only accessible from the private subnet → test passes from webserver, fails from workers. Diagnosis: `ssh worker_host && airflow connections test <conn_id>`. (2) **Different env vars**: test uses webserver's Fernet key to decrypt; worker uses a different Fernet key → decryption error. Check that all components use the same `AIRFLOW__CORE__FERNET_KEY`. (3) **Pool exhaustion**: test creates one connection successfully. Workers create 10 simultaneous connections and exhaust the pool → subsequent connections fail with "too many clients." (4) **SSL certificate**: webserver has the CA certificate installed; worker Docker image doesn't. Fix: add `CONN_EXTRA_sslmode=verify-full` and ensure the CA cert is in the worker image. **Resolution**: always run `connections test` from the worker container, not just the webserver.

**Q3: How do you implement connection access control — ensuring the Payments team can only use `payments_*` connections and cannot see or use `analytics_*` connections?**

> **Multi-layer access control**: (1) **Airflow RBAC**: create roles `PaymentsEngineer` and `AnalyticsEngineer`. Use Airflow's `ConnectionView` access policy to scope connection visibility. Note: Airflow's built-in RBAC doesn't support per-connection access control natively — all Admins see all connections. (2) **Secrets backend scoping**: use HashiCorp Vault with path-based policies. `payments` team's Vault policy: `path "secret/airflow/connections/payments_*" { capabilities = ["read"] }`. `analytics` team: `path "secret/airflow/connections/analytics_*" { capabilities = ["read"] }`. (3) **Kubernetes namespace isolation**: run payments and analytics pipelines in separate Kubernetes namespaces. Each namespace has its own K8s Secrets containing only its team's connections, mounted only to its team's Airflow workers. (4) **DAG-level connection enforcement**: use a custom AirflowPlugin that validates: when a payments DAG references `analytics_db`, reject the task with a clear permission error. Enforce naming conventions via CI: DAG files in `dags/payments/` may only import hooks with `payments_*` conn_ids.

---

## 📝 Self-Assessment Quiz

**Q1**: How do you create a PostgreSQL connection via CLI without using the UI?
<details><summary>Answer</summary>
```bash
airflow connections add 'postgres_analytics' \
    --conn-type 'postgres' \
    --conn-host 'db.example.com' \
    --conn-port '5432' \
    --conn-login 'airflow_user' \
    --conn-password 'secret' \
    --conn-schema 'analytics'
```
Then immediately verify: `airflow connections test postgres_analytics`. For production, prefer environment variables: `AIRFLOW_CONN_POSTGRES_ANALYTICS='postgresql://user:pass@host:5432/db'` to avoid passwords in bash history.
</details>

**Q2**: A developer exports all connections and commits the file to Git. What is the security risk?
<details><summary>Answer</summary>
The exported JSON contains PLAINTEXT passwords (they're stored Fernet-encrypted in the DB but exported as plaintext). Once committed to Git, these passwords are permanently in the repository history — even after deleting the file and force-pushing, forensic recovery tools can retrieve them. If the repository is ever cloned externally or made public, all production credentials are compromised. Correct approach: encrypt the export file immediately (GPG or secrets manager), never commit to Git, delete after use.
</details>

**Q3**: `airflow connections test postgres_prod` succeeds, but tasks using `postgres_prod` fail with "connection refused." What's the most likely cause?
<details><summary>Answer</summary>
Network segmentation. `connections test` runs from the WEBSERVER's network context. Your tasks run from WORKER nodes which may be in a different network segment (different VPC subnet, Docker network, Kubernetes pod). The database may be reachable from the webserver but not from workers. Diagnosis: SSH into the worker host (or exec into the worker pod) and run `airflow connections test postgres_prod` there. This tests from the actual network context where tasks execute.
</details>

**Q4**: You need to set up the same 30 connections in a new Airflow staging environment. How do you do this efficiently?
<details><summary>Answer</summary>
If you maintain connections as infrastructure-as-code (environment variables / Terraform / K8s Secrets): apply the IaC to the staging environment — connections are available in minutes. If not: (1) `airflow connections export connections.json` from dev. (2) Edit the JSON to swap dev credentials for staging credentials. (3) `airflow connections import connections.json` on staging. (4) `airflow connections test <conn_id>` for each critical connection. (5) Delete the JSON file. This is the manual migration path — the incident should motivate moving to IaC for future environments.
</details>

### Quick Self-Rating
- [ ] I can create connections via CLI with all required fields
- [ ] I always test connections immediately after adding them
- [ ] I never export connections to plaintext files or Git
- [ ] I use env vars / Secrets Manager for production connections (not CLI add)
- [ ] I can use import/export for environment migration safely

---

## 📚 Further Reading

- [Airflow CLI Reference — connections](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html#connections) — Complete CLI documentation
- [Connection URI Format](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html#uri-format) — Environment variable connection strings
- [Secrets Backend — HashiCorp Vault](https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/hashicorp-vault-secrets-backend.html) — Enterprise secrets management
- [REST API — Connections](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#tag/Connection) — Programmatic connection management
- [Fernet Key Management](https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/fernet.html) — Encryption and key rotation
