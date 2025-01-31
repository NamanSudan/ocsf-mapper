import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
import requests
from dotenv import load_dotenv
import logging
from datetime import datetime
import time
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Custom exceptions for better error handling
class OCSFError(Exception):
    """Base exception for OCSF-related errors."""
    pass

class ValidationError(OCSFError):
    """Raised when validation fails."""
    def __init__(self, message: str, errors: List[Dict]):
        self.errors = errors
        super().__init__(f"{message}: {json.dumps(errors, indent=2)}")

class RefinementError(OCSFError):
    """Raised when refinement fails."""
    def __init__(self, message: str, validation_errors: List[Dict], refinement_response: Optional[str] = None):
        self.validation_errors = validation_errors
        self.refinement_response = refinement_response
        super().__init__(f"{message}\nValidation Errors: {json.dumps(validation_errors, indent=2)}\nRefinement Response: {refinement_response}")

def retry_on_exception(retries: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (requests.RequestException,)):
    """Decorator for retrying operations that may fail."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_delay = delay
            last_exception = None
            
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < retries - 1:
                        logger.warning(f"Attempt {attempt + 1}/{retries} failed: {str(e)}. Retrying in {retry_delay:.1f}s...")
                        time.sleep(retry_delay)
                        retry_delay *= backoff
                    else:
                        logger.error(f"All {retries} attempts failed for {func.__name__}")
                        raise last_exception
            
            if last_exception:
                raise last_exception
        return wrapper
    return decorator

class OCSFValidator:
    """Handles validation of OCSF JSON objects against the OCSF server."""
    
    def __init__(self, ocsf_server_url: str = "http://localhost:8085"):
        self.server_url = ocsf_server_url
        self.validation_endpoint = f"{self.server_url}/api/v2/validate"
        
    @retry_on_exception(retries=3, delay=1.0)
    def validate_json(self, json_data: Dict) -> Dict:
        """
        Validates a JSON object against the OCSF schema.
        
        Args:
            json_data: The JSON object to validate
            
        Returns:
            Dict containing validation results with errors and warnings
            
        Raises:
            ValidationError: If validation fails with schema violations
            requests.RequestException: If the request to validation server fails
        """
        try:
            # Pre-process the JSON data
            # Convert string timestamps to epoch milliseconds
            if isinstance(json_data.get('time'), str):
                dt = datetime.fromisoformat(json_data['time'].replace('Z', '+00:00'))
                json_data['time'] = int(dt.timestamp() * 1000)

            # Convert hex PIDs to integers
            if 'actor' in json_data and 'process' in json_data['actor'] and 'pid' in json_data['actor']['process']:
                pid = json_data['actor']['process']['pid']
                if isinstance(pid, str) and pid.startswith('0x'):
                    json_data['actor']['process']['pid'] = int(pid, 16)

            if 'process' in json_data and 'pid' in json_data['process']:
                pid = json_data['process']['pid']
                if isinstance(pid, str) and pid.startswith('0x'):
                    json_data['process']['pid'] = int(pid, 16)

            # Ensure metadata version is 1.3.0
            if 'metadata' in json_data and 'version' in json_data['metadata']:
                json_data['metadata']['version'] = '1.3.0'
            
            # Log the request payload for debugging
            logger.debug(f"Validation request payload: {json.dumps(json_data, indent=2)}")
            
            response = requests.post(
                self.validation_endpoint,
                json=json_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Log the response details
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            logger.debug(f"Response body: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('errors'):
                raise ValidationError("Schema validation failed", result['errors'])
                
            return result
            
        except requests.RequestException as e:
            logger.error(f"Validation request failed: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response body: {e.response.text}")
            raise

class OCSFRefiner:
    """Handles LLM-based refinement of OCSF JSON objects."""
    
    def __init__(self, trieve_api_key: str, trieve_dataset_id: str, trieve_api_host: str):
        self.api_key = trieve_api_key
        self.dataset_id = trieve_dataset_id
        self.api_host = trieve_api_host
        
    @retry_on_exception(retries=2, delay=2.0)
    def refine_json(self, original_json: Dict, validation_results: Dict) -> Dict:
        """
        Refines a JSON object based on validation results using LLM.
        
        Args:
            original_json: The original JSON object
            validation_results: Validation results from OCSFValidator
            
        Returns:
            Refined JSON object
            
        Raises:
            RefinementError: If refinement fails or produces invalid JSON
            requests.RequestException: If the request to Trieve API fails
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'TR-Dataset': self.dataset_id
        }
        
        # Enhanced system prompt with more specific instructions
        system_prompt = (
            "You are an expert at fixing OCSF schema violations. "
            "Given the original JSON and validation errors, fix the specific fields "
            "to make the JSON fully compliant with the OCSF schema. "
            "Follow these rules:\n"
            "1. Only modify fields mentioned in validation errors\n"
            "2. Preserve all other fields exactly as they are\n"
            "3. Ensure all required fields are present\n"
            "4. Match data types exactly as specified in schema\n"
            "Return only the corrected JSON with no additional text or explanation."
        )
        
        # Format validation errors for the prompt
        validation_summary = json.dumps(validation_results, indent=2)
        original_json_str = json.dumps(original_json, indent=2)
        
        user_prompt = (
            f"Fix the following OCSF JSON based on the validation errors:\n\n"
            f"Original JSON:\n{original_json_str}\n\n"
            f"Validation Errors:\n{validation_summary}\n\n"
            f"Return the corrected JSON."
        )
        
        payload = {
            'chunk_ids': [],  # Empty for direct LLM completion
            'prev_messages': [
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': user_prompt
                }
            ],
            'temperature': 0.3,
            'stream_response': False
        }
        
        try:
            response = requests.post(
                f'{self.api_host}/api/chunk/generate',
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            try:
                # Parse the response JSON
                response_data = response.json()
                # Extract the message content
                if isinstance(response_data, dict) and 'message' in response_data:
                    llm_response = response_data['message']
                else:
                    llm_response = response_data
                
                # Extract JSON from the response
                refined_json = self._extract_json_from_response(llm_response)
                return refined_json
                
            except (json.JSONDecodeError, ValueError) as e:
                raise RefinementError(
                    "Failed to extract valid JSON from LLM response",
                    validation_results['errors'],
                    response.text
                )
                
        except requests.RequestException as e:
            logger.error(f"Refinement request failed: {str(e)}")
            raise

    def _extract_json_from_response(self, response_text: str) -> Dict:
        """
        Extracts JSON object from LLM response.
        
        Args:
            response_text: The text response from the LLM
            
        Returns:
            Dict containing the extracted JSON object
            
        Raises:
            ValueError: If no valid JSON found in response
            json.JSONDecodeError: If JSON parsing fails
        """
        try:
            # First try to parse the entire response as JSON
            if isinstance(response_text, dict):
                return response_text
            
            # Try to parse the text as JSON
            return json.loads(response_text)
            
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from markdown code block
            import re
            # Look for JSON in code blocks
            json_match = re.search(r"```(?:json)?\n(.*?)\n```", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
                
            # Look for JSON-like content (anything between curly braces)
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
                
            raise ValueError("Could not extract valid JSON from LLM response")

class ValidationReport:
    """Tracks validation statistics and error details."""
    
    def __init__(self):
        self.stats = {
            "processed": 0,
            "validation_errors": 0,
            "refinement_success": 0,
            "refinement_failure": 0,
            "error_details": {},  # Maps filename to error details
            "exception_types": {}  # Track Python exception types
        }
        self.timestamp = datetime.now().isoformat()
    
    def add_file_result(self, filename: str, validation_result: Optional[Dict] = None, 
                       refinement_success: bool = True, remaining_errors: Optional[List[Dict]] = None):
        """
        Add results for a processed file.
        
        Args:
            filename: Name of the processed file
            validation_result: Initial validation result if validation failed
            refinement_success: Whether refinement was successful
            remaining_errors: Any errors remaining after refinement attempt
        """
        self.stats["processed"] += 1
        
        if validation_result and validation_result.get("errors"):
            self.stats["validation_errors"] += 1
            
            if refinement_success:
                self.stats["refinement_success"] += 1
            else:
                self.stats["refinement_failure"] += 1
                # Store error details for failed refinements
                self.stats["error_details"][filename] = {
                    "initial_errors": validation_result.get("errors", []),
                    "remaining_errors": remaining_errors or []
                }
    
    def add_exception(self, error_type: str):
        """Track Python exception types."""
        self.stats["exception_types"][error_type] = self.stats["exception_types"].get(error_type, 0) + 1
    
    def get_report(self) -> Dict:
        """Generate the validation report."""
        success_rate = (self.stats["refinement_success"] / self.stats["validation_errors"] * 100 
                       if self.stats["validation_errors"] > 0 else 100)
        
        return {
            "timestamp": self.timestamp,
            "stats": self.stats,
            "success_rate": success_rate,
            "error_distribution": self._calculate_error_distribution(),
            "exception_distribution": self.stats["exception_types"]
        }
    
    def _calculate_error_distribution(self) -> Dict:
        """Calculate distribution of error types across failed validations."""
        error_types = {}
        for file_errors in self.stats["error_details"].values():
            for error in file_errors.get("remaining_errors", []):
                error_type = error.get("error", "unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1
        return error_types

class ValidationWorkflow:
    """Manages the end-to-end validation and refinement workflow."""
    
    def __init__(self, input_dir: str = "transformed", output_dir: str = "post-validation"):
        # Initialize from environment variables
        self.trieve_api_key = os.getenv('TRIEVE_API_KEY')
        self.trieve_dataset_id = os.getenv('DATASET_ID')
        self.trieve_api_host = os.getenv('TRIEVE_HOST')
        
        if not all([self.trieve_api_key, self.trieve_dataset_id, self.trieve_api_host]):
            raise ValueError("Missing required environment variables")
        
        self.validator = OCSFValidator()
        self.refiner = OCSFRefiner(
            trieve_api_key=self.trieve_api_key,
            trieve_dataset_id=self.trieve_dataset_id,
            trieve_api_host=self.trieve_api_host
        )
        
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.report = ValidationReport()
    
    def process_directory(self):
        """Process all JSON files in the input directory."""
        logger.info(f"Starting validation workflow for directory: {self.input_dir}")
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each JSON file
        for json_file in self.input_dir.glob("*.json"):
            if json_file.name == ".DS_Store":  # Skip macOS system files
                continue
                
            try:
                self._process_single_file(json_file)
            except Exception as e:
                logger.error(f"Error processing {json_file.name}: {str(e)}")
                self.report.add_exception(type(e).__name__)
        
        self._generate_report()
    
    def _process_single_file(self, input_file: Path):
        """Process a single JSON file through validation and refinement."""
        logger.info(f"Processing file: {input_file.name}")
        
        try:
            # Read input JSON
            with open(input_file, 'r') as f:
                original_json = json.load(f)
            
            try:
                # Attempt validation
                validation_result = self.validator.validate_json(original_json)
                logger.info(f"Validation passed for {input_file.name}")
                # Copy validated file to output directory
                output_file = self.output_dir / input_file.name
                with open(output_file, 'w') as f:
                    json.dump(original_json, f, indent=2)
                logger.info(f"Copied validated file to: {output_file}")
                self.report.add_file_result(input_file.name)
                
            except ValidationError as ve:
                # Validation failed, attempt refinement
                logger.info(f"Validation errors found in {input_file.name}, attempting refinement")
                validation_result = {"errors": ve.errors}
                
                try:
                    # Attempt refinement
                    refined_json = self.refiner.refine_json(original_json, validation_result)
                    
                    # Validate refined JSON
                    try:
                        self.validator.validate_json(refined_json)
                        # Refinement successful
                        output_file = self.output_dir / input_file.name
                        with open(output_file, 'w') as f:
                            json.dump(refined_json, f, indent=2)
                        logger.info(f"Successfully refined and saved: {output_file}")
                        self.report.add_file_result(input_file.name, validation_result, True)
                        
                    except ValidationError as ve2:
                        # Refinement didn't fix all issues
                        logger.warning(f"Refinement did not fix all validation errors in {input_file.name}. Remaining errors: {json.dumps(ve2.errors, indent=2)}")
                        self.report.add_file_result(input_file.name, validation_result, False, ve2.errors)
                        
                except (RefinementError, requests.RequestException) as e:
                    logger.error(f"Refinement failed for {input_file.name}: {str(e)}")
                    self.report.add_file_result(input_file.name, validation_result, False, validation_result.get("errors"))
                    
        except Exception as e:
            logger.error(f"Error processing {input_file.name}: {str(e)}")
            self.report.add_file_result(input_file.name, None, False)
            raise
    
    def _generate_report(self):
        """Generate and save the validation report."""
        report_data = self.report.get_report()
        
        # Save report
        report_file = self.output_dir / 'validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Log summary
        logger.info("Validation workflow completed:")
        logger.info(f"- Files processed: {self.report.stats['processed']}")
        logger.info(f"- Files with validation errors: {self.report.stats['validation_errors']}")
        logger.info(f"- Successful refinements: {self.report.stats['refinement_success']}")
        logger.info(f"- Failed refinements: {self.report.stats['refinement_failure']}")
        logger.info(f"- Success rate: {report_data['success_rate']:.2f}%")
        
        if self.report.stats['exception_types']:
            logger.info("Exception distribution:")
            for error_type, count in self.report.stats['exception_types'].items():
                logger.info(f"  - {error_type}: {count}")

def main():
    """Main entry point for the script."""
    try:
        workflow = ValidationWorkflow()
        workflow.process_directory()
    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 