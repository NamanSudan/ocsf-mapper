"""File utilities for template generator"""

import json
import os
from typing import Dict, Any
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Ensure directory exists"""
    path.parent.mkdir(parents=True, exist_ok=True)

def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file"""
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], path: Path) -> None:
    """Save data as JSON with pretty printing"""
    ensure_dir(path)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2) 