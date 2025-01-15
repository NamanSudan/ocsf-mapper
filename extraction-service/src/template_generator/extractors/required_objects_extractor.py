"""Required objects extractor for OCSF classes"""

import logging
from pathlib import Path
from typing import Dict, Any, Set
from ..utils.file_utils import load_json, save_json
from ..config import (
    CLASS_EXTRACTION_REQUIRED_DIR,
    OBJECT_EXTRACTION_DIR,
    OBJECT_EXTRACTION_REQUIRED_FOR_CLASSES_DIR,
    OBJECTS_FILE,
    REQUIRED_OBJECTS_SUFFIX
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_object_type_attributes(class_data: Dict[str, Any]) -> Set[str]:
    """
    Find all attributes that are of type object_t in a class
    
    Args:
        class_data: The class data dictionary
        
    Returns:
        Set of object names referenced in the class
    """
    object_types = set()
    attributes = class_data.get('attributes', {})
    
    for attr_name, attr_data in attributes.items():
        if attr_data.get('type') == 'object_t':
            # The object type should be specified in the object_type field
            if 'object_type' in attr_data:
                object_types.add(attr_data['object_type'])
            else:
                logger.warning(f"Attribute {attr_name} is of type object_t but has no object_type field")
    
    return object_types

def extract_object_definition(objects_data: Dict[str, Any], object_name: str) -> Dict[str, Any]:
    """
    Extract an object's definition including its attributes and other fields
    
    Args:
        objects_data: The complete objects dictionary from objects.json
        object_name: Name of the object to extract
        
    Returns:
        Object definition dictionary or empty dict if not found
    """
    if object_name not in objects_data:
        logger.warning(f"Object {object_name} not found in objects.json")
        return {}
    
    return objects_data[object_name]

def extract_required_objects() -> None:
    """
    Extract required objects for each class that has attributes of type object_t.
    For each such class:
    1. Find attributes of type object_t
    2. Look up those objects in objects.json
    3. Extract their definitions
    4. Save to a new file
    """
    try:
        # Load all objects
        objects_file = OBJECT_EXTRACTION_DIR / OBJECTS_FILE
        logger.info(f"Loading objects from {objects_file}")
        objects_data = load_json(objects_file)
        
        # Create output directory
        OBJECT_EXTRACTION_REQUIRED_FOR_CLASSES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Process each required class file
        for class_file in CLASS_EXTRACTION_REQUIRED_DIR.glob('*.json'):
            try:
                # Skip base_event.json
                if class_file.name == 'base_event.json':
                    logger.info("Skipping base_event.json")
                    continue
                
                # Load class data
                class_data = load_json(class_file)
                
                # Find object type attributes
                object_types = find_object_type_attributes(class_data)
                
                if not object_types:
                    logger.info(f"No object type attributes found in {class_file.name}")
                    continue
                
                # Extract required objects
                required_objects = {}
                for object_type in object_types:
                    object_def = extract_object_definition(objects_data, object_type)
                    if object_def:
                        required_objects[object_type] = object_def
                
                if required_objects:
                    # Generate output filename
                    output_name = class_file.stem + REQUIRED_OBJECTS_SUFFIX
                    output_path = OBJECT_EXTRACTION_REQUIRED_FOR_CLASSES_DIR / output_name
                    
                    # Save required objects
                    save_json(required_objects, output_path)
                    logger.info(f"Saved required objects for {class_file.stem} to {output_name}")
                
            except Exception as e:
                logger.error(f"Error processing {class_file.name}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to extract required objects: {str(e)}")
        raise 