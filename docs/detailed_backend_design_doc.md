```markdown:detailed_backend_design_doc.md
# Detailed Backend Design Document

## 1. Overview

This document provides an in-depth look at how to build a modular, maintainable repository for a "dynamic security log mapping" tool that uses Trieve's hybrid search and RAG features to map incoming logs to OCSF classes. By separating each layer (ingestion, knowledge base, search/classification, etc.) into its own module, we facilitate maintainability, extensibility, and clarity on the backend side.

---

## 2. Repository Structure

Below is a suggested structure for the repository, with a high-level description of each backend component. Note that this design can be adapted to your organization's preferred patterns (e.g., monorepo vs. multiple repos). For simplicity, we'll use a single repository with distinct directories.

```
ocsf-mapping/
├── backend/
│   ├── ingestion_service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── gunicorn.conf.py
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── app.py
│   │   │   ├── config.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   └── ingestion.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   └── log_processor.py
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       └── normalizer.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_ingestion.py
│   │
│   ├── classification_service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── gunicorn.conf.py
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── app.py
│   │   │   ├── config.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   └── classification.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── trieve_client.py
│   │   │   │   └── ml_reranker.py
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       └── helpers.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_classification.py
│   │
│   └── knowledge_base/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── src/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── config.py
│       │   ├── routes/
│       │   │   ├── __init__.py
│       │   │   └── chunks.py
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── chunk_manager.py
│       │   │   └── ocsf_parser.py
│       │   └── utils/
│       │       ├── __init__.py
│       │       └── helpers.py
│       └── tests/
│           ├── __init__.py
│           └── test_chunks.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── public/
│   │   ├── index.html
│   │   └── assets/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── dashboard/
│   │   │   └── classification/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── index.tsx
│   └── tests/
│       └── components/
│
├── infrastructure/
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.prod.yml
│   │   └── env/
│   │       ├── trieve.env.example
│   │       ├── clickhouse.env.example
│   │       └── redis.env.example
│   │
│   ├── k8s/
│   │   ├── base/
│   │   │   ├── deployments/
│   │   │   ├── services/
│   │   │   └── kustomization.yaml
│   │   └── overlays/
│   │       ├── dev/
│   │       └── prod/
│   │
│   └── nginx/
│       ├── Dockerfile
│       └── nginx.conf
│
├── scripts/
│   ├── setup/
│   │   ├── local_dev_setup.sh
│   │   └── install_dependencies.sh
│   ├── test/
│   │   └── run_tests.sh
│   └── deployment/
│       ├── deploy_prod.sh
│       └── rollback.sh
│
├── docs/
│   ├── architecture/
│   │   ├── high-level-design.md
│   │   └── tech-stack.md
│   ├── api/
│   │   └── swagger.yaml
│   └── guides/
│       ├── development.md
│       └── deployment.md
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
│
├── .gitignore
├── README.md
├── LICENSE
├── Makefile
└── pyproject.toml
```

Each sub-directory (e.g., `ingestion-service`, `knowledge-base`) stands alone—potentially containerized via Docker—and has minimal dependencies on the others, besides environment variables or well-defined API contracts.

---

## 3. Detailed Components and Responsibilities

### 3.1 Ingestion Service
- **Directory**: `ingestion-service/`  
- **Purpose**: Accepts logs from Vector.dev (or another aggregator) and normalizes them into a consistent JSON structure.  
- **Key Tasks**:  
  1. Listen for new log events.  
  2. Normalize raw data fields (e.g., timestamps, hostnames).  
  3. Add simple heuristics or ML-based tags if desired (optional).  
  4. Forward the normalized logs to the Classification Service, or queue them in a message broker (RabbitMQ, Redis, or Kafka).  

**Technologies**:  
- Node.js or Python (whatever your team prefers).  
- Dockerfile builds a container that can run continuously.  
- Uses environment variables (`.env`) for external connections.  

---

### 3.2 Knowledge Base
- **Directory**: `knowledge-base/`  
- **Purpose**: Converts OCSF specification documents (from the OCSF GitHub or internal docs) into chunks for ingestion into Trieve.  
- **Key Tasks**:  
  1. Parse each OCSF class specification (e.g., “Authentication,” “NetworkActivity,” etc.).  
  2. Convert them into robust textual chunks, possibly one chunk per subtopic or example.  
  3. Call the Trieve “create chunk” or “upsert chunk” endpoints to store OCSF references.  
  4. Manage chunk metadata (e.g., OCSF class ID, links, categories).  

**Technologies**:  
- Node.js or Python script using the “trieve-ts-sdk” or “trieve-py-client” to create/update chunks.  
- Can run periodically or be a one-time ingestion job.  

---

### 3.3 Classification Service
- **Directory**: `classification-service/`  
- **Purpose**: Receives normalized logs from the Ingestion Service (or message queue) and determines the best OCSF class via Trieve. Potentially also calls an LLM re-ranker or cross-encoder.  
- **Key Tasks**:  
  1. Perform a “hybrid search” on the log text or relevant fields (SPLADE + embeddings) using Trieve.  
  2. Retrieve top N candidate OCSF classes.  
  3. (Optional) Re-rank with a cross-encoder or short LLM-based prompt to ensure best match.  
  4. Output final classification + confidence score, and store it in a database like ClickHouse.  

**Technologies**:  
- Node.js (using “trieve-ts-sdk”) or Rust (calling Trieve’s REST endpoints).  
- Could run an LLM microservice or a local model to re-rank.  

---

### 3.4 UI (Optional in Backend-Focused View)
While the UI is not strictly part of the backend, it may be included in the monorepo for convenience. Analysts and operators can view or override classification results here.

---

### 3.5 docker/
- **Directory**: `docker/`  
- **Purpose**: Contains Docker Compose files and environment variable templates to run all services (and their dependencies) together.  
- **Contents**:  
  1. `docker-compose.yml`: Pulls in ingestion-service, classification-service, Qdrant, ClickHouse, Redis, optionally a local Trieve instance, etc.  
  2. `trieve.env`: Basic config for connecting to the Trieve server or for creating ephemeral local instances.  
  3. `clickhouse.env`, etc.  

**Example**:
```yaml
services:
  ingestion-service:
    build: ./ingestion-service
    environment:
      - SOME_SERVICE_URL=http://classification-service:3000
    ports:
      - "8081:8080"

  classification-service:
    build: ./classification-service
    environment:
      - TRIEVE_API_KEY=${TRIEVE_API_KEY}
      - TRIEVE_DATASET_ID=${DATASET_ID}
    ports:
      - "3000:3000"

  trieve:
    image: devflowinc/trieve:latest
    environment: 
      - ...
    ports:
      - "8082:8080"

  # ... Qdrant, ClickHouse, Redis, etc.
```
Use `.env` or environment variables for secrets, e.g., `TRIEVE_API_KEY`.

---

### 3.6 scripts/
- **Directory**: `scripts/`  
- **Purpose**: Utility scripts for local development, data loading, or testing.  
- **Examples**:  
  - `local_dev_setup.sh`: Installs dependencies, spins up Docker containers.  
  - `load_sample_data.sh`: Downloads sample logs from OCSF’s GitHub, loads them.  
  - `run_tests.sh`: Orchestrates unit tests, integration tests, etc.  

---

### 3.7 docs/
- **Directory**: `docs/`  
- **Purpose**: Main documentation for explaining architecture, design, operations, and usage.  
- **Subdirectories**:  
  - `design-docs/` for in-depth designs (like this one).  
  - Diagrams or user guides.  

---

## 4. Data Flow Example

Below is a typical step-by-step example illustrating how logs flow through the system on the backend:

1. **Ingestion**  
   - Vector.dev picks up a Windows 4624 event log and pushes it to the `ingestion-service`.  
   - `ingestion-service` normalizes it and either calls a classification endpoint or queues it in a message broker.

2. **Classification**  
   - The `classification-service` takes the normalized log text.  
   - Calls Trieve (hybrid search or semantic search).  
   - The top 3 OCSF classes are returned with scores.  
   - Optionally re-rank with a cross-encoder or an LLM.  
   - The best class is selected and stored in ClickHouse.

3. **Knowledge Base Refresh**  
   - The `knowledge-base` code might run daily or on file changes to parse new/updated OCSF classes or examples.  
   - The newly found documentation is chunked and upserted into Trieve for improved classification.

4. **UI / Analytics** (Optional from the backend’s perspective)  
   - Provides an interface for SOC analysts or business users to see logs, override classifications, etc.

---

## 5. Implementation and Configuration

1. **Language & Framework**:  
   - Node.js for ingestion & classification is straightforward but Python or Rust also combine well with Trieve’s REST or Python client.  

2. **Environment Variables**:  
   - `TRIEVE_API_KEY`, `DATASET_ID`, `ORGANIZATION_ID`, etc. for connecting to self-hosted or hosted Trieve.  
   - `REDIS_URL`, `CLICKHOUSE_URL`, etc. for your infrastructure.  
   - Keep them in `.env.example` for local development.

3. **Local vs. Production**:  
   - **Local**: `docker-compose up -d` from the root to spin up everything (Trieve, Qdrant, classification, UI, etc.).  
   - **Production**: Could replicate with Kubernetes or Docker Swarm.  

4. **Deployment**:  
   - Each microservice has a Dockerfile.  
   - The `docker-compose.yml` orchestrates them for dev or PoC.  
   - In production, you might use external Postgres/MySQL for Trieve’s relational store, Qdrant for vector search, and ClickHouse for large-scale analytics.

---

## 6. Scalability Considerations

- **Sharding**: If log volumes are large, you may shard by source or time.  
- **Autoscaling**: Horizontal scale classification-service pods as needed.  
- **Queue Backpressure**: Use Kafka, RabbitMQ, or Redis streams to handle spikes.  
- **LLM Load**: If cross-encoder or real-time LLM calls are heavy, consider caching or batching.

---

## 7. Future Enhancements

1. **Self-Improving Pipeline**: Capture user overrides into an active learning loop to fine-tune your re-ranker or classification approach.  
2. **Custom LLM**: If open-source LLM deployment is feasible, your classification-service could shift to using Mistral 7B or Llama 2 on GPUs.  
3. **Support Additional Schemas**: Expand beyond OCSF to MITRE ATT&CK or custom domain schemas.  
4. **Alerting**: Integrate Slack, Teams, or email to alert if certain classes appear at high volume.

---

## 8. Conclusion

By structuring the backend into modular services—Ingestion, Knowledge Base, Classification—the solution remains clean, extensible, and straightforward to maintain. Each piece interacts minimally with the others, primarily through well-defined API calls or queues and environment variables. Trieve provides the core search and RAG features you need for robust classification, with flexibility to incorporate advanced re-ranking or analytics when needed.
```
