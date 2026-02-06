#!/usr/bin/env python3
"""
Simple test to isolate and fix the recursion issue in pricing client.
"""

import sys
import os
import logging

# Add project root to the path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_aws_config_only():
    """Test just AWS config initialization."""
    try:
        from utils.aws_config import AWSConfig
        logger.info("Testing AWSConfig initialization...")
        aws_config = AWSConfig(region='us-east-1')
        logger.info("✅ AWSConfig initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ AWSConfig initialization failed: {e}")
        return False

def test_pricing_client_init_only():
    """Test pricing client initialization without any method calls."""
    try:
        from utils.aws_config import AWSConfig
        from aws.pricing_client import PricingClient, Currency
        
        logger.info("Testing PricingClient initialization...")
        aws_config = AWSConfig(region='us-east-1')
        
        # Initialize without calling any methods
        pricing_client = PricingClient(aws_config, Currency.USD)
        logger.info("✅ PricingClient initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ PricingClient initialization failed: {e}")
        return False

def test_simple_pricing_call():
    """Test a simple pricing call with fallback."""
    try:
        from utils.aws_config import AWSConfig
        from aws.pricing_client import PricingClient, Currency, PricingModel
        
        logger.info("Testing simple pricing call...")
        aws_config = AWSConfig(region='us-east-1')
        pricing_client = PricingClient(aws_config, Currency.USD)
        
        # Try a simple call that should use fallback
        result = pricing_client._get_fallback_pricing('AmazonEC2', 'us-east-1', PricingModel.ON_DEMAND)
        logger.info(f"✅ Fallback pricing call successful: {result.get('hourlyPrice', 'N/A')}")
        return True
    except Exception as e:
        logger.error(f"❌ Simple pricing call failed: {e}")
        return False

def main():
    """Run isolated tests to identify recursion issue."""
    logger.info("Starting recursion isolation tests...")
    
    tests = [
        ("AWS Config Only", test_aws_config_only),
        ("Pricing Client Init Only", test_pricing_client_init_only),
        ("Simple Pricing Call", test_simple_pricing_call),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info('='*50)
        
        try:
            result = test_func()
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            logger.error(f"{test_name}: ❌ EXCEPTION - {e}")
        
        logger.info("")

if __name__ == "__main__":
    main()