#!/usr/bin/env python3
"""
Run the hypothesis property-based test for ML right-sizing engine
"""

import sys
import os
from datetime import datetime, timedelta
import numpy as np

# Add the project root to Python path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from hypothesis import given, strategies as st, settings, assume
from test_ml_rightsizing import TestMLRightSizingProperties, ml_resource_with_history

def main():
    """Run the property-based test with hypothesis."""
    print("Running Hypothesis Property-Based Test for ML Right-Sizing...")
    print("=" * 60)
    
    try:
        # Initialize test suite
        test_suite = TestMLRightSizingProperties()
        test_suite.setup_method()
        
        # Counter for test cases
        test_count = 0
        
        # Configure hypothesis settings
        max_tests = 15  # Limit to 15 tests for demonstration (ML operations are computationally intensive)
        
        @given(st.lists(ml_resource_with_history(), min_size=1, max_size=3))
        @settings(max_examples=max_tests, deadline=90000)  # 90 second deadline for ML operations
        def run_property_test(resources):
            nonlocal test_count
            test_count += 1
            
            print(f"\n🔬 Test Case {test_count}:")
            print(f"  📊 Resources: {len(resources)}")
            
            # Display resource details
            for i, resource in enumerate(resources):
                resource_type = resource.get('resourceType', 'unknown')
                data_points = resource.get('utilizationMetrics', {}).get('dataPoints', 0)
                current_cost = resource.get('currentCost', 0)
                print(f"    Resource {i+1}: {resource_type} (${current_cost:.2f}/month, {data_points} data points)")
            
            print(f"  🧠 Running ML analysis with multiple models...")
            
            # Execute the property test
            test_suite.test_property_ml_recommendation_quality(resources)
            
            print(f"  ✅ Test case {test_count} passed - ML recommendations validated")
        
        # Execute the property test
        print("🚀 Starting property-based testing...")
        run_property_test()
        
        print(f"\n🎉 SUCCESS: All {test_count} property-based test cases passed!")
        print("\n📋 Test Summary:")
        print("   ✓ Property 7: ML Recommendation Quality validated successfully")
        print("   ✓ Requirements 3.2, 3.3 are satisfied")
        print("   ✓ ML right-sizing engine generates recommendations with:")
        print("     - Confidence intervals from multiple ML models")
        print("     - Cost savings estimates with detailed analysis")
        print("     - Performance impact assessments")
        print("     - Proper risk categorization and prioritization")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Property-based test failed: {str(e)}")
        print("\n🔍 Error Details:")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)