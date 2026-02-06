#!/usr/bin/env python3
"""
Test script to verify budget manager workflow functionality.
"""

import sys
import os

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from main import AdvancedFinOpsOrchestrator

def test_budget_workflow():
    """Test the budget management workflow."""
    print("Testing Budget Management Workflow...")
    
    # Initialize orchestrator
    orchestrator = AdvancedFinOpsOrchestrator(region='us-east-1', dry_run=True)
    
    # Run budget management
    results = orchestrator.run_budget_management(create_sample_budgets=True)
    
    print("\nBudget Management Results:")
    for key, value in results.items():
        if key == 'budget_summary':
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")
    
    # Verify key functionality
    assert results['budgets_analyzed'] > 0, "No budgets were analyzed"
    assert results['forecasts_generated'] > 0, "No forecasts were generated"
    assert 'budget_summary' in results, "Budget summary missing"
    
    print("\n✅ Budget management workflow test passed!")
    
    # Test individual budget manager components
    print("\nTesting individual budget manager components...")
    
    from core.budget_manager import BudgetManager, BudgetType
    
    budget_manager = BudgetManager(dry_run=True)
    
    # Test hierarchical budget creation
    org_budget = budget_manager.create_hierarchical_budget(
        budget_id="test-org-budget",
        budget_type=BudgetType.ORGANIZATION,
        parent_budget_id=None,
        budget_amount=100000.0,
        period_months=12
    )
    
    team_budget = budget_manager.create_hierarchical_budget(
        budget_id="test-team-budget",
        budget_type=BudgetType.TEAM,
        parent_budget_id="test-org-budget",
        budget_amount=50000.0,
        period_months=12
    )
    
    # Verify hierarchy
    assert team_budget['parent_budget_id'] == "test-org-budget"
    assert "test-team-budget" in org_budget['child_budgets']
    
    # Test forecasting
    sample_historical_data = [
        {"date": "2024-01-01T00:00:00Z", "cost": 8000.0},
        {"date": "2024-02-01T00:00:00Z", "cost": 8500.0},
        {"date": "2024-03-01T00:00:00Z", "cost": 8200.0},
        {"date": "2024-04-01T00:00:00Z", "cost": 9000.0},
        {"date": "2024-05-01T00:00:00Z", "cost": 8800.0},
        {"date": "2024-06-01T00:00:00Z", "cost": 9200.0}
    ]
    
    # Analyze trends
    trend_analysis = budget_manager.analyze_historical_trends(
        budget_id="test-org-budget",
        historical_data=sample_historical_data,
        analysis_months=6
    )
    
    # Generate forecast
    forecast = budget_manager.generate_cost_forecast(
        budget_id="test-org-budget",
        forecast_months=6,
        growth_projections={"overall": 0.1},  # 10% growth
        confidence_level=0.95
    )
    
    # Test budget performance tracking
    actual_costs = [
        {"amount": 8500.0, "date": "2024-01-01"},
        {"amount": 9000.0, "date": "2024-02-01"},
        {"amount": 8700.0, "date": "2024-03-01"}
    ]
    
    performance = budget_manager.track_budget_performance(
        budget_id="test-org-budget",
        actual_costs=actual_costs
    )
    
    # Test alert generation
    current_spend = sum(cost["amount"] for cost in actual_costs)
    alerts = budget_manager.generate_budget_alerts(
        budget_id="test-org-budget",
        current_spend=current_spend
    )
    
    # Test approval workflow
    workflow = budget_manager.trigger_approval_workflow(
        budget_id="test-org-budget",
        requested_amount=10000.0,
        justification="Additional infrastructure for Q2 expansion",
        requester="test-user"
    )
    
    # Test variance analysis
    variance_analysis = budget_manager.generate_variance_analysis(
        budget_id="test-org-budget",
        analysis_period_months=6
    )
    
    print("✅ Individual component tests passed!")
    
    # Print summary
    print(f"\nBudget Manager Summary:")
    print(f"  Total budgets created: {len(budget_manager.budgets)}")
    print(f"  Forecasts generated: {len(budget_manager.forecasts)}")
    print(f"  Alerts generated: {len(budget_manager.alerts)}")
    print(f"  Approval workflows: {len(budget_manager.approval_workflows)}")
    
    summary = budget_manager.get_budget_summary()
    print(f"  Total budget amount: ${summary['total_budget_amount']:,.2f}")
    print(f"  Overall utilization: {summary['overall_utilization']:.1f}%")
    
    print("\n🎉 All budget manager tests completed successfully!")

if __name__ == "__main__":
    test_budget_workflow()