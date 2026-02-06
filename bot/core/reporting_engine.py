#!/usr/bin/env python3
"""
Reporting Engine for Advanced FinOps Platform

Comprehensive cost analysis and reporting engine that:
- Provides detailed cost breakdowns by service, region, team, and project
- Implements variance analysis, trend reporting, and forecasting accuracy metrics
- Includes savings tracking, ROI calculations, and optimization impact analysis
- Offers customizable reporting templates and export capabilities
- Integrates with cost allocation, budget management, and anomaly detection

Requirements: 6.5, 8.5
"""

import logging
import statistics
import json
import csv
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
from collections import defaultdict
import io

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Types of reports that can be generated."""
    EXECUTIVE_SUMMARY = "executive_summary"
    COST_BREAKDOWN = "cost_breakdown"
    VARIANCE_ANALYSIS = "variance_analysis"
    TREND_ANALYSIS = "trend_analysis"
    SAVINGS_REPORT = "savings_report"
    ROI_ANALYSIS = "roi_analysis"
    FORECAST_ACCURACY = "forecast_accuracy"
    OPTIMIZATION_IMPACT = "optimization_impact"
    CUSTOM_REPORT = "custom_report"


class ReportFormat(Enum):
    """Output formats for reports."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"


class ReportPeriod(Enum):
    """Time periods for reporting."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ReportingEngine:
    """
    Comprehensive cost analysis and reporting engine with advanced analytics,
    variance analysis, trend reporting, and customizable export capabilities.
    """

    def __init__(self, dry_run: bool = True):
        """
        Initialize the Reporting Engine.
        
        Args:
            dry_run: If True, no actual reports will be saved to disk
        """
        self.dry_run = dry_run
        self.report_templates = {}
        self.generated_reports = {}
        self.report_history = []
        self.custom_metrics = {}
        self.export_configurations = {}
        
        # Initialize default report templates
        self._initialize_default_templates()
        
        logger.info(f"Reporting Engine initialized (DRY_RUN: {dry_run})")

    def _initialize_default_templates(self):
        """Initialize default report templates."""
        self.report_templates = {
            "executive_summary": {
                "name": "Executive Summary Report",
                "sections": [
                    "cost_overview",
                    "budget_performance",
                    "savings_achieved",
                    "key_insights",
                    "recommendations"
                ],
                "metrics": [
                    "total_spend",
                    "budget_variance",
                    "savings_percentage",
                    "optimization_opportunities"
                ]
            },
            "detailed_cost_breakdown": {
                "name": "Detailed Cost Breakdown",
                "sections": [
                    "service_breakdown",
                    "region_breakdown", 
                    "team_breakdown",
                    "project_breakdown",
                    "time_series_analysis"
                ],
                "metrics": [
                    "cost_by_service",
                    "cost_by_region",
                    "cost_by_team",
                    "cost_by_project",
                    "growth_rates"
                ]
            },
            "variance_analysis": {
                "name": "Variance Analysis Report",
                "sections": [
                    "budget_variance",
                    "forecast_variance",
                    "trend_variance",
                    "anomaly_analysis",
                    "root_cause_analysis"
                ],
                "metrics": [
                    "actual_vs_budget",
                    "actual_vs_forecast",
                    "variance_drivers",
                    "anomaly_impact"
                ]
            }
        }
    def generate_comprehensive_report(
        self,
        report_type: ReportType,
        period_start: str,
        period_end: str,
        cost_data: List[Dict[str, Any]],
        budget_data: Optional[Dict[str, Any]] = None,
        allocation_data: Optional[Dict[str, Any]] = None,
        anomaly_data: Optional[Dict[str, Any]] = None,
        optimization_data: Optional[Dict[str, Any]] = None,
        template_name: Optional[str] = None,
        custom_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive cost analysis report.
        
        Args:
            report_type: Type of report to generate
            period_start: Start date for reporting period (ISO format)
            period_end: End date for reporting period (ISO format)
            cost_data: Historical cost data
            budget_data: Budget information and performance
            allocation_data: Cost allocation results
            anomaly_data: Anomaly detection results
            optimization_data: Optimization actions and results
            template_name: Optional custom template name
            custom_filters: Optional filters for data analysis
            
        Returns:
            Dict containing comprehensive report data
        """
        try:
            logger.info(f"Generating {report_type.value} report for period {period_start} to {period_end}")
            
            # Initialize report structure
            report = {
                "report_id": f"report_{report_type.value}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "report_type": report_type.value,
                "period": {
                    "start_date": period_start,
                    "end_date": period_end,
                    "duration_days": self._calculate_period_duration(period_start, period_end)
                },
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "template_used": template_name or report_type.value,
                "data_sources": {
                    "cost_data_points": len(cost_data) if cost_data else 0,
                    "budget_data_available": budget_data is not None,
                    "allocation_data_available": allocation_data is not None,
                    "anomaly_data_available": anomaly_data is not None,
                    "optimization_data_available": optimization_data is not None
                }
            }
            
            # Apply custom filters if provided
            if custom_filters:
                cost_data = self._apply_data_filters(cost_data, custom_filters)
                report["filters_applied"] = custom_filters
            
            # Generate report sections based on type
            if report_type == ReportType.EXECUTIVE_SUMMARY:
                report.update(self._generate_executive_summary_report(
                    cost_data, budget_data, allocation_data, anomaly_data, optimization_data
                ))
            elif report_type == ReportType.COST_BREAKDOWN:
                report.update(self._generate_cost_breakdown_report(
                    cost_data, allocation_data
                ))
            elif report_type == ReportType.VARIANCE_ANALYSIS:
                report.update(self._generate_variance_analysis_report(
                    cost_data, budget_data, anomaly_data
                ))
            elif report_type == ReportType.TREND_ANALYSIS:
                report.update(self._generate_trend_analysis_report(
                    cost_data, period_start, period_end
                ))
            elif report_type == ReportType.SAVINGS_REPORT:
                report.update(self._generate_savings_report(
                    cost_data, optimization_data
                ))
            elif report_type == ReportType.ROI_ANALYSIS:
                report.update(self._generate_roi_analysis_report(
                    cost_data, optimization_data
                ))
            elif report_type == ReportType.FORECAST_ACCURACY:
                report.update(self._generate_forecast_accuracy_report(
                    cost_data, budget_data
                ))
            elif report_type == ReportType.OPTIMIZATION_IMPACT:
                report.update(self._generate_optimization_impact_report(
                    cost_data, optimization_data
                ))
            else:
                report.update(self._generate_custom_report(
                    cost_data, template_name, custom_filters
                ))
            
            # Store generated report
            self.generated_reports[report["report_id"]] = report
            self.report_history.append({
                "report_id": report["report_id"],
                "report_type": report_type.value,
                "generated_at": report["generated_at"],
                "period": report["period"]
            })
            
            logger.info(f"Generated report {report['report_id']} successfully")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating {report_type.value} report: {str(e)}")
            raise

    def _generate_executive_summary_report(
        self,
        cost_data: List[Dict[str, Any]],
        budget_data: Optional[Dict[str, Any]],
        allocation_data: Optional[Dict[str, Any]],
        anomaly_data: Optional[Dict[str, Any]],
        optimization_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate executive summary report section."""
        
        # Calculate total costs
        total_cost = sum(item.get("cost", 0.0) for item in cost_data)
        
        # Cost overview
        cost_overview = {
            "total_spend": total_cost,
            "average_daily_spend": total_cost / max(1, len(set(item.get("date", "") for item in cost_data))),
            "cost_distribution": self._calculate_cost_distribution(cost_data),
            "top_cost_drivers": self._identify_top_cost_drivers(cost_data, limit=5)
        }
        
        # Budget performance
        budget_performance = {}
        if budget_data:
            budget_performance = {
                "budget_utilization": self._calculate_budget_utilization(total_cost, budget_data),
                "budget_variance": self._calculate_budget_variance(total_cost, budget_data),
                "budget_status": self._determine_budget_status(total_cost, budget_data),
                "projected_end_of_period": self._project_end_of_period_spend(cost_data, budget_data)
            }
        
        # Savings achieved
        savings_achieved = {}
        if optimization_data:
            savings_achieved = {
                "total_savings": self._calculate_total_savings(optimization_data),
                "savings_percentage": self._calculate_savings_percentage(optimization_data, total_cost),
                "optimization_actions": self._summarize_optimization_actions(optimization_data),
                "potential_additional_savings": self._identify_additional_savings_opportunities(cost_data)
            }
        
        # Key insights
        key_insights = self._generate_key_insights(
            cost_data, budget_data, allocation_data, anomaly_data, optimization_data
        )
        
        # Recommendations
        recommendations = self._generate_executive_recommendations(
            cost_data, budget_data, allocation_data, anomaly_data, optimization_data
        )
        
        return {
            "executive_summary": {
                "cost_overview": cost_overview,
                "budget_performance": budget_performance,
                "savings_achieved": savings_achieved,
                "key_insights": key_insights,
                "recommendations": recommendations
            }
        }

    def _generate_cost_breakdown_report(
        self,
        cost_data: List[Dict[str, Any]],
        allocation_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate detailed cost breakdown report section."""
        
        # Service breakdown
        service_breakdown = self._analyze_costs_by_dimension(cost_data, "service")
        
        # Region breakdown
        region_breakdown = self._analyze_costs_by_dimension(cost_data, "region")
        
        # Team breakdown (from allocation data)
        team_breakdown = {}
        if allocation_data:
            team_breakdown = self._extract_team_costs_from_allocation(allocation_data)
        
        # Project breakdown (from allocation data)
        project_breakdown = {}
        if allocation_data:
            project_breakdown = self._extract_project_costs_from_allocation(allocation_data)
        
        # Time series analysis
        time_series_analysis = self._generate_time_series_analysis(cost_data)
        
        return {
            "cost_breakdown": {
                "service_breakdown": service_breakdown,
                "region_breakdown": region_breakdown,
                "team_breakdown": team_breakdown,
                "project_breakdown": project_breakdown,
                "time_series_analysis": time_series_analysis,
                "summary_statistics": self._calculate_breakdown_statistics(cost_data)
            }
        }

    def _generate_variance_analysis_report(
        self,
        cost_data: List[Dict[str, Any]],
        budget_data: Optional[Dict[str, Any]],
        anomaly_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate variance analysis report section."""
        
        total_cost = sum(item.get("cost", 0.0) for item in cost_data)
        
        # Budget variance analysis
        budget_variance = {}
        if budget_data:
            budget_variance = {
                "absolute_variance": self._calculate_absolute_variance(total_cost, budget_data),
                "percentage_variance": self._calculate_percentage_variance(total_cost, budget_data),
                "variance_trend": self._analyze_variance_trend(cost_data, budget_data),
                "variance_drivers": self._identify_variance_drivers(cost_data, budget_data)
            }
        
        # Forecast variance analysis
        forecast_variance = self._analyze_forecast_variance(cost_data, budget_data)
        
        # Trend variance analysis
        trend_variance = self._analyze_trend_variance(cost_data)
        
        # Anomaly analysis
        anomaly_analysis = {}
        if anomaly_data:
            anomaly_analysis = {
                "anomaly_impact": self._calculate_anomaly_impact(anomaly_data, total_cost),
                "anomaly_frequency": self._analyze_anomaly_frequency(anomaly_data),
                "anomaly_patterns": self._identify_anomaly_patterns(anomaly_data)
            }
        
        # Root cause analysis
        root_cause_analysis = self._perform_comprehensive_root_cause_analysis(
            cost_data, budget_data, anomaly_data
        )
        
        return {
            "variance_analysis": {
                "budget_variance": budget_variance,
                "forecast_variance": forecast_variance,
                "trend_variance": trend_variance,
                "anomaly_analysis": anomaly_analysis,
                "root_cause_analysis": root_cause_analysis
            }
        }
    def _generate_trend_analysis_report(
        self,
        cost_data: List[Dict[str, Any]],
        period_start: str,
        period_end: str
    ) -> Dict[str, Any]:
        """Generate trend analysis report section."""
        
        # Sort data by date for trend analysis
        sorted_data = sorted(cost_data, key=lambda x: x.get("timestamp", x.get("date", "")))
        
        # Overall cost trend
        overall_trend = self._calculate_overall_trend(sorted_data)
        
        # Service-level trends
        service_trends = self._calculate_service_trends(sorted_data)
        
        # Regional trends
        regional_trends = self._calculate_regional_trends(sorted_data)
        
        # Seasonal patterns
        seasonal_patterns = self._identify_seasonal_patterns(sorted_data)
        
        # Growth rate analysis
        growth_analysis = self._analyze_growth_rates(sorted_data)
        
        # Trend forecasting
        trend_forecast = self._generate_trend_forecast(sorted_data, forecast_days=30)
        
        return {
            "trend_analysis": {
                "overall_trend": overall_trend,
                "service_trends": service_trends,
                "regional_trends": regional_trends,
                "seasonal_patterns": seasonal_patterns,
                "growth_analysis": growth_analysis,
                "trend_forecast": trend_forecast,
                "trend_confidence": self._calculate_trend_confidence(sorted_data)
            }
        }

    def _generate_savings_report(
        self,
        cost_data: List[Dict[str, Any]],
        optimization_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate savings tracking report section."""
        
        if not optimization_data:
            return {
                "savings_report": {
                    "error": "No optimization data available for savings analysis"
                }
            }
        
        # Total savings achieved
        total_savings = self._calculate_total_savings(optimization_data)
        
        # Savings by optimization type
        savings_by_type = self._calculate_savings_by_optimization_type(optimization_data)
        
        # Savings by service
        savings_by_service = self._calculate_savings_by_service(optimization_data)
        
        # Savings timeline
        savings_timeline = self._generate_savings_timeline(optimization_data)
        
        # Savings rate analysis
        savings_rate = self._calculate_savings_rate(optimization_data, cost_data)
        
        # Potential future savings
        potential_savings = self._identify_potential_future_savings(cost_data, optimization_data)
        
        return {
            "savings_report": {
                "total_savings": total_savings,
                "savings_by_type": savings_by_type,
                "savings_by_service": savings_by_service,
                "savings_timeline": savings_timeline,
                "savings_rate": savings_rate,
                "potential_savings": potential_savings,
                "savings_metrics": self._calculate_savings_metrics(optimization_data)
            }
        }

    def _generate_roi_analysis_report(
        self,
        cost_data: List[Dict[str, Any]],
        optimization_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate ROI analysis report section."""
        
        if not optimization_data:
            return {
                "roi_analysis": {
                    "error": "No optimization data available for ROI analysis"
                }
            }
        
        # Calculate ROI for optimization investments
        optimization_roi = self._calculate_optimization_roi(optimization_data)
        
        # ROI by optimization category
        roi_by_category = self._calculate_roi_by_category(optimization_data)
        
        # Payback period analysis
        payback_analysis = self._calculate_payback_periods(optimization_data)
        
        # Cost-benefit analysis
        cost_benefit_analysis = self._perform_cost_benefit_analysis(optimization_data)
        
        # ROI trends over time
        roi_trends = self._analyze_roi_trends(optimization_data)
        
        return {
            "roi_analysis": {
                "optimization_roi": optimization_roi,
                "roi_by_category": roi_by_category,
                "payback_analysis": payback_analysis,
                "cost_benefit_analysis": cost_benefit_analysis,
                "roi_trends": roi_trends,
                "roi_summary": self._generate_roi_summary(optimization_data)
            }
        }

    def _generate_forecast_accuracy_report(
        self,
        cost_data: List[Dict[str, Any]],
        budget_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate forecasting accuracy metrics report section."""
        
        if not budget_data or "forecasts" not in budget_data:
            return {
                "forecast_accuracy": {
                    "error": "No forecast data available for accuracy analysis"
                }
            }
        
        # Calculate forecast accuracy metrics
        accuracy_metrics = self._calculate_forecast_accuracy_metrics(cost_data, budget_data)
        
        # Accuracy by forecast horizon
        accuracy_by_horizon = self._analyze_accuracy_by_horizon(cost_data, budget_data)
        
        # Accuracy by service/category
        accuracy_by_category = self._analyze_accuracy_by_category(cost_data, budget_data)
        
        # Forecast bias analysis
        bias_analysis = self._analyze_forecast_bias(cost_data, budget_data)
        
        # Model performance comparison
        model_performance = self._compare_forecast_model_performance(cost_data, budget_data)
        
        return {
            "forecast_accuracy": {
                "accuracy_metrics": accuracy_metrics,
                "accuracy_by_horizon": accuracy_by_horizon,
                "accuracy_by_category": accuracy_by_category,
                "bias_analysis": bias_analysis,
                "model_performance": model_performance,
                "improvement_recommendations": self._generate_forecast_improvement_recommendations(accuracy_metrics)
            }
        }

    def _generate_optimization_impact_report(
        self,
        cost_data: List[Dict[str, Any]],
        optimization_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate optimization impact analysis report section."""
        
        if not optimization_data:
            return {
                "optimization_impact": {
                    "error": "No optimization data available for impact analysis"
                }
            }
        
        # Overall optimization impact
        overall_impact = self._calculate_overall_optimization_impact(optimization_data, cost_data)
        
        # Impact by optimization type
        impact_by_type = self._calculate_impact_by_optimization_type(optimization_data)
        
        # Performance impact analysis
        performance_impact = self._analyze_performance_impact(optimization_data)
        
        # Risk assessment of optimizations
        risk_assessment = self._assess_optimization_risks(optimization_data)
        
        # Success rate analysis
        success_rate = self._calculate_optimization_success_rate(optimization_data)
        
        # Impact timeline
        impact_timeline = self._generate_optimization_impact_timeline(optimization_data)
        
        return {
            "optimization_impact": {
                "overall_impact": overall_impact,
                "impact_by_type": impact_by_type,
                "performance_impact": performance_impact,
                "risk_assessment": risk_assessment,
                "success_rate": success_rate,
                "impact_timeline": impact_timeline,
                "optimization_effectiveness": self._measure_optimization_effectiveness(optimization_data)
            }
        }

    def export_report(
        self,
        report_id: str,
        format_type: ReportFormat,
        output_path: Optional[str] = None,
        template_customizations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export report in specified format with customizable templates.
        
        Args:
            report_id: ID of the report to export
            format_type: Output format for the report
            output_path: Optional custom output path
            template_customizations: Optional template customizations
            
        Returns:
            Dict containing export results and file information
        """
        try:
            if report_id not in self.generated_reports:
                raise ValueError(f"Report {report_id} not found")
            
            report_data = self.generated_reports[report_id]
            
            # Generate filename if not provided
            if not output_path:
                timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                output_path = f"report_{report_id}_{timestamp}.{format_type.value}"
            
            export_result = {
                "report_id": report_id,
                "format": format_type.value,
                "output_path": output_path,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "file_size": 0,
                "export_success": False
            }
            
            # Export based on format type
            if format_type == ReportFormat.JSON:
                export_result.update(self._export_json(report_data, output_path, template_customizations))
            elif format_type == ReportFormat.CSV:
                export_result.update(self._export_csv(report_data, output_path, template_customizations))
            elif format_type == ReportFormat.HTML:
                export_result.update(self._export_html(report_data, output_path, template_customizations))
            elif format_type == ReportFormat.PDF:
                export_result.update(self._export_pdf(report_data, output_path, template_customizations))
            elif format_type == ReportFormat.EXCEL:
                export_result.update(self._export_excel(report_data, output_path, template_customizations))
            else:
                raise ValueError(f"Unsupported export format: {format_type.value}")
            
            logger.info(f"Exported report {report_id} to {output_path} in {format_type.value} format")
            
            return export_result
            
        except Exception as e:
            logger.error(f"Error exporting report {report_id}: {str(e)}")
            raise

    def create_custom_template(
        self,
        template_name: str,
        template_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create custom reporting template.
        
        Args:
            template_name: Name for the custom template
            template_config: Template configuration including sections and metrics
            
        Returns:
            Dict containing template creation results
        """
        try:
            # Validate template configuration
            validation_result = self._validate_template_config(template_config)
            if not validation_result["is_valid"]:
                raise ValueError(f"Invalid template configuration: {validation_result['errors']}")
            
            # Store custom template
            self.report_templates[template_name] = {
                "name": template_config.get("name", template_name),
                "sections": template_config.get("sections", []),
                "metrics": template_config.get("metrics", []),
                "filters": template_config.get("filters", {}),
                "formatting": template_config.get("formatting", {}),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_custom": True
            }
            
            logger.info(f"Created custom template: {template_name}")
            
            return {
                "template_name": template_name,
                "created_at": self.report_templates[template_name]["created_at"],
                "validation_result": validation_result,
                "template_config": self.report_templates[template_name]
            }
            
        except Exception as e:
            logger.error(f"Error creating custom template {template_name}: {str(e)}")
            raise
    # Helper methods for report generation and analysis

    def _calculate_period_duration(self, start_date: str, end_date: str) -> int:
        """Calculate duration between two dates in days."""
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            return (end - start).days
        except Exception:
            return 0

    def _apply_data_filters(
        self, cost_data: List[Dict[str, Any]], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply custom filters to cost data."""
        filtered_data = cost_data.copy()
        
        # Service filter
        if "services" in filters:
            services = filters["services"] if isinstance(filters["services"], list) else [filters["services"]]
            filtered_data = [item for item in filtered_data if item.get("service") in services]
        
        # Region filter
        if "regions" in filters:
            regions = filters["regions"] if isinstance(filters["regions"], list) else [filters["regions"]]
            filtered_data = [item for item in filtered_data if item.get("region") in regions]
        
        # Cost threshold filter
        if "min_cost" in filters:
            filtered_data = [item for item in filtered_data if item.get("cost", 0) >= filters["min_cost"]]
        
        if "max_cost" in filters:
            filtered_data = [item for item in filtered_data if item.get("cost", 0) <= filters["max_cost"]]
        
        return filtered_data

    def _calculate_cost_distribution(self, cost_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cost distribution across different dimensions."""
        total_cost = sum(item.get("cost", 0.0) for item in cost_data)
        
        if total_cost == 0:
            return {"error": "No cost data available"}
        
        # Distribution by service
        service_costs = defaultdict(float)
        for item in cost_data:
            service = item.get("service", "unknown")
            service_costs[service] += item.get("cost", 0.0)
        
        service_distribution = {
            service: (cost / total_cost * 100) 
            for service, cost in service_costs.items()
        }
        
        # Distribution by region
        region_costs = defaultdict(float)
        for item in cost_data:
            region = item.get("region", "unknown")
            region_costs[region] += item.get("cost", 0.0)
        
        region_distribution = {
            region: (cost / total_cost * 100) 
            for region, cost in region_costs.items()
        }
        
        return {
            "by_service": service_distribution,
            "by_region": region_distribution,
            "total_cost": total_cost
        }

    def _identify_top_cost_drivers(
        self, cost_data: List[Dict[str, Any]], limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Identify top cost drivers."""
        # Group by resource and sum costs
        resource_costs = defaultdict(float)
        resource_details = {}
        
        for item in cost_data:
            resource_id = item.get("resource_id", "unknown")
            cost = item.get("cost", 0.0)
            resource_costs[resource_id] += cost
            
            if resource_id not in resource_details:
                resource_details[resource_id] = {
                    "service": item.get("service", "unknown"),
                    "region": item.get("region", "unknown"),
                    "resource_type": item.get("resource_type", "unknown")
                }
        
        # Sort by cost and return top drivers
        sorted_resources = sorted(
            resource_costs.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]
        
        top_drivers = []
        for resource_id, cost in sorted_resources:
            details = resource_details.get(resource_id, {})
            top_drivers.append({
                "resource_id": resource_id,
                "cost": cost,
                "service": details.get("service", "unknown"),
                "region": details.get("region", "unknown"),
                "resource_type": details.get("resource_type", "unknown")
            })
        
        return top_drivers

    def _calculate_budget_utilization(
        self, total_cost: float, budget_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate budget utilization metrics."""
        if not budget_data:
            return {"error": "No budget data available"}
        
        budget_amount = budget_data.get("budget_amount", 0.0)
        if budget_amount == 0:
            return {"error": "Invalid budget amount"}
        
        utilization_percentage = (total_cost / budget_amount) * 100
        remaining_budget = budget_amount - total_cost
        
        return {
            "budget_amount": budget_amount,
            "spent_amount": total_cost,
            "utilization_percentage": utilization_percentage,
            "remaining_budget": remaining_budget,
            "status": "over_budget" if utilization_percentage > 100 else "within_budget"
        }

    def _calculate_budget_variance(
        self, total_cost: float, budget_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate budget variance metrics."""
        if not budget_data:
            return {"error": "No budget data available"}
        
        budget_amount = budget_data.get("budget_amount", 0.0)
        if budget_amount == 0:
            return {"error": "Invalid budget amount"}
        
        absolute_variance = total_cost - budget_amount
        percentage_variance = (absolute_variance / budget_amount) * 100
        
        return {
            "absolute_variance": absolute_variance,
            "percentage_variance": percentage_variance,
            "variance_type": "over_budget" if absolute_variance > 0 else "under_budget",
            "variance_significance": self._assess_variance_significance(percentage_variance)
        }

    def _assess_variance_significance(self, percentage_variance: float) -> str:
        """Assess the significance of budget variance."""
        abs_variance = abs(percentage_variance)
        
        if abs_variance < 5:
            return "minimal"
        elif abs_variance < 15:
            return "moderate"
        elif abs_variance < 30:
            return "significant"
        else:
            return "critical"

    def _determine_budget_status(
        self, total_cost: float, budget_data: Dict[str, Any]
    ) -> str:
        """Determine overall budget status."""
        if not budget_data:
            return "unknown"
        
        budget_amount = budget_data.get("budget_amount", 0.0)
        if budget_amount == 0:
            return "invalid"
        
        utilization = (total_cost / budget_amount) * 100
        
        if utilization <= 75:
            return "healthy"
        elif utilization <= 90:
            return "warning"
        elif utilization <= 100:
            return "critical"
        else:
            return "exceeded"

    def _project_end_of_period_spend(
        self, cost_data: List[Dict[str, Any]], budget_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Project end-of-period spending based on current trends."""
        if not cost_data or not budget_data:
            return {"error": "Insufficient data for projection"}
        
        # Calculate daily average spend
        dates = set(item.get("date", item.get("timestamp", ""))[:10] for item in cost_data)
        total_cost = sum(item.get("cost", 0.0) for item in cost_data)
        days_elapsed = len(dates)
        
        if days_elapsed == 0:
            return {"error": "No valid date data"}
        
        daily_average = total_cost / days_elapsed
        
        # Get budget period information
        budget_period_days = budget_data.get("period_days", 30)
        projected_total = daily_average * budget_period_days
        
        return {
            "daily_average_spend": daily_average,
            "days_elapsed": days_elapsed,
            "projected_total_spend": projected_total,
            "budget_amount": budget_data.get("budget_amount", 0.0),
            "projected_variance": projected_total - budget_data.get("budget_amount", 0.0)
        }

    def _analyze_costs_by_dimension(
        self, cost_data: List[Dict[str, Any]], dimension: str
    ) -> Dict[str, Any]:
        """Analyze costs by a specific dimension (service, region, etc.)."""
        dimension_costs = defaultdict(float)
        dimension_counts = defaultdict(int)
        
        for item in cost_data:
            dim_value = item.get(dimension, "unknown")
            cost = item.get("cost", 0.0)
            
            dimension_costs[dim_value] += cost
            dimension_counts[dim_value] += 1
        
        total_cost = sum(dimension_costs.values())
        
        # Calculate percentages and averages
        analysis = {}
        for dim_value, cost in dimension_costs.items():
            analysis[dim_value] = {
                "total_cost": cost,
                "percentage": (cost / total_cost * 100) if total_cost > 0 else 0,
                "resource_count": dimension_counts[dim_value],
                "average_cost": cost / dimension_counts[dim_value] if dimension_counts[dim_value] > 0 else 0
            }
        
        # Sort by cost descending
        sorted_analysis = dict(sorted(analysis.items(), key=lambda x: x[1]["total_cost"], reverse=True))
        
        return {
            "breakdown": sorted_analysis,
            "total_cost": total_cost,
            "dimension_count": len(dimension_costs),
            "top_contributor": max(dimension_costs.items(), key=lambda x: x[1]) if dimension_costs else None
        }

    def _generate_time_series_analysis(self, cost_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate time series analysis of costs."""
        # Group costs by date
        daily_costs = defaultdict(float)
        
        for item in cost_data:
            date_key = item.get("date", item.get("timestamp", ""))[:10]  # Extract date part
            daily_costs[date_key] += item.get("cost", 0.0)
        
        if not daily_costs:
            return {"error": "No date information available"}
        
        # Sort dates
        sorted_dates = sorted(daily_costs.keys())
        costs_series = [daily_costs[date] for date in sorted_dates]
        
        # Calculate trend
        if len(costs_series) > 1:
            trend = self._calculate_simple_trend(costs_series)
        else:
            trend = {"direction": "insufficient_data", "slope": 0}
        
        # Calculate statistics
        if costs_series:
            avg_daily_cost = statistics.mean(costs_series)
            max_daily_cost = max(costs_series)
            min_daily_cost = min(costs_series)
            std_dev = statistics.stdev(costs_series) if len(costs_series) > 1 else 0
        else:
            avg_daily_cost = max_daily_cost = min_daily_cost = std_dev = 0
        
        return {
            "daily_costs": dict(zip(sorted_dates, costs_series)),
            "trend": trend,
            "statistics": {
                "average_daily_cost": avg_daily_cost,
                "max_daily_cost": max_daily_cost,
                "min_daily_cost": min_daily_cost,
                "standard_deviation": std_dev,
                "total_days": len(sorted_dates)
            }
        }

    def _calculate_simple_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate simple linear trend for a series of values."""
        if len(values) < 2:
            return {"direction": "insufficient_data", "slope": 0}
        
        n = len(values)
        x_values = list(range(n))
        
        # Simple linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Determine direction
        if abs(slope) < 0.01:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        return {
            "direction": direction,
            "slope": slope,
            "daily_change": slope,
            "confidence": "medium"  # Simplified confidence assessment
        }

    def _calculate_total_savings(self, optimization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate total savings from optimization data."""
        if not optimization_data:
            return {"total_savings": 0.0, "error": "No optimization data"}
        
        # Extract savings from optimization actions
        optimizations = optimization_data.get("optimizations", [])
        total_savings = 0.0
        savings_count = 0
        
        for optimization in optimizations:
            savings = optimization.get("estimated_savings", 0.0)
            if optimization.get("status") == "completed":
                total_savings += savings
                savings_count += 1
        
        return {
            "total_savings": total_savings,
            "completed_optimizations": savings_count,
            "average_savings_per_optimization": total_savings / savings_count if savings_count > 0 else 0
        }

    def _generate_key_insights(
        self,
        cost_data: List[Dict[str, Any]],
        budget_data: Optional[Dict[str, Any]],
        allocation_data: Optional[Dict[str, Any]],
        anomaly_data: Optional[Dict[str, Any]],
        optimization_data: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate key insights from all available data."""
        insights = []
        
        # Cost insights
        total_cost = sum(item.get("cost", 0.0) for item in cost_data)
        if total_cost > 0:
            top_service = self._identify_top_cost_drivers(cost_data, 1)
            if top_service:
                service_name = top_service[0].get("service", "unknown")
                service_cost = top_service[0].get("cost", 0.0)
                service_percentage = (service_cost / total_cost) * 100
                insights.append(f"{service_name} is the largest cost driver, accounting for {service_percentage:.1f}% of total spend")
        
        # Budget insights
        if budget_data:
            budget_utilization = self._calculate_budget_utilization(total_cost, budget_data)
            utilization_pct = budget_utilization.get("utilization_percentage", 0)
            if utilization_pct > 90:
                insights.append(f"Budget utilization is at {utilization_pct:.1f}%, approaching or exceeding budget limits")
            elif utilization_pct < 50:
                insights.append(f"Budget utilization is only {utilization_pct:.1f}%, indicating potential for increased investment or budget reallocation")
        
        # Anomaly insights
        if anomaly_data and anomaly_data.get("anomalies_detected"):
            anomaly_count = len(anomaly_data["anomalies_detected"])
            insights.append(f"Detected {anomaly_count} cost anomalies requiring attention")
        
        # Optimization insights
        if optimization_data:
            savings_data = self._calculate_total_savings(optimization_data)
            total_savings = savings_data.get("total_savings", 0.0)
            if total_savings > 0:
                savings_percentage = (total_savings / total_cost) * 100 if total_cost > 0 else 0
                insights.append(f"Achieved ${total_savings:,.2f} in cost savings ({savings_percentage:.1f}% of total spend)")
        
        return insights

    def _generate_executive_recommendations(
        self,
        cost_data: List[Dict[str, Any]],
        budget_data: Optional[Dict[str, Any]],
        allocation_data: Optional[Dict[str, Any]],
        anomaly_data: Optional[Dict[str, Any]],
        optimization_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Generate executive-level recommendations."""
        recommendations = []
        
        # Budget-based recommendations
        if budget_data:
            total_cost = sum(item.get("cost", 0.0) for item in cost_data)
            budget_utilization = self._calculate_budget_utilization(total_cost, budget_data)
            utilization_pct = budget_utilization.get("utilization_percentage", 0)
            
            if utilization_pct > 100:
                recommendations.append({
                    "priority": "high",
                    "category": "budget_management",
                    "recommendation": "Immediate budget review required - spending has exceeded allocated budget",
                    "action": "Review and approve additional budget or implement cost reduction measures"
                })
            elif utilization_pct > 90:
                recommendations.append({
                    "priority": "medium",
                    "category": "budget_management", 
                    "recommendation": "Budget utilization approaching limits - proactive management needed",
                    "action": "Implement cost controls and monitor spending closely"
                })
        
        # Cost optimization recommendations
        top_drivers = self._identify_top_cost_drivers(cost_data, 3)
        if top_drivers:
            recommendations.append({
                "priority": "medium",
                "category": "cost_optimization",
                "recommendation": f"Focus optimization efforts on top cost drivers: {', '.join([d['service'] for d in top_drivers[:3]])}",
                "action": "Implement targeted cost optimization strategies for highest-spend services"
            })
        
        # Anomaly-based recommendations
        if anomaly_data and anomaly_data.get("anomalies_detected"):
            recommendations.append({
                "priority": "high",
                "category": "anomaly_management",
                "recommendation": "Cost anomalies detected requiring investigation",
                "action": "Review anomaly root causes and implement preventive measures"
            })
        
        return recommendations
    # Export methods for different formats

    def _export_json(
        self, report_data: Dict[str, Any], output_path: str, customizations: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export report as JSON format."""
        try:
            if self.dry_run:
                # In dry_run mode, just return the data without writing to file
                json_content = json.dumps(report_data, indent=2, default=str)
                return {
                    "export_success": True,
                    "file_size": len(json_content.encode('utf-8')),
                    "content_preview": json_content[:500] + "..." if len(json_content) > 500 else json_content
                }
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, default=str)
                
                # Get file size
                import os
                file_size = os.path.getsize(output_path)
                
                return {
                    "export_success": True,
                    "file_size": file_size
                }
        except Exception as e:
            return {
                "export_success": False,
                "error": str(e)
            }

    def _export_csv(
        self, report_data: Dict[str, Any], output_path: str, customizations: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export report as CSV format."""
        try:
            # Flatten report data for CSV export
            flattened_data = self._flatten_report_for_csv(report_data)
            
            if self.dry_run:
                # In dry_run mode, create CSV content in memory
                output = io.StringIO()
                if flattened_data:
                    writer = csv.DictWriter(output, fieldnames=flattened_data[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened_data)
                
                csv_content = output.getvalue()
                output.close()
                
                return {
                    "export_success": True,
                    "file_size": len(csv_content.encode('utf-8')),
                    "rows_exported": len(flattened_data),
                    "content_preview": csv_content[:500] + "..." if len(csv_content) > 500 else csv_content
                }
            else:
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    if flattened_data:
                        writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                        writer.writeheader()
                        writer.writerows(flattened_data)
                
                import os
                file_size = os.path.getsize(output_path)
                
                return {
                    "export_success": True,
                    "file_size": file_size,
                    "rows_exported": len(flattened_data)
                }
        except Exception as e:
            return {
                "export_success": False,
                "error": str(e)
            }

    def _export_html(
        self, report_data: Dict[str, Any], output_path: str, customizations: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export report as HTML format."""
        try:
            html_content = self._generate_html_report(report_data, customizations)
            
            if self.dry_run:
                return {
                    "export_success": True,
                    "file_size": len(html_content.encode('utf-8')),
                    "content_preview": html_content[:500] + "..." if len(html_content) > 500 else html_content
                }
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                import os
                file_size = os.path.getsize(output_path)
                
                return {
                    "export_success": True,
                    "file_size": file_size
                }
        except Exception as e:
            return {
                "export_success": False,
                "error": str(e)
            }

    def _export_pdf(
        self, report_data: Dict[str, Any], output_path: str, customizations: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export report as PDF format (placeholder implementation)."""
        # Note: PDF export would require additional libraries like reportlab or weasyprint
        # For now, return a placeholder implementation
        return {
            "export_success": False,
            "error": "PDF export not implemented - requires additional dependencies"
        }

    def _export_excel(
        self, report_data: Dict[str, Any], output_path: str, customizations: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export report as Excel format (placeholder implementation)."""
        # Note: Excel export would require libraries like openpyxl or xlsxwriter
        # For now, return a placeholder implementation
        return {
            "export_success": False,
            "error": "Excel export not implemented - requires additional dependencies"
        }

    def _flatten_report_for_csv(self, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten nested report data for CSV export."""
        flattened_rows = []
        
        # Extract key metrics and flatten them
        report_id = report_data.get("report_id", "")
        report_type = report_data.get("report_type", "")
        generated_at = report_data.get("generated_at", "")
        
        # Process different report sections
        if "executive_summary" in report_data:
            summary = report_data["executive_summary"]
            
            # Cost overview
            if "cost_overview" in summary:
                cost_overview = summary["cost_overview"]
                flattened_rows.append({
                    "report_id": report_id,
                    "report_type": report_type,
                    "generated_at": generated_at,
                    "section": "cost_overview",
                    "metric": "total_spend",
                    "value": cost_overview.get("total_spend", 0),
                    "description": "Total spending for the period"
                })
                
                flattened_rows.append({
                    "report_id": report_id,
                    "report_type": report_type,
                    "generated_at": generated_at,
                    "section": "cost_overview",
                    "metric": "average_daily_spend",
                    "value": cost_overview.get("average_daily_spend", 0),
                    "description": "Average daily spending"
                })
        
        # Process cost breakdown if available
        if "cost_breakdown" in report_data:
            breakdown = report_data["cost_breakdown"]
            
            # Service breakdown
            if "service_breakdown" in breakdown:
                service_data = breakdown["service_breakdown"].get("breakdown", {})
                for service, data in service_data.items():
                    flattened_rows.append({
                        "report_id": report_id,
                        "report_type": report_type,
                        "generated_at": generated_at,
                        "section": "service_breakdown",
                        "metric": "service_cost",
                        "dimension": service,
                        "value": data.get("total_cost", 0),
                        "percentage": data.get("percentage", 0),
                        "description": f"Cost for {service} service"
                    })
        
        return flattened_rows if flattened_rows else [{"report_id": report_id, "message": "No data to export"}]

    def _generate_html_report(
        self, report_data: Dict[str, Any], customizations: Optional[Dict[str, Any]]
    ) -> str:
        """Generate HTML report content."""
        
        # Basic HTML template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e9f4ff; border-radius: 3px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .insight {{ background-color: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                .recommendation {{ background-color: #d4edda; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <p><strong>Report ID:</strong> {report_id}</p>
                <p><strong>Generated:</strong> {generated_at}</p>
                <p><strong>Period:</strong> {period_start} to {period_end}</p>
            </div>
            
            {content}
        </body>
        </html>
        """
        
        # Extract report information
        title = f"{report_data.get('report_type', 'Unknown').replace('_', ' ').title()} Report"
        report_id = report_data.get("report_id", "N/A")
        generated_at = report_data.get("generated_at", "N/A")
        period = report_data.get("period", {})
        period_start = period.get("start_date", "N/A")
        period_end = period.get("end_date", "N/A")
        
        # Generate content sections
        content_sections = []
        
        # Executive Summary
        if "executive_summary" in report_data:
            summary = report_data["executive_summary"]
            content_sections.append('<div class="section"><h2>Executive Summary</h2>')
            
            # Cost Overview
            if "cost_overview" in summary:
                cost_overview = summary["cost_overview"]
                content_sections.append('<h3>Cost Overview</h3>')
                content_sections.append(f'<div class="metric">Total Spend: ${cost_overview.get("total_spend", 0):,.2f}</div>')
                content_sections.append(f'<div class="metric">Average Daily Spend: ${cost_overview.get("average_daily_spend", 0):,.2f}</div>')
            
            # Key Insights
            if "key_insights" in summary:
                insights = summary["key_insights"]
                content_sections.append('<h3>Key Insights</h3>')
                for insight in insights:
                    content_sections.append(f'<div class="insight">{insight}</div>')
            
            # Recommendations
            if "recommendations" in summary:
                recommendations = summary["recommendations"]
                content_sections.append('<h3>Recommendations</h3>')
                for rec in recommendations:
                    priority = rec.get("priority", "medium")
                    recommendation = rec.get("recommendation", "")
                    content_sections.append(f'<div class="recommendation"><strong>[{priority.upper()}]</strong> {recommendation}</div>')
            
            content_sections.append('</div>')
        
        # Cost Breakdown
        if "cost_breakdown" in report_data:
            breakdown = report_data["cost_breakdown"]
            content_sections.append('<div class="section"><h2>Cost Breakdown</h2>')
            
            # Service breakdown table
            if "service_breakdown" in breakdown:
                service_data = breakdown["service_breakdown"].get("breakdown", {})
                if service_data:
                    content_sections.append('<h3>By Service</h3>')
                    content_sections.append('<table>')
                    content_sections.append('<tr><th>Service</th><th>Cost</th><th>Percentage</th><th>Resources</th></tr>')
                    
                    for service, data in service_data.items():
                        cost = data.get("total_cost", 0)
                        percentage = data.get("percentage", 0)
                        count = data.get("resource_count", 0)
                        content_sections.append(f'<tr><td>{service}</td><td>${cost:,.2f}</td><td>{percentage:.1f}%</td><td>{count}</td></tr>')
                    
                    content_sections.append('</table>')
            
            content_sections.append('</div>')
        
        # Join all content sections
        content = '\n'.join(content_sections)
        
        return html_template.format(
            title=title,
            report_id=report_id,
            generated_at=generated_at,
            period_start=period_start,
            period_end=period_end,
            content=content
        )

    def _validate_template_config(self, template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate custom template configuration."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        required_fields = ["sections", "metrics"]
        for field in required_fields:
            if field not in template_config:
                validation_result["errors"].append(f"Missing required field: {field}")
        
        # Validate sections
        if "sections" in template_config:
            sections = template_config["sections"]
            if not isinstance(sections, list):
                validation_result["errors"].append("Sections must be a list")
            elif not sections:
                validation_result["warnings"].append("No sections defined in template")
        
        # Validate metrics
        if "metrics" in template_config:
            metrics = template_config["metrics"]
            if not isinstance(metrics, list):
                validation_result["errors"].append("Metrics must be a list")
            elif not metrics:
                validation_result["warnings"].append("No metrics defined in template")
        
        validation_result["is_valid"] = len(validation_result["errors"]) == 0
        
        return validation_result

    def _generate_custom_report(
        self,
        cost_data: List[Dict[str, Any]],
        template_name: Optional[str],
        custom_filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate custom report based on template."""
        if not template_name or template_name not in self.report_templates:
            return {
                "custom_report": {
                    "error": f"Template '{template_name}' not found"
                }
            }
        
        template = self.report_templates[template_name]
        
        # Generate report sections based on template
        custom_report = {
            "template_name": template_name,
            "template_sections": template.get("sections", []),
            "template_metrics": template.get("metrics", []),
            "generated_sections": {}
        }
        
        # Process each section defined in template
        for section in template.get("sections", []):
            if section == "cost_overview":
                custom_report["generated_sections"][section] = self._calculate_cost_distribution(cost_data)
            elif section == "service_breakdown":
                custom_report["generated_sections"][section] = self._analyze_costs_by_dimension(cost_data, "service")
            elif section == "region_breakdown":
                custom_report["generated_sections"][section] = self._analyze_costs_by_dimension(cost_data, "region")
            elif section == "time_series_analysis":
                custom_report["generated_sections"][section] = self._generate_time_series_analysis(cost_data)
            else:
                custom_report["generated_sections"][section] = {"note": f"Section '{section}' not implemented"}
        
        return {"custom_report": custom_report}

    # Additional helper methods for comprehensive analysis

    def _extract_team_costs_from_allocation(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract team cost information from allocation data."""
        if not allocation_data or "allocation_breakdown" not in allocation_data:
            return {"error": "No allocation breakdown available"}
        
        allocation_breakdown = allocation_data["allocation_breakdown"]
        team_costs = {}
        
        # Look for team-level allocations
        for scope, allocations in allocation_breakdown.items():
            if "team" in scope.lower():
                team_costs.update(allocations)
        
        # Calculate percentages
        total_allocated = sum(team_costs.values())
        team_breakdown = {}
        
        for team, cost in team_costs.items():
            team_breakdown[team] = {
                "total_cost": cost,
                "percentage": (cost / total_allocated * 100) if total_allocated > 0 else 0
            }
        
        return {
            "breakdown": team_breakdown,
            "total_allocated": total_allocated,
            "team_count": len(team_costs)
        }

    def _extract_project_costs_from_allocation(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract project cost information from allocation data."""
        if not allocation_data or "allocation_breakdown" not in allocation_data:
            return {"error": "No allocation breakdown available"}
        
        allocation_breakdown = allocation_data["allocation_breakdown"]
        project_costs = {}
        
        # Look for project-level allocations
        for scope, allocations in allocation_breakdown.items():
            if "project" in scope.lower():
                project_costs.update(allocations)
        
        # Calculate percentages
        total_allocated = sum(project_costs.values())
        project_breakdown = {}
        
        for project, cost in project_costs.items():
            project_breakdown[project] = {
                "total_cost": cost,
                "percentage": (cost / total_allocated * 100) if total_allocated > 0 else 0
            }
        
        return {
            "breakdown": project_breakdown,
            "total_allocated": total_allocated,
            "project_count": len(project_costs)
        }

    def get_report_summary(self) -> Dict[str, Any]:
        """Get summary of reporting engine status and generated reports."""
        return {
            "total_reports_generated": len(self.generated_reports),
            "report_history_count": len(self.report_history),
            "available_templates": list(self.report_templates.keys()),
            "custom_templates": [
                name for name, template in self.report_templates.items() 
                if template.get("is_custom", False)
            ],
            "supported_export_formats": [format_type.value for format_type in ReportFormat],
            "last_report_generated": self.report_history[-1] if self.report_history else None,
            "engine_status": "active",
            "dry_run_mode": self.dry_run
        }
    # Additional missing helper methods

    def _calculate_breakdown_statistics(self, cost_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for cost breakdown."""
        if not cost_data:
            return {"error": "No cost data available"}
        
        costs = [item.get("cost", 0.0) for item in cost_data]
        
        return {
            "total_resources": len(cost_data),
            "total_cost": sum(costs),
            "average_cost": statistics.mean(costs) if costs else 0,
            "median_cost": statistics.median(costs) if costs else 0,
            "max_cost": max(costs) if costs else 0,
            "min_cost": min(costs) if costs else 0,
            "std_deviation": statistics.stdev(costs) if len(costs) > 1 else 0
        }

    def _calculate_savings_percentage(
        self, optimization_data: Dict[str, Any], total_cost: float
    ) -> float:
        """Calculate savings as percentage of total cost."""
        total_savings = self._calculate_total_savings(optimization_data)
        savings_amount = total_savings.get("total_savings", 0.0)
        
        if total_cost > 0:
            return (savings_amount / total_cost) * 100
        return 0.0

    def _summarize_optimization_actions(self, optimization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize optimization actions by type."""
        optimizations = optimization_data.get("optimizations", [])
        
        action_summary = defaultdict(int)
        for opt in optimizations:
            opt_type = opt.get("optimization_type", "unknown")
            action_summary[opt_type] += 1
        
        return {
            "total_actions": len(optimizations),
            "by_type": dict(action_summary),
            "completed_actions": len([opt for opt in optimizations if opt.get("status") == "completed"]),
            "pending_actions": len([opt for opt in optimizations if opt.get("status") == "pending"])
        }

    def _identify_additional_savings_opportunities(self, cost_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify potential additional savings opportunities."""
        # Simplified implementation - in practice would use ML models
        high_cost_resources = [
            item for item in cost_data 
            if item.get("cost", 0.0) > 100.0
        ]
        
        potential_savings = sum(item.get("cost", 0.0) * 0.15 for item in high_cost_resources)  # 15% potential
        
        return {
            "high_cost_resources": len(high_cost_resources),
            "potential_savings": potential_savings,
            "optimization_opportunities": [
                "Right-size underutilized instances",
                "Implement automated scheduling",
                "Optimize storage classes",
                "Review Reserved Instance coverage"
            ]
        }

    def _calculate_absolute_variance(self, total_cost: float, budget_data: Dict[str, Any]) -> float:
        """Calculate absolute variance from budget."""
        budget_amount = budget_data.get("budget_amount", 0.0)
        return total_cost - budget_amount

    def _calculate_percentage_variance(self, total_cost: float, budget_data: Dict[str, Any]) -> float:
        """Calculate percentage variance from budget."""
        budget_amount = budget_data.get("budget_amount", 0.0)
        if budget_amount > 0:
            return ((total_cost - budget_amount) / budget_amount) * 100
        return 0.0

    def _analyze_variance_trend(
        self, cost_data: List[Dict[str, Any]], budget_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze variance trend over time."""
        # Simplified implementation
        daily_costs = defaultdict(float)
        for item in cost_data:
            date_key = item.get("date", "")[:10]
            daily_costs[date_key] += item.get("cost", 0.0)
        
        budget_amount = budget_data.get("budget_amount", 0.0)
        period_days = budget_data.get("period_days", 30)
        daily_budget = budget_amount / period_days if period_days > 0 else 0
        
        variances = []
        for date, cost in daily_costs.items():
            variance = cost - daily_budget
            variances.append(variance)
        
        if variances:
            trend_direction = "increasing" if variances[-1] > variances[0] else "decreasing"
            avg_variance = statistics.mean(variances)
        else:
            trend_direction = "stable"
            avg_variance = 0
        
        return {
            "trend_direction": trend_direction,
            "average_daily_variance": avg_variance,
            "variance_volatility": statistics.stdev(variances) if len(variances) > 1 else 0
        }

    def _identify_variance_drivers(
        self, cost_data: List[Dict[str, Any]], budget_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify key drivers of budget variance."""
        # Group costs by service and identify top contributors to variance
        service_costs = defaultdict(float)
        for item in cost_data:
            service = item.get("service", "unknown")
            service_costs[service] += item.get("cost", 0.0)
        
        total_cost = sum(service_costs.values())
        budget_amount = budget_data.get("budget_amount", 0.0)
        
        drivers = []
        for service, cost in service_costs.items():
            service_percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            expected_cost = budget_amount * (service_percentage / 100)
            variance = cost - expected_cost
            
            if abs(variance) > 10:  # Only include significant variances
                drivers.append({
                    "service": service,
                    "actual_cost": cost,
                    "expected_cost": expected_cost,
                    "variance": variance,
                    "variance_percentage": (variance / expected_cost * 100) if expected_cost > 0 else 0
                })
        
        # Sort by absolute variance
        drivers.sort(key=lambda x: abs(x["variance"]), reverse=True)
        return drivers[:5]  # Top 5 drivers

    def _analyze_forecast_variance(
        self, cost_data: List[Dict[str, Any]], budget_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze variance between actual costs and forecasts."""
        if not budget_data or "forecasts" not in budget_data:
            return {"error": "No forecast data available"}
        
        total_cost = sum(item.get("cost", 0.0) for item in cost_data)
        forecasts = budget_data["forecasts"]
        predicted_spend = forecasts.get("predicted_spend", 0.0)
        
        if predicted_spend > 0:
            forecast_variance = total_cost - predicted_spend
            forecast_accuracy = (1 - abs(forecast_variance) / predicted_spend) * 100
        else:
            forecast_variance = 0
            forecast_accuracy = 0
        
        return {
            "actual_spend": total_cost,
            "predicted_spend": predicted_spend,
            "forecast_variance": forecast_variance,
            "forecast_accuracy": forecast_accuracy,
            "confidence_interval": forecasts.get("confidence_interval", {}),
            "within_confidence_interval": self._check_within_confidence_interval(
                total_cost, forecasts.get("confidence_interval", {})
            )
        }

    def _check_within_confidence_interval(
        self, actual_cost: float, confidence_interval: Dict[str, float]
    ) -> bool:
        """Check if actual cost is within forecast confidence interval."""
        lower = confidence_interval.get("lower", 0)
        upper = confidence_interval.get("upper", float('inf'))
        return lower <= actual_cost <= upper

    def _analyze_trend_variance(self, cost_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze variance in cost trends."""
        # Group by date and calculate daily costs
        daily_costs = defaultdict(float)
        for item in cost_data:
            date_key = item.get("date", "")[:10]
            daily_costs[date_key] += item.get("cost", 0.0)
        
        if len(daily_costs) < 2:
            return {"error": "Insufficient data for trend analysis"}
        
        sorted_dates = sorted(daily_costs.keys())
        costs_series = [daily_costs[date] for date in sorted_dates]
        
        # Calculate trend
        trend = self._calculate_simple_trend(costs_series)
        
        # Calculate variance from trend
        if len(costs_series) > 1:
            trend_variance = statistics.variance(costs_series)
            coefficient_of_variation = (statistics.stdev(costs_series) / statistics.mean(costs_series)) * 100
        else:
            trend_variance = 0
            coefficient_of_variation = 0
        
        return {
            "trend_direction": trend["direction"],
            "trend_strength": abs(trend["slope"]),
            "trend_variance": trend_variance,
            "coefficient_of_variation": coefficient_of_variation,
            "volatility_assessment": self._assess_cost_volatility(coefficient_of_variation)
        }

    def _assess_cost_volatility(self, coefficient_of_variation: float) -> str:
        """Assess cost volatility based on coefficient of variation."""
        if coefficient_of_variation < 10:
            return "low"
        elif coefficient_of_variation < 25:
            return "moderate"
        elif coefficient_of_variation < 50:
            return "high"
        else:
            return "very_high"

    def _perform_comprehensive_root_cause_analysis(
        self,
        cost_data: List[Dict[str, Any]],
        budget_data: Optional[Dict[str, Any]],
        anomaly_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform comprehensive root cause analysis for variances."""
        root_causes = []
        
        # Analyze service-level contributions
        service_analysis = self._analyze_costs_by_dimension(cost_data, "service")
        top_services = list(service_analysis["breakdown"].items())[:3]
        
        for service, data in top_services:
            if data["percentage"] > 30:  # Services contributing >30% of costs
                root_causes.append({
                    "type": "high_service_contribution",
                    "service": service,
                    "contribution": data["percentage"],
                    "description": f"{service} accounts for {data['percentage']:.1f}% of total costs"
                })
        
        # Analyze regional distribution
        region_analysis = self._analyze_costs_by_dimension(cost_data, "region")
        top_regions = list(region_analysis["breakdown"].items())[:2]
        
        for region, data in top_regions:
            if data["percentage"] > 40:  # Regions contributing >40% of costs
                root_causes.append({
                    "type": "regional_concentration",
                    "region": region,
                    "contribution": data["percentage"],
                    "description": f"{region} accounts for {data['percentage']:.1f}% of total costs"
                })
        
        # Analyze anomaly contributions
        if anomaly_data and anomaly_data.get("anomalies_detected"):
            anomaly_count = len(anomaly_data["anomalies_detected"])
            root_causes.append({
                "type": "cost_anomalies",
                "anomaly_count": anomaly_count,
                "description": f"{anomaly_count} cost anomalies detected during the period"
            })
        
        return {
            "identified_root_causes": root_causes,
            "analysis_confidence": "medium",  # Simplified confidence assessment
            "recommendations": self._generate_root_cause_recommendations(root_causes)
        }

    def _generate_root_cause_recommendations(self, root_causes: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on root cause analysis."""
        recommendations = []
        
        for cause in root_causes:
            if cause["type"] == "high_service_contribution":
                recommendations.append(f"Review {cause['service']} usage and optimization opportunities")
            elif cause["type"] == "regional_concentration":
                recommendations.append(f"Consider multi-region cost optimization for {cause['region']}")
            elif cause["type"] == "cost_anomalies":
                recommendations.append("Investigate and address detected cost anomalies")
        
        return recommendations