from typing import Dict, Any
import jsonschema
import logging

logger = logging.getLogger(__name__)

class OCSFSchemaValidator:
    """Validates OCSF event schema compliance"""
    
    def __init__(self):
        # Load OCSF schema definitions
        self.schemas = self._load_schemas()
    
    def validate_event(self, event: Dict[str, Any]) -> bool:
        """Validate an event against OCSF schema"""
        try:
            class_uid = event.get("class_uid")
            schema = self.schemas.get(class_uid)
            if not schema:
                logger.warning(f"No schema found for class_uid: {class_uid}")
                return False
                
            jsonschema.validate(instance=event, schema=schema)
            return True
            
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"OCSF schema validation error: {str(e)}")
            return False 