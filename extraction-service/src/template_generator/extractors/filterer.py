"""Filterer for OCSF class attributes"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Callable, Set
from ..utils.file_utils import load_json, save_json
from ..config import CLASS_EXTRACTION_DIR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AttributeFilterer:
    """Filters OCSF class attributes based on different criteria"""
    
    def __init__(self, input_dir: Path, output_dir: Path):
        """
        Initialize the filterer
        
        Args:
            input_dir: Directory containing class JSON files
            output_dir: Directory to save filtered JSON files
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        
    def filter_by_requirement(self, requirement_types: Set[str], output_suffix: str) -> None:
        """
        Filter attributes by requirement type(s)
        
        Args:
            requirement_types: Set of requirement types to filter for (e.g. {'required'} or {'required', 'recommended'})
            output_suffix: Suffix to add to output filenames
        """
        def requirement_filter(attr_data: Dict[str, Any]) -> bool:
            return attr_data.get('requirement') in requirement_types
            
        self._filter_attributes(
            filter_func=requirement_filter,
            output_suffix=output_suffix,
            skip_files=['base_event.json']
        )
    
    def filter_by_custom(self, 
                        filter_func: Callable[[Dict[str, Any]], bool],
                        output_suffix: str,
                        skip_files: List[str] = None) -> None:
        """
        Filter attributes using a custom filter function
        
        Args:
            filter_func: Function that takes attribute data and returns bool
            output_suffix: Suffix to add to output filenames
            skip_files: List of filenames to skip
        """
        self._filter_attributes(
            filter_func=filter_func,
            output_suffix=output_suffix,
            skip_files=skip_files or []
        )
    
    def _filter_attributes(self,
                          filter_func: Callable[[Dict[str, Any]], bool],
                          output_suffix: str,
                          skip_files: List[str] = None) -> None:
        """
        Internal method to filter attributes based on a filter function
        
        Args:
            filter_func: Function that takes attribute data and returns bool
            output_suffix: Suffix to add to output filenames
            skip_files: List of filenames to skip
        """
        skip_files = skip_files or []
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each file in input directory
        for input_file in self.input_dir.glob('*.json'):
            try:
                # Skip specified files
                if input_file.name in skip_files:
                    logger.info(f"Skipping {input_file.name}")
                    continue
                
                # Load class data
                class_data = load_json(input_file)
                
                # Get attributes
                attributes = class_data.get('attributes', {})
                
                # Filter attributes
                filtered_attributes = {
                    name: attr_data
                    for name, attr_data in attributes.items()
                    if filter_func(attr_data)
                }
                
                # Create new class data with filtered attributes
                filtered_class_data = {
                    **{k: v for k, v in class_data.items() if k != 'attributes'},
                    'attributes': filtered_attributes
                }
                
                # Generate output filename
                output_name = input_file.stem + output_suffix + '.json'
                output_path = self.output_dir / output_name
                
                # Save filtered data
                save_json(filtered_class_data, output_path)
                logger.info(f"Saved filtered class {input_file.stem} to {output_name}")
                
            except Exception as e:
                logger.error(f"Error processing {input_file.name}: {str(e)}")
                continue

def extract_required_attributes(input_dir: Path, output_dir: Path) -> None:
    """
    Extract required attributes from class files
    
    Args:
        input_dir: Directory containing class JSON files
        output_dir: Directory to save filtered JSON files
    """
    filterer = AttributeFilterer(input_dir, output_dir)
    filterer.filter_by_requirement({'required'}, '-required')

def extract_required_and_recommended_attributes(input_dir: Path, output_dir: Path) -> None:
    """
    Extract both required and recommended attributes from class files
    
    Args:
        input_dir: Directory containing class JSON files
        output_dir: Directory to save filtered JSON files
    """
    filterer = AttributeFilterer(input_dir, output_dir)
    filterer.filter_by_requirement({'required', 'recommended'}, '-required_and_recommended') 