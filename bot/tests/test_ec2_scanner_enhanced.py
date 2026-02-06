#!/usr/bin/env python3
"""
Unit tests for enhanced EC2 Scanner functionality.

Tests the new features added for task 4.1:
- Configurable time ranges
- Memory metrics collection
- Regional cost comparison
- Enhanced instance type analysis
- Intelligent recommendations
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from aws.scan_ec2 import EC2Scanner


class TestEnhancedEC2Scanner(unittest.TestCase):
    """Test cases for enhanced EC2 Scanner functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock AWS config
        self.mock_aws_config = Mock()
        self.mock_ec2_client = Mock()
        self.mock_cloudwatch_client = Mock()
        self.mock_pricing_client = Mock()
        
        self.mock_aws_config.get_client.side_effect = lambda service, region=None: {
            'ec2': self.mock_ec2_client,
            'cloudwatch': self.mock_cloudwatch_client,
            'pricing': self.mock_pricing_client
        }.get(service)
        
        # Custom thresholds for testing
        self.custom_thresholds = {
            'unused_cpu_avg': 1.5,
            'underutilized_cpu_avg': 8.0,
            'minimum_data_points': 12,
            'unused_memory_avg': 15.0,
            'underutilized_memory_avg': 35.0
        }
        
        self.scanner = EC2Scanner(
            self.mock_aws_config, 
            region='us-east-1', 
            thresholds=self.custom_thresholds
        )
    
    def test_scanner_initialization_with_custom_thresholds(self):
        """Test scanner initialization with custom thresholds."""
        self.assertEqual(self.scanner.region, 'us-east-1')
        self.assertEqual(self.scanner.thresholds['unused_cpu_avg'], 1.5)
        self.assertEqual(self.scanner.thresholds['underutilized_cpu_avg'], 8.0)
        self.assertEqual(self.scanner.thresholds['minimum_data_points'], 12)
        
        # Test default thresholds are preserved
        self.assertIn('network_threshold_mb', self.scanner.thresholds)
    
    def test_get_instance_specifications(self):
        """Test instance specifications retrieval."""
        # Test known instance type
        specs = self.scanner._get_instance_specifications('t3.large')
        expected = {
            'vcpus': 2, 
            'memory_gb': 8, 
            'network': 'Up to 5 Gigabit', 
            'family': 'general_purpose'
        }
        self.assertEqual(specs, expected)
        
        # Test unknown instance type
        specs = self.scanner._get_instance_specifications('unknown.type')
        self.assertEqual(specs['vcpus'], 'unknown')
        self.assertEqual(specs['family'], 'unknown')
    
    def test_enhanced_cost_estimation(self):
        """Test enhanced cost estimation with multiple platforms."""
        # Test Linux pricing
        linux_cost = self.scanner._estimate_instance_cost('t3.large', 'linux')
        self.assertEqual(linux_cost, 60.74)
        
        # Test Windows pricing (should be 1.5x)
        windows_cost = self.scanner._estimate_instance_cost('t3.large', 'windows')
        self.assertEqual(windows_cost, 91.11)  # 60.74 * 1.5
        
        # Test RHEL pricing (should be 1.2x)
        rhel_cost = self.scanner._estimate_instance_cost('t3.large', 'rhel')
        self.assertEqual(rhel_cost, 72.89)  # 60.74 * 1.2 rounded
        
        # Test unknown instance type (should use default)
        unknown_cost = self.scanner._estimate_instance_cost('unknown.type', 'linux')
        self.assertEqual(unknown_cost, 100.0)
    
    def test_regional_cost_comparison(self):
        """Test regional cost comparison functionality."""
        regional_costs = self.scanner._get_regional_cost_comparison('t3.large', 'linux')
        
        # Should return costs for multiple regions
        self.assertGreater(len(regional_costs), 5)
        
        # Check specific regions exist
        self.assertIn('us-east-1', regional_costs)
        self.assertIn('us-west-2', regional_costs)
        self.assertIn('eu-west-1', regional_costs)
        
        # Check cost structure
        us_east_cost = regional_costs['us-east-1']
        self.assertIn('monthlyCost', us_east_cost)
        self.assertIn('multiplier', us_east_cost)
        self.assertIn('currency', us_east_cost)
        
        # us-east-1 should be base cost (multiplier = 1.0)
        self.assertEqual(us_east_cost['multiplier'], 1.0)
        self.assertEqual(us_east_cost['monthlyCost'], 60.74)
    
    def test_intelligent_instance_recommendation(self):
        """Test intelligent instance type recommendations."""
        # Test downsizing recommendation (low utilization)
        recommendation = self.scanner._get_intelligent_instance_recommendation(
            't3.xlarge', 15.0, 25.0, 30.0
        )
        self.assertEqual(recommendation, 't3.large')  # Should downsize
        
        # Test no change recommendation (adequate utilization)
        recommendation = self.scanner._get_intelligent_instance_recommendation(
            't3.large', 45.0, 60.0, 50.0
        )
        self.assertEqual(recommendation, 't3.large')  # Should stay same
        
        # Test memory-optimized instance with low memory usage
        recommendation = self.scanner._get_intelligent_instance_recommendation(
            'r5.large', 30.0, 40.0, 15.0  # Low memory usage
        )
        self.assertEqual(recommendation, 'm5.large')  # Should switch to general purpose
    
    def test_comprehensive_cost_analysis(self):
        """Test comprehensive cost analysis with regional comparison."""
        cost_analysis = self.scanner._get_comprehensive_cost_analysis(
            't3.large', 'linux', include_regional_comparison=True
        )
        
        # Check basic cost data
        self.assertEqual(cost_analysis['currentCost'], 60.74)
        self.assertEqual(cost_analysis['platform'], 'linux')
        self.assertEqual(cost_analysis['instanceType'], 't3.large')
        self.assertEqual(cost_analysis['region'], 'us-east-1')
        
        # Check regional comparison data
        self.assertIn('regionalComparison', cost_analysis)
        self.assertIn('cheapestRegion', cost_analysis)
        
        cheapest = cost_analysis['cheapestRegion']
        self.assertIn('region', cheapest)
        self.assertIn('monthlyCost', cheapest)
        self.assertIn('potentialSavings', cheapest)
    
    def test_enhanced_optimization_opportunities_unused_instance(self):
        """Test identification of unused instances with enhanced thresholds."""
        instance_data = {
            'resourceId': 'i-1234567890abcdef0',
            'instanceType': 't3.large',
            'currentCost': 60.74,
            'tags': {'Environment': 'test'}
        }
        
        # Metrics showing unused instance (below custom thresholds)
        metrics = {
            'avgCpuUtilization': 1.0,  # Below custom threshold of 1.5
            'maxCpuUtilization': 5.0,  # Below threshold of 10.0
            'avgMemoryUtilization': 10.0,  # Below custom threshold of 15.0
            'dataPoints': 24,  # Sufficient data
            'memoryDataAvailable': True
        }
        
        opportunities = self.scanner._identify_enhanced_optimization_opportunities(
            instance_data, metrics
        )
        
        # Should identify as cleanup opportunity
        cleanup_ops = [op for op in opportunities if op['type'] == 'cleanup']
        self.assertEqual(len(cleanup_ops), 1)
        
        cleanup_op = cleanup_ops[0]
        self.assertEqual(cleanup_op['priority'], 'HIGH')
        self.assertEqual(cleanup_op['confidence'], 'VERY_HIGH')  # Both CPU and memory low
        self.assertEqual(cleanup_op['action'], 'terminate')
        self.assertAlmostEqual(cleanup_op['estimatedSavings'], 60.74 * 0.95, places=2)
    
    def test_enhanced_optimization_opportunities_underutilized_instance(self):
        """Test identification of underutilized instances."""
        instance_data = {
            'resourceId': 'i-1234567890abcdef0',
            'instanceType': 't3.xlarge',
            'currentCost': 121.47,
            'tags': {'Environment': 'production'}
        }
        
        # Metrics showing underutilized instance
        metrics = {
            'avgCpuUtilization': 6.0,  # Below custom threshold of 8.0
            'maxCpuUtilization': 20.0,  # Below threshold of 30.0
            'avgMemoryUtilization': 25.0,  # Below custom threshold of 35.0
            'dataPoints': 48,  # Sufficient data
            'memoryDataAvailable': True,
            'cpuUtilizationStdDev': 3.0
        }
        
        opportunities = self.scanner._identify_enhanced_optimization_opportunities(
            instance_data, metrics
        )
        
        # Should identify as rightsizing opportunity
        rightsizing_ops = [op for op in opportunities if op['type'] == 'rightsizing']
        self.assertEqual(len(rightsizing_ops), 1)
        
        rightsizing_op = rightsizing_ops[0]
        self.assertEqual(rightsizing_op['priority'], 'MEDIUM')
        self.assertEqual(rightsizing_op['confidence'], 'HIGH')  # Both CPU and memory low
        self.assertEqual(rightsizing_op['action'], 'downsize')
        self.assertEqual(rightsizing_op['recommendedInstanceType'], 't3.large')
    
    def test_enhanced_optimization_opportunities_spot_candidate(self):
        """Test identification of Spot instance candidates."""
        instance_data = {
            'resourceId': 'i-1234567890abcdef0',
            'instanceType': 't3.large',
            'currentCost': 60.74,
            'tags': {'Environment': 'development'}
        }
        
        # Metrics showing stable workload suitable for Spot
        metrics = {
            'avgCpuUtilization': 25.0,  # Moderate usage
            'maxCpuUtilization': 45.0,  # Below 80% threshold
            'cpuUtilizationStdDev': 8.0,  # Low variability (< 15.0)
            'dataPoints': 72,  # Sufficient data
            'memoryDataAvailable': False
        }
        
        opportunities = self.scanner._identify_enhanced_optimization_opportunities(
            instance_data, metrics
        )
        
        # Should identify as pricing opportunity (Spot)
        pricing_ops = [op for op in opportunities if op['type'] == 'pricing' and op['action'] == 'convert_to_spot']
        self.assertEqual(len(pricing_ops), 1)
        
        spot_op = pricing_ops[0]
        self.assertEqual(spot_op['priority'], 'LOW')
        self.assertEqual(spot_op['confidence'], 'MEDIUM')
        self.assertAlmostEqual(spot_op['estimatedSavings'], 60.74 * 0.7, places=2)
    
    def test_governance_opportunities(self):
        """Test identification of governance opportunities."""
        instance_data = {
            'resourceId': 'i-1234567890abcdef0',
            'instanceType': 't3.large',
            'launchTime': (datetime.utcnow() - timedelta(days=400)).isoformat(),  # Old instance
            'tags': {'Environment': 'production'}  # Missing required tags
        }
        
        opportunities = self.scanner._identify_governance_opportunities(instance_data)
        
        # Should identify missing tags
        tag_ops = [op for op in opportunities if op['action'] == 'add_tags']
        self.assertEqual(len(tag_ops), 1)
        
        tag_op = tag_ops[0]
        self.assertIn('Project', tag_op['missingTags'])
        self.assertIn('Owner', tag_op['missingTags'])
        self.assertIn('CostCenter', tag_op['missingTags'])
        
        # Should identify old instance
        age_ops = [op for op in opportunities if op['action'] == 'review_age']
        self.assertEqual(len(age_ops), 1)
        
        age_op = age_ops[0]
        self.assertGreater(age_op['ageDays'], 365)
    
    def test_enhanced_optimization_summary(self):
        """Test enhanced optimization summary generation."""
        # Create sample instances with various optimization opportunities
        instances = [
            {
                'resourceId': 'i-unused',
                'instanceType': 't3.large',
                'state': 'running',
                'currentCost': 60.74,
                'cheapestRegion': {'region': 'us-east-2', 'potentialSavings': 5.0},
                'utilizationMetrics': {'avgCpuUtilization': 1.0, 'avgMemoryUtilization': 8.0, 'memoryDataAvailable': True},
                'optimizationOpportunities': [
                    {'type': 'cleanup', 'priority': 'HIGH', 'confidence': 'VERY_HIGH', 'riskLevel': 'LOW', 'estimatedSavings': 57.70}
                ]
            },
            {
                'resourceId': 'i-underutilized',
                'instanceType': 'm5.xlarge',
                'state': 'running',
                'currentCost': 175.20,
                'cheapestRegion': {'region': 'us-east-2', 'potentialSavings': 10.0},
                'utilizationMetrics': {'avgCpuUtilization': 7.0, 'avgMemoryUtilization': 30.0, 'memoryDataAvailable': True},
                'optimizationOpportunities': [
                    {'type': 'rightsizing', 'priority': 'MEDIUM', 'confidence': 'HIGH', 'riskLevel': 'MEDIUM', 'estimatedSavings': 52.56}
                ]
            }
        ]
        
        summary = self.scanner.get_enhanced_optimization_summary(instances)
        
        # Check basic counts
        self.assertEqual(summary['totalInstances'], 2)
        self.assertEqual(summary['runningInstances'], 2)
        self.assertEqual(summary['totalMonthlyCost'], 235.94)
        self.assertEqual(summary['potentialMonthlySavings'], 110.26)
        self.assertEqual(summary['regionalSavingsOpportunity'], 15.0)
        
        # Check optimization breakdown
        self.assertEqual(summary['optimizationOpportunities']['cleanup'], 1)
        self.assertEqual(summary['optimizationOpportunities']['rightsizing'], 1)
        
        # Check priority breakdown
        self.assertEqual(summary['priorityBreakdown']['HIGH'], 1)
        self.assertEqual(summary['priorityBreakdown']['MEDIUM'], 1)
        
        # Check confidence breakdown
        self.assertEqual(summary['confidenceBreakdown']['VERY_HIGH'], 1)
        self.assertEqual(summary['confidenceBreakdown']['HIGH'], 1)
        
        # Check utilization stats
        self.assertEqual(summary['utilizationStats']['avgCpuUtilization'], 4.0)  # (1.0 + 7.0) / 2
        self.assertEqual(summary['utilizationStats']['avgMemoryUtilization'], 19.0)  # (8.0 + 30.0) / 2
        self.assertEqual(summary['utilizationStats']['instancesWithMemoryData'], 2)
        self.assertEqual(summary['utilizationStats']['unusedInstances'], 1)
        self.assertEqual(summary['utilizationStats']['underutilizedInstances'], 1)
        
        # Check savings percentages
        self.assertAlmostEqual(summary['savingsPercentage'], 46.73, places=1)
        self.assertAlmostEqual(summary['regionalSavingsPercentage'], 6.36, places=1)


if __name__ == '__main__':
    unittest.main()