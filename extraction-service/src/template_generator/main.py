"""Main script for template generation"""

import logging
import argparse
from pathlib import Path
from typing import Set
from .extractors.class_extractor import extract_classes
from .extractors.filterer import extract_required_attributes, extract_required_and_recommended_attributes
from .extractors.object_extractor import extract_objects
from .extractors.required_objects_extractor import extract_required_objects
from .extractors.required_objects_with_constraints import extract_required_with_constraints
from .config import (
    CLASS_EXTRACTION_DIR, 
    CLASS_EXTRACTION_REQUIRED_DIR,
    CLASS_EXTRACTION_REQUIRED_AND_RECOMMENDED_DIR,
    OBJECT_EXTRACTION_DIR,
    OBJECT_EXTRACTION_REQUIRED_FOR_CLASSES_DIR,
    OBJECT_EXTRACTION_REQUIRED_WITH_CONSTRAINTS_DIR,
    OBJECTS_FILE
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def directory_has_files(directory: Path) -> bool:
    """Check if directory exists and has JSON files"""
    if not directory.exists():
        return False
    return any(directory.glob('*.json'))

def main():
    """Main function to run template generation"""
    parser = argparse.ArgumentParser(description='Generate OCSF templates')
    parser.add_argument('--filter-type', choices=['required', 'required_and_recommended'],
                      default='required',
                      help='Type of attribute filtering to perform')
    parser.add_argument('--steps', nargs='+', choices=['1', '2', '3.1', '3.2', '3.4'],
                      help='Specific steps to run (1: class extraction, 2: attribute filtering, '
                           '3.1: object extraction, 3.2: required objects extraction, '
                           '3.4: required objects with constraints)')
    parser.add_argument('--force', action='store_true',
                      help='Force re-run steps even if output files exist')
    
    args = parser.parse_args()
    steps_to_run: Set[str] = set(args.steps) if args.steps else {'1', '2', '3.1', '3.2', '3.4'}
    
    try:
        # Step 1: Extract all classes
        if '1' in steps_to_run:
            if args.force or not directory_has_files(CLASS_EXTRACTION_DIR):
                logger.info("Starting class extraction process")
                extract_classes()
                logger.info("Class extraction completed successfully")
            else:
                logger.info("Skipping class extraction - files already exist")
        
        # Step 2: Extract filtered attributes based on type
        if '2' in steps_to_run:
            target_dir = (CLASS_EXTRACTION_REQUIRED_AND_RECOMMENDED_DIR 
                         if args.filter_type == 'required_and_recommended' 
                         else CLASS_EXTRACTION_REQUIRED_DIR)
            
            if args.force or not directory_has_files(target_dir):
                if args.filter_type == 'required':
                    logger.info("Starting required attributes extraction")
                    extract_required_attributes(CLASS_EXTRACTION_DIR, CLASS_EXTRACTION_REQUIRED_DIR)
                    logger.info("Required attributes extraction completed successfully")
                else:  # required_and_recommended
                    logger.info("Starting required and recommended attributes extraction")
                    extract_required_and_recommended_attributes(
                        CLASS_EXTRACTION_DIR, 
                        CLASS_EXTRACTION_REQUIRED_AND_RECOMMENDED_DIR
                    )
                    logger.info("Required and recommended attributes extraction completed successfully")
            else:
                logger.info(f"Skipping {args.filter_type} attributes extraction - files already exist")
            
        # Step 3.1: Extract all objects
        if '3.1' in steps_to_run:
            objects_file = OBJECT_EXTRACTION_DIR / OBJECTS_FILE
            if args.force or not objects_file.exists():
                logger.info("Starting object extraction")
                extract_objects()
                logger.info("Object extraction completed successfully")
            else:
                logger.info("Skipping object extraction - objects.json already exists")
        
        # Step 3.2: Extract required objects for classes
        if '3.2' in steps_to_run:
            if args.force or not directory_has_files(OBJECT_EXTRACTION_REQUIRED_FOR_CLASSES_DIR):
                logger.info("Starting required objects extraction for classes")
                extract_required_objects()
                logger.info("Required objects extraction completed successfully")
            else:
                logger.info("Skipping required objects extraction - files already exist")
                
        # Step 3.4: Extract required objects with constraints
        if '3.4' in steps_to_run:
            if args.force or not directory_has_files(OBJECT_EXTRACTION_REQUIRED_WITH_CONSTRAINTS_DIR):
                logger.info("Starting required objects with constraints extraction")
                extract_required_with_constraints()
                logger.info("Required objects with constraints extraction completed successfully")
            else:
                logger.info("Skipping required objects with constraints extraction - files already exist")
        
    except Exception as e:
        logger.error(f"Template generation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 