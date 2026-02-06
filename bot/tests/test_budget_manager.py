#!/usr/bin/env python3
"""
Unit tests for Budget Manager

Tests the core functionality of the budget management system including:
- Hierarchical budget creation
- Cost forecasting with confidence intervals
- Budget threshold alerting
- Approval workflows
- Variance analysis
"""

import unittest
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.budget_manager import (
    BudgetManager, BudgetType, ForecastModel, AlertThreshold, 
    BudgetStatus, ApprovalLevel
)


class TestBudgetManager(unittest.TestCase):
    """Test cases for Budget Manager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.budget_manager = BudgetManager(dry_run=False)
        
        # Sample historical data for testing
        self.sample_historical_data = [
            {"date": "2024-01-01T00:00:00Z", "cost": 1000.0},
            {"date": "2024-02-01T00:00:00Z", "cost": 1100.0},
            {"date": "2024-03-01T00:00:00Z", "cost": 1050.0},
            {"date": "2024-04-01T00:00:00Z", "cost": 1200.0},
            {"date": "2024-05-01T00:00:00Z", "cost": 1150.0},
            {"date": "2024-06-01T00:00:00Z", "cost": 1300.0}
        ]

    def test_create_hierarchical_budget(self):
        """Test creating hierarchical budget structures."""
        # Create organization budget
        org_budget = self.budget_manager.create_hierarchical_budget(
            budget_id="org-2024",
            budget_type=BudgetType.ORGANIZATION,
            parent_budget_id=None,
            budget_amount=120000.0,
            period_months=12
        )
        
        self.assertEqual(org_budget["budget_id"], "org-2024")
        self.assertEqual(org_budget["budget_type"], "organization")
        self.assertEqual(org_budget["budget_amount"], 120000.0)
        self.assertEqual(org_budget["monthly_amount"], 10000.0)
        self.assertIsNone(org_budget["parent_budget_id"])
        
        # Create team budget under organization
        team_budget = self.budget_manager.create_hierarchical_budget(
            budget_id="team-engineering",
            budget_type=BudgetType.TEAM,
            parent_budget_id="org-2024",
            budget_amount=60000.0,
            period_months=12
        )
        
        self.assertEqual(team_budget["parent_budget_id"], "org-2024")
        self.assertIn("team-engineering", org_budget["child_budgets"])

    def test_analyze_historical_trends(self):
        """Test historical trend analysis."""
        # Create a budget first
        self.budget_manager.create_hierarchical_budget(
            budget_id="test-budget",
            budget_type=BudgetType.TEAM,
            parent_budget_id=None,
            budget_amount=12000.0
        )
        
        # Analyze trends
        trend_analysis = self.budget_manager.analyze_historical_trends(
            budget_id="test-budget",
            historical_data=self.sample_historical_data,
            analysis_months=6
        )
        
        self.assertIn("trend", trend_analysis)
        self.assertIn("seasonal_factors", trend_analysis)
        self.assertEqual(trend_analysis["data_points"], 6)

    def test_generate_cost_forecast(self):
        """Test cost forecasting with confidence intervals."""
        # Create budget and add historical data
        self.budget_manager.create_hierarchical_budget(
            budget_id="forecast-budget",
            budget_type=BudgetType.PROJECT,
            parent_budget_id=None,
            budget_amount=15000.0
        )
        
        self.budget_manager.analyze_historical_trends(
            budget_id="forecast-budget",
            historical_data=self.sample_historical_data
        )
        
        # Generate forecast
        forecast = self.budget_manager.generate_cost_forecast(
            budget_id="forecast-budget",
            forecast_months=6,
            growth_projections={"overall": 0.1},  # 10% annual growth
            confidence_level=0.95
        )
        
        self.assertEqual(forecast["budget_id"], "forecast-budget")
        self.assertEqual(forecast["forecast_months"], 6)
        self.assertIn("base_forecast", forecast)
        self.assertIn("confidence_intervals", forecast)
        self.assertIn("scenarios", forecast)
        self.assertEqual(len(forecast["base_forecast"]), 6)

    def test_track_budget_performance(self):
        """Test budget performance tracking."""
        # Create budget
        self.budget_manager.create_hierarchical_budget(
            budget_id="performance-budget",
            budget_type=BudgetType.TEAM,
            parent_budget_id=None,
            budget_amount=10000.0
        )
        
        # Track performance with actual costs
        actual_costs = [
            {"amount": 800.0, "date": "2024-01-01"},
            {"amount": 900.0, "date": "2024-02-01"},
            {"amount": 850.0, "date": "2024-03-01"}
        ]
        
        performance = self.budget_manager.track_budget_performance(
            budget_id="performance-budget",
            actual_costs=actual_costs
        )
        
        self.assertEqual(performance["budget_id"], "performance-budget")
        self.assertEqual(performance["current_spend"], 2550.0)
        self.assertEqual(performance["budget_amount"], 10000.0)
        self.assertAlmostEqual(performance["utilization_percentage"], 25.5, places=1)

    def test_generate_budget_alerts(self):
        """Test budget alert generation."""
        # Create budget
        self.budget_manager.create_hierarchical_budget(
            budget_id="alert-budget",
            budget_type=BudgetType.PROJECT,
            parent_budget_id=None,
            budget_amount=5000.0
        )
        
        # Generate alerts for 80% utilization
        alerts = self.budget_manager.generate_budget_alerts(
            budget_id="alert-budget",
            current_spend=4000.0
        )
        
        # Should trigger warning_75 threshold
        self.assertGreater(len(alerts), 0)
        
        # Check alert structure
        if alerts:
            alert = alerts[0]
            self.assertEqual(alert["budget_id"], "alert-budget")
            self.assertEqual(alert["current_spend"], 4000.0)
            self.assertEqual(alert["budget_amount"], 5000.0)
            self.assertIn("severity", alert)
            self.assertIn("message", alert)

    def test_trigger_approval_workflow(self):
        """Test approval workflow triggering."""
        # Create budget
        self.budget_manager.create_hierarchical_budget(
            budget_id="approval-budget",
            budget_type=BudgetType.TEAM,
            parent_budget_id=None,
            budget_amount=8000.0
        )
        
        # Trigger approval workflow
        workflow = self.budget_manager.trigger_approval_workflow(
            budget_id="approval-budget",
            requested_amount=2000.0,
            justification="Additional infrastructure for Q2 growth",
            requester="john.doe@company.com"
        )
        
        self.assertEqual(workflow["budget_id"], "approval-budget")
        self.assertEqual(workflow["requested_amount"], 2000.0)
        self.assertEqual(workflow["requester"], "john.doe@company.com")
        self.assertIn("approval_level", workflow)
        self.assertEqual(workflow["status"], "pending")

    def test_generate_variance_analysis(self):
        """Test variance analysis generation."""
        # Create budget with historical data
        self.budget_manager.create_hierarchical_budget(
            budget_id="variance-budget",
            budget_type=BudgetType.PROJECT,
            parent_budget_id=None,
            budget_amount=12000.0
        )
        
        self.budget_manager.analyze_historical_trends(
            budget_id="variance-budget",
            historical_data=self.sample_historical_data
        )
        
        # Generate variance analysis
        analysis = self.budget_manager.generate_variance_analysis(
            budget_id="variance-budget",
            analysis_period_months=6
        )
        
        self.assertEqual(analysis["budget_id"], "variance-budget")
        self.assertIn("variance_metrics", analysis)
        self.assertIn("cost_breakdown", analysis)
        self.assertIn("recommendations", analysis)
        self.assertIn("summary", analysis)

    def test_budget_status_determination(self):
        """Test budget status determination logic."""
        # Test different utilization levels
        self.assertEqual(
            self.budget_manager._determine_budget_status(0.5),
            BudgetStatus.HEALTHY
        )
        self.assertEqual(
            self.budget_manager._determine_budget_status(0.8),
            BudgetStatus.WARNING
        )
        self.assertEqual(
            self.budget_manager._determine_budget_status(0.95),
            BudgetStatus.CRITICAL
        )
        self.assertEqual(
            self.budget_manager._determine_budget_status(1.1),
            BudgetStatus.EXCEEDED
        )

    def test_approval_level_determination(self):
        """Test approval level determination logic."""
        # Test different percentage increases
        self.assertEqual(
            self.budget_manager._determine_approval_level(500, 10000, 5000),
            ApprovalLevel.AUTOMATIC  # 5% increase
        )
        self.assertEqual(
            self.budget_manager._determine_approval_level(1500, 10000, 5000),
            ApprovalLevel.MANAGER  # 15% increase
        )
        self.assertEqual(
            self.budget_manager._determine_approval_level(3000, 10000, 5000),
            ApprovalLevel.DIRECTOR  # 30% increase
        )
        self.assertEqual(
            self.budget_manager._determine_approval_level(6000, 10000, 5000),
            ApprovalLevel.EXECUTIVE  # 60% increase
        )

    def test_get_budget_summary(self):
        """Test budget summary generation."""
        # Create multiple budgets
        self.budget_manager.create_hierarchical_budget(
            budget_id="summary-budget-1",
            budget_type=BudgetType.ORGANIZATION,
            parent_budget_id=None,
            budget_amount=50000.0
        )
        
        self.budget_manager.create_hierarchical_budget(
            budget_id="summary-budget-2",
            budget_type=BudgetType.TEAM,
            parent_budget_id="summary-budget-1",
            budget_amount=25000.0
        )
        
        # Get summary
        summary = self.budget_manager.get_budget_summary()
        
        self.assertEqual(summary["total_budgets"], 2)
        self.assertEqual(summary["total_budget_amount"], 75000.0)
        self.assertIn("budget_status_distribution", summary)
        self.assertIn("overall_utilization", summary)

    def test_dry_run_mode(self):
        """Test dry run mode functionality."""
        dry_run_manager = BudgetManager(dry_run=True)
        
        # Create budget in dry run mode
        budget = dry_run_manager.create_hierarchical_budget(
            budget_id="dry-run-budget",
            budget_type=BudgetType.TEAM,
            parent_budget_id=None,
            budget_amount=5000.0
        )
        
        # Budget should be returned and stored (for demo/testing purposes)
        self.assertEqual(budget["budget_id"], "dry-run-budget")
        self.assertEqual(len(dry_run_manager.budgets), 1)
        
        # Verify dry_run flag is set correctly
        self.assertTrue(dry_run_manager.dry_run)

    def test_error_handling(self):
        """Test error handling for invalid operations."""
        # Test creating budget with non-existent parent
        with self.assertRaises(ValueError):
            self.budget_manager.create_hierarchical_budget(
                budget_id="invalid-budget",
                budget_type=BudgetType.TEAM,
                parent_budget_id="non-existent-parent",
                budget_amount=5000.0
            )
        
        # Test operations on non-existent budget
        with self.assertRaises(ValueError):
            self.budget_manager.track_budget_performance(
                budget_id="non-existent-budget",
                actual_costs=[]
            )


if __name__ == "__main__":
    unittest.main()