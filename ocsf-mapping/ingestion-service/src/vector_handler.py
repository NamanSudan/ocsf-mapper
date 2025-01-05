from typing import Dict, Any, List
import logging
from datetime import datetime
from windows_event_criticality import get_event_criticality, EventCriticality
from ocsf_mapper import OCSFWindowsEventMapper
from schema_validator import OCSFSchemaValidator

logger = logging.getLogger(__name__)

class VectorHandler:
    """
    Handles processing of logs from Vector.dev
    """
    def __init__(self):
        self.supported_sources = {
            "file": self._process_file_log,
            "syslog": self._process_syslog,
            "windows_event_log": self._process_windows_event
        }
        self.ocsf_mapper = OCSFWindowsEventMapper(metrics_handler)
        self.schema_validator = OCSFSchemaValidator()

    def process_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a log entry from Vector"""
        try:
            source_type = log_data.get("source_type", "unknown")
            processor = self.supported_sources.get(source_type, self._process_generic)
            return processor(log_data)
        except Exception as e:
            logger.error(f"Error processing log: {str(e)}")
            return self._process_generic(log_data)

    def _process_file_log(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Process file-based logs"""
        return {
            "timestamp": log.get("timestamp"),
            "source": "file",
            "file_path": log.get("file", {}).get("path", "unknown"),
            "message": log.get("message", ""),
            "metadata": {
                "host": log.get("host", "unknown"),
                "source_type": "file",
                "original": log
            }
        }

    def _process_syslog(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Process syslog format logs"""
        return {
            "timestamp": log.get("timestamp"),
            "source": "syslog",
            "facility": log.get("facility", "unknown"),
            "severity": log.get("severity", "unknown"),
            "message": log.get("message", ""),
            "metadata": {
                "host": log.get("host", "unknown"),
                "source_type": "syslog",
                "original": log
            }
        }

    def _process_windows_event(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Process Windows Event Log entries with OCSF mapping"""
        event_id = log.get("event_id")
        criticality = get_event_criticality(event_id)
        
        # First normalize the Windows Event
        normalized_event = {
            "timestamp": log.get("timestamp"),
            "event_id": event_id,
            "version": log.get("version"),
            "level": log.get("level"),
            "task": log.get("task"),
            "opcode": log.get("opcode"),
            "keywords": log.get("keywords"),
            "channel": log.get("channel"),
            "computer": log.get("computer"),
            "message": log.get("message"),
            "subject": log.get("event_data", {}).get("SubjectUserName"),
            "process_information": {
                "process_id": log.get("execution", {}).get("process_id"),
                "process_name": log.get("event_data", {}).get("ProcessName")
            },
            # Add other fields based on OCSF mapping requirements
        }
        
        # Map to OCSF format
        ocsf_event = self.ocsf_mapper.map_to_ocsf(normalized_event)
        
        # Validate OCSF schema
        if not self.schema_validator.validate_event(ocsf_event):
            logger.warning(f"Event failed OCSF schema validation: {log.get('event_id')}")
            
        # Track high criticality events
        if criticality == EventCriticality.HIGH:
            self.metrics.high_criticality_events.labels(
                event_id=str(event_id)
            ).inc()
        
        return ocsf_event

    def _process_generic(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Process any log format"""
        return {
            "timestamp": log.get("timestamp", datetime.utcnow().isoformat()),
            "source": "unknown",
            "message": log.get("message", ""),
            "metadata": {
                "host": log.get("host", "unknown"),
                "source_type": "unknown",
                "original": log
            }
        } 