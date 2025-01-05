from flask import Flask, request, jsonify
from typing import Dict, Any
import logging
from trieve_client import TrieveClient
from rag_handler import RAGHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
trieve_client = TrieveClient()
rag_handler = RAGHandler(trieve_client)

@app.route('/health', methods=['GET'])
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

@app.route('/classify', methods=['POST'])
async def classify_log() -> Dict[str, Any]:
    """
    Classify a log entry using Trieve's hybrid search
    """
    try:
        log_data = request.get_json()
        log_message = log_data.get('message', '')
        
        # Search for similar chunks in Trieve
        search_results = await trieve_client.search_chunks(
            query=log_message,
            search_type="hybrid",
            limit=3
        )
        
        # TODO: Implement cross-encoder reranking if needed
        
        return jsonify({
            "status": "success",
            "classifications": search_results,
            "log_message": log_message
        }), 200
        
    except Exception as e:
        logger.error(f"Classification error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@app.route('/store-chunk', methods=['POST'])
async def store_chunk() -> Dict[str, Any]:
    """
    Store a new chunk in Trieve (e.g., for OCSF class definitions)
    """
    try:
        data = request.get_json()
        result = await trieve_client.create_chunk(
            content=data.get('content'),
            metadata=data.get('metadata'),
            tags=data.get('tags')
        )
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        logger.error(f"Failed to store chunk: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/rag', methods=['POST'])
async def process_rag() -> Dict[str, Any]:
    """
    Process a RAG query with context retrieval
    """
    try:
        data = request.get_json()
        query = data.get('query')
        context_size = data.get('context_size', 3)

        result = await rag_handler.process_rag_query(
            query=query,
            context_size=context_size
        )
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        logger.error(f"RAG processing error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@app.route('/chunks/batch', methods=['POST'])
async def batch_store_chunks() -> Dict[str, Any]:
    """
    Store multiple chunks in one request
    """
    try:
        data = request.get_json()
        chunks = data.get('chunks', [])
        
        result = await trieve_client.batch_create_chunks(chunks)
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        logger.error(f"Batch chunk creation error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@app.route('/chunks/<chunk_id>', methods=['DELETE'])
async def delete_chunk_endpoint(chunk_id: str) -> Dict[str, Any]:
    """
    Delete a chunk by ID
    """
    try:
        result = await trieve_client.delete_chunk(chunk_id)
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        logger.error(f"Chunk deletion error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081) 