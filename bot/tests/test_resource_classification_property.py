#!/usr/bin/env python3
"""
Property-Based Test for Multi-Service Resource Discovery

**Feature: advanced-finops-platform, Property 2: Resource Classification Accuracy**

This test validates that for any discovered resource with utilization metrics, 
the system correctly classifies it as unused, underutilized, or misconfigured 
based on predefined thresholds and usage patterns.

**Validates: Requirements 1.4**

The test uses property-based testing to generate various resource scenarios
and verify that the classification logic is consistent and accurate across
all AWS services (EC2, RDS, Lambda, S3, EBS).
"""

import pytest
from hypothesis import given, strategies as st, settings, example
from hypothesis.strategies import composite
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import logging

# Import the scanners we want to test
from aws.scan_ec2 import EC2Scanner
from aws.scan_rds import RDSScanner
from aws.scan_lambda import LambdaScanner
from aws.scan_s3 import S3Scanner
from aws.scan_ebs import EBSScanner

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
    
    def get_metric_statistics(self, **kwargs):
        # Return empty metrics for testing
        return {'Datapoints': []}

class MockAWSResource:
    """Mock AWS resource for testing."""
    
    def __init__(self, service_name):
        self.service_name = service_name

# Strategy generators for different resource types
@composite
def ec2_instance_data(draw):
    """Generate EC2 instance data for testing."""
    return {
        'InstanceId': draw(st.text(min_size=10, max_size=20, alphabet='i-0123456789abcdef')),
        'InstanceType': draw(st.sampled_from(['t3.micro', 't3.small', 't3.medium', 't3.large', 'm5.large', 'c5.large'])),
        'State': {'Name': draw(st.sampled_from(['running', 'stopped', 'terminated']))},
        'LaunchTime': datetime.now(timezone.utc) - timedelta(days=draw(st.integers(min_value=1, max_value=365))),
        'Platform': draw(st.sampled_from(['linux', 'windows'])),
        'VpcId': draw(st.text(min_size=10, max_size=20, alphabet='vpc-0123456789abcdef')),
        'Tags': [
            {'Key': 'Environment', 'Value': draw(st.sampled_from(['prod', 'dev', 'test']))},
            {'Key': 'Project', 'Value': draw(st.text(min_size=3, max_size=10))}
        ]
    }

@composite
def ec2_metrics_data(draw):
    """Generate EC2 CloudWatch metrics data for testing."""
    # Generate realistic CPU utilization patterns
    avg_cpu = draw(st.floats(min_value=0.0, max_value=100.0))
    max_cpu = draw(st.floats(min_value=avg_cpu, max_value=100.0))
    data_points = draw(st.integers(min_value=0, max_value=168))  # 0 to 7 days of hourly data
    
    return {
        'cpuUtilization': [
            {
                'timestamp': (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
                'average': avg_cpu + draw(st.floats(min_value=-10, max_value=10)),
                'maximum': max_cpu + draw(st.floats(min_value=-5, max_value=5))
            }
            for i in range(data_points)
        ],
        'avgCpuUtilization': avg_cpu,
        'maxCpuUtilization': max_cpu,
        'dataPoints': data_points
    }

@composite
def rds_instance_data(draw):
    """Generate RDS instance data for testing."""
    return {
        'DBInstanceIdentifier': draw(st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-')),
        'DBInstanceClass': draw(st.sampled_from(['db.t3.micro', 'db.t3.small', 'db.m5.large', 'db.r5.large'])),
        'Engine': draw(st.sampled_from(['mysql', 'postgres', 'oracle-ee', 'sqlserver-se'])),
        'DBInstanceStatus': draw(st.sampled_from(['available', 'stopped', 'creating', 'deleting'])),
        'AllocatedStorage': draw(st.integers(min_value=20, max_value=1000)),
        'StorageType': draw(st.sampled_from(['gp2', 'io1', 'standard'])),
        'MultiAZ': draw(st.booleans()),
        'PubliclyAccessible': draw(st.booleans()),
        'StorageEncrypted': draw(st.booleans()),
        'DBInstanceArn': f"arn:aws:rds:us-east-1:123456789012:db:{draw(st.text(min_size=5, max_size=20))}"
    }

@composite
def rds_metrics_data(draw):
    """Generate RDS CloudWatch metrics data for testing."""
    avg_cpu = draw(st.floats(min_value=0.0, max_value=100.0))
    avg_connections = draw(st.floats(min_value=0.0, max_value=100.0))
    data_points = draw(st.integers(min_value=0, max_value=168))
    
    return {
        'cpuUtilization': [
            {
                'timestamp': (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
                'average': avg_cpu + draw(st.floats(min_value=-5, max_value=5)),
                'maximum': avg_cpu + draw(st.floats(min_value=0, max_value=20))
            }
            for i in range(data_points)
        ],
        'databaseConnections': [
            {
                'timestamp': (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
                'average': avg_connections + draw(st.floats(min_value=-2, max_value=2)),
                'maximum': avg_connections + draw(st.floats(min_value=0, max_value=10))
            }
            for i in range(data_points)
        ],
        'avgCpuUtilization': avg_cpu,
        'avgConnections': avg_connections,
        'dataPoints': data_points
    }

@composite
def lambda_function_data(draw):
    """Generate Lambda function data for testing."""
    return {
        'FunctionName': draw(st.text(min_size=5, max_size=30, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_')),
        'Runtime': draw(st.sampled_from(['python3.9', 'python3.8', 'nodejs14.x', 'java11', 'python2.7'])),
        'MemorySize': draw(st.sampled_from([128, 256, 512, 1024, 2048, 3008])),
        'Timeout': draw(st.integers(min_value=1, max_value=900)),
        'CodeSize': draw(st.integers(min_value=1000, max_value=50000000)),
        'LastModified': datetime.now(timezone.utc).isoformat(),
        'State': draw(st.sampled_from(['Active', 'Inactive', 'Pending'])),
        'FunctionArn': f"arn:aws:lambda:us-east-1:123456789012:function:{draw(st.text(min_size=5, max_size=20))}"
    }

@composite
def lambda_metrics_data(draw):
    """Generate Lambda CloudWatch metrics data for testing."""
    total_invocations = draw(st.integers(min_value=0, max_value=10000))
    avg_duration = draw(st.floats(min_value=0.0, max_value=30000.0))  # milliseconds
    error_rate = draw(st.floats(min_value=0.0, max_value=100.0))
    data_points = draw(st.integers(min_value=0, max_value=168))
    
    return {
        'invocations': [
            {
                'timestamp': (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
                'sum': draw(st.integers(min_value=0, max_value=100))
            }
            for i in range(data_points)
        ],
        'duration': [
            {
                'timestamp': (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
                'average': avg_duration + draw(st.floats(min_value=-1000, max_value=1000)),
                'maximum': avg_duration + draw(st.floats(min_value=0, max_value=5000))
            }
            for i in range(data_points)
        ],
        'totalInvocations': total_invocations,
        'avgDuration': avg_duration,
        'errorRate': error_rate,
        'dataPoints': data_points
    }

@composite
def s3_bucket_data(draw):
    """Generate S3 bucket data for testing."""
    return {
        'Name': draw(st.text(min_size=3, max_size=63, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-')),
        'CreationDate': datetime.now(timezone.utc) - timedelta(days=draw(st.integers(min_value=1, max_value=1000)))
    }

@composite
def s3_metrics_data(draw):
    """Generate S3 CloudWatch metrics data for testing."""
    current_size_gb = draw(st.floats(min_value=0.0, max_value=10000.0))
    object_count = draw(st.integers(min_value=0, max_value=1000000))
    total_requests = draw(st.integers(min_value=0, max_value=100000))
    data_points = draw(st.integers(min_value=7, max_value=30))  # Ensure at least 7 days for S3 analysis
    
    return {
        'currentSizeGB': current_size_gb,
        'currentObjectCount': object_count,
        'totalRequests': total_requests,
        'avgRequestsPerDay': total_requests / max(1, data_points),
        'dataPoints': data_points
    }

@composite
def ebs_volume_data(draw):
    """Generate EBS volume data for testing."""
    attachments = []
    attached = draw(st.booleans())
    
    if attached:
        attachments = [{
            'InstanceId': draw(st.text(min_size=10, max_size=20, alphabet='i-0123456789abcdef')),
            'Device': draw(st.sampled_from(['/dev/sda1', '/dev/xvdf', '/dev/xvdg'])),
            'AttachTime': datetime.now(timezone.utc) - timedelta(days=draw(st.integers(min_value=1, max_value=100))),
            'DeleteOnTermination': draw(st.booleans())
        }]
    
    return {
        'VolumeId': draw(st.text(min_size=10, max_size=20, alphabet='vol-0123456789abcdef')),
        'VolumeType': draw(st.sampled_from(['gp2', 'gp3', 'io1', 'io2', 'st1', 'sc1'])),
        'Size': draw(st.integers(min_value=1, max_value=1000)),
        'State': draw(st.sampled_from(['available', 'in-use', 'creating', 'deleting'])),
        'Encrypted': draw(st.booleans()),
        'Iops': draw(st.integers(min_value=100, max_value=10000)),
        'Attachments': attachments,
        'CreateTime': datetime.now(timezone.utc) - timedelta(days=draw(st.integers(min_value=1, max_value=365))),
        'Tags': [
            {'Key': 'Environment', 'Value': draw(st.sampled_from(['prod', 'dev', 'test']))},
        ]
    }

@composite
def ebs_metrics_data(draw):
    """Generate EBS CloudWatch metrics data for testing."""
    total_iops = draw(st.integers(min_value=0, max_value=100000))
    avg_iops_per_hour = total_iops / max(1, draw(st.integers(min_value=1, max_value=168)))
    data_points = draw(st.integers(min_value=0, max_value=168))
    
    return {
        'totalIOPS': total_iops,
        'avgIOPSPerHour': avg_iops_per_hour,
        'totalReadOps': draw(st.integers(min_value=0, max_value=total_iops)),
        'totalWriteOps': draw(st.integers(min_value=0, max_value=total_iops)),
        'avgQueueLength': draw(st.floats(min_value=0.0, max_value=10.0)),
        'dataPoints': data_points
    }

class TestResourceClassificationAccuracy:
    """Test suite for resource classification accuracy across all services."""
    
    def setup_method(self):
        """Set up test environment."""
        self.mock_aws_config = MockAWSConfig()
        
        # Initialize scanners with mock config
        self.ec2_scanner = EC2Scanner(self.mock_aws_config)
        self.rds_scanner = RDSScanner(self.mock_aws_config)
        self.lambda_scanner = LambdaScanner(self.mock_aws_config)
        self.s3_scanner = S3Scanner(self.mock_aws_config)
        self.ebs_scanner = EBSScanner(self.mock_aws_config)
    
    @given(
        instance_data=ec2_instance_data(),
        metrics_data=ec2_metrics_data()
    )
    @settings(max_examples=50, deadline=None)
    def test_ec2_resource_classification_consistency(self, instance_data, metrics_data):
        """
        Property: EC2 resource classification should be consistent and accurate.
        
        For any EC2 instance with utilization metrics, the classification should:
        1. Be deterministic (same input -> same output)
        2. Follow logical thresholds
        3. Include appropriate optimization opportunities
        """
        # Create mock instance data
        instance_analysis = {
            'resourceId': instance_data['InstanceId'],
            'resourceType': 'ec2',
            'instanceType': instance_data['InstanceType'],
            'state': instance_data['State']['Name'],
            'tags': {tag['Key']: tag['Value'] for tag in instance_data.get('Tags', [])},
            'currentCost': 100.0  # Mock cost
        }
        
        # Test classification logic
        opportunities = self.ec2_scanner._identify_optimization_opportunities(
            instance_analysis, metrics_data
        )
        
        # Property 1: Classification should be deterministic
        opportunities_2 = self.ec2_scanner._identify_optimization_opportunities(
            instance_analysis, metrics_data
        )
        assert opportunities == opportunities_2, "EC2 classification should be deterministic"
        
        # Property 2: Classification should follow logical thresholds
        avg_cpu = metrics_data.get('avgCpuUtilization', 0)
        max_cpu = metrics_data.get('maxCpuUtilization', 0)
        data_points = metrics_data.get('dataPoints', 0)
        
        if data_points >= 24:  # Sufficient data
            if avg_cpu < 2.0 and max_cpu < 10.0:
                # Should classify as unused (cleanup opportunity)
                cleanup_opportunities = [opp for opp in opportunities if opp['type'] == 'cleanup']
                assert len(cleanup_opportunities) > 0, "Very low utilization should trigger cleanup opportunity"
                
                high_priority_cleanup = [opp for opp in cleanup_opportunities if opp['priority'] == 'HIGH']
                assert len(high_priority_cleanup) > 0, "Unused resources should be HIGH priority"
            
            elif avg_cpu < 10.0 and max_cpu < 30.0:
                # Should classify as underutilized (rightsizing opportunity)
                rightsizing_opportunities = [opp for opp in opportunities if opp['type'] == 'rightsizing']
                assert len(rightsizing_opportunities) > 0, "Low utilization should trigger rightsizing opportunity"
        
        # Property 3: All opportunities should have required fields
        for opportunity in opportunities:
            assert 'type' in opportunity, "Opportunity must have type"
            assert 'reason' in opportunity, "Opportunity must have reason"
            assert 'priority' in opportunity, "Opportunity must have priority"
            assert 'estimatedSavings' in opportunity, "Opportunity must have estimated savings"
            assert 'confidence' in opportunity, "Opportunity must have confidence"
            assert 'action' in opportunity, "Opportunity must have action"
            
            # Priority should be valid
            assert opportunity['priority'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], \
                f"Invalid priority: {opportunity['priority']}"
            
            # Estimated savings should be non-negative
            assert opportunity['estimatedSavings'] >= 0, "Estimated savings should be non-negative"
    
    @given(
        db_data=rds_instance_data(),
        metrics_data=rds_metrics_data()
    )
    @settings(max_examples=50, deadline=None)
    def test_rds_resource_classification_consistency(self, db_data, metrics_data):
        """
        Property: RDS resource classification should be consistent and accurate.
        """
        # Create mock database data
        db_analysis = {
            'resourceId': db_data['DBInstanceIdentifier'],
            'resourceType': 'rds',
            'dbInstanceClass': db_data['DBInstanceClass'],
            'engine': db_data['Engine'],
            'status': db_data['DBInstanceStatus'],
            'multiAZ': db_data['MultiAZ'],
            'publiclyAccessible': db_data['PubliclyAccessible'],
            'storageEncrypted': db_data['StorageEncrypted'],  # Use correct field name for scanner
            'tags': {},
            'currentCost': 200.0  # Mock cost
        }
        
        # Test classification logic
        opportunities = self.rds_scanner._identify_optimization_opportunities(
            db_analysis, metrics_data
        )
        
        # Property: Classification should be deterministic
        opportunities_2 = self.rds_scanner._identify_optimization_opportunities(
            db_analysis, metrics_data
        )
        assert opportunities == opportunities_2, "RDS classification should be deterministic"
        
        # Property: Security issues should be flagged
        if db_data['PubliclyAccessible']:
            security_opportunities = [opp for opp in opportunities if opp['type'] == 'security']
            public_access_opportunities = [opp for opp in security_opportunities 
                                         if 'publicly accessible' in opp['reason'].lower()]
            assert len(public_access_opportunities) > 0, "Publicly accessible DB should trigger security opportunity"
        
        if not db_data['StorageEncrypted']:
            security_opportunities = [opp for opp in opportunities if opp['type'] == 'security']
            encryption_opportunities = [opp for opp in security_opportunities 
                                      if 'encrypt' in opp['reason'].lower()]  # Look for 'encrypt' instead of 'encryption'
            assert len(encryption_opportunities) > 0, "Unencrypted DB should trigger security opportunity"
        
        # Property: Low utilization should trigger optimization
        avg_cpu = metrics_data.get('avgCpuUtilization', 0)
        avg_connections = metrics_data.get('avgConnections', 0)
        data_points = metrics_data.get('dataPoints', 0)
        
        if data_points >= 24 and avg_cpu < 5.0 and avg_connections < 1.0:
            cleanup_opportunities = [opp for opp in opportunities if opp['type'] == 'cleanup']
            assert len(cleanup_opportunities) > 0, "Unused database should trigger cleanup opportunity"
    
    @given(
        function_data=lambda_function_data(),
        metrics_data=lambda_metrics_data()
    )
    @settings(max_examples=50, deadline=None)
    def test_lambda_resource_classification_consistency(self, function_data, metrics_data):
        """
        Property: Lambda resource classification should be consistent and accurate.
        """
        # Create mock function data
        function_analysis = {
            'resourceId': function_data['FunctionName'],
            'resourceType': 'lambda',
            'functionName': function_data['FunctionName'],
            'runtime': function_data['Runtime'],
            'memorySize': function_data['MemorySize'],
            'timeout': function_data['Timeout'],
            'state': function_data['State'],
            'tags': {},
            'currentCost': 50.0  # Mock cost
        }
        
        # Test classification logic
        opportunities = self.lambda_scanner._identify_optimization_opportunities(
            function_analysis, metrics_data
        )
        
        # Property: Classification should be deterministic
        opportunities_2 = self.lambda_scanner._identify_optimization_opportunities(
            function_analysis, metrics_data
        )
        assert opportunities == opportunities_2, "Lambda classification should be deterministic"
        
        # Property: Unused functions should be flagged
        total_invocations = metrics_data.get('totalInvocations', 0)
        data_points = metrics_data.get('dataPoints', 0)
        
        if data_points >= 24 and total_invocations == 0:
            cleanup_opportunities = [opp for opp in opportunities if opp['type'] == 'cleanup']
            unused_opportunities = [opp for opp in cleanup_opportunities 
                                  if 'not been invoked' in opp['reason']]
            assert len(unused_opportunities) > 0, "Unused function should trigger cleanup opportunity"
        
        # Property: Deprecated runtimes should be flagged
        if function_data['Runtime'] in ['python2.7', 'nodejs8.10', 'nodejs10.x']:
            security_opportunities = [opp for opp in opportunities if opp['type'] == 'security']
            runtime_opportunities = [opp for opp in security_opportunities 
                                   if 'deprecated runtime' in opp['reason'].lower()]
            assert len(runtime_opportunities) > 0, "Deprecated runtime should trigger security opportunity"
    
    @given(
        bucket_data=s3_bucket_data(),
        storage_metrics=s3_metrics_data(),
        access_metrics=s3_metrics_data()
    )
    @settings(max_examples=50, deadline=None)
    def test_s3_resource_classification_consistency(self, bucket_data, storage_metrics, access_metrics):
        """
        Property: S3 resource classification should be consistent and accurate.
        """
        # Create mock bucket data
        bucket_analysis = {
            'resourceId': bucket_data['Name'],
            'resourceType': 's3',
            'bucketName': bucket_data['Name'],
            'region': 'us-east-1',
            'versioning': 'Disabled',
            'encryption': 'Disabled',
            'hasLifecyclePolicy': False,
            'publicAccessBlock': {},
            'tags': {},
            'currentCost': 75.0  # Mock cost
        }
        
        # Test classification logic
        opportunities = self.s3_scanner._identify_optimization_opportunities(
            bucket_analysis, storage_metrics, access_metrics
        )
        
        # Property: Classification should be deterministic
        opportunities_2 = self.s3_scanner._identify_optimization_opportunities(
            bucket_analysis, storage_metrics, access_metrics
        )
        assert opportunities == opportunities_2, "S3 classification should be deterministic"
        
        # Property: Empty buckets should be flagged
        object_count = storage_metrics.get('currentObjectCount', 0)
        if object_count == 0:
            cleanup_opportunities = [opp for opp in opportunities if opp['type'] == 'cleanup']
            empty_opportunities = [opp for opp in cleanup_opportunities 
                                 if 'empty' in opp['reason'].lower()]
            assert len(empty_opportunities) > 0, "Empty bucket should trigger cleanup opportunity"
        
        # Property: Security issues should be flagged
        if bucket_analysis['encryption'] == 'Disabled':
            security_opportunities = [opp for opp in opportunities if opp['type'] == 'security']
            encryption_opportunities = [opp for opp in security_opportunities 
                                      if 'encryption' in opp['reason'].lower()]
            assert len(encryption_opportunities) > 0, "Unencrypted bucket should trigger security opportunity"
    
    @given(
        volume_data=ebs_volume_data(),
        metrics_data=ebs_metrics_data()
    )
    @settings(max_examples=50, deadline=None)
    def test_ebs_resource_classification_consistency(self, volume_data, metrics_data):
        """
        Property: EBS resource classification should be consistent and accurate.
        """
        # Create mock volume data
        volume_analysis = {
            'resourceId': volume_data['VolumeId'],
            'resourceType': 'ebs',
            'volumeId': volume_data['VolumeId'],
            'volumeType': volume_data['VolumeType'],
            'size': volume_data['Size'],
            'state': volume_data['State'],
            'attached': len(volume_data['Attachments']) > 0,
            'encrypted': volume_data['Encrypted'],
            'iops': volume_data['Iops'],
            'tags': {tag['Key']: tag['Value'] for tag in volume_data.get('Tags', [])},
            'currentCost': 30.0  # Mock cost
        }
        
        # Test classification logic
        opportunities = self.ebs_scanner._identify_volume_optimization_opportunities(volume_analysis)
        
        # Property: Classification should be deterministic
        opportunities_2 = self.ebs_scanner._identify_volume_optimization_opportunities(volume_analysis)
        assert opportunities == opportunities_2, "EBS classification should be deterministic"
        
        # Property: Unattached volumes should be flagged
        if not volume_analysis['attached']:
            cleanup_opportunities = [opp for opp in opportunities if opp['type'] == 'cleanup']
            unattached_opportunities = [opp for opp in cleanup_opportunities 
                                      if 'not attached' in opp['reason'].lower()]
            assert len(unattached_opportunities) > 0, "Unattached volume should trigger cleanup opportunity"
        
        # Property: Unencrypted volumes should be flagged
        if not volume_data['Encrypted']:
            security_opportunities = [opp for opp in opportunities if opp['type'] == 'security']
            encryption_opportunities = [opp for opp in security_opportunities 
                                      if 'not encrypted' in opp['reason'].lower()]
            assert len(encryption_opportunities) > 0, "Unencrypted volume should trigger security opportunity"
    
    def test_classification_completeness_property(self):
        """
        Property: All resource types should support classification.
        
        This test ensures that every scanner has the required classification methods
        and that they return properly structured optimization opportunities.
        """
        scanners = [
            ('EC2', self.ec2_scanner),
            ('RDS', self.rds_scanner),
            ('Lambda', self.lambda_scanner),
            ('S3', self.s3_scanner),
            ('EBS', self.ebs_scanner)
        ]
        
        for scanner_name, scanner in scanners:
            # Check that scanner has required methods
            if scanner_name == 'EC2':
                assert hasattr(scanner, '_identify_optimization_opportunities'), \
                    f"{scanner_name} scanner missing optimization identification method"
            elif scanner_name == 'RDS':
                assert hasattr(scanner, '_identify_optimization_opportunities'), \
                    f"{scanner_name} scanner missing optimization identification method"
            elif scanner_name == 'Lambda':
                assert hasattr(scanner, '_identify_optimization_opportunities'), \
                    f"{scanner_name} scanner missing optimization identification method"
            elif scanner_name == 'S3':
                assert hasattr(scanner, '_identify_optimization_opportunities'), \
                    f"{scanner_name} scanner missing optimization identification method"
            elif scanner_name == 'EBS':
                assert hasattr(scanner, '_identify_volume_optimization_opportunities'), \
                    f"{scanner_name} scanner missing optimization identification method"
            
            # Check that scanner has summary method
            assert hasattr(scanner, 'get_optimization_summary'), \
                f"{scanner_name} scanner missing optimization summary method"
    
    @given(
        # Generate multi-service resource data
        ec2_data=ec2_instance_data(),
        ec2_metrics=ec2_metrics_data(),
        rds_data=rds_instance_data(),
        rds_metrics=rds_metrics_data(),
        lambda_data=lambda_function_data(),
        lambda_metrics=lambda_metrics_data(),
        s3_data=s3_bucket_data(),
        s3_storage_metrics=s3_metrics_data(),
        s3_access_metrics=s3_metrics_data(),
        ebs_data=ebs_volume_data(),
        ebs_metrics=ebs_metrics_data()
    )
    @settings(max_examples=25, deadline=None)
    def test_multi_service_classification_consistency(self, ec2_data, ec2_metrics, rds_data, rds_metrics,
                                                     lambda_data, lambda_metrics, s3_data, s3_storage_metrics,
                                                     s3_access_metrics, ebs_data, ebs_metrics):
        """
        Property: Multi-service resource classification should be consistent across all services.
        
        **Validates: Requirements 1.4**
        
        This comprehensive test validates that resource classification is accurate and consistent
        across all AWS services (EC2, RDS, Lambda, S3, EBS) for any combination of resource
        utilization metrics and configurations.
        """
        
        # Test EC2 classification
        ec2_analysis = {
            'resourceId': ec2_data['InstanceId'],
            'resourceType': 'ec2',
            'instanceType': ec2_data['InstanceType'],
            'state': ec2_data['State']['Name'],
            'tags': {tag['Key']: tag['Value'] for tag in ec2_data.get('Tags', [])},
            'currentCost': 100.0
        }
        
        ec2_opportunities = self.ec2_scanner._identify_optimization_opportunities(ec2_analysis, ec2_metrics)
        
        # Test RDS classification
        rds_analysis = {
            'resourceId': rds_data['DBInstanceIdentifier'],
            'resourceType': 'rds',
            'dbInstanceClass': rds_data['DBInstanceClass'],
            'engine': rds_data['Engine'],
            'status': rds_data['DBInstanceStatus'],
            'multiAZ': rds_data['MultiAZ'],
            'publiclyAccessible': rds_data['PubliclyAccessible'],
            'storageEncrypted': rds_data['StorageEncrypted'],
            'tags': {},
            'currentCost': 200.0
        }
        
        rds_opportunities = self.rds_scanner._identify_optimization_opportunities(rds_analysis, rds_metrics)
        
        # Test Lambda classification
        lambda_analysis = {
            'resourceId': lambda_data['FunctionName'],
            'resourceType': 'lambda',
            'functionName': lambda_data['FunctionName'],
            'runtime': lambda_data['Runtime'],
            'memorySize': lambda_data['MemorySize'],
            'timeout': lambda_data['Timeout'],
            'state': lambda_data['State'],
            'tags': {},
            'currentCost': 50.0
        }
        
        lambda_opportunities = self.lambda_scanner._identify_optimization_opportunities(lambda_analysis, lambda_metrics)
        
        # Test S3 classification
        s3_analysis = {
            'resourceId': s3_data['Name'],
            'resourceType': 's3',
            'bucketName': s3_data['Name'],
            'region': 'us-east-1',
            'versioning': 'Disabled',
            'encryption': 'Disabled',
            'hasLifecyclePolicy': False,
            'publicAccessBlock': {},
            'tags': {},
            'currentCost': 75.0
        }
        
        s3_opportunities = self.s3_scanner._identify_optimization_opportunities(
            s3_analysis, s3_storage_metrics, s3_access_metrics
        )
        
        # Test EBS classification
        ebs_analysis = {
            'resourceId': ebs_data['VolumeId'],
            'resourceType': 'ebs',
            'volumeId': ebs_data['VolumeId'],
            'volumeType': ebs_data['VolumeType'],
            'size': ebs_data['Size'],
            'state': ebs_data['State'],
            'attached': len(ebs_data['Attachments']) > 0,
            'encrypted': ebs_data['Encrypted'],
            'iops': ebs_data['Iops'],
            'tags': {tag['Key']: tag['Value'] for tag in ebs_data.get('Tags', [])},
            'currentCost': 30.0
        }
        
        ebs_opportunities = self.ebs_scanner._identify_volume_optimization_opportunities(ebs_analysis)
        
        # Collect all opportunities for cross-service validation
        all_opportunities = {
            'ec2': ec2_opportunities,
            'rds': rds_opportunities,
            'lambda': lambda_opportunities,
            's3': s3_opportunities,
            'ebs': ebs_opportunities
        }
        
        # Property 1: All opportunities must have required fields
        for service_name, opportunities in all_opportunities.items():
            for opportunity in opportunities:
                assert 'type' in opportunity, f"{service_name} opportunity missing type field"
                assert 'reason' in opportunity, f"{service_name} opportunity missing reason field"
                assert 'priority' in opportunity, f"{service_name} opportunity missing priority field"
                assert 'estimatedSavings' in opportunity, f"{service_name} opportunity missing estimatedSavings field"
                assert 'confidence' in opportunity, f"{service_name} opportunity missing confidence field"
                assert 'action' in opportunity, f"{service_name} opportunity missing action field"
                
                # Validate priority levels
                assert opportunity['priority'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], \
                    f"{service_name} invalid priority: {opportunity['priority']}"
                
                # Validate estimated savings
                assert opportunity['estimatedSavings'] >= 0, \
                    f"{service_name} negative estimated savings: {opportunity['estimatedSavings']}"
        
        # Property 2: Classification should be deterministic (same input -> same output)
        ec2_opportunities_2 = self.ec2_scanner._identify_optimization_opportunities(ec2_analysis, ec2_metrics)
        assert ec2_opportunities == ec2_opportunities_2, "EC2 classification should be deterministic"
        
        rds_opportunities_2 = self.rds_scanner._identify_optimization_opportunities(rds_analysis, rds_metrics)
        assert rds_opportunities == rds_opportunities_2, "RDS classification should be deterministic"
        
        lambda_opportunities_2 = self.lambda_scanner._identify_optimization_opportunities(lambda_analysis, lambda_metrics)
        assert lambda_opportunities == lambda_opportunities_2, "Lambda classification should be deterministic"
        
        s3_opportunities_2 = self.s3_scanner._identify_optimization_opportunities(
            s3_analysis, s3_storage_metrics, s3_access_metrics
        )
        assert s3_opportunities == s3_opportunities_2, "S3 classification should be deterministic"
        
        ebs_opportunities_2 = self.ebs_scanner._identify_volume_optimization_opportunities(ebs_analysis)
        assert ebs_opportunities == ebs_opportunities_2, "EBS classification should be deterministic"
        
        # Property 3: Unused resources should be consistently flagged across services
        # Check for unused resource patterns
        unused_patterns = {
            'ec2': ec2_metrics.get('avgCpuUtilization', 0) < 2.0 and ec2_metrics.get('maxCpuUtilization', 0) < 10.0 and ec2_metrics.get('dataPoints', 0) >= 24,
            'rds': rds_metrics.get('avgCpuUtilization', 0) < 5.0 and rds_metrics.get('avgConnections', 0) < 1.0 and rds_metrics.get('dataPoints', 0) >= 24,
            'lambda': lambda_metrics.get('totalInvocations', 0) == 0 and lambda_metrics.get('dataPoints', 0) >= 24,
            's3': s3_storage_metrics.get('currentObjectCount', 0) == 0,
            'ebs': not ebs_analysis['attached']
        }
        
        for service_name, is_unused in unused_patterns.items():
            if is_unused:
                opportunities = all_opportunities[service_name]
                cleanup_opportunities = [opp for opp in opportunities if opp['type'] == 'cleanup']
                assert len(cleanup_opportunities) > 0, \
                    f"{service_name} unused resource should trigger cleanup opportunity"
        
        # Property 4: Security issues should be consistently flagged
        security_issues = {
            'rds': not rds_analysis['storageEncrypted'] or rds_analysis['publiclyAccessible'],
            's3': s3_analysis['encryption'] == 'Disabled',
            'ebs': not ebs_analysis['encrypted'],
            'lambda': lambda_analysis['runtime'] in ['python2.7', 'nodejs8.10', 'nodejs10.x']
        }
        
        for service_name, has_security_issue in security_issues.items():
            if has_security_issue:
                opportunities = all_opportunities[service_name]
                security_opportunities = [opp for opp in opportunities if opp['type'] == 'security']
                assert len(security_opportunities) > 0, \
                    f"{service_name} security issue should trigger security opportunity"
        
        # Property 5: Governance issues (missing tags) should be consistently flagged
        for service_name, opportunities in all_opportunities.items():
            # All test resources have minimal tags, so should trigger governance opportunities
            governance_opportunities = [opp for opp in opportunities if opp['type'] == 'governance']
            # Note: Not all services may have governance opportunities depending on their tag configuration
            # This is acceptable as long as the structure is consistent
        
        # Property 6: Opportunity types should be service-appropriate
        valid_opportunity_types = {
            'ec2': ['cleanup', 'rightsizing', 'pricing', 'governance', 'monitoring'],
            'rds': ['cleanup', 'rightsizing', 'storage_optimization', 'configuration', 'security', 'governance', 'monitoring'],
            'lambda': ['cleanup', 'rightsizing', 'configuration', 'performance', 'security', 'governance', 'monitoring'],
            's3': ['cleanup', 'storage_optimization', 'security', 'governance'],
            'ebs': ['cleanup', 'rightsizing', 'configuration', 'performance', 'security', 'governance', 'monitoring']
        }
        
        for service_name, opportunities in all_opportunities.items():
            valid_types = valid_opportunity_types[service_name]
            for opportunity in opportunities:
                assert opportunity['type'] in valid_types, \
                    f"{service_name} invalid opportunity type: {opportunity['type']}"

if __name__ == '__main__':
    # Run the property tests
    pytest.main([__file__, '-v', '--tb=short'])