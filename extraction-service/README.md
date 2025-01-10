# OCSF Extraction Service

A microservice designed to extract and store OCSF (Open Cybersecurity Schema Framework) schema data. This service is part of the OCSF Mapper project and is responsible for fetching schema definitions from the OCSF API.

## Features

- Extracts OCSF schema components:
  - Categories (`ocsf_categories.json`)
  - Classes (`ocsf_classes.json`)
  - Base Events (`ocsf_base_events.json`)
  - Complete Schema (`ocsf_schema.json`)
- RESTful API endpoints for each extraction type
- Automatic data storage in JSON format
- Comprehensive logging
- Health check endpoint
- Docker support

## Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- Access to OCSF Schema API (schema.ocsf.io)

## Installation

### Local Development

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the service:
```bash
python -m flask run --host=0.0.0.0 --port=8083
```

### Docker Deployment

The service is included in the project's docker-compose configuration:

```bash
# From the root directory
docker-compose -f docker/docker-compose-ocsf.yml up -d extraction-service
```

## API Endpoints

### Health Check
```
GET /health
Response: {"status": "healthy"}
```

### Extract Categories
```
POST /extract/ocsf/categories
Response: {"status": "success", "message": "Categories extracted successfully"}
```

### Extract Classes
```
POST /extract/ocsf/classes
Response: {"status": "success", "message": "Classes extracted successfully"}
```

### Extract Base Event
```
POST /extract/ocsf/base-event
Response: {"status": "success", "message": "Base events extracted successfully"}
```

### Extract Schema
```
POST /extract/ocsf/schema
Response: {"status": "success", "message": "Schema extracted successfully"}
```

## Data Storage

Extracted data is stored in the `data/ocsf` directory:
- `ocsf_categories.json`: OCSF categories (~46KB)
- `ocsf_classes.json`: OCSF classes (~40KB)
- `ocsf_base_events.json`: Base event definitions (~16KB)
- `ocsf_schema.json`: Complete OCSF schema (~2.5MB)

Note: The data directory is git-ignored. Run the extraction to generate these files.

## Utility Scripts

### Extract All Data
To extract all OCSF schema components at once:

```bash
# From the root directory
./scripts/extract_all_ocsf_data.sh
```

The script provides colored output showing the progress and status of each extraction.

## Error Handling

- HTTP errors are logged with detailed error messages
- File system errors are caught and reported
- Each extraction endpoint returns appropriate HTTP status codes
- Failed extractions don't affect other extractions

## Logging

The service implements comprehensive logging:
- Request/response logging
- File operation logging
- Error logging with stack traces
- Extraction status and progress

## Development

### Project Structure
```
extraction-service/
├── data/
│   └── ocsf/           # Extracted schema files
├── src/
│   ├── app.py          # Flask application
│   └── extractors/
│       ├── __init__.py
│       └── ocsf_schema.py  # OCSF schema extractor
├── Dockerfile
├── requirements.txt
└── README.md
```

### Adding New Extractors

1. Create a new extractor in `src/extractors/`
2. Implement the extraction logic
3. Add new endpoints in `app.py`
4. Update the extraction script if needed

## Contributing

1. Create a feature branch
2. Implement changes
3. Add/update tests
4. Submit a pull request

## License

[Include your license information here] 