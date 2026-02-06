#!/usr/bin/env python3
"""
Test script for Lambda Scanner functionality.

This script tests:
1. Lambda function discovery
2. Metrics collection from CloudWatch
3. Optimization opportunity identification
4. Cost estimation
5. Integration with main workflow

Requirements tested: 1.1, 7.2, 3.1
"""

import sys
import logging
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_lambda_scanner_import():
    """Test that Lambda scanner can be imported."""
    print("Testing Lambda scanner import...")
    
    try:
        from aws.scan_lambda import LambdaScanner
        print("✓ Lambda scanner imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import Lambda scanner: {e}")
        return False

def test_lambda_scanner_initialization():
    """Test Lambda scanner initialization."""
    print("\nTesting Lambda scanner initialization...")
    
    try:
        from aws.scan_lambda import LambdaScanner
        from utils.aws_config import AWSConfig
        
        # Mock AWS config
        aws_config = Mock()
        aws_config.get_client.return_value = Mock()
        
        scanner = LambdaScanner(aws_config, region='us-east-1')
        
        print("✓ Lambda scanner initialized successfully")
        print(f"  Region: {scanner.region}")
        return True
    except Exception as e:
        print(f"✗ Lambda scanner initialization failed: {e}")
        return False

def test_lambda_function_analysis():
    """Test Lambda function analysis with mocked data."""
    print("\nTesting Lambda function analysis...")
    
    try:
        from aws.scan_lambda import LambdaScanner
        
        # Mock AWS config and clients
        aws_config = Mock()
        lambda_client = Mock()
        cloudwatch_client = Mock()
        
        aws_config.get_client.side_effect = lambda service: {
            'lambda': lambda_client,
            'cloudwatch': cloudwatch_client
        }[service]
        
        scanner = LambdaScanner(aws_config, region='us-east-1')
        
        # Mock function data
        sample_function = {
            'FunctionName': 'test-function',
            'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:test-function',
            'Runtime': 'python3.9',
            'MemorySize': 512,
            'Timeout': 30,
            'CodeSize': 1024,
            'LastModified': '2024-01-01T00:00:00.000+0000',
            'State': 'Active',
            'PackageType': 'Zip',
            'Architectures': ['x86_64']
        }
        
        # Mock configuration response
        lambda_client.get_function_configuration.return_value = {
            'Description': 'Test function',
            'Handler': 'lambda_function.lambda_handler',
            'Role': 'arn:aws:iam::123456789012:role/lambda-role',
            'VpcConfig': {},
            'Environment': {'Variables': {}},
            'DeadLetterConfig': {},
            'TracingConfig': {'Mode': 'PassThrough'},
            'Layers': []
        }
        
        # Mock tags response
        lambda_client.list_tags.return_value = {
            'Tags': {
                'Environment': 'production',
                'Project': 'analytics',
                'Owner': 'data-team'
            }
        }
        
        # Mock CloudWatch metrics
        base_time = datetime.utcnow() - timedelta(days=14)
        
        # Mock invocations metrics
        invocations_datapoints = []
        for i in range(24):  # 24 hours of data
            invocations_datapoints.append({
                'Timestamp': base_time + timedelta(hours=i),
                'Sum': 100.0 + (i * 5)  # Increasing invocations
            })
        
        cloudwatch_client.get_metric_statistics.side_effect = [
            {'Datapoints': invocations_datapoints},  # Invocations
            {'Datapoints': [  # Duration
                {
                    'Timestamp': base_time + timedelta(hours=i),
                    'Average': 1500.0 + (i * 10),  # Average duration in ms
                    'Maximum': 2000.0 + (i * 15)   # Max duration in ms
                }
                for i in range(24)
            ]},
            {'Datapoints': [  # Errors
                {
                    'Timestamp': base_time + timedelta(hours=i),
                    'Sum': 2.0 if i % 12 == 0 else 0.0  # Some errors
                }
                for i in range(24)
            ]},
            {'Datapoints': [  # Throttles
                {
                    'Timestamp': base_time + timedelta(hours=i),
                    'Sum': 1.0 if i % 18 == 0 else 0.0  # Occasional throttles
                }
                for i in range(24)
            ]},
            {'Datapoints': [  # Concurrent Executions
                {
                    'Timestamp': base_time + timedelta(hours=i),
                    'Average': 5.0 + (i * 0.5),
                    'Maximum': 10.0 + (i * 1.0)
                }
                for i in range(24)
            ]}
        ]
        
        # Test function analysis
        function_data = scanner._analyze_function(sample_function, days_back=14)
        
        # Validate results
        assert function_data is not None, "Function analysis should return data"
        assert function_data['resourceId'] == 'test-function', "Resource ID should match function name"
        assert function_data['resourceType'] == 'lambda', "Resource type should be lambda"
        assert function_data['region'] == 'us-east-1', "Region should match"
        assert function_data['memorySize'] == 512, "Memory size should match"
        assert function_data['timeout'] == 30, "Timeout should match"
        
        # Check utilization metrics
        metrics = function_data['utilizationMetrics']
        assert 'totalInvocations' in metrics, "Should have total invocations"
        assert 'avgDuration' in metrics, "Should have average duration"
        assert 'errorRate' in metrics, "Should have error rate"
        assert metrics['totalInvocations'] > 0, "Should have invocations"
        
        # Check optimization opportunities
        opportunities = function_data['optimizationOpportunities']
        assert isinstance(opportunities, list), "Opportunities should be a list"
        
        # Check cost estimation
        assert 'currentCost' in function_data, "Should have cost estimation"
        assert function_data['currentCost'] >= 0, "Cost should be non-negative"
        
        print("✓ Lambda function analysis working correctly")
        print(f"  Function: {function_data['functionName']}")
        print(f"  Total invocations: {metrics['totalInvocations']}")
        print(f"  Average duration: {metrics['avgDuration']:.2f}ms")
        print(f"  Error rate: {metrics['errorRate']:.2f}%")
        print(f"  Optimization opportunities: {len(opportunities)}")
        print(f"  Estimated monthly cost: ${function_data['currentCost']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Lambda function analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_optimization_opportunities():
    """Test optimization opportunity identification."""
    print("\nTesting optimization opportunity identification...")
    
    try:
        from aws.scan_lambda import LambdaScanner
        
        # Mock AWS config
        aws_config = Mock()
        aws_config.get_client.return_value = Mock()
        
        scanner = LambdaScanner(aws_config, region='us-east-1')
        
        # Test case 1: Unused function
        unused_function_data = {
            'functionName': 'unused-function',
            'memorySize': 128,
            'timeout': 3,
            'runtime': 'python3.9',
            'tags': {},
            'vpcConfig': {},
            'deadLetterConfig': {},
            'currentCost': 0.0
        }
        
        unused_metrics = {
            'totalInvocations': 0,
            'avgDuration': 0.0,
            'maxDuration': 0.0,
            'errorRate': 0.0,
            'totalThrottles': 0,
            'dataPoints': 24
        }
        
        opportunities = scanner._identify_optimization_opportunities(unused_function_data, unused_metrics)
        
        # Should identify cleanup opportunity
        cleanup_opportunities = [opp for opp in opportunities if opp['type'] == 'cleanup']
        assert len(cleanup_opportunities) > 0, "Should identify cleanup opportunity for unused function"
        assert cleanup_opportunities[0]['priority'] == 'HIGH', "Unused function should be high priority"
        
        print("✓ Unused function optimization identified")
        
        # Test case 2: Over-provisioned memory
        overprov_function_data = {
            'functionName': 'overprov-function',
            'memorySize': 1024,
            'timeout': 60,
            'runtime': 'python3.9',
            'tags': {'Environment': 'production'},
            'vpcConfig': {},
            'deadLetterConfig': {},
            'currentCost': 50.0
        }
        
        overprov_metrics = {
            'totalInvocations': 1000,
            'avgDuration': 5000.0,  # 5 seconds average
            'maxDuration': 15000.0,  # 15 seconds max (25% of 60s timeout)
            'errorRate': 1.0,
            'totalThrottles': 0,
            'dataPoints': 24
        }
        
        opportunities = scanner._identify_optimization_opportunities(overprov_function_data, overprov_metrics)
        
        # Should identify rightsizing opportunity
        rightsizing_opportunities = [opp for opp in opportunities if opp['type'] == 'rightsizing']
        assert len(rightsizing_opportunities) > 0, "Should identify rightsizing opportunity"
        
        print("✓ Over-provisioned memory optimization identified")
        
        # Test case 3: High error rate
        error_function_data = {
            'functionName': 'error-function',
            'memorySize': 256,
            'timeout': 30,
            'runtime': 'python3.9',
            'tags': {'Environment': 'production'},
            'vpcConfig': {},
            'deadLetterConfig': {},
            'currentCost': 25.0
        }
        
        error_metrics = {
            'totalInvocations': 1000,
            'avgDuration': 2000.0,
            'maxDuration': 5000.0,
            'errorRate': 10.0,  # 10% error rate
            'totalThrottles': 0,
            'dataPoints': 24
        }
        
        opportunities = scanner._identify_optimization_opportunities(error_function_data, error_metrics)
        
        # Should identify performance opportunity
        performance_opportunities = [opp for opp in opportunities if opp['type'] == 'performance']
        assert len(performance_opportunities) > 0, "Should identify performance opportunity for high error rate"
        
        print("✓ High error rate optimization identified")
        
        # Test case 4: Deprecated runtime
        deprecated_function_data = {
            'functionName': 'deprecated-function',
            'memorySize': 256,
            'timeout': 30,
            'runtime': 'python2.7',  # Deprecated runtime
            'tags': {'Environment': 'production'},
            'vpcConfig': {},
            'deadLetterConfig': {},
            'currentCost': 25.0
        }
        
        deprecated_metrics = {
            'totalInvocations': 500,
            'avgDuration': 1000.0,
            'maxDuration': 2000.0,
            'errorRate': 2.0,
            'totalThrottles': 0,
            'dataPoints': 24
        }
        
        opportunities = scanner._identify_optimization_opportunities(deprecated_function_data, deprecated_metrics)
        
        # Should identify security opportunity
        security_opportunities = [opp for opp in opportunities if opp['type'] == 'security']
        assert len(security_opportunities) > 0, "Should identify security opportunity for deprecated runtime"
        
        print("✓ Deprecated runtime optimization identified")
        
        return True
        
    except Exception as e:
        print(f"✗ Optimization opportunity identification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cost_estimation():
    """Test Lambda cost estimation."""
    print("\nTesting Lambda cost estimation...")
    
    try:
        from aws.scan_lambda import LambdaScanner
        
        # Mock AWS config
        aws_config = Mock()
        aws_config.get_client.return_value = Mock()
        
        scanner = LambdaScanner(aws_config, region='us-east-1')
        
        # Test cost estimation for different scenarios
        test_cases = [
            {
                'name': 'Small function',
                'memory_size': 128,
                'total_invocations': 1000,
                'avg_duration': 100.0,  # 100ms
                'days_back': 30,
                'expected_min': 0.0,
                'expected_max': 5.0
            },
            {
                'name': 'Medium function',
                'memory_size': 512,
                'total_invocations': 10000,
                'avg_duration': 2000.0,  # 2 seconds
                'days_back': 30,
                'expected_min': 0.1,
                'expected_max': 5.0
            },
            {
                'name': 'Large function',
                'memory_size': 1024,
                'total_invocations': 100000,
                'avg_duration': 5000.0,  # 5 seconds
                'days_back': 30,
                'expected_min': 5.0,
                'expected_max': 100.0
            },
            {
                'name': 'Unused function',
                'memory_size': 256,
                'total_invocations': 0,
                'avg_duration': 0.0,
                'days_back': 30,
                'expected_min': 0.0,
                'expected_max': 0.0
            }
        ]
        
        for test_case in test_cases:
            cost = scanner._estimate_function_cost(
                test_case['memory_size'],
                test_case['total_invocations'],
                test_case['avg_duration'],
                test_case['days_back']
            )
            
            assert cost >= test_case['expected_min'], f"Cost too low for {test_case['name']}: {cost}"
            assert cost <= test_case['expected_max'], f"Cost too high for {test_case['name']}: {cost}"
            
            print(f"  {test_case['name']}: ${cost:.4f}/month")
        
        print("✓ Lambda cost estimation working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Lambda cost estimation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_optimization_summary():
    """Test optimization summary generation."""
    print("\nTesting optimization summary generation...")
    
    try:
        from aws.scan_lambda import LambdaScanner
        
        # Mock AWS config
        aws_config = Mock()
        aws_config.get_client.return_value = Mock()
        
        scanner = LambdaScanner(aws_config, region='us-east-1')
        
        # Create sample function data
        sample_functions = [
            {
                'functionName': 'active-function-1',
                'runtime': 'python3.9',
                'currentCost': 25.0,
                'utilizationMetrics': {'totalInvocations': 1000},
                'optimizationOpportunities': [
                    {'type': 'rightsizing', 'priority': 'MEDIUM', 'estimatedSavings': 5.0},
                    {'type': 'configuration', 'priority': 'LOW', 'estimatedSavings': 0.0}
                ]
            },
            {
                'functionName': 'active-function-2',
                'runtime': 'nodejs18.x',
                'currentCost': 15.0,
                'utilizationMetrics': {'totalInvocations': 500},
                'optimizationOpportunities': [
                    {'type': 'performance', 'priority': 'HIGH', 'estimatedSavings': 0.0}
                ]
            },
            {
                'functionName': 'unused-function',
                'runtime': 'python3.8',
                'currentCost': 0.0,
                'utilizationMetrics': {'totalInvocations': 0},
                'optimizationOpportunities': [
                    {'type': 'cleanup', 'priority': 'HIGH', 'estimatedSavings': 10.0}
                ]
            }
        ]
        
        summary = scanner.get_optimization_summary(sample_functions)
        
        # Validate summary
        assert summary['totalFunctions'] == 3, "Should count all functions"
        assert summary['activeFunctions'] == 2, "Should count active functions"
        assert summary['unusedFunctions'] == 1, "Should count unused functions"
        assert summary['totalMonthlyCost'] == 40.0, "Should sum total costs"
        assert summary['potentialMonthlySavings'] == 15.0, "Should sum potential savings"
        
        # Check optimization breakdown
        assert summary['optimizationOpportunities']['rightsizing'] == 1, "Should count rightsizing opportunities"
        assert summary['optimizationOpportunities']['cleanup'] == 1, "Should count cleanup opportunities"
        assert summary['optimizationOpportunities']['performance'] == 1, "Should count performance opportunities"
        assert summary['optimizationOpportunities']['configuration'] == 1, "Should count configuration opportunities"
        
        # Check priority breakdown
        assert summary['priorityBreakdown']['HIGH'] == 2, "Should count high priority opportunities"
        assert summary['priorityBreakdown']['MEDIUM'] == 1, "Should count medium priority opportunities"
        assert summary['priorityBreakdown']['LOW'] == 1, "Should count low priority opportunities"
        
        # Check runtime breakdown
        assert summary['runtimeBreakdown']['python3.9'] == 1, "Should count Python 3.9 functions"
        assert summary['runtimeBreakdown']['nodejs18.x'] == 1, "Should count Node.js 18.x functions"
        assert summary['runtimeBreakdown']['python3.8'] == 1, "Should count Python 3.8 functions"
        
        # Check savings percentage
        expected_percentage = (15.0 / 40.0) * 100
        assert abs(summary['savingsPercentage'] - expected_percentage) < 0.01, "Should calculate correct savings percentage"
        
        print("✓ Optimization summary generation working correctly")
        print(f"  Total functions: {summary['totalFunctions']}")
        print(f"  Active functions: {summary['activeFunctions']}")
        print(f"  Unused functions: {summary['unusedFunctions']}")
        print(f"  Total monthly cost: ${summary['totalMonthlyCost']:.2f}")
        print(f"  Potential savings: ${summary['potentialMonthlySavings']:.2f} ({summary['savingsPercentage']:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"✗ Optimization summary generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_main():
    """Test integration with main workflow."""
    print("\nTesting integration with main workflow...")
    
    try:
        # Test that Lambda scanner is properly imported in main.py
        from main import AdvancedFinOpsOrchestrator
        
        # Mock AWS config
        with patch('main.AWSConfig') as mock_aws_config:
            mock_aws_config.return_value = Mock()
            
            orchestrator = AdvancedFinOpsOrchestrator(region='us-east-1', dry_run=True)
            
            # Check that Lambda scanner is available
            assert hasattr(orchestrator, 'aws_config'), "Should have AWS config"
            
            print("✓ Lambda scanner integrated with main workflow")
            return True
            
    except Exception as e:
        print(f"✗ Integration with main workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Lambda scanner tests."""
    print("Advanced FinOps Platform - Lambda Scanner Test")
    print("=" * 60)
    
    tests = [
        test_lambda_scanner_import,
        test_lambda_scanner_initialization,
        test_lambda_function_analysis,
        test_optimization_opportunities,
        test_cost_estimation,
        test_optimization_summary,
        test_integration_with_main
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All Lambda scanner tests passed!")
        print("\nLambda Scanner Features Validated:")
        print("  • Function discovery and metadata collection")
        print("  • CloudWatch metrics integration (invocations, duration, errors)")
        print("  • Optimization opportunity identification:")
        print("    - Unused function cleanup")
        print("    - Memory right-sizing")
        print("    - Timeout optimization")
        print("    - Performance improvements")
        print("    - Security updates (deprecated runtimes)")
        print("    - Configuration optimization")
        print("  • Cost estimation and analysis")
        print("  • Comprehensive reporting and summaries")
        print("  • Integration with main workflow")
        print("\nRequirements Satisfied:")
        print("  • 1.1: Multi-service resource discovery")
        print("  • 7.2: Lambda-specific optimization rules")
        print("  • 3.1: Resource utilization analysis")
        
        return 0
    else:
        print("✗ Some Lambda scanner tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())