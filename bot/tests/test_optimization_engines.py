#!/usr/bin/env python3
"""
Test script to verify the core optimization engines are working properly.
"""

from core.cost_optimizer import CostOptimizer
from core.pricing_intelligence import PricingIntelligenceEngine
from core.ml_rightsizing import MLRightSizingEngine
import json

print('Testing Core Optimization Engines...')
print('=' * 50)

# Initialize AWS config (mock)
class MockAWSConfig:
    def __init__(self):
        self.region = 'us-east-1'
    
    def get_client(self, service):
        return None

aws_config = MockAWSConfig()

# Test Cost Optimizer Engine
print('1. Testing Cost Optimizer Engine...')
try:
    cost_optimizer = CostOptimizer(aws_config, region='us-east-1')
    
    # Test with sample resources
    sample_resources = [
        {
            'resourceId': 'i-1234567890abcdef0',
            'resourceType': 'ec2',
            'instanceType': 't3.medium',
            'currentCost': 50.0,
            'utilizationMetrics': {
                'avgCpuUtilization': 1.5,
                'maxCpuUtilization': 8.0,
                'dataPoints': 168
            }
        },
        {
            'resourceId': 'db-instance-1',
            'resourceType': 'rds',
            'dbInstanceClass': 'db.t3.medium',
            'currentCost': 80.0,
            'utilizationMetrics': {
                'avgCpuUtilization': 3.0,
                'maxCpuUtilization': 15.0,
                'avgConnections': 0.5,
                'dataPoints': 168
            }
        }
    ]
    
    result = cost_optimizer.optimize_resources(sample_resources)
    print(f'   ✓ Cost Optimizer working: {result["totalOptimizations"]} optimizations generated')
    print(f'   ✓ Total potential savings: ${result["summary"]["totalEstimatedSavings"]:.2f}/month')
    
except Exception as e:
    print(f'   ✗ Cost Optimizer failed: {e}')

print()

# Test Pricing Intelligence Engine
print('2. Testing Pricing Intelligence Engine...')
try:
    pricing_engine = PricingIntelligenceEngine(aws_config, region='us-east-1')
    
    # Test with sample resources
    sample_resources = [
        {
            'resourceId': 'i-1234567890abcdef0',
            'resourceType': 'ec2',
            'instanceType': 't3.medium',
            'currentCost': 50.0,
            'utilizationMetrics': {
                'avgCpuUtilization': 75.0,
                'runtimeHours': 720,
                'dataPoints': 168,
                'cpuUtilizationHistory': [70, 75, 80, 72, 78] * 33  # 165 data points
            }
        }
    ]
    
    result = pricing_engine.analyze_pricing_opportunities(sample_resources)
    print(f'   ✓ Pricing Intelligence working: {result["totalRecommendations"]} recommendations generated')
    print(f'   ✓ Strategies analyzed: {len(result["summary"]["strategyBreakdown"])} pricing strategies')
    
except Exception as e:
    print(f'   ✗ Pricing Intelligence failed: {e}')

print()

# Test ML Right-Sizing Engine
print('3. Testing ML Right-Sizing Engine...')
try:
    ml_engine = MLRightSizingEngine(aws_config, region='us-east-1')
    
    # Test with sample resources with historical data
    sample_resources = [
        {
            'resourceId': 'i-1234567890abcdef0',
            'resourceType': 'ec2',
            'instanceType': 't3.medium',
            'currentCost': 50.0,
            'utilizationMetrics': {
                'cpuUtilizationHistory': [20, 25, 30, 22, 28] * 50,  # 250 data points
                'memoryUtilizationHistory': [40, 45, 50, 42, 48] * 50,
                'networkInHistory': [100, 120, 110, 105, 115] * 50,
                'networkOutHistory': [80, 90, 85, 82, 88] * 50,
                'timestamps': [f'2024-01-{i//24+1:02d}T{i%24:02d}:00:00' for i in range(250)],
                'dataPoints': 250,
                'avgCpuUtilization': 25.0,
                'maxCpuUtilization': 35.0,
                'cpu_variance': 15.0,
                'dataAgeDays': 10
            }
        }
    ]
    
    result = ml_engine.analyze_rightsizing_opportunities(sample_resources)
    print(f'   ✓ ML Right-Sizing working: {result["summary"]["recommendationsGenerated"]} recommendations generated')
    print(f'   ✓ Resources analyzed: {result["summary"]["analyzedResources"]}')
    print(f'   ✓ High confidence recommendations: {result["summary"]["highConfidenceRecommendations"]}')
    
except Exception as e:
    print(f'   ✗ ML Right-Sizing failed: {e}')

print()
print('=' * 50)
print('Core Optimization Engines Test Complete!')