from enum import Enum
from typing import Dict

class EventCriticality(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Mapping of Event IDs to their criticality
WINDOWS_EVENT_CRITICALITY: Dict[int, EventCriticality] = {
    # High Criticality Events
    4618: EventCriticality.HIGH,  # Monitored security event pattern
    4649: EventCriticality.HIGH,  # Replay attack detected
    4719: EventCriticality.HIGH,  # System audit policy changed
    4765: EventCriticality.HIGH,  # SID History added
    4766: EventCriticality.HIGH,  # SID History add failed
    4794: EventCriticality.HIGH,  # Directory Services Restore Mode attempt
    4897: EventCriticality.HIGH,  # Role separation enabled
    4964: EventCriticality.HIGH,  # Special groups assigned to new logon
    
    # Medium to High Criticality Events
    550: EventCriticality.HIGH,   # Possible DoS attack
    1102: EventCriticality.HIGH,  # Audit log cleared
    517: EventCriticality.HIGH,   # Audit log cleared (legacy)
    
    # Medium Criticality Events
    4621: EventCriticality.MEDIUM,  # Administrator recovered system
    4675: EventCriticality.MEDIUM,  # SIDs were filtered
    4692: EventCriticality.MEDIUM,  # Backup of data protection master key
    4693: EventCriticality.MEDIUM,  # Recovery of data protection master key
    
    # Add more events as needed...
}

def get_event_criticality(event_id: int) -> EventCriticality:
    """Get the criticality level for a Windows Event ID"""
    return WINDOWS_EVENT_CRITICALITY.get(event_id, EventCriticality.LOW) 