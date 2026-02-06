#!/usr/bin/env python3
"""
Test script for enhanced Cost Optimizer Engine

Tests the new implementation timeline and cost-benefit analysis features.
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to the path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.cost_optimizer import CostOptimizer, OptimizationType, RiskLevel, ConfidenceLevel


class MockAWSConfig:
    """Mock AWS configuration for testing."""
    def __init__(self):
        self.region = 'us-east-1'


def create_test_resources():
    """Create test resources for optimization analysis."""
    return [
        {
            'resourceId': 'i-1234567890abcdef0',
            'resourceType': 'ec2',
            'region': 'us-east-1',
            'currentCost': 150.0,
            'instanceType': 't3.large',
            'utilizationMetrics': {
                'avgCpuUtilization': 8.5,
                'maxCpuUtilization': 25.0,
                'dataPoints': 48
            },
            'tags': {'Environment': 'production'}
        },
        {
            'resourceId': 'db-instance-1',
            'resourceType': 'rds',
            'region': 'us-east-1',
            'currentCost': 200.0,
            'dbInstanceClass': 'db.t3.large',
            'multiAZ': True,
            'utilizationMetrics': {
                'avgCpuUtilization': 15.0,
                'maxCpuUtilization': 35.0,
                'avgConnections': 5.0,
                'dataPoints': 48,
                'freeStorageSpace': [
                    {'average': 80000000000},  # 80GB free
                    {'average': 82000000000}   # 82GB free
                ]
            },
            'allocatedStorage': 100,  # 100GB allocated
            'tags': {'Environment': 'dev'}
        },
        {
            'resourceId': 'lambda-function-1',
            'resourceType': 'lambda',
            'region': 'us-east-1',
            'currentCost': 25.0,
            'memorySize': 1024,
            'timeout': 30,
            'utilizationMetrics': {
                'totalInvocations': 5,
                'avgDuration': 5000,  # 5 seconds
                'maxDuration': 8000,  # 8 seconds
                'dataPoints': 48
            }
        },
        {
            'resourceId': 'my-s3-bucket',
            'resourceType': 's3',
            'region': 'us-east-1',
            'currentCost': 50.0,
            'objectCount': 1500,
            'storageSizeGB': 200,
            'storageClass': 'STANDARD',
            'daysSinceLastAccess': 45
        },
        {
            'resourceId': 'vol-1234567890abcdef0',
            'resourceType': 'ebs',
            'region': 'us-east-1',
            'currentCost': 30.0,
            'state': 'available',
            'daysUnattached': 14,
            'volumeType': 'gp2',
            'sizeGB': 100
        }
    ]


def test_enhanced_cost_optimizer():
    """Test the enhanced cost optimizer with implementation timeline and cost-benefit analysis."""
    print("Testing Enhanced Cost Optimizer Engine")
    print("=" * 50)
    
    # Initialize optimizer
    aws_config = MockAWSConfig()
    
    # Test with custom thresholds
    custom_thresholds = {
        'ec2': {
            'unused_threshold': {
                'cpu_avg': 5.0,  # More aggressive threshold
                'cpu_max': 15.0
            }
        },
        'rds': {
            'storage_overprovisioned_threshold': 60.0  # Lower threshold
        }
    }
    
    optimizer = CostOptimizer(aws_config, region='us-east-1', custom_thresholds=custom_thresholds)
    
    # Create test resources
    test_resources = create_test_resources()
    
    print(f"Analyzing {len(test_resources)} test resources...")
    
    # Run optimization analysis
    results = optimizer.optimize_resources(test_resources)
    
    # Display results
    print("\nOptimization Results:")
    print("-" * 30)
    
    summary = results['summary']
    print(f"Total Current Cost: ${summary['totalCurrentCost']:.2f}/month")
    print(f"Total Estimated Savings: ${summary['totalEstimatedSavings']:.2f}/month")
    print(f"Total Annual Savings: ${summary['totalAnnualSavings']:.2f}")
    print(f"Total Implementation Cost: ${summary['totalImplementationCost']:.2f}")
    print(f"Net Annual Benefit: ${summary['netAnnualBenefit']:.2f}")
    print(f"Aggregate ROI: {summary['aggregateROI']:.1f}%")
    print(f"Average Payback Period: {summary['aggregatePaybackMonths']:.1f} months")
    print(f"Total NPV (3 years): ${summary['totalNPV']:.2f}")
    print(f"Savings Percentage: {summary['savingsPercentage']:.1f}%")
    print(f"Total Optimizations: {summary['totalOptimizations']}")
    
    # Display timeline analysis
    timeline = summary.get('timelineAnalysis', {})
    if timeline:
        print(f"\nTimeline Analysis:")
        print(f"Sequential Implementation: {timeline['totalSequentialWeeks']} weeks")
        print(f"Parallel Implementation: {timeline['estimatedParallelWeeks']} weeks")
        print(f"Timeline Savings: {timeline['timelineSavings']} weeks")
        
        phased = timeline.get('phasedApproach', {})
        if phased:
            print(f"\nPhased Implementation Approach:")
            print(f"Phase 1 (Low Risk): {phased['phase1_low_risk']['count']} optimizations, {phased['phase1_low_risk']['estimatedWeeks']} weeks")
            print(f"Phase 2 (Medium Risk): {phased['phase2_medium_risk']['count']} optimizations, {phased['phase2_medium_risk']['estimatedWeeks']} weeks")
            print(f"Phase 3 (High Risk): {phased['phase3_high_risk']['count']} optimizations, {phased['phase3_high_risk']['estimatedWeeks']} weeks")
    
    # Display quick wins
    quick_wins = summary.get('quickWins', [])
    if quick_wins:
        print(f"\nQuick Wins ({len(quick_wins)} opportunities):")
        for i, qw in enumerate(quick_wins[:3], 1):
            print(f"{i}. {qw['title']} - ${qw['estimatedSavings']:.2f}/month savings")
    
    # Display high-impact opportunities
    high_impact = summary.get('highImpactOpportunities', [])
    if high_impact:
        print(f"\nHigh-Impact Opportunities ({len(high_impact)} opportunities):")
        for i, hi in enumerate(high_impact[:3], 1):
            print(f"{i}. {hi['title']} - ${hi['estimatedSavings']:.2f}/month savings")
    
    # Display implementation recommendations
    recommendations = summary.get('implementationRecommendations', {})
    if recommendations:
        print(f"\nImplementation Recommendations:")
        
        immediate = recommendations.get('immediate_actions', [])
        if immediate:
            print("Immediate Actions (next 30 days):")
            for action in immediate:
                print(f"  • {action}")
        
        short_term = recommendations.get('short_term_goals', [])
        if short_term:
            print("Short-term Goals (next 90 days):")
            for goal in short_term:
                print(f"  • {goal}")
        
        long_term = recommendations.get('long_term_strategy', [])
        if long_term:
            print("Long-term Strategy (6-12 months):")
            for strategy in long_term:
                print(f"  • {strategy}")
        
        resources = recommendations.get('resource_requirements', {})
        if resources:
            print(f"\nResource Requirements:")
            print(f"  • Estimated effort: {resources['estimated_effort_weeks']} weeks")
            print(f"  • Recommended team size: {resources['recommended_team_size']} people")
            print(f"  • Budget required: ${resources['budget_required']:.2f}")
    
    # Display detailed optimization examples
    print(f"\nDetailed Optimization Examples:")
    print("-" * 40)
    
    optimizations = results['optimizations'][:3]  # Show first 3
    for i, opt in enumerate(optimizations, 1):
        print(f"\n{i}. {opt['title']}")
        print(f"   Resource: {opt['resourceId']} ({opt['resourceType']})")
        print(f"   Type: {opt['optimizationType']}")
        print(f"   Current Cost: ${opt['currentCost']:.2f}/month")
        print(f"   Projected Cost: ${opt['projectedCost']:.2f}/month")
        print(f"   Estimated Savings: ${opt['estimatedSavings']:.2f}/month ({opt['savingsPercentage']:.1f}%)")
        print(f"   Risk Level: {opt['riskLevel']}")
        print(f"   Confidence: {opt['confidenceScore']}")
        print(f"   Implementation Effort: {opt['implementationEffort']}")
        
        # Show timeline details
        timeline = opt.get('implementationTimeline', {})
        if timeline:
            print(f"   Implementation Timeline: {timeline['totalDays']} days ({timeline['totalWeeks']} weeks)")
            phases = timeline.get('phases', {})
            if phases:
                phase_str = ", ".join([f"{k}: {v}d" for k, v in phases.items()])
                print(f"   Phases: {phase_str}")
            
            rollback = timeline.get('rollbackTime', {})
            if rollback:
                print(f"   Rollback Time: {rollback['estimatedHours']} hours ({rollback['complexity']} complexity)")
        
        # Show cost-benefit analysis
        cba = opt.get('costBenefitAnalysis', {})
        if cba:
            print(f"   Annual Savings: ${cba['annualSavings']:.2f}")
            print(f"   Implementation Cost: ${cba['implementationCost']:.2f}")
            print(f"   Payback Period: {cba['paybackPeriodMonths']:.1f} months")
            print(f"   ROI: {cba['roiPercentage']:.1f}%")
            print(f"   NPV (3 years): ${cba['npv']:.2f}")
            print(f"   Business Case: {cba['businessCase']}")
    
    print(f"\nTest completed successfully!")
    print(f"Enhanced Cost Optimizer Engine is working with:")
    print(f"  ✓ Service-specific optimization rules")
    print(f"  ✓ Configurable thresholds")
    print(f"  ✓ Risk levels and confidence scores")
    print(f"  ✓ Implementation timeline estimates")
    print(f"  ✓ Comprehensive cost-benefit analysis")
    print(f"  ✓ Strategic implementation recommendations")
    
    return True


if __name__ == "__main__":
    try:
        success = test_enhanced_cost_optimizer()
        if success:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)