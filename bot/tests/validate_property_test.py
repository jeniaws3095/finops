#!/usr/bin/env python3
"""
Validation script for pricing intelligence property test
"""

import sys
import os

# Add the current directory to Python path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

try:
    from core.pricing_intelligence import PricingIntelligenceEngine
    from utils.aws_config import AWSConfig
    
    print("✓ Successfully imported pricing intelligence engine")
    
    # Test basic functionality
    aws_config = AWSConfig()
    engine = PricingIntelligenceEngine(aws_config, region='us-east-1')
    
    print("✓ Successfully initialized pricing intelligence engine")
    
    # Test with sample data
    test_resources = [
        {
            'resourceId': 'i-test123',
            'resourceType': 'ec2',
            'instanceType': 't3.medium',
            'currentCost': 50.0,
            'utilizationMetrics': {
                'avgCpuUtilization': 75.0,
                'dataPoints': 120,
                'runtimeHours': 720,
                'cpuUtilizationHistory': [70, 75, 80, 72, 78]
            },
            'tags': {'Environment': 'production', 'Name': 'web-server'},
            'storageSizeGB': 100,
            'costHistory': [48, 50, 52, 49, 51]
        }
    ]
    
    result = engine.analyze_pricing_opportunities(test_resources)
    
    print("✓ Successfully analyzed pricing opportunities")
    print(f"  - Total recommendations: {result.get('totalRecommendations', 0)}")
    print(f"  - RI recommendations: {len(result.get('reservedInstanceRecommendations', []))}")
    print(f"  - Spot recommendations: {len(result.get('spotInstanceRecommendations', []))}")
    print(f"  - SP recommendations: {len(result.get('savingsPlansRecommendations', []))}")
    
    # Validate basic property requirements
    required_keys = [
        'summary', 'recommendations', 'reservedInstanceRecommendations',
        'spotInstanceRecommendations', 'savingsPlansRecommendations',
        'regionalOptimizationRecommendations', 'totalRecommendations',
        'timestamp', 'region'
    ]
    
    for key in required_keys:
        if key not in result:
            print(f"❌ Missing required key: {key}")
            sys.exit(1)
    
    print("✓ All required keys present in result")
    
    # Validate recommendation structure
    all_recommendations = result['recommendations']
    for i, rec in enumerate(all_recommendations):
        required_fields = [
            'recommendationId', 'strategy', 'title', 'description',
            'currentMonthlyCost', 'projectedMonthlyCost', 'estimatedMonthlySavings',
            'confidenceScore', 'riskLevel', 'timestamp'
        ]
        
        for field in required_fields:
            if field not in rec:
                print(f"❌ Recommendation {i} missing field: {field}")
                sys.exit(1)
        
        # Validate confidence score
        confidence = rec['confidenceScore']
        if not (0 <= confidence <= 100):
            print(f"❌ Invalid confidence score: {confidence}")
            sys.exit(1)
        
        # Validate risk level
        if rec['riskLevel'] not in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            print(f"❌ Invalid risk level: {rec['riskLevel']}")
            sys.exit(1)
    
    print(f"✓ All {len(all_recommendations)} recommendations have valid structure")
    
    print("\n✅ Property test validation completed successfully!")
    print("The pricing intelligence engine generates complete recommendations")
    print("with confidence scores, risk assessments, and ROI calculations.")
    
except Exception as e:
    print(f"❌ Validation failed: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)