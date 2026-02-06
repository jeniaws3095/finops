#!/usr/bin/env python3
"""
Test suite for S3 Scanner functionality

Tests the S3 scanner's ability to:
- Discover and analyze S3 buckets
- Analyze storage classes, lifecycle policies, and versioning
- Identify unused buckets and storage optimization opportunities
- Include cross-region replication cost analysis
- Generate comprehensive optimization recommendations

Requirements: 1.1, 7.3, 2.4
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from aws.scan_s3 import S3Scanner
from utils.aws_config import AWSConfig


class TestS3Scanner(unittest.TestCase):
    """Test cases for S3Scanner functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_aws_config = Mock(spec=AWSConfig)
        self.mock_s3_client = Mock()
        self.mock_cloudwatch_client = Mock()
        
        self.mock_aws_config.get_client.side_effect = lambda service: {
            's3': self.mock_s3_client,
            'cloudwatch': self.mock_cloudwatch_client
        }.get(service)
        
        self.scanner = S3Scanner(self.mock_aws_config, region='us-east-1')
    
    def test_scanner_initialization(self):
        """Test S3Scanner initialization."""
        self.assertEqual(self.scanner.region, 'us-east-1')
        self.assertEqual(self.scanner.aws_config, self.mock_aws_config)
        self.assertEqual(self.scanner.s3_client, self.mock_s3_client)
        self.assertEqual(self.scanner.cloudwatch_client, self.mock_cloudwatch_client)
    
    def test_scan_buckets_basic(self):
        """Test basic bucket scanning functionality."""
        # Mock S3 list_buckets response
        self.mock_s3_client.list_buckets.return_value = {
            'Buckets': [
                {
                    'Name': 'test-bucket-1',
                    'CreationDate': datetime.now(timezone.utc)
                },
                {
                    'Name': 'test-bucket-2',
                    'CreationDate': datetime.now(timezone.utc)
                }
            ]
        }
        
        # Mock bucket analysis methods
        with patch.object(self.scanner, '_analyze_bucket') as mock_analyze:
            mock_analyze.side_effect = [
                {'resourceId': 'test-bucket-1', 'resourceType': 's3'},
                {'resourceId': 'test-bucket-2', 'resourceType': 's3'}
            ]
            
            buckets = self.scanner.scan_buckets()
            
            self.assertEqual(len(buckets), 2)
            self.assertEqual(buckets[0]['resourceId'], 'test-bucket-1')
            self.assertEqual(buckets[1]['resourceId'], 'test-bucket-2')
            self.assertEqual(mock_analyze.call_count, 2)
    
    def test_analyze_bucket_comprehensive(self):
        """Test comprehensive bucket analysis."""
        bucket = {
            'Name': 'test-bucket',
            'CreationDate': datetime.now(timezone.utc)
        }
        
        # Mock all the S3 API calls
        self.mock_s3_client.get_bucket_location.return_value = {
            'LocationConstraint': 'us-west-2'
        }
        
        self.mock_s3_client.get_bucket_versioning.return_value = {
            'Status': 'Enabled'
        }
        
        self.mock_s3_client.get_bucket_encryption.return_value = {
            'ServerSideEncryptionConfiguration': {
                'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]
            }
        }
        
        self.mock_s3_client.get_bucket_lifecycle_configuration.return_value = {
            'Rules': [
                {
                    'ID': 'test-rule',
                    'Status': 'Enabled',
                    'Transitions': [
                        {
                            'Days': 30,
                            'StorageClass': 'STANDARD_IA'
                        }
                    ]
                }
            ]
        }
        
        self.mock_s3_client.get_public_access_block.return_value = {
            'PublicAccessBlockConfiguration': {
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        }
        
        self.mock_s3_client.get_bucket_tagging.return_value = {
            'TagSet': [
                {'Key': 'Environment', 'Value': 'production'},
                {'Key': 'Project', 'Value': 'test-project'}
            ]
        }
        
        # Mock storage and access metrics
        with patch.object(self.scanner, '_get_bucket_storage_metrics') as mock_storage:
            with patch.object(self.scanner, '_get_bucket_access_metrics') as mock_access:
                with patch.object(self.scanner, '_analyze_storage_classes') as mock_storage_classes:
                    with patch.object(self.scanner, '_identify_optimization_opportunities') as mock_opportunities:
                        with patch.object(self.scanner, '_estimate_bucket_cost') as mock_cost:
                            
                            mock_storage.return_value = {
                                'currentSizeGB': 100.5,
                                'currentObjectCount': 1000,
                                'dataPoints': 14
                            }
                            
                            mock_access.return_value = {
                                'totalRequests': 500,
                                'avgRequestsPerDay': 35.7,
                                'totalGetRequests': 400,
                                'totalPutRequests': 100
                            }
                            
                            mock_storage_classes.return_value = {
                                'storageClasses': {'STANDARD': 800, 'STANDARD_IA': 200},
                                'totalObjects': 1000,
                                'hasIntelligentTiering': False,
                                'hasGlacierObjects': False
                            }
                            
                            mock_opportunities.return_value = [
                                {
                                    'type': 'storage_optimization',
                                    'reason': 'Consider intelligent tiering',
                                    'priority': 'MEDIUM',
                                    'estimatedSavings': 25.0,
                                    'confidence': 'HIGH'
                                }
                            ]
                            
                            mock_cost.return_value = 125.75
                            
                            result = self.scanner._analyze_bucket(bucket, 14)
                            
                            # Verify bucket data structure
                            self.assertEqual(result['resourceId'], 'test-bucket')
                            self.assertEqual(result['resourceType'], 's3')
                            self.assertEqual(result['region'], 'us-west-2')
                            self.assertEqual(result['versioning'], 'Enabled')
                            self.assertEqual(result['encryption'], 'Enabled')
                            self.assertTrue(result['hasLifecyclePolicy'])
                            self.assertEqual(result['currentCost'], 125.75)
                            
                            # Verify tags
                            self.assertEqual(result['tags']['Environment'], 'production')
                            self.assertEqual(result['tags']['Project'], 'test-project')
                            
                            # Verify public access block
                            pab = result['publicAccessBlock']
                            self.assertTrue(pab['BlockPublicAcls'])
                            self.assertTrue(pab['RestrictPublicBuckets'])
    
    def test_storage_metrics_collection(self):
        """Test storage metrics collection from CloudWatch."""
        bucket_name = 'test-bucket'
        
        # Mock CloudWatch responses
        size_response = {
            'Datapoints': [
                {
                    'Timestamp': datetime.now(timezone.utc) - timedelta(days=1),
                    'Average': 1073741824  # 1GB in bytes
                },
                {
                    'Timestamp': datetime.now(timezone.utc),
                    'Average': 2147483648  # 2GB in bytes
                }
            ]
        }
        
        objects_response = {
            'Datapoints': [
                {
                    'Timestamp': datetime.now(timezone.utc) - timedelta(days=1),
                    'Average': 500
                },
                {
                    'Timestamp': datetime.now(timezone.utc),
                    'Average': 1000
                }
            ]
        }
        
        self.mock_cloudwatch_client.get_metric_statistics.side_effect = [
            size_response, objects_response
        ]
        
        metrics = self.scanner._get_bucket_storage_metrics(bucket_name, 14)
        
        # Verify metrics structure
        self.assertEqual(len(metrics['bucketSizeBytes']), 2)
        self.assertEqual(len(metrics['numberOfObjects']), 2)
        self.assertEqual(metrics['currentSizeBytes'], 2147483648)
        self.assertAlmostEqual(metrics['currentSizeGB'], 2.0, places=1)
        self.assertEqual(metrics['currentObjectCount'], 1000)
        self.assertEqual(metrics['dataPoints'], 2)
    
    def test_access_metrics_collection(self):
        """Test access metrics collection from CloudWatch."""
        bucket_name = 'test-bucket'
        
        # Mock CloudWatch responses for different request types
        all_requests_response = {
            'Datapoints': [
                {'Timestamp': datetime.now(timezone.utc) - timedelta(days=1), 'Sum': 100},
                {'Timestamp': datetime.now(timezone.utc), 'Sum': 150}
            ]
        }
        
        get_requests_response = {
            'Datapoints': [
                {'Timestamp': datetime.now(timezone.utc) - timedelta(days=1), 'Sum': 80},
                {'Timestamp': datetime.now(timezone.utc), 'Sum': 120}
            ]
        }
        
        put_requests_response = {
            'Datapoints': [
                {'Timestamp': datetime.now(timezone.utc) - timedelta(days=1), 'Sum': 20},
                {'Timestamp': datetime.now(timezone.utc), 'Sum': 30}
            ]
        }
        
        self.mock_cloudwatch_client.get_metric_statistics.side_effect = [
            all_requests_response, get_requests_response, put_requests_response
        ]
        
        metrics = self.scanner._get_bucket_access_metrics(bucket_name, 14)
        
        # Verify access metrics
        self.assertEqual(len(metrics['allRequests']), 2)
        self.assertEqual(len(metrics['getRequests']), 2)
        self.assertEqual(len(metrics['putRequests']), 2)
        self.assertEqual(metrics['totalRequests'], 250)  # 100 + 150
        self.assertEqual(metrics['totalGetRequests'], 200)  # 80 + 120
        self.assertEqual(metrics['totalPutRequests'], 50)  # 20 + 30
        self.assertAlmostEqual(metrics['avgRequestsPerDay'], 125.0)  # 250 / 2
    
    def test_storage_class_analysis(self):
        """Test storage class analysis functionality."""
        bucket_name = 'test-bucket'
        
        # Mock list_objects_v2 paginator
        mock_paginator = Mock()
        mock_page_iterator = [
            {
                'Contents': [
                    {'Key': 'file1.txt', 'StorageClass': 'STANDARD'},
                    {'Key': 'file2.txt', 'StorageClass': 'STANDARD'},
                    {'Key': 'file3.txt', 'StorageClass': 'STANDARD_IA'},
                    {'Key': 'file4.txt', 'StorageClass': 'INTELLIGENT_TIERING'},
                    {'Key': 'file5.txt'}  # No StorageClass = STANDARD
                ]
            }
        ]
        
        mock_paginator.paginate.return_value = mock_page_iterator
        self.mock_s3_client.get_paginator.return_value = mock_paginator
        
        analysis = self.scanner._analyze_storage_classes(bucket_name)
        
        # Verify storage class analysis
        self.assertEqual(analysis['totalObjects'], 5)
        self.assertEqual(analysis['storageClasses']['STANDARD'], 3)  # 2 explicit + 1 default
        self.assertEqual(analysis['storageClasses']['STANDARD_IA'], 1)
        self.assertEqual(analysis['storageClasses']['INTELLIGENT_TIERING'], 1)
        self.assertTrue(analysis['hasIntelligentTiering'])
        self.assertFalse(analysis['hasGlacierObjects'])
    
    def test_optimization_opportunities_identification(self):
        """Test identification of optimization opportunities."""
        bucket_data = {
            'resourceId': 'test-bucket',
            'versioning': 'Enabled',
            'hasLifecyclePolicy': False,
            'encryption': 'Disabled',
            'publicAccessBlock': {
                'BlockPublicAcls': False,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            },
            'tags': {'Environment': 'production'},  # Missing Project and Owner tags
            'storageClassAnalysis': {
                'storageClasses': {'STANDARD': 500},
                'hasIntelligentTiering': False
            },
            'currentCost': 100.0
        }
        
        storage_metrics = {
            'currentSizeGB': 50.0,
            'currentObjectCount': 1000,
            'dataPoints': 14
        }
        
        access_metrics = {
            'totalRequests': 0,  # Unused bucket
            'avgRequestsPerDay': 0.0
        }
        
        opportunities = self.scanner._identify_optimization_opportunities(
            bucket_data, storage_metrics, access_metrics
        )
        
        # Verify different types of opportunities are identified
        opportunity_types = [opp['type'] for opp in opportunities]
        
        # Should identify unused bucket
        self.assertIn('cleanup', opportunity_types)
        
        # Should identify missing lifecycle policy
        self.assertIn('storage_optimization', opportunity_types)
        
        # Should identify security issues
        self.assertIn('security', opportunity_types)
        
        # Should identify missing tags
        self.assertIn('governance', opportunity_types)
        
        # Verify specific opportunities
        unused_bucket_opp = next((opp for opp in opportunities if opp['reason'].startswith('Bucket has')), None)
        self.assertIsNotNone(unused_bucket_opp)
        self.assertEqual(unused_bucket_opp['priority'], 'HIGH')
        
        encryption_opp = next((opp for opp in opportunities if 'encryption' in opp['reason']), None)
        self.assertIsNotNone(encryption_opp)
        self.assertEqual(encryption_opp['priority'], 'HIGH')
    
    def test_cost_estimation(self):
        """Test bucket cost estimation."""
        storage_metrics = {
            'currentSizeGB': 100.0,  # 100 GB
            'currentObjectCount': 1000
        }
        
        access_metrics = {
            'totalRequests': 10000,
            'totalGetRequests': 8000,
            'totalPutRequests': 2000
        }
        
        cost = self.scanner._estimate_bucket_cost(storage_metrics, access_metrics, 'us-east-1')
        
        # Verify cost calculation
        self.assertGreater(cost, 0)
        self.assertIsInstance(cost, float)
        
        # Test with different region (should have different cost)
        cost_west = self.scanner._estimate_bucket_cost(storage_metrics, access_metrics, 'us-west-1')
        self.assertNotEqual(cost, cost_west)
        
        # Test with zero storage (should be zero cost)
        zero_storage_metrics = {'currentSizeGB': 0, 'currentObjectCount': 0}
        zero_cost = self.scanner._estimate_bucket_cost(zero_storage_metrics, access_metrics, 'us-east-1')
        self.assertEqual(zero_cost, 0.0)
    
    def test_optimization_summary_generation(self):
        """Test optimization summary generation."""
        buckets = [
            {
                'resourceId': 'empty-bucket',
                'region': 'us-east-1',
                'storageMetrics': {'currentSizeGB': 0, 'currentObjectCount': 0},
                'accessMetrics': {'totalRequests': 0},
                'currentCost': 0.0,
                'optimizationOpportunities': [
                    {'type': 'cleanup', 'priority': 'MEDIUM', 'estimatedSavings': 0.0}
                ]
            },
            {
                'resourceId': 'unused-bucket',
                'region': 'us-west-2',
                'storageMetrics': {'currentSizeGB': 50.0, 'currentObjectCount': 100},
                'accessMetrics': {'totalRequests': 0},
                'currentCost': 25.0,
                'optimizationOpportunities': [
                    {'type': 'cleanup', 'priority': 'HIGH', 'estimatedSavings': 20.0},
                    {'type': 'security', 'priority': 'HIGH', 'estimatedSavings': 0.0}
                ]
            },
            {
                'resourceId': 'active-bucket',
                'region': 'us-east-1',
                'storageMetrics': {'currentSizeGB': 200.0, 'currentObjectCount': 2000},
                'accessMetrics': {'totalRequests': 1000},
                'currentCost': 100.0,
                'optimizationOpportunities': [
                    {'type': 'storage_optimization', 'priority': 'MEDIUM', 'estimatedSavings': 30.0}
                ]
            }
        ]
        
        summary = self.scanner.get_optimization_summary(buckets)
        
        # Verify summary statistics
        self.assertEqual(summary['totalBuckets'], 3)
        self.assertEqual(summary['emptyBuckets'], 1)
        self.assertEqual(summary['unusedBuckets'], 1)
        self.assertEqual(summary['totalStorageGB'], 250.0)  # 0 + 50 + 200
        self.assertEqual(summary['totalMonthlyCost'], 125.0)  # 0 + 25 + 100
        self.assertEqual(summary['potentialMonthlySavings'], 50.0)  # 0 + 20 + 30
        
        # Verify opportunity breakdown
        self.assertEqual(summary['optimizationOpportunities']['cleanup'], 2)
        self.assertEqual(summary['optimizationOpportunities']['storage_optimization'], 1)
        self.assertEqual(summary['optimizationOpportunities']['security'], 1)
        
        # Verify priority breakdown
        self.assertEqual(summary['priorityBreakdown']['HIGH'], 2)
        self.assertEqual(summary['priorityBreakdown']['MEDIUM'], 2)
        
        # Verify region breakdown
        self.assertEqual(summary['regionBreakdown']['us-east-1'], 2)
        self.assertEqual(summary['regionBreakdown']['us-west-2'], 1)
        
        # Verify savings percentage
        expected_percentage = (50.0 / 125.0) * 100
        self.assertAlmostEqual(summary['savingsPercentage'], expected_percentage, places=1)
    
    def test_bucket_count_by_region(self):
        """Test bucket count by region functionality."""
        self.mock_s3_client.list_buckets.return_value = {
            'Buckets': [
                {'Name': 'bucket-1'},
                {'Name': 'bucket-2'},
                {'Name': 'bucket-3'}
            ]
        }
        
        # Mock get_bucket_location responses
        location_responses = [
            {'LocationConstraint': None},  # us-east-1
            {'LocationConstraint': 'us-west-2'},
            {'LocationConstraint': 'eu-west-1'}
        ]
        
        self.mock_s3_client.get_bucket_location.side_effect = location_responses
        
        region_counts = self.scanner.get_bucket_count_by_region()
        
        # Verify region counts
        self.assertEqual(region_counts['us-east-1'], 1)
        self.assertEqual(region_counts['us-west-2'], 1)
        self.assertEqual(region_counts['eu-west-1'], 1)
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test bucket analysis with permission errors
        bucket = {'Name': 'restricted-bucket', 'CreationDate': datetime.now(timezone.utc)}
        
        from botocore.exceptions import ClientError
        
        # Mock permission denied error
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}}
        self.mock_s3_client.get_bucket_location.side_effect = ClientError(error_response, 'GetBucketLocation')
        
        # Should handle error gracefully and set region to 'unknown'
        with patch.object(self.scanner, '_get_bucket_storage_metrics') as mock_storage:
            with patch.object(self.scanner, '_get_bucket_access_metrics') as mock_access:
                with patch.object(self.scanner, '_analyze_storage_classes') as mock_storage_classes:
                    with patch.object(self.scanner, '_identify_optimization_opportunities') as mock_opportunities:
                        with patch.object(self.scanner, '_estimate_bucket_cost') as mock_cost:
                            
                            mock_storage.return_value = {'currentSizeGB': 0, 'currentObjectCount': 0, 'dataPoints': 0}
                            mock_access.return_value = {'totalRequests': 0, 'avgRequestsPerDay': 0}
                            mock_storage_classes.return_value = {'storageClasses': {}, 'totalObjects': 0}
                            mock_opportunities.return_value = []
                            mock_cost.return_value = 0.0
                            
                            result = self.scanner._analyze_bucket(bucket, 14)
                            
                            self.assertIsNotNone(result)
                            self.assertEqual(result['region'], 'unknown')


def run_s3_scanner_tests():
    """Run S3 scanner tests and return results."""
    print("=" * 60)
    print("RUNNING S3 SCANNER TESTS")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestS3Scanner)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("S3 SCANNER TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_s3_scanner_tests()
    sys.exit(0 if success else 1)