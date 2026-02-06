#!/usr/bin/env python3
"""
AWS Budgets Client for Advanced FinOps Platform

Comprehensive AWS Budgets integration for budget synchronization, creation, management,
alert configuration, and forecast synchronization. This client provides hierarchical
budget support and variance tracking capabilities.

Features:
- Budget creation and management via AWS APIs with hierarchical support
- Budget alert configuration with custom thresholds
- Budget forecast synchronization and variance tracking
- Multi-account and multi-region budget management
- Cost allocation and budget inheritance
- Automated budget monitoring and reporting

Requirements: 10.4, 6.1, 6.3
"""

import logging
import boto3
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, Union
from botocore.exceptions import ClientError
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class BudgetType:
    """AWS Budget types supported by the service."""
    COST = "COST"
    USAGE = "USAGE"
    RI_COVERAGE = "RI_COVERAGE"
    RI_UTILIZATION = "RI_UTILIZATION"
    SAVINGS_PLANS_COVERAGE = "SAVINGS_PLANS_COVERAGE"
    SAVINGS_PLANS_UTILIZATION = "SAVINGS_PLANS_UTILIZATION"


class TimeUnit:
    """Time units for budget periods."""
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUALLY = "ANNUALLY"


class ComparisonOperator:
    """Comparison operators for budget alerts."""
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    EQUAL_TO = "EQUAL_TO"


class ThresholdType:
    """Types of budget thresholds."""
    PERCENTAGE = "PERCENTAGE"
    ABSOLUTE_VALUE = "ABSOLUTE_VALUE"


class NotificationType:
    """Types of budget notifications."""
    ACTUAL = "ACTUAL"
    FORECASTED = "FORECASTED"


class SubscriberType:
    """Types of budget notification subscribers."""
    EMAIL = "EMAIL"
    SNS = "SNS"


class BudgetsClient:
    """
    Comprehensive AWS Budgets client for budget management and cost governance.
    
    Provides advanced AWS Budgets integration including:
    - Hierarchical budget creation and management
    - Custom alert configuration with multiple thresholds
    - Budget forecast synchronization and variance tracking
    - Multi-account budget coordination
    - Cost allocation and budget inheritance
    - Automated budget monitoring and reporting
    """
    
    def __init__(self, aws_config, account_id: Optional[str] = None):
        """
        Initialize AWS Budgets client with comprehensive configuration.
        
        Args:
            aws_config: AWSConfig instance for client management
            account_id: AWS account ID (auto-detected if not provided)
        """
        self.aws_config = aws_config
        self.budgets_client = aws_config.get_budgets_client()
        self.account_id = account_id or aws_config.get_account_id()
        
        # Budget management state
        self.managed_budgets = {}
        self.budget_hierarchy = {}
        self.alert_configurations = {}
        self.forecast_data = {}
        
        logger.info(f"AWS Budgets Client initialized for account: {self.account_id}")
    
    def create_hierarchical_budget(self,
                                 budget_name: str,
                                 budget_amount: float,
                                 time_unit: str = TimeUnit.MONTHLY,
                                 budget_type: str = BudgetType.COST,
                                 parent_budget_name: Optional[str] = None,
                                 cost_filters: Optional[Dict[str, Any]] = None,
                                 alert_thresholds: Optional[List[Dict[str, Any]]] = None,
                                 subscribers: Optional[List[Dict[str, str]]] = None,
                                 dry_run: bool = True) -> Dict[str, Any]:
        """
        Create a hierarchical budget with AWS Budgets API integration.
        
        Supports hierarchical budget structures for organizations, teams, and projects
        with comprehensive alert configuration and cost allocation.
        
        Args:
            budget_name: Unique name for the budget
            budget_amount: Budget limit amount
            time_unit: Budget time period (MONTHLY, QUARTERLY, ANNUALLY)
            budget_type: Type of budget (COST, USAGE, RI_COVERAGE, etc.)
            parent_budget_name: Name of parent budget for hierarchy (optional)
            cost_filters: AWS cost filters to apply to budget
            alert_thresholds: List of alert threshold configurations
            subscribers: List of notification subscribers (email/SNS)
            dry_run: If True, validate but don't create budget
            
        Returns:
            Dictionary containing budget creation result and metadata
            
        Requirements: 10.4, 6.1, 6.3
        """
        try:
            logger.info(f"Creating hierarchical budget: {budget_name} (${budget_amount:,.2f} {time_unit})")
            
            if dry_run:
                logger.info("DRY_RUN: Budget creation validation only")
            
            # Validate budget parameters
            validation_result = self._validate_budget_parameters(
                budget_name, budget_amount, time_unit, budget_type, cost_filters
            )
            if not validation_result['valid']:
                raise ValueError(f"Budget validation failed: {validation_result['errors']}")
            
            # Check for existing budget
            existing_budget = self._get_existing_budget(budget_name)
            if existing_budget:
                logger.warning(f"Budget {budget_name} already exists")
                return {
                    'success': False,
                    'budget_name': budget_name,
                    'message': 'Budget already exists',
                    'existing_budget': existing_budget,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            # Build budget definition
            budget_definition = self._build_budget_definition(
                budget_name, budget_amount, time_unit, budget_type, cost_filters
            )
            
            # Build notifications if provided
            notifications = []
            if alert_thresholds and subscribers:
                notifications = self._build_budget_notifications(
                    alert_thresholds, subscribers
                )
            
            # Handle hierarchical structure
            if parent_budget_name:
                self._establish_budget_hierarchy(budget_name, parent_budget_name)
            
            # Create budget via AWS API
            if not dry_run:
                response = self.aws_config.execute_with_retry(
                    self.budgets_client.create_budget,
                    'budgets',
                    AccountId=self.account_id,
                    Budget=budget_definition,
                    NotificationsWithSubscribers=notifications
                )
                
                logger.info(f"Successfully created budget: {budget_name}")
            else:
                response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
                logger.info(f"DRY_RUN: Budget {budget_name} would be created successfully")
            
            # Store budget metadata
            budget_metadata = {
                'budget_name': budget_name,
                'budget_amount': budget_amount,
                'time_unit': time_unit,
                'budget_type': budget_type,
                'parent_budget': parent_budget_name,
                'cost_filters': cost_filters,
                'alert_count': len(alert_thresholds) if alert_thresholds else 0,
                'subscriber_count': len(subscribers) if subscribers else 0,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'dry_run': dry_run
            }
            
            self.managed_budgets[budget_name] = budget_metadata
            
            return {
                'success': True,
                'budget_name': budget_name,
                'budget_metadata': budget_metadata,
                'aws_response': response,
                'message': f"Budget {budget_name} {'validated' if dry_run else 'created'} successfully",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            error_msg = f"Failed to create budget {budget_name}: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'budget_name': budget_name,
                'error': str(e),
                'message': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def configure_budget_alerts(self,
                              budget_name: str,
                              alert_thresholds: List[Dict[str, Any]],
                              subscribers: List[Dict[str, str]],
                              dry_run: bool = True) -> Dict[str, Any]:
        """
        Configure custom alert thresholds for an existing budget.
        
        Supports multiple threshold types (percentage, absolute) and notification
        methods (email, SNS) with progressive alerting capabilities.
        
        Args:
            budget_name: Name of existing budget
            alert_thresholds: List of threshold configurations
            subscribers: List of notification subscribers
            dry_run: If True, validate but don't modify alerts
            
        Returns:
            Dictionary containing alert configuration result
            
        Requirements: 6.3
        """
        try:
            logger.info(f"Configuring alerts for budget: {budget_name}")
            
            if dry_run:
                logger.info("DRY_RUN: Alert configuration validation only")
            
            # Validate budget exists
            existing_budget = self._get_existing_budget(budget_name)
            if not existing_budget:
                raise ValueError(f"Budget {budget_name} does not exist")
            
            # Validate alert configurations
            validation_result = self._validate_alert_configurations(
                alert_thresholds, subscribers
            )
            if not validation_result['valid']:
                raise ValueError(f"Alert validation failed: {validation_result['errors']}")
            
            # Build notification configurations
            notifications = self._build_budget_notifications(alert_thresholds, subscribers)
            
            # Update budget notifications via AWS API
            if not dry_run:
                # Delete existing notifications first
                existing_notifications = self._get_existing_notifications(budget_name)
                for notification in existing_notifications:
                    self.aws_config.execute_with_retry(
                        self.budgets_client.delete_notification,
                        'budgets',
                        AccountId=self.account_id,
                        BudgetName=budget_name,
                        Notification=notification
                    )
                
                # Create new notifications
                for notification_config in notifications:
                    self.aws_config.execute_with_retry(
                        self.budgets_client.create_notification,
                        'budgets',
                        AccountId=self.account_id,
                        BudgetName=budget_name,
                        Notification=notification_config['Notification'],
                        Subscribers=notification_config['Subscribers']
                    )
                
                logger.info(f"Successfully configured {len(notifications)} alerts for budget: {budget_name}")
            else:
                logger.info(f"DRY_RUN: {len(notifications)} alerts would be configured for budget: {budget_name}")
            
            # Update alert configuration metadata
            alert_metadata = {
                'budget_name': budget_name,
                'alert_count': len(alert_thresholds),
                'subscriber_count': len(subscribers),
                'thresholds': alert_thresholds,
                'subscribers': subscribers,
                'configured_at': datetime.now(timezone.utc).isoformat(),
                'dry_run': dry_run
            }
            
            self.alert_configurations[budget_name] = alert_metadata
            
            return {
                'success': True,
                'budget_name': budget_name,
                'alert_metadata': alert_metadata,
                'message': f"Alerts for budget {budget_name} {'validated' if dry_run else 'configured'} successfully",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            error_msg = f"Failed to configure alerts for budget {budget_name}: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'budget_name': budget_name,
                'error': str(e),
                'message': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def synchronize_budget_forecasts(self,
                                   budget_names: Optional[List[str]] = None,
                                   forecast_horizon_months: int = 12) -> Dict[str, Any]:
        """
        Synchronize budget forecasts with AWS Cost Explorer predictions.
        
        Retrieves cost forecasts from AWS and compares with budget allocations
        to provide variance tracking and early warning capabilities.
        
        Args:
            budget_names: List of budget names to sync (all if None)
            forecast_horizon_months: Forecast period in months
            
        Returns:
            Dictionary containing forecast synchronization results
            
        Requirements: 10.4, 6.1
        """
        try:
            logger.info("Synchronizing budget forecasts with AWS Cost Explorer")
            
            # Get list of budgets to process
            if budget_names is None:
                budget_names = list(self.managed_budgets.keys())
                if not budget_names:
                    # Get all budgets from AWS if none managed locally
                    budget_names = self._get_all_budget_names()
            
            if not budget_names:
                logger.warning("No budgets found for forecast synchronization")
                return {
                    'success': True,
                    'message': 'No budgets found',
                    'forecasts': {},
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            logger.info(f"Synchronizing forecasts for {len(budget_names)} budgets")
            
            # Get Cost Explorer client for forecasting
            ce_client = self.aws_config.get_cost_explorer_client()
            
            forecast_results = {}
            
            for budget_name in budget_names:
                try:
                    logger.debug(f"Processing forecast for budget: {budget_name}")
                    
                    # Get budget details
                    budget_details = self._get_budget_details(budget_name)
                    if not budget_details:
                        logger.warning(f"Could not retrieve details for budget: {budget_name}")
                        continue
                    
                    # Generate forecast using Cost Explorer
                    forecast_data = self._generate_cost_forecast(
                        ce_client, budget_details, forecast_horizon_months
                    )
                    
                    # Calculate variance analysis
                    variance_analysis = self._calculate_budget_variance(
                        budget_details, forecast_data
                    )
                    
                    # Store forecast data
                    forecast_result = {
                        'budget_name': budget_name,
                        'budget_amount': budget_details.get('BudgetLimit', {}).get('Amount'),
                        'budget_unit': budget_details.get('BudgetLimit', {}).get('Unit'),
                        'forecast_data': forecast_data,
                        'variance_analysis': variance_analysis,
                        'forecast_horizon_months': forecast_horizon_months,
                        'synchronized_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    forecast_results[budget_name] = forecast_result
                    self.forecast_data[budget_name] = forecast_result
                    
                    logger.debug(f"Forecast synchronized for budget: {budget_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to sync forecast for budget {budget_name}: {e}")
                    forecast_results[budget_name] = {
                        'budget_name': budget_name,
                        'error': str(e),
                        'synchronized_at': datetime.now(timezone.utc).isoformat()
                    }
            
            successful_syncs = len([r for r in forecast_results.values() if 'error' not in r])
            
            logger.info(f"Forecast synchronization completed: {successful_syncs}/{len(budget_names)} successful")
            
            return {
                'success': True,
                'forecasts': forecast_results,
                'summary': {
                    'total_budgets': len(budget_names),
                    'successful_syncs': successful_syncs,
                    'failed_syncs': len(budget_names) - successful_syncs,
                    'forecast_horizon_months': forecast_horizon_months
                },
                'message': f"Synchronized forecasts for {successful_syncs} budgets",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            error_msg = f"Failed to synchronize budget forecasts: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': str(e),
                'message': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def track_budget_variance(self,
                            budget_name: str,
                            analysis_period_days: int = 30) -> Dict[str, Any]:
        """
        Track budget variance and spending patterns for a specific budget.
        
        Analyzes actual spending vs budget allocation with trend analysis
        and provides recommendations for budget adjustments.
        
        Args:
            budget_name: Name of budget to analyze
            analysis_period_days: Period for variance analysis
            
        Returns:
            Dictionary containing variance tracking results
            
        Requirements: 6.1, 6.3
        """
        try:
            logger.info(f"Tracking variance for budget: {budget_name}")
            
            # Get budget details
            budget_details = self._get_budget_details(budget_name)
            if not budget_details:
                raise ValueError(f"Budget {budget_name} not found")
            
            # Get actual spending data
            actual_spending = self._get_actual_spending(budget_name, analysis_period_days)
            
            # Calculate variance metrics
            variance_metrics = self._calculate_detailed_variance_metrics(
                budget_details, actual_spending, analysis_period_days
            )
            
            # Analyze spending trends
            trend_analysis = self._analyze_spending_trends(actual_spending)
            
            # Generate recommendations
            recommendations = self._generate_budget_recommendations(
                budget_details, variance_metrics, trend_analysis
            )
            
            # Prepare variance tracking result
            variance_result = {
                'budget_name': budget_name,
                'budget_details': {
                    'budget_limit': budget_details.get('BudgetLimit', {}),
                    'time_unit': budget_details.get('TimeUnit'),
                    'budget_type': budget_details.get('BudgetType')
                },
                'variance_metrics': variance_metrics,
                'trend_analysis': trend_analysis,
                'recommendations': recommendations,
                'analysis_period_days': analysis_period_days,
                'analyzed_at': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Variance tracking completed for budget: {budget_name}")
            
            return {
                'success': True,
                'variance_result': variance_result,
                'message': f"Variance tracking completed for budget {budget_name}",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            error_msg = f"Failed to track variance for budget {budget_name}: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'budget_name': budget_name,
                'error': str(e),
                'message': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def manage_budget_lifecycle(self,
                              budget_name: str,
                              action: str,
                              new_amount: Optional[float] = None,
                              dry_run: bool = True) -> Dict[str, Any]:
        """
        Manage budget lifecycle operations (update, delete, archive).
        
        Args:
            budget_name: Name of budget to manage
            action: Lifecycle action ('update', 'delete', 'archive')
            new_amount: New budget amount for update operations
            dry_run: If True, validate but don't execute action
            
        Returns:
            Dictionary containing lifecycle management result
        """
        try:
            logger.info(f"Managing budget lifecycle: {budget_name} - {action}")
            
            if dry_run:
                logger.info("DRY_RUN: Budget lifecycle validation only")
            
            # Validate budget exists
            budget_details = self._get_budget_details(budget_name)
            if not budget_details:
                raise ValueError(f"Budget {budget_name} not found")
            
            result = {}
            
            if action == 'update':
                if new_amount is None:
                    raise ValueError("new_amount required for update action")
                
                result = self._update_budget_amount(budget_name, new_amount, dry_run)
                
            elif action == 'delete':
                result = self._delete_budget(budget_name, dry_run)
                
            elif action == 'archive':
                result = self._archive_budget(budget_name, dry_run)
                
            else:
                raise ValueError(f"Invalid action: {action}. Must be 'update', 'delete', or 'archive'")
            
            return {
                'success': True,
                'budget_name': budget_name,
                'action': action,
                'result': result,
                'message': f"Budget {budget_name} {action} {'validated' if dry_run else 'completed'} successfully",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            error_msg = f"Failed to manage budget {budget_name} lifecycle ({action}): {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'budget_name': budget_name,
                'action': action,
                'error': str(e),
                'message': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_budget_status_report(self,
                               budget_names: Optional[List[str]] = None,
                               include_forecasts: bool = True,
                               include_variance: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive budget status report.
        
        Args:
            budget_names: List of budget names to include (all if None)
            include_forecasts: Include forecast data in report
            include_variance: Include variance analysis in report
            
        Returns:
            Dictionary containing comprehensive budget status report
        """
        try:
            logger.info("Generating budget status report")
            
            # Get list of budgets to report on
            if budget_names is None:
                budget_names = self._get_all_budget_names()
            
            if not budget_names:
                return {
                    'success': True,
                    'message': 'No budgets found',
                    'report': {},
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            report_data = {}
            
            for budget_name in budget_names:
                try:
                    budget_report = self._generate_individual_budget_report(
                        budget_name, include_forecasts, include_variance
                    )
                    report_data[budget_name] = budget_report
                    
                except Exception as e:
                    logger.error(f"Failed to generate report for budget {budget_name}: {e}")
                    report_data[budget_name] = {
                        'budget_name': budget_name,
                        'error': str(e),
                        'status': 'ERROR'
                    }
            
            # Generate summary statistics
            summary = self._generate_report_summary(report_data)
            
            logger.info(f"Budget status report generated for {len(budget_names)} budgets")
            
            return {
                'success': True,
                'report': {
                    'summary': summary,
                    'budgets': report_data,
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'include_forecasts': include_forecasts,
                    'include_variance': include_variance
                },
                'message': f"Budget status report generated for {len(budget_names)} budgets",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            error_msg = f"Failed to generate budget status report: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': str(e),
                'message': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    # Private helper methods
    
    def _validate_budget_parameters(self,
                                  budget_name: str,
                                  budget_amount: float,
                                  time_unit: str,
                                  budget_type: str,
                                  cost_filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate budget creation parameters."""
        errors = []
        
        # Validate budget name
        if not budget_name or len(budget_name) < 1 or len(budget_name) > 100:
            errors.append("Budget name must be 1-100 characters")
        
        # Validate budget amount
        if budget_amount <= 0:
            errors.append("Budget amount must be positive")
        
        # Validate time unit
        valid_time_units = [TimeUnit.DAILY, TimeUnit.MONTHLY, TimeUnit.QUARTERLY, TimeUnit.ANNUALLY]
        if time_unit not in valid_time_units:
            errors.append(f"Time unit must be one of: {valid_time_units}")
        
        # Validate budget type
        valid_budget_types = [
            BudgetType.COST, BudgetType.USAGE, BudgetType.RI_COVERAGE,
            BudgetType.RI_UTILIZATION, BudgetType.SAVINGS_PLANS_COVERAGE,
            BudgetType.SAVINGS_PLANS_UTILIZATION
        ]
        if budget_type not in valid_budget_types:
            errors.append(f"Budget type must be one of: {valid_budget_types}")
        
        # Validate cost filters if provided
        if cost_filters:
            filter_errors = self._validate_cost_filters(cost_filters)
            errors.extend(filter_errors)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_cost_filters(self, cost_filters: Dict[str, Any]) -> List[str]:
        """Validate AWS cost filters structure."""
        errors = []
        
        # Check for valid filter structure
        valid_filter_keys = ['Dimensions', 'Tags', 'CostCategories', 'And', 'Or', 'Not']
        
        for key in cost_filters.keys():
            if key not in valid_filter_keys:
                errors.append(f"Invalid filter key: {key}")
        
        # Validate dimensions if present
        if 'Dimensions' in cost_filters:
            dimensions = cost_filters['Dimensions']
            if not isinstance(dimensions, dict):
                errors.append("Dimensions must be a dictionary")
            else:
                required_dim_keys = ['Key', 'Values']
                for req_key in required_dim_keys:
                    if req_key not in dimensions:
                        errors.append(f"Dimensions missing required key: {req_key}")
        
        return errors
    
    def _get_existing_budget(self, budget_name: str) -> Optional[Dict[str, Any]]:
        """Check if budget already exists."""
        try:
            response = self.aws_config.execute_with_retry(
                self.budgets_client.describe_budget,
                'budgets',
                AccountId=self.account_id,
                BudgetName=budget_name
            )
            return response.get('Budget')
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'NotFoundException':
                return None
            raise
    
    def _build_budget_definition(self,
                               budget_name: str,
                               budget_amount: float,
                               time_unit: str,
                               budget_type: str,
                               cost_filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build AWS budget definition structure."""
        # Calculate time period
        now = datetime.now(timezone.utc)
        if time_unit == TimeUnit.MONTHLY:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1)
        elif time_unit == TimeUnit.QUARTERLY:
            quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            start_date = now.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=90)  # Approximate quarter
        else:  # ANNUALLY
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(year=start_date.year + 1)
        
        budget_definition = {
            'BudgetName': budget_name,
            'BudgetLimit': {
                'Amount': str(budget_amount),
                'Unit': 'USD'
            },
            'TimeUnit': time_unit,
            'BudgetType': budget_type,
            'TimePeriod': {
                'Start': start_date,
                'End': end_date
            }
        }
        
        # Add cost filters if provided
        if cost_filters:
            budget_definition['CostFilters'] = cost_filters
        
        return budget_definition
    
    def _validate_alert_configurations(self,
                                     alert_thresholds: List[Dict[str, Any]],
                                     subscribers: List[Dict[str, str]]) -> Dict[str, Any]:
        """Validate alert threshold and subscriber configurations."""
        errors = []
        
        # Validate alert thresholds
        for i, threshold in enumerate(alert_thresholds):
            if 'threshold' not in threshold:
                errors.append(f"Alert {i}: missing 'threshold' field")
            elif not isinstance(threshold['threshold'], (int, float)) or threshold['threshold'] <= 0:
                errors.append(f"Alert {i}: threshold must be positive number")
            
            if 'type' not in threshold:
                errors.append(f"Alert {i}: missing 'type' field")
            elif threshold['type'] not in [ThresholdType.PERCENTAGE, ThresholdType.ABSOLUTE_VALUE]:
                errors.append(f"Alert {i}: invalid threshold type")
            
            if 'comparison' not in threshold:
                errors.append(f"Alert {i}: missing 'comparison' field")
            elif threshold['comparison'] not in [ComparisonOperator.GREATER_THAN, ComparisonOperator.LESS_THAN, ComparisonOperator.EQUAL_TO]:
                errors.append(f"Alert {i}: invalid comparison operator")
        
        # Validate subscribers
        for i, subscriber in enumerate(subscribers):
            if 'type' not in subscriber:
                errors.append(f"Subscriber {i}: missing 'type' field")
            elif subscriber['type'] not in [SubscriberType.EMAIL, SubscriberType.SNS]:
                errors.append(f"Subscriber {i}: invalid subscriber type")
            
            if 'address' not in subscriber:
                errors.append(f"Subscriber {i}: missing 'address' field")
            elif subscriber['type'] == SubscriberType.EMAIL and '@' not in subscriber['address']:
                errors.append(f"Subscriber {i}: invalid email address")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _build_budget_notifications(self,
                                  alert_thresholds: List[Dict[str, Any]],
                                  subscribers: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Build AWS budget notification configurations."""
        notifications = []
        
        for threshold in alert_thresholds:
            notification = {
                'Notification': {
                    'NotificationType': threshold.get('notification_type', NotificationType.ACTUAL),
                    'ComparisonOperator': threshold['comparison'],
                    'Threshold': threshold['threshold']
                },
                'Subscribers': [
                    {
                        'SubscriptionType': sub['type'],
                        'Address': sub['address']
                    }
                    for sub in subscribers
                ]
            }
            
            # Add threshold type if specified
            if threshold.get('type') == ThresholdType.ABSOLUTE_VALUE:
                notification['Notification']['ThresholdType'] = ThresholdType.ABSOLUTE_VALUE
            
            notifications.append(notification)
        
        return notifications
    
    def _establish_budget_hierarchy(self, budget_name: str, parent_budget_name: str) -> None:
        """Establish hierarchical relationship between budgets."""
        if parent_budget_name not in self.budget_hierarchy:
            self.budget_hierarchy[parent_budget_name] = []
        
        self.budget_hierarchy[parent_budget_name].append(budget_name)
        logger.debug(f"Established hierarchy: {parent_budget_name} -> {budget_name}")
    
    def _get_existing_notifications(self, budget_name: str) -> List[Dict[str, Any]]:
        """Get existing notifications for a budget."""
        try:
            response = self.aws_config.execute_with_retry(
                self.budgets_client.describe_notifications_for_budget,
                'budgets',
                AccountId=self.account_id,
                BudgetName=budget_name
            )
            return response.get('Notifications', [])
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'NotFoundException':
                return []
            raise
    
    def _get_all_budget_names(self) -> List[str]:
        """Get all budget names from AWS."""
        try:
            response = self.aws_config.execute_with_retry(
                self.budgets_client.describe_budgets,
                'budgets',
                AccountId=self.account_id
            )
            return [budget['BudgetName'] for budget in response.get('Budgets', [])]
        except Exception as e:
            logger.error(f"Failed to get budget names: {e}")
            return []
    
    def _get_budget_details(self, budget_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed budget information."""
        try:
            response = self.aws_config.execute_with_retry(
                self.budgets_client.describe_budget,
                'budgets',
                AccountId=self.account_id,
                BudgetName=budget_name
            )
            return response.get('Budget')
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'NotFoundException':
                return None
            raise
    
    def _generate_cost_forecast(self,
                              ce_client: Any,
                              budget_details: Dict[str, Any],
                              forecast_horizon_months: int) -> Dict[str, Any]:
        """Generate cost forecast using Cost Explorer."""
        try:
            # Calculate forecast period
            start_date = datetime.now(timezone.utc).date()
            end_date = start_date + timedelta(days=30 * forecast_horizon_months)
            
            # Build forecast request
            forecast_request = {
                'TimePeriod': {
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                'Metric': 'UNBLENDED_COST',
                'Granularity': 'MONTHLY'
            }
            
            # Add cost filters from budget if available
            if 'CostFilters' in budget_details:
                forecast_request['Filter'] = budget_details['CostFilters']
            
            # Get forecast from Cost Explorer
            response = self.aws_config.execute_with_retry(
                ce_client.get_cost_forecast,
                'ce',
                **forecast_request
            )
            
            return {
                'forecast_results': response.get('ForecastResultsByTime', []),
                'total_forecast': response.get('Total', {}),
                'forecast_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'months': forecast_horizon_months
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate cost forecast: {e}")
            return {
                'error': str(e),
                'forecast_period': {
                    'start': start_date.isoformat() if 'start_date' in locals() else None,
                    'end': end_date.isoformat() if 'end_date' in locals() else None,
                    'months': forecast_horizon_months
                }
            }
    
    def _calculate_budget_variance(self,
                                 budget_details: Dict[str, Any],
                                 forecast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate variance between budget and forecast."""
        try:
            budget_amount = float(budget_details.get('BudgetLimit', {}).get('Amount', 0))
            
            if 'total_forecast' in forecast_data and 'Amount' in forecast_data['total_forecast']:
                forecast_amount = float(forecast_data['total_forecast']['Amount'])
                
                variance_amount = forecast_amount - budget_amount
                variance_percentage = (variance_amount / budget_amount * 100) if budget_amount > 0 else 0
                
                return {
                    'budget_amount': budget_amount,
                    'forecast_amount': forecast_amount,
                    'variance_amount': variance_amount,
                    'variance_percentage': variance_percentage,
                    'status': 'over_budget' if variance_amount > 0 else 'under_budget',
                    'risk_level': self._assess_variance_risk(variance_percentage)
                }
            else:
                return {
                    'budget_amount': budget_amount,
                    'forecast_amount': None,
                    'variance_amount': None,
                    'variance_percentage': None,
                    'status': 'forecast_unavailable',
                    'risk_level': 'UNKNOWN'
                }
                
        except Exception as e:
            logger.error(f"Failed to calculate budget variance: {e}")
            return {
                'error': str(e),
                'status': 'calculation_failed'
            }
    
    def _assess_variance_risk(self, variance_percentage: float) -> str:
        """Assess risk level based on variance percentage."""
        if variance_percentage <= -20:
            return 'LOW'  # Significantly under budget
        elif variance_percentage <= 0:
            return 'LOW'  # Under budget
        elif variance_percentage <= 10:
            return 'MEDIUM'  # Slightly over budget
        elif variance_percentage <= 25:
            return 'HIGH'  # Moderately over budget
        else:
            return 'CRITICAL'  # Significantly over budget
    
    def _get_actual_spending(self, budget_name: str, analysis_period_days: int) -> Dict[str, Any]:
        """Get actual spending data for variance analysis."""
        try:
            # Get budget details to understand cost filters
            budget_details = self._get_budget_details(budget_name)
            if not budget_details:
                raise ValueError(f"Budget {budget_name} not found")
            
            # Calculate analysis period
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date - timedelta(days=analysis_period_days)
            
            # Get Cost Explorer client
            ce_client = self.aws_config.get_cost_explorer_client()
            
            # Build cost query
            cost_request = {
                'TimePeriod': {
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                'Granularity': 'DAILY',
                'Metrics': ['UnblendedCost']
            }
            
            # Add cost filters from budget if available
            if 'CostFilters' in budget_details:
                cost_request['Filter'] = budget_details['CostFilters']
            
            # Get actual costs
            response = self.aws_config.execute_with_retry(
                ce_client.get_cost_and_usage,
                'ce',
                **cost_request
            )
            
            return {
                'cost_results': response.get('ResultsByTime', []),
                'total_cost': response.get('Total', {}),
                'analysis_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': analysis_period_days
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get actual spending for budget {budget_name}: {e}")
            return {
                'error': str(e),
                'analysis_period': {
                    'start': start_date.isoformat() if 'start_date' in locals() else None,
                    'end': end_date.isoformat() if 'end_date' in locals() else None,
                    'days': analysis_period_days
                }
            }
    
    def _calculate_detailed_variance_metrics(self,
                                           budget_details: Dict[str, Any],
                                           actual_spending: Dict[str, Any],
                                           analysis_period_days: int) -> Dict[str, Any]:
        """Calculate detailed variance metrics."""
        try:
            budget_amount = float(budget_details.get('BudgetLimit', {}).get('Amount', 0))
            time_unit = budget_details.get('TimeUnit', TimeUnit.MONTHLY)
            
            # Calculate daily budget allocation
            if time_unit == TimeUnit.MONTHLY:
                daily_budget = budget_amount / 30
            elif time_unit == TimeUnit.QUARTERLY:
                daily_budget = budget_amount / 90
            elif time_unit == TimeUnit.ANNUALLY:
                daily_budget = budget_amount / 365
            else:  # DAILY
                daily_budget = budget_amount
            
            # Calculate expected spending for analysis period
            expected_spending = daily_budget * analysis_period_days
            
            # Get actual spending amount
            actual_amount = 0
            if 'total_cost' in actual_spending and 'UnblendedCost' in actual_spending['total_cost']:
                actual_amount = float(actual_spending['total_cost']['UnblendedCost']['Amount'])
            
            # Calculate variance metrics
            variance_amount = actual_amount - expected_spending
            variance_percentage = (variance_amount / expected_spending * 100) if expected_spending > 0 else 0
            
            # Calculate burn rate
            daily_burn_rate = actual_amount / analysis_period_days if analysis_period_days > 0 else 0
            projected_monthly_spend = daily_burn_rate * 30
            
            return {
                'budget_amount': budget_amount,
                'time_unit': time_unit,
                'analysis_period_days': analysis_period_days,
                'expected_spending': expected_spending,
                'actual_spending': actual_amount,
                'variance_amount': variance_amount,
                'variance_percentage': variance_percentage,
                'daily_budget_allocation': daily_budget,
                'daily_burn_rate': daily_burn_rate,
                'projected_monthly_spend': projected_monthly_spend,
                'budget_utilization_percentage': (projected_monthly_spend / budget_amount * 100) if budget_amount > 0 else 0,
                'risk_level': self._assess_variance_risk(variance_percentage)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate detailed variance metrics: {e}")
            return {
                'error': str(e),
                'analysis_period_days': analysis_period_days
            }
    
    def _analyze_spending_trends(self, actual_spending: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze spending trends from actual spending data."""
        try:
            cost_results = actual_spending.get('cost_results', [])
            if not cost_results:
                return {'error': 'No cost data available for trend analysis'}
            
            # Extract daily spending amounts
            daily_amounts = []
            dates = []
            
            for result in cost_results:
                if 'Total' in result and 'UnblendedCost' in result['Total']:
                    amount = float(result['Total']['UnblendedCost']['Amount'])
                    daily_amounts.append(amount)
                    dates.append(result['TimePeriod']['Start'])
            
            if len(daily_amounts) < 2:
                return {'error': 'Insufficient data for trend analysis'}
            
            # Calculate trend metrics
            avg_daily_spend = sum(daily_amounts) / len(daily_amounts)
            max_daily_spend = max(daily_amounts)
            min_daily_spend = min(daily_amounts)
            
            # Calculate trend direction (simple linear trend)
            n = len(daily_amounts)
            x_sum = sum(range(n))
            y_sum = sum(daily_amounts)
            xy_sum = sum(i * amount for i, amount in enumerate(daily_amounts))
            x2_sum = sum(i * i for i in range(n))
            
            # Linear regression slope
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum) if (n * x2_sum - x_sum * x_sum) != 0 else 0
            
            # Determine trend direction
            if slope > 0.01:
                trend_direction = 'increasing'
            elif slope < -0.01:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
            
            # Calculate volatility (standard deviation)
            variance = sum((amount - avg_daily_spend) ** 2 for amount in daily_amounts) / len(daily_amounts)
            volatility = variance ** 0.5
            
            return {
                'avg_daily_spend': avg_daily_spend,
                'max_daily_spend': max_daily_spend,
                'min_daily_spend': min_daily_spend,
                'trend_direction': trend_direction,
                'trend_slope': slope,
                'volatility': volatility,
                'data_points': len(daily_amounts),
                'analysis_period': actual_spending.get('analysis_period', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze spending trends: {e}")
            return {
                'error': str(e)
            }
    
    def _generate_budget_recommendations(self,
                                       budget_details: Dict[str, Any],
                                       variance_metrics: Dict[str, Any],
                                       trend_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate budget adjustment recommendations."""
        recommendations = []
        
        try:
            # Recommendation based on variance
            if 'variance_percentage' in variance_metrics:
                variance_pct = variance_metrics['variance_percentage']
                
                if variance_pct > 25:
                    recommendations.append({
                        'type': 'budget_increase',
                        'priority': 'HIGH',
                        'description': f'Consider increasing budget by {variance_pct:.1f}% due to significant overspend',
                        'suggested_amount': variance_metrics.get('budget_amount', 0) * (1 + variance_pct / 100),
                        'rationale': 'Current spending significantly exceeds budget allocation'
                    })
                elif variance_pct < -20:
                    recommendations.append({
                        'type': 'budget_optimization',
                        'priority': 'MEDIUM',
                        'description': f'Budget may be over-allocated by {abs(variance_pct):.1f}%',
                        'suggested_amount': variance_metrics.get('budget_amount', 0) * (1 + variance_pct / 100),
                        'rationale': 'Consistent underspending indicates potential for budget optimization'
                    })
            
            # Recommendation based on trend
            if 'trend_direction' in trend_analysis:
                if trend_analysis['trend_direction'] == 'increasing':
                    recommendations.append({
                        'type': 'trend_alert',
                        'priority': 'MEDIUM',
                        'description': 'Spending trend is increasing - monitor closely',
                        'rationale': 'Upward spending trend may lead to budget overrun'
                    })
                elif trend_analysis['trend_direction'] == 'decreasing':
                    recommendations.append({
                        'type': 'cost_optimization',
                        'priority': 'LOW',
                        'description': 'Decreasing spend trend - good cost management',
                        'rationale': 'Downward trend indicates effective cost control'
                    })
            
            # Recommendation based on volatility
            if 'volatility' in trend_analysis and 'avg_daily_spend' in trend_analysis:
                volatility_ratio = trend_analysis['volatility'] / trend_analysis['avg_daily_spend']
                if volatility_ratio > 0.5:
                    recommendations.append({
                        'type': 'spending_volatility',
                        'priority': 'MEDIUM',
                        'description': 'High spending volatility detected - investigate irregular patterns',
                        'rationale': 'Irregular spending patterns may indicate inefficient resource usage'
                    })
            
            # Alert configuration recommendations
            if not recommendations:
                recommendations.append({
                    'type': 'monitoring',
                    'priority': 'LOW',
                    'description': 'Budget is performing within expected parameters',
                    'rationale': 'Continue current monitoring and alert configuration'
                })
            
        except Exception as e:
            logger.error(f"Failed to generate budget recommendations: {e}")
            recommendations.append({
                'type': 'error',
                'priority': 'HIGH',
                'description': f'Failed to generate recommendations: {e}',
                'rationale': 'Manual review required due to analysis error'
            })
        
        return recommendations
    
    def _update_budget_amount(self, budget_name: str, new_amount: float, dry_run: bool) -> Dict[str, Any]:
        """Update budget amount."""
        try:
            budget_details = self._get_budget_details(budget_name)
            if not budget_details:
                raise ValueError(f"Budget {budget_name} not found")
            
            # Update budget amount
            budget_details['BudgetLimit']['Amount'] = str(new_amount)
            
            if not dry_run:
                self.aws_config.execute_with_retry(
                    self.budgets_client.update_budget,
                    'budgets',
                    AccountId=self.account_id,
                    NewBudget=budget_details
                )
                logger.info(f"Updated budget {budget_name} amount to ${new_amount:,.2f}")
            else:
                logger.info(f"DRY_RUN: Would update budget {budget_name} amount to ${new_amount:,.2f}")
            
            return {
                'action': 'update',
                'old_amount': float(budget_details['BudgetLimit']['Amount']),
                'new_amount': new_amount,
                'dry_run': dry_run
            }
            
        except Exception as e:
            logger.error(f"Failed to update budget {budget_name}: {e}")
            raise
    
    def _delete_budget(self, budget_name: str, dry_run: bool) -> Dict[str, Any]:
        """Delete budget."""
        try:
            if not dry_run:
                self.aws_config.execute_with_retry(
                    self.budgets_client.delete_budget,
                    'budgets',
                    AccountId=self.account_id,
                    BudgetName=budget_name
                )
                logger.info(f"Deleted budget: {budget_name}")
                
                # Remove from local tracking
                if budget_name in self.managed_budgets:
                    del self.managed_budgets[budget_name]
                if budget_name in self.alert_configurations:
                    del self.alert_configurations[budget_name]
                if budget_name in self.forecast_data:
                    del self.forecast_data[budget_name]
            else:
                logger.info(f"DRY_RUN: Would delete budget: {budget_name}")
            
            return {
                'action': 'delete',
                'budget_name': budget_name,
                'dry_run': dry_run
            }
            
        except Exception as e:
            logger.error(f"Failed to delete budget {budget_name}: {e}")
            raise
    
    def _archive_budget(self, budget_name: str, dry_run: bool) -> Dict[str, Any]:
        """Archive budget (disable alerts but keep budget)."""
        try:
            # Get existing notifications
            notifications = self._get_existing_notifications(budget_name)
            
            if not dry_run:
                # Delete all notifications to effectively "archive" the budget
                for notification in notifications:
                    self.aws_config.execute_with_retry(
                        self.budgets_client.delete_notification,
                        'budgets',
                        AccountId=self.account_id,
                        BudgetName=budget_name,
                        Notification=notification
                    )
                
                logger.info(f"Archived budget {budget_name} (removed {len(notifications)} notifications)")
            else:
                logger.info(f"DRY_RUN: Would archive budget {budget_name} (remove {len(notifications)} notifications)")
            
            return {
                'action': 'archive',
                'budget_name': budget_name,
                'notifications_removed': len(notifications),
                'dry_run': dry_run
            }
            
        except Exception as e:
            logger.error(f"Failed to archive budget {budget_name}: {e}")
            raise
    
    def _generate_individual_budget_report(self,
                                         budget_name: str,
                                         include_forecasts: bool,
                                         include_variance: bool) -> Dict[str, Any]:
        """Generate report for individual budget."""
        try:
            # Get budget details
            budget_details = self._get_budget_details(budget_name)
            if not budget_details:
                return {
                    'budget_name': budget_name,
                    'status': 'NOT_FOUND',
                    'error': 'Budget not found'
                }
            
            report = {
                'budget_name': budget_name,
                'status': 'ACTIVE',
                'budget_details': {
                    'amount': budget_details.get('BudgetLimit', {}).get('Amount'),
                    'unit': budget_details.get('BudgetLimit', {}).get('Unit'),
                    'type': budget_details.get('BudgetType'),
                    'time_unit': budget_details.get('TimeUnit')
                }
            }
            
            # Add forecast data if requested
            if include_forecasts and budget_name in self.forecast_data:
                report['forecast_data'] = self.forecast_data[budget_name]
            
            # Add variance analysis if requested
            if include_variance:
                variance_result = self.track_budget_variance(budget_name, analysis_period_days=30)
                if variance_result['success']:
                    report['variance_analysis'] = variance_result['variance_result']
            
            # Add alert configuration
            if budget_name in self.alert_configurations:
                report['alert_configuration'] = self.alert_configurations[budget_name]
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate report for budget {budget_name}: {e}")
            return {
                'budget_name': budget_name,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _generate_report_summary(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for budget report."""
        try:
            total_budgets = len(report_data)
            active_budgets = len([r for r in report_data.values() if r.get('status') == 'ACTIVE'])
            error_budgets = len([r for r in report_data.values() if r.get('status') == 'ERROR'])
            
            # Calculate total budget amounts
            total_budget_amount = 0
            for report in report_data.values():
                if report.get('status') == 'ACTIVE' and 'budget_details' in report:
                    amount_str = report['budget_details'].get('amount', '0')
                    try:
                        total_budget_amount += float(amount_str)
                    except (ValueError, TypeError):
                        continue
            
            # Count budgets by risk level
            risk_levels = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0, 'UNKNOWN': 0}
            for report in report_data.values():
                if 'variance_analysis' in report and 'variance_metrics' in report['variance_analysis']:
                    risk_level = report['variance_analysis']['variance_metrics'].get('risk_level', 'UNKNOWN')
                    if risk_level in risk_levels:
                        risk_levels[risk_level] += 1
            
            return {
                'total_budgets': total_budgets,
                'active_budgets': active_budgets,
                'error_budgets': error_budgets,
                'total_budget_amount': total_budget_amount,
                'risk_distribution': risk_levels,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate report summary: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }


# Example usage and testing functions
def main():
    """Example usage of BudgetsClient."""
    import sys
    import os
    
    # Add utils directory to path for imports
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
    
    try:
        from aws_config import AWSConfig
        
        # Initialize AWS configuration
        aws_config = AWSConfig(region='us-east-1')
        
        # Initialize budgets client
        budgets_client = BudgetsClient(aws_config)
        
        print("=== AWS Budgets Client Test ===")
        
        # Test budget creation (DRY_RUN)
        print("\n1. Testing budget creation...")
        
        alert_thresholds = [
            {
                'threshold': 80,
                'type': ThresholdType.PERCENTAGE,
                'comparison': ComparisonOperator.GREATER_THAN,
                'notification_type': NotificationType.ACTUAL
            },
            {
                'threshold': 100,
                'type': ThresholdType.PERCENTAGE,
                'comparison': ComparisonOperator.GREATER_THAN,
                'notification_type': NotificationType.FORECASTED
            }
        ]
        
        subscribers = [
            {
                'type': SubscriberType.EMAIL,
                'address': 'admin@example.com'
            }
        ]
        
        cost_filters = {
            'Dimensions': {
                'Key': 'SERVICE',
                'Values': ['Amazon Elastic Compute Cloud - Compute'],
                'MatchOptions': ['EQUALS']
            }
        }
        
        result = budgets_client.create_hierarchical_budget(
            budget_name='test-ec2-budget',
            budget_amount=1000.0,
            time_unit=TimeUnit.MONTHLY,
            budget_type=BudgetType.COST,
            cost_filters=cost_filters,
            alert_thresholds=alert_thresholds,
            subscribers=subscribers,
            dry_run=True
        )
        
        print(f"Budget creation result: {result['success']}")
        print(f"Message: {result['message']}")
        
        # Test forecast synchronization
        print("\n2. Testing forecast synchronization...")
        
        forecast_result = budgets_client.synchronize_budget_forecasts(
            budget_names=['test-ec2-budget'],
            forecast_horizon_months=6
        )
        
        print(f"Forecast sync result: {forecast_result['success']}")
        print(f"Message: {forecast_result['message']}")
        
        # Test budget status report
        print("\n3. Testing budget status report...")
        
        report_result = budgets_client.get_budget_status_report(
            include_forecasts=True,
            include_variance=True
        )
        
        print(f"Report generation result: {report_result['success']}")
        print(f"Message: {report_result['message']}")
        
        print("\n=== AWS Budgets Client Test Completed ===")
        
    except Exception as e:
        print(f"Test failed: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())