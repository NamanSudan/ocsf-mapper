from typing import Dict, List
import logging
from pathlib import Path

class SchemaDocGenerator:
    """Generator for OCSF schema documentation"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_class_documentation(self, class_data: Dict) -> Dict:
        """Generate documentation for a class"""
        try:
            doc = {
                "title": class_data.get('caption', ''),
                "description": class_data.get('description', ''),
                "uid": class_data.get('uid', ''),
                "version": class_data.get('version', ''),
                "fields": self._process_fields(class_data.get('fields', [])),
                "examples": class_data.get('examples', []),
                "relationships": {
                    "extends": class_data.get('extends'),
                    "extended_by": [],  # To be filled by parent
                    "referenced_by": []  # To be filled by parent
                }
            }

            return doc
        except Exception as e:
            self.logger.error(f"Error generating class documentation: {str(e)}")
            raise

    def generate_category_overview(self, categories_data: List[Dict]) -> Dict:
        """Generate category overview documentation"""
        try:
            overview = {
                "categories": [],
                "relationships": [],
                "usage_guidelines": []
            }

            for category in categories_data:
                cat_doc = {
                    "name": category.get('caption', ''),
                    "description": category.get('description', ''),
                    "uid": category.get('uid', ''),
                    "type": category.get('type', ''),
                    "classes": category.get('classes', []),
                    "fields": self._process_fields(category.get('fields', []))
                }
                overview["categories"].append(cat_doc)

                # Add relationships
                if category.get('related_to'):
                    overview["relationships"].append({
                        "from": category['uid'],
                        "to": category['related_to'],
                        "type": "related"
                    })

            return overview
        except Exception as e:
            self.logger.error(f"Error generating category overview: {str(e)}")
            raise

    def generate_field_reference(self, schema_data: Dict) -> Dict:
        """Generate field reference documentation"""
        try:
            field_ref = {
                "common_fields": [],
                "field_types": {},
                "usage_patterns": []
            }

            # Track field occurrences
            field_occurrences = {}
            type_examples = {}

            # Analyze all fields across classes
            for class_data in schema_data.get('classes', []):
                for field in class_data.get('fields', []):
                    field_name = field.get('name')
                    field_type = field.get('type')

                    # Track field occurrences
                    if field_name not in field_occurrences:
                        field_occurrences[field_name] = {
                            "count": 0,
                            "types": set(),
                            "classes": []
                        }
                    
                    field_occurrences[field_name]["count"] += 1
                    field_occurrences[field_name]["types"].add(field_type)
                    field_occurrences[field_name]["classes"].append(class_data.get('uid'))

                    # Collect type examples
                    if field_type not in type_examples and field.get('example'):
                        type_examples[field_type] = field.get('example')

            # Identify common fields (used in multiple classes)
            for field_name, data in field_occurrences.items():
                if data["count"] > 1:
                    field_ref["common_fields"].append({
                        "name": field_name,
                        "occurrences": data["count"],
                        "types": list(data["types"]),
                        "classes": data["classes"]
                    })

            # Document field types
            for field_type, example in type_examples.items():
                field_ref["field_types"][field_type] = {
                    "example": example,
                    "classes_count": sum(
                        1 for f in field_occurrences.values() 
                        if field_type in f["types"]
                    )
                }

            # Identify usage patterns
            field_ref["usage_patterns"] = self._identify_usage_patterns(field_occurrences)

            return field_ref
        except Exception as e:
            self.logger.error(f"Error generating field reference: {str(e)}")
            raise

    def _process_fields(self, fields: List[Dict]) -> List[Dict]:
        """Process and format field information"""
        processed_fields = []
        for field in fields:
            processed_fields.append({
                "name": field.get('name', ''),
                "type": field.get('type', ''),
                "description": field.get('description', ''),
                "required": field.get('required', False),
                "default": field.get('default'),
                "enum_values": field.get('values', []) if field.get('type') == 'enum' else None,
                "example": field.get('example')
            })
        return processed_fields

    def _identify_usage_patterns(self, field_occurrences: Dict) -> List[Dict]:
        """Identify common field usage patterns"""
        patterns = []
        
        # Find fields that commonly appear together
        field_sets = {}
        for field_name, data in field_occurrences.items():
            classes_set = frozenset(data["classes"])
            if len(classes_set) > 1:  # Only consider fields used in multiple classes
                if classes_set not in field_sets:
                    field_sets[classes_set] = set()
                field_sets[classes_set].add(field_name)

        # Convert patterns to list
        for classes, fields in field_sets.items():
            if len(fields) > 1:  # Only include patterns with multiple fields
                patterns.append({
                    "fields": list(fields),
                    "classes": list(classes),
                    "occurrence_count": len(classes)
                })

        # Sort by occurrence count
        patterns.sort(key=lambda x: x["occurrence_count"], reverse=True)
        return patterns 