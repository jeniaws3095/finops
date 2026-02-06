#!/usr/bin/env python3
"""
Test runner for Budget Hierarchical Property Test

This script runs the property-based test for hierarchical budget support
to validate that the Budget_Manager correctly handles organizational structures.

**Feature: advanced-finops-platform, Property 17: Hierarchical Budget Support**
**Validates: Requirements 6.1**
"""

import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_budget_hierarchical_test():
    """Run the budget hierarchical property test."""
    try:
        logger.info("Starting Budget Hierarchical Property Test...")
        logger.info("Testing Property 17: Hierarchical Budget Support")
        logger.info("Validates: Requirements 6.1")
        
        # Run the property test
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'test_budget_hierarchical_property.py',
            '-v',
            '--tb=short',
            '--hypothesis-show-statistics'
        ], capture_output=True, text=True)
        
        # Print output
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        # Check result
        if result.returncode == 0:
            logger.info("✅ Budget Hierarchical Property Test PASSED")
            logger.info("Property 17 (Hierarchical Budget Support) validated successfully")
            return True
        else:
            logger.error("❌ Budget Hierarchical Property Test FAILED")
            logger.error(f"Exit code: {result.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"Error running budget hierarchical test: {str(e)}")
        return False

def main():
    """Main execution function."""
    print("=" * 80)
    print("Budget Hierarchical Property Test Runner")
    print("Advanced FinOps Platform - Property 17: Hierarchical Budget Support")
    print("=" * 80)
    
    success = run_budget_hierarchical_test()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ ALL TESTS PASSED - Hierarchical Budget Support validated")
        print("Requirements 6.1 successfully validated")
    else:
        print("❌ TESTS FAILED - Check output above for details")
        sys.exit(1)
    print("=" * 80)

if __name__ == "__main__":
    main()