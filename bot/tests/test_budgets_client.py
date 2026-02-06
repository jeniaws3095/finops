#!/usr/bin/env python3
"""
Unit tests for AWS Budgets Client

Tests the comprehensive AWS Budgets integration including:
- Hierarchical budget creation and management
- Custom alert configuration with multiple thresholds
- Budget forecast synchronization and variance tracking
- Multi-account budget coordination
- Cost allocation and budget inheritance

Requirements: 10.4, 6.1, 6.3
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime, timezone, timedelta

# Add project root to the path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from aws.budgets_client import (
    BudgetsClient, BudgetType, TimeUnit, ThresholdType, 
    ComparisonOperator, NotificationType, SubscriberType
)


class TestBudgetsClient(unittest.TestCase):
    """Test cases for BudgetsClient functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock AWS config
        self.mock_aws_config = Mock()
        self.mock_budgets_client = Mock()
        self.mock_aws_config.get_budgets_client.return_value = self.mock_budgets_client
        self.mock_aws_config.get_account_id.return_value = '123456789012'
        self.mock_aws_config.execute_with_retry = Mock()
        
        # Initialize BudgetsClient with mocked config
        self.budgets_client = BudgetsClient(self.mock_aws_config, account_id='123456789012')
    
    def test_initialization(self):
        """Test BudgetsClient initialization."""
        self.assertEqual(self.budgets_client.account_id, '123456789012')
        self.assertIsNotNone(self.budgets_client.managed_budgets)
        self.assertIsNotNone(self.budgets_client.budget_hierarchy)
        self.assertIsNotNone(self.budgets_client.alert_configurations)
        self.assertIsNotNone(self.budgets_client.forecast_data)
    
    def test_validate_budget_parameters_valid(self):
        """Test budget parameter validation with valid inputs."""
        result = self.budgets_client._validate_budget_parameters(
            budget_name='test-budget',
            budget_amount=1000.0,
            time_unit=TimeUnit.MONTHLY,
            budget_type=BudgetType.COST,
            cost_filters=None
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_validate_budget_parameters_invalid(self):
        """Test budget parameter validation with invalid inputs."""
        # Test invalid budget amount
        result = self.budgets_client._validate_budget_parameters(
            budget_name='test-budget',
            budget_amount=-100.0,  # Invalid: negative amount
            time_unit=TimeUnit.MONTHLY,
            budget_type=BudgetType.COST,
            cost_filters=None
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('Budget amount must be positive', result['errors'])
        
        # Test invalid time unit
        result = self.budgets_client._validate_budget_parameters(
            budget_name='test-budget',
            budget_amount=1000.0,
            time_unit='INVALID_UNIT',  # Invalid time unit
            budget_type=BudgetType.COST,
            cost_filters=None
        )
        
        self.assertFalse(result['valid'])
        self.assertTrue(any('Time unit must be one of' in error for error in result['errors']))
    
    def test_validate_alert_configurations_valid(self):
        """Test alert configuration validation with valid inputs."""
        alert_thresholds = [
            {
                'threshold': 80,
                'type': ThresholdType.PERCENTAGE,
                'comparison': ComparisonOperator.GREATER_THAN
            }
        ]
        
        subscribers = [
            {
                'type': SubscriberType.EMAIL,
                'address': 'test@example.com'
            }
        ]
        
        result = self.budgets_client._validate_alert_configurations(
            alert_thresholds, subscribers
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_validate_alert_configurations_invalid(self):
        """Test alert configuration validation with invalid inputs."""
        # Test missing threshold
        alert_thresholds = [
            {
                'type': ThresholdType.PERCENTAGE,
                'comparison': ComparisonOperator.GREATER_THAN
                # Missing 'threshold' field
            }
        ]
        
        subscribers = [
            {
                'type': SubscriberType.EMAIL,
                'address': 'invalid-email'  # Invalid email format
            }
        ]
        
        result = self.budgets_client._validate_alert_configurations(
            alert_thresholds, subscribers
        )
        
        self.assertFalse(result['valid'])
        self.assertTrue(any('missing \'threshold\' field' in error for error in result['errors']))
        self.assertTrue(any('invalid email address' in error for error in result['errors']))
    
    def test_build_budget_definition(self):
        """Test budget definition building."""
        budget_def = self.budgets_client._build_budget_definition(
            budget_name='test-budget',
            budget_amount=1000.0,
            time_unit=TimeUnit.MONTHLY,
            budget_type=BudgetType.COST,
            cost_filters=None
        )
        
        self.assertEqual(budget_def['BudgetName'], 'test-budget')
        self.assertEqual(budget_def['BudgetLimit']['Amount'], '1000.0')
        self.assertEqual(budget_def['BudgetLimit']['Unit'], 'USD')
        self.assertEqual(budget_def['TimeUnit'], TimeUnit.MONTHLY)
        self.assertEqual(budget_def['BudgetType'], BudgetType.COST)
        self.assertIn('TimePeriod', budget_def)
    
    def test_build_budget_notifications(self):
        """Test budget notification building."""
        alert_thresholds = [
            {
                'threshold': 80,
                'type': ThresholdType.PERCENTAGE,
                'comparison': ComparisonOperator.GREATER_THAN,
                'notification_type': NotificationType.ACTUAL
            }
        ]
        
        subscribers = [
            {
                'type': SubscriberType.EMAIL,
                'address': 'test@example.com'
            }
        ]
        
        notifications = self.budgets_client._build_budget_notifications(
            alert_thresholds, subscribers
        )
        
        self.assertEqual(len(notifications), 1)
        notification = notifications[0]
        
        self.assertEqual(notification['Notification']['Threshold'], 80)
        self.assertEqual(notification['Notification']['ComparisonOperator'], ComparisonOperator.GREATER_THAN)
        self.assertEqual(len(notification['Subscribers']), 1)
        self.assertEqual(notification['Subscribers'][0]['Address'], 'test@example.com')
    
    def test_assess_variance_risk(self):
        """Test variance risk assessment."""
        # Test different variance levels
        self.assertEqual(self.budgets_client._assess_variance_risk(-25), 'LOW')  # Significantly under budget
        self.assertEqual(self.budgets_client._assess_variance_risk(-5), 'LOW')   # Under budget
        self.assertEqual(self.budgets_client._assess_variance_risk(5), 'MEDIUM') # Slightly over budget
        self.assertEqual(self.budgets_client._assess_variance_risk(15), 'HIGH')  # Moderately over budget
        self.assertEqual(self.budgets_client._assess_variance_risk(30), 'CRITICAL') # Significantly over budget
    
    @patch('aws.budgets_client.datetime')
    def test_create_hierarchical_budget_dry_run(self, mock_datetime):
        """Test hierarchical budget creation in dry run mode."""
        # Mock datetime
        mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        
        # Mock existing budget check (budget doesn't exist)
        self.budgets_client._get_existing_budget = Mock(return_value=None)
        
        result = self.budgets_client.create_hierarchical_budget(
            budget_name='test-budget',
            budget_amount=1000.0,
            time_unit=TimeUnit.MONTHLY,
            budget_type=BudgetType.COST,
            dry_run=True
        )
        
        self.assertTrue(result['success'])
        self.assertIn('validated', result['message'])
        self.assertEqual(result['budget_name'], 'test-budget')
        self.assertTrue(result['budget_metadata']['dry_run'])
        
        # Verify AWS API was not called in dry run mode
        self.mock_aws_config.execute_with_retry.assert_not_called()
    
    def test_establish_budget_hierarchy(self):
        """Test budget hierarchy establishment."""
        self.budgets_client._establish_budget_hierarchy('child-budget', 'parent-budget')
        
        self.assertIn('parent-budget', self.budgets_client.budget_hierarchy)
        self.assertIn('child-budget', self.budgets_client.budget_hierarchy['parent-budget'])
    
    def test_calculate_detailed_variance_metrics(self):
        """Test detailed variance metrics calculation."""
        budget_details = {
            'BudgetLimit': {'Amount': '1000.0'},
            'TimeUnit': TimeUnit.MONTHLY
        }
        
        actual_spending = {
            'total_cost': {
                'UnblendedCost': {'Amount': '800.0'}
            }
        }
        
        metrics = self.budgets_client._calculate_detailed_variance_metrics(
            budget_details, actual_spending, analysis_period_days=30
        )
        
        self.assertEqual(metrics['budget_amount'], 1000.0)
        self.assertEqual(metrics['actual_spending'], 800.0)
        self.assertEqual(metrics['analysis_period_days'], 30)
        self.assertIn('variance_amount', metrics)
        self.assertIn('variance_percentage', metrics)
        self.assertIn('daily_burn_rate', metrics)
        self.assertIn('projected_monthly_spend', metrics)
    
    def test_analyze_spending_trends(self):
        """Test spending trend analysis."""
        actual_spending = {
            'cost_results': [
                {
                    'TimePeriod': {'Start': '2024-01-01'},
                    'Total': {'UnblendedCost': {'Amount': '30.0'}}
                },
                {
                    'TimePeriod': {'Start': '2024-01-02'},
                    'Total': {'UnblendedCost': {'Amount': '35.0'}}
                },
                {
                    'TimePeriod': {'Start': '2024-01-03'},
                    'Total': {'UnblendedCost': {'Amount': '40.0'}}
                }
            ]
        }
        
        trends = self.budgets_client._analyze_spending_trends(actual_spending)
        
        self.assertIn('avg_daily_spend', trends)
        self.assertIn('trend_direction', trends)
        self.assertIn('volatility', trends)
        self.assertEqual(trends['data_points'], 3)
        self.assertEqual(trends['trend_direction'], 'increasing')  # Spending is increasing
    
    def test_generate_budget_recommendations(self):
        """Test budget recommendation generation."""
        budget_details = {
            'BudgetLimit': {'Amount': '1000.0'}
        }
        
        variance_metrics = {
            'variance_percentage': 30,  # 30% over budget
            'budget_amount': 1000.0
        }
        
        trend_analysis = {
            'trend_direction': 'increasing',
            'volatility': 5.0,
            'avg_daily_spend': 35.0
        }
        
        recommendations = self.budgets_client._generate_budget_recommendations(
            budget_details, variance_metrics, trend_analysis
        )
        
        self.assertGreater(len(recommendations), 0)
        
        # Should recommend budget increase due to significant overspend
        budget_increase_rec = next(
            (rec for rec in recommendations if rec['type'] == 'budget_increase'), 
            None
        )
        self.assertIsNotNone(budget_increase_rec)
        self.assertEqual(budget_increase_rec['priority'], 'HIGH')


def run_tests():
    """Run all tests."""
    print("=== Running AWS Budgets Client Tests ===")
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestBudgetsClient)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n=== Test Results ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASS' if success else 'FAIL'}")
    
    return success


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)