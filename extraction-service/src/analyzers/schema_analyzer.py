from typing import Dict, List, Any
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

    def analyze_schema(self, schema_data: Dict) -> Dict:
        """Comprehensive analysis of the schema structure combining basic and deep analysis"""
        try:
            self.logger.info("Starting unified schema analysis")
            
            stats = {
                "metadata": {
                    "version": str(schema_data.get("version", "unknown")),
                    "total_keys": 0,
                    "unique_keys": [],
                    "max_depth": 0
                },
                "structure_metrics": {
                    "top_level_objects_count": len(schema_data.get("objects", {})),
                    "total_objects_count": 0,
                    "max_nesting_depth": 0
                },
                "ocsf_summary": {
                    "categories": {
                        "total_count": 0,
                        "with_classes": 0,
                        "distribution": {},
                        "class_counts": {
                            "min": float('inf'),
                            "max": 0,
                            "avg": 0
                        }
                    },
                    "classes": {
                        "total_count": 0,
                        "base_classes": 0,
                        "derived_classes": 0,
                        "with_examples": 0,
                        "inheritance_depth": {
                            "max": 0,
                            "avg": 0
                        },
                        "category_distribution": {}
                    },
                    "events": {
                        "total_types": 0,
                        "base_event_fields": 0,
                        "extension_points": [],
                        "field_groups": {
                            "classification": [],
                            "context": [],
                            "occurrence": [],
                            "primary": []
                        }
                    },
                    "profiles": {
                        "total_count": 0,
                        "usage_distribution": {},
                        "most_used": [],
                        "least_used": []
                    }
                },
                "objects_summary": {
                    "total_count": 0,
                    "with_attributes": 0,
                    "with_profiles": 0,
                    "with_constraints": 0,
                    "inheritance": {
                        "base_objects": 0,
                        "derived_objects": 0,
                        "inheritance_chains": []
                    }
                },
                "attributes_analysis": {
                    "total_fields": 0,
                    "required_fields": 0,
                    "recommended_fields": 0,
                    "optional_fields": 0,
                    "field_types": {},
                    "avg_fields_per_object": 0,
                    "field_groups": {},
                    "field_relationships": []
                },
                "structure_analysis": {
                    "branching_factor": {},
                    "leaf_depths": [],
                    "complex_objects": [],
                    "circular_refs": [],
                    "composition_patterns": [],
                    "reuse_patterns": {}
                },
                "key_analysis": {
                    "frequency": {},
                    "depth_distribution": {},
                    "parent_child_relationships": [],
                    "value_types": {},
                    "key_paths": [],
                    "patterns": {
                        "prefixes": {},
                        "suffixes": {},
                        "compounds": {}
                    }
                },
                "value_analysis": {
                    "type_distribution": {},
                    "requirements_distribution": {},
                    "constraints_types": {},
                    "profiles_usage": {},
                    "deprecated_items": [],
                    "examples_count": 0,
                    "descriptions_count": 0,
                    "common_patterns": {
                        "enums": {},
                        "ranges": {},
                        "formats": {},
                        "defaults": {}
                    }
                }
            }
            
            unique_keys = set()
            key_paths = set()
            field_groups = {}
            seen_patterns = set()
            
            def analyze_key_patterns(key: str):
                """Analyze patterns in key names"""
                parts = key.split('_')
                if len(parts) > 1:
                    prefix = parts[0]
                    suffix = parts[-1]
                    stats["key_analysis"]["patterns"]["prefixes"][prefix] = \
                        stats["key_analysis"]["patterns"]["prefixes"].get(prefix, 0) + 1
                    stats["key_analysis"]["patterns"]["suffixes"][suffix] = \
                        stats["key_analysis"]["patterns"]["suffixes"].get(suffix, 0) + 1
                    if '_' in key:
                        stats["key_analysis"]["patterns"]["compounds"][key] = \
                            stats["key_analysis"]["patterns"]["compounds"].get(key, 0) + 1

            def analyze_value_patterns(value: Any, path: str):
                """Analyze patterns in values"""
                if isinstance(value, dict):
                    # Check for common object patterns
                    pattern_key = frozenset(value.keys())
                    if pattern_key not in seen_patterns:
                        seen_patterns.add(pattern_key)
                        if len(value) > 2:
                            stats["structure_analysis"]["composition_patterns"].append({
                                "keys": list(value.keys()),
                                "path": path
                            })
                    
                    # Track field relationships
                    if len(value) > 1:
                        related_fields = list(value.keys())
                        stats["attributes_analysis"]["field_relationships"].append({
                            "fields": related_fields,
                            "path": path
                        })
                    
                    # Analyze field groups
                    if "group" in value:
                        group = str(value["group"])
                        if group not in field_groups:
                            field_groups[group] = []
                        field_groups[group].append(path)
                    
                    # Track value patterns
                    if "enum" in value:
                        stats["value_analysis"]["common_patterns"]["enums"][path] = value["enum"]
                    if "format" in value:
                        stats["value_analysis"]["common_patterns"]["formats"][path] = value["format"]
                    if "default" in value:
                        stats["value_analysis"]["common_patterns"]["defaults"][path] = value["default"]
                    if all(k in value for k in ["minimum", "maximum"]):
                        stats["value_analysis"]["common_patterns"]["ranges"][path] = {
                            "min": value["minimum"],
                            "max": value["maximum"]
                        }

            def update_key_stats(key: str, value: Any, depth: int, path: str, parent_key: str = None):
                """Update statistics about a key"""
                # Track unique keys
                unique_keys.add(key)
                
                # Update key frequency
                stats["key_analysis"]["frequency"][key] = \
                    stats["key_analysis"]["frequency"].get(key, 0) + 1
                
                # Track depth distribution
                if key not in stats["key_analysis"]["depth_distribution"]:
                    stats["key_analysis"]["depth_distribution"][key] = []
                if depth not in stats["key_analysis"]["depth_distribution"][key]:
                    stats["key_analysis"]["depth_distribution"][key].append(depth)
                
                # Track key paths
                key_paths.add(path)
                
                # Track parent-child relationship
                if parent_key:
                    stats["key_analysis"]["parent_child_relationships"].append({
                        "parent": str(parent_key),
                        "child": str(key),
                        "depth": depth,
                        "path": path
                    })
                
                # Track value types
                value_type = type(value).__name__
                if key not in stats["key_analysis"]["value_types"]:
                    stats["key_analysis"]["value_types"][key] = []
                if value_type not in stats["key_analysis"]["value_types"][key]:
                    stats["key_analysis"]["value_types"][key].append(value_type)
                
                # Update branching factor
                if depth not in stats["structure_analysis"]["branching_factor"]:
                    stats["structure_analysis"]["branching_factor"][depth] = 0
                if isinstance(value, (dict, list)):
                    stats["structure_analysis"]["branching_factor"][depth] += 1
                
                # Analyze key patterns
                analyze_key_patterns(key)
                
                # Analyze value patterns
                analyze_value_patterns(value, path)
            
            def analyze_ocsf_elements(node: Dict, path: str):
                """Analyze OCSF-specific elements in the schema"""
                if isinstance(node, dict):
                    # Category analysis
                    if "category_uid" in node or "category_name" in node:
                        category = str(node.get("category_name", node.get("category_uid")))
                        stats["ocsf_summary"]["categories"]["distribution"][category] = \
                            stats["ocsf_summary"]["categories"]["distribution"].get(category, 0) + 1
                    
                    # Class analysis
                    if "class_uid" in node:
                        stats["ocsf_summary"]["classes"]["total_count"] += 1
                        if "extends" in node:
                            stats["ocsf_summary"]["classes"]["derived_classes"] += 1
                        else:
                            stats["ocsf_summary"]["classes"]["base_classes"] += 1
                        
                        if "example" in node or "examples" in node:
                            stats["ocsf_summary"]["classes"]["with_examples"] += 1
                        
                        category = str(node.get("category_name", "unknown"))
                        stats["ocsf_summary"]["classes"]["category_distribution"][category] = \
                            stats["ocsf_summary"]["classes"]["category_distribution"].get(category, 0) + 1
                    
                    # Event analysis
                    if "activity_id" in node or "activity_name" in node:
                        stats["ocsf_summary"]["events"]["total_types"] += 1
                    
                    # Profile analysis
                    if "profiles" in node:
                        profiles = node["profiles"]
                        if isinstance(profiles, list):
                            for profile in profiles:
                                profile = str(profile)
                                stats["ocsf_summary"]["profiles"]["usage_distribution"][profile] = \
                                    stats["ocsf_summary"]["profiles"]["usage_distribution"].get(profile, 0) + 1
                    
                    # Field group categorization
                    if "group" in node:
                        group = str(node["group"])
                        field_name = path.split(".")[-1]
                        if group in stats["ocsf_summary"]["events"]["field_groups"]:
                            stats["ocsf_summary"]["events"]["field_groups"][group].append(field_name)
                    
                    # Extension point detection
                    if path.endswith("_ext"):
                        stats["ocsf_summary"]["events"]["extension_points"].append(path)

            def analyze_node(node: Any, depth: int = 0, path: str = "", parent_key: str = None, visited=None) -> None:
                """Recursively analyze a node and its children"""
                if visited is None:
                    visited = set()
                
                # Check for circular references
                node_id = id(node)
                if node_id in visited:
                    stats["structure_analysis"]["circular_refs"].append(path)
                    return
                visited.add(node_id)
                
                # Update structural metrics
                if isinstance(node, dict):
                    stats["structure_metrics"]["total_objects_count"] += 1
                    stats["structure_metrics"]["max_nesting_depth"] = max(
                        stats["structure_metrics"]["max_nesting_depth"],
                        depth
                    )
                
                stats["metadata"]["max_depth"] = max(stats["metadata"]["max_depth"], depth)
                
                if isinstance(node, dict):
                    # Analyze OCSF-specific elements
                    analyze_ocsf_elements(node, path)
                    
                    # Special key handling
                    if "type" in node:
                        type_val = str(node["type"])
                        stats["value_analysis"]["type_distribution"][type_val] = \
                            stats["value_analysis"]["type_distribution"].get(type_val, 0) + 1
                    
                    if "requirement" in node:
                        req = str(node["requirement"])
                        stats["value_analysis"]["requirements_distribution"][req] = \
                            stats["value_analysis"]["requirements_distribution"].get(req, 0) + 1
                        if req == "required":
                            stats["attributes_analysis"]["required_fields"] += 1
                        elif req == "recommended":
                            stats["attributes_analysis"]["recommended_fields"] += 1
                        else:
                            stats["attributes_analysis"]["optional_fields"] += 1
                    
                    if "constraints" in node:
                        for constraint_type in node["constraints"].keys():
                            constraint_type = str(constraint_type)
                            stats["value_analysis"]["constraints_types"][constraint_type] = \
                                stats["value_analysis"]["constraints_types"].get(constraint_type, 0) + 1
                    
                    if "profiles" in node:
                        for profile in node["profiles"]:
                            profile = str(profile)
                            stats["value_analysis"]["profiles_usage"][profile] = \
                                stats["value_analysis"]["profiles_usage"].get(profile, 0) + 1
                    
                    if "extends" in node:
                        base = str(node["extends"])
                        derived = str(node.get("name", path))
                        stats["objects_summary"]["inheritance"]["derived_objects"] += 1
                        
                        # Track inheritance chain
                        chain = [derived, base]
                        stats["objects_summary"]["inheritance"]["inheritance_chains"].append({
                            "chain": chain,
                            "path": path
                        })
                    
                    if "@deprecated" in node:
                        stats["value_analysis"]["deprecated_items"].append({
                            "path": path,
                            "details": str(node["@deprecated"])
                        })
                    
                    if "example" in node or "examples" in node:
                        stats["value_analysis"]["examples_count"] += 1
                    
                    if "description" in node:
                        stats["value_analysis"]["descriptions_count"] += 1
                    
                    # Track complex objects
                    if depth > 3 and len(node) > 5:
                        stats["structure_analysis"]["complex_objects"].append({
                            "path": path,
                            "depth": depth,
                            "size": len(node),
                            "keys": list(node.keys())
                        })
                    
                    # Process all keys in the dictionary
                    for key, value in node.items():
                        stats["metadata"]["total_keys"] += 1
                        new_path = f"{path}.{key}" if path else str(key)
                        update_key_stats(str(key), value, depth, new_path, parent_key)
                        analyze_node(value, depth + 1, new_path, str(key), visited.copy())
                
                elif isinstance(node, list):
                    for i, item in enumerate(node):
                        new_path = f"{path}[{i}]"
                        analyze_node(item, depth + 1, new_path, parent_key, visited.copy())
                
                else:  # Leaf node
                    stats["structure_analysis"]["leaf_depths"].append(depth)
                
            # Start the recursive analysis
            analyze_node(schema_data)
            
            # Process objects specifically
            objects = schema_data.get("objects", {})
            stats["objects_summary"]["total_count"] = len(objects)
            
            for obj_name, obj_data in objects.items():
                # Track inheritance
                if not obj_data.get("extends"):
                    stats["objects_summary"]["inheritance"]["base_objects"] += 1
                
                # Track profiles
                if obj_data.get("profiles"):
                    stats["objects_summary"]["with_profiles"] += 1
                
                # Track constraints
                if "constraints" in obj_data:
                    stats["objects_summary"]["with_constraints"] += 1
                
                # Process attributes
                attributes = obj_data.get("attributes", {})
                if attributes:
                    stats["objects_summary"]["with_attributes"] += 1
                    stats["attributes_analysis"]["total_fields"] += len(attributes)
            
            # Post-processing
            stats["metadata"]["unique_keys"] = sorted(list(unique_keys))
            stats["key_analysis"]["key_paths"] = sorted(list(key_paths))
            stats["attributes_analysis"]["field_groups"] = field_groups
            
            # Calculate averages
            if stats["objects_summary"]["with_attributes"] > 0:
                stats["attributes_analysis"]["avg_fields_per_object"] = \
                    stats["attributes_analysis"]["total_fields"] / stats["objects_summary"]["with_attributes"]
            
            if stats["structure_analysis"]["leaf_depths"]:
                avg_leaf_depth = sum(stats["structure_analysis"]["leaf_depths"]) / \
                    len(stats["structure_analysis"]["leaf_depths"])
                stats["structure_analysis"]["average_leaf_depth"] = avg_leaf_depth
            
            # Sort all distributions by frequency
            for section in ["value_analysis", "key_analysis"]:
                for key, value in stats[section].items():
                    if isinstance(value, dict) and not key == "common_patterns":
                        stats[section][key] = dict(sorted(
                            value.items(),
                            key=lambda x: x[1] if isinstance(x[1], (int, float)) else len(x[1]),
                            reverse=True
                        ))
            
            # Sort key patterns
            for pattern_type in ["prefixes", "suffixes", "compounds"]:
                stats["key_analysis"]["patterns"][pattern_type] = dict(sorted(
                    stats["key_analysis"]["patterns"][pattern_type].items(),
                    key=lambda x: x[1],
                    reverse=True
                ))
            
            # Sort complex objects by depth and size
            stats["structure_analysis"]["complex_objects"].sort(
                key=lambda x: (x["depth"], x["size"]),
                reverse=True
            )
            
            # Analyze reuse patterns
            reuse_counts = {}
            for pattern in stats["structure_analysis"]["composition_patterns"]:
                pattern_key = tuple(sorted(pattern["keys"]))
                if pattern_key not in reuse_counts:
                    reuse_counts[pattern_key] = []
                reuse_counts[pattern_key].append(pattern["path"])
            
            # Only keep patterns that are reused
            stats["structure_analysis"]["reuse_patterns"] = {
                str(k): paths for k, paths in reuse_counts.items()
                if len(paths) > 1
            }
            
            # Post-processing for OCSF-specific stats
            if stats["ocsf_summary"]["categories"]["distribution"]:
                class_counts = list(stats["ocsf_summary"]["categories"]["distribution"].values())
                stats["ocsf_summary"]["categories"].update({
                    "total_count": len(stats["ocsf_summary"]["categories"]["distribution"]),
                    "with_classes": sum(1 for count in class_counts if count > 0),
                    "class_counts": {
                        "min": min(class_counts),
                        "max": max(class_counts),
                        "avg": sum(class_counts) / len(class_counts)
                    }
                })
            
            # Sort profile usage
            profile_usage = stats["ocsf_summary"]["profiles"]["usage_distribution"]
            stats["ocsf_summary"]["profiles"].update({
                "total_count": len(profile_usage),
                "most_used": sorted(profile_usage.items(), key=lambda x: x[1], reverse=True)[:5],
                "least_used": sorted(profile_usage.items(), key=lambda x: x[1])[:5]
            })
            
            # Sort category distribution
            stats["ocsf_summary"]["categories"]["distribution"] = dict(sorted(
                stats["ocsf_summary"]["categories"]["distribution"].items(),
                key=lambda x: x[1],
                reverse=True
            ))
            
            # Sort class category distribution
            stats["ocsf_summary"]["classes"]["category_distribution"] = dict(sorted(
                stats["ocsf_summary"]["classes"]["category_distribution"].items(),
                key=lambda x: x[1],
                reverse=True
            ))
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in schema analysis: {str(e)}")
            raise 

    def analyze_dictionary(self, dictionary_data: Dict) -> Dict:
        """Analyze dictionary data structure and contents"""
        try:
            self.logger.info(f"Analyzing dictionary data of type: {type(dictionary_data)}")
            
            stats = {
                "metadata": {
                    "total_entries": 0,
                    "total_enums": 0,
                    "total_mappings": 0,
                    "nesting_depth": 0
                },
                "structure": {
                    "top_level_keys": [],
                    "nested_objects": [],
                    "value_types": {},
                    "enum_distribution": {},
                    "mapping_types": {}
                },
                "enums": {
                    "total_values": 0,
                    "unique_values": set(),
                    "distribution": {},
                    "categories": {}
                },
                "mappings": {
                    "source_types": {},
                    "target_types": {},
                    "complexity": {
                        "simple": 0,
                        "complex": 0
                    }
                },
                "relationships": {
                    "parent_child": [],
                    "references": [],
                    "dependencies": []
                }
            }

            def analyze_value(value: Any, path: str = "", depth: int = 0) -> None:
                """Recursively analyze a value in the dictionary"""
                # Update nesting depth
                stats["metadata"]["nesting_depth"] = max(stats["metadata"]["nesting_depth"], depth)
                
                if isinstance(value, dict):
                    # Track nested object structure
                    if depth > 0:
                        stats["structure"]["nested_objects"].append({
                            "path": path,
                            "depth": depth,
                            "keys": list(value.keys())
                        })
                    
                    # Analyze dictionary entries
                    for key, val in value.items():
                        new_path = f"{path}.{key}" if path else key
                        
                        # Track value types
                        val_type = type(val).__name__
                        stats["structure"]["value_types"][val_type] = \
                            stats["structure"]["value_types"].get(val_type, 0) + 1
                        
                        # Check for enum-like structures
                        if isinstance(val, dict) and all(isinstance(v, (str, int)) for v in val.values()):
                            stats["metadata"]["total_enums"] += 1
                            stats["enums"]["distribution"][new_path] = len(val)
                            stats["enums"]["total_values"] += len(val)
                            stats["enums"]["unique_values"].update(val.values())
                        
                        # Check for mapping structures
                        if isinstance(val, dict) and "source" in val and "target" in val:
                            stats["metadata"]["total_mappings"] += 1
                            complexity = "complex" if len(val) > 2 else "simple"
                            stats["mappings"]["complexity"][complexity] += 1
                            
                            # Track source and target types
                            if "source_type" in val:
                                source_type = str(val["source_type"])
                                stats["mappings"]["source_types"][source_type] = \
                                    stats["mappings"]["source_types"].get(source_type, 0) + 1
                            if "target_type" in val:
                                target_type = str(val["target_type"])
                                stats["mappings"]["target_types"][target_type] = \
                                    stats["mappings"]["target_types"].get(target_type, 0) + 1
                        
                        # Track relationships
                        if isinstance(val, dict):
                            for ref_key in ["extends", "references", "depends_on"]:
                                if ref_key in val:
                                    stats["relationships"]["references"].append({
                                        "from": new_path,
                                        "to": val[ref_key],
                                        "type": ref_key
                                    })
                        
                        analyze_value(val, new_path, depth + 1)
                
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        new_path = f"{path}[{i}]"
                        analyze_value(item, new_path, depth + 1)
            
            # Start analysis from root
            if isinstance(dictionary_data, dict):
                stats["structure"]["top_level_keys"] = list(dictionary_data.keys())
                stats["metadata"]["total_entries"] = len(dictionary_data)
                analyze_value(dictionary_data)
            
            # Convert unique values set to list for JSON serialization
            stats["enums"]["unique_values"] = list(stats["enums"]["unique_values"])
            
            # Sort distributions by frequency
            stats["structure"]["value_types"] = dict(sorted(
                stats["structure"]["value_types"].items(),
                key=lambda x: x[1],
                reverse=True
            ))
            stats["enums"]["distribution"] = dict(sorted(
                stats["enums"]["distribution"].items(),
                key=lambda x: x[1],
                reverse=True
            ))
            stats["mappings"]["source_types"] = dict(sorted(
                stats["mappings"]["source_types"].items(),
                key=lambda x: x[1],
                reverse=True
            ))
            stats["mappings"]["target_types"] = dict(sorted(
                stats["mappings"]["target_types"].items(),
                key=lambda x: x[1],
                reverse=True
            ))
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error analyzing dictionary: {str(e)}")
            raise 