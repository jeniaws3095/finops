#!/usr/bin/env python3
"""
Property-Based Test for ML Right-Sizing Engine

**Feature: advanced-finops-platform, Property 7: ML Recommendation Quality**
**Validates: Requirements 3.2, 3.3**

This test validates that the ML right-sizing engine generates recommendations with:
- Confidence intervals (Requirement 3.2)
- Cost savings estimates and performance impact assessments (Requirement 3.3)
"""

import sys
import os
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume, settings, HealthCheck

# Add the project root to Python path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.ml_rightsizing import MLRightSizingEngine
from utils.aws_config import AWSConfig


# Simplified strategy for generating ML test resources
@st.composite
def simple_ml_resource(draw):
    """Generate a simple resource with sufficient historical data for ML analysis."""
    resource_type = draw(st.sampled_from(['ec2']))  # Focus on EC2 for simplicity
    
    # Fixed data points for consistency
    data_points = 200  # ~8 days of hourly data
    current_cost = draw(st.floats(min_value=30.0, max_value=200.0))
    
    # Generate realistic CPU utilization with some variance
    base_cpu = draw(st.floats(min_value=15.0, max_value=70.0))
    cpu_variance = draw(st.floats(min_value=3.0, max_value=10.0))
    
    # Create consistent time series data
    cpu_history = []
    memory_history = []
    
    for i in range(data_points):
        # Simple seasonal pattern (daily cycle)
        seasonal_factor = 1 + 0.1 * (1 if (i % 24) < 12 else -1)
        
        # Add variance
        cpu_val = max(5, min(90, base_cpu * seasonal_factor + draw(st.floats(min_value=-cpu_variance, max_value=cpu_variance))))
        memory_val = max(10, min(85, cpu_val * 1.2 + draw(st.floats(min_value=-5.0, max_value=5.0))))
        
        cpu_history.append(cpu_val)
        memory_history.append(memory_val)
    
    # Generate correlated network and disk metrics
    network_in = [max(50, cpu * 3) for cpu in cpu_history]
    network_out = [max(30, cpu * 2) for cpu in cpu_history]
    disk_read_ops = [max(10, cpu * 1.5) for cpu in cpu_history]
    disk_write_ops = [max(5, cpu * 1) for cpu in cpu_history]
    disk_read_bytes = [max(500, cpu * 25) for cpu in cpu_history]
    disk_write_bytes = [max(300, cpu * 15) for cpu in cpu_history]
    
    # Generate timestamps
    timestamps = [(datetime.utcnow() - timedelta(hours=i)).isoformat() for i in range(data_points, 0, -1)]
    
    # Resource configuration
    instance_type = draw(st.sampled_from(['t3.small', 't3.medium', 't3.large', 'm5.large']))
    
    return {
        'resourceId': f'i-{draw(st.text(min_size=8, max_size=12, alphabet="abcdef0123456789"))}',
        'resourceType': resource_type,
        'instanceType': instance_type,
        'currentCost': current_cost,
        'utilizationMetrics': {
            'cpuUtilizationHistory': cpu_history,
            'memoryUtilizationHistory': memory_history,
            'networkInHistory': network_in,
            'networkOutHistory': network_out,
            'diskReadOpsHistory': disk_read_ops,
            'diskWriteOpsHistory': disk_write_ops,
            'diskReadBytesHistory': disk_read_bytes,
            'diskWriteBytesHistory': disk_write_bytes,
            'timestamps': timestamps,
            'dataPoints': data_points
        },
        'tags': {
            'Environment': draw(st.sampled_from(['production', 'staging', 'dev'])),
            'Name': draw(st.sampled_from(['web-server', 'api-server', 'worker']))
        }
    }


class TestMLRightSizingProperties:
    """Property-based tests for ML right-sizing engine."""
    
    def __init__(self):
        self.aws_config = AWSConfig()
        self.engine = MLRightSizingEngine(self.aws_config, region='us-east-1')
    
    @given(simple_ml_resource())
    @settings(max_examples=3, deadline=30000, suppress_health_check=[HealthCheck.large_base_example, HealthCheck.data_too_large])
    def test_ml_recommendation_quality_property(self, resource):
        """
        **Property 7: ML Recommendation Quality**
        **Validates: Requirements 3.2, 3.3**
        
        For any resource with sufficient historical data, the ML right-sizing engine should 
        generate recommendations with confidence intervals, cost savings estimates, and 
        performance impact assessments.
        """
        # Ensure we have valid resource with sufficient data
        assume(resource.get('currentCost', 0) > 0)
        assume(resource.get('utilizationMetrics', {}).get('dataPoints', 0) >= 168)
        
        # Execute ML right-sizing analysis
        result = self.engine.analyze_rightsizing_opportunities([resource])
        
        # Property 1: Analysis result must be complete and well-structured
        assert isinstance(result, dict), "ML analysis result must be a dictionary"
        
        required_keys = ['summary', 'recommendations', 'mlModelsUsed', 'analysisTimestamp', 'region']
        for key in required_keys:
            assert key in result, f"ML analysis result must contain '{key}'"
        
        # Property 2: If recommendations are generated, they must have confidence intervals
        # (Validates Requirement 3.2: Generate ML-powered size recommendations with confidence intervals)
        recommendations = result['recommendations']
        
        for recommendation in recommendations:
            # Each recommendation must have confidence analysis with intervals
            assert 'confidenceAnalysis' in recommendation, "ML recommendation must have confidence analysis"
            
            confidence_analysis = recommendation['confidenceAnalysis']
            required_confidence_fields = ['overall_confidence', 'confidence_level', 'confidence_interval']
            
            for field in required_confidence_fields:
                assert field in confidence_analysis, f"Confidence analysis must contain '{field}'"
            
            # Confidence interval must be properly structured
            confidence_interval = confidence_analysis['confidence_interval']
            assert 'lower' in confidence_interval, "Confidence interval must have lower bound"
            assert 'upper' in confidence_interval, "Confidence interval must have upper bound"
            assert confidence_interval['lower'] >= 0, "Lower confidence bound must be non-negative"
            assert confidence_interval['upper'] > confidence_interval['lower'], "Upper bound must be greater than lower bound"
            
            # Overall confidence must be valid percentage
            overall_confidence = confidence_analysis['overall_confidence']
            assert 0 <= overall_confidence <= 100, f"Overall confidence must be 0-100%, got {overall_confidence}"
            
            # Confidence level must be valid
            confidence_level = confidence_analysis['confidence_level']
            assert confidence_level in ['LOW', 'MEDIUM', 'HIGH'], f"Invalid confidence level: {confidence_level}"
        
        # Property 3: All ML recommendations must have cost savings estimates and performance impact
        # (Validates Requirement 3.3: Estimate cost savings and performance impact)
        for recommendation in recommendations:
            # Each recommendation must have cost analysis
            assert 'costAnalysis' in recommendation, "ML recommendation must have cost analysis"
            
            cost_analysis = recommendation['costAnalysis']
            required_cost_fields = ['current_cost', 'projected_cost', 'monthly_savings', 'annual_savings', 'savings_percentage']
            
            for field in required_cost_fields:
                assert field in cost_analysis, f"Cost analysis must contain '{field}'"
            
            # Cost values must be logical
            current_cost = cost_analysis['current_cost']
            projected_cost = cost_analysis['projected_cost']
            monthly_savings = cost_analysis['monthly_savings']
            annual_savings = cost_analysis['annual_savings']
            
            assert current_cost >= 0, "Current cost must be non-negative"
            assert projected_cost >= 0, "Projected cost must be non-negative"
            assert annual_savings == monthly_savings * 12, "Annual savings must equal monthly savings * 12"
            
            # Each recommendation must have performance impact analysis
            assert 'performanceImpact' in recommendation, "ML recommendation must have performance impact analysis"
            
            performance_impact = recommendation['performanceImpact']
            required_performance_fields = ['impact_level', 'impact_description']
            
            for field in required_performance_fields:
                assert field in performance_impact, f"Performance impact must contain '{field}'"
            
            # Impact level must be valid
            impact_level = performance_impact['impact_level']
            valid_impact_levels = ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'POSITIVE']
            assert impact_level in valid_impact_levels, f"Invalid impact level: {impact_level}"
        
        # Property 4: ML recommendations must include ML-specific details
        for recommendation in recommendations:
            assert 'mlDetails' in recommendation, "ML recommendation must have ML details"
            
            ml_details = recommendation['mlDetails']
            required_ml_fields = ['modelsUsed', 'predictions', 'optimalConfig']
            
            for field in required_ml_fields:
                assert field in ml_details, f"ML details must contain '{field}'"
            
            # Models used must be a list
            models_used = ml_details['modelsUsed']
            assert isinstance(models_used, list), "Models used must be a list"
            assert len(models_used) > 0, "Must use at least one ML model"
            
            # Predictions must be a dictionary with model results
            predictions = ml_details['predictions']
            assert isinstance(predictions, dict), "Predictions must be a dictionary"
            assert len(predictions) > 0, "Must have at least one prediction"


def run_property_test():
    """Run the property-based test manually."""
    print("Running ML Right-Sizing Property-Based Test...")
    
    test_suite = TestMLRightSizingProperties()
    
    # Run the hypothesis test directly
    try:
        test_suite.test_ml_recommendation_quality_property()
        print("\n✅ All ML property-based tests passed!")
    except Exception as e:
        print(f"\n❌ Property test failed: {str(e)}")
        raise


if __name__ == '__main__':
    try:
        run_property_test()
    except Exception as e:
        print(f"\n❌ Property test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)