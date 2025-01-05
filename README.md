# OCSF Log Mapping Tool

A dynamic security log mapping tool that uses Trieve's hybrid search and RAG features to map incoming logs to OCSF classes. The system integrates Vector.dev for log ingestion and provides a scalable architecture for processing and classifying security logs.

## Architecture Overview

The system consists of several microservices:

1. **Ingestion Service**
   - Accepts logs from Vector.dev
   - Normalizes log formats
   - Queues logs for classification
   - Provides metrics and monitoring

2. **Classification Service**
   - Uses Trieve for hybrid search and RAG
   - Implements cross-encoder reranking
   - Classifies logs according to OCSF schema

3. **Supporting Services**
   - Redis for message queuing
   - ClickHouse for log storage
   - Prometheus for metrics collection

## Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Vector.dev
- Trieve API credentials

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/your-org/ocsf-mapping.git
cd ocsf-mapping
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the services:
```bash
cd docker
docker-compose up --build
```

## Service Configuration

### Vector.dev Setup
Vector configuration is located in `docker/vector/vector.toml`. It's configured to:
- Collect logs from multiple sources (files, syslog, Windows events)
- Normalize timestamps and fields
- Forward to the ingestion service

### Ingestion Service
Handles log ingestion and normalization:
- Endpoint: `http://localhost:8080/ingest`
- Health check: `http://localhost:8080/health`
- Metrics: `http://localhost:8080/metrics`

### Classification Service
Provides log classification using Trieve:
- Endpoint: `http://localhost:8081/classify`
- RAG endpoint: `http://localhost:8081/rag`
- Chunk management: `http://localhost:8081/chunks`

## Development

### Local Development Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Running Tests
```bash
cd scripts
./run_tests.sh
```

### Adding New Log Sources
1. Update Vector configuration in `docker/vector/vector.toml`
2. Add corresponding processor in `ingestion-service/src/vector_handler.py`
3. Update tests and documentation

## Monitoring & Metrics

The system provides Prometheus metrics for:
- Log ingestion rates
- Processing times
- Queue sizes
- Error rates

Access metrics at:
- Ingestion Service: `http://localhost:8080/metrics`
- Classification Service: `http://localhost:8081/metrics`

## API Documentation

### Ingestion Service

#### POST /ingest
Accepts logs from Vector.dev:
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "message": "User login successful",
  "source": "windows_event_log",
  "event_id": 4624
}
```

### Classification Service

#### POST /classify
Classifies a log entry:
```json
{
  "message": "User login successful",
  "context_size": 3
}
```

#### POST /rag
Performs RAG operations:
```json
{
  "query": "User login event",
  "context_size": 3
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details.

## Documentation

Additional documentation can be found in the `/docs` directory:
- `design-docs/detailed-design.md`: Overall system design
- `design-docs/detailed_backend_design_doc.md`: Backend implementation details
- `design-docs/detailed_vectorDev_integration_guide.md`: Vector.dev integration guide
- `design-docs/trieve_integration_guide.md`: Trieve integration details 