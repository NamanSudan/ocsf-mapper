"""Required objects extractor with constraints for OCSF classes"""

import logging
from pathlib import Path
from typing import Dict, Any, Set
from ..utils.file_utils import load_json, save_json
from ..config import (
    OBJECT_EXTRACTION_REQUIRED_FOR_CLASSES_DIR,
    OBJECT_EXTRACTION_REQUIRED_WITH_CONSTRAINTS_DIR
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_required_attributes(obj_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get required attributes from an object
    
    Args:
        obj_data: Object data dictionary
        
    Returns:
        Dictionary of required attributes
    """
    attributes = obj_data.get('attributes', {})
    return {
        name: attr_data
        for name, attr_data in attributes.items()
        if attr_data.get('requirement') == 'required'
    }

def get_constraint_attributes(obj_data: Dict[str, Any], attributes: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get attributes specified in constraints
    
    Args:
        obj_data: Object data dictionary
        attributes: Full attributes dictionary from the object
        
    Returns:
        Dictionary of attributes specified in constraints
    """
    constraints = obj_data.get('constraints', {})
    if not constraints:
        return {}
        
    # Get attribute names from constraints
    constraint_attrs = set()
    if 'at_least_one' in constraints:
        constraint_attrs.update(constraints['at_least_one'])
    if 'just_one' in constraints:
        constraint_attrs.update(constraints['just_one'])
        
    # Extract those attributes from the full attributes dictionary
    return {
        name: attr_data
        for name, attr_data in attributes.items()
        if name in constraint_attrs
    }

def process_object_with_constraints(obj_name: str, obj_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an object to get its required attributes and constraint attributes
    
    Args:
        obj_name: Name of the object
        obj_data: Object data dictionary
        
    Returns:
        Dictionary containing required and constraint attributes
    """
    # Get all attributes
    all_attributes = obj_data.get('attributes', {})
    
    # Get required attributes
    required_attrs = get_required_attributes(obj_data)
    
    # Get constraint attributes
    constraint_attrs = get_constraint_attributes(obj_data, all_attributes)
    
    # Combine required and constraint attributes
    combined_attrs = {**required_attrs, **constraint_attrs}
    
    # Create new object data with combined attributes
    return {
        **{k: v for k, v in obj_data.items() if k != 'attributes'},
        'attributes': combined_attrs
    }

def extract_required_with_constraints() -> None:
    """
    Extract required attributes and constraint attributes for each object in each class.
    For each class's required objects:
    1. Get required attributes
    2. Get attributes specified in constraints
    3. Combine them
    4. Save to new file
    """
    try:
        # Create output directory
        OBJECT_EXTRACTION_REQUIRED_WITH_CONSTRAINTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Process each class's required objects file
        for input_file in OBJECT_EXTRACTION_REQUIRED_FOR_CLASSES_DIR.glob('*.json'):
            try:
                # Load required objects data
                objects_data = load_json(input_file)
                
                # Process each object
                processed_objects = {}
                for obj_name, obj_data in objects_data.items():
                    processed_objects[obj_name] = process_object_with_constraints(obj_name, obj_data)
                
                # Generate output path (same name as input)
                output_path = OBJECT_EXTRACTION_REQUIRED_WITH_CONSTRAINTS_DIR / input_file.name
                
                # Save processed objects
                save_json(processed_objects, output_path)
                logger.info(f"Saved required objects with constraints for {input_file.stem}")
                
            except Exception as e:
                logger.error(f"Error processing {input_file.name}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to extract required objects with constraints: {str(e)}")
        raise 