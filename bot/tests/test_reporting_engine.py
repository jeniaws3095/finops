#!/usr/bin/env python3
"""
Unit Tests for Reporting Engine

Tests comprehensive cost analysis and reporting functionality including:
- Report generation for different types
- Cost breakdown analysis
- Variance analysis and trend reporting
- Export functionality in multiple formats
- Custom template creation and validation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timezone, timedelta
import sys
import os

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.reporting_engine import (
    ReportingEngine, ReportType, ReportFormat, ReportPeriod
)


class TestReportingEngine(unittest.TestCase):
    """Test cases for the Reporting Engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.reporting_engine = ReportingEngine(dry_run=True)
        
        # Sample cost data for testing
        self.sample_cost_data = [
            {
                "resource_id": "i-1234567890abcdef0",
                "service": "EC2",
                "region": "us-east-1",
                "cost": 150.50,
                "date": "2024-01-15",
                "timestamp": "2024-01-15T10:00:00Z",
                "resource_type": "instance"
            },
            {
                "resource_id": "vol-0987654321fedcba0",
                "service": "EBS",
                "region": "us-east-1", 
                "cost": 25.75,
                "date": "2024-01-15",
                "timestamp": "2024-01-15T10:00:00Z",
                "resource_type": "volume"
            },
            {
                "resource_id": "db-instance-1",
                "service": "RDS",
                "region": "us-west-2",
                "cost": 200.00,
                "date": "2024-01-16",
                "timestamp": "2024-01-16T10:00:00Z",
                "resource_type": "database"
            }
        ]
        
        # Sample budget data
        self.sample_budget_data = {
            "budget_amount": 500.00,
            "period_days": 30,
            "forecasts": {
                "predicted_spend": 450.00,
                "confidence_interval": {"lower": 400.00, "upper": 500.00}
            }
        }
        
        # Sample allocation data
        self.sample_allocation_data = {
            "allocation_breakdown": {
                "team": {
                    "engineering": 200.00,
                    "marketing": 100.00,
                    "operations": 76.25
                },
                "project": {
                    "project-a": 150.00,
                    "project-b": 226.25
                }
            },
            "total_costs": 376.25,
            "allocated_costs": 376.25
        }
        
        # Sample optimization data
        self.sample_optimization_data = {
            "optimizations": [
                {
                    "optimization_id": "opt-001",
                    "resource_id": "i-1234567890abcdef0",
                    "optimization_type": "rightsizing",
                    "estimated_savings": 50.00,
                    "status": "completed"
                },
                {
                    "optimization_id": "opt-002", 
                    "resource_id": "vol-0987654321fedcba0",
                    "optimization_type": "storage_optimization",
                    "estimated_savings": 10.00,
                    "status": "pending"
                }
            ]
        }

    def test_initialization(self):
        """Test reporting engine initialization."""
        engine = ReportingEngine(dry_run=True)
        
        self.assertTrue(engine.dry_run)
        self.assertIsInstance(engine.report_templates, dict)
        self.assertIsInstance(engine.generated_reports, dict)
        self.assertIsInstance(engine.report_history, list)
        
        # Check default templates are loaded
        self.assertIn("executive_summary", engine.report_templates)
        self.assertIn("detailed_cost_breakdown", engine.report_templates)
        self.assertIn("variance_analysis", engine.report_templates)

    def test_generate_executive_summary_report(self):
        """Test executive summary report generation."""
        report = self.reporting_engine.generate_comprehensive_report(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            period_start="2024-01-15T00:00:00Z",
            period_end="2024-01-16T23:59:59Z",
            cost_data=self.sample_cost_data,
            budget_data=self.sample_budget_data,
            allocation_data=self.sample_allocation_data,
            optimization_data=self.sample_optimization_data
        )
        
        # Verify report structure
        self.assertIn("report_id", report)
        self.assertEqual(report["report_type"], "executive_summary")
        self.assertIn("executive_summary", report)
        
        # Verify executive summary sections
        exec_summary = report["executive_summary"]
        self.assertIn("cost_overview", exec_summary)
        self.assertIn("budget_performance", exec_summary)
        self.assertIn("savings_achieved", exec_summary)
        self.assertIn("key_insights", exec_summary)
        self.assertIn("recommendations", exec_summary)
        
        # Verify cost overview calculations
        cost_overview = exec_summary["cost_overview"]
        expected_total = sum(item["cost"] for item in self.sample_cost_data)
        self.assertEqual(cost_overview["total_spend"], expected_total)
        self.assertIn("top_cost_drivers", cost_overview)

    def test_generate_cost_breakdown_report(self):
        """Test cost breakdown report generation."""
        report = self.reporting_engine.generate_comprehensive_report(
            report_type=ReportType.COST_BREAKDOWN,
            period_start="2024-01-15T00:00:00Z",
            period_end="2024-01-16T23:59:59Z",
            cost_data=self.sample_cost_data,
            allocation_data=self.sample_allocation_data
        )
        
        # Verify report structure
        self.assertIn("cost_breakdown", report)
        
        # Verify breakdown sections
        breakdown = report["cost_breakdown"]
        self.assertIn("service_breakdown", breakdown)
        self.assertIn("region_breakdown", breakdown)
        self.assertIn("team_breakdown", breakdown)
        self.assertIn("project_breakdown", breakdown)
        self.assertIn("time_series_analysis", breakdown)
        
        # Verify service breakdown
        service_breakdown = breakdown["service_breakdown"]
        self.assertIn("breakdown", service_breakdown)
        self.assertIn("total_cost", service_breakdown)
        
        # Check that services are properly categorized
        service_data = service_breakdown["breakdown"]
        self.assertIn("EC2", service_data)
        self.assertIn("EBS", service_data)
        self.assertIn("RDS", service_data)

    def test_generate_variance_analysis_report(self):
        """Test variance analysis report generation."""
        report = self.reporting_engine.generate_comprehensive_report(
            report_type=ReportType.VARIANCE_ANALYSIS,
            period_start="2024-01-15T00:00:00Z",
            period_end="2024-01-16T23:59:59Z",
            cost_data=self.sample_cost_data,
            budget_data=self.sample_budget_data
        )
        
        # Verify report structure
        self.assertIn("variance_analysis", report)
        
        # Verify variance analysis sections
        variance = report["variance_analysis"]
        self.assertIn("budget_variance", variance)
        self.assertIn("forecast_variance", variance)
        self.assertIn("trend_variance", variance)
        self.assertIn("root_cause_analysis", variance)
        
        # Verify budget variance calculations
        budget_variance = variance["budget_variance"]
        self.assertIn("absolute_variance", budget_variance)
        self.assertIn("percentage_variance", budget_variance)

    def test_cost_distribution_calculation(self):
        """Test cost distribution calculation."""
        distribution = self.reporting_engine._calculate_cost_distribution(self.sample_cost_data)
        
        self.assertIn("by_service", distribution)
        self.assertIn("by_region", distribution)
        self.assertIn("total_cost", distribution)
        
        # Verify total cost calculation
        expected_total = sum(item["cost"] for item in self.sample_cost_data)
        self.assertEqual(distribution["total_cost"], expected_total)
        
        # Verify service distribution percentages
        service_dist = distribution["by_service"]
        total_percentage = sum(service_dist.values())
        self.assertAlmostEqual(total_percentage, 100.0, places=1)

    def test_top_cost_drivers_identification(self):
        """Test identification of top cost drivers."""
        top_drivers = self.reporting_engine._identify_top_cost_drivers(self.sample_cost_data, limit=2)
        
        self.assertIsInstance(top_drivers, list)
        self.assertLessEqual(len(top_drivers), 2)
        
        if top_drivers:
            # Verify structure of top driver
            driver = top_drivers[0]
            self.assertIn("resource_id", driver)
            self.assertIn("cost", driver)
            self.assertIn("service", driver)
            self.assertIn("region", driver)
            
            # Verify drivers are sorted by cost (descending)
            if len(top_drivers) > 1:
                self.assertGreaterEqual(top_drivers[0]["cost"], top_drivers[1]["cost"])

    def test_budget_utilization_calculation(self):
        """Test budget utilization calculation."""
        total_cost = sum(item["cost"] for item in self.sample_cost_data)
        utilization = self.reporting_engine._calculate_budget_utilization(total_cost, self.sample_budget_data)
        
        self.assertIn("budget_amount", utilization)
        self.assertIn("spent_amount", utilization)
        self.assertIn("utilization_percentage", utilization)
        self.assertIn("remaining_budget", utilization)
        self.assertIn("status", utilization)
        
        # Verify calculations
        expected_utilization = (total_cost / self.sample_budget_data["budget_amount"]) * 100
        self.assertAlmostEqual(utilization["utilization_percentage"], expected_utilization, places=2)

    def test_time_series_analysis(self):
        """Test time series analysis generation."""
        time_series = self.reporting_engine._generate_time_series_analysis(self.sample_cost_data)
        
        self.assertIn("daily_costs", time_series)
        self.assertIn("trend", time_series)
        self.assertIn("statistics", time_series)
        
        # Verify daily costs structure
        daily_costs = time_series["daily_costs"]
        self.assertIsInstance(daily_costs, dict)
        
        # Verify statistics
        stats = time_series["statistics"]
        self.assertIn("average_daily_cost", stats)
        self.assertIn("max_daily_cost", stats)
        self.assertIn("min_daily_cost", stats)
        self.assertIn("total_days", stats)

    def test_export_json_format(self):
        """Test JSON export functionality."""
        # Generate a report first
        report = self.reporting_engine.generate_comprehensive_report(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            period_start="2024-01-15T00:00:00Z",
            period_end="2024-01-16T23:59:59Z",
            cost_data=self.sample_cost_data
        )
        
        # Export to JSON
        export_result = self.reporting_engine.export_report(
            report_id=report["report_id"],
            format_type=ReportFormat.JSON,
            output_path="test_report.json"
        )
        
        self.assertTrue(export_result["export_success"])
        self.assertIn("file_size", export_result)
        self.assertIn("content_preview", export_result)  # In dry_run mode

    def test_export_csv_format(self):
        """Test CSV export functionality."""
        # Generate a report first
        report = self.reporting_engine.generate_comprehensive_report(
            report_type=ReportType.COST_BREAKDOWN,
            period_start="2024-01-15T00:00:00Z",
            period_end="2024-01-16T23:59:59Z",
            cost_data=self.sample_cost_data
        )
        
        # Export to CSV
        export_result = self.reporting_engine.export_report(
            report_id=report["report_id"],
            format_type=ReportFormat.CSV,
            output_path="test_report.csv"
        )
        
        self.assertTrue(export_result["export_success"])
        self.assertIn("file_size", export_result)
        self.assertIn("rows_exported", export_result)

    def test_export_html_format(self):
        """Test HTML export functionality."""
        # Generate a report first
        report = self.reporting_engine.generate_comprehensive_report(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            period_start="2024-01-15T00:00:00Z",
            period_end="2024-01-16T23:59:59Z",
            cost_data=self.sample_cost_data,
            budget_data=self.sample_budget_data
        )
        
        # Export to HTML
        export_result = self.reporting_engine.export_report(
            report_id=report["report_id"],
            format_type=ReportFormat.HTML,
            output_path="test_report.html"
        )
        
        self.assertTrue(export_result["export_success"])
        self.assertIn("file_size", export_result)
        self.assertIn("content_preview", export_result)

    def test_create_custom_template(self):
        """Test custom template creation."""
        template_config = {
            "name": "Custom Cost Analysis",
            "sections": ["cost_overview", "service_breakdown", "recommendations"],
            "metrics": ["total_spend", "top_services", "optimization_opportunities"],
            "filters": {"min_cost": 10.0},
            "formatting": {"currency": "USD"}
        }
        
        result = self.reporting_engine.create_custom_template(
            template_name="custom_analysis",
            template_config=template_config
        )
        
        self.assertIn("template_name", result)
        self.assertIn("created_at", result)
        self.assertIn("validation_result", result)
        self.assertTrue(result["validation_result"]["is_valid"])
        
        # Verify template is stored
        self.assertIn("custom_analysis", self.reporting_engine.report_templates)

    def test_template_validation(self):
        """Test template configuration validation."""
        # Valid template
        valid_config = {
            "sections": ["cost_overview"],
            "metrics": ["total_spend"]
        }
        validation = self.reporting_engine._validate_template_config(valid_config)
        self.assertTrue(validation["is_valid"])
        self.assertEqual(len(validation["errors"]), 0)
        
        # Invalid template (missing required fields)
        invalid_config = {
            "name": "Test Template"
        }
        validation = self.reporting_engine._validate_template_config(invalid_config)
        self.assertFalse(validation["is_valid"])
        self.assertGreater(len(validation["errors"]), 0)

    def test_custom_filters_application(self):
        """Test application of custom filters to cost data."""
        filters = {
            "services": ["EC2", "RDS"],
            "min_cost": 50.0
        }
        
        filtered_data = self.reporting_engine._apply_data_filters(self.sample_cost_data, filters)
        
        # Should only include EC2 and RDS services with cost >= 50
        self.assertLessEqual(len(filtered_data), len(self.sample_cost_data))
        
        for item in filtered_data:
            self.assertIn(item["service"], ["EC2", "RDS"])
            self.assertGreaterEqual(item["cost"], 50.0)

    def test_flatten_report_for_csv(self):
        """Test flattening of nested report data for CSV export."""
        # Generate a sample report
        report = self.reporting_engine.generate_comprehensive_report(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            period_start="2024-01-15T00:00:00Z",
            period_end="2024-01-16T23:59:59Z",
            cost_data=self.sample_cost_data
        )
        
        flattened = self.reporting_engine._flatten_report_for_csv(report)
        
        self.assertIsInstance(flattened, list)
        self.assertGreater(len(flattened), 0)
        
        # Verify structure of flattened data
        if flattened:
            row = flattened[0]
            self.assertIn("report_id", row)
            self.assertIn("report_type", row)
            self.assertIn("section", row)
            self.assertIn("metric", row)

    def test_key_insights_generation(self):
        """Test generation of key insights."""
        insights = self.reporting_engine._generate_key_insights(
            self.sample_cost_data,
            self.sample_budget_data,
            self.sample_allocation_data,
            None,  # No anomaly data
            self.sample_optimization_data
        )
        
        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)
        
        # Verify insights are strings
        for insight in insights:
            self.assertIsInstance(insight, str)
            self.assertGreater(len(insight), 0)

    def test_executive_recommendations_generation(self):
        """Test generation of executive recommendations."""
        recommendations = self.reporting_engine._generate_executive_recommendations(
            self.sample_cost_data,
            self.sample_budget_data,
            self.sample_allocation_data,
            None,  # No anomaly data
            self.sample_optimization_data
        )
        
        self.assertIsInstance(recommendations, list)
        
        # Verify recommendation structure
        for rec in recommendations:
            self.assertIn("priority", rec)
            self.assertIn("category", rec)
            self.assertIn("recommendation", rec)
            self.assertIn("action", rec)
            self.assertIn(rec["priority"], ["low", "medium", "high"])

    def test_report_history_tracking(self):
        """Test that report history is properly tracked."""
        initial_count = len(self.reporting_engine.report_history)
        
        # Generate a report
        self.reporting_engine.generate_comprehensive_report(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            period_start="2024-01-15T00:00:00Z",
            period_end="2024-01-16T23:59:59Z",
            cost_data=self.sample_cost_data
        )
        
        # Verify history was updated
        self.assertEqual(len(self.reporting_engine.report_history), initial_count + 1)
        
        # Verify history entry structure
        latest_entry = self.reporting_engine.report_history[-1]
        self.assertIn("report_id", latest_entry)
        self.assertIn("report_type", latest_entry)
        self.assertIn("generated_at", latest_entry)
        self.assertIn("period", latest_entry)

    def test_get_report_summary(self):
        """Test report summary generation."""
        # Generate a few reports first
        for report_type in [ReportType.EXECUTIVE_SUMMARY, ReportType.COST_BREAKDOWN]:
            self.reporting_engine.generate_comprehensive_report(
                report_type=report_type,
                period_start="2024-01-15T00:00:00Z",
                period_end="2024-01-16T23:59:59Z",
                cost_data=self.sample_cost_data
            )
        
        summary = self.reporting_engine.get_report_summary()
        
        self.assertIn("total_reports_generated", summary)
        self.assertIn("report_history_count", summary)
        self.assertIn("available_templates", summary)
        self.assertIn("supported_export_formats", summary)
        self.assertIn("engine_status", summary)
        self.assertIn("dry_run_mode", summary)
        
        # Verify counts
        self.assertGreaterEqual(summary["total_reports_generated"], 2)
        self.assertEqual(summary["dry_run_mode"], True)

    def test_error_handling_invalid_report_id(self):
        """Test error handling for invalid report ID during export."""
        with self.assertRaises(ValueError):
            self.reporting_engine.export_report(
                report_id="non-existent-report",
                format_type=ReportFormat.JSON
            )

    def test_error_handling_empty_cost_data(self):
        """Test handling of empty cost data."""
        report = self.reporting_engine.generate_comprehensive_report(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            period_start="2024-01-15T00:00:00Z",
            period_end="2024-01-16T23:59:59Z",
            cost_data=[]  # Empty cost data
        )
        
        # Should still generate a report structure
        self.assertIn("report_id", report)
        self.assertIn("executive_summary", report)
        
        # Cost overview should handle empty data gracefully
        cost_overview = report["executive_summary"]["cost_overview"]
        self.assertEqual(cost_overview["total_spend"], 0.0)


if __name__ == '__main__':
    unittest.main()