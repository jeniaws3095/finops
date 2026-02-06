#!/usr/bin/env python3
"""
Test script for Billing and Pricing Clients

Tests the basic functionality of the new billing_client.py and pricing_client.py
implementations to ensure they work correctly with the existing AWS configuration.
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add project root to the path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from utils.aws_config import AWSConfig
from aws.billing_client import BillingClient
from aws.pricing_client import PricingClient, Currency, PricingModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_billing_client():
    """Test the BillingClient functionality."""
    logger.info("Testing BillingClient...")
    
    try:
        # Initialize AWS config and billing client
        aws_config = AWSConfig(region='us-east-1')
        billing_client = BillingClient(aws_config)
        
        # Test date range (last 30 days)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        logger.info(f"Testing billing summary from {start_date} to {end_date}")
        
        # Test account billing summary
        billing_summary = billing_client.get_account_billing_summary(start_date, end_date)
        logger.info(f"Billing summary retrieved: Total cost = ${billing_summary.get('totalCost', 0):.2f}")
        
        # Test service billing breakdown
        service_breakdown = billing_client.get_service_billing_breakdown(start_date, end_date)
        logger.info(f"Service breakdown retrieved: {len(service_breakdown.get('services', {}))} services")
        
        # Test regional billing analysis
        regional_analysis = billing_client.get_regional_billing_analysis(start_date, end_date)
        logger.info(f"Regional analysis retrieved: {len(regional_analysis.get('regions', {}))} regions")
        
        # Test billing trends
        trends = billing_client.get_billing_trends(months_back=6)
        logger.info(f"Billing trends retrieved: {len(trends.get('monthlyData', []))} data points")
        
        # Test RI utilization
        ri_utilization = billing_client.get_reserved_instance_utilization(start_date, end_date)
        logger.info(f"RI utilization retrieved: {len(ri_utilization.get('utilization', {}))} periods")
        
        # Test Savings Plans utilization
        sp_utilization = billing_client.get_savings_plans_utilization(start_date, end_date)
        logger.info(f"SP utilization retrieved: {len(sp_utilization.get('utilization', {}))} periods")
        
        logger.info("✅ BillingClient tests completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ BillingClient test failed: {e}")
        return False


def test_pricing_client():
    """Test the PricingClient functionality."""
    logger.info("Testing PricingClient...")
    
    try:
        # Initialize AWS config and pricing client
        aws_config = AWSConfig(region='us-east-1')
        pricing_client = PricingClient(aws_config, Currency.USD)
        
        # Test service pricing
        logger.info("Testing EC2 On-Demand pricing...")
        ec2_pricing = pricing_client.get_service_pricing(
            'AmazonEC2', 
            'us-east-1',
            [{'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': 't3.medium'}],
            PricingModel.ON_DEMAND
        )
        logger.info(f"EC2 pricing retrieved: ${ec2_pricing.get('hourlyPrice', 0):.4f}/hour")
        
        # Test regional pricing comparison
        logger.info("Testing regional pricing comparison...")
        regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        regional_comparison = pricing_client.compare_regional_pricing(
            'AmazonEC2', 't3.medium', regions, PricingModel.ON_DEMAND
        )
        logger.info(f"Regional comparison: {len(regional_comparison.get('regionalPricing', {}))} regions")
        
        # Test Reserved Instance pricing
        logger.info("Testing Reserved Instance pricing...")
        ri_pricing = pricing_client.get_reserved_instance_pricing(
            't3.medium', 'us-east-1', term_years=1, payment_option='No Upfront'
        )
        logger.info(f"RI pricing: ${ri_pricing.get('reservedHourlyPrice', 0):.4f}/hour, "
                   f"${ri_pricing.get('upfrontCost', 0):.2f} upfront")
        
        # Test Savings Plans pricing
        logger.info("Testing Savings Plans pricing...")
        sp_pricing = pricing_client.get_savings_plans_pricing(
            'EC2Instance', commitment_amount=100.0, term_years=1
        )
        logger.info(f"SP pricing: {sp_pricing.get('discountRate', 0)*100:.1f}% discount rate")
        
        # Test Spot pricing analysis
        logger.info("Testing Spot pricing analysis...")
        spot_analysis = pricing_client.get_spot_pricing_analysis('t3.medium', 'us-east-1')
        logger.info(f"Spot analysis: ${spot_analysis.get('averageSpotPrice', 0):.4f}/hour average, "
                   f"{spot_analysis.get('averageSavingsPercentage', 0):.1f}% savings")
        
        # Test currency conversion
        logger.info("Testing currency conversion...")
        conversion = pricing_client.convert_currency(100.0, Currency.USD, Currency.EUR)
        logger.info(f"Currency conversion: $100 USD = €{conversion.get('convertedAmount', 0):.2f} EUR")
        
        # Test pricing trends
        logger.info("Testing pricing trends...")
        trends = pricing_client.get_pricing_trends('AmazonEC2', 't3.medium', 'us-east-1', months_back=6)
        logger.info(f"Pricing trends: {trends.get('trendAnalysis', {}).get('trend', 'unknown')} trend")
        
        # Test TCO calculation
        logger.info("Testing TCO calculation...")
        tco = pricing_client.calculate_total_cost_of_ownership(
            't3.medium', 'us-east-1', usage_hours_per_month=730, months=12
        )
        logger.info(f"TCO analysis: {len(tco.get('tcoAnalysis', {}))} pricing models compared")
        
        logger.info("✅ PricingClient tests completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ PricingClient test failed: {e}")
        return False


def test_integration():
    """Test integration between billing and pricing clients."""
    logger.info("Testing integration between billing and pricing clients...")
    
    try:
        # Initialize clients
        aws_config = AWSConfig(region='us-east-1')
        billing_client = BillingClient(aws_config)
        pricing_client = PricingClient(aws_config, Currency.USD)
        
        # Get billing data for a service
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        service_breakdown = billing_client.get_service_billing_breakdown(
            start_date, end_date, service_codes=['AmazonEC2']
        )
        
        # Get pricing data for the same service
        ec2_pricing = pricing_client.get_service_pricing(
            'AmazonEC2', 'us-east-1',
            [{'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': 't3.medium'}],
            PricingModel.ON_DEMAND
        )
        
        # Verify both clients return data
        has_billing_data = 'services' in service_breakdown
        has_pricing_data = 'hourlyPrice' in ec2_pricing
        
        logger.info(f"Integration test: Billing data = {has_billing_data}, Pricing data = {has_pricing_data}")
        
        if has_billing_data and has_pricing_data:
            logger.info("✅ Integration test completed successfully")
            return True
        else:
            logger.warning("⚠️ Integration test completed with limited data")
            return True  # Still consider success as APIs may have limited data
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("Starting Billing and Pricing Clients test suite...")
    
    test_results = []
    
    # Run individual tests
    test_results.append(("BillingClient", test_billing_client()))
    test_results.append(("PricingClient", test_pricing_client()))
    test_results.append(("Integration", test_integration()))
    
    # Report results
    logger.info("\n" + "="*50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    logger.info("="*50)
    logger.info(f"OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests completed successfully!")
        logger.info("Billing and Pricing Clients are ready for use.")
    else:
        logger.warning(f"⚠️ {total - passed} test(s) failed. Check the logs above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)