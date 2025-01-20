"""Class extractor for OCSF schema"""

import logging
from pathlib import Path
from typing import Dict, Any
from ..utils.file_utils import load_json, save_json
from ..config import CLASS_EXTRACTION_DIR, CLASS_TEMPLATE_PATTERN, SCHEMA_FILE_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_classes() -> None:
    """
    Extract classes from OCSF schema and save as individual files.
    Each class will be saved in its own file named by its UID and name.
    """
    try:
        # Load the schema
        logger.info(f"Loading schema from {SCHEMA_FILE_PATH}")
        schema = load_json(SCHEMA_FILE_PATH)
        
        # Get classes from schema
        classes = schema.get('classes', {})
        logger.info(f"Found {len(classes)} classes in schema")
        
        # Create extraction directory if it doesn't exist
        CLASS_EXTRACTION_DIR.mkdir(parents=True, exist_ok=True)
        
        # Extract and save each class
        for class_name, class_data in classes.items():
            try:
                # Handle base_event specially
                if class_name == 'base_event':
                    filename = 'base_event.json'
                else:
                    # Get class UID
                    uid = class_data.get('uid', '')
                    if not uid:
                        logger.warning(f"No UID found for class {class_name}, skipping")
                        continue
                    
                    # Replace forward slashes with underscores in class name for filename
                    safe_class_name = class_name.replace('/', '_')
                    
                    # Generate filename
                    filename = CLASS_TEMPLATE_PATTERN.format(
                        uid=uid,
                        name=safe_class_name
                    )
                
                # Create full path (directly in CLASS_EXTRACTION_DIR)
                output_path = CLASS_EXTRACTION_DIR / filename
                
                # Save class data
                save_json(class_data, output_path)
                logger.info(f"Saved class {class_name} to {filename}")
                
            except Exception as e:
                logger.error(f"Error processing class {class_name}: {str(e)}")
                continue
                
        logger.info("Class extraction completed")
        
    except Exception as e:
        logger.error(f"Failed to extract classes: {str(e)}")
        raise 