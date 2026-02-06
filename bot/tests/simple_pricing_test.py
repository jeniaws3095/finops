#!/usr/bin/env python3
"""
Simple test for Pricing Intelligence Engine
"""

import sys
import os

# Add the current directory to Python path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

try:
    from core.pricing_intelligence import PricingIntelligenceEngine, PricingStrategy
    from utils.aws_config import AWSConfig
    
    print("✓ Successfully imported pricing intelligence engine")
    
    # Initialize engine
    aws_config = AWSConfig()
    engine = PricingIntelligenceEngine(aws_config, region='us-east-1')
    print("✓ Successfully initialized pricing intelligence engine")
    
    # Test with sample data
    sample_resources = [
        {
            'resourceId': 'i-1234567890abcdef0',
            'resourceType': 'ec2',
            'instanceType': 't3.medium',
            'currentCost': 30.0,
            'utilizationMetrics': {
                'avgCpuUtilization': 75.0,
                'dataPoints': 90,
                'runtimeHours': 720,
                'cpuUtilizationHistory': [70, 75, 80, 72, 78]
            },
            'tags': {'Environment': 'production', 'Name': 'web-server'}
        }
    ]
    
    # Run analysis
    result = engine.analyze_pricing_opportunities(sample_resources)
    print("✓ Successfully ran pricing analysis")
    
    # Verify results
    assert 'summary' in result
    assert 'recommendations' in result
    assert 'reservedInstanceRecommendations' in result
    assert 'spotInstanceRecommendations' in result
    assert 'savingsPlansRecommendations' in result
    assert 'regionalOptimizationRecommendations' in result
    
    print("✓ All result fields present")
    print(f"✓ Generated {result['totalRecommendations']} total recommendations")
    print(f"✓ Potential monthly savings: ${result['summary']['totalPotentialMonthlySavings']:.2f}")
    
    print("\n🎉 Pricing Intelligence Engine test completed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)