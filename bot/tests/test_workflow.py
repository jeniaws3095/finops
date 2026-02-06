#!/usr/bin/env python3
"""
Test the complete workflow setup.
"""

import sys
import os

# Add current directory to path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

def test_workflow():
    """Test the workflow."""
    print("Testing Advanced FinOps Platform workflow...")
    
    try:
        from main import AdvancedFinOpsOrchestrator
        
        # Initialize orchestrator
        orchestrator = AdvancedFinOpsOrchestrator(
            region='us-east-1',
            dry_run=True
        )
        
        print("✓ Orchestrator initialized successfully")
        
        # Test discovery
        results = orchestrator.run_discovery(['ec2'])
        print(f"✓ Discovery completed: {results['services_scanned']} services scanned")
        
        # Test complete workflow
        workflow_results = orchestrator.run_complete_workflow(
            services=['ec2'],
            scan_only=True
        )
        
        print(f"✓ Complete workflow test: Success = {workflow_results.get('success', False)}")
        print(f"  Duration: {workflow_results.get('workflow_duration', 0):.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"✗ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_workflow()
    sys.exit(0 if success else 1)