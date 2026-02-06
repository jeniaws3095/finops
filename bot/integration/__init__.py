"""
Integration package for connecting Python bot with external systems.

This package handles:
- Backend API synchronization
- Data transformation and formatting
- External service integrations
"""

from .backend_sync import BackendSync

__all__ = ['BackendSync']
