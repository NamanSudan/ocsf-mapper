```markdown:design_doc.md
# Detailed Design Document

## 1. Overview

This document provides an in-depth look at how to build a modular, maintainable repository for a “dynamic security log mapping” tool that uses Trieve’s hybrid search and RAG features to map incoming logs to OCSF classes. By separating each layer (ingestion, knowledge base, search/classification, user interface, etc.) into its own module, we facilitate maintainability, extensibility, and clarity.

--------------------------------------------------------------------------------
## 2. Repository Structure

Below is the detailed structure for the repository:

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
│   │   ├── config.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── chunks.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── chunk_manager.py
│   │   │   └── ocsf_parser.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── helpers.py
│   └── tests/
│       ├── __init__.py
│       └── test_chunks.py
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

Each service is containerized and follows a clean, modular Python structure with proper separation of concerns. The backend services use FastAPI/Flask with gunicorn, while the frontend uses React/TypeScript.

--------------------------------------------------------------------------------
## 3. Detailed Components and Responsibilities

### 3.1 Ingestion Service
- **Directory**: `backend/ingestion_service/`  
- **Purpose**: Accepts logs from Vector.dev (or another aggregator) and normalizes them into a consistent JSON structure.  
- **Key Tasks**:  
  1. Listen for new log events via Flask endpoints.
  2. Normalize raw data fields (e.g., timestamps, hostnames).
  3. Add simple heuristics or ML-based tags if desired (optional).
  4. Forward the normalized logs to the Classification Service, or queue them in a message broker.

**Technologies**:  
- Python Flask with Gunicorn for production deployment
- RESTful API endpoints defined in `routes/ingestion.py`
- Core processing logic in `services/log_processor.py`
- Utility functions for normalization in `utils/normalizer.py`
- Unit tests in `tests/` directory

### 3.2 Knowledge Base
- **Directory**: `backend/knowledge_base/`  
- **Purpose**: Converts OCSF specification documents into chunks for ingestion into Trieve.  
- **Key Tasks**:  
  1. Parse each OCSF class specification via `services/ocsf_parser.py`
  2. Convert them into robust textual chunks using `services/chunk_manager.py`
  3. Call the Trieve "create chunk" or "upsert chunk" endpoints via `trieve-py-client`
  4. Manage chunk metadata (e.g., OCSF class ID, links, categories)

**Technologies**:  
- Python Flask application with RESTful endpoints
- Trieve Python client ("trieve-py-client") for chunk management
- Structured service layer for OCSF parsing and chunk creation
- Comprehensive test coverage with pytest

### 3.3 Classification Service
- **Directory**: `backend/classification_service/`  
- **Purpose**: Receives normalized logs and determines the best OCSF class via Trieve.  
- **Key Tasks**:  
  1. Expose RESTful endpoints in `routes/classification.py`
  2. Use `services/trieve_client.py` for hybrid search
  3. Optional re-ranking via `services/ml_reranker.py`
  4. Store results to ClickHouse

**Technologies**:  
- Python Flask with Gunicorn for high-performance serving
- Integration with Trieve via Python client
- ML/LLM integration for re-ranking when needed
- Structured error handling and logging

### 3.4 Frontend
- **Directory**: `frontend/`  
- **Purpose**: React/TypeScript interface for security analysts
- **Key Components**:  
  - `components/dashboard/`: Real-time event monitoring
  - `components/classification/`: Review and override UI
  - `components/common/`: Shared UI elements
  - `services/`: API integration with backend
  - `utils/`: Helper functions and types

**Technologies**:  
- React with TypeScript
- Modern component architecture
- Integration with Trieve's React components
- Comprehensive test coverage

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

