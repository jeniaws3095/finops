#!/usr/bin/env python3
"""
Simple test script for ML Right-Sizing Engine
"""

import sys
import os
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.ml_rightsizing import MLRightSizingEngine
from utils.aws_config import AWSConfig
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)

def test_ml_engine():
    """Test ML Right-Sizing Engine initialization and basic functionality."""
    try:
        print("Testing ML Right-Sizing Engine...")
        
        # Test initialization
        aws_config = AWSConfig('us-east-1')
        ml_engine = MLRightSizingEngine(aws_config, 'us-east-1')
        print('✓ ML Right-Sizing Engine initialized successfully')
        
        # Test status method
        status = ml_engine.get_ml_engine_status()
        print(f'✓ Engine status: {status["engine_status"]}')
        print(f'✓ Region: {status["initialized_region"]}')
        print(f'✓ Model count: {status["model_count"]}')
        
        # Test thresholds
        print(f'✓ ML thresholds configured: {len(status["thresholds"])} categories')
        
        # Test cache status
        cache_status = status["cache_status"]
        print(f'✓ Cache directory: {cache_status["model_cache_dir"]}')
        
        print('✓ All basic functionality tests passed')
        return True
        
    except Exception as e:
        print(f'✗ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ml_engine()
    sys.exit(0 if success else 1)