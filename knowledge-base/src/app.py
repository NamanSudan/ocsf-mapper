from flask import Flask, request, jsonify
from trieve_client import TrieveClient
import logging
import traceback

# Set up more detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
trieve_client = TrieveClient()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        logger.debug("Health check endpoint called")
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        logger.error(traceback.format_exc())  # This will log the full stack trace
        return jsonify({"error": str(e)}), 500

@app.route('/chunk-group', methods=['POST'])
def create_group():
    """Create a new chunk group"""
    try:
        data = request.get_json()
        result = trieve_client.create_chunk_group(
            name=data["name"],
            description=data["description"],
            metadata=data.get("metadata"),
            tag_set=data.get("tag_set"),
            tracking_id=data.get("tracking_id"),
            upsert=data.get("upsert", False)
        )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error creating chunk group: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/chunk-group/<group_id>/chunk', methods=['POST'])
def add_chunk_to_group(group_id: str):
    """Create a chunk and add it to a group"""
    try:
        data = request.get_json()
        
        # First create the chunk
        chunk = trieve_client.create_chunk(
            content=data["content"],
            metadata=data.get("metadata"),
            tags=data.get("tags")
        )
        
        # Then add it to the group
        result = trieve_client.add_chunk_to_group(
            group_id=group_id,
            chunk_id=chunk["id"]
        )
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error adding chunk to group: {str(e)}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082) 