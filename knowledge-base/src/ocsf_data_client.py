import os
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OCSFDataClient:
    """Client for fetching OCSF data from the extraction service"""
    
    def __init__(self):
        self.base_url = os.getenv("EXTRACTION_SERVICE_URL", "http://localhost:8083")
        logger.info(f"Initialized OCSF data client with base URL: {self.base_url}")

    def fetch_data(self, data_type: str) -> Dict[str, Any]:
        """
        Fetch OCSF data from the extraction service
        
        Args:
            data_type: One of 'categories', 'classes', 'base-event', 'schema', 'all'
            
        Returns:
            Dict containing the requested OCSF data
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        valid_types = {'categories', 'classes', 'base-event', 'schema', 'all'}
        if data_type not in valid_types:
            raise ValueError(f"Invalid data type. Must be one of: {valid_types}")

        url = f"{self.base_url}/data/ocsf/{data_type}"
        logger.debug(f"Fetching OCSF data from: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            logger.debug(f"Raw response status code: {response.status_code}")
            logger.debug(f"Raw response text: {response.text}")
            
            data = response.json()
            logger.debug(f"Parsed response data: {data}")
            
            if data.get("status") != "success":
                raise ValueError(f"API returned error status: {data.get('error')}")
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch OCSF {data_type} data: {str(e)}")
            raise

    def verify_connection(self) -> bool:
        """
        Verify connection to the extraction service
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False 