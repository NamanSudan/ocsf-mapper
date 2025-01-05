
```markdown:directory_structure.md
# Project Directory Structure

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

This updated structure reflects the Python Flask backend architecture, with separate services organized in a more Pythonic way. Key changes and additions include:

1. **Backend Organization**
   - Each service follows Flask best practices
   - Gunicorn configuration for production
   - Proper Python package structure with `__init__.py` files
   - Separated routes, services, and utilities

2. **Infrastructure**
   - Added Kubernetes manifests directory
   - Nginx configuration for reverse proxy
   - Separated Docker Compose files for dev/prod

3. **Frontend**
   - TypeScript-based React structure
   - Organized component hierarchy
   - Dedicated services and utilities folders

4. **CI/CD**
   - GitHub Actions workflows
   - Deployment and rollback scripts
   - Make commands for common operations

5. **Documentation**
   - API specifications with Swagger
   - Separate guides for development and deployment
   - Architecture documentation

This structure supports both development and production environments while maintaining clear separation of concerns and following Python/Flask best practices.