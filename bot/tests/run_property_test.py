#!/usr/bin/env python3
"""
Simple test runner for the pricing intelligence property test
"""

import sys
import os

# Add the current directory to Python path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from test_pricing_intelligence import TestPricingIntelligenceProperties

def run_property_test():
    """Run the property test for pricing intelligence."""
    print("Running Pricing Intelligence Property Test...")
    
    try:
        # Initialize test suite
        test_suite = TestPricingIntelligenceProperties()
        test_suite.setup_method()
        
        # Create test data that should trigger recommendations
        test_resources = [
            {
                'resourceId': 'i-test123',
                'resourceType': 'ec2',
                'instanceType': 't3.medium',
                'currentCost': 50.0,
                'utilizationMetrics': {
                    'avgCpuUtilization': 75.0,
                    'dataPoints': 120,
                    'runtimeHours': 720,
                    'cpuUtilizationHistory': [70, 75, 80, 72, 78]
                },
                'tags': {'Environment': 'production', 'Name': 'web-server'},
                'storageSizeGB': 100,
                'costHistory': [48, 50, 52, 49, 51]
            },
            {
                'resourceId': 'i-spot456',
                'resourceType': 'ec2',
                'instanceType': 't3.large',
                'currentCost': 80.0,
                'utilizationMetrics': {
                    'avgCpuUtilization': 45.0,
                    'dataPoints': 90,
                    'runtimeHours': 600,
                    'cpuUtilizationHistory': [40, 45, 50, 42, 48]
                },
                'tags': {'Environment': 'dev', 'Name': 'batch-processing'},
                'storageSizeGB': 50,
                'costHistory': [75, 80, 85, 78, 82]
            },
            {
                'resourceId': 'lambda-func1',
                'resourceType': 'lambda',
                'currentCost': 150.0,
                'utilizationMetrics': {
                    'avgCpuUtilization': 60.0,
                    'dataPoints': 180,
                    'runtimeHours': 500,
                    'cpuUtilizationHistory': [55, 60, 65, 58, 62]
                },
                'tags': {'Environment': 'production', 'Name': 'api-function'},
                'storageSizeGB': 0,
                'costHistory': [140, 150, 160, 145, 155]
            }
        ]
        
        # Run the property test
        test_suite.test_property_pricing_intelligence_recommendation_completeness(test_resources)
        
        print("✅ Property test passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Property test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_property_test()
    sys.exit(0 if success else 1)