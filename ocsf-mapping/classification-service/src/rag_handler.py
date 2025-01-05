from typing import Dict, Any, List
import logging
from trieve_client import TrieveClient

logger = logging.getLogger(__name__)

class RAGHandler:
    """
    Handles RAG (Retrieval Augmented Generation) operations
    """
    def __init__(self, trieve_client: TrieveClient):
        self.trieve_client = trieve_client

    async def process_rag_query(self, query: str, context_size: int = 3) -> Dict[str, Any]:
        """
        Process a RAG query:
        1. Retrieve relevant chunks
        2. Format context
        3. Store RAG event
        """
        try:
            # Get relevant chunks
            search_results = await self.trieve_client.search_chunks(
                query=query,
                search_type="hybrid",
                limit=context_size
            )

            # Format chunks for context
            context = self._format_chunks_for_context(search_results)

            # TODO: Send to LLM for processing
            llm_response = "Placeholder LLM response"  # Replace with actual LLM call

            # Store RAG event
            await self.trieve_client.store_rag_event(
                user_message=query,
                llm_response=llm_response
            )

            return {
                "query": query,
                "context": context,
                "response": llm_response,
                "raw_results": search_results
            }

        except Exception as e:
            logger.error(f"RAG processing error: {str(e)}")
            raise

    def _format_chunks_for_context(self, search_results: Dict[str, Any]) -> List[str]:
        """Format search results into context strings"""
        context = []
        try:
            chunks = search_results.get("chunks", [])
            for chunk in chunks:
                context.append(f"{chunk.get('content', '')} [Score: {chunk.get('score', 0)}]")
        except Exception as e:
            logger.warning(f"Error formatting chunks: {str(e)}")
        return context 