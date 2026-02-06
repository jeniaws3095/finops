#!/usr/bin/env python3
"""
Test script for enhanced AWS configuration utilities.

Tests the enhanced features added for task 8.1:
- IAM role support and credential handling
- Multi-region configuration (Requirement 1.5)
- AWS Cost Management API integration (Requirements 10.1, 10.2, 10.3)
- Advanced rate limiting and exponential backoff
"""

import sys
import os
import logging
from unittest.mock import Mock, patch

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from utils.aws_config import AWSConfig, RateLimiter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_rate_limiter():
    """Test the RateLimiter functionality."""
    print("\n=== Testing RateLimiter ===")
    
    rate_limiter = RateLimiter()
    
    # Test basic rate limiting
    print("Testing basic rate limiting...")
    import time
    start_time = time.time()
    
    # Make several calls quickly
    for i in range(5):
        rate_limiter.wait_if_needed('test-service')
    
    elapsed = time.time() - start_time
    print(f"5 calls took {elapsed:.2f} seconds")
    
    # Test throttle handling
    print("Testing throttle handling...")
    wait_time = rate_limiter.handle_throttle('test-service')
    print(f"First throttle wait time: {wait_time:.2f} seconds")
    
    wait_time = rate_limiter.handle_throttle('test-service')
    print(f"Second throttle wait time: {wait_time:.2f} seconds")
    
    # Reset throttle
    rate_limiter.reset_throttle('test-service')
    wait_time = rate_limiter.handle_throttle('test-service')
    print(f"Wait time after reset: {wait_time:.2f} seconds")
    
    print("✓ RateLimiter tests completed")


def test_aws_config_initialization():
    """Test AWSConfig initialization with various parameters."""
    print("\n=== Testing AWSConfig Initialization ===")
    
    try:
        # Test basic initialization
        print("Testing basic initialization...")
        config = AWSConfig(region='us-west-2')
        print(f"✓ Basic initialization successful, region: {config.region}")
        
        # Test multi-region initialization
        print("Testing multi-region initialization...")
        regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        config_multi = AWSConfig(region='us-east-1', regions=regions)
        print(f"✓ Multi-region initialization successful, regions: {config_multi.regions}")
        
        # Test with profile (will fail if profile doesn't exist, but that's expected)
        print("Testing profile initialization (may fail if profile doesn't exist)...")
        try:
            config_profile = AWSConfig(profile_name='test-profile')
            print("✓ Profile initialization successful")
        except Exception as e:
            print(f"⚠ Profile initialization failed (expected): {e}")
        
        print("✓ AWSConfig initialization tests completed")
        
    except Exception as e:
        print(f"✗ AWSConfig initialization failed: {e}")
        return False
    
    return True


def test_client_creation():
    """Test enhanced client creation functionality."""
    print("\n=== Testing Client Creation ===")
    
    try:
        config = AWSConfig()
        
        # Test basic client creation
        print("Testing basic client creation...")
        sts_client = config.get_client('sts')
        print(f"✓ STS client created: {type(sts_client)}")
        
        # Test Cost Management clients
        print("Testing Cost Management clients...")
        
        # Cost Explorer (should use us-east-1)
        ce_client = config.get_cost_explorer_client()
        print(f"✓ Cost Explorer client created: {type(ce_client)}")
        
        # Budgets client
        budgets_client = config.get_budgets_client()
        print(f"✓ Budgets client created: {type(budgets_client)}")
        
        # Pricing client (should use us-east-1)
        pricing_client = config.get_pricing_client()
        print(f"✓ Pricing client created: {type(pricing_client)}")
        
        # CloudWatch client
        cw_client = config.get_cloudwatch_client()
        print(f"✓ CloudWatch client created: {type(cw_client)}")
        
        # Test multi-region clients
        print("Testing multi-region client creation...")
        regions = ['us-east-1', 'us-west-2']
        multi_clients = config.get_multi_region_clients('ec2', regions)
        print(f"✓ Multi-region EC2 clients created for {len(multi_clients)} regions")
        
        print("✓ Client creation tests completed")
        
    except Exception as e:
        print(f"✗ Client creation failed: {e}")
        return False
    
    return True


def test_service_validation():
    """Test service access validation."""
    print("\n=== Testing Service Validation ===")
    
    try:
        config = AWSConfig()
        
        # Test basic service validation
        print("Testing basic service validation...")
        is_accessible, error = config.validate_service_access('sts')
        print(f"STS accessible: {is_accessible}" + (f" (error: {error})" if error else ""))
        
        # Test Cost Management service validation
        print("Testing Cost Management service validation...")
        cost_results = config.validate_cost_management_access()
        
        for service, (accessible, error) in cost_results.items():
            status = "✓" if accessible else "✗"
            print(f"{status} {service}: {accessible}" + (f" (error: {error})" if error else ""))
        
        # Test multi-region validation
        print("Testing multi-region validation...")
        regions = ['us-east-1', 'us-west-2']
        multi_results = config.validate_multi_region_access('ec2', regions)
        
        for region, (accessible, error) in multi_results.items():
            status = "✓" if accessible else "✗"
            print(f"{status} EC2 in {region}: {accessible}" + (f" (error: {error})" if error else ""))
        
        print("✓ Service validation tests completed")
        
    except Exception as e:
        print(f"✗ Service validation failed: {e}")
        return False
    
    return True


def test_configuration_summary():
    """Test configuration summary functionality."""
    print("\n=== Testing Configuration Summary ===")
    
    try:
        config = AWSConfig(regions=['us-east-1', 'us-west-2', 'eu-west-1'])
        
        summary = config.get_configuration_summary()
        
        print("Configuration Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        print("✓ Configuration summary test completed")
        
    except Exception as e:
        print(f"✗ Configuration summary failed: {e}")
        return False
    
    return True


def test_retry_logic():
    """Test the enhanced retry logic with mocked failures."""
    print("\n=== Testing Retry Logic ===")
    
    try:
        config = AWSConfig()
        
        # Mock operation that fails then succeeds
        call_count = 0
        def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                from botocore.exceptions import ClientError
                error_response = {
                    'Error': {
                        'Code': 'Throttling',
                        'Message': 'Request was throttled'
                    }
                }
                raise ClientError(error_response, 'TestOperation')
            return {'success': True}
        
        print("Testing retry with throttling...")
        result = config.execute_with_retry(mock_operation, 'test-service')
        print(f"✓ Retry successful after {call_count} attempts: {result}")
        
        print("✓ Retry logic tests completed")
        
    except Exception as e:
        print(f"✗ Retry logic failed: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("Starting enhanced AWS configuration tests...")
    
    tests = [
        test_rate_limiter,
        test_aws_config_initialization,
        test_client_creation,
        test_service_validation,
        test_configuration_summary,
        test_retry_logic
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)