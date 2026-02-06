#!/usr/bin/env python3
"""
Unit Tests for Anomaly Detector

Tests the core functionality of the anomaly detection engine including:
- Baseline pattern establishment
- Anomaly detection with configurable thresholds
- Root cause analysis
- Alert generation
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the Python path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.anomaly_detector import AnomalyDetector, AnomalyType, AnomalySeverity, BaselineModel
from utils.aws_config import AWSConfig


class TestAnomalyDetector(unittest.TestCase):
    """Test cases for the AnomalyDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock AWS config
        self.mock_aws_config = Mock(spec=AWSConfig)
        self.detector = AnomalyDetector(self.mock_aws_config, region='us-east-1')
        
        # Create sample cost data
        self.sample_cost_data = self._create_sample_cost_data()
        self.sample_resources = self._create_sample_resources()
    
    def _create_sample_cost_data(self):
        """Create sample cost data for testing."""
        base_time = datetime.utcnow() - timedelta(days=30)
        cost_data = []
        
        # Generate 30 days of hourly cost data with normal pattern
        for day in range(30):
            for hour in range(24):
                timestamp = base_time + timedelta(days=day, hours=hour)
                
                # Normal cost pattern with some variation
                base_cost = 100.0
                hourly_variation = 10.0 if 9 <= hour <= 17 else 5.0  # Higher during business hours
                daily_variation = 5.0 if day % 7 < 5 else 2.0  # Higher on weekdays
                
                cost = base_cost + hourly_variation + daily_variation
                
                # Add some anomalies for testing
                if day == 25 and hour == 14:  # Cost spike
                    cost = 300.0
                elif day == 28 and 10 <= hour <= 16:  # Sustained increase
                    cost = 200.0
                
                cost_data.append({
                    'timestamp': timestamp.isoformat(),
                    'cost': cost,
                    'service': 'ec2',
                    'region': 'us-east-1'
                })
        
        return cost_data
    
    def _create_sample_resources(self):
        """Create sample resource data for testing."""
        return [
            {
                'resourceId': 'i-1234567890abcdef0',
                'resourceType': 'ec2',
                'region': 'us-east-1',
                'currentCost': 150.0,
                'historicalAverageCost': 100.0,
                'tags': {'Environment': 'production', 'Team': 'backend'}
            },
            {
                'resourceId': 'db-abcdef1234567890',
                'resourceType': 'rds',
                'region': 'us-east-1',
                'currentCost': 80.0,
                'historicalAverageCost': 75.0,
                'tags': {'Environment': 'production', 'Team': 'data'}
            },
            {
                'resourceId': 'lambda-function-1',
                'resourceType': 'lambda',
                'region': 'us-east-1',
                'currentCost': 20.0,
                'historicalAverageCost': 15.0,
                'tags': {'Environment': 'production', 'Team': 'api'}
            }
        ]
    
    def test_initialization(self):
        """Test anomaly detector initialization."""
        self.assertEqual(self.detector.region, 'us-east-1')
        self.assertIsNotNone(self.detector.detection_thresholds)
        self.assertIn('baseline_requirements', self.detector.detection_thresholds)
        self.assertIn('anomaly_thresholds', self.detector.detection_thresholds)
    
    def test_baseline_establishment_sufficient_data(self):
        """Test baseline establishment with sufficient data."""
        result = self.detector.detect_anomalies(self.sample_cost_data)
        
        self.assertTrue(result['baseline_analysis']['baseline_established'])
        self.assertIn('baseline_statistics', result['baseline_analysis'])
        self.assertIn('baseline_models', result['baseline_analysis'])
        self.assertIn('selected_model', result['baseline_analysis'])
    
    def test_baseline_establishment_insufficient_data(self):
        """Test baseline establishment with insufficient data."""
        # Create minimal cost data
        minimal_data = self.sample_cost_data[:5]  # Only 5 data points
        
        result = self.detector.detect_anomalies(minimal_data)
        
        self.assertFalse(result['baseline_analysis']['baseline_established'])
        self.assertIn('error', result)
    
    def test_anomaly_detection_cost_spike(self):
        """Test detection of cost spike anomalies."""
        result = self.detector.detect_anomalies(self.sample_cost_data, self.sample_resources)
        
        # Should detect the cost spike we injected
        anomalies = result['anomalies_detected']
        self.assertGreater(len(anomalies), 0)
        
        # Check for cost spike anomaly
        spike_anomalies = [a for a in anomalies if a['anomalyType'] == AnomalyType.COST_SPIKE.value]
        self.assertGreater(len(spike_anomalies), 0)
        
        # Verify anomaly structure
        spike_anomaly = spike_anomalies[0]
        self.assertIn('anomalyId', spike_anomaly)
        self.assertIn('actualCost', spike_anomaly)
        self.assertIn('expectedCost', spike_anomaly)
        self.assertIn('deviationPercentage', spike_anomaly)
        self.assertIn('severity', spike_anomaly)
    
    def test_root_cause_analysis(self):
        """Test root cause analysis for detected anomalies."""
        result = self.detector.detect_anomalies(self.sample_cost_data, self.sample_resources)
        
        anomalies = result['anomalies_detected']
        if anomalies:
            anomaly = anomalies[0]
            self.assertIn('rootCauseAnalysis', anomaly)
            
            root_cause = anomaly['rootCauseAnalysis']
            self.assertIn('contributingFactors', root_cause)
            self.assertIn('serviceBreakdown', root_cause)
            self.assertIn('resourceBreakdown', root_cause)
            self.assertIn('recommendations', root_cause)
    
    def test_alert_generation(self):
        """Test alert generation for significant anomalies."""
        result = self.detector.detect_anomalies(self.sample_cost_data, self.sample_resources)
        
        alerts = result['alerts_generated']
        
        # Should generate alerts for medium+ severity anomalies
        if result['anomalies_detected']:
            medium_plus_anomalies = [
                a for a in result['anomalies_detected'] 
                if a['severity'] in ['MEDIUM', 'HIGH', 'CRITICAL']
            ]
            
            if medium_plus_anomalies:
                self.assertGreater(len(alerts), 0)
                
                alert = alerts[0]
                self.assertIn('alertId', alert)
                self.assertIn('severity', alert)
                self.assertIn('title', alert)
                self.assertIn('description', alert)
                self.assertIn('recommendations', alert)
    
    def test_baseline_statistics_calculation(self):
        """Test baseline statistics calculation."""
        costs = [100.0, 110.0, 95.0, 105.0, 120.0, 90.0, 115.0]
        stats = self.detector._calculate_baseline_statistics(costs)
        
        self.assertIn('mean', stats)
        self.assertIn('median', stats)
        self.assertIn('std_dev', stats)
        self.assertIn('min', stats)
        self.assertIn('max', stats)
        self.assertEqual(stats['data_points'], len(costs))
        self.assertAlmostEqual(stats['mean'], sum(costs) / len(costs), places=2)
    
    def test_moving_average_baseline(self):
        """Test moving average baseline calculation."""
        costs = [100.0, 110.0, 95.0, 105.0, 120.0, 90.0, 115.0, 100.0]
        baseline = self.detector._calculate_moving_average_baseline(costs, window=3)
        
        self.assertEqual(baseline['model_type'], BaselineModel.MOVING_AVERAGE.value)
        self.assertEqual(baseline['window_size'], 3)
        self.assertIn('predictions', baseline)
        self.assertIn('accuracy', baseline)
        self.assertIn('confidence', baseline)
        self.assertEqual(len(baseline['predictions']), len(costs))
    
    def test_linear_trend_baseline(self):
        """Test linear trend baseline calculation."""
        costs = [100.0, 102.0, 104.0, 106.0, 108.0, 110.0]
        timestamps = [
            (datetime.utcnow() - timedelta(hours=i)).isoformat() 
            for i in range(len(costs))
        ]
        
        baseline = self.detector._calculate_linear_trend_baseline(costs, timestamps)
        
        self.assertEqual(baseline['model_type'], BaselineModel.LINEAR_TREND.value)
        self.assertIn('slope', baseline)
        self.assertIn('intercept', baseline)
        self.assertIn('predictions', baseline)
        self.assertGreater(baseline['slope'], 0)  # Should detect upward trend
    
    def test_percentile_baseline(self):
        """Test percentile-based baseline calculation."""
        costs = [90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0]
        baseline = self.detector._calculate_percentile_baseline(costs)
        
        self.assertEqual(baseline['model_type'], BaselineModel.PERCENTILE_BASED.value)
        self.assertIn('percentiles', baseline)
        self.assertIn('predictions', baseline)
        
        percentiles = baseline['percentiles']
        self.assertIn('p50', percentiles)
        self.assertIn('p25', percentiles)
        self.assertIn('p75', percentiles)
    
    def test_model_accuracy_calculation(self):
        """Test model accuracy calculation."""
        actual = [100.0, 110.0, 95.0, 105.0, 120.0]
        predicted = [98.0, 112.0, 93.0, 107.0, 118.0]
        
        accuracy = self.detector._calculate_model_accuracy(actual, predicted)
        
        self.assertGreaterEqual(accuracy, 0.0)
        self.assertLessEqual(accuracy, 100.0)
        self.assertGreater(accuracy, 80.0)  # Should be reasonably accurate
    
    def test_model_confidence_calculation(self):
        """Test model confidence calculation."""
        actual = [100.0, 110.0, 95.0, 105.0, 120.0]
        predicted = [98.0, 112.0, 93.0, 107.0, 118.0]
        
        confidence = self.detector._calculate_model_confidence(actual, predicted)
        
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 100.0)
        self.assertGreater(confidence, 80.0)  # Should be reasonably confident
    
    def test_data_quality_validation_sufficient(self):
        """Test data quality validation with sufficient data."""
        quality = self.detector._validate_baseline_data_quality(self.sample_cost_data)
        
        self.assertTrue(quality['sufficient_data'])
        self.assertGreater(quality['data_points'], 24)
        self.assertGreater(quality['completeness_ratio'], 0.8)
    
    def test_data_quality_validation_insufficient(self):
        """Test data quality validation with insufficient data."""
        # Test with too few data points
        minimal_data = self.sample_cost_data[:5]
        quality = self.detector._validate_baseline_data_quality(minimal_data)
        
        self.assertFalse(quality['sufficient_data'])
        self.assertIn('reason', quality)
    
    def test_service_contribution_analysis(self):
        """Test service-level contribution analysis."""
        anomaly_timestamp = datetime.utcnow().isoformat()
        thresholds = self.detector.detection_thresholds['root_cause_analysis']
        
        analysis = self.detector._analyze_service_contributions(
            anomaly_timestamp, self.sample_resources, thresholds
        )
        
        self.assertIn('ec2', analysis)
        self.assertIn('rds', analysis)
        self.assertIn('lambda', analysis)
        
        # Check structure of service analysis
        ec2_analysis = analysis['ec2']
        self.assertIn('cost_increase', ec2_analysis)
        self.assertIn('resource_count', ec2_analysis)
        self.assertIn('contribution_percentage', ec2_analysis)
    
    def test_resource_contribution_analysis(self):
        """Test resource-level contribution analysis."""
        anomaly_timestamp = datetime.utcnow().isoformat()
        thresholds = self.detector.detection_thresholds['root_cause_analysis']
        
        analysis = self.detector._analyze_resource_contributions(
            anomaly_timestamp, self.sample_resources, thresholds
        )
        
        # Should have analysis for each resource
        self.assertEqual(len(analysis), len(self.sample_resources))
        
        # Check structure of resource analysis
        for resource in self.sample_resources:
            resource_id = resource['resourceId']
            self.assertIn(resource_id, analysis)
            
            resource_analysis = analysis[resource_id]
            self.assertIn('resource_type', resource_analysis)
            self.assertIn('cost_increase', resource_analysis)
            self.assertIn('contribution_percentage', resource_analysis)
    
    def test_trend_anomaly_detection(self):
        """Test trend anomaly detection."""
        # Create data points with increasing trend
        base_time = datetime.utcnow()
        recent_points = []
        
        for i in range(5):
            recent_points.append({
                'timestamp': (base_time + timedelta(hours=i)).isoformat(),
                'cost': 100.0 + (i * 20.0)  # Increasing trend
            })
        
        baseline_stats = {'mean': 100.0, 'std_dev': 10.0}
        
        trend_result = self.detector._detect_trend_anomaly(recent_points, baseline_stats)
        
        self.assertTrue(trend_result['is_anomaly'])
        self.assertIn('severity', trend_result)
        self.assertIn('trend_slope', trend_result)
        self.assertEqual(trend_result['trend_direction'], 'increasing')
    
    def test_time_window_analysis(self):
        """Test time window pattern analysis."""
        anomaly_timestamp = datetime.utcnow().isoformat()
        
        analysis = self.detector._analyze_time_window_patterns(
            anomaly_timestamp, self.sample_cost_data, window_hours=24
        )
        
        self.assertIn('window_start', analysis)
        self.assertIn('window_end', analysis)
        self.assertIn('data_points', analysis)
        self.assertIn('cost_statistics', analysis)
        self.assertIn('cost_trend', analysis)
        
        # Check cost statistics structure
        cost_stats = analysis['cost_statistics']
        self.assertIn('mean', cost_stats)
        self.assertIn('median', cost_stats)
        self.assertIn('std_dev', cost_stats)
    
    def test_detection_summary_generation(self):
        """Test detection summary generation."""
        # Create sample anomalies
        anomalies = [
            {
                'severity': 'HIGH',
                'anomalyType': 'cost_spike',
                'actualCost': 200.0,
                'expectedCost': 100.0
            },
            {
                'severity': 'MEDIUM',
                'anomalyType': 'cost_trend',
                'actualCost': 150.0,
                'expectedCost': 100.0
            }
        ]
        
        summary = self.detector._generate_detection_summary(anomalies)
        
        self.assertEqual(summary['total_anomalies'], 2)
        self.assertIn('severity_breakdown', summary)
        self.assertIn('type_breakdown', summary)
        self.assertIn('total_cost_impact', summary)
        
        # Check severity breakdown
        self.assertEqual(summary['severity_breakdown']['HIGH'], 1)
        self.assertEqual(summary['severity_breakdown']['MEDIUM'], 1)
        
        # Check type breakdown
        self.assertEqual(summary['type_breakdown']['cost_spike'], 1)
        self.assertEqual(summary['type_breakdown']['cost_trend'], 1)
    
    def test_empty_cost_data_handling(self):
        """Test handling of empty cost data."""
        result = self.detector.detect_anomalies([])
        
        self.assertFalse(result['baseline_analysis']['baseline_established'])
        self.assertIn('error', result)
        self.assertEqual(len(result['anomalies_detected']), 0)
    
    def test_baseline_model_selection(self):
        """Test baseline model selection logic."""
        # Create mock baseline models with different accuracies
        baseline_models = {
            'moving_average': {'accuracy': 85.0, 'confidence': 80.0},
            'linear_trend': {'accuracy': 90.0, 'confidence': 75.0},
            'percentile': {'accuracy': 70.0, 'confidence': 85.0}
        }
        
        costs = [100.0, 110.0, 95.0, 105.0]
        best_model = self.detector._select_best_baseline_model(baseline_models, costs)
        
        self.assertIn('model_name', best_model)
        self.assertIn('score', best_model)
        # Should select linear_trend as it has highest weighted score
        self.assertEqual(best_model['model_name'], 'linear_trend')


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)