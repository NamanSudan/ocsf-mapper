from flask import Flask, request, jsonify
import logging
import traceback
from trieve_client import TrieveClient
from ocsf_data_client import OCSFDataClient

# Set up more detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
trieve_client = TrieveClient()
ocsf_client = OCSFDataClient()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        logger.debug("Health check endpoint called")
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/verify-extraction-service', methods=['GET'])
def verify_extraction_service():
    """Verify connection to the extraction service"""
    try:
        is_connected = ocsf_client.verify_connection()
        if is_connected:
            return jsonify({
                "status": "success",
                "message": "Successfully connected to extraction service"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to connect to extraction service"
            }), 503
    except Exception as e:
        logger.error(f"Error verifying extraction service: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/fetch-ocsf-data/<data_type>', methods=['GET'])
def fetch_ocsf_data(data_type: str):
    """Fetch OCSF data from extraction service"""
    try:
        data = ocsf_client.fetch_data(data_type)
        return jsonify({
            "status": "success",
            "data": data
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error fetching OCSF data: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082) 