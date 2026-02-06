#!/usr/bin/env python3
"""
Simple test to verify configuration manager works.
"""

import sys
import os

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

try:
    from utils.config_manager import ConfigManager
    
    print("Testing ConfigManager...")
    
    # Test basic initialization
    config_manager = ConfigManager()
    print(f"✓ ConfigManager initialized")
    print(f"✓ Default region: {config_manager.get('aws.default_region')}")
    print(f"✓ DRY_RUN default: {config_manager.get('safety.dry_run.default')}")
    print(f"✓ Enabled services: {config_manager.get('services.enabled')}")
    
    # Test validation
    issues = config_manager.validate()
    print(f"✓ Configuration validation: {len(issues)} issues found")
    
    # Test service checks
    print(f"✓ EC2 enabled: {config_manager.is_service_enabled('ec2')}")
    print(f"✓ Continuous monitoring: {config_manager.is_continuous_monitoring_enabled()}")
    
    print("\n✓ All configuration tests passed!")
    
except Exception as e:
    print(f"✗ Configuration test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)