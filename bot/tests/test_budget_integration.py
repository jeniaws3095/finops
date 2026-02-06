#!/usr/bin/env python3
"""
Integration test for Budget Manager with main workflow

Tests the integration of the budget manager with the main FinOps workflow.
"""

import unittest
import sys
import os
from datetime import datetime

# Add the project root to the path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from main import AdvancedFinOpsOrchestrator


class TestBudgetIntegration(unittest.TestCase):
    """Test cases for Budget Manager integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = AdvancedFinOpsOrchestrator(
            region='us-east-1',
            dry_run=True  # Always use dry run for tests
        )

    def test_budget_management_workflow(self):
        """Test the complete budget management workflow."""
        # Run budget management
        results = self.orchestrator.run_budget_management(
            create_sample_budgets=True
        )
        
        # Verify results structure
        self.assertIn('timestamp', results)
        self.assertIn('region', results)
        self.assertIn('budgets_analyzed', results)
        self.assertIn('forecasts_generated', results)
        self.assertIn('alerts_triggered', results)
        self.assertIn('budget_summary', results)
        
        # Verify budgets were created and analyzed
        self.assertGreater(results['budgets_analyzed'], 0)
        self.assertGreater(results['forecasts_generated'], 0)
        
        # Verify budget summary
        budget_summary = results['budget_summary']
        self.assertIn('total_budgets', budget_summary)
        self.assertIn('total_budget_amount', budget_summary)
        self.assertIn('overall_utilization', budget_summary)

    def test_complete_workflow_with_budget_management(self):
        """Test the complete workflow including budget management."""
        # Run complete workflow
        results = self.orchestrator.run_complete_workflow(
            services=['ec2', 'rds'],
            scan_only=False,
            approve_low_risk=False
        )
        
        # Verify workflow completed successfully
        self.assertTrue(results.get('success', False))
        self.assertIn('phases', results)
        
        # Verify budget management phase was included
        phases = results['phases']
        self.assertIn('budget_management', phases)
        
        # Verify budget management results
        budget_phase = phases['budget_management']
        self.assertIn('budgets_analyzed', budget_phase)
        self.assertIn('forecasts_generated', budget_phase)

    def test_budget_manager_initialization(self):
        """Test that budget manager is properly initialized."""
        from core.budget_manager import BudgetType
        
        # Verify budget manager exists
        self.assertIsNotNone(self.orchestrator.budget_manager)
        
        # Verify dry run mode is set correctly
        self.assertTrue(self.orchestrator.budget_manager.dry_run)
        
        # Test basic budget manager functionality
        budget = self.orchestrator.budget_manager.create_hierarchical_budget(
            budget_id="test-budget",
            budget_type=BudgetType.TEAM,
            parent_budget_id=None,
            budget_amount=10000.0
        )
        
        self.assertEqual(budget['budget_id'], "test-budget")
        self.assertEqual(budget['budget_amount'], 10000.0)

    def test_error_handling(self):
        """Test error handling in budget management workflow."""
        # Test with invalid historical data
        results = self.orchestrator.run_budget_management(
            historical_data=[],  # Empty data
            create_sample_budgets=True
        )
        
        # Should still complete successfully with sample data
        self.assertIn('budgets_analyzed', results)
        self.assertNotIn('error', results)

    def test_budget_manager_components(self):
        """Test individual budget manager components."""
        from core.budget_manager import BudgetType
        
        budget_manager = self.orchestrator.budget_manager
        
        # Test hierarchical budget creation
        org_budget = budget_manager.create_hierarchical_budget(
            budget_id="test-org",
            budget_type=BudgetType.ORGANIZATION,
            parent_budget_id=None,
            budget_amount=50000.0
        )
        
        team_budget = budget_manager.create_hierarchical_budget(
            budget_id="test-team",
            budget_type=BudgetType.TEAM,
            parent_budget_id="test-org",
            budget_amount=25000.0
        )
        
        # Verify hierarchy
        self.assertEqual(team_budget['parent_budget_id'], "test-org")
        self.assertIn("test-team", org_budget['child_budgets'])
        
        # Test forecast generation
        sample_historical_data = [
            {"date": "2024-01-01T00:00:00Z", "cost": 2000.0},
            {"date": "2024-02-01T00:00:00Z", "cost": 2100.0},
            {"date": "2024-03-01T00:00:00Z", "cost": 2050.0}
        ]
        
        budget_manager.analyze_historical_trends(
            budget_id="test-org",
            historical_data=sample_historical_data
        )
        
        forecast = budget_manager.generate_cost_forecast(
            budget_id="test-org",
            forecast_months=3
        )
        
        self.assertEqual(forecast['budget_id'], "test-org")
        self.assertEqual(forecast['forecast_months'], 3)
        self.assertIn('base_forecast', forecast)
        self.assertIn('confidence_intervals', forecast)


if __name__ == "__main__":
    unittest.main()