# OCSF Schema Analytics

This document provides an analysis of the Open Cybersecurity Schema Framework (OCSF) schema structure and composition.

## Schema Structure Metrics

### Overall Structure
- **Top-level Objects**: 121
- **Total Objects**: 10,665
- **Maximum Nesting Depth**: 6 levels

### Type Distribution
- String fields (string_t): 1,708
- Object fields (object_t): 1,518
- Integer fields (integer_t): 907
- Timestamp/Datetime fields: ~600 combined
  - timestamp_t: 302
  - datetime_t: 299
- Specialized types:
  - email_t
  - ip_t
  - url_t
  - and others

### Requirements Distribution
- Optional fields: 2,211
- Recommended fields: 1,286
- Required fields: 910

### Profiles Usage (Top 5)
1. datetime: 98 uses
2. data_classification: 92 uses
3. container: 82 uses
4. cloud: 74 uses
5. linux/linux_users: 73 uses
6. host: 65 uses

## Schema Composition

### Field Organization
The schema organizes fields into logical groups:
- Classification fields
- Context fields
- Occurrence fields
- Primary fields

### Dictionary Attributes
The schema includes comprehensive dictionaries for:
- Field types and requirements
- Enumerated values with descriptions
- Deprecated fields with migration guidance
- Field relationships and dependencies

## Analysis Insights

### Schema Complexity
- The 6-level nesting depth indicates a well-structured hierarchy
- The ratio of objects to fields suggests good modularity
- Consistent use of profiles indicates good reusability

### Field Requirements
- The majority of fields are optional (50.2%)
- Significant number of recommended fields (29.2%)
- Core required fields (20.6%) form the essential structure

### Type Usage Patterns
- Strong preference for string types (38.8% of fields)
- Substantial use of structured objects (34.5%)
- Good balance of primitive and complex types

## Notes
- This analysis was generated from the OCSF schema version 1.3.0
- The analysis includes both structural metrics and semantic insights
- All counts and distributions are based on the current schema version 

## Accessing Schema Data and Analytics
The extraction service provides HTTP endpoints to access both the OCSF schema and its analytics:

1. **Schema Analytics Endpoint**
   - URL: `http://localhost:8083/data/ocsf/analytics`
   - Method: GET
   - Returns: Complete analytics of the OCSF schema including structural metrics, type distributions, and insights
   - Example Python code:
     ```python
     import requests
     
     response = requests.get('http://localhost:8083/data/ocsf/analytics')
     if response.status_code == 200:
         analytics_data = response.json()
         # Access analytics data
         schema_version = analytics_data.get('schema_version')
         structural_metrics = analytics_data.get('structure_metrics')
     ```

2. **Schema Data Endpoint**
   - URL: `http://localhost:8083/data/ocsf/schema`
   - Method: GET
   - Returns: Complete OCSF schema in JSON format
   - Example Python code:
     ```python
     import requests
     
     response = requests.get('http://localhost:8083/data/ocsf/schema')
     if response.status_code == 200:
         schema_data = response.json()
         # Access schema data
         objects = schema_data.get('objects')
         attributes = schema_data.get('attributes')
     ```

Both endpoints return JSON responses and include appropriate error handling:
- 200: Success with JSON response
- 404: Data not found (schema or analytics haven't been generated)
- 500: Internal server error

Note: Replace `localhost:8083` with the appropriate host and port if accessing from a different environment or service. 