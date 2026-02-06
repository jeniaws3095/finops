#!/usr/bin/env python3
"""
Budget Manager for Advanced FinOps Platform

Core budget management engine that:
- Supports hierarchical budget structures for organizations, teams, and projects
- Analyzes historical spending trends and seasonal patterns for forecasting
- Incorporates planned infrastructure changes and growth projections
- Provides confidence intervals and scenario analysis for cost forecasts
- Tracks actual vs. predicted spending and adjusts models
- Sends progressive alerts at configurable percentages
- Triggers approval workflows for additional spending
- Provides detailed cost breakdowns and variance analysis

Requirements: 5.1, 5.2, 5.3, 6.1, 6.3
"""

import logging
import statistics
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
import json
import math

logger = logging.getLogger(__name__)


class BudgetType(Enum):
    """Types of budget hierarchies."""
    ORGANIZATION = "organization"
    TEAM = "team"
    PROJECT = "project"
    SERVICE = "service"
    REGION = "region"


class ForecastModel(Enum):
    """Types of forecasting models."""
    LINEAR_TREND = "linear_trend"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    GROWTH_PROJECTION = "growth_projection"


class AlertThreshold(Enum):
    """Budget alert threshold levels."""
    WARNING_50 = 0.50
    WARNING_75 = 0.75
    CRITICAL_90 = 0.90
    EXCEEDED_100 = 1.00


class BudgetStatus(Enum):
    """Budget status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"


class ApprovalLevel(Enum):
    """Approval levels for budget overruns."""
    AUTOMATIC = "automatic"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"


class BudgetManager:
    """
    Advanced budget management system with hierarchical structure support,
    predictive forecasting, and automated alerting.
    """

    def __init__(self, dry_run: bool = True):
        """
        Initialize the Budget Manager.
        
        Args:
            dry_run: If True, no actual budget modifications will be made
        """
        self.dry_run = dry_run
        self.budgets = {}  # Hierarchical budget storage
        self.forecasts = {}  # Cost forecasts by budget
        self.alerts = []  # Active budget alerts
        self.approval_workflows = []  # Pending approval requests
        self.historical_data = {}  # Historical spending data
        self.seasonal_patterns = {}  # Seasonal adjustment factors
        self.BudgetType = BudgetType
        
        logger.info(f"Budget Manager initialized (DRY_RUN: {dry_run})")

    def create_hierarchical_budget(
        self,
        budget_id: str,
        budget_type: BudgetType,
        parent_budget_id: Optional[str],
        budget_amount: float,
        period_months: int = 12,
        currency: str = "USD",
        tags: Optional[Dict[str, str]] = None,
        allocation_rules: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a hierarchical budget structure.
        
        Args:
            budget_id: Unique identifier for the budget
            budget_type: Type of budget (organization, team, project, etc.)
            parent_budget_id: Parent budget ID for hierarchical structure
            budget_amount: Total budget amount for the period
            period_months: Budget period in months
            currency: Currency code (default: USD)
            tags: Resource tags for cost allocation
            allocation_rules: Rules for automatic cost allocation
            
        Returns:
            Dict containing budget configuration and metadata
        """
        try:
            # Validate parent budget exists if specified
            if parent_budget_id and parent_budget_id not in self.budgets:
                raise ValueError(f"Parent budget {parent_budget_id} does not exist")
            
            # Calculate monthly budget allocation
            monthly_amount = budget_amount / period_months
            
            budget_config = {
                "budget_id": budget_id,
                "budget_type": budget_type.value,
                "parent_budget_id": parent_budget_id,
                "budget_amount": budget_amount,
                "monthly_amount": monthly_amount,
                "period_months": period_months,
                "currency": currency,
                "tags": tags or {},
                "allocation_rules": allocation_rules or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": BudgetStatus.HEALTHY.value,
                "current_spend": 0.0,
                "forecasted_spend": 0.0,
                "variance": 0.0,
                "alert_thresholds": {
                    "warning_50": budget_amount * AlertThreshold.WARNING_50.value,
                    "warning_75": budget_amount * AlertThreshold.WARNING_75.value,
                    "critical_90": budget_amount * AlertThreshold.CRITICAL_90.value,
                    "exceeded_100": budget_amount * AlertThreshold.EXCEEDED_100.value
                },
                "child_budgets": [],
                "approval_workflows": []
            }
            
            # Add to parent's child budgets if applicable
            if parent_budget_id:
                if parent_budget_id in self.budgets:
                    self.budgets[parent_budget_id]["child_budgets"].append(budget_id)
                else:
                    # In dry_run mode, we still need to track relationships
                    logger.warning(f"Parent budget {parent_budget_id} not found in storage")
            
            # Store budget configuration (even in dry_run for testing/demo purposes)
            self.budgets[budget_id] = budget_config
            
            if self.dry_run:
                logger.info(f"DRY_RUN: Created budget {budget_id} with amount {budget_amount}")
            else:
                logger.info(f"Created hierarchical budget: {budget_id} ({budget_type.value})")
            
            return budget_config
            
        except Exception as e:
            logger.error(f"Error creating hierarchical budget {budget_id}: {str(e)}")
            raise

    def analyze_historical_trends(
        self,
        budget_id: str,
        historical_data: List[Dict[str, Any]],
        analysis_months: int = 12
    ) -> Dict[str, Any]:
        """
        Analyze historical spending trends and seasonal patterns.
        
        Args:
            budget_id: Budget identifier
            historical_data: List of historical cost data points
            analysis_months: Number of months to analyze
            
        Returns:
            Dict containing trend analysis and seasonal patterns
        """
        try:
            if not historical_data:
                logger.warning(f"No historical data available for budget {budget_id}")
                return {"trend": "insufficient_data", "seasonal_factors": {}}
            
            # Sort data by date
            sorted_data = sorted(historical_data, key=lambda x: x.get("date", ""))
            
            # Extract monthly costs
            monthly_costs = []
            dates = []
            
            for data_point in sorted_data[-analysis_months:]:
                cost = data_point.get("cost", 0.0)
                date = data_point.get("date", "")
                monthly_costs.append(cost)
                dates.append(date)
            
            if len(monthly_costs) < 3:
                return {"trend": "insufficient_data", "seasonal_factors": {}}
            
            # Calculate trend analysis
            trend_analysis = self._calculate_trend(monthly_costs)
            
            # Calculate seasonal patterns
            seasonal_factors = self._calculate_seasonal_patterns(monthly_costs, dates)
            
            # Store for future use
            self.historical_data[budget_id] = {
                "monthly_costs": monthly_costs,
                "dates": dates,
                "trend_analysis": trend_analysis,
                "seasonal_factors": seasonal_factors,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Analyzed historical trends for budget {budget_id}")
            
            return {
                "trend": trend_analysis,
                "seasonal_factors": seasonal_factors,
                "data_points": len(monthly_costs),
                "analysis_period_months": analysis_months
            }
            
        except Exception as e:
            logger.error(f"Error analyzing historical trends for {budget_id}: {str(e)}")
            raise

    def generate_cost_forecast(
        self,
        budget_id: str,
        forecast_months: int = 6,
        growth_projections: Optional[Dict[str, float]] = None,
        infrastructure_changes: Optional[List[Dict[str, Any]]] = None,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Generate cost forecasts with confidence intervals and scenario analysis.
        
        Args:
            budget_id: Budget identifier
            forecast_months: Number of months to forecast
            growth_projections: Expected growth rates by service/category
            infrastructure_changes: Planned infrastructure changes
            confidence_level: Confidence level for intervals (default: 0.95)
            
        Returns:
            Dict containing forecast data with confidence intervals
        """
        try:
            if budget_id not in self.budgets:
                raise ValueError(f"Budget {budget_id} not found")
            
            budget = self.budgets[budget_id]
            historical_data = self.historical_data.get(budget_id, {})
            
            # Base forecast using historical trends
            base_forecast = self._generate_base_forecast(
                historical_data, forecast_months
            )
            
            # Apply growth projections
            if growth_projections:
                base_forecast = self._apply_growth_projections(
                    base_forecast, growth_projections
                )
            
            # Apply infrastructure changes
            if infrastructure_changes:
                base_forecast = self._apply_infrastructure_changes(
                    base_forecast, infrastructure_changes
                )
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(
                base_forecast, confidence_level, historical_data
            )
            
            # Generate scenario analysis
            scenarios = self._generate_scenario_analysis(
                base_forecast, growth_projections, infrastructure_changes
            )
            
            forecast_data = {
                "budget_id": budget_id,
                "forecast_months": forecast_months,
                "base_forecast": base_forecast,
                "confidence_intervals": confidence_intervals,
                "scenarios": scenarios,
                "confidence_level": confidence_level,
                "assumptions": {
                    "growth_projections": growth_projections or {},
                    "infrastructure_changes": infrastructure_changes or [],
                    "seasonal_adjustments": historical_data.get("seasonal_factors", {})
                },
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store forecast
            self.forecasts[budget_id] = forecast_data
            
            logger.info(f"Generated cost forecast for budget {budget_id}")
            
            return forecast_data
            
        except Exception as e:
            logger.error(f"Error generating cost forecast for {budget_id}: {str(e)}")
            raise

    def track_budget_performance(
        self,
        budget_id: str,
        actual_costs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Track actual vs. predicted spending and adjust models.
        
        Args:
            budget_id: Budget identifier
            actual_costs: List of actual cost data points
            
        Returns:
            Dict containing performance tracking and variance analysis
        """
        try:
            if budget_id not in self.budgets:
                raise ValueError(f"Budget {budget_id} not found")
            
            budget = self.budgets[budget_id]
            forecast = self.forecasts.get(budget_id, {})
            
            # Calculate current spend
            current_spend = sum(cost.get("amount", 0.0) for cost in actual_costs)
            
            # Calculate variance from budget
            budget_variance = (current_spend - budget["budget_amount"]) / budget["budget_amount"] * 100
            
            # Calculate forecast accuracy if forecast exists
            forecast_accuracy = None
            if forecast and "base_forecast" in forecast:
                predicted_spend = sum(forecast["base_forecast"])
                if predicted_spend > 0:
                    forecast_accuracy = (1 - abs(current_spend - predicted_spend) / predicted_spend) * 100
            
            # Update budget status
            utilization = current_spend / budget["budget_amount"]
            status = self._determine_budget_status(utilization)
            
            # Check for threshold alerts
            alerts = self._check_threshold_alerts(budget_id, current_spend, budget)
            
            performance_data = {
                "budget_id": budget_id,
                "current_spend": current_spend,
                "budget_amount": budget["budget_amount"],
                "utilization_percentage": utilization * 100,
                "budget_variance": budget_variance,
                "forecast_accuracy": forecast_accuracy,
                "status": status.value,
                "alerts_triggered": len(alerts),
                "performance_metrics": {
                    "spend_rate": current_spend / max(1, len(actual_costs)),
                    "trend_direction": "increasing" if budget_variance > 0 else "decreasing",
                    "days_remaining": self._calculate_days_remaining(budget),
                    "projected_end_spend": self._project_end_spend(actual_costs, budget)
                },
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            # Update budget with current performance (even in dry_run for testing/demo)
            budget.update({
                "current_spend": current_spend,
                "variance": budget_variance,
                "status": status.value,
                "last_performance_update": datetime.now(timezone.utc).isoformat()
            })
            
            if self.dry_run:
                logger.info(f"DRY_RUN: Tracked budget performance for {budget_id}: {utilization:.1%} utilized")
            else:
                logger.info(f"Tracked budget performance for {budget_id}: {utilization:.1%} utilized")
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Error tracking budget performance for {budget_id}: {str(e)}")
            raise

    def generate_budget_alerts(
        self,
        budget_id: str,
        current_spend: float,
        alert_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate progressive alerts at configurable percentages.
        
        Args:
            budget_id: Budget identifier
            current_spend: Current spending amount
            alert_config: Custom alert configuration
            
        Returns:
            List of generated alerts
        """
        try:
            if budget_id not in self.budgets:
                raise ValueError(f"Budget {budget_id} not found")
            
            budget = self.budgets[budget_id]
            budget_amount = budget["budget_amount"]
            utilization = current_spend / budget_amount
            
            alerts = []
            
            # Default alert thresholds
            thresholds = alert_config or budget["alert_thresholds"]
            
            # Check each threshold
            for threshold_name, threshold_amount in thresholds.items():
                threshold_percentage = threshold_amount / budget_amount
                
                if current_spend >= threshold_amount:
                    severity = self._determine_alert_severity(threshold_percentage)
                    
                    alert = {
                        "alert_id": f"{budget_id}_{threshold_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                        "budget_id": budget_id,
                        "threshold_name": threshold_name,
                        "threshold_percentage": threshold_percentage * 100,
                        "current_spend": current_spend,
                        "budget_amount": budget_amount,
                        "utilization_percentage": utilization * 100,
                        "severity": severity,
                        "message": self._generate_alert_message(
                            budget_id, threshold_name, utilization, current_spend, budget_amount
                        ),
                        "recommended_actions": self._get_recommended_actions(severity, utilization),
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "acknowledged": False
                    }
                    
                    alerts.append(alert)
            
            # Store alerts (even in dry_run for testing/demo purposes)
            if alerts:
                self.alerts.extend(alerts)
                if self.dry_run:
                    logger.info(f"DRY_RUN: Generated {len(alerts)} budget alerts for {budget_id}")
                else:
                    logger.info(f"Generated {len(alerts)} budget alerts for {budget_id}")
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating budget alerts for {budget_id}: {str(e)}")
            raise

    def trigger_approval_workflow(
        self,
        budget_id: str,
        requested_amount: float,
        justification: str,
        requester: str
    ) -> Dict[str, Any]:
        """
        Trigger approval workflows for additional spending.
        
        Args:
            budget_id: Budget identifier
            requested_amount: Additional amount requested
            justification: Business justification for additional spending
            requester: Person requesting additional budget
            
        Returns:
            Dict containing approval workflow details
        """
        try:
            if budget_id not in self.budgets:
                raise ValueError(f"Budget {budget_id} not found")
            
            budget = self.budgets[budget_id]
            current_spend = budget.get("current_spend", 0.0)
            budget_amount = budget["budget_amount"]
            
            # Determine approval level required
            approval_level = self._determine_approval_level(
                requested_amount, budget_amount, current_spend
            )
            
            workflow = {
                "workflow_id": f"approval_{budget_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "budget_id": budget_id,
                "requested_amount": requested_amount,
                "current_spend": current_spend,
                "budget_amount": budget_amount,
                "new_total_if_approved": current_spend + requested_amount,
                "percentage_increase": (requested_amount / budget_amount) * 100,
                "approval_level": approval_level.value,
                "requester": requester,
                "justification": justification,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "approvers": self._get_required_approvers(approval_level),
                "approval_deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "risk_assessment": self._assess_approval_risk(
                    requested_amount, budget_amount, current_spend
                )
            }
            
            # Store workflow (even in dry_run for testing/demo purposes)
            self.approval_workflows.append(workflow)
            budget["approval_workflows"].append(workflow["workflow_id"])
            
            if self.dry_run:
                logger.info(f"DRY_RUN: Triggered approval workflow for budget {budget_id}: {requested_amount}")
            else:
                logger.info(f"Triggered approval workflow for budget {budget_id}: {requested_amount}")
            
            return workflow
            
        except Exception as e:
            logger.error(f"Error triggering approval workflow for {budget_id}: {str(e)}")
            raise

    def generate_variance_analysis(
        self,
        budget_id: str,
        analysis_period_months: int = 12
    ) -> Dict[str, Any]:
        """
        Provide detailed cost breakdowns and variance analysis.
        
        Args:
            budget_id: Budget identifier
            analysis_period_months: Period for variance analysis
            
        Returns:
            Dict containing detailed variance analysis
        """
        try:
            if budget_id not in self.budgets:
                raise ValueError(f"Budget {budget_id} not found")
            
            budget = self.budgets[budget_id]
            historical_data = self.historical_data.get(budget_id, {})
            forecast = self.forecasts.get(budget_id, {})
            
            # Calculate variance metrics
            variance_metrics = {
                "budget_variance": {
                    "actual_vs_budget": budget.get("variance", 0.0),
                    "absolute_variance": abs(budget.get("variance", 0.0)),
                    "variance_category": self._categorize_variance(budget.get("variance", 0.0))
                },
                "forecast_variance": {},
                "trend_analysis": {},
                "seasonal_analysis": {}
            }
            
            # Forecast variance if available
            if forecast and "base_forecast" in forecast:
                predicted_total = sum(forecast["base_forecast"])
                actual_total = budget.get("current_spend", 0.0)
                if predicted_total > 0:
                    forecast_variance = ((actual_total - predicted_total) / predicted_total) * 100
                    variance_metrics["forecast_variance"] = {
                        "predicted_spend": predicted_total,
                        "actual_spend": actual_total,
                        "variance_percentage": forecast_variance,
                        "accuracy_score": max(0, 100 - abs(forecast_variance))
                    }
            
            # Trend analysis
            if historical_data and "trend_analysis" in historical_data:
                variance_metrics["trend_analysis"] = historical_data["trend_analysis"]
            
            # Seasonal analysis
            if historical_data and "seasonal_factors" in historical_data:
                variance_metrics["seasonal_analysis"] = historical_data["seasonal_factors"]
            
            # Cost breakdown by categories
            cost_breakdown = self._generate_cost_breakdown(budget_id)
            
            # Recommendations based on variance
            recommendations = self._generate_variance_recommendations(variance_metrics)
            
            analysis_result = {
                "budget_id": budget_id,
                "analysis_period_months": analysis_period_months,
                "variance_metrics": variance_metrics,
                "cost_breakdown": cost_breakdown,
                "recommendations": recommendations,
                "summary": {
                    "overall_performance": self._assess_overall_performance(variance_metrics),
                    "key_insights": self._extract_key_insights(variance_metrics),
                    "action_items": self._generate_action_items(variance_metrics)
                },
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Generated variance analysis for budget {budget_id}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error generating variance analysis for {budget_id}: {str(e)}")
            raise

    # Helper methods for internal calculations

    def _calculate_trend(self, monthly_costs: List[float]) -> Dict[str, Any]:
        """Calculate trend analysis from monthly cost data."""
        if len(monthly_costs) < 2:
            return {"direction": "unknown", "slope": 0, "r_squared": 0}
        
        # Simple linear regression
        n = len(monthly_costs)
        x = list(range(n))
        y = monthly_costs
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Determine trend direction
        if abs(slope) < 0.01:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        # Calculate R-squared (simplified)
        if len(set(y)) == 1:
            r_squared = 1.0
        else:
            y_pred = [y_mean + slope * (xi - x_mean) for xi in x]
            ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
            ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            "direction": direction,
            "slope": slope,
            "r_squared": max(0, min(1, r_squared)),
            "monthly_change": slope,
            "confidence": "high" if r_squared > 0.7 else "medium" if r_squared > 0.4 else "low"
        }

    def _calculate_seasonal_patterns(
        self, monthly_costs: List[float], dates: List[str]
    ) -> Dict[str, float]:
        """Calculate seasonal adjustment factors."""
        if len(monthly_costs) < 12:
            return {}
        
        # Group by month
        monthly_groups = {}
        for i, date_str in enumerate(dates):
            try:
                month = datetime.fromisoformat(date_str.replace('Z', '+00:00')).month
                if month not in monthly_groups:
                    monthly_groups[month] = []
                monthly_groups[month].append(monthly_costs[i])
            except:
                continue
        
        # Calculate seasonal factors
        overall_mean = statistics.mean(monthly_costs)
        seasonal_factors = {}
        
        for month, costs in monthly_groups.items():
            if costs:
                month_mean = statistics.mean(costs)
                seasonal_factors[f"month_{month}"] = month_mean / overall_mean if overall_mean > 0 else 1.0
        
        return seasonal_factors

    def _generate_base_forecast(
        self, historical_data: Dict[str, Any], forecast_months: int
    ) -> List[float]:
        """Generate base forecast using historical trends."""
        if not historical_data or "monthly_costs" not in historical_data:
            # Default forecast based on average
            return [1000.0] * forecast_months  # Placeholder
        
        monthly_costs = historical_data["monthly_costs"]
        trend_analysis = historical_data.get("trend_analysis", {})
        
        if not monthly_costs:
            return [1000.0] * forecast_months
        
        # Use trend to project forward
        last_cost = monthly_costs[-1]
        monthly_change = trend_analysis.get("slope", 0)
        
        forecast = []
        for i in range(forecast_months):
            projected_cost = last_cost + (monthly_change * (i + 1))
            forecast.append(max(0, projected_cost))  # Ensure non-negative
        
        return forecast

    def _apply_growth_projections(
        self, base_forecast: List[float], growth_projections: Dict[str, float]
    ) -> List[float]:
        """Apply growth projections to base forecast."""
        overall_growth = growth_projections.get("overall", 0.0)
        monthly_growth = overall_growth / 12  # Convert annual to monthly
        
        adjusted_forecast = []
        for i, base_cost in enumerate(base_forecast):
            growth_factor = 1 + (monthly_growth * (i + 1))
            adjusted_forecast.append(base_cost * growth_factor)
        
        return adjusted_forecast

    def _apply_infrastructure_changes(
        self, base_forecast: List[float], infrastructure_changes: List[Dict[str, Any]]
    ) -> List[float]:
        """Apply planned infrastructure changes to forecast."""
        adjusted_forecast = base_forecast.copy()
        
        for change in infrastructure_changes:
            start_month = change.get("start_month", 0)
            cost_impact = change.get("monthly_cost_impact", 0.0)
            
            for i in range(start_month, len(adjusted_forecast)):
                adjusted_forecast[i] += cost_impact
        
        return adjusted_forecast

    def _calculate_confidence_intervals(
        self, base_forecast: List[float], confidence_level: float, historical_data: Dict[str, Any]
    ) -> Dict[str, List[float]]:
        """Calculate confidence intervals for forecast."""
        # Simplified confidence interval calculation
        # In practice, this would use more sophisticated statistical methods
        
        if not historical_data or "monthly_costs" not in historical_data:
            margin = 0.2  # 20% default margin
        else:
            monthly_costs = historical_data["monthly_costs"]
            if len(monthly_costs) > 1:
                std_dev = statistics.stdev(monthly_costs)
                mean_cost = statistics.mean(monthly_costs)
                margin = (std_dev / mean_cost) if mean_cost > 0 else 0.2
            else:
                margin = 0.2
        
        # Calculate confidence bounds
        lower_bound = [cost * (1 - margin) for cost in base_forecast]
        upper_bound = [cost * (1 + margin) for cost in base_forecast]
        
        return {
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "confidence_level": confidence_level,
            "margin_of_error": margin
        }

    def _generate_scenario_analysis(
        self,
        base_forecast: List[float],
        growth_projections: Optional[Dict[str, float]],
        infrastructure_changes: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, List[float]]:
        """Generate optimistic, pessimistic, and realistic scenarios."""
        scenarios = {
            "realistic": base_forecast,
            "optimistic": [cost * 0.85 for cost in base_forecast],  # 15% savings
            "pessimistic": [cost * 1.25 for cost in base_forecast]  # 25% increase
        }
        
        return scenarios

    def _determine_budget_status(self, utilization: float) -> BudgetStatus:
        """Determine budget status based on utilization."""
        if utilization >= 1.0:
            return BudgetStatus.EXCEEDED
        elif utilization >= 0.9:
            return BudgetStatus.CRITICAL
        elif utilization >= 0.75:
            return BudgetStatus.WARNING
        else:
            return BudgetStatus.HEALTHY

    def _check_threshold_alerts(
        self, budget_id: str, current_spend: float, budget: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check if any alert thresholds have been triggered."""
        return self.generate_budget_alerts(budget_id, current_spend)

    def _calculate_days_remaining(self, budget: Dict[str, Any]) -> int:
        """Calculate days remaining in budget period."""
        # Simplified calculation - in practice would use actual budget period dates
        return 30  # Placeholder

    def _project_end_spend(
        self, actual_costs: List[Dict[str, Any]], budget: Dict[str, Any]
    ) -> float:
        """Project spending at end of budget period."""
        if not actual_costs:
            return 0.0
        
        # Simple projection based on current rate
        total_spend = sum(cost.get("amount", 0.0) for cost in actual_costs)
        days_elapsed = len(actual_costs)  # Simplified
        daily_rate = total_spend / max(1, days_elapsed)
        
        days_remaining = self._calculate_days_remaining(budget)
        projected_additional = daily_rate * days_remaining
        
        return total_spend + projected_additional

    def _determine_alert_severity(self, threshold_percentage: float) -> str:
        """Determine alert severity based on threshold."""
        if threshold_percentage >= 1.0:
            return "critical"
        elif threshold_percentage >= 0.9:
            return "high"
        elif threshold_percentage >= 0.75:
            return "medium"
        else:
            return "low"

    def _generate_alert_message(
        self, budget_id: str, threshold_name: str, utilization: float,
        current_spend: float, budget_amount: float
    ) -> str:
        """Generate human-readable alert message."""
        return (
            f"Budget {budget_id} has reached {threshold_name} threshold. "
            f"Current utilization: {utilization:.1%} "
            f"(${current_spend:,.2f} of ${budget_amount:,.2f})"
        )

    def _get_recommended_actions(self, severity: str, utilization: float) -> List[str]:
        """Get recommended actions based on alert severity."""
        actions = []
        
        if severity == "critical":
            actions.extend([
                "Immediate review of spending required",
                "Consider emergency cost reduction measures",
                "Escalate to budget owner for approval"
            ])
        elif severity == "high":
            actions.extend([
                "Review current spending patterns",
                "Identify potential cost savings",
                "Prepare budget adjustment request"
            ])
        elif severity == "medium":
            actions.extend([
                "Monitor spending closely",
                "Review upcoming expenses",
                "Consider optimization opportunities"
            ])
        else:
            actions.append("Continue monitoring budget utilization")
        
        return actions

    def _determine_approval_level(
        self, requested_amount: float, budget_amount: float, current_spend: float
    ) -> ApprovalLevel:
        """Determine required approval level for additional spending."""
        percentage_increase = (requested_amount / budget_amount) * 100
        
        if percentage_increase >= 50:
            return ApprovalLevel.EXECUTIVE
        elif percentage_increase >= 25:
            return ApprovalLevel.DIRECTOR
        elif percentage_increase >= 10:
            return ApprovalLevel.MANAGER
        else:
            return ApprovalLevel.AUTOMATIC

    def _get_required_approvers(self, approval_level: ApprovalLevel) -> List[str]:
        """Get list of required approvers for approval level."""
        approvers_map = {
            ApprovalLevel.AUTOMATIC: [],
            ApprovalLevel.MANAGER: ["team_manager"],
            ApprovalLevel.DIRECTOR: ["team_manager", "department_director"],
            ApprovalLevel.EXECUTIVE: ["team_manager", "department_director", "executive_sponsor"]
        }
        
        return approvers_map.get(approval_level, [])

    def _assess_approval_risk(
        self, requested_amount: float, budget_amount: float, current_spend: float
    ) -> Dict[str, Any]:
        """Assess risk of approving additional spending."""
        total_if_approved = current_spend + requested_amount
        utilization_if_approved = total_if_approved / budget_amount
        
        if utilization_if_approved >= 2.0:
            risk_level = "very_high"
        elif utilization_if_approved >= 1.5:
            risk_level = "high"
        elif utilization_if_approved >= 1.25:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_level": risk_level,
            "utilization_if_approved": utilization_if_approved * 100,
            "budget_overrun_percentage": max(0, (utilization_if_approved - 1) * 100),
            "financial_impact": requested_amount
        }

    def _generate_cost_breakdown(self, budget_id: str) -> Dict[str, Any]:
        """Generate detailed cost breakdown for budget."""
        # Placeholder implementation - would integrate with actual cost data
        return {
            "by_service": {"ec2": 40, "rds": 25, "s3": 15, "lambda": 10, "other": 10},
            "by_region": {"us-east-1": 60, "us-west-2": 30, "eu-west-1": 10},
            "by_team": {"engineering": 50, "data": 30, "ops": 20}
        }

    def _categorize_variance(self, variance_percentage: float) -> str:
        """Categorize variance based on percentage."""
        abs_variance = abs(variance_percentage)
        
        if abs_variance >= 25:
            return "significant"
        elif abs_variance >= 10:
            return "moderate"
        elif abs_variance >= 5:
            return "minor"
        else:
            return "minimal"

    def _generate_variance_recommendations(
        self, variance_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on variance analysis."""
        recommendations = []
        
        budget_variance = variance_metrics.get("budget_variance", {})
        variance_category = budget_variance.get("variance_category", "minimal")
        
        if variance_category == "significant":
            recommendations.extend([
                "Conduct thorough budget review",
                "Implement immediate cost controls",
                "Revise forecasting models"
            ])
        elif variance_category == "moderate":
            recommendations.extend([
                "Review spending patterns",
                "Adjust budget allocations",
                "Improve cost monitoring"
            ])
        else:
            recommendations.append("Continue current budget management practices")
        
        return recommendations

    def _assess_overall_performance(self, variance_metrics: Dict[str, Any]) -> str:
        """Assess overall budget performance."""
        budget_variance = variance_metrics.get("budget_variance", {})
        variance_category = budget_variance.get("variance_category", "minimal")
        
        performance_map = {
            "minimal": "excellent",
            "minor": "good",
            "moderate": "fair",
            "significant": "poor"
        }
        
        return performance_map.get(variance_category, "unknown")

    def _extract_key_insights(self, variance_metrics: Dict[str, Any]) -> List[str]:
        """Extract key insights from variance analysis."""
        insights = []
        
        # Add insights based on variance patterns
        budget_variance = variance_metrics.get("budget_variance", {})
        if budget_variance.get("actual_vs_budget", 0) > 0:
            insights.append("Spending is above budget allocation")
        else:
            insights.append("Spending is within budget limits")
        
        return insights

    def _generate_action_items(self, variance_metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable items based on variance analysis."""
        action_items = []
        
        budget_variance = variance_metrics.get("budget_variance", {})
        variance_category = budget_variance.get("variance_category", "minimal")
        
        if variance_category in ["moderate", "significant"]:
            action_items.extend([
                "Schedule budget review meeting",
                "Analyze top cost drivers",
                "Implement cost optimization measures"
            ])
        
        return action_items

    def get_budget_summary(self) -> Dict[str, Any]:
        """Get summary of all budgets and their status."""
        summary = {
            "total_budgets": len(self.budgets),
            "active_alerts": len(self.alerts),
            "pending_approvals": len(self.approval_workflows),
            "budget_status_distribution": {},
            "total_budget_amount": 0.0,
            "total_current_spend": 0.0,
            "overall_utilization": 0.0
        }
        
        # Calculate status distribution
        status_counts = {}
        total_budget = 0.0
        total_spend = 0.0
        
        for budget in self.budgets.values():
            status = budget.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            total_budget += budget.get("budget_amount", 0.0)
            total_spend += budget.get("current_spend", 0.0)
        
        summary["budget_status_distribution"] = status_counts
        summary["total_budget_amount"] = total_budget
        summary["total_current_spend"] = total_spend
        summary["overall_utilization"] = (total_spend / total_budget * 100) if total_budget > 0 else 0.0
        
        return summary