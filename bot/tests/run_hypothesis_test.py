#!/usr/bin/env python3
"""
Run the hypothesis property-based test for pricing intelligence
"""

import sys
import os

# Add the current directory to Python path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from hypothesis import given, strategies as st, settings, assume
from test_pricing_intelligence import TestPricingIntelligenceProperties

def main():
    """Run the property-based test with hypothesis."""
    print("Running Hypothesis Property-Based Test for Pricing Intelligence...")
    
    try:
        # Initialize test suite
        test_suite = TestPricingIntelligenceProperties()
        test_suite.setup_method()
        
        # Define the resource generation strategy
        @st.composite
        def resource_strategy(draw):
            resource_type = draw(st.sampled_from(['ec2', 'rds', 'lambda', 's3', 'ebs']))
            
            # Generate realistic utilization metrics
            avg_cpu = draw(st.floats(min_value=5.0, max_value=95.0))
            data_points = draw(st.integers(min_value=30, max_value=365))
            runtime_hours = draw(st.integers(min_value=100, max_value=744))
            current_cost = draw(st.floats(min_value=10.0, max_value=1000.0))
            
            # Generate CPU utilization history
            variance = draw(st.floats(min_value=5.0, max_value=20.0))
            cpu_history = []
            for _ in range(min(10, data_points // 10)):
                cpu_val = max(0, min(100, avg_cpu + draw(st.floats(min_value=-variance, max_value=variance))))
                cpu_history.append(cpu_val)
            
            instance_type = 't3.medium'
            if resource_type == 'ec2':
                instance_type = draw(st.sampled_from(['t3.micro', 't3.small', 't3.medium', 't3.large', 'm5.large', 'm5.xlarge']))
            
            environment = draw(st.sampled_from(['production', 'staging', 'dev', 'test']))
            workload_type = draw(st.sampled_from(['web-server', 'api-server', 'batch-processing', 'analytics', 'database']))
            
            return {
                'resourceId': f'resource-{draw(st.text(min_size=8, max_size=12, alphabet="abcdef0123456789"))}',
                'resourceType': resource_type,
                'instanceType': instance_type,
                'currentCost': current_cost,
                'utilizationMetrics': {
                    'avgCpuUtilization': avg_cpu,
                    'dataPoints': data_points,
                    'runtimeHours': runtime_hours,
                    'cpuUtilizationHistory': cpu_history
                },
                'tags': {
                    'Environment': environment,
                    'Name': workload_type
                },
                'storageSizeGB': draw(st.integers(min_value=20, max_value=1000)) if resource_type in ['ec2', 'rds', 'ebs'] else 0,
                'costHistory': [current_cost + draw(st.floats(min_value=-current_cost*0.2, max_value=current_cost*0.2)) 
                               for _ in range(min(12, data_points // 30))]
            }
        
        # Run multiple test cases
        test_count = 0
        max_tests = 10  # Limit to 10 tests for demonstration
        
        @given(st.lists(resource_strategy(), min_size=1, max_size=5))
        @settings(max_examples=max_tests, deadline=60000)  # 60 second deadline
        def run_property_test(resources):
            nonlocal test_count
            test_count += 1
            
            # Ensure we have valid resources
            assume(len(resources) > 0)
            assume(all(r.get('currentCost', 0) > 0 for r in resources))
            
            print(f"  Running test case {test_count} with {len(resources)} resources...")
            
            # Execute the property test
            test_suite.test_property_pricing_intelligence_recommendation_completeness(resources)
            
            print(f"  ✓ Test case {test_count} passed")
        
        # Execute the property test
        run_property_test()
        
        print(f"\n✅ All {test_count} property-based test cases passed!")
        print("Property 4: Pricing Intelligence Recommendation Completeness validated successfully")
        print("Requirements 2.1, 2.2, 2.3, 2.5 are satisfied")
        
        return True
        
    except Exception as e:
        print(f"❌ Property-based test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)