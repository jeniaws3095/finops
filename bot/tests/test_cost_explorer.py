#!/usr/bin/env python3
"""
Unit tests for Cost Explorer integration.

Tests the AWS Cost Explorer integration functionality including:
- Historical cost analysis
- Cost and usage report generation
- Cost trend analysis and forecasting
- Cost anomaly detection integration

Requirements: 10.1, 5.1
"""

import unittest
import sys
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from aws.cost_explorer import CostExplorer, CostMetric, Granularity, DimensionKey, create_cost_explorer


class TestCostExplorer(unittest.TestCase):
    """Test cases for Cost Explorer integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cost_explorer = create_cost_explorer(dry_run=True)
        self.start_date = datetime.now(timezone.utc) - timedelta(days=30)
        self.end_date = datetime.now(timezone.utc)
    
    def test_cost_explorer_initialization(self):
        """Test Cost Explorer initialization."""
        self.assertIsInstance(self.cost_explorer, CostExplorer)
        self.assertEqual(self.cost_explorer.region, 'us-east-1')
        self.assertTrue(self.cost_explorer.dry_run)
        self.assertEqual(self.cost_explorer.default_metrics, [CostMetric.UNBLENDED_COST.value])
    
    def test_get_cost_and_usage_dry_run(self):
        """Test cost and usage data retrieval in DRY_RUN mode."""
        result = self.cost_explorer.get_cost_and_usage(
            start_date=self.start_date,
            end_date=self.end_date,
            granularity=Granularity.DAILY
        )
        
        # Verify response structure
        self.assertIn('metadata', result)
        self.assertIn('results_by_time', result)
        self.assertIn('total_cost', result)
        self.assertIn('currency', result)
        
        # Verify metadata
        metadata = result['metadata']
        self.assertIn('start_date', metadata)
        self.assertIn('end_date', metadata)
        self.assertIn('total_periods', metadata)
        self.assertTrue(metadata.get('mock_data', False))
        
        # Verify cost data
        self.assertGreater(result['total_cost'], 0)
        self.assertEqual(result['currency'], 'USD')
        self.assertGreater(len(result['results_by_time']), 0)
    
    def test_get_dimension_values_dry_run(self):
        """Test dimension values retrieval in DRY_RUN mode."""
        result = self.cost_explorer.get_dimension_values(
            dimension=DimensionKey.SERVICE,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Verify response
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # Check for expected service names
        expected_services = ['Amazon Elastic Compute Cloud - Compute', 'Amazon Simple Storage Service']
        for service in expected_services:
            self.assertIn(service, result)
    
    def test_get_cost_forecast_dry_run(self):
        """Test cost forecast generation in DRY_RUN mode."""
        forecast_start = self.end_date + timedelta(days=1)
        forecast_end = forecast_start + timedelta(days=7)
        
        result = self.cost_explorer.get_cost_forecast(
            start_date=forecast_start,
            end_date=forecast_end,
            granularity=Granularity.DAILY
        )
        
        # Verify response structure
        self.assertIn('metadata', result)
        self.assertIn('total_forecast', result)
        self.assertIn('forecast_results_by_time', result)
        self.assertIn('confidence_level', result)
        
        # Verify forecast data
        self.assertEqual(result['confidence_level'], 80)
        self.assertGreater(len(result['forecast_results_by_time']), 0)
        
        # Check forecast structure
        forecast_period = result['forecast_results_by_time'][0]
        self.assertIn('time_period', forecast_period)
        self.assertIn('mean_value', forecast_period)
        self.assertIn('prediction_interval_lower_bound', forecast_period)
        self.assertIn('prediction_interval_upper_bound', forecast_period)
    
    def test_get_usage_forecast_dry_run(self):
        """Test usage forecast generation in DRY_RUN mode."""
        forecast_start = self.end_date + timedelta(days=1)
        forecast_end = forecast_start + timedelta(days=7)
        
        # Usage forecasts require filter expression
        filter_expression = {
            'Dimensions': {
                'Key': 'SERVICE',
                'Values': ['Amazon Elastic Compute Cloud - Compute'],
                'MatchOptions': ['EQUALS']
            }
        }
        
        result = self.cost_explorer.get_usage_forecast(
            start_date=forecast_start,
            end_date=forecast_end,
            filter_expression=filter_expression
        )
        
        # Verify response structure
        self.assertIn('metadata', result)
        self.assertIn('forecast_type', result['metadata'])
        self.assertEqual(result['metadata']['forecast_type'], 'usage')
        self.assertIn('forecast_results_by_time', result)
    
    def test_get_usage_forecast_requires_filter(self):
        """Test that usage forecast requires filter expression."""
        forecast_start = self.end_date + timedelta(days=1)
        forecast_end = forecast_start + timedelta(days=7)
        
        with self.assertRaises(ValueError) as context:
            self.cost_explorer.get_usage_forecast(
                start_date=forecast_start,
                end_date=forecast_end
            )
        
        self.assertIn('Filter expression is required', str(context.exception))
    
    def test_analyze_cost_trends_dry_run(self):
        """Test cost trend analysis in DRY_RUN mode."""
        result = self.cost_explorer.analyze_cost_trends(
            start_date=self.start_date,
            end_date=self.end_date,
            granularity=Granularity.DAILY
        )
        
        # Verify trend analysis structure
        expected_fields = [
            'period_count', 'total_cost', 'average_daily_cost', 'median_daily_cost',
            'min_daily_cost', 'max_daily_cost', 'cost_variance', 'cost_std_dev',
            'trend_direction', 'trend_percentage', 'cost_spikes', 'spike_count'
        ]
        
        for field in expected_fields:
            self.assertIn(field, result)
        
        # Verify trend analysis values
        self.assertGreater(result['period_count'], 0)
        self.assertGreater(result['total_cost'], 0)
        self.assertGreater(result['average_daily_cost'], 0)
        self.assertIn(result['trend_direction'], ['increasing', 'decreasing', 'insufficient_data'])
        self.assertIsInstance(result['cost_spikes'], list)
        self.assertIsInstance(result['spike_count'], int)
    
    def test_get_cost_anomalies_dry_run(self):
        """Test cost anomaly detection in DRY_RUN mode."""
        result = self.cost_explorer.get_cost_anomalies(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Verify response
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # Check anomaly structure
        anomaly = result[0]
        expected_fields = [
            'anomaly_id', 'anomaly_score', 'impact', 'severity',
            'anomaly_start_date', 'anomaly_end_date', 'processed_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, anomaly)
        
        # Verify severity levels
        self.assertIn(anomaly['severity'], ['LOW', 'MEDIUM', 'HIGH'])
    
    def test_generate_cost_report_dry_run(self):
        """Test comprehensive cost report generation in DRY_RUN mode."""
        result = self.cost_explorer.generate_cost_report(
            start_date=self.start_date,
            end_date=self.end_date,
            include_forecast=True,
            include_anomalies=True
        )
        
        # Verify report structure
        expected_sections = [
            'report_metadata', 'cost_summary', 'cost_by_service',
            'cost_by_region', 'trend_analysis', 'forecast_data', 'anomalies'
        ]
        
        for section in expected_sections:
            self.assertIn(section, result)
        
        # Verify report metadata
        metadata = result['report_metadata']
        self.assertEqual(metadata['report_type'], 'comprehensive')
        self.assertTrue(metadata['include_forecast'])
        self.assertTrue(metadata['include_anomalies'])
        
        # Verify cost summary
        cost_summary = result['cost_summary']
        self.assertIn('total_cost', cost_summary)
        self.assertIn('currency', cost_summary)
        self.assertEqual(cost_summary['currency'], 'USD')
        
        # Verify forecast and anomalies are included
        self.assertIsInstance(result['forecast_data'], dict)
        self.assertIsInstance(result['anomalies'], list)
    
    def test_enums_and_constants(self):
        """Test enum values and constants."""
        # Test CostMetric enum
        self.assertEqual(CostMetric.UNBLENDED_COST.value, 'UnblendedCost')
        self.assertEqual(CostMetric.BLENDED_COST.value, 'BlendedCost')
        self.assertEqual(CostMetric.AMORTIZED_COST.value, 'AmortizedCost')
        
        # Test Granularity enum
        self.assertEqual(Granularity.DAILY.value, 'DAILY')
        self.assertEqual(Granularity.MONTHLY.value, 'MONTHLY')
        self.assertEqual(Granularity.HOURLY.value, 'HOURLY')
        
        # Test DimensionKey enum
        self.assertEqual(DimensionKey.SERVICE.value, 'SERVICE')
        self.assertEqual(DimensionKey.REGION.value, 'REGION')
        self.assertEqual(DimensionKey.INSTANCE_TYPE.value, 'INSTANCE_TYPE')
    
    def test_factory_function(self):
        """Test the factory function for creating Cost Explorer instances."""
        cost_explorer = create_cost_explorer(region='us-west-2', dry_run=False)
        
        self.assertIsInstance(cost_explorer, CostExplorer)
        self.assertEqual(cost_explorer.region, 'us-west-2')
        self.assertFalse(cost_explorer.dry_run)
    
    def test_mock_data_generation(self):
        """Test mock data generation methods."""
        # Test mock cost data
        mock_cost_data = self.cost_explorer._generate_mock_cost_data(
            self.start_date, self.end_date, Granularity.DAILY, ['UnblendedCost']
        )
        
        self.assertIn('metadata', mock_cost_data)
        self.assertIn('results_by_time', mock_cost_data)
        self.assertTrue(mock_cost_data['metadata']['mock_data'])
        
        # Test mock dimension values
        mock_services = self.cost_explorer._generate_mock_dimension_values(DimensionKey.SERVICE)
        self.assertIsInstance(mock_services, list)
        self.assertGreater(len(mock_services), 0)
        
        # Test mock forecast data
        forecast_start = self.end_date + timedelta(days=1)
        forecast_end = forecast_start + timedelta(days=7)
        
        mock_forecast = self.cost_explorer._generate_mock_forecast_data(
            forecast_start, forecast_end, Granularity.DAILY, 80
        )
        
        self.assertIn('metadata', mock_forecast)
        self.assertIn('forecast_results_by_time', mock_forecast)
        self.assertTrue(mock_forecast['metadata']['mock_data'])
        
        # Test mock anomalies
        mock_anomalies = self.cost_explorer._generate_mock_anomalies(
            self.start_date, self.end_date
        )
        
        self.assertIsInstance(mock_anomalies, list)
        self.assertGreater(len(mock_anomalies), 0)


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduce log noise during tests
    
    # Run tests
    unittest.main(verbosity=2)