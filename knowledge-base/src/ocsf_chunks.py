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

class OCSFClassChunk(OCSFChunk):
    """Handles OCSF class chunks"""
    
    def __init__(self, trieve_client: TrieveClient):
        super().__init__(trieve_client)
    
    def _build_content(self, class_name: str, class_data: Dict[str, Any]) -> str:
        """Build HTML content for a class chunk"""
        caption = class_data.get("caption", "")
        description = class_data.get("description", "")
        uid = class_data.get("uid", "")
        extends = class_data.get("extends", "")
        profiles = class_data.get("profiles", [])
        constraints = class_data.get("constraints", {})
        
        # Build constraints HTML if they exist
        constraints_html = ""
        if constraints:
            constraints_items = []
            for rule, values in constraints.items():
                constraints_items.append(f"""
                    <div class="constraint">
                        <p><strong>{rule}:</strong> {', '.join(values)}</p>
                    </div>
                """)
            constraints_html = f"""
                <h4>Constraints</h4>
                <div class="constraints-list">
                    {''.join(constraints_items)}
                </div>
            """
        
        # Build profiles HTML
        profiles_html = ""
        if profiles:
            profiles_html = f"""
                <h4>Profiles</h4>
                <div class="profiles-list">
                    <p>{', '.join(profiles)}</p>
                </div>
            """
        
        # Build full HTML content
        return f"""
            <div class="class">
                <h2>{caption}</h2>
                <p><strong>Name:</strong> {class_name}</p>
                <p><strong>UID:</strong> {uid}</p>
                <p><strong>Extends:</strong> {extends}</p>
                <p><strong>Description:</strong> {description}</p>
                {constraints_html}
                {profiles_html}
            </div>
        """
    
    def _build_metadata(self, class_name: str, class_data: Dict[str, Any], category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build metadata for a class chunk"""
        return {
            "type": "class",
            "name": class_name,
            "caption": class_data.get("caption"),
            "uid": class_data.get("uid"),
            "extends": class_data.get("extends"),
            "category": {
                "name": category_data["name"],
                "caption": category_data["caption"],
                "uid": category_data["uid"]
            }
        }
    
    def _build_tag_set(self, class_name: str, class_data: Dict[str, Any], category_data: Dict[str, Any]) -> List[str]:
        """Build tag set for a class chunk"""
        tags = ["ocsf", "class", category_data["name"]]
        
        # Add class name and caption
        if class_name:
            tags.append(class_name)
        if class_data.get("caption"):
            tags.append(class_data["caption"])
            
        # Add category caption
        if category_data.get("caption"):
            tags.append(category_data["caption"])
            
        # Add profiles as tags
        tags.extend(class_data.get("profiles", []))
        
        return list(set(tags))  # Remove duplicates
    
    def create_or_update_class_chunk(self, class_name: str, class_data: Dict[str, Any], category_data: Dict[str, Any], group_tracking_id: str) -> Dict[str, Any]:
        """Create or update a class chunk with the given data"""
        content = self._build_content(class_name, class_data)
        metadata = self._build_metadata(class_name, class_data, category_data)
        tag_set = self._build_tag_set(class_name, class_data, category_data)
        tracking_id = f"ocsf_class_{category_data['name']}_{class_name}"
        
        return self.create_or_update(
            content=content,
            metadata=metadata,
            tag_set=tag_set,
            tracking_id=tracking_id,
            group_tracking_ids=[group_tracking_id]
        ) 

class OCSFBaseEventAttributeChunk(OCSFChunk):
    """Handles OCSF base event attribute chunks"""
    
    def __init__(self, trieve_client: TrieveClient):
        super().__init__(trieve_client)
    
    def _process_value(self, value: Any) -> str:
        """Process a value for HTML display"""
        if isinstance(value, dict):
            return json.dumps(value, indent=2)
        elif isinstance(value, list):
            return json.dumps(value, indent=2)
        else:
            return str(value)
    
    def _build_field_html(self, key: str, value: Any) -> str:
        """Build HTML for a single field"""
        processed_value = self._process_value(value)
        return f"""
            <div class="field">
                <p><strong>{key}:</strong> {processed_value}</p>
            </div>
        """
    
    def _build_enum_value_html(self, enum_key: str, enum_data: Dict[str, Any]) -> str:
        """Build HTML for an enum value"""
        fields = []
        for key, value in enum_data.items():
            if key not in ["_source"]:  # Skip internal fields
                fields.append(f"<p><strong>{key}:</strong> {self._process_value(value)}</p>")
        
        return f"""
            <div class="enum-value">
                <h4>Value: {enum_key}</h4>
                {''.join(fields)}
            </div>
        """
    
    def _build_enum_section_html(self, enum_data: Dict[str, Dict[str, Any]]) -> str:
        """Build HTML for the enum section"""
        enum_values = []
        for enum_key, value_data in sorted(enum_data.items()):
            enum_values.append(self._build_enum_value_html(enum_key, value_data))
        
        return f"""
            <div class="enum-section">
                <h3>Enumeration Values</h3>
                {''.join(enum_values)}
            </div>
        """
    
    def _build_content(self, attr_name: str, attr_data: Dict[str, Any]) -> str:
        """Build HTML content for an attribute chunk"""
        sections = []
        
        # Add basic fields first
        basic_fields = {}
        enum_data = None
        
        for key, value in attr_data.items():
            if key == "enum":
                enum_data = value
            elif not key.startswith("_"):  # Skip internal fields
                basic_fields[key] = value
        
        # Build basic fields HTML
        for key, value in basic_fields.items():
            sections.append(self._build_field_html(key, value))
        
        # Add enum section if present
        if enum_data:
            sections.append(self._build_enum_section_html(enum_data))
        
        # Build full HTML content
        return f"""
            <div class="base-event-attribute">
                <h2>{attr_data.get('caption', attr_name)}</h2>
                {''.join(sections)}
            </div>
        """
    
    def _build_metadata(self, attr_name: str, attr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build metadata for an attribute chunk"""
        metadata = {
            "type": "base_event_attribute",
            "name": attr_name,
        }
        
        # Add all fields except internal ones and enum
        for key, value in attr_data.items():
            if not key.startswith("_") and key != "enum":
                metadata[key] = value
        
        # Add enum information if present
        if "enum" in attr_data:
            metadata["has_enum"] = True
            metadata["enum_values"] = list(attr_data["enum"].keys())
        
        return metadata
    
    def _build_tag_set(self, attr_name: str, attr_data: Dict[str, Any]) -> List[str]:
        """Build tag set for an attribute chunk"""
        tags = ["ocsf", "base_event", "attribute"]
        
        # Add attribute name
        tags.append(attr_name)
        
        # Add caption if present
        if "caption" in attr_data:
            tags.append(attr_data["caption"])
        
        # Add group if present
        if "group" in attr_data:
            tags.append(f"group:{attr_data['group']}")
        
        # Add type if present
        if "type" in attr_data:
            tags.append(f"type:{attr_data['type']}")
        
        # Add requirement if present
        if "requirement" in attr_data:
            tags.append(attr_data["requirement"])
        
        # Add enum values if present
        if "enum" in attr_data:
            for enum_key, enum_data in attr_data["enum"].items():
                if "caption" in enum_data:
                    tags.append(enum_data["caption"])
        
        return list(set(tags))
    
    def create_attribute_chunks(self, attr_name: str, attr_data: Dict[str, Any], group_tracking_id: str) -> List[Dict[str, Any]]:
        """Create all necessary chunks for an attribute and its nested data"""
        chunks = []
        
        # Create main attribute chunk
        main_chunk = self.create_or_update(
            content=self._build_content(attr_name, attr_data),
            metadata=self._build_metadata(attr_name, attr_data),
            tag_set=self._build_tag_set(attr_name, attr_data),
            tracking_id=f"ocsf_base_event_attr_{attr_name}",
            group_tracking_ids=[group_tracking_id]
        )
        chunks.append(main_chunk)
        
        # Create enum value chunks if present
        if "enum" in attr_data:
            for enum_key, enum_data in attr_data["enum"].items():
                enum_chunk = self.create_or_update(
                    content=self._build_enum_value_html(enum_key, enum_data),
                    metadata={
                        "type": "base_event_attribute_enum",
                        "attribute_name": attr_name,
                        "enum_key": enum_key,
                        **{k: v for k, v in enum_data.items() if not k.startswith("_")}
                    },
                    tag_set=["ocsf", "base_event", "attribute", "enum", attr_name, f"value:{enum_key}"] + 
                           ([enum_data["caption"]] if "caption" in enum_data else []),
                    tracking_id=f"ocsf_base_event_attr_{attr_name}_enum_{enum_key}",
                    group_tracking_ids=[group_tracking_id]
                )
                chunks.append(enum_chunk)
        
        return chunks 