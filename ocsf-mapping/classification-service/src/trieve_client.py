from typing import Dict, Any, List, Optional
import os
from trieve_py_client.api import chunk_api
from trieve_py_client.configuration import Configuration
from trieve_py_client.api_client import ApiClient
from trieve_py_client.models.rag import RAG

class TrieveClient:
    """
    Wrapper class for Trieve API interactions
    """
    def __init__(self):
        # Read environment variables
        self.api_key = os.getenv("TRIEVE_API_KEY")
        self.dataset_id = os.getenv("TRIEVE_DATASET_ID")
        self.host = os.getenv("TRIEVE_HOST", "https://api.trieve.ai")

        # Configure Trieve client
        config = Configuration(
            host=self.host,
            api_key={"Authorization": self.api_key}
        )
        
        # Initialize API client and endpoints
        self.client = ApiClient(config)
        self.chunk_endpoint = chunk_api.ChunkApi(self.client)

    async def create_chunk(self, content: str, metadata: Optional[Dict[str, Any]] = None, 
                         tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new chunk in Trieve"""
        chunk_payload = {
            "content": content,
            "metadata": metadata or {},
            "tags": tags or []
        }

        try:
            result = self.chunk_endpoint.create_or_upsert_chunk(
                dataset_id=self.dataset_id,
                create_or_upsert_chunk_req_payload=[chunk_payload]
            )
            return result.to_dict()
        except Exception as e:
            raise Exception(f"Failed to create chunk: {str(e)}")

    async def search_chunks(self, query: str, search_type: str = "hybrid", 
                          limit: int = 5) -> Dict[str, Any]:
        """Search for chunks using specified search type"""
        search_payload = {
            "query": query,
            "search_type": search_type,
            "limit": limit
        }

        try:
            results = self.chunk_endpoint.search_chunks(
                dataset_id=self.dataset_id,
                search_chunk_req_payload=search_payload
            )
            return results.to_dict()
        except Exception as e:
            raise Exception(f"Failed to search chunks: {str(e)}")

    async def store_rag_event(self, user_message: str, llm_response: str) -> Dict[str, Any]:
        """Store a RAG event for analytics"""
        try:
            rag_event = RAG(
                event_type="rag",
                user_message=user_message,
                llm_response=llm_response
            )
            # TODO: Implement RAG event storage once API endpoint is available
            return {"status": "success", "event": rag_event.to_dict()}
        except Exception as e:
            raise Exception(f"Failed to store RAG event: {str(e)}")

    async def batch_create_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple chunks in one request"""
        try:
            chunk_payloads = []
            for chunk in chunks:
                chunk_payloads.append({
                    "content": chunk.get("content"),
                    "metadata": chunk.get("metadata", {}),
                    "tags": chunk.get("tags", [])
                })

            result = self.chunk_endpoint.create_or_upsert_chunk(
                dataset_id=self.dataset_id,
                create_or_upsert_chunk_req_payload=chunk_payloads
            )
            return result.to_dict()
        except Exception as e:
            raise Exception(f"Failed to create chunks in batch: {str(e)}")

    async def delete_chunk(self, chunk_id: str) -> Dict[str, Any]:
        """Delete a chunk by ID"""
        try:
            result = self.chunk_endpoint.delete_chunk(
                dataset_id=self.dataset_id,
                chunk_id=chunk_id
            )
            return {"status": "success", "chunk_id": chunk_id}
        except Exception as e:
            raise Exception(f"Failed to delete chunk: {str(e)}") 