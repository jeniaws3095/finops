"""
Pytest configuration. Ensures project root is on sys.path so tests can import
main, utils, aws, and core when run from any working directory.
"""
import sys
import os

# Add project root to path (parent of tests/)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
