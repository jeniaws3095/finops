#!/usr/bin/env python3
"""
Task 15: Final Integration and Validation Test

This test validates the complete integration between the Python automation engine
and the backend API, including:
- Data flow from Python to API
- Error handling and recovery mechanisms
- Real-time synchronization
- Monitoring and alerting systems
- End-to-end workflow validation

Requirements being validated: 9.1, 4.4
"""

import pytest
import requests
import json
import time
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

class TestTask15Integration:
    """Test complete integration for Task 15."""
    
    def setup_method(self):
        """Set up test environment."""
        self.backend_url = "http://localhost:5002"
        self.timeout = 10
        
        # Test data samples
        self.sample_resource = {
            'resourceId': 'test-resource-001',
            'resourceType': 'ec2',
            'region': 'us-east-1',
            'currentCost': 150.0,
            'utilizationMetrics': {
                'cpu': 25.5,
                'memory': 60.2,
                'network': 15.8
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.sample_optimization = {
            'optimizationId': 'opt-test-001',
            'resourceId': 'test-resource-001',
            'optimizationType': 'rightsizing',
            'currentCost': 150.0,
            'projectedCost': 100.0,
            'estimatedSavings': 50.0,
            'confidenceScore': 0.