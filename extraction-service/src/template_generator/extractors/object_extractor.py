"""Object extractor for OCSF schema"""

import logging
from pathlib import Path
from typing import Dict, Any
from ..utils.file_utils import load_json, save_json
from ..config import SCHEMA_FILE_PATH, OBJECT_EXTRACTION_DIR, OBJECTS_FILE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_objects() -> None:
    """
    Extract all objects from the OCSF schema and save them to a single file.
    This includes objects like 'cve', 'endpoint_connection', 'container', etc.
    """
    try:
        # Load schema
        logger.info(f"Loading schema from {SCHEMA_FILE_PATH}")
        schema_data = load_json(SCHEMA_FILE_PATH)
        
        # Extract objects
        objects = schema_data.get('objects', {})
        if not objects:
            logger.warning("No objects found in schema")
            return
            
        logger.info(f"Found {len(objects)} objects in schema")
        
        # Create output directory
        OBJECT_EXTRACTION_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save objects to file
        output_path = OBJECT_EXTRACTION_DIR / OBJECTS_FILE
        save_json(objects, output_path)
        logger.info(f"Saved {len(objects)} objects to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to extract objects: {str(e)}")
        raise 