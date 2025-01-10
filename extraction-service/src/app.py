from flask import Flask, jsonify
from dotenv import load_dotenv
import os
import logging

from extractors.ocsf_schema import OCSFSchemaExtractor

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/extract/ocsf/categories', methods=['POST'])
def extract_categories():
    try:
        logger.info("Starting categories extraction")
        extractor = OCSFSchemaExtractor()
        result = extractor.extract_categories()
        logger.info(f"Categories extraction result: {result}")
        return jsonify(result), 200 if result["status"] == "success" else 500
    except Exception as e:
        logger.error(f"Error in categories extraction: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/extract/ocsf/classes', methods=['POST'])
def extract_classes():
    try:
        logger.info("Starting classes extraction")
        extractor = OCSFSchemaExtractor()
        result = extractor.extract_classes()
        logger.info(f"Classes extraction result: {result}")
        return jsonify(result), 200 if result["status"] == "success" else 500
    except Exception as e:
        logger.error(f"Error in classes extraction: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/extract/ocsf/base-event', methods=['POST'])
def extract_base_event():
    try:
        logger.info("Starting base event extraction")
        extractor = OCSFSchemaExtractor()
        result = extractor.extract_base_event()
        logger.info(f"Base event extraction result: {result}")
        return jsonify(result), 200 if result["status"] == "success" else 500
    except Exception as e:
        logger.error(f"Error in base event extraction: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/extract/ocsf/schema', methods=['POST'])
def extract_schema():
    try:
        logger.info("Starting schema extraction")
        extractor = OCSFSchemaExtractor()
        result = extractor.extract_schema()
        logger.info(f"Schema extraction result: {result}")
        return jsonify(result), 200 if result["status"] == "success" else 500
    except Exception as e:
        logger.error(f"Error in schema extraction: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8083))
    app.run(host='0.0.0.0', port=port) 