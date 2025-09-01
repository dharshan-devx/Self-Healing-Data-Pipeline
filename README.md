# Self‑Healing Data Pipeline

A production‑grade approach to building resilient, observable, and automated data pipelines that detect, diagnose, and recover from failures without human intervention.

---

## Executive Summary

Modern businesses depend on continuous, trustworthy data to power analytics, personalization, and AI. Traditional pipelines fail silently, recover slowly, and require manual effort—resulting in lost revenue, stale dashboards, and compliance risk.

**This project delivers a *Self‑Healing Data Pipeline*:** an orchestrated, observable, and governed flow that *automatically detects anomalies and failures*, *applies the right remediation strategy* (retry, fallback, quarantine, backfill), and *proves end‑to‑end data lineage*. It reduces mean time to recovery (MTTR), protects SLAs/SLOs, and increases stakeholder trust in data.

---

## The Problem (Why this matters)

### Business Symptoms

* Late or missing dashboards; inaccurate KPIs during critical windows (e.g., finance close, campaign launch).
* Fragile batch jobs that break on upstream schema changes or API rate limits.
* Incident resolution that relies on tribal knowledge, Slack threads, and one or two “pipeline heroes.”
* Limited answers to simple questions like *“Where did this number come from?”* or *“What was the blast radius?”*

### Root Causes

* **Operational Fragility:** one failing task blocks all downstream tasks; manual reruns are error‑prone.
* **Low Observability:** logs scattered across systems; no single view of task health and data dependencies.
* **Poor Lineage & Governance:** unclear source→transform→destination mapping; limited auditability.
* **Change Volatility:** upstream schema drift, API instability, late files, and transient infra/network failures.

### Impact

* **Revenue & Cost:** missed personalization windows, stockouts, campaign misallocation; over‑spend on on‑call time.
* **Trust:** business users lose confidence in data; teams build shadow pipelines.
* **Compliance:** weak traceability for audits and incident post‑mortems.

---

## The Solution (What we built)

A **self‑healing** data platform that combines orchestration, lineage, and automated remediation.

### Core Capabilities

1. **Proactive Detection** – Health checks, data freshness SLAs, volume/profile monitors, and schema guards.
2. **Smart Remediation** – Tuned retries with jitter, circuit breakers, dynamic backoff, fallback sources, and quarantine/rewind for bad data.
3. **Lineage & Blast‑Radius Analysis** – End‑to‑end lineage (job, dataset, column) to quantify impact and drive safe rollbacks/backfills.
4. **Idempotent, Re‑runnable Tasks** – Safe to retry without duplicates; checkpointing and exactly‑once/at‑least‑once strategies.
5. **Governance‑Ready** – Audit trails, metadata, and policy hooks for PII and regulatory requirements.

### Reference Architecture (deployed in this repo)

* **Airflow** – Orchestration and scheduling of DAGs (pipelines), retries, SLAs, and task dependencies.
* **PostgreSQL** – Durable metadata store (Airflow Metadatabase) and example analytical sink.
* **Marquez (OpenLineage)** – Operational metadata + data lineage for jobs and datasets.
* **Kafka + Zookeeper (optional)** – Event streaming and dead‑letter queues for real‑time ingestion.
* **Neo4j (optional)** – Graph store for advanced lineage queries or anomaly/impact exploration.

> Note: Kafka/Neo4j are optional depending on your use case. The self‑healing patterns apply to both batch and streaming.

### Architecture Diagram (Mermaid)

```mermaid
graph TD
  U[Upstream Sources<br/>(APIs, DBs, Files)] -->|Extract| A[Airflow DAGs]
  A -->|Transform| T[Processing Tasks]
  T -->|Load| D[(Analytics Store / Postgres)]
  A -->|Emit metadata| M[Marquez / OpenLineage]
  K[(Kafka Broker)] -- optional --> A
  Z[(Zookeeper)] -- manages --> K
  M --> L[Lineage UI / Impact Analysis]
  subgraph Self-Healing Controls
    H1[Health Checks]
    H2[Retry Policies]
    H3[Circuit Breakers]
    H4[Fallback & Quarantine]
  end
  H1 -.-> A
  H2 -.-> A
  H3 -.-> A
  H4 -.-> A
```

---

## How Self‑Healing Works (Step‑by‑step)

1. **Detect**

   * **Liveness**: task heartbeat, scheduler health.
   * **Freshness**: *dataset X must update by 07:00 IST*; alert if late.
   * **Volume/Null/Uniqueness**: profile expectations (e.g., row count ±20%, null rate < 1%).
   * **Schema**: strict/compatible schema checks; optional contract enforcement.

2. **Classify** (Root‑Cause Hints)

   * Transient network/API issues vs. deterministic code/logic errors.
   * Upstream unavailability vs. downstream write/permission failures.
   * Data quality breach vs. structural (schema) drift.

3. **Remediate**

   * **Retry with backoff + jitter** for transient issues.
   * **Circuit break** dependent tasks to avoid cascading failures.
   * **Fallback Source** (e.g., cached snapshot, secondary API region) when primary is down.
   * **Quarantine** suspect batches to a **Dead‑Letter** area; continue healthy partitions.
   * **Backfill** once upstream stabilizes; compute only missing partitions (idempotent).

4. **Prove & Learn**

   * Emit **OpenLineage** events to Marquez for traceability.
   * Capture incident metadata and outcomes; update runbooks and policies.

---

## Example Failure Scenarios & Responses

### A) API Rate‑Limited During Peak Hours

* **Detection:** 429 responses spike + task SLA at risk.
* **Action:** Backoff and retry with jitter; switch to cached snapshot for read‑only features; resume primary once window clears.
* **Outcome:** No missed ingestion; downstream freshness within SLA.

### B) Late File Arrival from Vendor

* **Detection:** Freshness breach on `s3://vendor/d=date` by 06:30 IST.
* **Action:** Pause downstream joins; ingest previous day as placeholder; auto‑backfill once file lands; mark partitions reconciled.
* **Outcome:** Dashboards stay mostly current; final numbers reconcile automatically.

### C) Schema Drift (new column added)

* **Detection:** Contract mismatch on extract step.
* **Action:** Route batch to quarantine; continue ingesting other sources; notify owner; apply transform shim (ignore/new column mapping); reprocess.
* **Outcome:** No pipeline‑wide outage; controlled adaptation.

### D) Downstream Warehouse Write Failure

* **Detection:** Insert timeout / permission error.
* **Action:** Retry with exponential backoff; if persistent, write to staging; open ticket with lineage context; enable read path from last good partition.
* **Outcome:** Minimal downtime; clear blast‑radius view for responders.

---

## Operational Model

### SLAs & SLOs

* **Freshness SLOs** per dataset (e.g., D+1 by 07:00 IST; streaming p95 end‑to‑end < 2 minutes).
* **Reliability SLOs** per DAG (e.g., >99.5% successful daily runs).
* **Error Budget** to govern changes and deployments.

### Idempotency & Exactly‑Once

* Deterministic keys and upserts; watermarking/checkpointing for replay.
* Partitioned processing (by date/hour) to enable safe partial reruns.

### Observability

* Airflow task states, SLAs, retries, and logs.
* Marquez/OpenLineage for dataset↔job↔column lineage and impact analysis.
* Metrics: success rate, retry rate, time‑to‑detect, MTTR, number of quarantined batches.

---

## Governance, Security & Compliance

* **Access Control**: least‑privilege for orchestrator, storage, and sinks.
* **Data Classification**: tag PII/regulated datasets; restrict propagation.
* **Auditability**: lineage + run history + config versioning.
* **Privacy**: encrypt in transit (TLS) and at rest; key management via vault/KMS.

---

## What This Delivers to the Business

* **Faster Recovery:** MTTR reduced via automation and targeted remediation.
* **Protected SLAs:** Predictable data freshness for executive dashboards and ML features.
* **Traceability:** Know precisely which reports and models were impacted.
* **Lower Ops Cost:** Fewer midnight pages; fewer full‑pipeline reruns.
* **Trust:** Stakeholders regain confidence in data outputs.

**Sample ROI Levers**

* Avoid 2–4 hours/day of manual incident handling.
* Prevent missed campaign windows or erroneous decisions due to stale data.
* Faster onboarding of new pipelines due to consistent patterns and governance.

---

## Scope & Extensibility

* **In Scope:** Batch orchestration, optional streaming, lineage, health checks, automated remediation, quarantine/backfill patterns.
* **Out of Scope (baseline):** Real‑time schema registry, advanced ML‑driven anomaly detection (can be added), lakehouse optimization.

**Easy Extensions**

* Integrate a Data Quality framework (e.g., Great Expectations) to formalize tests.
* Add Slack/Teams on‑call routing with incident tickets pre‑filled from lineage.
* Promote Kafka dead‑letter topics for automated replay.
* Use Neo4j to explore lineage/impact as a graph at scale.

---

## FAQ (for non‑technical stakeholders)

**Q: Does this remove the need for data engineers?**
*A:* No. It removes repetitive firefighting so engineers can focus on features and governance.

**Q: Can it handle our existing pipelines?**
*A:* The patterns are technology‑agnostic. Airflow orchestrates Python/SQL/Spark/etc. We standardize retries, idempotency, and lineage across them.

**Q: How do we know it worked during an incident?**
*A:* Every remediation action is logged and linked in lineage. Dashboards show freshness, retries, quarantines, and backfills by dataset.

**Q: Is it safe for regulated data?**
*A:* Yes—lineage and audit trails, encryption, and role‑based access are first‑class concerns.

---

## Glossary

* **DAG:** Directed Acyclic Graph; defines task order in a pipeline.
* **Lineage:** Trace of data’s origin and transformations.
* **Quarantine/Dead‑Letter:** Holding area for suspect/failed records or batches.
* **Idempotent:** Safe to run the same task multiple times without side effects.
* **SLA/SLO:** Service Level Agreement/Objectives—commitments on freshness/reliability.

---

## Decision Checklist for Adopting Self‑Healing

* Do we have measurable data freshness targets for key datasets?
* Are tasks idempotent with clear partitioning and checkpoints?
* Do we emit lineage and health metrics for every job/dataset?
* Are remediation actions automated and auditable?
* Is there a clear, owned runbook for exceptions that cannot be automated?

---






# 🔄 How the Self-Healing Data Pipeline Works

The **Self-Healing Data Pipeline** continuously ingests, processes, monitors, and delivers high-quality data while automatically detecting and fixing issues.  
Here’s how the system works from start to finish:

---

## **Step 1: Data Ingestion**
- Data is collected from multiple sources:
  - APIs
  - Databases
  - Files (CSV, JSON, Parquet, etc.)
  - Streaming sources (optional)
- All raw data is stored temporarily in a **staging area**.

---

## **Step 2: Data Validation & Quality Checks**
- Before processing, the system automatically validates incoming data:
  - Checks for missing fields and invalid formats.
  - Ensures schema consistency.
  - Flags duplicate or corrupted records.
- Invalid data is **quarantined** without stopping the pipeline.

---

## **Step 3: Automatic Failure Detection**
- Every stage of the pipeline is monitored in real time.
- The system detects issues like:
  - Network/API failures.
  - Missing or delayed files.
  - Schema mismatches.
  - Data anomalies.
- Alerts are generated instantly for critical failures.

---

## **Step 4: Self-Healing & Remediation**
When an issue is detected, the pipeline **automatically responds**:
- **Retries** failed tasks with exponential backoff.
- **Fallbacks** to cached snapshots or alternate sources if primary sources fail.
- **Quarantines** faulty data batches to prevent contamination.
- **Backfills** missing data once the source becomes available.
- Keeps the rest of the pipeline running smoothly.

---

## **Step 5: Orchestration & Monitoring**
- The entire workflow is managed using **Apache Airflow**:
  - Automates task scheduling and dependencies.
  - Monitors the health of each data pipeline.
  - Automatically restarts failed tasks.
- Real-time dashboards show pipeline health, data freshness, and retry status.

---

## **Step 6: Data Transformation**
- Clean, validated data is processed:
  - Aggregations.
  - Joins.
  - Business rule applications.
  - Feature generation for analytics and machine learning.

---

## **Step 7: Data Delivery**
- Final processed data is delivered to:
  - Data warehouses.
  - Business dashboards.
  - Machine learning pipelines.
- Ensures **high availability** and **data consistency**.

---

## **Step 8: Observability & Lineage Tracking**
- The system integrates with **Marquez / OpenLineage** to track:
  - Job execution history.
  - Dataset lineage.
  - Column-level transformations.
- Provides full transparency for audits and troubleshooting.

---

## **Key Highlights**
- 🚀 **Always-On Data** → No pipeline-wide outages.  
- 🧠 **Smart Self-Healing** → Automated retries, fallbacks, and quarantines.  
- 📊 **Real-Time Monitoring** → Dashboards for pipeline health and SLAs.  
- 🔍 **Full Lineage Tracking** → Understand exactly where each data point comes from.  

---

🚀 Self-Healing Data Pipeline — Setup Guide

This section explains all commands required to set up, configure, and run the Self-Healing Data Pipeline from scratch.
It also includes common error fixes so you won’t get stuck.

📌 Prerequisites

Before starting, make sure you have installed:

Docker → Download

Docker Compose → Install

Git → Download

Python 3.10+ (optional, only if you plan to run Airflow CLI locally)

📂 1. Clone the Repository
git clone https://github.com/<your-username>/self-healing-data-pipeline.git
cd self-healing-data-pipeline

🐳 2. Build and Start the Containers
docker-compose up -d --build


✅ What this does:

Builds all services (Airflow Scheduler, Webserver, PostgreSQL, etc.)

Starts them in the background (-d means detached mode)

📌 3. Check Container Status
docker ps


You should see services like:

airflow-webserver

airflow-scheduler

postgres

airflow-worker (if using Celery)

⏳ 4. Check Airflow Webserver Health
docker inspect --format='{{.State.Health.Status}}' airflow-webserver


If it shows:
✅ healthy → proceed to next step.
⏳ starting → wait for a few minutes (1-3 mins).
❌ unhealthy → see Error Fix #1 below.

👤 5. Create an Admin User
docker-compose exec airflow-webserver airflow users create \
    --username admin \
    --firstname YourName \
    --lastname Admin \
    --role Admin \
    --email admin@example.com \
    --password admin

✅ One-liner Version
docker-compose exec airflow-webserver airflow users create --username admin --firstname YourName --lastname Admin --role Admin --email admin@example.com --password admin

🌐 6. Access the Airflow UI

Once healthy, open your browser and go to:

🔗 http://localhost:8080

Username: admin

Password: admin

🔄 7. Restart Services (If Needed)

If you make any config changes:

docker-compose down && docker-compose up -d

📜 8. View Live Logs

For debugging the Airflow Webserver:

docker-compose logs -f airflow-webserver


For checking all services:

docker-compose logs -f

🧹 9. Stop & Remove All Containers
docker-compose down


If you want to remove volumes (clears database, start fresh):

docker-compose down -v

🛠 Common Errors & Fixes
❌ Error 1: Airflow Webserver Stuck on starting
docker inspect --format='{{.State.Health.Status}}' airflow-webserver
# Output: starting


Fix:

docker-compose down -v
docker-compose up -d --build


This removes cached volumes and rebuilds everything fresh.

❌ Error 2: "No Module Named Airflow"

Fix:

docker-compose build --no-cache
docker-compose up -d

❌ Error 3: Database Migration Issues

If you see something like:

sqlalchemy.exc.OperationalError: could not connect to database


Fix:

docker-compose down -v
docker-compose up -d

❌ Error 4: Port 8080 Already in Use

Fix:

netstat -ano | findstr :8080  # Get the process ID using port 8080
taskkill /PID <PID> /F        # Kill that process
docker-compose up -d

⚡ Quick Start Summary
# 1. Clone repo
git clone https://github.com/<your-username>/self-healing-data-pipeline.git
cd self-healing-data-pipeline

# 2. Start services
docker-compose up -d --build

# 3. Create admin user
docker-compose exec airflow-webserver airflow users create \
    --username admin --firstname YourName --lastname Admin \
    --role Admin --email admin@example.com --password admin

# 4. Open Airflow UI
http://localhost:8080

🎯 Final Notes

This project uses Apache Airflow for orchestration.

It is designed to self-heal by retrying failed tasks, quarantining bad data, and automatically recovering pipelines.

All configurations are in docker-compose.yml and dags/.



docker-compose down -v
docker-compose up -d
docker exec -it airflow-webserver ls -l /opt/airflow/dags


http://localhost:8080


docker-compose exec airflow-webserver airflow users create --username admin --firstname YourName --lastname Admin --role Admin --email admin@example.com --password admin
