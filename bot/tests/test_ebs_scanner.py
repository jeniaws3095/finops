#!/usr/bin/env python3
"""
Unit tests for EBS Scanner

Tests the EBS scanner's functionality including:
- Volume discovery and analysis
- Snapshot analysis and cleanup recommendations
- Utilization metrics collection
- Cost estimation and optimization opportunities
- Cross-AZ analysis and volume type optimization

Requirements: 1.1, 7.4, 2.4
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from aws.scan_ebs import EBSScanner
from botocore.exceptions import ClientError


class TestEBSScanner(unittest.TestCase):
    """Test cases for EBS Scanner."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_aws_config = Mock()
        self.mock_ec2_client = Mock()
        self.mock_cloudwatch_client = Mock()
        
        self.mock_aws_config.get_client.side_effect = lambda service: {
            'ec2': self.mock_ec2_client,
            'cloudwatch': self.mock_cloudwatch_client
        }.get(service)
        
        self.scanner = EBSScanner(self.mock_aws_config, region='us-east-1')
    
    def test_scanner_initialization(self):
        """Test EBS scanner initialization."""
        self.assertEqual(self.scanner.region, 'us-east-1')
        self.assertEqual(self.scanner.aws_config, self.mock_aws_config)
        self.assertEqual(self.scanner.ec2_client, self.mock_ec2_client)
        self.assertEqual(self.scanner.cloudwatch_client, self.mock_cloudwatch_client)
    
    def test_scan_volumes_success(self):
        """Test successful volume scanning."""
        # Mock paginator response
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [
            {
                'Volumes': [
                    {
                        'VolumeId': 'vol-12345',
                        'VolumeType': 'gp3',
                        'Size': 100,
                        'State': 'in-use',
                        'Encrypted': True,
                        'Iops': 3000,
                        'Throughput': 125,
                        'AvailabilityZone': 'us-east-1a',
                        'CreateTime': datetime.utcnow(),
                        'Attachments': [
                            {
                                'InstanceId': 'i-12345',
                                'Device': '/dev/sda1',
                                'AttachTime': datetime.utcnow(),
                                'DeleteOnTermination': True
                            }
                        ],
                        'Tags': [
                            {'Key': 'Environment', 'Value': 'production'}
                        ]
                    }
                ]
            }
        ]
        
        self.mock_ec2_client.get_paginator.return_value = mock_paginator
        
        # Mock CloudWatch metrics - need different responses for different metrics
        def mock_get_metric_statistics(Namespace, MetricName, **kwargs):
            if MetricName == 'VolumeQueueLength':
                return {
                    'Datapoints': [
                        {
                            'Timestamp': datetime.utcnow() - timedelta(hours=i),
                            'Average': 1.0 + i * 0.1
                        }
                        for i in range(24)
                    ]
                }
            else:
                return {
                    'Datapoints': [
                        {
                            'Timestamp': datetime.utcnow(),
                            'Sum': 100
                        }
                    ]
                }
        
        self.mock_cloudwatch_client.get_metric_statistics.side_effect = mock_get_metric_statistics
        
        volumes = self.scanner.scan_volumes(days_back=14)
        
        self.assertEqual(len(volumes), 1)
        volume = volumes[0]
        self.assertEqual(volume['resourceId'], 'vol-12345')
        self.assertEqual(volume['volumeType'], 'gp3')
        self.assertEqual(volume['size'], 100)
        self.assertTrue(volume['attached'])
        self.assertTrue(volume['encrypted'])
    
    def test_scan_volumes_error_handling(self):
        """Test volume scanning error handling."""
        self.mock_ec2_client.get_paginator.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation'}},
            'DescribeVolumes'
        )
        
        with self.assertRaises(ClientError):
            self.scanner.scan_volumes()
    
    def test_scan_snapshots_success(self):
        """Test successful snapshot scanning."""
        # Mock paginator response
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [
            {
                'Snapshots': [
                    {
                        'SnapshotId': 'snap-12345',
                        'VolumeId': 'vol-12345',
                        'VolumeSize': 100,
                        'State': 'completed',
                        'Progress': '100%',
                        'StartTime': datetime.utcnow() - timedelta(days=30),
                        'Description': 'Test snapshot',
                        'Encrypted': True,
                        'Tags': [
                            {'Key': 'Environment', 'Value': 'production'}
                        ]
                    }
                ]
            }
        ]
        
        self.mock_ec2_client.get_paginator.return_value = mock_paginator
        
        # Mock volume existence check
        self.mock_ec2_client.describe_volumes.return_value = {'Volumes': []}
        
        snapshots = self.scanner.scan_snapshots(days_back=30)
        
        self.assertEqual(len(snapshots), 1)
        snapshot = snapshots[0]
        self.assertEqual(snapshot['resourceId'], 'snap-12345')
        self.assertEqual(snapshot['volumeId'], 'vol-12345')
        self.assertEqual(snapshot['volumeSize'], 100)
        self.assertTrue(snapshot['sourceVolumeExists'])
    
    def test_analyze_attached_volume(self):
        """Test analysis of attached volume."""
        volume_data = {
            'VolumeId': 'vol-12345',
            'VolumeType': 'gp3',
            'Size': 100,
            'State': 'in-use',
            'Encrypted': True,
            'Iops': 3000,
            'Throughput': 125,
            'AvailabilityZone': 'us-east-1a',
            'CreateTime': datetime.utcnow(),
            'Attachments': [
                {
                    'InstanceId': 'i-12345',
                    'Device': '/dev/sda1',
                    'AttachTime': datetime.utcnow(),
                    'DeleteOnTermination': True
                }
            ],
            'Tags': [
                {'Key': 'Environment', 'Value': 'production'},
                {'Key': 'Project', 'Value': 'web-app'},
                {'Key': 'Owner', 'Value': 'dev-team'}
            ]
        }
        
        # Mock CloudWatch metrics - need different responses for different metrics
        def mock_get_metric_statistics(Namespace, MetricName, **kwargs):
            if MetricName == 'VolumeQueueLength':
                return {
                    'Datapoints': [
                        {
                            'Timestamp': datetime.utcnow() - timedelta(hours=i),
                            'Average': 1.0 + i * 0.1
                        }
                        for i in range(24)
                    ]
                }
            else:
                return {
                    'Datapoints': [
                        {
                            'Timestamp': datetime.utcnow() - timedelta(hours=i),
                            'Sum': 100 + i
                        }
                        for i in range(24)
                    ]
                }
        
        self.mock_cloudwatch_client.get_metric_statistics.side_effect = mock_get_metric_statistics
        
        result = self.scanner._analyze_volume(volume_data, days_back=14)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['resourceId'], 'vol-12345')
        self.assertEqual(result['volumeType'], 'gp3')
        self.assertTrue(result['attached'])
        self.assertEqual(result['instanceId'], 'i-12345')
        self.assertTrue(result['encrypted'])
        self.assertIn('utilizationMetrics', result)
        self.assertIn('optimizationOpportunities', result)
        self.assertGreater(result['currentCost'], 0)
    
    def test_analyze_unattached_volume(self):
        """Test analysis of unattached volume."""
        volume_data = {
            'VolumeId': 'vol-unattached',
            'VolumeType': 'gp2',
            'Size': 50,
            'State': 'available',
            'Encrypted': False,
            'Iops': 150,
            'AvailabilityZone': 'us-east-1b',
            'CreateTime': datetime.utcnow() - timedelta(days=30),
            'Attachments': [],
            'Tags': []
        }
        
        result = self.scanner._analyze_volume(volume_data, days_back=14)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['resourceId'], 'vol-unattached')
        self.assertFalse(result['attached'])
        self.assertIsNone(result['instanceId'])
        self.assertFalse(result['encrypted'])
        
        # Should have cleanup opportunity for unattached volume
        opportunities = result['optimizationOpportunities']
        cleanup_opportunities = [opp for opp in opportunities if opp['type'] == 'cleanup']
        self.assertGreater(len(cleanup_opportunities), 0)
    
    def test_analyze_snapshot_orphaned(self):
        """Test analysis of orphaned snapshot."""
        snapshot_data = {
            'SnapshotId': 'snap-orphaned',
            'VolumeId': 'vol-nonexistent',
            'VolumeSize': 100,
            'State': 'completed',
            'Progress': '100%',
            'StartTime': datetime.utcnow() - timedelta(days=400),
            'Description': 'Orphaned snapshot',
            'Encrypted': True,
            'Tags': []
        }
        
        # Mock volume not found
        self.mock_ec2_client.describe_volumes.side_effect = ClientError(
            {'Error': {'Code': 'InvalidVolume.NotFound'}},
            'DescribeVolumes'
        )
        
        result = self.scanner._analyze_snapshot(snapshot_data, days_back=30)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['resourceId'], 'snap-orphaned')
        self.assertFalse(result['sourceVolumeExists'])
        self.assertGreater(result['ageDays'], 365)
        
        # Should have cleanup opportunities
        opportunities = result['optimizationOpportunities']
        cleanup_opportunities = [opp for opp in opportunities if opp['type'] == 'cleanup']
        self.assertGreater(len(cleanup_opportunities), 0)
    
    def test_get_volume_metrics_success(self):
        """Test successful volume metrics retrieval."""
        # Mock CloudWatch metrics - need different responses for different metrics
        def mock_get_metric_statistics(Namespace, MetricName, **kwargs):
            if MetricName == 'VolumeQueueLength':
                return {
                    'Datapoints': [
                        {
                            'Timestamp': datetime.utcnow() - timedelta(hours=i),
                            'Average': 1.0 + i * 0.1
                        }
                        for i in range(24)
                    ]
                }
            else:
                return {
                    'Datapoints': [
                        {
                            'Timestamp': datetime.utcnow() - timedelta(hours=i),
                            'Sum': 100 + i * 10
                        }
                        for i in range(24)
                    ]
                }
        
        self.mock_cloudwatch_client.get_metric_statistics.side_effect = mock_get_metric_statistics
        
        metrics = self.scanner._get_volume_metrics('vol-12345', days_back=14)
        
        self.assertIn('volumeReadOps', metrics)
        self.assertIn('volumeWriteOps', metrics)
        self.assertIn('totalIOPS', metrics)
        self.assertIn('avgIOPSPerHour', metrics)
        self.assertGreater(metrics['dataPoints'], 0)
    
    def test_get_volume_metrics_error_handling(self):
        """Test volume metrics error handling."""
        self.mock_cloudwatch_client.get_metric_statistics.side_effect = ClientError(
            {'Error': {'Code': 'InvalidParameterValue'}},
            'GetMetricStatistics'
        )
        
        metrics = self.scanner._get_volume_metrics('vol-12345', days_back=14)
        
        # Should return empty metrics on error
        self.assertEqual(metrics['totalIOPS'], 0)
        self.assertEqual(metrics['dataPoints'], 0)
    
    def test_identify_volume_optimization_opportunities(self):
        """Test volume optimization opportunity identification."""
        # Test unattached volume
        volume_data = {
            'volumeType': 'gp2',
            'size': 100,
            'attached': False,
            'state': 'available',
            'encrypted': False,
            'tags': {},
            'currentCost': 10.0,
            'utilizationMetrics': {}
        }
        
        opportunities = self.scanner._identify_volume_optimization_opportunities(volume_data)
        
        # Should identify cleanup opportunity
        cleanup_opps = [opp for opp in opportunities if opp['type'] == 'cleanup']
        self.assertGreater(len(cleanup_opps), 0)
        
        # Should identify security opportunity (encryption)
        security_opps = [opp for opp in opportunities if opp['type'] == 'security']
        self.assertGreater(len(security_opps), 0)
        
        # Should identify governance opportunity (missing tags)
        governance_opps = [opp for opp in opportunities if opp['type'] == 'governance']
        self.assertGreater(len(governance_opps), 0)
    
    def test_identify_volume_optimization_low_utilization(self):
        """Test optimization opportunities for low utilization volume."""
        volume_data = {
            'volumeType': 'gp2',
            'size': 100,
            'attached': True,
            'state': 'in-use',
            'encrypted': True,
            'tags': {'Environment': 'production', 'Project': 'web-app', 'Owner': 'dev-team'},
            'currentCost': 10.0,
            'utilizationMetrics': {
                'totalIOPS': 0,
                'avgIOPSPerHour': 0,
                'dataPoints': 24
            }
        }
        
        opportunities = self.scanner._identify_volume_optimization_opportunities(volume_data)
        
        # Should identify cleanup opportunity for unused volume
        cleanup_opps = [opp for opp in opportunities if opp['type'] == 'cleanup']
        self.assertGreater(len(cleanup_opps), 0)
        
        # Should identify configuration opportunity (gp2 to gp3)
        config_opps = [opp for opp in opportunities if opp['type'] == 'configuration']
        self.assertGreater(len(config_opps), 0)
    
    def test_identify_snapshot_optimization_opportunities(self):
        """Test snapshot optimization opportunity identification."""
        # Test old orphaned snapshot
        snapshot_data = {
            'ageDays': 400,
            'sourceVolumeExists': False,
            'state': 'completed',
            'tags': {},
            'currentCost': 5.0
        }
        
        opportunities = self.scanner._identify_snapshot_optimization_opportunities(snapshot_data, days_back=30)
        
        # Should identify multiple cleanup opportunities
        cleanup_opps = [opp for opp in opportunities if opp['type'] == 'cleanup']
        self.assertGreater(len(cleanup_opps), 0)
        
        # Should identify governance opportunity (missing tags)
        governance_opps = [opp for opp in opportunities if opp['type'] == 'governance']
        self.assertGreater(len(governance_opps), 0)
    
    def test_estimate_volume_cost(self):
        """Test volume cost estimation."""
        # Test GP3 volume
        cost_gp3 = self.scanner._estimate_volume_cost('gp3', 100, 0, 125)
        self.assertGreater(cost_gp3, 0)
        self.assertEqual(cost_gp3, 100 * 0.08)  # GP3 base cost
        
        # Test IO1 volume with IOPS
        cost_io1 = self.scanner._estimate_volume_cost('io1', 100, 1000, 0)
        expected_cost = (100 * 0.125) + (1000 * 0.065)
        self.assertEqual(cost_io1, expected_cost)
        
        # Test GP3 with additional throughput
        cost_gp3_throughput = self.scanner._estimate_volume_cost('gp3', 100, 0, 250)
        expected_cost = (100 * 0.08) + ((250 - 125) * 0.04)
        self.assertEqual(cost_gp3_throughput, expected_cost)
    
    def test_estimate_snapshot_cost(self):
        """Test snapshot cost estimation."""
        cost = self.scanner._estimate_snapshot_cost(100)
        expected_cost = (100 * 0.5) * 0.05  # 50% of volume size * $0.05/GB
        self.assertEqual(cost, expected_cost)
    
    def test_get_volume_count_by_type(self):
        """Test volume count by type."""
        self.mock_ec2_client.describe_volumes.return_value = {
            'Volumes': [
                {'VolumeType': 'gp3'},
                {'VolumeType': 'gp2'},
                {'VolumeType': 'gp3'},
                {'VolumeType': 'io1'}
            ]
        }
        
        counts = self.scanner.get_volume_count_by_type()
        
        self.assertEqual(counts['gp3'], 2)
        self.assertEqual(counts['gp2'], 1)
        self.assertEqual(counts['io1'], 1)
    
    def test_get_optimization_summary(self):
        """Test optimization summary generation."""
        volumes = [
            {
                'attached': True,
                'size': 100,
                'currentCost': 10.0,
                'volumeType': 'gp3',
                'optimizationOpportunities': [
                    {'type': 'configuration', 'priority': 'MEDIUM', 'estimatedSavings': 2.0}
                ]
            },
            {
                'attached': False,
                'size': 50,
                'currentCost': 5.0,
                'volumeType': 'gp2',
                'optimizationOpportunities': [
                    {'type': 'cleanup', 'priority': 'HIGH', 'estimatedSavings': 5.0}
                ]
            }
        ]
        
        snapshots = [
            {
                'sourceVolumeExists': False,
                'ageDays': 400,
                'currentCost': 2.5,
                'optimizationOpportunities': [
                    {'type': 'cleanup', 'priority': 'HIGH', 'estimatedSavings': 2.5}
                ]
            }
        ]
        
        summary = self.scanner.get_optimization_summary(volumes, snapshots)
        
        self.assertEqual(summary['totalVolumes'], 2)
        self.assertEqual(summary['attachedVolumes'], 1)
        self.assertEqual(summary['unattachedVolumes'], 1)
        self.assertEqual(summary['totalStorageGB'], 150)
        self.assertEqual(summary['totalMonthlyCost'], 17.5)
        self.assertEqual(summary['potentialMonthlySavings'], 9.5)
        self.assertEqual(summary['totalSnapshots'], 1)
        self.assertEqual(summary['orphanedSnapshots'], 1)
        self.assertEqual(summary['oldSnapshots'], 1)


if __name__ == '__main__':
    unittest.main()