```markdown:implementation_guide.md
# Implementation Guide

This document provides a high-level overview and step-by-step reference for setting up and starting development on the dynamic security log mapping tool. It is designed to work alongside the existing design documents (e.g., "backend_design_doc.md") and technology overviews (e.g., "tech_stack.md"). The goal is to help you get your environment running, outline basic workflows, and prepare the ground for further integrations—such as Trieve-specific functionality—after you complete these initial steps.

---

## 1. Overview

1. Establish a local environment that includes the ingestion service, classification service, knowledge base, and any necessary data stores.  
2. Define consistent development practices: code style, linting, testing, and CI/CD pipelines.  
3. Provide a blueprint for deploying or scaling the system in a containerized environment (Docker Compose for local, potentially Kubernetes for production).  
4. Serve as a foundation for eventual Trieve integration—once the basic system is operational, Trieve-specific features can be layered on top.

---

## 2. Prerequisites

• Python 3.9+ environment (system-wide or via a virtual environment).  
• Docker and Docker Compose installed (for local container orchestration).  
• (Optional) GitHub Actions or another CI pipeline if you want continuous integration from the start.  
• Basic familiarity with Python Flask or similar frameworks.

---

## 3. Repository Structure Review

If you have not already, familiarize yourself with the repository structure referenced in “backend_design_doc.md”:

```
ocsf-mapping/
├── docs/
│   └── design-docs/
├── ingestion-service/
├── knowledge-base/
├── classification-service/
├── ui/
├── docker/
├── scripts/
├── .env.example
├── .gitignore
├── README.md
└── ...
```

Each folder typically contains its own source code, Dockerfile, and configuration. The “docker/” folder includes Compose files that orchestrate the microservices and supporting databases.

---

## 4. Environment Setup

### 4.1 Clone the Repository

Begin by cloning the repository to your local machine:

```bash
git clone https://github.com/<your-org>/<ocsf-mapping>.git
cd ocsf-mapping/
```

### 4.2 Python Virtual Environment (Local Development)

Although Docker Compose can run everything in containers, some prefer testing Python code locally before containerizing:

```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows

pip install -r requirements.txt
```

(If you have separate requirements within each service’s folder, install those similarly.)

### 4.3 Environment Variables

In the root directory (or each microservice directory), copy `.env.example` to `.env`. Update placeholders (like DB URLs, message queue URLs) with your local or default values:

```bash
cp .env.example .env
# Modify TRIEVE_API_KEY=...
# Modify DB_HOST=...
# etc.
```

(If you do not have final credentials, keep placeholders for now.)

---

## 5. Local Development Workflow

### 5.1 Docker Compose

The easiest way to run all services together locally:

```bash
cd docker
docker-compose up --build
```

This command:  
1. Builds each service image (ingestion-service, classification-service, ui, etc.).  
2. Spins up supporting containers (ClickHouse, Redis, Qdrant/Trieve self-hosted if applicable).  
3. Exposes ports (e.g., 5000 for Flask services, 8080 for a local Trieve instance, 8123 for ClickHouse).

### 5.2 Accessing Services

• Ingestion Service (Flask): http://localhost:5001 or a configured port.  
• Classification Service (Flask): http://localhost:5002 or a configured port.  
• UI: http://localhost:3000 or whichever port is defined in docker-compose.yml.  
• ClickHouse: http://localhost:8123 or a relevant port.

(Exact port mappings may vary based on your docker-compose.yml.)

### 5.3 Verification & Logging

• Use Docker logs:  
  ```bash
  docker-compose logs -f ingestion-service
  ```  
• Check if you see messages indicating successful startup.  
• Test basic endpoints with a tool like curl or Postman:
  ```bash
  curl http://localhost:5001/health
  ```

---

## 6. Basic Usage Example

1. **Ingest Sample Logs**:  
   - Run the ingestion service or call its endpoint with sample log data (e.g., Windows Event 4624).  
   - The service normalizes and forwards logs to classification, or to a message queue.

2. **Classify with Knowledge Base**:  
   - Classification service receives normalized logs.  
   - It queries the knowledge base (if integrated) or returns a placeholder classification.  
   - Results are stored in ClickHouse or printed in the container logs.

3. **UI** (Optional for Now):  
   - If you also brought up the UI container, open a browser at http://localhost:3000 to see a minimal dashboard.  
   - Confirm that logs and classification results appear.

At this point, you have a minimal end-to-end pipeline. The next stage is to refine the classification logic, integrate an actual OCSF knowledge base, and eventually incorporate Trieve for advanced retrieval.

---

## 7. Development Guidelines

### 7.1 Code Conventions & Linting

• **Python**: Use [Black](https://github.com/psf/black) and [Flake8](https://github.com/pycqa/flake8) for formatting and linting.  
• **Commit Hooks**: Optionally set up pre-commit hooks to enforce style checks before pushing.

### 7.2 Testing

• Write unit tests for ingestion, classification logic, etc.  
• Place them in a `/tests` folder within each service.  
• Use [pytest](https://docs.pytest.org/) for test discovery.  
• For integration tests, spin up Docker Compose, run a test script that executes real calls.

### 7.3 CI/CD Pipeline

• Implement GitHub Actions (or another CI system) to run builds, lint checks, and tests on each pull request.  
• Attach artifact building or Docker image pushes to certain branches (e.g., main / release).

---

## 8. Architecture Extension: Trieve Integration

• This guide focuses on base-level ingestion, classification, and environment setup.  
• Once stable, refer to “trieve_integration_guide.md” for connecting the classification-service to a running Trieve instance or using the “trieve-py-client.”  
• This layered approach ensures you have all local infrastructure validated before injecting advanced search or RAG calls to Trieve.

---

## 9. Next Steps

1. **Populate Knowledge Base**: Start ingesting OCSF references or real docs into the knowledge-base service.  
2. **Enhance Classification**: Integrate light ML or rule-based classification logic.  
3. **Optimize Performance**: Evaluate message queue usage (Kafka, RabbitMQ, or Redis streams) if you expect high log throughput.  
4. **Add Observability**: Include logs, metrics, and tracing with tools like Prometheus + Grafana or ELK.  
5. **Trieve Integration**: Move on to the “trieve_integration_guide.md” to incorporate hybrid search and RAG capabilities.

---

## 10. Summary

• You now have a clear path to set up and develop the ingestion, knowledge base, and classification services, along with Docker container orchestration.  
• Testing and validating these fundamental pieces lays the groundwork for further expansions—especially advanced search and classification with Trieve.  
• As you proceed, keep environment variables, CI/CD, and service isolation in mind for seamless scaling.

Happy Building!
```
