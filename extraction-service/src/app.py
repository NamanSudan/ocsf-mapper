from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
import logging
import json
from pathlib import Path

from extractors.ocsf_schema import OCSFSchemaExtractor
from analyzers.schema_analyzer import SchemaAnalyzer
from validators.schema_validator import SchemaValidator
from generators.doc_generator import SchemaDocGenerator

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize components
analyzer = SchemaAnalyzer()
validator = SchemaValidator()
doc_generator = SchemaDocGenerator()

def load_schema_file(filename: str) -> dict:
    """Load a schema file from the data directory"""
    data_dir = Path(__file__).parent.parent / "data" / "ocsf"
    file_path = data_dir / filename
    try:
        logger.info(f"Loading file from: {file_path}")
        # Read file in chunks to handle large files
        with open(file_path, 'r') as f:
            # Read first character to determine if it's an array or object
            first_char = f.read(1)
            f.seek(0)  # Reset to start
            
            if first_char == '{':
                # Process as object
                data = {}
                decoder = json.JSONDecoder()
                buffer = ''
                
                while True:
                    chunk = f.read(8192)  # Read 8KB at a time
                    if not chunk:
                        break
                    buffer += chunk
                    try:
                        data, index = decoder.raw_decode(buffer)
                        break
                    except json.JSONDecodeError:
                        continue
                        
            elif first_char == '[':
                # Process as array
                data = []
                decoder = json.JSONDecoder()
                buffer = ''
                
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    buffer += chunk
                    try:
                        data, index = decoder.raw_decode(buffer)
                        break
                    except json.JSONDecodeError:
                        continue
            else:
                raise ValueError(f"Unexpected JSON format starting with: {first_char}")
                
            logger.info(f"Loaded data type: {type(data)}")
            return data
            
    except Exception as e:
        logger.error(f"Error loading {filename}: {str(e)}")
        raise

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Extraction endpoints
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

@app.route('/extract/ocsf/dictionary', methods=['POST'])
def extract_dictionary():
    try:
        logger.info("Starting dictionary extraction")
        extractor = OCSFSchemaExtractor()
        result = extractor.extract_dictionary()
        logger.info(f"Dictionary extraction result: {result}")
        return jsonify(result), 200 if result["status"] == "success" else 500
    except Exception as e:
        logger.error(f"Error in dictionary extraction: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/extract/ocsf/data-types', methods=['POST'])
def extract_data_types():
    try:
        logger.info("Starting data types extraction")
        extractor = OCSFSchemaExtractor()
        result = extractor.extract_data_types()
        logger.info(f"Data types extraction result: {result}")
        return jsonify(result), 200 if result["status"] == "success" else 500
    except Exception as e:
        logger.error(f"Error in data types extraction: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/extract/ocsf/objects', methods=['POST'])
def extract_objects():
    try:
        logger.info("Starting objects extraction")
        extractor = OCSFSchemaExtractor()
        result = extractor.extract_objects()
        logger.info(f"Objects extraction result: {result}")
        return jsonify(result), 200 if result["status"] == "success" else 500
    except Exception as e:
        logger.error(f"Error in objects extraction: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

# Analysis endpoints
@app.route('/analyze/categories', methods=['GET'])
def analyze_categories():
    try:
        data = load_schema_file('ocsf_categories.json')
        result = analyzer.analyze_categories(data)
        return jsonify({"status": "success", "analysis": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/analyze/classes', methods=['GET'])
def analyze_classes():
    try:
        data = load_schema_file('ocsf_classes.json')
        result = analyzer.analyze_classes(data)
        return jsonify({"status": "success", "analysis": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/analyze/ocsf/base-event', methods=['GET'])
def analyze_base_event():
    try:
        logger.info("Starting base event analysis")
        data = load_schema_file('ocsf_base_events.json')
        analyzer = SchemaAnalyzer()
        result = analyzer.analyze_base_event(data)
        logger.info(f"Base event analysis result: {result}")
        return jsonify({"status": "success", "analysis": result}), 200
    except Exception as e:
        logger.error(f"Error in base event analysis: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/analyze/ocsf/schema-structure', methods=['GET'])
def analyze_schema_structure():
    """Analyze the complete schema structure"""
    try:
        logger.info("Starting unified schema analysis")
        schema_data = load_schema_file('ocsf_schema.json')
        analyzer = SchemaAnalyzer()
        result = analyzer.analyze_schema(schema_data)
        return jsonify({"status": "success", "analysis": result}), 200
    except Exception as e:
        logger.error(f"Error analyzing schema structure: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/analyze/ocsf/schema-deep', methods=['GET'])
def analyze_schema_deep_structure():
    try:
        logger.info("Starting deep schema structure analysis")
        data = load_schema_file('ocsf_schema.json')
        result = analyzer.analyze_schema_deep_structure(data)
        logger.info(f"Deep schema structure analysis completed")
        return jsonify({"status": "success", "analysis": result}), 200
    except Exception as e:
        logger.error(f"Error in deep schema structure analysis: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/analyze/ocsf/dictionary', methods=['GET'])
def analyze_dictionary():
    try:
        logger.info("Starting dictionary analysis")
        data = load_schema_file('ocsf_dictionary.json')
        analyzer = SchemaAnalyzer()
        result = analyzer.analyze_dictionary(data)
        logger.info(f"Dictionary analysis completed")
        return jsonify({"status": "success", "analysis": result}), 200
    except Exception as e:
        logger.error(f"Error in dictionary analysis: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

# Validation endpoints
@app.route('/validate/references', methods=['GET'])
def validate_references():
    try:
        data = load_schema_file('ocsf_schema.json')
        issues = validator.validate_references(data)
        return jsonify({
            "status": "success",
            "valid": len(issues) == 0,
            "issues": issues
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/validate/inheritance', methods=['GET'])
def validate_inheritance():
    try:
        data = load_schema_file('ocsf_classes.json')
        issues = validator.validate_inheritance(data)
        return jsonify({
            "status": "success",
            "valid": len(issues) == 0,
            "issues": issues
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/validate/enums', methods=['GET'])
def validate_enums():
    try:
        data = load_schema_file('ocsf_schema.json')
        issues = validator.validate_enums(data)
        return jsonify({
            "status": "success",
            "valid": len(issues) == 0,
            "issues": issues
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# Documentation generation endpoints
@app.route('/generate/class-docs/<class_id>', methods=['GET'])
def generate_class_docs(class_id):
    try:
        classes_data = load_schema_file('ocsf_classes.json')
        class_data = next((c for c in classes_data if c.get('uid') == class_id), None)
        if not class_data:
            return jsonify({"status": "error", "error": "Class not found"}), 404
        
        docs = doc_generator.generate_class_documentation(class_data)
        return jsonify({"status": "success", "documentation": docs}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/generate/category-overview', methods=['GET'])
def generate_category_overview():
    try:
        categories_data = load_schema_file('ocsf_categories.json')
        overview = doc_generator.generate_category_overview(categories_data)
        return jsonify({"status": "success", "documentation": overview}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/generate/field-reference', methods=['GET'])
def generate_field_reference():
    try:
        schema_data = load_schema_file('ocsf_schema.json')
        reference = doc_generator.generate_field_reference(schema_data)
        return jsonify({"status": "success", "documentation": reference}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# Data serving endpoints
@app.route('/data/ocsf/categories', methods=['GET'])
def serve_categories():
    try:
        logger.info("Serving categories data")
        data = load_schema_file('ocsf_categories.json')
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Error serving categories data: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/data/ocsf/classes', methods=['GET'])
def serve_classes():
    try:
        logger.info("Serving classes data")
        data = load_schema_file('ocsf_classes.json')
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Error serving classes data: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/data/ocsf/base-event', methods=['GET'])
def serve_base_event():
    try:
        logger.info("Serving base event data")
        data = load_schema_file('ocsf_base_events.json')
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Error serving base event data: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/data/ocsf/schema', methods=['GET'])
def get_ocsf_schema():
    """Serve the extracted OCSF schema"""
    try:
        logger.info("Serving OCSF schema data")
        schema_path = os.path.join('data', 'ocsf', 'ocsf_schema.json')
        
        if not os.path.exists(schema_path):
            return jsonify({
                "error": "OCSF schema data not found. Please run extraction first.",
                "status": "error"
            }), 404
            
        with open(schema_path, 'r') as f:
            schema_data = json.load(f)
            
        return jsonify({
            "status": "success",
            "schema": schema_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error serving OCSF schema: {str(e)}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/data/ocsf/data-types', methods=['GET'])
def serve_data_types():
    try:
        logger.info("Serving data types data")
        data = load_schema_file('ocsf_data_types.json')
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Error serving data types data: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/data/ocsf/dictionary', methods=['GET'])
def serve_dictionary():
    try:
        logger.info("Serving dictionary data")
        data = load_schema_file('ocsf_dictionary.json')
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Error serving dictionary data: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/data/ocsf/objects', methods=['GET'])
def serve_objects():
    try:
        logger.info("Serving objects data")
        data = load_schema_file('ocsf_objects.json')
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Error serving objects data: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/data/ocsf/all', methods=['GET'])
def serve_all_data():
    try:
        logger.info("Serving all OCSF data")
        data = {
            "categories": load_schema_file('ocsf_categories.json'),
            "classes": load_schema_file('ocsf_classes.json'),
            "base_event": load_schema_file('ocsf_base_events.json'),
            "schema": load_schema_file('ocsf_schema.json'),
            "data_types": load_schema_file('ocsf_data_types.json'),
            "dictionary": load_schema_file('ocsf_dictionary.json'),
            "objects": load_schema_file('ocsf_objects.json')
        }
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Error serving all data: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/data/ocsf/analytics', methods=['GET'])
def get_ocsf_analytics():
    """Serve the OCSF schema analytics"""
    try:
        logger.info("Serving OCSF schema analytics")
        analytics_path = os.path.join('data', 'analysis', 'ocsf_schema_analysis.json')
        
        if not os.path.exists(analytics_path):
            return jsonify({
                "error": "OCSF schema analytics not found. Please run analysis first.",
                "status": "error"
            }), 404
            
        with open(analytics_path, 'r') as f:
            analytics_data = json.load(f)
            
        return jsonify({
            "status": "success",
            "analytics": analytics_data,
            "schema_version": "1.3.0",
            "analysis_timestamp": analytics_data.get("metadata", {}).get("analysis_timestamp", None)
        }), 200
        
    except Exception as e:
        logger.error(f"Error serving OCSF schema analytics: {str(e)}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8083))
    app.run(host='0.0.0.0', port=port) 