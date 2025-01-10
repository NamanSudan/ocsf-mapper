import httpx
import json
import os
import logging
from typing import Dict, List, Any
from pathlib import Path

class OCSFSchemaExtractor:
    """Extractor for OCSF Schema data"""
    
    BASE_URL = "https://schema.ocsf.io/api"
    DATA_DIR = Path(__file__).parent.parent.parent / "data" / "ocsf"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        self._setup_logging()
        self._ensure_data_directory()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Data directory ensured at: {self.DATA_DIR}")
    
    def _get(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request to the OCSF API"""
        url = f"{self.BASE_URL}/{endpoint}"
        self.logger.info(f"Making GET request to: {url}")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error occurred while fetching {url}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error occurred while fetching {url}: {str(e)}")
            raise
    
    def _save_to_file(self, data: Dict[str, Any], filename: str):
        """Save data to a JSON file"""
        file_path = self.DATA_DIR / filename
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Successfully saved data to: {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving data to {file_path}: {str(e)}")
            raise
    
    def extract_categories(self) -> Dict[str, Any]:
        """Extract categories data"""
        try:
            self.logger.info("Starting categories extraction")
            data = self._get("categories")
            self._save_to_file(data, "ocsf_categories.json")
            return {"status": "success", "message": "Categories extracted successfully"}
        except Exception as e:
            self.logger.error(f"Failed to extract categories: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def extract_classes(self) -> Dict[str, Any]:
        """Extract classes data"""
        try:
            self.logger.info("Starting classes extraction")
            data = self._get("classes")
            self._save_to_file(data, "ocsf_classes.json")
            return {"status": "success", "message": "Classes extracted successfully"}
        except Exception as e:
            self.logger.error(f"Failed to extract classes: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def extract_base_event(self) -> Dict[str, Any]:
        """Extract base event data"""
        try:
            self.logger.info("Starting base event extraction")
            data = self._get("base_event")
            self._save_to_file(data, "ocsf_base_events.json")
            return {"status": "success", "message": "Base events extracted successfully"}
        except Exception as e:
            self.logger.error(f"Failed to extract base event: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def extract_schema(self) -> Dict[str, Any]:
        """Extract complete schema data"""
        try:
            self.logger.info("Starting schema extraction")
            # Note: The export endpoint doesn't include /api/
            data = self._get("../export/schema")
            self._save_to_file(data, "ocsf_schema.json")
            return {"status": "success", "message": "Schema extracted successfully"}
        except Exception as e:
            self.logger.error(f"Failed to extract schema: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def __del__(self):
        """Cleanup client session"""
        self.client.close() 