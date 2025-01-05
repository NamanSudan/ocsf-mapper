from typing import Dict, Any
import logging
from prometheus_client import Counter, Histogram, Gauge
import time

logger = logging.getLogger(__name__)

class MetricsHandler:
    """
    Handles metrics collection and monitoring
    """
    def __init__(self):
        # Counters
        self.logs_received = Counter(
            'logs_received_total',
            'Total number of logs received',
            ['source_type']
        )
        self.logs_processed = Counter(
            'logs_processed_total',
            'Total number of logs processed successfully',
            ['source_type']
        )
        self.processing_errors = Counter(
            'log_processing_errors_total',
            'Total number of processing errors',
            ['error_type']
        )
        
        # Histograms
        self.processing_time = Histogram(
            'log_processing_seconds',
            'Time spent processing logs',
            ['operation']
        )
        
        # Gauges
        self.queue_size = Gauge(
            'log_queue_size',
            'Current number of logs in processing queue'
        )
        
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

    def track_received_log(self, source_type: str):
        """Track received log"""
        self.logs_received.labels(source_type=source_type).inc()

    def track_processed_log(self, source_type: str):
        """Track successfully processed log"""
        self.logs_processed.labels(source_type=source_type).inc()

    def track_error(self, error_type: str):
        """Track processing error"""
        self.processing_errors.labels(error_type=error_type).inc()

    def track_processing_time(self, operation: str):
        """Context manager to track operation time"""
        return self.processing_time.labels(operation=operation).time()

    def set_queue_size(self, size: int):
        """Update queue size gauge"""
        self.queue_size.set(size) 