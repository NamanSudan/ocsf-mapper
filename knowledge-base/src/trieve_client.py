import os
import requests
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class TrieveClient:
    """
    HTTP client for Trieve API chunk group operations
    """
    def __init__(self):
        self.api_key = os.getenv("TRIEVE_API_KEY")
        self.dataset_id = os.getenv("DATASET_ID")
        self.host = os.getenv("TRIEVE_HOST", "http://localhost:8090")
        
        # Log configuration for debugging
        logger.debug(f"Initializing TrieveClient with host: {self.host}")
        logger.debug(f"Dataset ID: {self.dataset_id}")
        logger.debug(f"API Key present: {bool(self.api_key)}")
        
        # Base headers for all requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "TR-Dataset": self.dataset_id
        }

    def create_chunk_group(self, 
                          name: str,
                          description: str,
                          metadata: Optional[Dict[str, Any]] = None,
                          tag_set: Optional[List[str]] = None,
                          tracking_id: Optional[str] = None,
                          upsert: bool = False) -> Dict[str, Any]:
        """Create a new chunk group"""
        url = f"{self.host}/api/chunk_group"
        
        payload = {
            "name": name,
            "description": description,
            "metadata": metadata or {},
            "tag_set": tag_set or [],
            "tracking_id": tracking_id,
            "upsert_by_tracking_id": upsert
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create chunk group: {str(e)}")
            raise

    def add_chunk_to_group(self, 
                          group_id: str,
                          chunk_id: str) -> Dict[str, Any]:
        """Add a chunk to an existing group"""
        url = f"{self.host}/api/chunk_group/{group_id}/chunk/{chunk_id}"
        
        try:
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to add chunk to group: {str(e)}")
            raise

    def create_chunk(self, 
                    content: str,
                    metadata: Optional[Dict[str, Any]] = None,
                    tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new chunk that can be added to a group"""
        url = f"{self.host}/api/chunk"
        
        payload = {
            "content": content,
            "metadata": metadata or {},
            "tags": tags or []
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create chunk: {str(e)}")
            raise 