"""Configuration for template generator"""

import os
from pathlib import Path

# Get base paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# Template directories
TEMPLATE_BASE_DIR = DATA_DIR / "templates"
PREPARATION_DIR = TEMPLATE_BASE_DIR / "preparation"
CLASS_EXTRACTION_DIR = PREPARATION_DIR / "class-extraction"
CLASS_EXTRACTION_REQUIRED_DIR = PREPARATION_DIR / "class-extraction-required"
CLASS_EXTRACTION_REQUIRED_AND_RECOMMENDED_DIR = PREPARATION_DIR / "class-extraction-required_and_recommended"
OBJECT_EXTRACTION_DIR = PREPARATION_DIR / "object-extraction"
OBJECT_EXTRACTION_REQUIRED_DIR = PREPARATION_DIR / "object-extraction-required"
OBJECT_EXTRACTION_REQUIRED_FOR_CLASSES_DIR = OBJECT_EXTRACTION_REQUIRED_DIR / "required-object-for-classes"
OBJECT_EXTRACTION_REQUIRED_WITH_CONSTRAINTS_DIR = OBJECT_EXTRACTION_REQUIRED_DIR / "concatenate-required-object-and-class"

# Source schema path
SCHEMA_FILE_PATH = DATA_DIR / "ocsf" / "ocsf_schema.json"

# File naming pattern
CLASS_TEMPLATE_PATTERN = "{uid}_{name}.json"
OBJECTS_FILE = "objects.json"
REQUIRED_OBJECTS_SUFFIX = "_required_objects.json" 