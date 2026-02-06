#!/usr/bin/env python3
"""
Test script to verify Advanced FinOps Platform setup.

This script tests:
1. AWS credentials configuration
2. Python dependencies
3. Module imports
4. Basic functionality
"""

import sys
import logging

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing module imports...")
    
    try:
        import boto3
        print("✓ boto3 imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import boto3: {e}")
        return False
    
    try:
        import requests
        print("✓ requests imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import requests: {e}")
        return False
    
    try:
        from utils.aws_config import AWSConfig
        from utils.safety_controls import SafetyControls
        from utils.http_client import HTTPClient
        print("✓ All utility modules imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import utility modules: {e}")
        return False
    
    return True

def test_aws_config():
    """Test AWS configuration."""
    print("\nTesting AWS configuration...")
    
    try:
        from utils.aws_config import AWSConfig
        aws_config = AWSConfig()
        account_id = aws_config.get_account_id()
        print(f"✓ AWS credentials validated for account: {account_id}")
        return True
    except Exception as e:
        print(f"✗ AWS configuration failed: {e}")
        return False

def test_safety_controls():
    """Test safety controls."""
    print("\nTesting safety controls...")
    
    try:
        from utils.safety_controls import SafetyControls, RiskLevel, OperationType
        safety = SafetyControls(dry_run=True)
        
        # Test risk assessment
        risk = safety.assess_risk(
            OperationType.TERMINATE_INSTANCE,
            {'instance_type': 't2.micro', 'tags': {}}
        )
        print(f"✓ Risk assessment working: {risk}")
        
        return True
    except Exception as e:
        print(f"✗ Safety controls test failed: {e}")
        return False

def test_http_client():
    """Test HTTP client (without requiring backend to be running)."""
    print("\nTesting HTTP client...")
    
    try:
        from utils.http_client import HTTPClient
        client = HTTPClient()
        print("✓ HTTP client initialized successfully")
        
        # Note: We don't test actual connectivity since backend may not be running
        print("  (Backend connectivity not tested - backend may not be running)")
        
        return True
    except Exception as e:
        print(f"✗ HTTP client test failed: {e}")
        return False

def main():
    """Run all setup tests."""
    print("Advanced FinOps Platform - Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_aws_config,
        test_safety_controls,
        test_http_client
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Setup is complete.")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())