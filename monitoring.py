# File: monitoring.py
# Day 8: Basic monitoring and metrics

from datetime import datetime
import psutil
import time
from typing import Dict, Any

class SimpleMonitoring:
    """Basic application monitoring"""

    def __init__(self):
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0

    def record_request(self):
        """Record API request"""
        self.request_count += 1

    def record_error(self):
        """Record API error"""
        self.error_count += 1

    def get_health_status(self) -> Dict[str, Any]:
        """Get application health status"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "status": "healthy",
            "uptime_seconds": uptime,
            "requests_total": self.request_count,
            "errors_total": self.error_count,
            "error_rate": self.error_count / max(1, self.request_count),
            "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
            "cpu_percent": psutil.cpu_percent(),
            "timestamp": datetime.now().isoformat()
        }

# Global monitoring instance
monitor = SimpleMonitoring()
