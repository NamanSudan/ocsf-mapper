from typing import Dict, Any, Optional
from datetime import datetime
import logging
from prometheus_client import Counter

logger = logging.getLogger(__name__)

class MetricsHandler:
    def __init__(self):
        # Add OCSF-specific metrics
        self.ocsf_mappings = Counter(
            'ocsf_mappings_total',
            'Total number of events mapped to OCSF format',
            ['event_class', 'status']
        )
        
        self.ocsf_mapping_errors = Counter(
            'ocsf_mapping_errors_total',
            'Total number of OCSF mapping errors',
            ['error_type']
        )
        
        self.high_criticality_events = Counter(
            'high_criticality_events_total',
            'Total number of high criticality events detected',
            ['event_id']
        )

class OCSFWindowsEventMapper:
    """Maps Windows Events to OCSF schema based on official mappings"""
    
    def __init__(self, metrics_handler: MetricsHandler):
        # Define event class mappings based on OCSF schema
        self.event_class_map = {
            # Authentication events
            4624: {"uid": 1001, "name": "Authentication", "type": "User Logon"},
            4625: {"uid": 1001, "name": "Authentication", "type": "User Logon Failure"},
            4634: {"uid": 1001, "name": "Authentication", "type": "User Logoff"},
            
            # Process events
            4688: {"uid": 1002, "name": "Process Activity", "type": "Process Creation"},
            4689: {"uid": 1002, "name": "Process Activity", "type": "Process Termination"},
            
            # Object access events
            4656: {"uid": 1003, "name": "Object Access", "type": "Handle Requested"},
            4663: {"uid": 1003, "name": "Object Access", "type": "Object Access Attempt"},
            
            # Policy change events
            4719: {"uid": 1004, "name": "Policy Change", "type": "System Audit Policy Changed"},
            4739: {"uid": 1004, "name": "Policy Change", "type": "Domain Policy Changed"}
        }
        self.metrics = metrics_handler

    def map_to_ocsf(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Maps a Windows Event to OCSF format"""
        try:
            event_id = event.get("event_id")
            event_data = event.get("event_data", {})
            
            # Get event class information
            class_info = self.event_class_map.get(event_id, {
                "uid": 0,
                "name": "Unknown",
                "type": "Unknown"
            })

            # Base OCSF structure
            ocsf_event = {
                "type_uid": 400001,  # Windows Event Log type
                "class_uid": class_info["uid"],
                "class_name": class_info["name"],
                "activity_id": event_id,
                "activity_name": class_info["type"],
                
                "time": event.get("timestamp"),
                "message": event.get("message"),
                "severity": self._map_severity(event.get("level")),
                "status": self._map_status(event.get("keywords")),
                "category": event.get("task_category"),
                
                # Actor (Subject in Windows Events)
                "actor": self._extract_actor(event_data),
                
                # Target details
                "target": self._extract_target(event_data),
                
                # Device context
                "device": {
                    "hostname": event.get("computer"),
                    "uid": event_data.get("WorkstationName"),
                    "ip": event_data.get("IpAddress"),
                    "port": event_data.get("IpPort"),
                    "os": {
                        "name": "Windows",
                        "type": "Windows"
                    }
                },
                
                # Process details
                "process": self._extract_process(event_data),
                
                # Authentication specific fields
                "authentication": self._extract_auth_details(event_data),
                
                # Metadata and raw event
                "metadata": {
                    "version": event.get("version"),
                    "product": {
                        "name": "Microsoft Windows",
                        "vendor_name": "Microsoft",
                        "feature": {
                            "name": "Security Auditing"
                        }
                    },
                    "original_event": event
                }
            }
            
            # Track successful mapping
            self.metrics.ocsf_mappings.labels(
                event_class=class_info["name"],
                status="success"
            ).inc()
            
            return ocsf_event
            
        except Exception as e:
            # Track mapping error
            self.metrics.ocsf_mapping_errors.labels(
                error_type=type(e).__name__
            ).inc()
            logger.error(f"Error mapping event to OCSF: {str(e)}")
            return self._create_error_event(event, str(e))

    def _extract_actor(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract actor details from event data"""
        return {
            "user": {
                "name": event_data.get("SubjectUserName"),
                "uid": event_data.get("SubjectUserSid"),
                "domain": event_data.get("SubjectDomainName"),
                "type": "Windows",
                "session_uid": event_data.get("SubjectLogonId")
            },
            "session": {
                "uid": event_data.get("SubjectLogonId")
            }
        }

    def _extract_target(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract target details from event data"""
        return {
            "user": {
                "name": event_data.get("TargetUserName"),
                "uid": event_data.get("TargetUserSid"),
                "domain": event_data.get("TargetDomainName"),
                "type": "Windows"
            },
            "process": {
                "name": event_data.get("TargetProcessName"),
                "pid": event_data.get("TargetProcessId")
            },
            "resource": {
                "name": event_data.get("ObjectName"),
                "type": event_data.get("ObjectType")
            }
        }

    def _extract_process(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract process details from event data"""
        return {
            "name": event_data.get("ProcessName"),
            "pid": event_data.get("ProcessId"),
            "cmd_line": event_data.get("CommandLine"),
            "parent_process": {
                "pid": event_data.get("ParentProcessId"),
                "name": event_data.get("ParentProcessName")
            }
        }

    def _extract_auth_details(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract authentication details from event data"""
        return {
            "protocol": event_data.get("AuthenticationPackageName"),
            "logon_type": event_data.get("LogonType"),
            "process": event_data.get("LogonProcessName"),
            "session": {
                "uid": event_data.get("LogonID")
            }
        }

    def _map_severity(self, level: Optional[int]) -> str:
        """Map Windows Event level to OCSF severity"""
        if level is None:
            return "UNKNOWN"
            
        severity_map = {
            1: "CRITICAL",
            2: "HIGH",
            3: "MEDIUM",
            4: "LOW",
            5: "INFO"
        }
        return severity_map.get(level, "UNKNOWN")

    def _map_status(self, keywords: Optional[str]) -> str:
        """Map Windows Event keywords to OCSF status"""
        if not keywords:
            return "UNKNOWN"
            
        if "Audit Success" in keywords:
            return "SUCCESS"
        elif "Audit Failure" in keywords:
            return "FAILURE"
        return "UNKNOWN"

    def _create_error_event(self, original_event: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create an error event when mapping fails"""
        return {
            "class_uid": 0,
            "class_name": "Unknown",
            "time": datetime.utcnow().isoformat(),
            "message": f"Failed to map event: {error}",
            "severity": "ERROR",
            "metadata": {
                "error": error,
                "original_event": original_event
            }
        } 