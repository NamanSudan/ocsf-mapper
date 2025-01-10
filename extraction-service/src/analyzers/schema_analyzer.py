from typing import Dict, List
import logging
import json

class SchemaAnalyzer:
    """Analyzer for OCSF schema statistics and metrics"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_categories(self, categories_data: Dict) -> Dict:
        """Analyze category statistics"""
        try:
            self.logger.info(f"Analyzing categories data of type: {type(categories_data)}")
            
            # Extract categories from the nested structure
            categories = []
            if isinstance(categories_data, dict) and 'attributes' in categories_data:
                for category_name, category in categories_data['attributes'].items():
                    category['name'] = category_name
                    categories.append(category)
            else:
                categories = [categories_data]

            stats = {
                "total_categories": len(categories),
                "categories_summary": [],
                "class_counts": {
                    "min": float('inf'),
                    "max": 0,
                    "avg": 0,
                    "total": 0
                }
            }

            for category in categories:
                # Get category details
                classes = category.get('classes', {})
                class_count = len(classes)
                
                # Update class count statistics
                stats['class_counts']['min'] = min(stats['class_counts']['min'], class_count)
                stats['class_counts']['max'] = max(stats['class_counts']['max'], class_count)
                stats['class_counts']['total'] += class_count

                # Add category summary
                stats['categories_summary'].append({
                    "name": category.get('name', 'unnamed'),
                    "description": category.get('description', ''),
                    "uid": category.get('uid', ''),
                    "number_of_classes": class_count,
                    "classes": list(classes.keys()) if class_count > 0 else []
                })

            # Calculate average
            if stats['total_categories'] > 0:
                stats['class_counts']['avg'] = stats['class_counts']['total'] / stats['total_categories']

            if stats['class_counts']['min'] == float('inf'):
                stats['class_counts']['min'] = 0

            # Sort categories by number of classes
            stats['categories_summary'].sort(key=lambda x: x['number_of_classes'], reverse=True)

            return stats
        except Exception as e:
            self.logger.error(f"Error analyzing categories: {str(e)}")
            raise

    def analyze_classes(self, classes_data: Dict) -> Dict:
        """Analyze class statistics"""
        try:
            self.logger.info(f"Analyzing classes data of type: {type(classes_data)}")
            
            # Handle different input formats
            classes = []
            if isinstance(classes_data, dict):
                if 'attributes' in classes_data:
                    # Handle nested dictionary format
                    for class_name, class_info in classes_data['attributes'].items():
                        class_info['name'] = class_name
                        classes.append(class_info)
                else:
                    # Handle flat dictionary format
                    classes.append(classes_data)
            elif isinstance(classes_data, list):
                # Handle list format
                classes = classes_data
            else:
                raise ValueError(f"Unexpected data type: {type(classes_data)}")

            stats = {
                "total_classes": len(classes),
                "classes_summary": [],
                "field_stats": {
                    "total_fields": 0,
                    "required_fields": 0,
                    "field_types": {},
                    "avg_fields_per_class": 0,
                    "avg_required_fields": 0
                },
                "inheritance": {
                    "base_classes": 0,
                    "derived_classes": 0,
                    "max_depth": 0,
                    "inheritance_tree": {}
                },
                "category_distribution": {}
            }

            for class_info in classes:
                # Basic class info
                class_summary = {
                    "name": class_info.get('name', 'unnamed'),
                    "description": class_info.get('description', ''),
                    "uid": class_info.get('uid', ''),
                    "version": class_info.get('version', '1.0.0'),
                    "extends": class_info.get('extends', None),
                    "category": class_info.get('category', 'unknown'),
                    "profiles": class_info.get('profiles', [])
                }

                # Track category distribution
                category = class_info.get('category_name', class_info.get('category', 'unknown'))
                stats['category_distribution'][category] = \
                    stats['category_distribution'].get(category, 0) + 1

                # Count fields from profiles
                profile_count = len(class_info.get('profiles', []))
                class_summary["profile_count"] = profile_count
                
                # Track inheritance
                extends = class_info.get('extends')
                if extends:
                    stats["inheritance"]["derived_classes"] += 1
                    class_summary["type"] = "derived"
                    # Track inheritance tree
                    if extends not in stats["inheritance"]["inheritance_tree"]:
                        stats["inheritance"]["inheritance_tree"][extends] = []
                    stats["inheritance"]["inheritance_tree"][extends].append(class_summary["name"])
                else:
                    stats["inheritance"]["base_classes"] += 1
                    class_summary["type"] = "base"

                stats["classes_summary"].append(class_summary)

            # Calculate inheritance depth
            def calculate_depth(class_name, visited=None):
                if visited is None:
                    visited = set()
                if class_name in visited:
                    return 0  # Prevent cycles
                visited.add(class_name)
                children = stats["inheritance"]["inheritance_tree"].get(class_name, [])
                if not children:
                    return 0
                return 1 + max(calculate_depth(child, visited.copy()) for child in children)

            # Calculate max inheritance depth
            max_depth = 0
            for base_class in [c["name"] for c in stats["classes_summary"] if c["type"] == "base"]:
                depth = calculate_depth(base_class)
                max_depth = max(max_depth, depth)
            stats["inheritance"]["max_depth"] = max_depth

            # Sort classes by category and name
            stats["classes_summary"].sort(key=lambda x: (x["category"], x["name"]))

            # Sort category distribution by count
            stats["category_distribution"] = dict(
                sorted(
                    stats["category_distribution"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            )

            return stats
        except Exception as e:
            self.logger.error(f"Error analyzing classes: {str(e)}")
            raise

    def analyze_base_event(self, base_event_data: Dict) -> Dict:
        """Analyze base event structure and fields"""
        try:
            self.logger.info(f"Analyzing base event data of type: {type(base_event_data)}")
            
            stats = {
                "total_base_fields": 0,
                "required_fields": 0,
                "recommended_fields": 0,
                "field_types": {},
                "field_groups": {},
                "field_details": []
            }

            # Extract fields from the attributes array
            fields = []
            if isinstance(base_event_data, dict) and 'attributes' in base_event_data:
                fields = base_event_data['attributes']
            elif isinstance(base_event_data, list):
                fields = base_event_data

            stats["total_base_fields"] = len(fields)

            # Analyze each field
            for field_entry in fields:
                # Each field entry is a dictionary with a single key-value pair
                for field_name, field_info in field_entry.items():
                    field_detail = {
                        "name": field_name,
                        "type": field_info.get('type', 'unknown'),
                        "type_name": field_info.get('type_name', 'Unknown'),
                        "description": field_info.get('description', ''),
                        "group": field_info.get('group', 'uncategorized'),
                        "requirement": field_info.get('requirement', 'optional'),
                        "source": field_info.get('_source', 'unknown')
                    }

                    # Track requirements
                    requirement = field_detail["requirement"]
                    if requirement == "required":
                        stats["required_fields"] += 1
                    elif requirement == "recommended":
                        stats["recommended_fields"] += 1

                    # Track field types
                    field_type = field_detail["type_name"]
                    stats["field_types"][field_type] = \
                        stats["field_types"].get(field_type, 0) + 1

                    # Track field groups
                    group = field_detail["group"]
                    stats["field_groups"][group] = \
                        stats["field_groups"].get(group, 0) + 1

                    stats["field_details"].append(field_detail)

            # Sort field details by group and name
            stats["field_details"].sort(key=lambda x: (x["group"], x["name"]))

            # Sort dictionaries by count
            stats["field_types"] = dict(sorted(
                stats["field_types"].items(),
                key=lambda x: x[1],
                reverse=True
            ))
            stats["field_groups"] = dict(sorted(
                stats["field_groups"].items(),
                key=lambda x: x[1],
                reverse=True
            ))

            return stats
        except Exception as e:
            self.logger.error(f"Error analyzing base event: {str(e)}")
            raise

    def _calculate_inheritance_depth(self, class_data: Dict) -> int:
        """Calculate the inheritance depth of a class"""
        depth = 0
        current = class_data
        while current.get('extends'):
            depth += 1
            # In a real implementation, you'd need to look up the parent class
            # This is a simplified version
            current = {'extends': None}  # Placeholder for parent lookup
        return depth 