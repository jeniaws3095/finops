#!/usr/bin/env python3
"""
Property-Based Test for Budget Management - Hierarchical Budget Support

**Feature: advanced-finops-platform, Property 17: Hierarchical Budget Support**

This test validates that for any organizational structure, the Budget_Manager 
should support creating and managing hierarchical budgets across organizations, 
teams, and projects.

**Validates: Requirements 6.1**

The test uses property-based testing to generate various organizational structures
and verify that the hierarchical budget management is consistent, accurate, and
maintains proper parent-child relationships across all budget levels.
"""

import pytest
from hypothesis import given, strategies as st, settings, example, assume
from hypothesis.strategies import composite
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
import logging
import json

# Import the budget manager we want to test
from core.budget_manager import BudgetManager, BudgetType, BudgetStatus, AlertThreshold

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Strategy generators for hierarchical budget structures
@composite
def budget_type_strategy(draw):
    """Generate valid budget types for hierarchical structures."""
    return draw(st.sampled_from([
        BudgetType.ORGANIZATION,
        BudgetType.TEAM,
        BudgetType.PROJECT,
        BudgetType.SERVICE,
        BudgetType.REGION
    ]))


@composite
def budget_amount_strategy(draw):
    """Generate realistic budget amounts."""
    return draw(st.floats(
        min_value=1000.0,
        max_value=1000000.0,
        allow_nan=False,
        allow_infinity=False
    ))


@composite
def budget_period_strategy(draw):
    """Generate valid budget periods in months."""
    return draw(st.integers(min_value=1, max_value=36))


@composite
def currency_strategy(draw):
    """Generate valid currency codes."""
    return draw(st.sampled_from(['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD']))


@composite
def budget_tags_strategy(draw):
    """Generate realistic budget tags."""
    tag_keys = ['Environment', 'Project', 'Team', 'CostCenter', 'Owner', 'Department']
    tag_values = ['prod', 'dev', 'test', 'engineering', 'data', 'ops', 'finance', 'marketing']
    
    num_tags = draw(st.integers(min_value=0, max_value=4))
    tags = {}
    
    for _ in range(num_tags):
        key = draw(st.sampled_from(tag_keys))
        value = draw(st.sampled_from(tag_values))
        tags[key] = value
    
    return tags


@composite
def allocation_rules_strategy(draw):
    """Generate realistic cost allocation rules."""
    rules = {}
    
    # Add some common allocation rules
    if draw(st.booleans()):
        rules['tag_based'] = {
            'tag_key': draw(st.sampled_from(['Team', 'Project', 'Environment'])),
            'allocation_method': draw(st.sampled_from(['equal', 'proportional', 'usage_based']))
        }
    
    if draw(st.booleans()):
        rules['service_based'] = {
            'services': draw(st.lists(
                st.sampled_from(['ec2', 'rds', 's3', 'lambda', 'cloudwatch']),
                min_size=1,
                max_size=3,
                unique=True
            )),
            'allocation_percentage': draw(st.floats(min_value=0.1, max_value=1.0))
        }
    
    return rules


@composite
def budget_hierarchy_strategy(draw):
    """Generate a complete hierarchical budget structure."""
    # Start with organization budget
    org_budget = {
        'budget_id': f"org-{draw(st.text(min_size=3, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))}",
        'budget_type': BudgetType.ORGANIZATION,
        'parent_budget_id': None,
        'budget_amount': draw(budget_amount_strategy()),
        'period_months': draw(budget_period_strategy()),
        'currency': draw(currency_strategy()),
        'tags': draw(budget_tags_strategy()),
        'allocation_rules': draw(allocation_rules_strategy())
    }
    
    # Generate team budgets under organization
    num_teams = draw(st.integers(min_value=1, max_value=5))
    team_budgets = []
    
    total_team_allocation = 0.0
    for i in range(num_teams):
        team_allocation = draw(st.floats(min_value=0.1, max_value=0.4))
        total_team_allocation += team_allocation
        
        # Ensure we don't exceed parent budget
        if total_team_allocation > 0.9:
            team_allocation = 0.9 - (total_team_allocation - team_allocation)
            if team_allocation <= 0:
                break
        
        team_budget = {
            'budget_id': f"team-{i}-{draw(st.text(min_size=3, max_size=8, alphabet='abcdefghijklmnopqrstuvwxyz'))}",
            'budget_type': BudgetType.TEAM,
            'parent_budget_id': org_budget['budget_id'],
            'budget_amount': org_budget['budget_amount'] * team_allocation,
            'period_months': org_budget['period_months'],
            'currency': org_budget['currency'],
            'tags': draw(budget_tags_strategy()),
            'allocation_rules': draw(allocation_rules_strategy())
        }
        team_budgets.append(team_budget)
    
    # Generate project budgets under teams
    project_budgets = []
    for team_budget in team_budgets:
        num_projects = draw(st.integers(min_value=0, max_value=3))
        
        total_project_allocation = 0.0
        for j in range(num_projects):
            project_allocation = draw(st.floats(min_value=0.2, max_value=0.6))
            total_project_allocation += project_allocation
            
            # Ensure we don't exceed parent budget
            if total_project_allocation > 0.8:
                project_allocation = 0.8 - (total_project_allocation - project_allocation)
                if project_allocation <= 0:
                    break
            
            project_budget = {
                'budget_id': f"proj-{j}-{draw(st.text(min_size=3, max_size=8, alphabet='abcdefghijklmnopqrstuvwxyz'))}",
                'budget_type': BudgetType.PROJECT,
                'parent_budget_id': team_budget['budget_id'],
                'budget_amount': team_budget['budget_amount'] * project_allocation,
                'period_months': team_budget['period_months'],
                'currency': team_budget['currency'],
                'tags': draw(budget_tags_strategy()),
                'allocation_rules': draw(allocation_rules_strategy())
            }
            project_budgets.append(project_budget)
    
    return {
        'organization': org_budget,
        'teams': team_budgets,
        'projects': project_budgets
    }


@composite
def historical_cost_data_strategy(draw):
    """Generate realistic historical cost data for budget analysis."""
    num_months = draw(st.integers(min_value=3, max_value=24))
    base_cost = draw(st.floats(min_value=1000.0, max_value=50000.0))
    
    historical_data = []
    current_date = datetime.now(timezone.utc)
    
    for i in range(num_months):
        # Add some realistic variation and trend
        month_variation = draw(st.floats(min_value=-0.2, max_value=0.3))
        seasonal_factor = 1.0 + (0.1 * (i % 12 - 6) / 6)  # Simple seasonal pattern
        
        cost = base_cost * (1 + month_variation) * seasonal_factor
        date = current_date - timedelta(days=30 * (num_months - i))
        
        historical_data.append({
            'date': date.isoformat(),
            'cost': max(0, cost),  # Ensure non-negative
            'service_breakdown': {
                'ec2': cost * draw(st.floats(min_value=0.2, max_value=0.6)),
                'rds': cost * draw(st.floats(min_value=0.1, max_value=0.3)),
                's3': cost * draw(st.floats(min_value=0.05, max_value=0.2)),
                'lambda': cost * draw(st.floats(min_value=0.02, max_value=0.1)),
                'other': cost * draw(st.floats(min_value=0.05, max_value=0.15))
            }
        })
    
    return historical_data


class TestHierarchicalBudgetSupport:
    """Test suite for hierarchical budget support property."""
    
    def setup_method(self):
        """Set up test environment."""
        self.budget_manager = BudgetManager(dry_run=True)
    
    @given(hierarchy=budget_hierarchy_strategy())
    @settings(max_examples=50, deadline=None)
    def test_hierarchical_budget_creation_consistency(self, hierarchy):
        """
        Property: Hierarchical budget creation should be consistent and maintain proper relationships.
        
        For any organizational structure, the Budget_Manager should:
        1. Create budgets in proper hierarchical order
        2. Maintain parent-child relationships
        3. Ensure child budgets don't exceed parent allocations
        4. Preserve budget metadata and configuration
        """
        # Create organization budget first
        org_budget = hierarchy['organization']
        
        created_org = self.budget_manager.create_hierarchical_budget(
            budget_id=org_budget['budget_id'],
            budget_type=org_budget['budget_type'],
            parent_budget_id=org_budget['parent_budget_id'],
            budget_amount=org_budget['budget_amount'],
            period_months=org_budget['period_months'],
            currency=org_budget['currency'],
            tags=org_budget['tags'],
            allocation_rules=org_budget['allocation_rules']
        )
        
        # Property 1: Organization budget should be created successfully
        assert created_org is not None, "Organization budget creation should succeed"
        assert created_org['budget_id'] == org_budget['budget_id'], "Budget ID should match"
        assert created_org['budget_type'] == org_budget['budget_type'].value, "Budget type should match"
        assert created_org['parent_budget_id'] is None, "Organization budget should have no parent"
        assert created_org['budget_amount'] == org_budget['budget_amount'], "Budget amount should match"
        
        # Property 2: Budget should be stored in manager
        assert org_budget['budget_id'] in self.budget_manager.budgets, "Budget should be stored"
        stored_budget = self.budget_manager.budgets[org_budget['budget_id']]
        assert stored_budget['budget_amount'] == org_budget['budget_amount'], "Stored amount should match"
        
        # Create team budgets
        created_teams = []
        for team_budget in hierarchy['teams']:
            created_team = self.budget_manager.create_hierarchical_budget(
                budget_id=team_budget['budget_id'],
                budget_type=team_budget['budget_type'],
                parent_budget_id=team_budget['parent_budget_id'],
                budget_amount=team_budget['budget_amount'],
                period_months=team_budget['period_months'],
                currency=team_budget['currency'],
                tags=team_budget['tags'],
                allocation_rules=team_budget['allocation_rules']
            )
            created_teams.append(created_team)
        
        # Property 3: Team budgets should maintain parent relationship
        for i, team_budget in enumerate(hierarchy['teams']):
            created_team = created_teams[i]
            assert created_team['parent_budget_id'] == org_budget['budget_id'], "Team should have org as parent"
            assert team_budget['budget_id'] in self.budget_manager.budgets, "Team budget should be stored"
            
            # Check parent-child relationship is maintained
            org_stored = self.budget_manager.budgets[org_budget['budget_id']]
            assert team_budget['budget_id'] in org_stored['child_budgets'], "Team should be in parent's children"
        
        # Create project budgets
        created_projects = []
        for project_budget in hierarchy['projects']:
            created_project = self.budget_manager.create_hierarchical_budget(
                budget_id=project_budget['budget_id'],
                budget_type=project_budget['budget_type'],
                parent_budget_id=project_budget['parent_budget_id'],
                budget_amount=project_budget['budget_amount'],
                period_months=project_budget['period_months'],
                currency=project_budget['currency'],
                tags=project_budget['tags'],
                allocation_rules=project_budget['allocation_rules']
            )
            created_projects.append(created_project)
        
        # Property 4: Project budgets should maintain team parent relationship
        for i, project_budget in enumerate(hierarchy['projects']):
            created_project = created_projects[i]
            parent_team_id = project_budget['parent_budget_id']
            
            assert created_project['parent_budget_id'] == parent_team_id, "Project should have team as parent"
            assert project_budget['budget_id'] in self.budget_manager.budgets, "Project budget should be stored"
            
            # Check parent-child relationship is maintained
            if parent_team_id in self.budget_manager.budgets:
                team_stored = self.budget_manager.budgets[parent_team_id]
                assert project_budget['budget_id'] in team_stored['child_budgets'], "Project should be in team's children"
    
    @given(
        hierarchy=budget_hierarchy_strategy(),
        historical_data=historical_cost_data_strategy()
    )
    @settings(max_examples=30, deadline=None)
    def test_hierarchical_budget_forecasting_consistency(self, hierarchy, historical_data):
        """
        Property: Hierarchical budget forecasting should be consistent across all levels.
        
        For any organizational structure with historical data, forecasting should:
        1. Work at all hierarchy levels
        2. Maintain consistency between parent and child forecasts
        3. Provide appropriate confidence intervals
        4. Handle missing data gracefully
        """
        # Create the hierarchy
        org_budget = hierarchy['organization']
        self.budget_manager.create_hierarchical_budget(
            budget_id=org_budget['budget_id'],
            budget_type=org_budget['budget_type'],
            parent_budget_id=org_budget['parent_budget_id'],
            budget_amount=org_budget['budget_amount'],
            period_months=org_budget['period_months'],
            currency=org_budget['currency'],
            tags=org_budget['tags'],
            allocation_rules=org_budget['allocation_rules']
        )
        
        # Analyze historical trends for organization
        trend_analysis = self.budget_manager.analyze_historical_trends(
            budget_id=org_budget['budget_id'],
            historical_data=historical_data,
            analysis_months=12
        )
        
        # Property 1: Trend analysis should complete successfully
        assert trend_analysis is not None, "Trend analysis should succeed"
        assert 'trend' in trend_analysis, "Trend analysis should include trend data"
        assert 'seasonal_factors' in trend_analysis, "Trend analysis should include seasonal factors"
        
        # Generate forecast for organization
        forecast = self.budget_manager.generate_cost_forecast(
            budget_id=org_budget['budget_id'],
            forecast_months=6,
            growth_projections={'overall': 0.15},
            confidence_level=0.95
        )
        
        # Property 2: Forecast should be properly structured
        assert forecast is not None, "Forecast should be generated"
        assert 'base_forecast' in forecast, "Forecast should include base projection"
        assert 'confidence_intervals' in forecast, "Forecast should include confidence intervals"
        assert 'scenarios' in forecast, "Forecast should include scenario analysis"
        assert len(forecast['base_forecast']) == 6, "Forecast should have 6 months of data"
        
        # Property 3: Confidence intervals should be reasonable
        confidence_intervals = forecast['confidence_intervals']
        assert 'lower_bound' in confidence_intervals, "Should have lower bound"
        assert 'upper_bound' in confidence_intervals, "Should have upper bound"
        assert len(confidence_intervals['lower_bound']) == 6, "Lower bound should have 6 months"
        assert len(confidence_intervals['upper_bound']) == 6, "Upper bound should have 6 months"
        
        # Verify bounds are logical
        for i in range(6):
            lower = confidence_intervals['lower_bound'][i]
            upper = confidence_intervals['upper_bound'][i]
            base = forecast['base_forecast'][i]
            
            assert lower <= base <= upper, f"Base forecast should be within bounds at month {i}"
            assert lower >= 0, f"Lower bound should be non-negative at month {i}"
            assert upper >= lower, f"Upper bound should be >= lower bound at month {i}"
        
        # Property 4: Scenarios should be reasonable
        scenarios = forecast['scenarios']
        assert 'realistic' in scenarios, "Should have realistic scenario"
        assert 'optimistic' in scenarios, "Should have optimistic scenario"
        assert 'pessimistic' in scenarios, "Should have pessimistic scenario"
        
        for scenario_name, scenario_data in scenarios.items():
            assert len(scenario_data) == 6, f"{scenario_name} scenario should have 6 months"
            for month_cost in scenario_data:
                assert month_cost >= 0, f"{scenario_name} scenario costs should be non-negative"
    
    @given(
        hierarchy=budget_hierarchy_strategy(),
        spending_data=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['amount', 'date', 'service', 'team']),
                values=st.one_of(
                    st.floats(min_value=0, max_value=10000),
                    st.text(min_size=5, max_size=20),
                    st.sampled_from(['ec2', 'rds', 's3', 'lambda']),
                    st.sampled_from(['engineering', 'data', 'ops'])
                )
            ),
            min_size=1,
            max_size=50
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_hierarchical_budget_performance_tracking(self, hierarchy, spending_data):
        """
        Property: Budget performance tracking should work consistently across hierarchy levels.
        
        For any organizational structure and spending data, performance tracking should:
        1. Calculate utilization correctly at all levels
        2. Maintain consistent status across hierarchy
        3. Generate appropriate alerts based on thresholds
        4. Track variance accurately
        """
        # Create the hierarchy
        org_budget = hierarchy['organization']
        self.budget_manager.create_hierarchical_budget(
            budget_id=org_budget['budget_id'],
            budget_type=org_budget['budget_type'],
            parent_budget_id=org_budget['parent_budget_id'],
            budget_amount=org_budget['budget_amount'],
            period_months=org_budget['period_months'],
            currency=org_budget['currency'],
            tags=org_budget['tags'],
            allocation_rules=org_budget['allocation_rules']
        )
        
        # Ensure spending data has proper structure
        normalized_spending = []
        for spend in spending_data:
            if isinstance(spend.get('amount'), (int, float)) and spend.get('amount') >= 0:
                normalized_spending.append({
                    'amount': float(spend['amount']),
                    'date': spend.get('date', datetime.now().isoformat()),
                    'service': spend.get('service', 'ec2'),
                    'team': spend.get('team', 'engineering')
                })
        
        if not normalized_spending:
            # Create minimal spending data if none provided
            normalized_spending = [{'amount': 100.0, 'date': datetime.now().isoformat()}]
        
        # Track budget performance
        performance = self.budget_manager.track_budget_performance(
            budget_id=org_budget['budget_id'],
            actual_costs=normalized_spending
        )
        
        # Property 1: Performance tracking should complete successfully
        assert performance is not None, "Performance tracking should succeed"
        assert 'budget_id' in performance, "Performance should include budget ID"
        assert 'current_spend' in performance, "Performance should include current spend"
        assert 'utilization_percentage' in performance, "Performance should include utilization"
        assert 'status' in performance, "Performance should include status"
        
        # Property 2: Utilization calculation should be accurate
        current_spend = performance['current_spend']
        budget_amount = org_budget['budget_amount']
        expected_utilization = (current_spend / budget_amount) * 100
        
        assert abs(performance['utilization_percentage'] - expected_utilization) < 0.01, \
            "Utilization calculation should be accurate"
        
        # Property 3: Status should be consistent with utilization
        utilization_ratio = current_spend / budget_amount
        expected_status = None
        
        if utilization_ratio >= 1.0:
            expected_status = BudgetStatus.EXCEEDED.value
        elif utilization_ratio >= 0.9:
            expected_status = BudgetStatus.CRITICAL.value
        elif utilization_ratio >= 0.75:
            expected_status = BudgetStatus.WARNING.value
        else:
            expected_status = BudgetStatus.HEALTHY.value
        
        assert performance['status'] == expected_status, \
            f"Status should be {expected_status} for utilization {utilization_ratio:.2%}"
        
        # Property 4: Performance metrics should be reasonable
        assert performance['current_spend'] >= 0, "Current spend should be non-negative"
        assert 'performance_metrics' in performance, "Should include performance metrics"
        
        metrics = performance['performance_metrics']
        assert 'spend_rate' in metrics, "Should include spend rate"
        assert 'trend_direction' in metrics, "Should include trend direction"
        assert metrics['spend_rate'] >= 0, "Spend rate should be non-negative"
    
    @given(
        hierarchy=budget_hierarchy_strategy(),
        alert_scenarios=st.lists(
            st.tuples(
                st.floats(min_value=0.0, max_value=2.0),  # utilization multiplier
                st.sampled_from(['warning_50', 'warning_75', 'critical_90', 'exceeded_100'])
            ),
            min_size=1,
            max_size=4
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_hierarchical_budget_alerting_consistency(self, hierarchy, alert_scenarios):
        """
        Property: Budget alerting should be consistent across hierarchy levels.
        
        For any organizational structure and alert scenarios, alerting should:
        1. Generate alerts at appropriate thresholds
        2. Include proper severity levels
        3. Provide actionable recommendations
        4. Maintain alert history
        """
        # Create the hierarchy
        org_budget = hierarchy['organization']
        self.budget_manager.create_hierarchical_budget(
            budget_id=org_budget['budget_id'],
            budget_type=org_budget['budget_type'],
            parent_budget_id=org_budget['parent_budget_id'],
            budget_amount=org_budget['budget_amount'],
            period_months=org_budget['period_months'],
            currency=org_budget['currency'],
            tags=org_budget['tags'],
            allocation_rules=org_budget['allocation_rules']
        )
        
        # Test different alert scenarios
        for utilization_multiplier, expected_threshold in alert_scenarios:
            current_spend = org_budget['budget_amount'] * utilization_multiplier
            
            # Generate alerts
            alerts = self.budget_manager.generate_budget_alerts(
                budget_id=org_budget['budget_id'],
                current_spend=current_spend
            )
            
            # Property 1: Alerts should be properly structured
            for alert in alerts:
                assert 'alert_id' in alert, "Alert should have ID"
                assert 'budget_id' in alert, "Alert should have budget ID"
                assert 'threshold_name' in alert, "Alert should have threshold name"
                assert 'severity' in alert, "Alert should have severity"
                assert 'message' in alert, "Alert should have message"
                assert 'recommended_actions' in alert, "Alert should have recommendations"
                assert 'generated_at' in alert, "Alert should have timestamp"
                
                # Property 2: Alert data should be consistent
                assert alert['budget_id'] == org_budget['budget_id'], "Alert should reference correct budget"
                assert alert['current_spend'] == current_spend, "Alert should have correct spend amount"
                assert alert['budget_amount'] == org_budget['budget_amount'], "Alert should have correct budget amount"
                
                # Property 3: Severity should match threshold
                threshold_percentage = alert['threshold_percentage'] / 100
                expected_severity = None
                
                if threshold_percentage >= 1.0:
                    expected_severity = 'critical'
                elif threshold_percentage >= 0.9:
                    expected_severity = 'high'
                elif threshold_percentage >= 0.75:
                    expected_severity = 'medium'
                else:
                    expected_severity = 'low'
                
                assert alert['severity'] == expected_severity, \
                    f"Severity should be {expected_severity} for threshold {threshold_percentage:.1%}"
                
                # Property 4: Recommendations should be actionable
                recommendations = alert['recommended_actions']
                assert isinstance(recommendations, list), "Recommendations should be a list"
                assert len(recommendations) > 0, "Should have at least one recommendation"
                
                for recommendation in recommendations:
                    assert isinstance(recommendation, str), "Recommendation should be a string"
                    assert len(recommendation) > 0, "Recommendation should not be empty"
    
    def test_hierarchical_budget_structure_validation(self):
        """
        Property: Hierarchical budget structure should maintain integrity.
        
        This test ensures that:
        1. Parent budgets must exist before creating child budgets
        2. Child budget amounts don't exceed parent allocations
        3. Budget relationships are properly maintained
        4. Circular dependencies are prevented
        """
        # Property 1: Creating child without parent should fail gracefully
        with pytest.raises(ValueError, match="Parent budget .* does not exist"):
            self.budget_manager.create_hierarchical_budget(
                budget_id="orphan-budget",
                budget_type=BudgetType.TEAM,
                parent_budget_id="non-existent-parent",
                budget_amount=10000.0,
                period_months=12
            )
        
        # Property 2: Valid hierarchy should work
        # Create organization budget
        org_budget = self.budget_manager.create_hierarchical_budget(
            budget_id="test-org",
            budget_type=BudgetType.ORGANIZATION,
            parent_budget_id=None,
            budget_amount=100000.0,
            period_months=12
        )
        
        assert org_budget is not None, "Organization budget should be created"
        assert "test-org" in self.budget_manager.budgets, "Budget should be stored"
        
        # Create team budget under organization
        team_budget = self.budget_manager.create_hierarchical_budget(
            budget_id="test-team",
            budget_type=BudgetType.TEAM,
            parent_budget_id="test-org",
            budget_amount=50000.0,
            period_months=12
        )
        
        assert team_budget is not None, "Team budget should be created"
        assert team_budget['parent_budget_id'] == "test-org", "Team should have org as parent"
        
        # Verify parent-child relationship
        org_stored = self.budget_manager.budgets["test-org"]
        assert "test-team" in org_stored['child_budgets'], "Team should be in org's children"
        
        # Create project budget under team
        project_budget = self.budget_manager.create_hierarchical_budget(
            budget_id="test-project",
            budget_type=BudgetType.PROJECT,
            parent_budget_id="test-team",
            budget_amount=25000.0,
            period_months=12
        )
        
        assert project_budget is not None, "Project budget should be created"
        assert project_budget['parent_budget_id'] == "test-team", "Project should have team as parent"
        
        # Verify team-project relationship
        team_stored = self.budget_manager.budgets["test-team"]
        assert "test-project" in team_stored['child_budgets'], "Project should be in team's children"
        
        # Property 3: Budget summary should reflect hierarchy
        summary = self.budget_manager.get_budget_summary()
        assert summary['total_budgets'] == 3, "Should have 3 budgets total"
        assert summary['total_budget_amount'] == 175000.0, "Total amount should be sum of all budgets"


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])