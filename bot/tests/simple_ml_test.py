#!/usr/bin/env python3
"""
Simple test for ML Right-Sizing Engine to verify core functionality
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.ml_rightsizing import MLRightSizingEngine
from utils.aws_config import AWSConfig


def test_ml_rightsizing_basic():
    """Test basic ML right-sizing functionality."""
    print("Testing ML Right-Sizing Engine...")
    
    # Initialize engine
    aws_config = AWSConfig()
    engine = MLRightSizingEngine(aws_config, region='us-east-1')
    print("✓ Engine initialized")
    
    # Create test resource with sufficient historical data
    test_resource = {
        'resourceId': 'i-test123',
        'resourceType': 'ec2',
        'instanceType': 't3.medium',
        'currentCost': 60.0,
        'utilizationMetrics': {
            'cpuUtilizationHistory': [25, 30, 28, 32, 27, 29, 31, 26, 33, 28] * 20,  # 200 data points
            'memoryUtilizationHistory': [40, 45, 42, 48, 41, 44, 46, 39, 49, 43] * 20,
            'networkInHistory': [100, 120, 110, 130, 105, 115, 125, 95, 135, 108] * 20,
            'networkOutHistory': [80, 90, 85, 95, 82, 88, 92, 78, 98, 86] * 20,
            'diskReadOpsHistory': [50, 60, 55, 65, 52, 58, 62, 48, 68, 56] * 20,
            'diskWriteOpsHistory': [30, 40, 35, 45, 32, 38, 42, 28, 48, 36] * 20,
            'diskReadBytesHistory': [1000, 1200, 1100, 1300, 1050, 1150, 1250, 950, 1350, 1080] * 20,
            'diskWriteBytesHistory': [800, 900, 850, 950, 820, 880, 920, 780, 980, 860] * 20,
            'timestamps': [(datetime.utcnow() - timedelta(hours=i)).isoformat() for i in range(200, 0, -1)],
            'dataPoints': 200
        },
        'tags': {'Environment': 'production', 'Name': 'web-server'}
    }
    
    # Test ML analysis
    result = engine.analyze_rightsizing_opportunities([test_resource])
    print("✓ ML analysis completed")
    
    # Verify result structure
    assert 'summary' in result
    assert 'recommendations' in result
    assert 'mlModelsUsed' in result
    assert 'analysisTimestamp' in result
    print("✓ Result structure validated")
    
    # Check recommendations if any were generated
    recommendations = result['recommendations']
    if recommendations:
        rec = recommendations[0]
        
        # Verify ML-specific fields
        assert 'confidenceAnalysis' in rec
        assert 'mlDetails' in rec
        assert 'costAnalysis' in rec
        assert 'performanceImpact' in rec
        
        # Verify confidence analysis
        confidence_analysis = rec['confidenceAnalysis']
        assert 'overall_confidence' in confidence_analysis
        assert 'confidence_level' in confidence_analysis
        assert 'confidence_interval' in confidence_analysis
        
        # Verify confidence interval structure
        confidence_interval = confidence_analysis['confidence_interval']
        assert 'lower' in confidence_interval
        assert 'upper' in confidence_interval
        assert confidence_interval['lower'] >= 0
        assert confidence_interval['upper'] > confidence_interval['lower']
        
        print("✓ ML recommendation structure validated")
        print(f"  - Confidence Level: {confidence_analysis['confidence_level']}")
        print(f"  - Overall Confidence: {confidence_analysis['overall_confidence']:.1f}%")
        print(f"  - Confidence Interval: [{confidence_interval['lower']:.1f}, {confidence_interval['upper']:.1f}]")
        
        # Verify ML details
        ml_details = rec['mlDetails']
        assert 'modelsUsed' in ml_details
        assert 'predictions' in ml_details
        assert 'optimalConfig' in ml_details
        
        print(f"  - ML Models Used: {ml_details['modelsUsed']}")
        print(f"  - Predictions: {len(ml_details['predictions'])} models")
        
        # Verify cost analysis
        cost_analysis = rec['costAnalysis']
        assert 'monthly_savings' in cost_analysis
        assert 'annual_savings' in cost_analysis
        assert 'savings_percentage' in cost_analysis
        
        print(f"  - Monthly Savings: ${cost_analysis['monthly_savings']:.2f}")
        print(f"  - Annual Savings: ${cost_analysis['annual_savings']:.2f}")
        print(f"  - Savings Percentage: {cost_analysis['savings_percentage']:.1f}%")
        
        print("✓ All ML recommendation properties validated")
    else:
        print("ℹ No recommendations generated (resource may already be optimally sized)")
    
    print("\n✅ ML Right-Sizing Engine test completed successfully!")
    return True


if __name__ == '__main__':
    try:
        test_ml_rightsizing_basic()
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)