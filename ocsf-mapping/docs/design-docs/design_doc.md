```markdown:design_doc.md
# Detailed Design Document

## 1. Overview

This document provides an in-depth look at how to build a modular, maintainable repository for a “dynamic security log mapping” tool that uses Trieve’s hybrid search and RAG features to map incoming logs to OCSF classes. By separating each layer (ingestion, knowledge base, search/classification, user interface, etc.) into its own module, we facilitate maintainability, extensibility, and clarity.

--------------------------------------------------------------------------------
## 2. Repository Structure

Below is a suggested structure for the repository, along with a high-level description of each component. Note that this design can be adapted to your organization’s preferred patterns (e.g., monorepo vs. multiple repos). For simplicity, we’ll use a single repository with distinct directories.

```
ocsf-mapping/
├── docs/
│   └── design-docs/
│       └── detailed-design.md
│       └── user-stories.md
│       └── architecture-diagrams.svg
├── ingestion-service/
│   ├── Dockerfile
│   ├── src/
│   │   └── ingest_logs.ts  # or ingest_logs.py, main entry
│   ├── README.md
│   └── package.json        # (if using Node.js)
├── knowledge-base/
│   ├── Dockerfile
│   ├── src/
│   │   ├── parse_ocsf_specs.ts
│   │   ├── create_chunks.ts
│   │   └── ...
│   ├── README.md
│   └── package.json
├── classification-service/
│   ├── Dockerfile
│   ├── src/
│   │   ├── classification_pipeline.ts
│   │   ├── cross_encoder_reranker.ts
│   │   └── ...
│   └── package.json
├── ui/
│   ├── Dockerfile
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── main.tsx
│   ├── package.json
│   └── README.md
├── docker/
│   ├── docker-compose.yml
│   ├── trieve.env
│   ├── clickhouse.env
│   └── ...
├── scripts/
│   ├── local_dev_setup.sh
│   ├── load_sample_data.sh
│   └── run_tests.sh
├── .env.example
├── .gitignore
├── package.json (optional root-level if needed)
├── README.md
└── LICENSE
```

Each sub-directory (e.g., `ingestion-service`, `knowledge-base`) stands alone—potentially containerized via Docker—and has minimal dependencies on the others, besides environment variables or well-defined API contracts.

--------------------------------------------------------------------------------
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
- Dockerfile: Builds a container that can run continuously.  
- Configuration: Usually references an `.env` or environment variables for external connections.  

### 3.2 Knowledge Base
- **Directory**: `knowledge-base/`  
- **Purpose**: Converts OCSF specification documents (from the OCSF GitHub, or internal docs) into chunks for ingestion into Trieve.  
- **Key Tasks**:  
  1. Parse each OCSF class specification (e.g., “Authentication,” “NetworkActivity,” etc.).  
  2. Convert them into robust textual chunks, possibly one chunk per subtopic or example.  
  3. Call the Trieve “create chunk” or “upsert chunk” endpoints to store OCSF references.  
  4. Manage chunk metadata (e.g., OCSF class ID, links, categories).  

**Technologies**:  
- Node.js or Python script that uses the “trieve-ts-sdk” or “trieve-py-client” to create/update chunks.  
- This can run periodically or be a one-time ingestion job.  

### 3.3 Classification Service
- **Directory**: `classification-service/`  
- **Purpose**: Receives normalized logs from the Ingestion Service (or message queue) and determines the best OCSF class via Trieve. Potentially also calls an LLM re-ranker or cross-encoder.  
- **Key Tasks**:  
  1. Perform a “hybrid search” on the log text or relevant fields (SPLADE + Embeddings) using Trieve.  
  2. Retrieve top N candidate OCSF classes.  
  3. (Optional) Re-rank with a cross-encoder or short LLM-based prompt to ensure best match.  
  4. Output final classification + confidence score, store to a database like ClickHouse.  

**Technologies**:  
- Node.js (using “trieve-ts-sdk”) or Rust (calling Trieve’s REST endpoints).  
- The classification-service might also have an LLM microservice or a local model to re-rank.  

### 3.4 UI
- **Directory**: `ui/`  
- **Purpose**: Provide a front-end interface for security analysts to:  
  1. Review classification results in near real-time.  
  2. Override or correct misclassifications.  
  3. Inspect OCSF references and chunk highlights for transparency.  
- **Key Tasks**:  
  - Interactive dashboard: Show logs, predicted OCSF class, confidence, reference snippet.  
  - Batch review: Analysts can see suspicious or low-confidence mappings.  
  - Feedback loops: Overridden mappings feed back into future training or incremental improvement.  

**Technologies**:  
- Any modern framework (React, Vue, Solid.js).  
- Possibly includes “TrieveSearch” (the Web Component or React component from “trieve-ts-sdk”).  
- Docker container for hosting if needed.  

### 3.5 docker/
- **Directory**: `docker/`  
- **Purpose**: Contains Docker Compose files and environment variable templates to run all services (and their dependencies) together.  
- **Contents**:  
  1. `docker-compose.yml`: Pulls in ingestion-service, classification-service, UI, Trieve instance, Qdrant, ClickHouse, Redis, etc.  
  2. `trieve.env`: Basic config for connecting to the Trieve server or for setting up an ephemeral Trieve instance.  
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
Use `.env` or environment variables for secrets, e.g., TRIEVE_API_KEY or other keys.

### 3.6 scripts/
- **Directory**: `scripts/`  
- **Purpose**: Utility scripts for local development, data loading, or testing.  
- **Examples**:  
  - `local_dev_setup.sh`: Install dependencies, spin up Docker containers.  
  - `load_sample_data.sh`: Download sample logs from OCSF’s GitHub, load them.  
  - `run_tests.sh`: Orchestrates unit tests, integration tests, etc.  

### 3.7 docs/
- **Directory**: `docs/`  
- **Purpose**: Main documentation for explaining architecture, design, operations, and usage.  
- **Subdirectories**:  
  - `design-docs/` for in-depth designs like this file.  
  - Diagrams or user guides.  

--------------------------------------------------------------------------------
## 4. Data Flow Example

Below is a typical step-by-step example illustrating how logs flow through the system:

1. **Ingestion**  
   - Vector.dev picks up a Windows 4624 event log and pushes it to the `ingestion-service`.  
   - `ingestion-service` normalizes it and puts it into a queue or calls a classification endpoint.

2. **Classification**  
   - `classification-service` takes the normalized log text.  
   - Calls `trieve` with a hybrid search.  
   - The top 3 OCSF classes are returned with scores.  
   - Optional cross-encoder re-rank.  
   - The best class is selected.  
   - The classification result is saved to ClickHouse.

3. **UI**  
   - Security analysts open the web UI at `ui/`.  
   - They see recent classifications, any flagged or uncertain events.  
   - If a log is misclassified, they override it.  
   - The system captures the override for future improvement.

4. **Knowledge Base Refresh**  
   - Meanwhile, the `knowledge-base` code might run daily (or triggered on OCSF spec changes) to parse new/updated OCSF classes or examples.  
   - The newly found documentation is chunked and upserted into Trieve.

--------------------------------------------------------------------------------
## 5. Implementation and Configuration

1. **Language & Framework**: 
   - Node.js for ingestion & classification is straightforward, especially with “trieve-ts-sdk.”  
   - Python or Rust are also valid choices; just ensure consistent integration with Trieve’s REST or Python client.  

2. **Environment Variables**:
   - `TRIEVE_API_KEY`, `DATASET_ID`, `ORGANIZATION_ID`, etc. for connecting to a self-hosted or hosted Trieve instance.  
   - `REDIS_URL`, `CLICKHOUSE_URL`, or other connection strings.  
   - Keep them in `.env.example`. Do not commit real keys to the repo.

3. **Local vs. Production**:
   - **Local**: `docker-compose up -d` from the root to spin up everything (Trieve, Qdrant, classification, UI).  
   - **Production**: Potentially replicate this with Kubernetes or Docker Swarm.  
   - A `deployment/` folder or `helm/` folder can hold K8s charts if you prefer.

4. **Deployment**:
   - Each microservice has a Dockerfile.  
   - The `docker-compose.yml` orchestrates them for dev or POC.  
   - For production, you may prefer an external Postgres or MySQL for Trieve’s relational storage, Qdrant for vectors, ClickHouse for analytics, etc.

--------------------------------------------------------------------------------
## 6. Scalability Considerations

- **Sharding**: If log volumes are large, you may want to shard by event source or time interval.  
- **Autoscaling**: Horizontal scale classification-service pods.  
- **Queue Backpressure**: If logs spike, ensure your message queue (e.g. Kafka or RabbitMQ) can handle it.  
- **LLM Load**: If you do real-time cross-encoder or big LLM calls, watch for overhead. Caching or batching calls might be necessary.

--------------------------------------------------------------------------------
## 7. Future Enhancements

1. **Self-Improving Pipeline**: Capture user overrides into an active learning loop that fine-tunes your re-ranker or classification approach.  
2. **Custom LLM**: If open-source LLM deployment is feasible, your classification-service could shift to using Mistral 7B or Llama 2 quantized on GPUs.  
3. **Additional Schemas**: Expand beyond OCSF to MITRE ATT&CK or custom schema definitions.  
4. **Alerting**: Integrate with Slack, Teams, or Email to alert analysts if certain classes appear with high volume.  

--------------------------------------------------------------------------------
## 8. Conclusion

By structuring the repository into modular services—Ingestion, Knowledge Base, Classification, UI—the solution remains clean, extensible, and easy to reason about. Each piece interacts minimally with the others, primarily through well-defined API calls and environment variables. Trieve provides the bedrock search and RAG capabilities you need for robust classification while letting you scale features like cross-encoder re-ranking, LLM classification, or advanced analytics in a controlled manner.
```