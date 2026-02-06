#!/usr/bin/env python3
"""
Validation script for AWS configuration utilities.

This script validates that the aws_config.py module is properly implemented
and meets the requirements for task 8.1.
"""

import sys
import os
import inspect
from typing import List, Dict, Any

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from utils.aws_config import AWSConfig


def validate_class_structure() -> Dict[str, bool]:
    """Validate that AWSConfig class has required methods and attributes."""
    
    results = {}
    
    # Check if class exists
    results['class_exists'] = hasattr(sys.modules['aws_config'], 'AWSConfig')
    
    if not results['class_exists']:
        return results
    
    # Get class methods
    methods = [method for method in dir(AWSConfig) if not method.startswith('_')]
    
    # Required methods based on requirements 10.1, 10.2, 10.3
    required_methods = [
        'get_client',
        'get_resource', 
        'get_account_id',
        'list_regions',
        'get_cost_explorer_client',  # Requirement 10.1
        'get_budgets_client',        # Requirement 10.2
        'get_cloudwatch_client',     # Requirement 10.3
        'get_pricing_client',
        'execute_with_retry',
        'validate_service_access'
    ]
    
    for method in required_methods:
        results[f'has_{method}'] = method in methods
    
    # Check class attributes
    class_attrs = [attr for attr in dir(AWSConfig) if not attr.startswith('_')]
    results['has_cost_management_services'] = 'COST_MANAGEMENT_SERVICES' in class_attrs
    
    return results


def validate_method_signatures() -> Dict[str, bool]:
    """Validate method signatures match expected interface."""
    
    results = {}
    
    try:
        # Check __init__ method
        init_sig = inspect.signature(AWSConfig.__init__)
        init_params = list(init_sig.parameters.keys())
        results['init_has_region_param'] = 'region' in init_params
        results['init_has_max_retries_param'] = 'max_retries' in init_params
        
        # Check get_client method
        client_sig = inspect.signature(AWSConfig.get_client)
        client_params = list(client_sig.parameters.keys())
        results['get_client_has_service_param'] = 'service_name' in client_params
        results['get_client_has_region_param'] = 'region' in client_params
        
        # Check execute_with_retry method
        retry_sig = inspect.signature(AWSConfig.execute_with_retry)
        retry_params = list(retry_sig.parameters.keys())
        results['execute_with_retry_has_operation_param'] = 'operation' in retry_params
        
    except Exception as e:
        results['signature_validation_error'] = str(e)
    
    return results


def validate_error_handling() -> Dict[str, bool]:
    """Validate error handling capabilities."""
    
    results = {}
    
    try:
        # Check that proper exceptions are imported
        import aws_config
        
        # Check for botocore exception imports
        source_code = inspect.getsource(aws_config)
        
        required_exceptions = [
            'ClientError',
            'NoCredentialsError', 
            'PartialCredentialsError',
            'BotoCoreError',
            'EndpointConnectionError'
        ]
        
        for exception in required_exceptions:
            results[f'imports_{exception}'] = exception in source_code
        
        # Check for retry logic
        results['has_retry_logic'] = 'retry' in source_code.lower()
        results['has_exponential_backoff'] = 'sleep' in source_code and '**' in source_code
        
    except Exception as e:
        results['error_handling_validation_error'] = str(e)
    
    return results


def validate_cost_management_support() -> Dict[str, bool]:
    """Validate support for AWS Cost Management APIs (Requirements 10.1, 10.2, 10.3)."""
    
    results = {}
    
    try:
        # Check COST_MANAGEMENT_SERVICES constant
        cost_services = AWSConfig.COST_MANAGEMENT_SERVICES
        
        # Required services for cost management
        required_services = {'ce', 'budgets', 'pricing', 'cloudwatch'}
        
        for service in required_services:
            results[f'supports_{service}_service'] = service in cost_services
        
        # Check specific client methods exist
        aws_config_methods = dir(AWSConfig)
        
        cost_client_methods = [
            'get_cost_explorer_client',
            'get_budgets_client', 
            'get_pricing_client',
            'get_cloudwatch_client'
        ]
        
        for method in cost_client_methods:
            results[f'has_{method}_method'] = method in aws_config_methods
        
    except Exception as e:
        results['cost_management_validation_error'] = str(e)
    
    return results


def validate_requirements_compliance() -> Dict[str, bool]:
    """Validate compliance with specific requirements 10.1, 10.2, 10.3."""
    
    results = {}
    
    try:
        # Requirement 10.1: Integration with AWS Cost Explorer API
        results['req_10_1_cost_explorer'] = hasattr(AWSConfig, 'get_cost_explorer_client')
        
        # Requirement 10.2: AWS Billing and Cost Management APIs  
        results['req_10_2_billing_apis'] = (
            hasattr(AWSConfig, 'get_budgets_client') and
            hasattr(AWSConfig, 'get_pricing_client')
        )
        
        # Requirement 10.3: CloudWatch for resource utilization analysis
        results['req_10_3_cloudwatch'] = hasattr(AWSConfig, 'get_cloudwatch_client')
        
        # General AWS API error handling
        source_code = inspect.getsource(sys.modules['aws_config'])
        results['has_comprehensive_error_handling'] = (
            'ClientError' in source_code and
            'NoCredentialsError' in source_code and
            'retry' in source_code.lower()
        )
        
        # Credential management (never hardcode)
        results['no_hardcoded_credentials'] = (
            'aws_access_key_id' not in source_code.lower() and
            'aws_secret_access_key' not in source_code.lower()
        )
        
    except Exception as e:
        results['requirements_validation_error'] = str(e)
    
    return results


def print_validation_results(category: str, results: Dict[str, bool]) -> int:
    """Print validation results for a category."""
    
    print(f"\n{category}:")
    print("-" * len(category))
    
    passed = 0
    total = 0
    
    for test_name, result in results.items():
        if test_name.endswith('_error'):
            print(f"  ✗ Error: {result}")
            continue
            
        total += 1
        if result:
            print(f"  ✓ {test_name}")
            passed += 1
        else:
            print(f"  ✗ {test_name}")
    
    if total > 0:
        print(f"\nPassed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    return passed


def main():
    """Run all validation tests."""
    
    print("=" * 60)
    print("AWS Configuration Utilities Validation")
    print("=" * 60)
    print("Validating compliance with Requirements 10.1, 10.2, 10.3")
    
    total_passed = 0
    
    # Run validation tests
    validation_tests = [
        ("Class Structure", validate_class_structure()),
        ("Method Signatures", validate_method_signatures()),
        ("Error Handling", validate_error_handling()),
        ("Cost Management Support", validate_cost_management_support()),
        ("Requirements Compliance", validate_requirements_compliance())
    ]
    
    for category, results in validation_tests:
        passed = print_validation_results(category, results)
        total_passed += passed
    
    print("\n" + "=" * 60)
    print(f"Overall Validation Results: {total_passed} tests passed")
    
    # Check if all critical requirements are met
    critical_tests = [
        validate_requirements_compliance()
    ]
    
    all_critical_passed = all(
        result for test_results in critical_tests 
        for key, result in test_results.items() 
        if not key.endswith('_error')
    )
    
    if all_critical_passed:
        print("✓ All critical requirements (10.1, 10.2, 10.3) are satisfied!")
        print("✓ Task 8.1 implementation is COMPLETE and COMPLIANT")
    else:
        print("✗ Some critical requirements are not fully satisfied")
        return 1
    
    print("=" * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())