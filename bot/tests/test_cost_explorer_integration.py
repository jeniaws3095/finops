#!/usr/bin/env python3
"""
Integration tests for Cost Explorer with Advanced FinOps Platform.

Tests the integration of Cost Explorer with the existing system components:
- Integration with AWS configuration utilities
- Cost analysis workflow integration
- End-to-end cost analysis functionality

Requirements: 10.1, 5.1
"""

import unittest
import sys
import os
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from aws.cost_explorer import CostExplorer, create_cost_explorer
from utils.aws_config import AWSConfig


class TestCostExplorerIntegration(unittest.TestCase):
    """Integration test cases for Cost Explorer with Advanced FinOps Platform."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.aws_config = AWSConfig()
        self.cost_explorer = CostExplorer(aws_config=self.aws_config, dry_run=True)
        
        self.start_date = datetime.now(timezone.utc) - timedelta(days=30)
        self.end_date = datetime.now(timezone.utc)
    
    def test_cost_explorer_with_aws_config(self):
        """Test Cost Explorer integration with AWS configuration."""
        # Test that Cost Explorer can use AWS config
        self.assertIsNotNone(self.cost_explorer.aws_config)
        self.assertEqual(self.cost_explorer.aws_config, self.aws_config)
        
        # Test client creation through AWS config
        # In DRY_RUN mode, this should work without actual AWS credentials
        self.assertIsNotNone(self.cost_explorer.client)
        self.assertIsNotNone(self.cost_explorer.anomaly_client)
    
    def test_cost_data_backend_format(self):
        """Test cost data formatting for backend API."""
        # Generate cost data
        cost_data = self.cost_explorer.get_cost_and_usage(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Transform for backend API
        backend_data = {
            'type': 'cost_analysis',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'total_cost': cost_data['total_cost'],
                'currency': cost_data['currency'],
                'period_count': cost_data['metadata']['total_periods'],
                'analysis_period': {
                    'start_date': cost_data['metadata']['start_date'],
                    'end_date': cost_data['metadata']['end_date']
                },
                'cost_breakdown': cost_data['results_by_time'][:5]  # Send first 5 periods
            }
        }
        
        # Verify data structure for backend
        self.assertIn('type', backend_data)
        self.assertIn('data', backend_data)
        self.assertEqual(backend_data['type'], 'cost_analysis')
        self.assertGreater(backend_data['data']['total_cost'], 0)
        self.assertEqual(backend_data['data']['currency'], 'USD')
    
    def test_forecast_data_backend_format(self):
        """Test forecast data formatting for backend."""
        forecast_start = self.end_date + timedelta(days=1)
        forecast_end = forecast_start + timedelta(days=30)
        
        # Generate forecast
        forecast_data = self.cost_explorer.get_cost_forecast(
            start_date=forecast_start,
            end_date=forecast_end
        )
        
        # Transform for backend
        backend_forecast = {
            'type': 'cost_forecast',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'forecast_period': {
                    'start_date': forecast_data['metadata']['start_date'],
                    'end_date': forecast_data['metadata']['end_date']
                },
                'confidence_level': forecast_data['confidence_level'],
                'total_forecast': forecast_data['total_forecast'],
                'daily_forecasts': forecast_data['forecast_results_by_time'][:7]  # First week
            }
        }
        
        # Verify data structure
        self.assertIn('type', backend_forecast)
        self.assertIn('data', backend_forecast)
        self.assertEqual(backend_forecast['type'], 'cost_forecast')
        self.assertIn('confidence_level', backend_forecast['data'])
        self.assertEqual(backend_forecast['data']['confidence_level'], 80)
    
    def test_anomaly_data_backend_format(self):
        """Test anomaly data formatting for backend."""
        # Get anomaly data
        anomalies = self.cost_explorer.get_cost_anomalies(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Transform for backend
        backend_anomalies = {
            'type': 'cost_anomalies',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'anomaly_count': len(anomalies),
                'analysis_period': {
                    'start_date': self.start_date.isoformat(),
                    'end_date': self.end_date.isoformat()
                },
                'anomalies': [
                    {
                        'anomaly_id': anomaly['anomaly_id'],
                        'severity': anomaly['severity'],
                        'anomaly_score': anomaly['anomaly_score'],
                        'impact': anomaly['impact'],
                        'start_date': anomaly['anomaly_start_date'],
                        'end_date': anomaly['anomaly_end_date']
                    }
                    for anomaly in anomalies
                ]
            }
        }
        
        # Verify data structure
        self.assertIn('type', backend_anomalies)
        self.assertEqual(backend_anomalies['type'], 'cost_anomalies')
        self.assertGreater(backend_anomalies['data']['anomaly_count'], 0)
        self.assertIsInstance(backend_anomalies['data']['anomalies'], list)
    
    def test_comprehensive_cost_report_backend_format(self):
        """Test comprehensive cost report formatting for backend."""
        # Generate comprehensive report
        report = self.cost_explorer.generate_cost_report(
            start_date=self.start_date,
            end_date=self.end_date,
            include_forecast=True,
            include_anomalies=True
        )
        
        # Transform for backend storage
        backend_report = {
            'type': 'comprehensive_cost_report',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'report_metadata': report['report_metadata'],
                'summary': {
                    'total_cost': report['cost_summary']['total_cost'],
                    'currency': report['cost_summary']['currency'],
                    'period_count': report['cost_summary']['period_count']
                },
                'trend_analysis': {
                    'trend_direction': report['trend_analysis']['trend_direction'],
                    'trend_percentage': report['trend_analysis']['trend_percentage'],
                    'spike_count': report['trend_analysis']['spike_count']
                },
                'service_breakdown': report['cost_by_service'],
                'regional_breakdown': report['cost_by_region'],
                'forecast_summary': {
                    'has_forecast': 'forecast_data' in report and 'error' not in report['forecast_data'],
                    'forecast_periods': len(report.get('forecast_data', {}).get('forecast_results_by_time', []))
                },
                'anomaly_summary': {
                    'anomaly_count': len(report['anomalies']),
                    'high_severity_count': len([a for a in report['anomalies'] if a['severity'] == 'HIGH'])
                }
            }
        }
        
        # Verify comprehensive report structure
        self.assertIn('type', backend_report)
        self.assertEqual(backend_report['type'], 'comprehensive_cost_report')
        
        # Verify all sections are present
        data = backend_report['data']
        expected_sections = ['report_metadata', 'summary', 'trend_analysis', 'service_breakdown', 'regional_breakdown']
        for section in expected_sections:
            self.assertIn(section, data)
        
        # Verify summary data
        summary = data['summary']
        self.assertGreater(summary['total_cost'], 0)
        self.assertEqual(summary['currency'], 'USD')
        self.assertGreater(summary['period_count'], 0)
    
    def test_cost_optimization_workflow_integration(self):
        """Test integration with cost optimization workflow."""
        # Simulate a complete cost analysis workflow
        workflow_results = {}
        
        # Step 1: Historical cost analysis
        cost_data = self.cost_explorer.get_cost_and_usage(
            start_date=self.start_date,
            end_date=self.end_date
        )
        workflow_results['historical_analysis'] = {
            'total_cost': cost_data['total_cost'],
            'daily_average': cost_data['total_cost'] / cost_data['metadata']['total_periods']
        }
        
        # Step 2: Trend analysis
        trends = self.cost_explorer.analyze_cost_trends(
            start_date=self.start_date,
            end_date=self.end_date
        )
        workflow_results['trend_analysis'] = {
            'direction': trends['trend_direction'],
            'percentage_change': trends['trend_percentage'],
            'volatility': trends['cost_std_dev']
        }
        
        # Step 3: Forecast future costs
        forecast_start = self.end_date + timedelta(days=1)
        forecast_end = forecast_start + timedelta(days=30)
        
        forecast = self.cost_explorer.get_cost_forecast(
            start_date=forecast_start,
            end_date=forecast_end
        )
        workflow_results['forecast'] = {
            'predicted_monthly_cost': float(forecast['total_forecast']['MeanValue']),
            'confidence_range': {
                'lower': float(forecast['total_forecast']['PredictionIntervalLowerBound']),
                'upper': float(forecast['total_forecast']['PredictionIntervalUpperBound'])
            }
        }
        
        # Step 4: Anomaly detection
        anomalies = self.cost_explorer.get_cost_anomalies(
            start_date=self.start_date,
            end_date=self.end_date
        )
        workflow_results['anomaly_detection'] = {
            'anomaly_count': len(anomalies),
            'high_impact_anomalies': len([a for a in anomalies if a['severity'] in ['HIGH', 'CRITICAL']])
        }
        
        # Step 5: Generate optimization recommendations
        workflow_results['optimization_recommendations'] = []
        
        # If costs are trending upward, recommend investigation
        if trends['trend_direction'] == 'increasing' and trends['trend_percentage'] > 10:
            workflow_results['optimization_recommendations'].append({
                'type': 'cost_trend_investigation',
                'priority': 'HIGH',
                'description': f"Costs trending upward by {trends['trend_percentage']:.1f}% - investigate drivers"
            })
        
        # If high volatility, recommend cost controls
        if trends['cost_std_dev'] > trends['average_daily_cost'] * 0.2:
            workflow_results['optimization_recommendations'].append({
                'type': 'cost_volatility_control',
                'priority': 'MEDIUM',
                'description': "High cost volatility detected - implement cost controls"
            })
        
        # If anomalies detected, recommend review
        if len(anomalies) > 0:
            workflow_results['optimization_recommendations'].append({
                'type': 'anomaly_review',
                'priority': 'HIGH',
                'description': f"{len(anomalies)} cost anomalies detected - review and address"
            })
        
        # Verify workflow results
        self.assertIn('historical_analysis', workflow_results)
        self.assertIn('trend_analysis', workflow_results)
        self.assertIn('forecast', workflow_results)
        self.assertIn('anomaly_detection', workflow_results)
        self.assertIn('optimization_recommendations', workflow_results)
        
        # Verify we have actionable recommendations
        self.assertGreater(len(workflow_results['optimization_recommendations']), 0)
        
        # Verify recommendation structure
        for rec in workflow_results['optimization_recommendations']:
            self.assertIn('type', rec)
            self.assertIn('priority', rec)
            self.assertIn('description', rec)
            self.assertIn(rec['priority'], ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
    
    def test_multi_dimensional_cost_analysis(self):
        """Test multi-dimensional cost analysis capabilities."""
        # Test cost analysis by service
        service_costs = self.cost_explorer.get_cost_and_usage(
            start_date=self.start_date,
            end_date=self.end_date,
            group_by=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        # Test cost analysis by region
        region_costs = self.cost_explorer.get_cost_and_usage(
            start_date=self.start_date,
            end_date=self.end_date,
            group_by=[{'Type': 'DIMENSION', 'Key': 'REGION'}]
        )
        
        # Test filtered cost analysis
        ec2_filter = {
            'Dimensions': {
                'Key': 'SERVICE',
                'Values': ['Amazon Elastic Compute Cloud - Compute'],
                'MatchOptions': ['EQUALS']
            }
        }
        
        ec2_costs = self.cost_explorer.get_cost_and_usage(
            start_date=self.start_date,
            end_date=self.end_date,
            filter_expression=ec2_filter
        )
        
        # Verify all analyses completed successfully
        self.assertIn('results_by_time', service_costs)
        self.assertIn('results_by_time', region_costs)
        self.assertIn('results_by_time', ec2_costs)
        
        # Verify data structure
        self.assertGreater(service_costs['total_cost'], 0)
        self.assertGreater(region_costs['total_cost'], 0)
        self.assertGreater(ec2_costs['total_cost'], 0)
    
    def test_cost_explorer_factory_integration(self):
        """Test Cost Explorer factory function integration."""
        # Test factory function with AWS config
        cost_explorer = create_cost_explorer(
            aws_config=self.aws_config,
            region='us-east-1',
            dry_run=True
        )
        
        self.assertIsInstance(cost_explorer, CostExplorer)
        self.assertEqual(cost_explorer.aws_config, self.aws_config)
        self.assertTrue(cost_explorer.dry_run)
        self.assertEqual(cost_explorer.region, 'us-east-1')
        
        # Test basic functionality
        cost_data = cost_explorer.get_cost_and_usage(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertIn('total_cost', cost_data)
        self.assertGreater(cost_data['total_cost'], 0)


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduce log noise during tests
    
    # Run tests
    unittest.main(verbosity=2)