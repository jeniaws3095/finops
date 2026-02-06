#!/usr/bin/env python3
"""
Unit tests for AWS configuration utilities.

Tests the aws_config.py module functionality including:
- Credential validation
- Client creation and caching
- Error handling
- Cost Management API support
"""

import unittest
import logging
from unittest.mock import Mock, patch, MagicMock
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import sys
import os

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from utils.aws_config import AWSConfig


class TestAWSConfig(unittest.TestCase):
    """Test cases for AWSConfig class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_region = 'us-west-2'
        self.test_account_id = '123456789012'
    
    @patch('boto3.Session')
    def test_init_success(self, mock_session):
        """Test successful initialization."""
        # Mock STS client and response
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {
            'Account': self.test_account_id,
            'Arn': 'arn:aws:iam::123456789012:user/test-user'
        }
        
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_sts_client
        mock_session.return_value = mock_session_instance
        
        # Create AWSConfig instance
        config = AWSConfig(region=self.test_region)
        
        # Verify initialization
        self.assertEqual(config.region, self.test_region)
        self.assertEqual(config.max_retries, 3)
        self.assertIsNotNone(config._config)
    
    @patch('boto3.Session')
    def test_init_no_credentials(self, mock_session):
        """Test initialization with no credentials."""
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.side_effect = NoCredentialsError()
        
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_sts_client
        mock_session.return_value = mock_session_instance
        
        # Should raise exception
        with self.assertRaises(Exception) as context:
            AWSConfig(region=self.test_region)
        
        self.assertIn("AWS credentials not configured", str(context.exception))
    
    @patch('boto3.Session')
    def test_get_client_caching(self, mock_session):
        """Test client caching functionality."""
        # Mock STS client for initialization
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {
            'Account': self.test_account_id
        }
        
        # Mock EC2 client
        mock_ec2_client = Mock()
        
        mock_session_instance = Mock()
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'sts': mock_sts_client,
            'ec2': mock_ec2_client
        }.get(service)
        mock_session.return_value = mock_session_instance
        
        config = AWSConfig(region=self.test_region)
        
        # Get client twice
        client1 = config.get_client('ec2')
        client2 = config.get_client('ec2')
        
        # Should be the same instance (cached)
        self.assertIs(client1, client2)
    
    @patch('boto3.Session')
    def test_get_cost_explorer_client(self, mock_session):
        """Test Cost Explorer client creation (should use us-east-1)."""
        # Mock STS client for initialization
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {
            'Account': self.test_account_id
        }
        
        # Mock CE client
        mock_ce_client = Mock()
        
        mock_session_instance = Mock()
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'sts': mock_sts_client,
            'ce': mock_ce_client
        }.get(service)
        mock_session.return_value = mock_session_instance
        
        config = AWSConfig(region=self.test_region)
        
        # Get Cost Explorer client
        ce_client = config.get_cost_explorer_client()
        
        # Verify it's the mocked client
        self.assertIs(ce_client, mock_ce_client)
        
        # Verify it was called with us-east-1 region
        mock_session_instance.client.assert_called_with('ce', config=unittest.mock.ANY)
    
    @patch('boto3.Session')
    def test_get_account_id(self, mock_session):
        """Test getting AWS account ID."""
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {
            'Account': self.test_account_id
        }
        
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_sts_client
        mock_session.return_value = mock_session_instance
        
        config = AWSConfig(region=self.test_region)
        account_id = config.get_account_id()
        
        self.assertEqual(account_id, self.test_account_id)
    
    @patch('boto3.Session')
    def test_list_regions(self, mock_session):
        """Test listing AWS regions."""
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {
            'Account': self.test_account_id
        }
        
        mock_ec2_client = Mock()
        mock_ec2_client.describe_regions.return_value = {
            'Regions': [
                {'RegionName': 'us-east-1'},
                {'RegionName': 'us-west-2'},
                {'RegionName': 'eu-west-1'}
            ]
        }
        
        mock_session_instance = Mock()
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'sts': mock_sts_client,
            'ec2': mock_ec2_client
        }.get(service)
        mock_session.return_value = mock_session_instance
        
        config = AWSConfig(region=self.test_region)
        regions = config.list_regions()
        
        expected_regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        self.assertEqual(regions, expected_regions)
    
    @patch('boto3.Session')
    def test_execute_with_retry_success(self, mock_session):
        """Test successful operation with retry logic."""
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {
            'Account': self.test_account_id
        }
        
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_sts_client
        mock_session.return_value = mock_session_instance
        
        config = AWSConfig(region=self.test_region)
        
        # Mock operation that succeeds
        mock_operation = Mock(return_value={'result': 'success'})
        
        result = config.execute_with_retry(mock_operation, 'arg1', kwarg1='value1')
        
        self.assertEqual(result, {'result': 'success'})
        mock_operation.assert_called_once_with('arg1', kwarg1='value1')
    
    @patch('boto3.Session')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_execute_with_retry_throttling(self, mock_sleep, mock_session):
        """Test retry logic with throttling error."""
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {
            'Account': self.test_account_id
        }
        
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_sts_client
        mock_session.return_value = mock_session_instance
        
        config = AWSConfig(region=self.test_region, max_retries=2)
        
        # Mock operation that fails with throttling then succeeds
        throttling_error = ClientError(
            error_response={'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}},
            operation_name='TestOperation'
        )
        
        mock_operation = Mock(side_effect=[throttling_error, {'result': 'success'}])
        
        result = config.execute_with_retry(mock_operation)
        
        self.assertEqual(result, {'result': 'success'})
        self.assertEqual(mock_operation.call_count, 2)
        mock_sleep.assert_called_once()  # Should have slept once for retry
    
    @patch('boto3.Session')
    def test_validate_service_access_success(self, mock_session):
        """Test successful service access validation."""
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {
            'Account': self.test_account_id
        }
        
        mock_ec2_client = Mock()
        mock_ec2_client.describe_regions.return_value = {'Regions': []}
        
        mock_session_instance = Mock()
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'sts': mock_sts_client,
            'ec2': mock_ec2_client
        }.get(service)
        mock_session.return_value = mock_session_instance
        
        config = AWSConfig(region=self.test_region)
        
        # Test EC2 service validation
        is_accessible = config.validate_service_access('ec2')
        
        self.assertTrue(is_accessible)
        mock_ec2_client.describe_regions.assert_called_once()
    
    @patch('boto3.Session')
    def test_validate_service_access_failure(self, mock_session):
        """Test service access validation failure."""
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {
            'Account': self.test_account_id
        }
        
        mock_ec2_client = Mock()
        mock_ec2_client.describe_regions.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='DescribeRegions'
        )
        
        mock_session_instance = Mock()
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'sts': mock_sts_client,
            'ec2': mock_ec2_client
        }.get(service)
        mock_session.return_value = mock_session_instance
        
        config = AWSConfig(region=self.test_region)
        
        # Test EC2 service validation failure
        is_accessible = config.validate_service_access('ec2')
        
        self.assertFalse(is_accessible)


if __name__ == '__main__':
    # Set up logging for tests
    logging.basicConfig(level=logging.DEBUG)
    
    # Run tests
    unittest.main(verbosity=2)