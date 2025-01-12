from typing import Dict, Any, List, Optional
from trieve_client import TrieveClient
import logging
import json

logger = logging.getLogger(__name__)

class OCSFChunk:
    """Base class for OCSF chunks"""
    
    def __init__(self, trieve_client: TrieveClient):
        self.trieve_client = trieve_client
    
    def create_or_update(self, content: str, metadata: Dict[str, Any], tag_set: List[str], tracking_id: str, group_tracking_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create or update a chunk with the given content and metadata"""
        logger.debug(f"Creating/updating chunk {tracking_id}")
        logger.debug(f"Content length: {len(content)} chars")
        logger.debug(f"Tag set: {tag_set}")
        if group_tracking_ids:
            logger.debug(f"Group tracking IDs: {group_tracking_ids}")

        try:
            result = self.trieve_client.create_chunk(
                html_content=content,
                metadata=metadata,
                tag_set=tag_set,
                tracking_id=tracking_id,
                group_tracking_ids=group_tracking_ids,
                upsert=True
            )
            return result
        except Exception as e:
            logger.error(f"Failed to create/update chunk {tracking_id}: {e}")
            raise

class OCSFCategoryChunk(OCSFChunk):
    """Handles OCSF category chunks"""
    
    def __init__(self, trieve_client: TrieveClient):
        super().__init__(trieve_client)
    
    def _build_content(self, category_data: Dict[str, Any]) -> str:
        """Build HTML content from category data"""
        name = category_data.get("name", "")
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
                <p><strong>Name:</strong> {name}</p>
                <p><strong>UID:</strong> {uid}</p>
                <p><strong>Description:</strong> {description}</p>
                
                <h3>Classes</h3>
                <div class="class-list">
                    {class_list}
                </div>
            </div>
        """
    
    def _build_metadata(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build metadata from category data"""
        return {
            "type": "category",
            "name": category_data.get("name"),
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
    
    def _build_tag_set(self, category_data: Dict[str, Any]) -> List[str]:
        """Build tag set from category data"""
        tags = ["ocsf", "category"]
        
        # Add category name and caption
        name = category_data.get("name")
        caption = category_data.get("caption")
        if name:
            tags.append(name)
        if caption:
            tags.append(caption)
        
        # Add class names
        class_names = [
            class_data.get("name")
            for class_data in category_data.get("classes", {}).values()
            if class_data.get("name")
        ]
        tags.extend(class_names)
        
        return list(set(tags))  # Remove duplicates 