from typing import Dict, List, Set
import logging
from collections import defaultdict

class SchemaValidator:
    """Validator for OCSF schema data"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_references(self, schema_data: Dict) -> List[Dict]:
        """Validate all references within the schema"""
        issues = []
        try:
            # Collect all UIDs
            valid_uids = set()
            for item in schema_data.get('classes', []):
                if 'uid' in item:
                    valid_uids.add(item['uid'])

            # Check references
            for item in schema_data.get('classes', []):
                # Check extends references
                if 'extends' in item and item['extends'] not in valid_uids:
                    issues.append({
                        'type': 'invalid_reference',
                        'severity': 'error',
                        'message': f"Class {item.get('uid', 'Unknown')} extends non-existent class {item['extends']}"
                    })

                # Check field references
                for field in item.get('fields', []):
                    if 'ref' in field and field['ref'] not in valid_uids:
                        issues.append({
                            'type': 'invalid_reference',
                            'severity': 'error',
                            'message': f"Field {field.get('name', 'Unknown')} references non-existent class {field['ref']}"
                        })

            return issues
        except Exception as e:
            self.logger.error(f"Error validating references: {str(e)}")
            raise

    def check_circular_dependencies(self, classes_data: Dict) -> List[Dict]:
        """Check for circular dependencies in class inheritance"""
        circular_refs = []
        try:
            # Build inheritance graph
            graph = defaultdict(list)
            for class_data in classes_data:
                if 'extends' in class_data:
                    graph[class_data['uid']].append(class_data['extends'])

            # Check for cycles using DFS
            def has_cycle(node: str, visited: Set[str], path: Set[str]) -> bool:
                visited.add(node)
                path.add(node)

                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if has_cycle(neighbor, visited, path):
                            circular_refs.append({
                                'type': 'circular_dependency',
                                'severity': 'error',
                                'message': f"Circular inheritance detected involving class {node}",
                                'path': list(path)
                            })
                            return True
                    elif neighbor in path:
                        circular_refs.append({
                            'type': 'circular_dependency',
                            'severity': 'error',
                            'message': f"Circular inheritance detected involving class {node}",
                            'path': list(path) + [neighbor]
                        })
                        return True

                path.remove(node)
                return False

            visited = set()
            for class_id in graph:
                if class_id not in visited:
                    has_cycle(class_id, visited, set())

            return circular_refs
        except Exception as e:
            self.logger.error(f"Error checking circular dependencies: {str(e)}")
            raise

    def validate_enums(self, schema_data: Dict) -> List[Dict]:
        """Validate enum values consistency"""
        enum_issues = []
        try:
            # Track enum definitions
            enum_definitions = {}

            # First pass: collect enum definitions
            for class_data in schema_data.get('classes', []):
                for field in class_data.get('fields', []):
                    if field.get('type') == 'enum':
                        enum_name = field.get('enum_name')
                        if enum_name:
                            if enum_name in enum_definitions:
                                # Compare values
                                existing_values = set(enum_definitions[enum_name])
                                new_values = set(field.get('values', []))
                                if existing_values != new_values:
                                    enum_issues.append({
                                        'type': 'inconsistent_enum',
                                        'severity': 'warning',
                                        'message': f"Inconsistent values for enum {enum_name}",
                                        'details': {
                                            'existing_values': list(existing_values),
                                            'new_values': list(new_values),
                                            'class': class_data.get('uid'),
                                            'field': field.get('name')
                                        }
                                    })
                            else:
                                enum_definitions[enum_name] = field.get('values', [])

            return enum_issues
        except Exception as e:
            self.logger.error(f"Error validating enums: {str(e)}")
            raise

    def validate_inheritance(self, classes_data: Dict) -> List[Dict]:
        """Validate class inheritance chains"""
        inheritance_issues = []
        try:
            for class_data in classes_data:
                if 'extends' in class_data:
                    parent_id = class_data['extends']
                    parent = next((c for c in classes_data if c.get('uid') == parent_id), None)

                    if not parent:
                        inheritance_issues.append({
                            'type': 'missing_parent',
                            'severity': 'error',
                            'message': f"Parent class {parent_id} not found for {class_data.get('uid')}",
                        })
                        continue

                    # Check field overrides
                    parent_fields = {f['name']: f for f in parent.get('fields', [])}
                    for field in class_data.get('fields', []):
                        if field['name'] in parent_fields:
                            parent_field = parent_fields[field['name']]
                            if field.get('type') != parent_field.get('type'):
                                inheritance_issues.append({
                                    'type': 'invalid_override',
                                    'severity': 'error',
                                    'message': f"Invalid field override in {class_data.get('uid')}",
                                    'details': {
                                        'field': field['name'],
                                        'parent_type': parent_field.get('type'),
                                        'child_type': field.get('type')
                                    }
                                })

            return inheritance_issues
        except Exception as e:
            self.logger.error(f"Error validating inheritance: {str(e)}")
            raise 