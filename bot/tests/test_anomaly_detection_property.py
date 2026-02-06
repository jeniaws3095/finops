#!/usr/bin/env python3
"""
Property-Based Test for Cost Anomaly Detection

**Feature: advanced-finops-platform, Property 11: Cost Spike Detection Accuracy**

This test validates that for any cost increase exceeding configured thresholds, 
the Anomaly_Detector should detect the anomaly and perform root cause analysis 
to identify contributing resources.

**Validates: Requirements 4.2, 4.3**

The test uses property-based testing to generate various cost scenarios and verify 
that the anomaly detection logic is accurate and consistent across different 
cost patterns, thresholds, and resource configurations.
"""

import pytest
from hypothesis import given, strategies as st, settings, example, assume
from hypothesis.strategies import composite
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import logging
import statistics
import random

# Import the anomaly detector we want to test
from core.anomaly_detector import AnomalyDetector, AnomalyType, AnomalySeverity

# Mock AWS config for testing
class MockAWSConfig:
    """Mock AWS configuration for testing."""
    
    def __init__(self, region='us-east-1'):
        self.region = region
    
    def get_client(self, service_name):
        return MockAWSClient(service_name)
    
    def get_resource(self, service_name):
        return MockAWSResource(service_name)

class MockAWSClient:
    """Mock AWS client for testing."""
    
    def __init__(self, service_name):
        self.service_name = service_name

class MockAWSResource:
    """Mock AWS resource for testing."""
    
    def __init__(self, service_name):
        self.service_name = service_name

# Strategy generators for cost data and anomaly scenarios
@composite
def baseline_cost_data(draw):
    """Generate baseline cost data with normal patterns."""
    base_cost = draw(st.floats(min_value=50.0, max_value=500.0))
    days = draw(st.integers(min_value=14, max_value=60))  # 2 weeks to 2 months
    hourly_variation = draw(st.floats(min_value=0.05, max_value=0.3))  # 5-30% variation
    daily_variation = draw(st.floats(min_value=0.1, max_value=0.2))   # 10-20% daily variation
    
    cost_data = []
    base_time = datetime.now(timezone.utc) - timedelta(days=days)
    
    for day in range(days):
        for hour in range(24):
            timestamp = base_time + timedelta(days=day, hours=hour)
            
            # Create realistic patterns
            # Business hours (9-17) have higher costs
            hour_factor = 1.0 + (hourly_variation if 9 <= hour <= 17 else 0)
            # Weekdays have higher costs than weekends
            day_factor = 1.0 + (daily_variation if day % 7 < 5 else 0)
            # Add some random noise
            noise_factor = 1.0 + draw(st.floats(min_value=-0.1, max_value=0.1))
            
            cost = base_cost * hour_factor * day_factor * noise_factor
            cost = max(0, cost)  # Ensure non-negative
            
            cost_data.append({
                'timestamp': timestamp.isoformat(),
                'cost': cost,
                'service': 'mixed',
                'region': 'us-east-1'
            })
    
    return cost_data

@composite
def anomaly_injection_config(draw):
    """Generate configuration for injecting anomalies into cost data."""
    return {
        'anomaly_type': draw(st.sampled_from(['spike', 'sustained_increase', 'trend_change'])),
        'severity_multiplier': draw(st.floats(min_value=1.5, max_value=5.0)),  # How much to increase cost
        'duration_hours': draw(st.integers(min_value=1, max_value=48)),  # How long the anomaly lasts
        'start_offset_hours': draw(st.integers(min_value=24, max_value=168)),  # When to inject (from end)
        'affected_services': draw(st.lists(
            st.sampled_from(['ec2', 'rds', 'lambda', 's3', 'ebs']), 
            min_size=1, max_size=3, unique=True
        ))
    }

@composite
def resource_data_for_root_cause(draw):
    """Generate resource data for root cause analysis."""
    num_resources = draw(st.integers(min_value=1, max_value=10))
    resources = []
    
    for i in range(num_resources):
        resource_type = draw(st.sampled_from(['ec2', 'rds', 'lambda', 's3', 'ebs']))
        
        # Generate cost increase that could contribute to anomaly
        historical_cost = draw(st.floats(min_value=10.0, max_value=200.0))
        cost_increase_factor = draw(st.floats(min_value=1.0, max_value=3.0))
        current_cost = historical_cost * cost_increase_factor
        
        resource = {
            'resourceId': f"{resource_type}-{i:03d}-{draw(st.text(min_size=8, max_size=12, alphabet='0123456789abcdef'))}",
            'resourceType': resource_type,
            'region': 'us-east-1',
            'currentCost': current_cost,
            'historicalAverageCost': historical_cost,
            'tags': {
                'Environment': draw(st.sampled_from(['production', 'staging', 'development'])),
                'Team': draw(st.sampled_from(['backend', 'frontend', 'data', 'analytics', 'infrastructure'])),
                'Application': draw(st.text(min_size=3, max_size=15, alphabet='abcdefghijklmnopqrstuvwxyz'))
            }
        }
        
        # Add resource-type specific fields
        if resource_type == 'ec2':
            resource['instanceType'] = draw(st.sampled_from(['t3.micro', 't3.small', 't3.medium', 'm5.large', 'c5.xlarge']))
        elif resource_type == 'rds':
            resource['dbInstanceClass'] = draw(st.sampled_from(['db.t3.micro', 'db.t3.small', 'db.m5.large']))
        elif resource_type == 'lambda':
            resource['memorySize'] = draw(st.sampled_from([128, 256, 512, 1024, 2048]))
            resource['timeout'] = draw(st.integers(min_value=3, max_value=900))
        elif resource_type == 'ebs':
            resource['volumeType'] = draw(st.sampled_from(['gp2', 'gp3', 'io1', 'io2']))
            resource['size'] = draw(st.integers(min_value=8, max_value=1000))
        
        resources.append(resource)
    
    return resources

@composite
def threshold_configuration(draw):
    """Generate threshold configuration for anomaly detection."""
    return {
        'cost_spike_threshold': draw(st.floats(min_value=1.5, max_value=4.0)),
        'percentage_increase_threshold': draw(st.floats(min_value=25.0, max_value=100.0)),
        'absolute_cost_threshold': draw(st.floats(min_value=50.0, max_value=200.0)),
        'consecutive_anomaly_threshold': draw(st.integers(min_value=2, max_value=5))
    }

def inject_anomaly_into_cost_data(cost_data: List[Dict[str, Any]], 
                                 anomaly_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Inject a known anomaly into cost data for testing."""
    if not cost_data:
        return cost_data
    
    # Make a copy to avoid modifying original data
    modified_data = cost_data.copy()
    
    # Calculate baseline statistics
    costs = [float(item['cost']) for item in cost_data]
    baseline_mean = statistics.mean(costs)
    baseline_std = statistics.stdev(costs) if len(costs) > 1 else baseline_mean * 0.1
    
    # Determine injection point
    start_index = max(0, len(modified_data) - anomaly_config['start_offset_hours'])
    end_index = min(len(modified_data), start_index + anomaly_config['duration_hours'])
    
    # Inject anomaly based on type
    anomaly_type = anomaly_config['anomaly_type']
    severity_multiplier = anomaly_config['severity_multiplier']
    
    for i in range(start_index, end_index):
        original_cost = modified_data[i]['cost']
        
        if anomaly_type == 'spike':
            # Sharp cost spike
            modified_data[i]['cost'] = original_cost * severity_multiplier
        elif anomaly_type == 'sustained_increase':
            # Sustained cost increase
            modified_data[i]['cost'] = original_cost * severity_multiplier
        elif anomaly_type == 'trend_change':
            # Gradual trend change
            progress = (i - start_index) / max(1, end_index - start_index)
            multiplier = 1.0 + (severity_multiplier - 1.0) * progress
            modified_data[i]['cost'] = original_cost * multiplier
    
    return modified_data

class TestAnomalyDetectionAccuracy:
    """Test suite for cost anomaly detection accuracy and root cause analysis."""
    
    def setup_method(self):
        """Set up test environment."""
        self.mock_aws_config = MockAWSConfig()
        self.detector = AnomalyDetector(self.mock_aws_config, region='us-east-1')
    
    @given(
        baseline_data=baseline_cost_data(),
        anomaly_config=anomaly_injection_config(),
        resources=resource_data_for_root_cause()
    )
    @settings(max_examples=50, deadline=None)
    def test_cost_spike_detection_accuracy(self, baseline_data, anomaly_config, resources):
        """
        Property: Cost spike detection should accurately identify anomalies exceeding thresholds.
        
        **Validates: Requirements 4.2**
        
        For any cost increase exceeding configured thresholds, the Anomaly_Detector 
        should detect the anomaly with appropriate severity classification.
        """
        # Assume we have sufficient baseline data
        assume(len(baseline_data) >= 24)  # At least 24 hours of data
        
        # Inject known anomaly
        cost_data_with_anomaly = inject_anomaly_into_cost_data(baseline_data, anomaly_config)
        
        # Calculate expected anomaly characteristics
        baseline_costs = [float(item['cost']) for item in baseline_data]
        baseline_mean = statistics.mean(baseline_costs)
        baseline_std = statistics.stdev(baseline_costs) if len(baseline_costs) > 1 else baseline_mean * 0.1
        
        # Run anomaly detection
        results = self.detector.detect_anomalies(cost_data_with_anomaly, resources)
        
        # Property 1: Baseline should be established with sufficient data
        assert results['baseline_analysis']['baseline_established'], \
            "Baseline should be established with sufficient historical data"
        
        baseline_stats = results['baseline_analysis']['baseline_statistics']
        assert baseline_stats['data_points'] >= 24, \
            "Baseline should include sufficient data points"
        assert baseline_stats['mean'] > 0, \
            "Baseline mean should be positive"
        assert baseline_stats['std_dev'] >= 0, \
            "Baseline standard deviation should be non-negative"
        
        # Property 2: Injected anomaly should be detected
        anomalies = results['anomalies_detected']
        
        # Calculate expected deviation for injected anomaly
        severity_multiplier = anomaly_config['severity_multiplier']
        expected_deviation_std = (baseline_mean * severity_multiplier - baseline_mean) / baseline_std
        
        # Should detect anomaly if it exceeds thresholds
        thresholds = self.detector.detection_thresholds['anomaly_thresholds']
        should_detect = (
            expected_deviation_std >= thresholds['cost_spike_threshold'] or
            (severity_multiplier - 1.0) * 100 >= thresholds['percentage_increase_threshold'] or
            (baseline_mean * severity_multiplier - baseline_mean) >= thresholds['absolute_cost_threshold']
        )
        
        if should_detect:
            assert len(anomalies) > 0, \
                f"Should detect anomaly with {severity_multiplier}x cost increase " \
                f"(expected std dev: {expected_deviation_std:.2f})"
            
            # Check that detected anomaly has correct characteristics
            detected_anomaly = anomalies[0]  # Check first anomaly
            
            assert 'anomalyId' in detected_anomaly, "Anomaly should have unique ID"
            assert 'timestamp' in detected_anomaly, "Anomaly should have timestamp"
            assert 'severity' in detected_anomaly, "Anomaly should have severity"
            assert 'actualCost' in detected_anomaly, "Anomaly should have actual cost"
            assert 'expectedCost' in detected_anomaly, "Anomaly should have expected cost"
            assert 'deviationPercentage' in detected_anomaly, "Anomaly should have deviation percentage"
            
            # Severity should match the magnitude of the anomaly
            severity = detected_anomaly['severity']
            severity_mapping = self.detector.detection_thresholds['severity_mapping']
            
            if expected_deviation_std >= severity_mapping['critical_threshold']:
                assert severity == 'CRITICAL', f"High deviation should be CRITICAL, got {severity}"
            elif expected_deviation_std >= severity_mapping['high_threshold']:
                assert severity in ['HIGH', 'CRITICAL'], f"Medium-high deviation should be HIGH or CRITICAL, got {severity}"
            elif expected_deviation_std >= severity_mapping['medium_threshold']:
                assert severity in ['MEDIUM', 'HIGH', 'CRITICAL'], f"Medium deviation should be MEDIUM or higher, got {severity}"
        
        # Property 3: Detection should be deterministic
        results_2 = self.detector.detect_anomalies(cost_data_with_anomaly, resources)
        assert len(results['anomalies_detected']) == len(results_2['anomalies_detected']), \
            "Anomaly detection should be deterministic"
        
        # Property 4: All detected anomalies should have valid structure
        for anomaly in anomalies:
            assert anomaly['severity'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], \
                f"Invalid severity: {anomaly['severity']}"
            assert anomaly['actualCost'] >= 0, "Actual cost should be non-negative"
            assert anomaly['expectedCost'] >= 0, "Expected cost should be non-negative"
            assert 'anomalyType' in anomaly, "Anomaly should have type"
            assert 'region' in anomaly, "Anomaly should have region"
            assert 'detectedAt' in anomaly, "Anomaly should have detection timestamp"
    
    @given(
        baseline_data=baseline_cost_data(),
        anomaly_config=anomaly_injection_config(),
        resources=resource_data_for_root_cause()
    )
    @settings(max_examples=30, deadline=None)
    def test_root_cause_analysis_accuracy(self, baseline_data, anomaly_config, resources):
        """
        Property: Root cause analysis should identify contributing resources.
        
        **Validates: Requirements 4.3**
        
        For any detected anomaly, the system should perform root cause analysis 
        to identify contributing resources and services.
        """
        # Assume we have sufficient data
        assume(len(baseline_data) >= 24)
        assume(len(resources) >= 1)
        
        # Inject known anomaly
        cost_data_with_anomaly = inject_anomaly_into_cost_data(baseline_data, anomaly_config)
        
        # Run anomaly detection
        results = self.detector.detect_anomalies(cost_data_with_anomaly, resources)
        
        # Property 1: If anomalies are detected, they should have root cause analysis
        anomalies = results['anomalies_detected']
        
        for anomaly in anomalies:
            assert 'rootCauseAnalysis' in anomaly, \
                "Detected anomaly should have root cause analysis"
            
            root_cause = anomaly['rootCauseAnalysis']
            
            # Root cause analysis should have required structure
            assert 'analysisTimestamp' in root_cause, \
                "Root cause analysis should have timestamp"
            assert 'anomalyId' in root_cause, \
                "Root cause analysis should reference anomaly ID"
            assert 'contributingFactors' in root_cause, \
                "Root cause analysis should identify contributing factors"
            assert 'serviceBreakdown' in root_cause, \
                "Root cause analysis should include service breakdown"
            assert 'resourceBreakdown' in root_cause, \
                "Root cause analysis should include resource breakdown"
            assert 'recommendations' in root_cause, \
                "Root cause analysis should include recommendations"
            
            # Contributing factors should be properly structured
            contributing_factors = root_cause['contributingFactors']
            for factor in contributing_factors:
                assert 'type' in factor, "Contributing factor should have type"
                assert factor['type'] in ['service', 'resource'], \
                    f"Invalid contributing factor type: {factor['type']}"
                assert 'contribution' in factor, "Contributing factor should have contribution percentage"
                assert 0 <= factor['contribution'] <= 100, \
                    f"Invalid contribution percentage: {factor['contribution']}"
                assert 'description' in factor, "Contributing factor should have description"
                
                if factor['type'] == 'service':
                    assert 'name' in factor, "Service factor should have name"
                elif factor['type'] == 'resource':
                    assert 'resourceId' in factor, "Resource factor should have resource ID"
                    assert 'resourceType' in factor, "Resource factor should have resource type"
            
            # Service breakdown should analyze all provided services
            service_breakdown = root_cause['serviceBreakdown']
            provided_services = set(resource['resourceType'] for resource in resources)
            
            for service_type in provided_services:
                if service_type in service_breakdown:
                    service_data = service_breakdown[service_type]
                    assert 'cost_increase' in service_data, \
                        f"Service {service_type} should have cost increase data"
                    assert 'resource_count' in service_data, \
                        f"Service {service_type} should have resource count"
                    assert 'contribution_percentage' in service_data, \
                        f"Service {service_type} should have contribution percentage"
                    
                    assert service_data['cost_increase'] >= 0, \
                        f"Service {service_type} cost increase should be non-negative"
                    assert service_data['resource_count'] > 0, \
                        f"Service {service_type} should have positive resource count"
                    assert 0 <= service_data['contribution_percentage'] <= 100, \
                        f"Service {service_type} contribution should be 0-100%"
            
            # Resource breakdown should analyze all provided resources
            resource_breakdown = root_cause['resourceBreakdown']
            
            for resource in resources:
                resource_id = resource['resourceId']
                if resource_id in resource_breakdown:
                    resource_data = resource_breakdown[resource_id]
                    assert 'resource_type' in resource_data, \
                        f"Resource {resource_id} should have type"
                    assert 'current_cost' in resource_data, \
                        f"Resource {resource_id} should have current cost"
                    assert 'historical_cost' in resource_data, \
                        f"Resource {resource_id} should have historical cost"
                    assert 'cost_increase' in resource_data, \
                        f"Resource {resource_id} should have cost increase"
                    assert 'contribution_percentage' in resource_data, \
                        f"Resource {resource_id} should have contribution percentage"
                    
                    assert resource_data['current_cost'] >= 0, \
                        f"Resource {resource_id} current cost should be non-negative"
                    assert resource_data['historical_cost'] >= 0, \
                        f"Resource {resource_id} historical cost should be non-negative"
                    assert resource_data['cost_increase'] >= 0, \
                        f"Resource {resource_id} cost increase should be non-negative"
                    assert 0 <= resource_data['contribution_percentage'] <= 100, \
                        f"Resource {resource_id} contribution should be 0-100%"
            
            # Recommendations should be actionable
            recommendations = root_cause['recommendations']
            for recommendation in recommendations:
                assert 'type' in recommendation, "Recommendation should have type"
                assert 'priority' in recommendation, "Recommendation should have priority"
                assert 'title' in recommendation, "Recommendation should have title"
                assert 'description' in recommendation, "Recommendation should have description"
                assert 'action' in recommendation, "Recommendation should have action"
                
                assert recommendation['priority'] in ['LOW', 'MEDIUM', 'HIGH'], \
                    f"Invalid recommendation priority: {recommendation['priority']}"
                assert len(recommendation['title']) > 0, "Recommendation title should not be empty"
                assert len(recommendation['description']) > 0, "Recommendation description should not be empty"
                assert len(recommendation['action']) > 0, "Recommendation action should not be empty"
    
    @given(
        baseline_data=baseline_cost_data(),
        threshold_config=threshold_configuration()
    )
    @settings(max_examples=25, deadline=None)
    def test_configurable_threshold_behavior(self, baseline_data, threshold_config):
        """
        Property: Anomaly detection should respect configurable thresholds.
        
        **Validates: Requirements 4.2**
        
        The system should detect anomalies based on configurable thresholds and 
        adjust sensitivity accordingly.
        """
        assume(len(baseline_data) >= 24)
        
        # Temporarily modify detector thresholds
        original_thresholds = self.detector.detection_thresholds['anomaly_thresholds'].copy()
        self.detector.detection_thresholds['anomaly_thresholds'].update(threshold_config)
        
        try:
            # Create a mild anomaly that may or may not trigger based on thresholds
            mild_anomaly_config = {
                'anomaly_type': 'spike',
                'severity_multiplier': 1.8,  # 80% increase
                'duration_hours': 2,
                'start_offset_hours': 48,
                'affected_services': ['ec2']
            }
            
            cost_data_with_anomaly = inject_anomaly_into_cost_data(baseline_data, mild_anomaly_config)
            
            # Run detection
            results = self.detector.detect_anomalies(cost_data_with_anomaly)
            
            # Property: Detection should respect configured thresholds
            anomalies = results['anomalies_detected']
            
            # Calculate expected behavior based on thresholds
            baseline_costs = [float(item['cost']) for item in baseline_data]
            baseline_mean = statistics.mean(baseline_costs)
            baseline_std = statistics.stdev(baseline_costs) if len(baseline_costs) > 1 else baseline_mean * 0.1
            
            expected_deviation_std = (baseline_mean * 1.8 - baseline_mean) / baseline_std
            percentage_increase = 80.0  # 80% increase
            absolute_increase = baseline_mean * 0.8
            
            should_detect = (
                expected_deviation_std >= threshold_config['cost_spike_threshold'] or
                percentage_increase >= threshold_config['percentage_increase_threshold'] or
                absolute_increase >= threshold_config['absolute_cost_threshold']
            )
            
            if should_detect:
                assert len(anomalies) > 0, \
                    f"Should detect anomaly with thresholds: spike={threshold_config['cost_spike_threshold']}, " \
                    f"percentage={threshold_config['percentage_increase_threshold']}, " \
                    f"absolute={threshold_config['absolute_cost_threshold']}"
            
            # Property: Threshold configuration should be persistent
            assert self.detector.detection_thresholds['anomaly_thresholds']['cost_spike_threshold'] == \
                   threshold_config['cost_spike_threshold'], \
                   "Threshold configuration should be applied"
        
        finally:
            # Restore original thresholds
            self.detector.detection_thresholds['anomaly_thresholds'] = original_thresholds
    
    @given(baseline_data=baseline_cost_data())
    @settings(max_examples=20, deadline=None)
    def test_baseline_establishment_accuracy(self, baseline_data):
        """
        Property: Baseline establishment should be accurate and robust.
        
        **Validates: Requirements 4.1**
        
        The system should establish accurate baseline patterns from historical data
        and select appropriate models for anomaly detection.
        """
        assume(len(baseline_data) >= 24)
        
        # Run anomaly detection to trigger baseline establishment
        results = self.detector.detect_anomalies(baseline_data)
        
        baseline_analysis = results['baseline_analysis']
        
        # Property 1: Baseline should be established with sufficient data
        assert baseline_analysis['baseline_established'], \
            "Baseline should be established with sufficient historical data"
        
        # Property 2: Baseline statistics should be accurate
        baseline_stats = baseline_analysis['baseline_statistics']
        actual_costs = [float(item['cost']) for item in baseline_data]
        
        assert abs(baseline_stats['mean'] - statistics.mean(actual_costs)) < 0.01, \
            "Baseline mean should match actual data mean"
        assert abs(baseline_stats['median'] - statistics.median(actual_costs)) < 0.01, \
            "Baseline median should match actual data median"
        assert baseline_stats['min'] == min(actual_costs), \
            "Baseline min should match actual data min"
        assert baseline_stats['max'] == max(actual_costs), \
            "Baseline max should match actual data max"
        assert baseline_stats['data_points'] == len(actual_costs), \
            "Baseline data points should match actual count"
        
        if len(actual_costs) > 1:
            expected_std = statistics.stdev(actual_costs)
            assert abs(baseline_stats['std_dev'] - expected_std) < 0.01, \
                "Baseline standard deviation should match actual data"
        
        # Property 3: Multiple baseline models should be evaluated
        baseline_models = baseline_analysis['baseline_models']
        assert 'moving_average' in baseline_models, \
            "Should include moving average baseline model"
        assert 'linear_trend' in baseline_models, \
            "Should include linear trend baseline model"
        assert 'percentile' in baseline_models, \
            "Should include percentile baseline model"
        
        # Property 4: Best model should be selected
        selected_model = baseline_analysis['selected_model']
        assert 'model_type' in selected_model, \
            "Selected model should have type"
        assert 'accuracy' in selected_model, \
            "Selected model should have accuracy score"
        assert 'confidence' in selected_model, \
            "Selected model should have confidence score"
        assert 'predictions' in selected_model, \
            "Selected model should have predictions"
        
        assert 0 <= selected_model['accuracy'] <= 100, \
            f"Model accuracy should be 0-100, got {selected_model['accuracy']}"
        assert 0 <= selected_model['confidence'] <= 100, \
            f"Model confidence should be 0-100, got {selected_model['confidence']}"
        assert len(selected_model['predictions']) == len(baseline_data), \
            "Model predictions should match data length"
        
        # Property 5: Baseline period should be correctly identified
        baseline_period = baseline_analysis['baseline_period']
        assert 'start_date' in baseline_period, \
            "Baseline period should have start date"
        assert 'end_date' in baseline_period, \
            "Baseline period should have end date"
        assert 'data_points' in baseline_period, \
            "Baseline period should have data point count"
        
        assert baseline_period['data_points'] == len(baseline_data), \
            "Baseline period data points should match actual count"
    
    def test_anomaly_detection_edge_cases(self):
        """
        Property: Anomaly detection should handle edge cases gracefully.
        
        This test validates behavior with edge cases like empty data, 
        insufficient data, and extreme values.
        """
        # Test with empty data
        results = self.detector.detect_anomalies([])
        assert not results['baseline_analysis']['baseline_established'], \
            "Should not establish baseline with empty data"
        assert len(results['anomalies_detected']) == 0, \
            "Should not detect anomalies with empty data"
        
        # Test with insufficient data
        insufficient_data = [
            {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cost': 100.0,
                'service': 'ec2',
                'region': 'us-east-1'
            }
        ]
        
        results = self.detector.detect_anomalies(insufficient_data)
        assert not results['baseline_analysis']['baseline_established'], \
            "Should not establish baseline with insufficient data"
        
        # Test with extreme values
        extreme_data = []
        base_time = datetime.now(timezone.utc) - timedelta(days=7)
        
        for hour in range(168):  # 1 week of hourly data
            timestamp = base_time + timedelta(hours=hour)
            # Most values are normal, but include some extreme values
            if hour == 100:
                cost = 10000.0  # Extreme spike
            elif hour == 150:
                cost = 0.0  # Zero cost
            else:
                cost = 100.0  # Normal cost
            
            extreme_data.append({
                'timestamp': timestamp.isoformat(),
                'cost': cost,
                'service': 'mixed',
                'region': 'us-east-1'
            })
        
        results = self.detector.detect_anomalies(extreme_data)
        
        # Should handle extreme values gracefully
        assert results['baseline_analysis']['baseline_established'], \
            "Should establish baseline even with extreme values"
        
        # Should detect the extreme spike
        anomalies = results['anomalies_detected']
        assert len(anomalies) > 0, \
            "Should detect extreme cost spike"
        
        # Check that extreme spike is classified as high severity
        spike_anomalies = [a for a in anomalies if a['actualCost'] > 1000]
        assert len(spike_anomalies) > 0, \
            "Should detect the extreme cost spike"
        assert spike_anomalies[0]['severity'] in ['HIGH', 'CRITICAL'], \
            "Extreme spike should be high severity"

if __name__ == '__main__':
    # Run the property tests
    pytest.main([__file__, '-v', '--tb=short'])