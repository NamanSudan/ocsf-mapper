import os
from dotenv import load_dotenv
from trieve_client import TrieveClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_create_group():
    """Test creating a chunk group"""
    client = TrieveClient()
    
    try:
        # Create a test group
        group = client.create_chunk_group(
            name="Test Category Group",
            description="A test category group for OCSF categories",
            metadata={"type": "category", "version": "1.0.0"},
            tag_set=["test", "category"],
            tracking_id="test_category_group",
            upsert=True
        )
        logger.info(f"Created group: {group}")
        return group
    except Exception as e:
        logger.error(f"Failed to create group: {e}")
        raise

def test_create_chunk():
    """Test creating a chunk and adding it to a group"""
    client = TrieveClient()
    
    try:
        # Create a test chunk
        chunk = client.create_chunk(
            chunk_html="<h1>Test Category</h1><p>This is a test category description</p>",
            group_tracking_ids=["test_category_group"],
            metadata={"type": "category", "name": "test"},
            tag_set=["test", "category"],
            tracking_id="test_category_chunk",
            upsert=True
        )
        logger.info(f"Created chunk: {chunk}")
        return chunk
    except Exception as e:
        logger.error(f"Failed to create chunk: {e}")
        raise

def test_add_chunk_to_group():
    """Test adding a chunk to a group using tracking IDs"""
    client = TrieveClient()
    
    try:
        # Add chunk to group
        result = client.add_chunk_to_group_by_tracking_id(
            group_tracking_id="test_category_group",
            chunk_tracking_id="test_category_chunk"
        )
        logger.info(f"Added chunk to group: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to add chunk to group: {e}")
        raise

def main():
    """Run all tests"""
    load_dotenv()  # Load environment variables
    
    logger.info("Starting Trieve client tests...")
    
    try:
        # Run tests
        group = test_create_group()
        chunk = test_create_chunk()
        result = test_add_chunk_to_group()
        
        logger.info("All tests completed successfully!")
    except Exception as e:
        logger.error(f"Tests failed: {e}")
        raise

if __name__ == "__main__":
    main() 