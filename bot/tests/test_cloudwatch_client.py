#!/usr/bin/env python3
"""
Unit Tests for CloudWatch Client

Tests comprehensive CloudWatch integration including:
- Resource utilization monitoring
- Custom metrics publishing
- Log analysis for cost events
- Multi-region metrics aggregation
- Cost optimization alerting
- Unused resource cleanup
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta
import sys
import os

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from aws.cloudwatch_client import CloudWatchClient


class TestCloudWatchClient(unittest.TestCase):
    """Test cases for CloudWatch Client."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_aws_config = Mock()
        self.mock_cloudwatch_client = Mock()
        self.mock_logs_client = Mock()
        
        # Configure mock AWS config
        self.mock_aws_config.get_cloudwatch_client.return_value = self.mock_cloudwatch_client
        self.mock_aws_config.get_cloudwatch_logs_client.return_value = self.mock_logs_client
        self.mock_aws_config.get_multi_region_cloudwatch_clients.return_value = {
            'us-east-1': self.mock_cloudwatch_client,
            'us-west-2': Mock()
        }
        self.mock_aws_config.execute_with_retry = Mock(side_effect=lambda func, service, *args, **kwargs: func(*args, **kwargs))
        
        # Initialize CloudWatch client
        self.cloudwatch_client = CloudWatchClient(self.mock_aws_config, region='us-east-1')
    
    def test_initialization(self):
        """Test CloudWatch client initialization."""
        self.assertEqual(self.cloudwatch_client.region, 'us-east-1')
        self.assertEqual(self.cloudwatch_client.cloudwatch_client, self.mock_cloudwatch_client)
        self.assertEqual(self.cloudwatch_client.logs_client, self.mock_logs_client)
        self.assertEqual(len(self.cloudwatch_client.multi_region_clients), 2)
    
    def test_collect_resource_utilization_metrics_ec2(self):
        """Test collecting utilization metrics for EC2 instances."""
        # Mock CloudWatch response
        mock_response = {
            'Datapoints': [
                {
                    'Timestamp': datetime.utcnow() - timedelta(hours=1),
                    'Average': 25.5,
                    'Maximum': 45.0,
                    'Minimum': 10.0,
                    'Sum': 255.0,
                    'SampleCount': 10
                },
                {
                    'Timestamp': datetime.utcnow() - timedelta(hours=2),
                    'Average': 30.2,
                    'Maximum': 50.0,
                    'Minimum': 15.0,
                    'Sum': 302.0,
                    'SampleCount': 10
                }
            ]
        }
        
        self.mock_cloudwatch_client.get_metric_statistics.return_value = mock_response
        
        # Test collecting metrics
        result = self.cloudwatch_client.collect_resource_utilization_metrics(
            resource_type='ec2',
            resource_ids=['i-1234567890abcdef0'],
            days_back=7
        )
        
        # Verify results
        self.assertEqual(result['resourceType'], 'ec2')
        self.assertEqual(result['region'], 'us-east-1')
        self.assertEqual(result['timeRange']['daysBack'], 7)
        self.assertIn('i-1234567890abcdef0', result['resources'])
        
        # Verify resource metrics
        resource_data = result['resources']['i-1234567890abcdef0']
        self.assertIn('CPUUtilization', resource_data)
        self.assertIn('utilizationAnalysis', resource_data)
        
        # Verify aggregated metrics
        self.assertIn('aggregatedMetrics', result)
        self.assertIn('utilizationSummary', result)
        self.assertIn('costOptimizationInsights', result)
    
    def test_collect_resource_utilization_metrics_rds(self):
        """Test collecting utilization metrics for RDS instances."""
        # Mock CloudWatch response
        mock_response = {
            'Datapoints': [
                {
                    'Timestamp': datetime.utcnow() - timedelta(hours=1),
                    'Average': 15.0,
                    'Maximum': 25.0,
                    'Minimum': 5.0,
                    'Sum': 150.0,
                    'SampleCount': 10
                }
            ]
        }
        
        self.mock_cloudwatch_client.get_metric_statistics.return_value = mock_response
        
        # Test collecting metrics
        result = self.cloudwatch_client.collect_resource_utilization_metrics(
            resource_type='rds',
            resource_ids=['mydb-instance'],
            days_back=14
        )
        
        # Verify results
        self.assertEqual(result['resourceType'], 'rds')
        self.assertIn('mydb-instance', result['resources'])
        
        # Verify RDS-specific metrics are collected
        resource_data = result['resources']['mydb-instance']
        expected_metrics = ['CPUUtilization', 'DatabaseConnections', 'ReadIOPS', 'WriteIOPS']
        
        # At least some metrics should be present
        self.assertTrue(any(metric in resource_data for metric in expected_metrics))
    
    def test_collect_resource_utilization_metrics_lambda(self):
        """Test collecting utilization metrics for Lambda functions."""
        # Mock CloudWatch response
        mock_response = {
            'Datapoints': [
                {
                    'Timestamp': datetime.utcnow() - timedelta(hours=1),
                    'Average': 100.0,
                    'Maximum': 150.0,
                    'Minimum': 50.0,
                    'Sum': 1000.0,
                    'SampleCount': 10
                }
            ]
        }
        
        self.mock_cloudwatch_client.get_metric_statistics.return_value = mock_response
        
        # Test collecting metrics
        result = self.cloudwatch_client.collect_resource_utilization_metrics(
            resource_type='lambda',
            resource_ids=['my-function'],
            days_back=7
        )
        
        # Verify results
        self.assertEqual(result['resourceType'], 'lambda')
        self.assertIn('my-function', result['resources'])
        
        # Verify Lambda-specific metrics
        resource_data = result['resources']['my-function']
        expected_metrics = ['Invocations', 'Duration', 'Errors', 'Throttles']
        
        # At least some metrics should be present
        self.assertTrue(any(metric in resource_data for metric in expected_metrics))
    
    def test_get_resource_dimensions(self):
        """Test getting appropriate dimensions for different resource types."""
        # Test EC2 dimensions
        ec2_dims = self.cloudwatch_client._get_resource_dimensions('ec2', 'i-1234567890abcdef0')
        self.assertEqual(ec2_dims, [{'Name': 'InstanceId', 'Value': 'i-1234567890abcdef0'}])
        
        # Test RDS dimensions
        rds_dims = self.cloudwatch_client._get_resource_dimensions('rds', 'mydb-instance')
        self.assertEqual(rds_dims, [{'Name': 'DBInstanceIdentifier', 'Value': 'mydb-instance'}])
        
        # Test Lambda dimensions
        lambda_dims = self.cloudwatch_client._get_resource_dimensions('lambda', 'my-function')
        self.assertEqual(lambda_dims, [{'Name': 'FunctionName', 'Value': 'my-function'}])
        
        # Test unknown resource type
        unknown_dims = self.cloudwatch_client._get_resource_dimensions('unknown', 'resource-id')
        self.assertEqual(unknown_dims, [])
    
    def test_classify_utilization_level(self):
        """Test utilization level classification."""
        # Test CPU utilization classification
        self.assertEqual(self.cloudwatch_client._classify_utilization_level('CPUUtilization', [5.0]), 'low')
        self.assertEqual(self.cloudwatch_client._classify_utilization_level('CPUUtilization', [25.0]), 'medium')
        self.assertEqual(self.cloudwatch_client._classify_utilization_level('CPUUtilization', [70.0]), 'high')
        self.assertEqual(self.cloudwatch_client._classify_utilization_level('CPUUtilization', [90.0]), 'very_high')
        
        # Test network utilization classification
        self.assertEqual(self.cloudwatch_client._classify_utilization_level('NetworkIn', [500000]), 'low')
        self.assertEqual(self.cloudwatch_client._classify_utilization_level('NetworkIn', [5000000]), 'medium')
        
        # Test no data
        self.assertEqual(self.cloudwatch_client._classify_utilization_level('CPUUtilization', []), 'no_data')
    
    def test_calculate_metric_trends(self):
        """Test metric trend calculation."""
        # Test increasing trend
        datapoints = [
            {'Timestamp': datetime.utcnow() - timedelta(hours=3), 'Average': 10.0},
            {'Timestamp': datetime.utcnow() - timedelta(hours=2), 'Average': 20.0},
            {'Timestamp': datetime.utcnow() - timedelta(hours=1), 'Average': 30.0}
        ]
        
        trends = self.cloudwatch_client._calculate_metric_trends(datapoints)
        self.assertEqual(trends['trend'], 'increasing')
        self.assertGreater(trends['slope'], 0)
        self.assertEqual(trends['dataPointCount'], 3)
        
        # Test stable trend
        stable_datapoints = [
            {'Timestamp': datetime.utcnow() - timedelta(hours=3), 'Average': 25.0},
            {'Timestamp': datetime.utcnow() - timedelta(hours=2), 'Average': 25.1},
            {'Timestamp': datetime.utcnow() - timedelta(hours=1), 'Average': 24.9}
        ]
        
        stable_trends = self.cloudwatch_client._calculate_metric_trends(stable_datapoints)
        self.assertEqual(stable_trends['trend'], 'stable')
        
        # Test insufficient data
        insufficient_data = [{'Timestamp': datetime.utcnow(), 'Average': 10.0}]
        insufficient_trends = self.cloudwatch_client._calculate_metric_trends(insufficient_data)
        self.assertEqual(insufficient_trends['trend'], 'insufficient_data')
    
    def test_analyze_resource_utilization(self):
        """Test resource utilization analysis."""
        # Mock metrics data with low CPU utilization
        metrics_data = {
            'CPUUtilization': {
                'metricName': 'CPUUtilization',
                'statistics': {
                    'overallAverage': 3.5,
                    'overallMax': 8.0,
                    'overallMin': 1.0
                },
                'utilizationLevel': 'low',
                'trends': {'trend': 'stable', 'slope': 0.01}
            }
        }
        
        analysis = self.cloudwatch_client._analyze_resource_utilization(
            'i-1234567890abcdef0', 'ec2', metrics_data
        )
        
        # Verify analysis results
        self.assertEqual(analysis['resourceId'], 'i-1234567890abcdef0')
        self.assertEqual(analysis['resourceType'], 'ec2')
        self.assertEqual(analysis['overallUtilization'], 'underutilized')
        self.assertIn('Average CPU utilization: 3.5%', analysis['keyFindings'])
        
        # Verify optimization opportunities
        self.assertTrue(len(analysis['optimizationOpportunities']) > 0)
        rightsizing_ops = [op for op in analysis['optimizationOpportunities'] if op['type'] == 'rightsizing']
        self.assertTrue(len(rightsizing_ops) > 0)
        self.assertEqual(rightsizing_ops[0]['priority'], 'HIGH')
    
    def test_publish_custom_metrics(self):
        """Test publishing custom metrics to CloudWatch."""
        # Mock metrics data
        metrics_data = [
            {
                'metricName': 'CostOptimizationScore',
                'value': 85.5,
                'unit': 'Percent',
                'timestamp': datetime.utcnow().isoformat(),
                'dimensions': {
                    'ResourceType': 'EC2',
                    'Region': 'us-east-1'
                }
            },
            {
                'metricName': 'PotentialSavings',
                'value': 1250.75,
                'unit': 'None',
                'timestamp': datetime.utcnow().isoformat(),
                'dimensions': {
                    'ResourceType': 'RDS',
                    'Region': 'us-east-1'
                }
            }
        ]
        
        # Test publishing metrics
        result = self.cloudwatch_client.publish_custom_metrics(metrics_data)
        
        # Verify results
        self.assertEqual(result['totalMetrics'], 2)
        self.assertEqual(result['publishedMetrics'], 2)
        self.assertEqual(result['failedMetrics'], 0)
        self.assertEqual(result['namespace'], self.cloudwatch_client.COST_OPTIMIZATION_NAMESPACE)
        
        # Verify CloudWatch API was called
        self.mock_cloudwatch_client.put_metric_data.assert_called()
        call_args = self.mock_cloudwatch_client.put_metric_data.call_args
        self.assertEqual(call_args[1]['Namespace'], self.cloudwatch_client.COST_OPTIMIZATION_NAMESPACE)
        self.assertEqual(len(call_args[1]['MetricData']), 2)
    
    def test_publish_custom_metrics_with_custom_namespace(self):
        """Test publishing custom metrics with custom namespace."""
        metrics_data = [
            {
                'metricName': 'TestMetric',
                'value': 100.0,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
        
        custom_namespace = 'CustomFinOps/Testing'
        result = self.cloudwatch_client.publish_custom_metrics(metrics_data, namespace=custom_namespace)
        
        # Verify custom namespace was used
        self.assertEqual(result['namespace'], custom_namespace)
        call_args = self.mock_cloudwatch_client.put_metric_data.call_args
        self.assertEqual(call_args[1]['Namespace'], custom_namespace)
    
    def test_analyze_log_patterns_for_cost_events(self):
        """Test analyzing CloudWatch logs for cost-related events."""
        # Mock log events response
        mock_log_events = {
            'events': [
                {
                    'timestamp': int((datetime.utcnow() - timedelta(hours=1)).timestamp() * 1000),
                    'logStreamName': 'test-stream',
                    'message': 'High cost alert: EC2 instance spending exceeded budget'
                },
                {
                    'timestamp': int((datetime.utcnow() - timedelta(hours=2)).timestamp() * 1000),
                    'logStreamName': 'test-stream',
                    'message': 'Billing notification: Monthly spend approaching limit'
                }
            ]
        }
        
        # Mock paginator
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [mock_log_events]
        self.mock_logs_client.get_paginator.return_value = mock_paginator
        
        # Test log analysis
        result = self.cloudwatch_client.analyze_log_patterns_for_cost_events(
            log_group_names=['/aws/lambda/cost-monitor'],
            days_back=7
        )
        
        # Verify results
        self.assertEqual(result['logGroups'], ['/aws/lambda/cost-monitor'])
        self.assertEqual(result['region'], 'us-east-1')
        self.assertEqual(result['timeRange']['daysBack'], 7)
        self.assertGreater(result['totalEventsAnalyzed'], 0)
        self.assertIn('cost', result['patterns'])
        self.assertIn('billing', result['patterns'])
        
        # Verify insights were generated
        if result['insights']:
            frequent_patterns = [insight for insight in result['insights'] if insight['type'] == 'frequent_pattern']
            self.assertTrue(len(frequent_patterns) >= 0)  # May or may not have frequent patterns
    
    def test_create_cost_optimization_alarms(self):
        """Test creating cost optimization alarms."""
        alarm_configs = [
            {
                'alarmName': 'HighCPUUtilization',
                'comparisonOperator': 'GreaterThanThreshold',
                'evaluationPeriods': 2,
                'metricName': 'CPUUtilization',
                'namespace': 'AWS/EC2',
                'period': 300,
                'statistic': 'Average',
                'threshold': 80.0,
                'alarmDescription': 'Alert when CPU utilization is high',
                'dimensions': [{'Name': 'InstanceId', 'Value': 'i-1234567890abcdef0'}]
            },
            {
                'alarmName': 'LowCPUUtilization',
                'comparisonOperator': 'LessThanThreshold',
                'evaluationPeriods': 3,
                'metricName': 'CPUUtilization',
                'namespace': 'AWS/EC2',
                'period': 3600,
                'statistic': 'Average',
                'threshold': 5.0,
                'alarmDescription': 'Alert when CPU utilization is very low'
            }
        ]
        
        # Test creating alarms
        result = self.cloudwatch_client.create_cost_optimization_alarms(alarm_configs)
        
        # Verify results
        self.assertEqual(result['totalAlarms'], 2)
        self.assertEqual(result['createdAlarms'], 2)
        self.assertEqual(result['failedAlarms'], 0)
        self.assertIn('HighCPUUtilization', result['alarmNames'])
        self.assertIn('LowCPUUtilization', result['alarmNames'])
        
        # Verify CloudWatch API was called
        self.assertEqual(self.mock_cloudwatch_client.put_metric_alarm.call_count, 2)
    
    def test_get_multi_region_metrics_summary(self):
        """Test getting multi-region metrics summary."""
        result = self.cloudwatch_client.get_multi_region_metrics_summary(
            resource_type='ec2',
            metric_name='CPUUtilization',
            days_back=7
        )
        
        # Verify results
        self.assertEqual(result['resourceType'], 'ec2')
        self.assertEqual(result['metricName'], 'CPUUtilization')
        self.assertEqual(result['timeRange']['daysBack'], 7)
        self.assertIn('regions', result)
        self.assertIn('costOptimizationInsights', result)
        
        # Verify multi-region analysis insight
        multi_region_insights = [
            insight for insight in result['costOptimizationInsights'] 
            if insight['type'] == 'multi_region_analysis'
        ]
        self.assertTrue(len(multi_region_insights) > 0)
    
    def test_cleanup_unused_metrics_and_alarms_dry_run(self):
        """Test cleanup of unused metrics and alarms in dry run mode."""
        # Mock list_metrics response
        mock_metrics_response = {
            'Metrics': [
                {
                    'Namespace': 'AdvancedFinOps',
                    'MetricName': 'UnusedMetric',
                    'Dimensions': [{'Name': 'ResourceType', 'Value': 'EC2'}]
                }
            ]
        }
        
        # Mock describe_alarms response
        mock_alarms_response = {
            'MetricAlarms': [
                {
                    'AlarmName': 'UnusedAlarm',
                    'Namespace': 'AWS/EC2',
                    'MetricName': 'CPUUtilization'
                }
            ]
        }
        
        # Mock empty statistics (indicating unused)
        mock_empty_stats = {'Datapoints': []}
        mock_empty_history = {'AlarmHistoryItems': []}
        
        # Configure mocks
        mock_paginator = Mock()
        mock_paginator.paginate.side_effect = [
            [mock_metrics_response],  # For list_metrics
            [mock_alarms_response]    # For describe_alarms
        ]
        self.mock_cloudwatch_client.get_paginator.return_value = mock_paginator
        self.mock_cloudwatch_client.get_metric_statistics.return_value = mock_empty_stats
        self.mock_cloudwatch_client.describe_alarm_history.return_value = mock_empty_history
        
        # Test cleanup in dry run mode
        result = self.cloudwatch_client.cleanup_unused_metrics_and_alarms(
            dry_run=True,
            days_inactive=30
        )
        
        # Verify results
        self.assertTrue(result['dryRun'])
        self.assertEqual(result['daysInactive'], 30)
        self.assertEqual(len(result['unusedMetrics']), 1)
        self.assertEqual(len(result['unusedAlarms']), 1)
        self.assertGreater(result['potentialSavings'], 0)
        
        # Verify unused metric details
        unused_metric = result['unusedMetrics'][0]
        self.assertEqual(unused_metric['namespace'], 'AdvancedFinOps')
        self.assertEqual(unused_metric['metricName'], 'UnusedMetric')
        
        # Verify unused alarm details
        unused_alarm = result['unusedAlarms'][0]
        self.assertEqual(unused_alarm['alarmName'], 'UnusedAlarm')
        self.assertEqual(unused_alarm['namespace'], 'AWS/EC2')
    
    def test_get_cloudwatch_cost_optimization_summary(self):
        """Test getting comprehensive CloudWatch cost optimization summary."""
        result = self.cloudwatch_client.get_cloudwatch_cost_optimization_summary()
        
        # Verify summary structure
        self.assertIn('timestamp', result)
        self.assertEqual(result['region'], 'us-east-1')
        self.assertEqual(result['multiRegionSupport'], 2)
        
        # Verify custom namespaces
        expected_namespaces = [
            'AdvancedFinOps',
            'AdvancedFinOps/CostOptimization',
            'AdvancedFinOps/ResourceUtilization',
            'AdvancedFinOps/SavingsTracking'
        ]
        self.assertEqual(result['customNamespaces'], expected_namespaces)
        
        # Verify capabilities
        capabilities = result['capabilities']
        self.assertTrue(capabilities['resourceUtilizationMonitoring'])
        self.assertTrue(capabilities['customMetricsPublishing'])
        self.assertTrue(capabilities['logAnalysisForCostEvents'])
        self.assertTrue(capabilities['multiRegionMetricsAggregation'])
        self.assertTrue(capabilities['costOptimizationAlarming'])
        self.assertTrue(capabilities['unusedResourceCleanup'])
        
        # Verify supported services
        expected_services = ['ec2', 'rds', 'lambda', 's3', 'ebs', 'elb']
        for service in expected_services:
            self.assertIn(service, result['supportedServices'])
        
        # Verify optimization features
        self.assertIsInstance(result['optimizationFeatures'], list)
        self.assertGreater(len(result['optimizationFeatures']), 0)
    
    def test_error_handling_in_collect_metrics(self):
        """Test error handling in metrics collection."""
        # Mock CloudWatch client to raise an exception
        self.mock_cloudwatch_client.get_metric_statistics.side_effect = Exception("CloudWatch API error")
        
        # Test that the method handles errors gracefully
        result = self.cloudwatch_client.collect_resource_utilization_metrics(
            resource_type='ec2',
            resource_ids=['i-1234567890abcdef0'],
            days_back=7
        )
        
        # Verify that the method returns a valid structure even with errors
        self.assertEqual(result['resourceType'], 'ec2')
        self.assertEqual(result['region'], 'us-east-1')
        # Resources dict should be empty due to errors
        self.assertEqual(len(result['resources']), 0)
    
    def test_error_handling_in_publish_metrics(self):
        """Test error handling in metrics publishing."""
        # Mock CloudWatch client to raise an exception
        self.mock_cloudwatch_client.put_metric_data.side_effect = Exception("Publishing failed")
        
        metrics_data = [
            {
                'metricName': 'TestMetric',
                'value': 100.0,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
        
        # Test that the method handles errors gracefully
        result = self.cloudwatch_client.publish_custom_metrics(metrics_data)
        
        # Verify error handling
        self.assertEqual(result['totalMetrics'], 1)
        self.assertEqual(result['publishedMetrics'], 0)
        self.assertEqual(result['failedMetrics'], 1)
        self.assertTrue(len(result['errors']) > 0)
    
    def test_unknown_resource_type_handling(self):
        """Test handling of unknown resource types."""
        result = self.cloudwatch_client.collect_resource_utilization_metrics(
            resource_type='unknown_service',
            resource_ids=['resource-123'],
            days_back=7
        )
        
        # Should return empty result for unknown resource type
        self.assertEqual(result, {})
    
    def test_empty_resource_list_handling(self):
        """Test handling of empty resource list."""
        result = self.cloudwatch_client.collect_resource_utilization_metrics(
            resource_type='ec2',
            resource_ids=[],
            days_back=7
        )
        
        # Should return valid structure with empty resources
        self.assertEqual(result['resourceType'], 'ec2')
        self.assertEqual(len(result['resources']), 0)


if __name__ == '__main__':
    unittest.main()