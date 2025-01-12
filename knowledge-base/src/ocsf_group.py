from typing import Dict, Any, List, Optional
from trieve_client import TrieveClient
from ocsf_data_client import OCSFDataClient
from ocsf_chunks import OCSFCategoryChunk
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

class OCSFGroup:
    """Base class for OCSF group operations"""
    
    def __init__(self, trieve_client: TrieveClient, data_client: OCSFDataClient):
        self.trieve_client = trieve_client
        self.data_client = data_client
    
    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """Calculate a hash of the data to detect changes"""
        # Sort the dictionary to ensure consistent hashing
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def create_or_update(self, 
                        name: str,
                        description: str,
                        group_type: str,
                        metadata: Dict[str, Any],
                        tag_set: List[str],
                        tracking_id: str) -> Dict[str, Any]:
        """Create or update a group with the given parameters"""
        # Add type to metadata
        metadata = {
            "type": group_type,
            **metadata
        }
        
        return self.trieve_client.create_chunk_group(
            name=name,
            description=description,
            metadata=metadata,
            tag_set=tag_set,
            tracking_id=tracking_id,
            upsert_by_tracking_id=True  # Fixed parameter name
        )

class OCSFCategoryGroup(OCSFGroup):
    """Handles OCSF category group operations"""
    
    def __init__(self, trieve_client: TrieveClient, data_client: OCSFDataClient):
        super().__init__(trieve_client, data_client)
        self.group_type = "categories"
        self.tracking_id = "ocsf_categories"
    
    def _build_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build metadata from category data"""
        categories = data.get("attributes", {})
        return {
            "type": self.group_type,
            "name": data.get("name"),
            "caption": data.get("caption"),
            "description": data.get("description"),
            "category_count": len(categories),
            "category_names": list(categories.keys())  # Just store category names instead of full data
        }
    
    def _build_tag_set(self, data: Dict[str, Any]) -> List[str]:
        """Build tag set from category data"""
        # Base tags
        tags = ["ocsf", self.group_type]
        
        # Add category names and captions
        for category in data.get("attributes", {}).values():
            name = category.get("name")
            caption = category.get("caption")
            if name:
                tags.append(name)
            if caption:
                tags.append(caption)
        
        return list(set(tags))  # Remove duplicates
    
    def update_from_data(self, create_chunks: bool = False) -> Dict[str, Any]:
        """Update category group from extracted data"""
        # Fetch category data
        response = self.data_client.fetch_data("categories")
        logger.debug("Raw response from data client:")
        logger.debug(f"Response structure: {response.keys()}")
        logger.debug(f"Response data structure: {response.get('data', {}).keys()}")
        
        if not response or not response.get("data"):
            logger.error(f"Invalid response structure: {response}")
            raise ValueError("No category data received from extraction service")
        
        data = response["data"]
        logger.debug("Processing extracted data:")
        logger.debug(f"Data keys: {data.keys()}")
        logger.debug(f"Attributes keys: {data.get('attributes', {}).keys()}")
        
        # Build group parameters from data
        metadata = self._build_metadata(data)
        tag_set = self._build_tag_set(data)
        
        logger.debug("Built group parameters:")
        logger.debug(f"Metadata: {metadata}")
        logger.debug(f"Tag set: {tag_set}")
        
        # Create/update the group
        logger.info("Creating/updating OCSF_Categories group...")
        group_result = self.create_or_update(
            name="OCSF_Categories",
            description=data.get("description", "Group containing all OCSF categories"),
            group_type=self.group_type,
            metadata=metadata,
            tag_set=tag_set,
            tracking_id=self.tracking_id
        )
        logger.info(f"Successfully created/updated group with tracking_id: {self.tracking_id}")
        
        chunks_results = []
        chunks_updated = False
        
        # Only create chunks if flag is True
        if create_chunks:
            logger.info("Creating chunks...")
            chunk_creator = OCSFCategoryChunk(self.trieve_client)
            
            for category_name, category_data in data.get("attributes", {}).items():
                try:
                    # Calculate chunk hash before creating/updating
                    chunk_content = chunk_creator._build_content(category_data)
                    chunk_metadata = chunk_creator._build_metadata(category_data)
                    chunk_tag_set = chunk_creator._build_tag_set(category_data)
                    chunk_tracking_id = f"ocsf_category_{category_data.get('name', '')}"
                    
                    chunk_hash = self._calculate_hash({
                        "content": chunk_content,
                        "metadata": chunk_metadata,
                        "tag_set": chunk_tag_set,
                        "group_tracking_ids": [self.tracking_id]
                    })
                    
                    # Check if chunk needs update
                    chunk_needs_update = True
                    try:
                        existing_chunk = self.trieve_client.get_chunk(chunk_tracking_id)
                        if existing_chunk:
                            existing_hash = existing_chunk.get("metadata", {}).get("content_hash")
                            if existing_hash == chunk_hash:
                                logger.info(f"No changes detected for chunk {category_name}")
                                chunks_results.append(existing_chunk)
                                chunk_needs_update = False
                                continue
                    except Exception as e:
                        logger.debug(f"No existing chunk found for {category_name}: {str(e)}")
                    
                    # If we reach here, chunk needs update
                    if chunk_needs_update:
                        logger.info(f"Updating chunk for category {category_name}")
                        chunk_metadata["content_hash"] = chunk_hash
                        chunk_result = chunk_creator.create_or_update(
                            content=chunk_content,
                            metadata=chunk_metadata,
                            tag_set=chunk_tag_set,
                            tracking_id=chunk_tracking_id,
                            group_tracking_ids=[self.tracking_id]
                        )
                        chunks_results.append(chunk_result)
                        chunks_updated = True
                    
                except Exception as e:
                    logger.error(f"Failed to process chunk for category {category_name}: {str(e)}")
        
        return {
            "group": group_result,
            "chunks": chunks_results,
            "updates": {
                "group_updated": True,
                "chunks_updated": chunks_updated
            }
        }

    def create_test_chunk(self, category_name: str) -> Dict[str, Any]:
        """Create a test chunk for a single category"""
        # Fetch category data
        response = self.data_client.fetch_data("categories")
        if not response or not response.get("data"):
            raise ValueError("No category data received from extraction service")
            
        extracted_data = response["data"].get("attributes", {})
        
        # Get the specific category data
        category_data = extracted_data.get(category_name)
        if not category_data:
            raise ValueError(f"Category {category_name} not found in extracted data")
            
        logger.info(f"Creating test chunk for category: {category_name}")
        logger.debug(f"Category data: {category_data}")
        
        # Create chunk
        chunk_tracking_id = f"ocsf_category_{category_name}"
        
        # Initialize category chunk creator if not already done
        if not hasattr(self, 'category_chunk'):
            self.category_chunk = OCSFCategoryChunk(self.trieve_client)
            
        chunk_result = self.category_chunk.create_or_update(
            content=self._build_chunk_content(category_name, category_data),
            metadata=self._build_chunk_metadata(category_name, category_data),
            tag_set=self._build_chunk_tag_set(category_name, category_data),
            tracking_id=chunk_tracking_id,
            group_tracking_ids=[self.tracking_id]
        )
        
        return {
            "chunk": chunk_result,
            "tracking_id": chunk_tracking_id,
            "category": category_name
        }

    def _build_chunk_content(self, category_name: str, category_data: Dict[str, Any]) -> str:
        """Build HTML content for a category chunk"""
        caption = category_data.get("caption", "")
        description = category_data.get("description", "")
        uid = category_data.get("uid", "")
        classes = category_data.get("classes", {})
        
        # Build class list HTML
        class_items = []
        for class_name, class_data in sorted(classes.items()):
            class_items.append(f"""
                <div class="class-item">
                    <h4>{class_data.get('caption', '')}</h4>
                    <p><strong>Name:</strong> {class_name}</p>
                    <p><strong>UID:</strong> {class_data.get('uid', '')}</p>
                    <p>{class_data.get('description', '')}</p>
                </div>
            """)
        
        class_list = "\n".join(class_items)
        
        # Build full HTML content
        return f"""
            <div class="category">
                <h2>{caption}</h2>
                <p><strong>Name:</strong> {category_name}</p>
                <p><strong>UID:</strong> {uid}</p>
                <p><strong>Description:</strong> {description}</p>
                
                <h3>Classes</h3>
                <div class="class-list">
                    {class_list}
                </div>
            </div>
        """

    def _build_chunk_metadata(self, category_name: str, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build metadata for a category chunk"""
        return {
            "type": "category",
            "name": category_name,
            "caption": category_data.get("caption"),
            "uid": category_data.get("uid"),
            "class_count": len(category_data.get("classes", {})),
            "classes": {
                name: {
                    "caption": class_data.get("caption"),
                    "uid": class_data.get("uid"),
                    "extends": class_data.get("extends")
                }
                for name, class_data in category_data.get("classes", {}).items()
            }
        }

    def _build_chunk_tag_set(self, category_name: str, category_data: Dict[str, Any]) -> List[str]:
        """Build tag set for a category chunk"""
        tags = ["ocsf", "category"]
        
        # Add category name and caption
        if category_name:
            tags.append(category_name)
        caption = category_data.get("caption")
        if caption:
            tags.append(caption)
        
        # Add class names
        class_names = [
            name
            for name in category_data.get("classes", {}).keys()
        ]
        tags.extend(class_names)
        
        return list(set(tags))  # Remove duplicates 