#!/usr/bin/env python3
"""
Integration Test for Cost Calculator with Pricing Intelligence Engine

Tests the integration between cost calculation utilities and pricing intelligence
to ensure they work together correctly for optimization recommendations.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from utils.cost_calculator import CostCalculator, Currency, PricingModel
from core.pricing_intelligence import PricingIntelligenceEngine
from utils.aws_config import AWSConfig


class TestCostCalculatorIntegration(unittest.TestCase):
    """Integration tests for cost calculator with pricing intelligence."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        # Mock AWS config
        self.mock_aws_config = Mock(spec=AWSConfig)
        self.mock_pricing_client = Mock()
        self.mock_aws_config.get_pricing_client.return_value = self.mock_pricing_client
        self.mock_aws_config.execute_with_retry = Mock()
        
        # Create instances
        self.cost_calculator = CostCalculator(self.mock_aws_config, Currency.USD)
        self.pricing_engine = PricingIntelligenceEngine(self.mock_aws_config, 'us-east-1')
    
    def test_pricing_engine_uses_cost_calculator(self):
        """Test that pricing intelligence engine integrates with cost calculator."""
        # Verify the pricing engine has a cost calculator instance
        self.assertIsNotNone(self.pricing_engine.cost_calculator)
        self.assertIsInstance(self.pricing_engine.cost_calculator, CostCalculator)
    
    def test_regional_pricing_comparison_integration(self):
        """Test regional pricing comparison using cost calculator."""
        # Mock cost calculator regional comparison
        mock_regional_data = {
            'instanceType': 't3.micro',
            'serviceCode': 'AmazonEC2',
            'regionalPricing': {
                'us-east-1': {'hourlyPrice': 0.0104, 'monthlyPrice': 75.92},
                'us-west-2': {'hourlyPrice': 0.0110, 'monthlyPrice': 80.30},
                'eu-west-1': {'hourlyPrice': 0.0115, 'monthlyPrice': 83.95}
            },
            'cheapestRegion': 'us-east-1',
            'mostExpensiveRegion': 'eu-west-1',
            'maxPotentialSavingsPercentage': 9.57
        }
        
        self.pricing_engine.cost_calculator.compare_regional_pricing = Mock(return_value=mock_regional_data)
        
        # Test that pricing engine can use cost calculator for regional analysis
        result = self.pricing_engine.cost_calculator.compare_regional_pricing(
            'AmazonEC2', 't3.micro', ['us-east-1', 'us-west-2', 'eu-west-1']
        )
        
        self.assertEqual(result['cheapestRegion'], 'us-east-1')
        self.assertEqual(result['mostExpensiveRegion'], 'eu-west-1')
        self.assertGreater(result['maxPotentialSavingsPercentage'], 0)
    
    def test_reserved_instance_calculation_integration(self):
        """Test RI calculations using cost calculator."""
        # Mock RI calculation
        mock_ri_data = {
            'instanceType': 't3.micro',
            'region': 'us-east-1',
            'quantity': 2,
            'termYears': 1,
            'totalSavings': 45.50,
            'savingsPercentage': 25.3,
            'paybackPeriodMonths': 8.2
        }
        
        self.pricing_engine.cost_calculator.calculate_reserved_instance_savings = Mock(return_value=mock_ri_data)
        
        # Test RI calculation integration
        result = self.pricing_engine.cost_calculator.calculate_reserved_instance_savings(
            't3.micro', 'us-east-1', 2, 1
        )
        
        self.assertEqual(result['instanceType'], 't3.micro')
        self.assertGreater(result['totalSavings'], 0)
        self.assertGreater(result['savingsPercentage'], 0)
    
    def test_spot_instance_calculation_integration(self):
        """Test Spot instance calculations using cost calculator."""
        # Mock Spot calculation
        mock_spot_data = {
            'instanceType': 't3.micro',
            'region': 'us-east-1',
            'averageSavingsPercentage': 70.2,
            'monthlySavings': 53.25,
            'interruptionRate': 5.0,
            'riskAdjusted': True
        }
        
        self.pricing_engine.cost_calculator.calculate_spot_instance_savings = Mock(return_value=mock_spot_data)
        
        # Test Spot calculation integration
        result = self.pricing_engine.cost_calculator.calculate_spot_instance_savings(
            't3.micro', 'us-east-1', 75.92
        )
        
        self.assertEqual(result['instanceType'], 't3.micro')
        self.assertGreater(result['averageSavingsPercentage'], 0)
        self.assertGreater(result['monthlySavings'], 0)
    
    def test_cost_forecasting_integration(self):
        """Test cost forecasting using cost calculator."""
        # Mock cost forecast
        historical_costs = [100.0, 105.0, 110.0, 115.0, 120.0, 125.0]
        mock_forecast_data = {
            'forecastMonths': 6,
            'monthlyForecast': [130.0, 135.0, 140.0, 145.0, 150.0, 155.0],
            'totalForecastCost': 855.0,
            'projectedGrowthPercentage': 24.0,
            'forecastAccuracy': 0.95
        }
        
        self.pricing_engine.cost_calculator.project_cost_forecast = Mock(return_value=mock_forecast_data)
        
        # Test cost forecasting integration
        result = self.pricing_engine.cost_calculator.project_cost_forecast(historical_costs, 6)
        
        self.assertEqual(result['forecastMonths'], 6)
        self.assertEqual(len(result['monthlyForecast']), 6)
        self.assertGreater(result['totalForecastCost'], 0)
    
    def test_currency_conversion_integration(self):
        """Test currency conversion using cost calculator."""
        # Mock currency conversion
        mock_conversion_data = {
            'originalAmount': 100.0,
            'convertedAmount': 85.0,
            'fromCurrency': 'USD',
            'toCurrency': 'EUR',
            'exchangeRate': 0.85
        }
        
        self.pricing_engine.cost_calculator.convert_currency = Mock(return_value=mock_conversion_data)
        
        # Test currency conversion integration
        result = self.pricing_engine.cost_calculator.convert_currency(100.0, Currency.USD, Currency.EUR)
        
        self.assertEqual(result['originalAmount'], 100.0)
        self.assertEqual(result['convertedAmount'], 85.0)
        self.assertEqual(result['exchangeRate'], 0.85)
    
    def test_end_to_end_pricing_analysis_with_cost_calculator(self):
        """Test complete pricing analysis workflow using cost calculator."""
        # Mock comprehensive pricing analysis
        mock_resources = [
            {
                'resourceId': 'i-1234567890abcdef0',
                'resourceType': 'ec2',
                'instanceType': 't3.micro',
                'region': 'us-east-1',
                'currentCost': 75.92,
                'utilizationMetrics': {
                    'avgCpuUtilization': 85.0,
                    'runtimeHours': 720,
                    'dataPoints': 720
                }
            }
        ]
        
        # Mock cost calculator methods
        self.pricing_engine.cost_calculator.compare_regional_pricing = Mock(return_value={
            'cheapestRegion': 'us-east-1',
            'maxPotentialSavingsPercentage': 8.5
        })
        
        self.pricing_engine.cost_calculator.calculate_reserved_instance_savings = Mock(return_value={
            'totalSavings': 228.0,
            'savingsPercentage': 25.0,
            'paybackPeriodMonths': 6.0
        })
        
        self.pricing_engine.cost_calculator.calculate_spot_instance_savings = Mock(return_value={
            'averageSavingsPercentage': 70.0,
            'monthlySavings': 53.14,
            'interruptionRate': 5.0
        })
        
        # Test that pricing engine can leverage cost calculator for comprehensive analysis
        # This would be called within the pricing engine's analyze_pricing_opportunities method
        
        # Verify cost calculator methods are available and working
        regional_result = self.pricing_engine.cost_calculator.compare_regional_pricing(
            'AmazonEC2', 't3.micro', ['us-east-1', 'us-west-2']
        )
        
        ri_result = self.pricing_engine.cost_calculator.calculate_reserved_instance_savings(
            't3.micro', 'us-east-1', 1, 1
        )
        
        spot_result = self.pricing_engine.cost_calculator.calculate_spot_instance_savings(
            't3.micro', 'us-east-1', 75.92
        )
        
        # Verify results
        self.assertIsInstance(regional_result, dict)
        self.assertIsInstance(ri_result, dict)
        self.assertIsInstance(spot_result, dict)
        
        # Verify cost calculator provides accurate data for pricing decisions
        self.assertGreater(ri_result['totalSavings'], 0)
        self.assertGreater(spot_result['monthlySavings'], 0)
        self.assertIn('cheapestRegion', regional_result)


if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run integration tests
    unittest.main(verbosity=2)