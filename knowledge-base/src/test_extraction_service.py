import requests
import json
import logging
import os
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXTRACTION_SERVICE_URL = os.getenv("OCSF_DATA_SERVICE_URL", "http://localhost:8083")

def test_schema_endpoint() -> Dict[str, Any]:
    """Test the schema endpoint that serves the complete OCSF schema"""
    url = f"{EXTRACTION_SERVICE_URL}/data/ocsf/schema"
    logger.info(f"Testing schema endpoint: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] != "success":
            logger.error(f"Schema endpoint returned error status: {data}")
            return {}
            
        schema_data = data["schema"]
        logger.info("\n=== OCSF Schema Structure ===")
        logger.info(f"Schema data type: {type(schema_data)}")
        
        # Log top-level keys
        logger.info("\nTop-level keys:")
        for key in schema_data.keys():
            logger.info(f"- {key}")
            
        # Sample some object structures if available
        if "objects" in schema_data:
            objects = schema_data["objects"]
            logger.info("\nSample object structure:")
            if objects:
                sample_obj = next(iter(objects.values()))
                logger.info("Keys in a sample object:")
                for key in sample_obj.keys():
                    logger.info(f"- {key}")
                    
        # Check for attributes structure
        if "attributes" in schema_data:
            attrs = schema_data["attributes"]
            logger.info("\nAttributes structure:")
            logger.info(f"Number of attributes: {len(attrs)}")
            if attrs:
                sample_attr = next(iter(attrs.values()))
                logger.info("Keys in a sample attribute:")
                for key in sample_attr.keys():
                    logger.info(f"- {key}")
        
        return schema_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to access schema endpoint: {str(e)}")
        return {}

def test_analytics_endpoint() -> Dict[str, Any]:
    """Test the analytics endpoint that serves the schema analytics"""
    url = f"{EXTRACTION_SERVICE_URL}/data/ocsf/analytics"
    logger.info(f"Testing analytics endpoint: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] != "success":
            logger.error(f"Analytics endpoint returned error status: {data}")
            return {}
            
        analytics_data = data["analytics"]
        schema_version = data["schema_version"]
        analysis_timestamp = data["analysis_timestamp"]
        
        logger.info("Successfully retrieved analytics data")
        logger.info(f"Schema version: {schema_version}")
        logger.info(f"Analysis timestamp: {analysis_timestamp}")
        
        # Log some key metrics from the analytics
        if "structure_metrics" in analytics_data:
            metrics = analytics_data["structure_metrics"]
            logger.info("Structure Metrics:")
            logger.info(f"- Total objects count: {metrics.get('total_objects_count', 0)}")
            logger.info(f"- Max nesting depth: {metrics.get('max_nesting_depth', 0)}")
            
        return analytics_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to access analytics endpoint: {str(e)}")
        return {}

if __name__ == "__main__":
    logger.info("Testing OCSF data service endpoints...")
    
    # Test schema endpoint
    schema_data = test_schema_endpoint()
    if schema_data:
        logger.info("✅ Schema endpoint test passed")
    else:
        logger.error("❌ Schema endpoint test failed")
        
    # Test analytics endpoint
    analytics_data = test_analytics_endpoint()
    if analytics_data:
        logger.info("✅ Analytics endpoint test passed")
    else:
        logger.error("❌ Analytics endpoint test failed") 