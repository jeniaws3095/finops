#!/usr/bin/env python3
"""
Test script for enhanced ML Right-Sizing Engine functionality.

This script tests the core ML functionality without requiring sklearn imports.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import json

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger