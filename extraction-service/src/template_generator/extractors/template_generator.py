import json
import logging
from pathlib import Path
from typing import Dict, Any, Set

from ..config import (
    CLASS_EXTRACTION_REQUIRED_DIR,
    OBJECT_EXTRACTION_REQUIRED_WITH_CONSTRAINTS_DIR,
    TEMPLATES_DIR,
)

logger = logging.getLogger(__name__)

def merge_object_attributes(class_obj: Dict[str, Any], required_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge object attributes while preserving common keys from class object.
    
    Args:
        class_obj: The object definition from class-required file
        required_obj: The object definition from required-objects file
        
    Returns:
        Dict containing merged object definition
    """
    # Create a copy of the class object to modify
    merged = class_obj.copy()
    
    # Get top-level keys from both objects
    class_keys = set(class_obj.keys())
    required_keys = set(required_obj.keys())
    
    # Find keys that are unique to required_obj (not in class_obj)
    unique_keys = required_keys - class_keys
    
    # Add all unique keys and their values from required_obj
    for key in unique_keys:
        merged[key] = required_obj[key]
    
    return merged

def merge_required_objects_with_class(class_uid: str, class_name: str) -> None:
    """
    Merge required objects with their class file, giving priority to class attributes.
    
    Args:
        class_uid: The UID of the class
        class_name: The name of the class
    """
    # Setup paths
    required_objects_file = OBJECT_EXTRACTION_REQUIRED_WITH_CONSTRAINTS_DIR / f"{class_uid}_{class_name}-required_required_objects.json"
    required_class_file = CLASS_EXTRACTION_REQUIRED_DIR / f"{class_uid}_{class_name}-required.json"
    output_file = TEMPLATES_DIR / f"{class_uid}_{class_name}_required_template.json"

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load required objects
        with open(required_objects_file, 'r') as f:
            required_objects = json.load(f)

        # Load required class
        with open(required_class_file, 'r') as f:
            required_class = json.load(f)

        # Create a copy of required_class to modify
        merged_result = required_class.copy()

        # For each attribute in required_class that is of type object_t
        for attr_name, attr_data in required_class.get('attributes', {}).items():
            if attr_data.get('type') == 'object_t':
                # Find corresponding object in required_objects
                if attr_name in required_objects:
                    # Merge the object definitions
                    merged_result['attributes'][attr_name] = merge_object_attributes(
                        attr_data,
                        required_objects[attr_name]
                    )

        # Save the merged result
        with open(output_file, 'w') as f:
            json.dump(merged_result, f, indent=2)

        logger.info(f"Successfully merged required objects for {class_uid}_{class_name}")

    except Exception as e:
        logger.error(f"Error merging required objects for {class_uid}_{class_name}: {str(e)}")
        raise

def generate_templates() -> None:
    """Generate templates by merging required objects with their class files."""
    logger.info("Starting template generation")
    
    # Get all required class files
    required_class_files = CLASS_EXTRACTION_REQUIRED_DIR.glob('*.json')
    
    for class_file in required_class_files:
        # Extract class_uid and name from filename
        filename = class_file.stem  # Remove .json extension
        if '-required' in filename:
            base_name = filename.replace('-required', '')
            class_uid = base_name.split('_')[0]
            class_name = '_'.join(base_name.split('_')[1:])
            
            try:
                merge_required_objects_with_class(class_uid, class_name)
            except Exception as e:
                logger.error(f"Failed to generate template for {class_uid}_{class_name}: {str(e)}")
                continue

    logger.info("Completed template generation") 