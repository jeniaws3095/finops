#!/usr/bin/env python3
"""
Test suite for ML Right-Sizing Engine

Tests the core functionality of ML-powered right-sizing including:
- Historical metrics collection and validation
- ML model predictions and confidence intervals
- Cost savings and performance impact assessments
- Property-based testing for ML recommendation quality
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from typing import List, Dict, Any
# import numpy as np  # Commented out for basic testing - but ML engine needs it
import numpy as np  # Required for ML right-sizing engine
import statistics

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.ml_rightsizing import MLRightSizingEngine, MLModelType, ResourceType, ConfidenceLevel, RiskLevel
from utils.aws_config import AWSConfig


class TestMLRightSizingEngine:
    """Test suite for ML right-sizing engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.aws_config = AWSConfig()
        self.engine = MLRightSizingEngine(self.aws_config, region='us-east-1')
        
        # Sample EC2 resources with sufficient historical data for ML analysis
        self.sample_ec2_resources = [
            {
                'resourceId': 'i-1234567890abcdef0',
                'resourceType': 'ec2',
                'instanceType': 't3.medium',
                'currentCost': 60.0,
                'utilizationMetrics': {
                    'cpuUtilizationHistory': [25, 30, 28, 32, 27, 29, 31, 26, 33, 28] * 20,  # 200 data points
                    'memoryUtilizationHistory': [40, 45, 42, 48, 41, 44, 46, 39, 49, 43] * 20,
                    'networkInHistory': [100, 120, 110, 130, 105, 115, 125, 95, 135, 108] * 20,
                    'networkOutHistory': [80, 90, 85, 95, 82, 88, 92, 78, 98, 86] * 20,
                    'diskReadOpsHistory': [50, 60, 55, 65, 52, 58, 62, 48, 68, 56] * 20,
                    'diskWriteOpsHistory': [30, 40, 35, 45, 32, 38, 42, 28, 48, 36] * 20,
                    'diskReadBytesHistory': [1000, 1200, 1100, 1300, 1050, 1150, 1250, 950, 1350, 1080] * 20,
                    'diskWriteBytesHistory': [800, 900, 850, 950, 820, 880, 920, 780, 980, 860] * 20,
                    'timestamps': [(datetime.now(timezone.utc) - timedelta(hours=i)).isoformat() for i in range(200, 0, -1)],
                    'dataPoints': 200
                },
                'tags': {'Environment': 'production', 'Name': 'web-server'}
            },
            {
                'resourceId': 'i-0987654321fedcba0',
                'resourceType': 'ec2',
                'instanceType': 'm5.large',
                'currentCost': 120.0,
                'utilizationMetrics': {
                    'cpuUtilizationHistory': [70, 75, 72, 78, 69, 74, 76, 68, 79, 73] * 30,  # 300 data points
                    'memoryUtilizationHistory': [80, 85, 82, 88, 79, 84, 86, 78, 89, 83] * 30,
                    'networkInHistory': [500, 520, 510, 530, 505, 515, 525, 495, 535, 508] * 30,
                    'networkOutHistory': [400, 420, 410, 430, 405, 415, 425, 395, 435, 408] * 30,
                    'diskReadOpsHistory': [200, 220, 210, 230, 205, 215, 225, 195, 235, 208] * 30,
                    'diskWriteOpsHistory': [150, 170, 160, 180, 155, 165, 175, 145, 185, 158] * 30,
                    'diskReadBytesHistory': [5000, 5200, 5100, 5300, 5050, 5150, 5250, 4950, 5350, 5080] * 30,
                    'diskWriteBytesHistory': [4000, 4200, 4100, 4300, 4050, 4150, 4250, 3950, 4350, 4080] * 30,
                    'timestamps': [(datetime.now(timezone.utc) - timedelta(hours=i)).isoformat() for i in range(300, 0, -1)],
                    'dataPoints': 300
                },
                'tags': {'Environment': 'production', 'Name': 'api-server'}
            }
        ]
        
        # Sample RDS resources with database-specific metrics
        self.sample_rds_resources = [
            {
                'resourceId': 'db-instance-1',
                'resourceType': 'rds',
                'dbInstanceClass': 'db.t3.medium',
                'currentCost': 80.0,
                'utilizationMetrics': {
                    'cpuUtilizationHistory': [35, 40, 38, 42, 36, 39, 41, 34, 43, 37] * 25,  # 250 data points
                    'memoryUtilizationHistory': [60, 65, 62, 68, 59, 64, 66, 58, 69, 63] * 25,
                    'connections_history': [20, 25, 22, 28, 21, 24, 26, 19, 29, 23] * 25,
                    'timestamps': [(datetime.now(timezone.utc) - timedelta(hours=i)).isoformat() for i in range(250, 0, -1)],
                    'dataPoints': 250
                },
                'tags': {'Environment': 'production', 'Name': 'main-database'}
            }
        ]
        
        # Sample Lambda resources with execution metrics
        self.sample_lambda_resources = [
            {
                'resourceId': 'lambda-func-1',
                'resourceType': 'lambda',
                'memorySize': 512,
                'timeout': 30,
                'currentCost': 25.0,
                'utilizationMetrics': {
                    'duration_history': [2500, 2800, 2600, 3000, 2400, 2700, 2900, 2300, 3100, 2650] * 18,  # 180 data points
                    'memory_used_history': [300, 320, 310, 340, 295, 315, 335, 290, 345, 305] * 18,
                    'timestamps': [(datetime.now(timezone.utc) - timedelta(hours=i)).isoformat() for i in range(180, 0, -1)],
                    'dataPoints': 180
                },
                'tags': {'Environment': 'production', 'Name': 'data-processor'}
            }
        ]
        
        # Sample EBS resources with I/O metrics
        self.sample_ebs_resources = [
            {
                'resourceId': 'vol-1234567890abcdef0',
                'resourceType': 'ebs',
                'volumeType': 'gp2',
                'size': 100,
                'iops': 300,
                'currentCost': 10.0,
                'utilizationMetrics': {
                    'disk_read_ops': [100, 120, 110, 130, 105, 115, 125, 95, 135, 108] * 20,  # 200 data points
                    'disk_write_ops': [80, 90, 85, 95, 82, 88, 92, 78, 98, 86] * 20,
                    'disk_read_bytes': [2000, 2200, 2100, 2300, 2050, 2150, 2250, 1950, 2350, 2080] * 20,
                    'disk_write_bytes': [1500, 1700, 1600, 1800, 1550, 1650, 1750, 1450, 1850, 1580] * 20,
                    'timestamps': [(datetime.now(timezone.utc) - timedelta(hours=i)).isoformat() for i in range(200, 0, -1)],
                    'dataPoints': 200
                },
                'tags': {'Environment': 'production', 'Name': 'app-storage'}
            }
        ]
    
    def test_engine_initialization(self):
        """Test that the ML right-sizing engine initializes correctly."""
        assert self.engine.region == 'us-east-1'
        assert self.engine.aws_config is not None
        assert 'data_requirements' in self.engine.ml_thresholds
        assert 'confidence_scoring' in self.engine.ml_thresholds
        assert 'sizing_parameters' in self.engine.ml_thresholds
        assert 'performance_impact' in self.engine.ml_thresholds
    
    def test_historical_metrics_collection(self):
        """Test collection of historical CPU, memory, network, and storage metrics."""
        resource = self.sample_ec2_resources[0]
        metrics = self.engine._collect_historical_metrics(resource)
        
        # Verify all required metrics are collected
        required_metrics = [
            'cpu_utilization', 'memory_utilization', 'network_in', 'network_out',
            'disk_read_ops', 'disk_write_ops', 'disk_read_bytes', 'disk_write_bytes',
            'timestamps', 'data_points'
        ]
        
        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"
        
        # Verify derived statistics are calculated
        assert 'cpu_avg' in metrics
        assert 'cpu_max' in metrics
        assert 'cpu_p95' in metrics
        assert 'cpu_variance' in metrics
        
        # Verify data quality
        assert metrics['data_points'] == 200
        assert len(metrics['cpu_utilization']) == 200
        assert metrics['cpu_avg'] > 0
        assert metrics['cpu_variance'] > 0
    
    def test_data_quality_validation(self):
        """Test validation of historical data quality for ML analysis."""
        # Test with sufficient data
        resource = self.sample_ec2_resources[0]
        metrics = self.engine._collect_historical_metrics(resource)
        assert self.engine._validate_data_quality(metrics) == True
        
        # Test with insufficient data points
        insufficient_resource = {
            'utilizationMetrics': {
                'cpuUtilizationHistory': [25, 30, 28],  # Only 3 data points
                'timestamps': [(datetime.now(timezone.utc) - timedelta(hours=i)).isoformat() for i in range(3, 0, -1)],
                'dataPoints': 3
            }
        }
        insufficient_metrics = self.engine._collect_historical_metrics(insufficient_resource)
        assert self.engine._validate_data_quality(insufficient_metrics) == False
        
        # Test with old data
        old_resource = {
            'utilizationMetrics': {
                'cpuUtilizationHistory': [25, 30, 28] * 60,  # 180 data points
                'timestamps': [(datetime.now(timezone.utc) - timedelta(days=100, hours=i)).isoformat() for i in range(180, 0, -1)],
                'dataPoints': 180
            }
        }
        old_metrics = self.engine._collect_historical_metrics(old_resource)
        assert self.engine._validate_data_quality(old_metrics) == False
    
    def test_ml_model_predictions(self):
        """Test ML model predictions for different resource types."""
        # Test EC2 ML predictions
        resource = self.sample_ec2_resources[0]
        metrics = self.engine._collect_historical_metrics(resource)
        predictions = self.engine._apply_ml_models_ec2(metrics, 't3.medium')
        
        assert isinstance(predictions, dict)
        # Should have multiple ML models
        assert len(predictions) > 0
        
        # Each prediction should have required structure
        for model_name, prediction in predictions.items():
            assert 'predicted_cpu_avg' in prediction
            assert 'confidence' in prediction
            assert 0 <= prediction['confidence'] <= 100
    
    def test_confidence_interval_calculation(self):
        """Test calculation of confidence intervals for ML recommendations."""
        # Create mock ML predictions
        ml_predictions = {
            'linear_regression': {'predicted_cpu_avg': 30.0, 'confidence': 85.0},
            'moving_average': {'predicted_cpu_avg': 28.0, 'confidence': 75.0},
            'seasonal': {'predicted_cpu_avg': 32.0, 'confidence': 80.0}
        }
        
        confidence_analysis = self.engine._calculate_confidence_intervals(ml_predictions)
        
        # Verify confidence analysis structure
        assert 'overall_confidence' in confidence_analysis
        assert 'confidence_level' in confidence_analysis
        assert 'confidence_interval' in confidence_analysis
        assert 'model_confidences' in confidence_analysis
        
        # Verify confidence level determination
        overall_confidence = confidence_analysis['overall_confidence']
        assert 70 <= overall_confidence <= 90  # Should be average of input confidences
        
        confidence_level = confidence_analysis['confidence_level']
        assert confidence_level in ['LOW', 'MEDIUM', 'HIGH']
        
        # Verify confidence interval
        interval = confidence_analysis['confidence_interval']
        assert 'lower' in interval
        assert 'upper' in interval
        assert interval['lower'] >= 0
        assert interval['upper'] > interval['lower']
    
    def test_cost_savings_estimation(self):
        """Test estimation of cost savings for right-sizing recommendations."""
        # Test EC2 cost impact calculation
        cost_analysis = self.engine._calculate_ec2_cost_impact('t3.medium', 't3.small', 60.0)
        
        assert 'current_cost' in cost_analysis
        assert 'projected_cost' in cost_analysis
        assert 'monthly_savings' in cost_analysis
        assert 'annual_savings' in cost_analysis
        assert 'savings_percentage' in cost_analysis
        
        # Verify calculations are logical
        assert cost_analysis['current_cost'] > 0
        assert cost_analysis['projected_cost'] >= 0
        assert cost_analysis['annual_savings'] == cost_analysis['monthly_savings'] * 12
        
        if cost_analysis['current_cost'] > 0:
            expected_pct = (cost_analysis['monthly_savings'] / cost_analysis['current_cost']) * 100
            assert abs(expected_pct - cost_analysis['savings_percentage']) < 0.01
    
    def test_performance_impact_assessment(self):
        """Test assessment of performance impact for right-sizing changes."""
        resource = self.sample_ec2_resources[0]
        metrics = self.engine._collect_historical_metrics(resource)
        
        # Test performance impact assessment
        performance_impact = self.engine._assess_ec2_performance_impact(metrics, 't3.medium', 't3.small')
        
        assert 'impact_level' in performance_impact
        assert 'impact_description' in performance_impact
        assert 'current_cpu_avg' in performance_impact
        assert 'current_cpu_max' in performance_impact
        assert 'performance_headroom' in performance_impact
        
        # Verify impact level is valid
        impact_level = performance_impact['impact_level']
        assert impact_level in ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'POSITIVE']
    
    def test_ml_recommendation_creation(self):
        """Test creation of complete ML recommendations."""
        # Analyze EC2 resources
        result = self.engine.analyze_rightsizing_opportunities(self.sample_ec2_resources)
        
        assert 'summary' in result
        assert 'recommendations' in result
        
        recommendations = result['recommendations']
        
        if recommendations:
            rec = recommendations[0]
            
            # Verify complete recommendation structure
            required_fields = [
                'recommendationId', 'resourceId', 'resourceType', 'recommendationType',
                'title', 'description', 'currentConfiguration', 'recommendedConfiguration',
                'costAnalysis', 'performanceImpact', 'confidenceAnalysis',
                'estimatedMonthlySavings', 'estimatedAnnualSavings', 'savingsPercentage',
                'confidenceLevel', 'riskLevel', 'implementationEffort',
                'mlDetails', 'recommendedAction', 'rollbackCapability',
                'validationRequired', 'timestamp', 'region', 'resourceData'
            ]
            
            for field in required_fields:
                assert field in rec, f"Missing field: {field}"
            
            # Verify ML-specific details
            ml_details = rec['mlDetails']
            assert 'modelsUsed' in ml_details
            assert 'predictions' in ml_details
            assert 'optimalConfig' in ml_details
            
            # Verify confidence analysis
            confidence_analysis = rec['confidenceAnalysis']
            assert 'overall_confidence' in confidence_analysis
            assert 'confidence_level' in confidence_analysis
            assert 'confidence_interval' in confidence_analysis


# Property-Based Testing for ML Right-Sizing

# Strategy for generating valid resource data with sufficient historical metrics
@st.composite
def ml_resource_with_history(draw):
    """Generate realistic resource data with sufficient historical metrics for ML analysis."""
    resource_type = draw(st.sampled_from(['ec2', 'rds', 'lambda', 'ebs']))
    
    # Generate sufficient data points for ML analysis (minimum 168 for 1 week)
    data_points = draw(st.integers(min_value=168, max_value=200))  # 1 week to ~8 days of hourly data
    current_cost = draw(st.floats(min_value=20.0, max_value=500.0))
    
    # Generate realistic base utilization values
    base_cpu = draw(st.floats(min_value=10.0, max_value=80.0))
    base_memory = draw(st.floats(min_value=20.0, max_value=90.0))
    
    # Generate historical data with realistic patterns and variance
    cpu_variance = draw(st.floats(min_value=5.0, max_value=15.0))
    memory_variance = draw(st.floats(min_value=5.0, max_value=15.0))
    
    # Create time series data with some trend and seasonality
    cpu_history = []
    memory_history = []
    network_in_history = []
    network_out_history = []
    disk_read_ops = []
    disk_write_ops = []
    disk_read_bytes = []
    disk_write_bytes = []
    
    for i in range(data_points):
        # Add some seasonal pattern (daily cycle) - simplified without numpy
        seasonal_factor = 1 + 0.2 * (0.5 if (i % 24) < 12 else -0.5)  # Simple day/night pattern
        
        # Add some random variance
        cpu_val = max(1, min(95, base_cpu * seasonal_factor + draw(st.floats(min_value=-cpu_variance, max_value=cpu_variance))))
        memory_val = max(5, min(95, base_memory * seasonal_factor + draw(st.floats(min_value=-memory_variance, max_value=memory_variance))))
        
        cpu_history.append(cpu_val)
        memory_history.append(memory_val)
        
        # Network and disk metrics correlated with CPU usage
        network_in_history.append(max(10, cpu_val * draw(st.floats(min_value=2.0, max_value=8.0))))
        network_out_history.append(max(5, cpu_val * draw(st.floats(min_value=1.0, max_value=4.0))))
        disk_read_ops.append(max(1, cpu_val * draw(st.floats(min_value=0.5, max_value=2.0))))
        disk_write_ops.append(max(1, cpu_val * draw(st.floats(min_value=0.3, max_value=1.5))))
        disk_read_bytes.append(max(100, cpu_val * draw(st.floats(min_value=10.0, max_value=50.0))))
        disk_write_bytes.append(max(50, cpu_val * draw(st.floats(min_value=5.0, max_value=30.0))))
    
    # Generate timestamps
    timestamps = [(datetime.now(timezone.utc) - timedelta(hours=i)).isoformat() for i in range(data_points, 0, -1)]
    
    # Resource-specific configurations
    if resource_type == 'ec2':
        instance_type = draw(st.sampled_from(['t3.micro', 't3.small', 't3.medium', 't3.large', 'm5.large', 'm5.xlarge', 'c5.large']))
        resource_config = {'instanceType': instance_type}
    elif resource_type == 'rds':
        db_instance_class = draw(st.sampled_from(['db.t3.micro', 'db.t3.small', 'db.t3.medium', 'db.t3.large', 'db.m5.large']))
        resource_config = {'dbInstanceClass': db_instance_class}
        # Add database-specific metrics
        connections_history = [max(1, int(cpu_val * 0.5)) for cpu_val in cpu_history]
    elif resource_type == 'lambda':
        memory_size = draw(st.sampled_from([128, 256, 512, 1024, 2048, 3008]))
        timeout = draw(st.integers(min_value=3, max_value=900))
        resource_config = {'memorySize': memory_size, 'timeout': timeout}
        # Add Lambda-specific metrics
        duration_history = [max(100, min(timeout * 1000 - 100, memory_val * 30)) for memory_val in memory_history]
        memory_used_history = [max(64, min(memory_size - 10, memory_val * memory_size / 100)) for memory_val in memory_history]
    elif resource_type == 'ebs':
        volume_type = draw(st.sampled_from(['gp2', 'gp3', 'io1', 'io2', 'st1', 'sc1']))
        size = draw(st.integers(min_value=20, max_value=1000))
        iops = draw(st.integers(min_value=100, max_value=16000))
        resource_config = {'volumeType': volume_type, 'size': size, 'iops': iops}
    
    # Build utilization metrics
    utilization_metrics = {
        'cpuUtilizationHistory': cpu_history,
        'memoryUtilizationHistory': memory_history,
        'networkInHistory': network_in_history,
        'networkOutHistory': network_out_history,
        'diskReadOpsHistory': disk_read_ops,
        'diskWriteOpsHistory': disk_write_ops,
        'diskReadBytesHistory': disk_read_bytes,
        'diskWriteBytesHistory': disk_write_bytes,
        'timestamps': timestamps,
        'dataPoints': data_points
    }
    
    # Add resource-specific metrics
    if resource_type == 'rds':
        utilization_metrics['connections_history'] = connections_history
    elif resource_type == 'lambda':
        utilization_metrics['duration_history'] = duration_history
        utilization_metrics['memory_used_history'] = memory_used_history
    
    # Generate resource ID and tags
    resource_id = f'{resource_type}-{draw(st.text(min_size=8, max_size=12, alphabet="abcdef0123456789"))}'
    environment = draw(st.sampled_from(['production', 'staging', 'dev', 'test']))
    name = draw(st.sampled_from(['web-server', 'api-server', 'database', 'cache', 'worker', 'analytics']))
    
    resource = {
        'resourceId': resource_id,
        'resourceType': resource_type,
        'currentCost': current_cost,
        'utilizationMetrics': utilization_metrics,
        'tags': {
            'Environment': environment,
            'Name': name
        }
    }
    
    # Add resource-specific configuration
    resource.update(resource_config)
    
    return resource


class TestMLRightSizingProperties:
    """Property-based tests for ML right-sizing engine."""
    
    def setup_method(self):
        """Set up test fixtures for property tests."""
        self.aws_config = AWSConfig()
        self.engine = MLRightSizingEngine(self.aws_config, region='us-east-1')
    
    @given(st.lists(ml_resource_with_history(), min_size=1, max_size=2))
    @settings(max_examples=5, deadline=60000, suppress_health_check=[HealthCheck.large_base_example, HealthCheck.data_too_large])  # 60 second deadline for complex ML operations
    def test_property_ml_recommendation_quality(self, resources: List[Dict[str, Any]]):
        """
        **Feature: advanced-finops-platform, Property 7: ML Recommendation Quality**
        **Validates: Requirements 3.2, 3.3**
        
        For any resource with sufficient historical data, the ML right-sizing engine should 
        generate recommendations with confidence intervals, cost savings estimates, and 
        performance impact assessments.
        """
        # Ensure we have valid resources with sufficient data
        assume(len(resources) > 0)
        assume(all(r.get('currentCost', 0) > 0 for r in resources))
        assume(all(r.get('utilizationMetrics', {}).get('dataPoints', 0) >= 168 for r in resources))
        
        # Execute ML right-sizing analysis
        result = self.engine.analyze_rightsizing_opportunities(resources)
        
        # Property 1: Analysis result must be complete and well-structured
        assert isinstance(result, dict), "ML analysis result must be a dictionary"
        
        required_keys = [
            'summary', 'recommendations', 'mlModelsUsed', 'analysisTimestamp',
            'region', 'confidenceDistribution'
        ]
        
        for key in required_keys:
            assert key in result, f"ML analysis result must contain '{key}'"
        
        # Property 2: Summary must accurately reflect the ML analysis
        summary = result['summary']
        
        summary_fields = [
            'totalResources', 'analyzedResources', 'recommendationsGenerated',
            'totalPotentialSavings', 'highConfidenceRecommendations',
            'mediumConfidenceRecommendations', 'lowConfidenceRecommendations'
        ]
        
        for field in summary_fields:
            assert field in summary, f"Summary must contain '{field}'"
        
        # Verify summary calculations
        assert summary['totalResources'] == len(resources)
        assert summary['analyzedResources'] <= len(resources)
        assert summary['totalPotentialSavings'] >= 0
        
        # Confidence distribution should sum to total recommendations
        confidence_dist = result['confidenceDistribution']
        total_confidence_recs = confidence_dist['high'] + confidence_dist['medium'] + confidence_dist['low']
        assert total_confidence_recs == summary['recommendationsGenerated']
        
        # Property 3: All ML recommendations must have confidence intervals
        # (Validates Requirement 3.2: Generate ML-powered size recommendations with confidence intervals)
        recommendations = result['recommendations']
        
        for recommendation in recommendations:
            # Each recommendation must have confidence analysis with intervals
            assert 'confidenceAnalysis' in recommendation, "ML recommendation must have confidence analysis"
            
            confidence_analysis = recommendation['confidenceAnalysis']
            required_confidence_fields = [
                'overall_confidence', 'confidence_level', 'confidence_interval', 'model_confidences'
            ]
            
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
            
            # Model confidences must be present and valid
            model_confidences = confidence_analysis['model_confidences']
            assert isinstance(model_confidences, dict), "Model confidences must be a dictionary"
            assert len(model_confidences) > 0, "Must have at least one ML model confidence"
            
            for model_name, confidence in model_confidences.items():
                assert 0 <= confidence <= 100, f"Model confidence for {model_name} must be 0-100%, got {confidence}"
        
        # Property 4: All ML recommendations must have cost savings estimates
        # (Validates Requirement 3.3: Estimate cost savings and performance impact)
        for recommendation in recommendations:
            # Each recommendation must have cost analysis
            assert 'costAnalysis' in recommendation, "ML recommendation must have cost analysis"
            
            cost_analysis = recommendation['costAnalysis']
            required_cost_fields = [
                'current_cost', 'projected_cost', 'monthly_savings', 
                'annual_savings', 'savings_percentage'
            ]
            
            for field in required_cost_fields:
                assert field in cost_analysis, f"Cost analysis must contain '{field}'"
            
            # Cost values must be logical
            current_cost = cost_analysis['current_cost']
            projected_cost = cost_analysis['projected_cost']
            monthly_savings = cost_analysis['monthly_savings']
            annual_savings = cost_analysis['annual_savings']
            savings_percentage = cost_analysis['savings_percentage']
            
            assert current_cost >= 0, "Current cost must be non-negative"
            assert projected_cost >= 0, "Projected cost must be non-negative"
            assert annual_savings == monthly_savings * 12, "Annual savings must equal monthly savings * 12"
            
            # Savings calculation must be consistent
            expected_savings = current_cost - projected_cost
            assert abs(expected_savings - monthly_savings) < 0.01, "Savings calculation must be consistent"
            
            # Savings percentage must be calculated correctly
            if current_cost > 0:
                expected_pct = (monthly_savings / current_cost) * 100
                assert abs(expected_pct - savings_percentage) < 0.01, "Savings percentage must be calculated correctly"
            
            # Recommendation-level savings fields must match cost analysis
            assert recommendation['estimatedMonthlySavings'] == monthly_savings
            assert recommendation['estimatedAnnualSavings'] == annual_savings
            assert recommendation['savingsPercentage'] == savings_percentage
        
        # Property 5: All ML recommendations must have performance impact assessments
        # (Validates Requirement 3.3: Estimate performance impact)
        for recommendation in recommendations:
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
            
            # Impact description must be meaningful
            impact_description = performance_impact['impact_description']
            assert isinstance(impact_description, str), "Impact description must be a string"
            assert len(impact_description) > 0, "Impact description must not be empty"
        
        # Property 6: All ML recommendations must include ML-specific details
        for recommendation in recommendations:
            # Each recommendation must have ML details
            assert 'mlDetails' in recommendation, "ML recommendation must have ML details"
            
            ml_details = recommendation['mlDetails']
            required_ml_fields = ['modelsUsed', 'predictions', 'optimalConfig']
            
            for field in required_ml_fields:
                assert field in ml_details, f"ML details must contain '{field}'"
            
            # Models used must be a list of valid ML models
            models_used = ml_details['modelsUsed']
            assert isinstance(models_used, list), "Models used must be a list"
            assert len(models_used) > 0, "Must use at least one ML model"
            
            # Predictions must be a dictionary with model results
            predictions = ml_details['predictions']
            assert isinstance(predictions, dict), "Predictions must be a dictionary"
            assert len(predictions) > 0, "Must have at least one prediction"
            
            # Each prediction must have required structure
            for model_name, prediction in predictions.items():
                assert 'confidence' in prediction, f"Prediction for {model_name} must have confidence"
                confidence = prediction['confidence']
                assert 0 <= confidence <= 100, f"Prediction confidence must be 0-100%, got {confidence}"
            
            # Optimal config must be present and appropriate for resource type
            optimal_config = ml_details['optimalConfig']
            assert isinstance(optimal_config, dict), "Optimal config must be a dictionary"
            assert len(optimal_config) > 0, "Optimal config must not be empty"
            
            resource_type = recommendation['resourceType']
            if resource_type == 'ec2':
                assert 'instance_type' in optimal_config, "EC2 optimal config must have instance_type"
            elif resource_type == 'rds':
                assert 'instance_class' in optimal_config, "RDS optimal config must have instance_class"
            elif resource_type == 'lambda':
                assert 'memory_size' in optimal_config, "Lambda optimal config must have memory_size"
                assert 'timeout' in optimal_config, "Lambda optimal config must have timeout"
            elif resource_type == 'ebs':
                assert 'volume_type' in optimal_config, "EBS optimal config must have volume_type"
        
        # Property 7: Recommendations must be properly prioritized by confidence and savings
        if len(recommendations) > 1:
            for i in range(len(recommendations) - 1):
                current_rec = recommendations[i]
                next_rec = recommendations[i + 1]
                
                # Calculate priority scores (confidence * 0.6 + normalized_savings * 0.4)
                current_confidence = current_rec['confidenceAnalysis']['overall_confidence']
                current_savings = current_rec['estimatedMonthlySavings']
                current_priority = (current_confidence * 0.6) + (min(100, (current_savings / 10) * 100) * 0.4)
                
                next_confidence = next_rec['confidenceAnalysis']['overall_confidence']
                next_savings = next_rec['estimatedMonthlySavings']
                next_priority = (next_confidence * 0.6) + (min(100, (next_savings / 10) * 100) * 0.4)
                
                # Current recommendation should have higher or equal priority
                assert current_priority >= next_priority - 1.0, "Recommendations should be prioritized by confidence and savings"
        
        # Property 8: ML models used must be appropriate and documented
        ml_models_used = result['mlModelsUsed']
        assert isinstance(ml_models_used, list), "ML models used must be a list"
        
        # Should use multiple ML models for robust predictions
        if recommendations:
            assert len(ml_models_used) > 0, "Should use at least one ML model when generating recommendations"
        
        # Property 9: Rollback capability must be enabled for all ML recommendations
        for recommendation in recommendations:
            assert recommendation.get('rollbackCapability', False) == True, "ML recommendations must have rollback capability"
            assert recommendation.get('validationRequired', False) == True, "ML recommendations must require validation"
        
        # Property 10: Risk levels must be appropriate for ML recommendations
        for recommendation in recommendations:
            risk_level = recommendation['riskLevel']
            confidence_level = recommendation['confidenceLevel']
            performance_impact = recommendation['performanceImpact']['impact_level']
            
            # High performance impact should result in higher risk
            if performance_impact == 'HIGH':
                assert risk_level in ['HIGH', 'CRITICAL'], "High performance impact should result in high risk"
            
            # Low confidence should result in higher risk
            if confidence_level == 'LOW':
                assert risk_level in ['MEDIUM', 'HIGH'], "Low confidence should result in medium or high risk"


if __name__ == '__main__':
    # Run basic functionality tests
    test_suite = TestMLRightSizingEngine()
    test_suite.setup_method()
    
    print("Testing ML Right-Sizing Engine...")
    
    try:
        test_suite.test_engine_initialization()
        print("✓ Engine initialization test passed")
        
        test_suite.test_historical_metrics_collection()
        print("✓ Historical metrics collection test passed")
        
        test_suite.test_data_quality_validation()
        print("✓ Data quality validation test passed")
        
        test_suite.test_ml_model_predictions()
        print("✓ ML model predictions test passed")
        
        test_suite.test_confidence_interval_calculation()
        print("✓ Confidence interval calculation test passed")
        
        test_suite.test_cost_savings_estimation()
        print("✓ Cost savings estimation test passed")
        
        test_suite.test_performance_impact_assessment()
        print("✓ Performance impact assessment test passed")
        
        test_suite.test_ml_recommendation_creation()
        print("✓ ML recommendation creation test passed")
        
        print("\n✅ All unit tests passed!")
        
        # Run property-based tests
        print("\nRunning property-based tests...")
        property_test_suite = TestMLRightSizingProperties()
        property_test_suite.setup_method()
        
        # Run a few examples of the property test manually for demonstration
        from hypothesis import strategies as st
        
        # Generate a test case manually for demonstration
        test_resources = [
            {
                'resourceId': 'i-ml-test123',
                'resourceType': 'ec2',
                'instanceType': 't3.medium',
                'currentCost': 60.0,
                'utilizationMetrics': {
                    'cpuUtilizationHistory': [25, 30, 28, 32, 27, 29, 31, 26, 33, 28] * 20,  # 200 data points
                    'memoryUtilizationHistory': [40, 45, 42, 48, 41, 44, 46, 39, 49, 43] * 20,
                    'networkInHistory': [100, 120, 110, 130, 105, 115, 125, 95, 135, 108] * 20,
                    'networkOutHistory': [80, 90, 85, 95, 82, 88, 92, 78, 98, 86] * 20,
                    'diskReadOpsHistory': [50, 60, 55, 65, 52, 58, 62, 48, 68, 56] * 20,
                    'diskWriteOpsHistory': [30, 40, 35, 45, 32, 38, 42, 28, 48, 36] * 20,
                    'diskReadBytesHistory': [1000, 1200, 1100, 1300, 1050, 1150, 1250, 950, 1350, 1080] * 20,
                    'diskWriteBytesHistory': [800, 900, 850, 950, 820, 880, 920, 780, 980, 860] * 20,
                    'timestamps': [(datetime.now(timezone.utc) - timedelta(hours=i)).isoformat() for i in range(200, 0, -1)],
                    'dataPoints': 200
                },
                'tags': {'Environment': 'production', 'Name': 'web-server'}
            }
        ]
        
        property_test_suite.test_property_ml_recommendation_quality(test_resources)
        print("✓ Property test for ML recommendation quality passed")
        
        print("\n✅ All ML Right-Sizing Engine tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()