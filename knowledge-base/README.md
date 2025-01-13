# Knowledge Base Service

## Overview
The Knowledge Base Service is responsible for managing OCSF (Open Cybersecurity Schema Framework) specifications and converting them into searchable chunks using Trieve. It processes various OCSF components including categories, classes, and base event attributes, creating a structured and searchable knowledge base.

## Project Structure

### Source Files
1. **create_knowledge_base.py**
   - Main entry point for the knowledge base creation
   - Orchestrates the creation of groups and chunks
   - Handles the overall chunking process flow

2. **ocsf_group.py**
   - Contains group management classes
   - Handles creation and updates of category, class, and base event groups
   - Manages group metadata and relationships

3. **ocsf_chunks.py**
   - Contains chunk creation and management logic
   - Handles HTML content generation for chunks
   - Manages chunk metadata and tagging

4. **ocsf_data_client.py**
   - Communicates with the local OCSF extraction service
   - Fetches processed OCSF schema data
   - Handles data retrieval for categories, classes, and base event attributes

5. **trieve_client.py**
   - Manages interaction with Trieve service
   - Handles chunk creation and updates
   - Manages group operations and search functionality

## Setup

### Docker Setup (Recommended)
1. Navigate to the root directory of the project
2. Run the following command to build and start the service:
   ```bash
   docker-compose -f docker/docker-compose-ocsf.yml up --build knowledge-base
   ```
   This will:
   - Build the knowledge-base service container
   - Start required dependencies (OCSF extraction service, Trieve)
   - Configure networking between services
   - Mount necessary volumes

### Manual Setup
#### Prerequisites
1. Python 3.8+
2. Running instances of:
   - OCSF Extraction Service (for schema data)
   - Trieve Service (for chunk storage)

#### Installation
1. Clone the repository
2. Navigate to the knowledge-base directory
3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

#### Configuration
1. Set up environment variables:
   ```bash
   export TRIEVE_API_KEY=your_api_key
   export TRIEVE_HOST=http://localhost:8090
   export TRIEVE_DATASET_ID=your_dataset_id
   export OCSF_DATA_SERVICE_URL=http://localhost:8083
   ```

## Usage

### Creating the Knowledge Base
Run the main script to create/update the entire knowledge base:
```bash
python create_knowledge_base.py
```

This will:
1. Create/update the main categories group
2. Create/update individual category groups
3. Create/update the base event group
4. Generate chunks for all components

## Data Structure

### Groups
1. **Categories Group**
   - Contains overview of all OCSF categories
   - Tracking ID: `ocsf_categories`

2. **Category-Specific Groups**
   - One group per category
   - Tracking ID format: `ocsf_category_{category_name}`

3. **Base Event Group**
   - Contains base event attributes
   - Tracking ID: `ocsf_base_event`

### Chunks
1. **Category Chunks**
   - Tracking ID format: `ocsf_category_{category_name}`
   - Contains category metadata and class list

2. **Class Chunks**
   - Tracking ID format: `ocsf_class_{category_name}_{class_name}`
   - Contains class details and constraints

3. **Base Event Attribute Chunks**
   - Main attribute chunks: `ocsf_base_event_attr_{attribute_name}`
   - Enum value chunks: `ocsf_base_event_attr_{attribute_name}_enum_{value}`

## Features

### Dynamic Content Processing
- Automatic processing of all fields
- Support for nested data structures
- Special handling for enumerations

### Metadata Management
- Rich metadata for groups and chunks
- Comprehensive tag sets for improved searchability
- Content hashing for change detection

### Chunk Organization
- Hierarchical structure (groups → chunks)
- Separate chunks for enum values
- Relationship tracking via group associations

## Development

### Adding New Features
1. Create new modules for distinct functionality
2. Follow existing file structure patterns
3. Implement required interfaces for group or chunk processing
4. Add appropriate logging and error handling

### Best Practices
1. Use logging for debugging and tracking
2. Implement error handling
3. Follow existing naming conventions
4. Update tests for new functionality

## Troubleshooting

### Common Issues
1. **Connection Errors**
   - Verify service URLs
   - Check API keys
   - Ensure services are running

2. **Missing Data**
   - Check OCSF extraction service response
   - Verify data structure matches expected format

3. **Chunk Creation Failures**
   - Check Trieve service logs
   - Verify chunk size limits
   - Ensure valid metadata format

### Debugging
1. Enable debug logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. Check service responses in debug logs

## Contributing
1. Follow Python code style guidelines
2. Add appropriate logging statements
3. Update documentation for new features
4. Add tests for new functionality 