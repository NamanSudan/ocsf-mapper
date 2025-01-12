from trieve_client import TrieveClient
from ocsf_data_client import OCSFDataClient
from ocsf_group import OCSFCategoryGroup
from dotenv import load_dotenv
import logging
import json
import os
from datetime import datetime
import pathlib

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

def create_ocsf_knowledge_base():
    # Initialize clients
    trieve_client = TrieveClient()
    data_client = OCSFDataClient()
    
    # Update categories group from extracted data
    category_group = OCSFCategoryGroup(trieve_client, data_client)
    
    # Update the full categories group and all chunks
    result = category_group.update_from_data(create_chunks=True)
    
    # Print the JSON result to stdout
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    create_ocsf_knowledge_base() 