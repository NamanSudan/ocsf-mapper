from trieve_client import TrieveClient
from ocsf_data_client import OCSFDataClient
from ocsf_group import OCSFCategoryGroup, OCSFCategorySpecificGroup, OCSFBaseEventGroup
from dotenv import load_dotenv
import logging
import json
import os
from datetime import datetime
import pathlib
from typing import Dict, Any
# Load environment variables
load_dotenv()

# Get path to knowledge-base/logs directory
LOGS_DIR = pathlib.Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging with timestamp in filename and format
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOGS_DIR / f"knowledge_base_{timestamp}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_ocsf_knowledge_base(
    create_categories: bool = False,
    create_category_specific: bool = False,
    create_base_event: bool = True
) -> Dict[str, Any]:
    """Create or update the OCSF knowledge base
    
    Args:
        create_categories: Whether to create/update the main categories group
        create_category_specific: Whether to create/update category-specific groups
        create_base_event: Whether to create/update the base event group
    """
    # Initialize clients
    trieve_client = TrieveClient()
    data_client = OCSFDataClient()
    
    result = {}
    
    # Create/update the main categories group if requested
    if create_categories:
        logger.info("Creating/updating main categories group...")
        category_group = OCSFCategoryGroup(trieve_client, data_client)
        result["categories"] = category_group.update_from_data(create_chunks=True)
    
    # Create category-specific groups if requested
    if create_category_specific:
        logger.info("Creating/updating category-specific groups...")
        # Get all categories from the data
        response = data_client.fetch_data("categories")
        if response.get("status") != "success" or not response.get("data"):
            raise ValueError("Failed to fetch categories data")
            
        categories_data = response["data"]["attributes"]
        if not categories_data:
            raise ValueError("No categories data found in response")
        
        # Create category-specific groups for each category
        category_specific_group = OCSFCategorySpecificGroup(trieve_client, data_client)
        category_specific_results = {}
        
        for category_name in categories_data.keys():
            try:
                logger.info(f"Creating category-specific group for: {category_name}")
                result = category_specific_group.create_category_group(category_name)
                category_specific_results[category_name] = result
            except Exception as e:
                logger.error(f"Failed to create group for category {category_name}: {str(e)}")
                category_specific_results[category_name] = {"error": str(e)}
                
        result["category_specific_groups"] = category_specific_results
    
    # Create base event group if requested
    if create_base_event:
        logger.info("Creating/updating base event group...")
        base_event_group = OCSFBaseEventGroup(trieve_client, data_client)
        result["base_event"] = base_event_group.update_from_data(create_chunks=True)
    
    return result

if __name__ == "__main__":
    # By default, only create the base event group
    result = create_ocsf_knowledge_base(
        create_categories=False,
        create_category_specific=False,
        create_base_event=True
    )
    print(json.dumps(result, indent=2)) 