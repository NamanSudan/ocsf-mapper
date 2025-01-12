import os
import requests
from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TrieveClient:
    """
    HTTP client for Trieve API operations
    """
    def __init__(self):
        self.api_key = os.getenv("TRIEVE_API_KEY")
        self.dataset_id = os.getenv("DATASET_ID")
        self.host = os.getenv("TRIEVE_HOST", "http://localhost:8090")
        
        if not self.api_key:
            raise ValueError("TRIEVE_API_KEY environment variable is required")
        if not self.dataset_id:
            raise ValueError("DATASET_ID environment variable is required")
        
        # Log configuration for debugging
        logger.debug(f"Initializing TrieveClient with host: {self.host}")
        logger.debug(f"Dataset ID: {self.dataset_id}")
        logger.debug(f"API Key present: {bool(self.api_key)}")
        
        # Base headers for all requests - note the Bearer prefix for Authorization
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "TR-Dataset": self.dataset_id
        }
        
        logger.debug(f"Headers configured: {self.headers}")

    def create_chunk_group(self, 
                          name: str,
                          description: str,
                          metadata: Optional[Dict[str, Any]] = None,
                          tag_set: Optional[List[str]] = None,
                          tracking_id: Optional[str] = None,
                          upsert_by_tracking_id: bool = False) -> Dict[str, Any]:
        """
        Create a new chunk group.
        
        Args:
            name: Name to assign to the chunk_group
            description: Description of the chunk_group
            metadata: Optional metadata to assign to the chunk_group
            tag_set: Optional tags to assign to the chunk_group
            tracking_id: Optional tracking id to assign to the chunk_group
            upsert_by_tracking_id: Whether to update if a chunk_group with same tracking_id exists
        """
        url = f"{self.host}/api/chunk_group"
        
        payload = {
            "name": name,
            "description": description,
            "metadata": metadata or {},
            "tag_set": tag_set or [],
            "tracking_id": tracking_id,
            "upsert_by_tracking_id": upsert_by_tracking_id
        }

        try:
            logger.info(f"Creating chunk group with tracking_id: {tracking_id}")
            logger.debug("Full request details:")
            logger.debug(f"URL: {url}")
            logger.debug(f"Headers: {self.headers}")
            logger.debug(f"Payload: {payload}")
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response text: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Full response received: {result}")
            group_id = result.get("id")
            logger.info(f"Successfully created group - ID: {group_id}, tracking_id: {tracking_id}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to create chunk group with tracking_id {tracking_id}: {str(e)}")
            logger.error(f"Response text: {response.text if 'response' in locals() else 'No response'}")
            raise

    def add_chunk_to_group_by_tracking_id(self,
                                        group_tracking_id: str,
                                        chunk_id: Optional[str] = None,
                                        chunk_tracking_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a chunk to a group using the group's tracking ID.
        
        Args:
            group_tracking_id: Tracking ID of the group to add the chunk to
            chunk_id: ID of the chunk to add (optional)
            chunk_tracking_id: Tracking ID of the chunk to add (optional)
            
        Note: Either chunk_id or chunk_tracking_id must be provided
        """
        if not chunk_id and not chunk_tracking_id:
            raise ValueError("Either chunk_id or chunk_tracking_id must be provided")
            
        url = f"{self.host}/api/chunk_group/tracking_id/{group_tracking_id}"
        
        payload = {
            "chunk_id": chunk_id,
            "chunk_tracking_id": chunk_tracking_id
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to add chunk to group: {str(e)}")
            raise

    def create_chunk(self,
                    html_content: str,
                    metadata: Optional[Dict[str, Any]] = None,
                    tag_set: Optional[List[str]] = None,
                    tracking_id: Optional[str] = None,
                    group_tracking_ids: Optional[List[str]] = None,
                    upsert: bool = False) -> Dict[str, Any]:
        """
        Create a new chunk.
        
        Args:
            html_content: The HTML content of the chunk
            metadata: Optional metadata to assign to the chunk
            tag_set: Optional tags to assign to the chunk
            tracking_id: Optional tracking id to assign to the chunk
            group_tracking_ids: Optional list of group tracking IDs to add the chunk to
            upsert: Whether to update if a chunk with same tracking_id exists
        """
        url = f"{self.host}/api/chunk"
        
        payload = {
            "chunk_html": html_content,
            "metadata": metadata or {},
            "tag_set": tag_set or [],
            "tracking_id": tracking_id,
            "group_tracking_ids": group_tracking_ids or [],
            "upsert_by_tracking_id": upsert
        }

        try:
            logger.info(f"Creating chunk with tracking_id: {tracking_id}")
            if group_tracking_ids:
                logger.info(f"Adding to groups: {', '.join(group_tracking_ids)}")
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            chunk_metadata = result.get("chunk_metadata", {})
            chunk_id = chunk_metadata.get("id")
            
            logger.info(f"Successfully created chunk - ID: {chunk_id}, tracking_id: {tracking_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to create chunk with tracking_id {tracking_id}: {str(e)}")
            raise

    def get_chunk_group(self, tracking_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a chunk group by its tracking ID.
        
        Args:
            tracking_id: The tracking ID of the group to retrieve
            
        Returns:
            The chunk group if found, None otherwise
        """
        url = f"{self.host}/api/chunk_group/tracking_id/{tracking_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            logger.error(f"Failed to get chunk group: {str(e)}")
            raise

    def get_chunk(self, tracking_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a chunk by its tracking ID.
        
        Args:
            tracking_id: The tracking ID of the chunk to retrieve
            
        Returns:
            The chunk if found, None otherwise
        """
        url = f"{self.host}/api/chunk/tracking_id/{tracking_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            logger.error(f"Failed to get chunk: {str(e)}")
            raise 