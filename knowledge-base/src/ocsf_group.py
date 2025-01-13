from typing import Dict, Any, List, Optional
from trieve_client import TrieveClient
from ocsf_data_client import OCSFDataClient
from ocsf_chunks import OCSFCategoryChunk, OCSFClassChunk
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

class OCSFGroup:
    """Base class for OCSF group operations"""
    
    def __init__(self, trieve_client: TrieveClient, data_client: OCSFDataClient):
        self.trieve_client = trieve_client
        self.data_client = data_client
    
    def delete_group_chunks(self, group_tracking_id: str) -> None:
        """Delete all chunks associated with a group"""
        try:
            # Get all chunks in the group
            chunks = self.trieve_client.search_chunks(
                group_tracking_ids=[group_tracking_id],
                page_size=100  # Get up to 100 chunks at a time
            )
            
            # Delete each chunk
            for chunk in chunks.get("chunks", []):
                chunk_tracking_id = chunk.get("tracking_id")
                if chunk_tracking_id:
                    logger.info(f"Deleting chunk: {chunk_tracking_id}")
                    self.trieve_client.delete_chunk(chunk_tracking_id)
                    
            logger.info(f"Successfully deleted all chunks in group: {group_tracking_id}")
        except Exception as e:
            logger.error(f"Failed to delete chunks in group {group_tracking_id}: {str(e)}")
            raise
    
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

class OCSFCategorySpecificGroup:
    """Handles creation and management of category-specific OCSF groups.
    Each group represents a specific OCSF category (e.g. System Activity) and contains
    chunks of information about the classes that belong to that category."""
    
    def __init__(self, trieve_client: TrieveClient, data_client: OCSFDataClient):
        self.trieve_client = trieve_client
        self.data_client = data_client
        
    def _build_group_metadata(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build metadata for a category-specific group"""
        return {
            "type": "category_specific",
            "name": category_data["name"],
            "uid": category_data["uid"],
            "caption": category_data["caption"],
            "description": category_data["description"],
            "class_count": len(category_data["classes"])
        }
        
    def _build_group_tag_set(self, category_data: Dict[str, Any]) -> List[str]:
        """Build tag set for a category-specific group"""
        tags = ["ocsf"]  # Base tag
        
        # Add category name and caption
        if category_data.get("name"):
            tags.append(category_data["name"])
        if category_data.get("caption"):
            tags.append(category_data["caption"])
            
        # Add class names and captions
        for class_name, class_data in category_data.get("classes", {}).items():
            if class_name:
                tags.append(class_name)
            if class_data.get("caption"):
                tags.append(class_data["caption"])
        
        return list(set(tags))  # Remove duplicates
        
    def create_category_group(self, category_name: str) -> Dict[str, Any]:
        """Create a category-specific group containing class information chunks"""
        # Fetch categories data
        response = self.data_client.fetch_data("categories")
        logger.debug(f"Full response from data client: {response}")
        
        # Check if response is successful and contains data
        if response.get("status") != "success" or not response.get("data"):
            raise ValueError("Failed to fetch categories data")
            
        # Get the specified category from the attributes section
        categories_data = response["data"]["attributes"]
        if not categories_data:
            raise ValueError("No categories data found in response")
            
        # Get the specified category
        category_data = categories_data.get(category_name)
        if not category_data:
            raise ValueError(f"Category {category_name} not found")
            
        # Build group metadata
        group_metadata = self._build_group_metadata(category_data)
        
        # Create the group with the category-specific naming convention
        group_name = f"OCSF Category: {category_data['caption']}"
        tracking_id = f"ocsf_category_{category_name}"
        
        # Build dynamic tag set
        tag_set = self._build_group_tag_set(category_data)
        
        group = self.trieve_client.create_chunk_group(
            name=group_name,
            description=category_data["description"],
            metadata=group_metadata,
            tracking_id=tracking_id,
            tag_set=tag_set,
            upsert_by_tracking_id=True
        )

        # Create chunks for each class in this category using OCSFClassChunk
        chunks_results = []
        chunks_updated = False
        
        # Initialize the class chunk creator
        class_chunk_creator = OCSFClassChunk(self.trieve_client)
        
        for class_name, class_data in category_data.get("classes", {}).items():
            try:
                # Create/update the chunk using the dedicated chunk class
                chunk_result = class_chunk_creator.create_or_update_class_chunk(
                    class_name=class_name,
                    class_data=class_data,
                    category_data=category_data,
                    group_tracking_id=tracking_id
                )
                
                chunks_results.append(chunk_result)
                chunks_updated = True
                
            except Exception as e:
                logger.error(f"Failed to process chunk for class {class_name}: {str(e)}")
        
        return {
            "group": group,
            "chunks": chunks_results,
            "updates": {
                "group_updated": True,
                "chunks_updated": chunks_updated
            }
        } 

class OCSFBaseEventGroup(OCSFGroup):
    """Handles OCSF base event group operations"""
    
    def __init__(self, trieve_client: TrieveClient, data_client: OCSFDataClient):
        super().__init__(trieve_client, data_client)
        self.group_type = "base_event"
        self.tracking_id = "ocsf_base_event"
    
    def _build_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build metadata from base event data"""
        attributes = data.get("attributes", [])
        attribute_groups = {}
        required_attributes = []
        
        # Process attributes which are a list of single-key dictionaries
        for attr_dict in attributes:
            # Each attr_dict has a single key-value pair
            for attr_name, attr_data in attr_dict.items():
                group = attr_data.get("group", "Other")
                if group not in attribute_groups:
                    attribute_groups[group] = []
                    
                attribute_info = {
                    "name": attr_name,
                    "caption": attr_data.get("caption"),
                    "type": attr_data.get("type"),
                    "required": attr_data.get("requirement") == "required"
                }
                
                attribute_groups[group].append(attribute_info)
                
                if attr_data.get("requirement") == "required":
                    required_attributes.append(attr_name)
        
        return {
            "type": self.group_type,
            "name": data.get("name"),
            "caption": data.get("caption"),
            "description": data.get("description"),
            "uid": data.get("uid"),
            "category": data.get("category"),
            "category_uid": data.get("category_uid"),
            "profiles": data.get("profiles", []),
            "attribute_groups": attribute_groups,
            "attribute_count": len(attributes),
            "required_attributes": required_attributes
        }
        
    def _build_tag_set(self, data: Dict[str, Any]) -> List[str]:
        """Build tag set from base event data"""
        tags = set(["ocsf", self.group_type, "base_event"])
        
        # Add name and caption
        if data.get("name"):
            tags.add(data["name"])
        if data.get("caption"):
            tags.add(data["caption"])
        
        # Add profile tags
        tags.update(data.get("profiles", []))
        
        # Add attribute groups and types
        attributes = data.get("attributes", [])
        for attr_dict in attributes:
            for attr_data in attr_dict.values():
                # Add group
                if "group" in attr_data:
                    tags.add(f"group:{attr_data['group']}")
                
                # Add type
                if "type" in attr_data:
                    tags.add(f"type:{attr_data['type']}")
                    
                # Add requirement status
                if attr_data.get("requirement") == "required":
                    tags.add("required_attribute")
        
        return list(tags)
    
    def update_from_data(self, create_chunks: bool = False) -> Dict[str, Any]:
        """Update base event group from extracted data"""
        # Fetch base event data
        response = self.data_client.fetch_data("base-event")
        logger.debug("Raw response from data client:")
        logger.debug(f"Response structure: {response}")
        
        if not response or not response.get("data"):
            logger.error(f"Invalid response structure: {response}")
            raise ValueError("No base event data received from extraction service")
        
        data = response["data"]
        logger.debug("Processing extracted data:")
        logger.debug(f"Data keys: {data.keys()}")
        
        # Build group parameters from data
        metadata = self._build_metadata(data)
        tag_set = self._build_tag_set(data)
        
        logger.debug("Built group parameters:")
        logger.debug(f"Metadata: {metadata}")
        logger.debug(f"Tag set: {tag_set}")
        
        # Delete existing chunks if we're creating new ones
        if create_chunks:
            logger.info("Deleting existing chunks...")
            # self.delete_group_chunks(self.tracking_id)  # Commented out as chunks were manually deleted
        
        # Create/update the group
        logger.info("Creating/updating OCSF Base Event group...")
        group_result = self.create_or_update(
            name="OCSF Base Event",
            description=data.get("description", "The base event class that defines attributes available in most event classes"),
            group_type=self.group_type,
            metadata=metadata,
            tag_set=tag_set,
            tracking_id=self.tracking_id
        )
        logger.info(f"Successfully created/updated group with tracking_id: {self.tracking_id}")
        
        chunks_results = []
        chunks_updated = False
        
        # Create chunks for each attribute if requested
        if create_chunks:
            logger.info("Creating chunks for base event attributes...")
            from ocsf_chunks import OCSFBaseEventAttributeChunk
            chunk_creator = OCSFBaseEventAttributeChunk(self.trieve_client)
            
            # Process attributes which are a list of single-key dictionaries
            for attr_dict in data.get("attributes", []):
                try:
                    # Each attr_dict has a single key-value pair
                    for attr_name, attr_data in attr_dict.items():
                        logger.info(f"Creating/updating chunks for attribute: {attr_name}")
                        # Create all chunks for this attribute (main + enum values if present)
                        attr_chunks = chunk_creator.create_attribute_chunks(
                            attr_name=attr_name,
                            attr_data=attr_data,
                            group_tracking_id=self.tracking_id
                        )
                        chunks_results.extend(attr_chunks)
                        chunks_updated = True
                except Exception as e:
                    logger.error(f"Failed to process chunks for attribute {attr_name}: {str(e)}")
        
        return {
            "group": group_result,
            "chunks": chunks_results,
            "updates": {
                "group_updated": True,
                "chunks_updated": chunks_updated
            }
        } 