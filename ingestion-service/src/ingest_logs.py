from flask import Flask, request, jsonify
from typing import Dict, Any, List
import logging
import os
from datetime import datetime
from vector_handler import VectorHandler
from common.queue_handler import QueueHandler
from common.metrics_handler import MetricsHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
vector_handler = VectorHandler()
queue_handler = QueueHandler()
metrics_handler = MetricsHandler()

@app.route('/health', methods=['GET'])
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

@app.route('/ingest', methods=['POST'])
async def ingest_log() -> Dict[str, Any]:
    """
    Endpoint to receive and normalize logs from Vector.dev
    """
    with metrics_handler.track_processing_time('ingest'):
        try:
            log_data = request.get_json()
            logger.info(f"Received log entry from Vector")
            
            # Handle both single log and batch of logs
            if isinstance(log_data, list):
                normalized_logs = [vector_handler.process_log(log) for log in log_data]
            else:
                normalized_logs = [vector_handler.process_log(log_data)]
            
            # Queue logs for classification
            for log in normalized_logs:
                source_type = log.get("source", "unknown")
                metrics_handler.track_received_log(source_type)
                
                if await queue_handler.enqueue_log(log):
                    metrics_handler.track_processed_log(source_type)
                else:
                    metrics_handler.track_error("queue_error")
            
            # Update queue size metric
            queue_size = await queue_handler.get_queue_length()
            metrics_handler.set_queue_size(queue_size)
            
            return jsonify({
                "status": "success",
                "message": f"Processed {len(normalized_logs)} log entries",
                "queue_size": queue_size
            }), 200
            
        except Exception as e:
            metrics_handler.track_error("processing_error")
            logger.error(f"Error processing log: {str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 