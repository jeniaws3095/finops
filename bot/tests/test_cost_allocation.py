#!/usr/bin/env python3
"""
Unit Tests for Cost Allocation Engine

Tests the comprehensive cost allocation functionality including:
- Tag-based allocation logic with fallback rules
- Usage pattern analysis for automatic cost distribution
- Team and project cost tracking with hierarchical rollup
- Allocation rule validation and conflict resolution

Requirements: 6.2 - Automated Cost Allocation
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
import json

# Import the cost allocation engine
from core.cost_allocation import (
    CostAllocationEngine, AllocationMethod, AllocationScope, 
    FallbackStrategy, AllocationRule
)


class TestCostAllocationEngine(unittest.TestCase):
    """Test cases for the Cost Allocation Engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = CostAllocationEngine(dry_run=True)
        
        # Sample cost data for testing
        self.sample_cost_data = [
            {
                "resource_id": "i-1234567890abcdef0",
                "service": "ec2",
                "region": "us-east-1",
                "cost": 150.50,
                "tags": {
                    "Team": "engineering",
                    "Project": "web-app",
                    "Environment": "production"
                },
                "timestamp": "2024-01-15T10:00:00Z"
            },
            {
                "resource_id": "db-abcdef1234567890",
                "service": "rds",
                "region": "us-east-1",
                "cost": 89.25,
                "tags": {
                    "Team": "data",
                    "Project": "analytics",
                    "Environment": "production"
                },
                "timestamp": "2024-01-15T10:00:00Z"
            },
            {
                "resource_id": "lambda-func-123",
                "service": "lambda",
                "region": "us-west-2",
                "cost": 12.75,
                "tags": {
                    "Team": "engineering",
                    "Environment": "development"
                },
                "timestamp": "2024-01-15T10:00:00Z"
            },
            {
                "resource_id": "s3-bucket-456",
                "service": "s3",
                "region": "us-east-1",
                "cost": 45.00,
                "tags": {},  # Untagged resource
                "timestamp": "2024-01-15T10:00:00Z"
            }
        ]

    def test_engine_initialization(self):
        """Test cost allocation engine initialization."""
        engine = CostAllocationEngine(dry_run=True)
        
        self.assertTrue(engine.dry_run)
        self.assertEqual(len(engine.allocation_rules), 0)
        self.assertEqual(len(engine.allocation_history), 0)
        self.assertIn("primary_allocation_tags", engine.default_config)
        self.assertEqual(engine.default_config["fallback_strategy"], FallbackStrategy.UNALLOCATED_POOL)

    def test_create_tag_based_allocation_rule(self):
        """Test creating a tag-based allocation rule."""
        rule_config = self.engine.create_allocation_rule(
            rule_id="team_allocation",
            name="Team-based Cost Allocation",
            method=AllocationMethod.TAG_BASED,
            scope=AllocationScope.TEAM,
            priority=10,
            conditions={"tags": {"Environment": ["production", "staging"]}},
            allocation_targets={"engineering": 60.0, "data": 40.0}
        )
        
        self.assertIsNotNone(rule_config)
        self.assertEqual(rule_config["rule_id"], "team_allocation")
        self.assertEqual(rule_config["method"], "tag_based")
        self.assertEqual(rule_config["scope"], "team")
        self.assertEqual(rule_config["priority"], 10)
        self.assertTrue(rule_config["validation_result"]["is_valid"])
        
        # Verify rule is stored
        self.assertIn("team_allocation", self.engine.allocation_rules)

    def test_create_proportional_allocation_rule(self):
        """Test creating a proportional allocation rule."""
        rule_config = self.engine.create_allocation_rule(
            rule_id="project_allocation",
            name="Project Proportional Allocation",
            method=AllocationMethod.PROPORTIONAL,
            scope=AllocationScope.PROJECT,
            priority=20,
            allocation_targets={"web-app": 70.0, "analytics": 30.0}
        )
        
        self.assertIsNotNone(rule_config)
        self.assertEqual(rule_config["method"], "proportional")
        self.assertTrue(rule_config["validation_result"]["is_valid"])

    def test_allocation_rule_validation(self):
        """Test allocation rule validation."""
        # Test invalid rule (proportional without targets)
        with self.assertRaises(ValueError):
            self.engine.create_allocation_rule(
                rule_id="invalid_rule",
                name="Invalid Rule",
                method=AllocationMethod.PROPORTIONAL,
                scope=AllocationScope.PROJECT,
                priority=10
                # Missing allocation_targets
            )

    def test_cost_allocation_with_tag_based_rule(self):
        """Test cost allocation using tag-based rules."""
        # Create a tag-based allocation rule
        self.engine.create_allocation_rule(
            rule_id="team_tag_rule",
            name="Team Tag Allocation",
            method=AllocationMethod.TAG_BASED,
            scope=AllocationScope.TEAM,
            priority=10
        )
        
        # Allocate costs
        allocation_results = self.engine.allocate_costs(
            self.sample_cost_data,
            allocation_period="2024-01"
        )
        
        self.assertIsNotNone(allocation_results)
        self.assertEqual(allocation_results["period"], "2024-01")
        self.assertGreater(allocation_results["total_costs"], 0)
        self.assertGreater(allocation_results["allocated_costs"], 0)
        
        # Check that tagged resources were allocated
        self.assertGreater(len(allocation_results["rule_applications"]), 0)
        
        # Verify allocation breakdown
        self.assertIn("allocation_breakdown", allocation_results)

    def test_cost_allocation_with_untagged_resources(self):
        """Test handling of untagged resources."""
        # Create a tag-based rule
        self.engine.create_allocation_rule(
            rule_id="team_only_rule",
            name="Team Only Allocation",
            method=AllocationMethod.TAG_BASED,
            scope=AllocationScope.TEAM,
            priority=10
        )
        
        # Allocate costs (includes untagged S3 bucket)
        allocation_results = self.engine.allocate_costs(
            self.sample_cost_data,
            allocation_period="2024-01"
        )
        
        # Should have unallocated costs due to untagged resource
        self.assertGreater(allocation_results["unallocated_costs"], 0)
        self.assertGreater(len(allocation_results["unallocated_resources"]), 0)
        
        # Find the untagged resource
        untagged_resource = next(
            (r for r in allocation_results["unallocated_resources"] 
             if r["resource_id"] == "s3-bucket-456"), 
            None
        )
        self.assertIsNotNone(untagged_resource)

    def test_proportional_allocation(self):
        """Test proportional allocation method."""
        # Create proportional allocation rule
        self.engine.create_allocation_rule(
            rule_id="proportional_rule",
            name="Proportional Allocation",
            method=AllocationMethod.PROPORTIONAL,
            scope=AllocationScope.PROJECT,
            priority=10,
            allocation_targets={"web-app": 60.0, "analytics": 40.0}
        )
        
        # Test with single cost record
        test_cost = [
            {
                "resource_id": "test-resource",
                "service": "ec2",
                "region": "us-east-1",
                "cost": 100.0,
                "tags": {"Team": "engineering"},
                "timestamp": "2024-01-15T10:00:00Z"
            }
        ]
        
        allocation_results = self.engine.allocate_costs(test_cost, "2024-01")
        
        # Should be allocated proportionally
        self.assertEqual(allocation_results["allocated_costs"], 100.0)
        self.assertEqual(allocation_results["unallocated_costs"], 0.0)

    def test_equal_split_allocation(self):
        """Test equal split allocation method."""
        # Create equal split allocation rule
        self.engine.create_allocation_rule(
            rule_id="equal_split_rule",
            name="Equal Split Allocation",
            method=AllocationMethod.EQUAL_SPLIT,
            scope=AllocationScope.TEAM,
            priority=10,
            allocation_targets={"team1": 0, "team2": 0, "team3": 0}  # Values don't matter for equal split
        )
        
        # Test with single cost record
        test_cost = [
            {
                "resource_id": "test-resource",
                "service": "ec2",
                "region": "us-east-1",
                "cost": 90.0,  # Should split into 30.0 each
                "tags": {"Environment": "production"},
                "timestamp": "2024-01-15T10:00:00Z"
            }
        ]
        
        allocation_results = self.engine.allocate_costs(test_cost, "2024-01")
        
        # Should be fully allocated
        self.assertEqual(allocation_results["allocated_costs"], 90.0)
        self.assertEqual(allocation_results["unallocated_costs"], 0.0)

    def test_usage_pattern_analysis(self):
        """Test usage pattern analysis functionality."""
        # Analyze usage patterns
        pattern_analysis = self.engine.analyze_usage_patterns(
            self.sample_cost_data,
            analysis_period_months=6
        )
        
        self.assertIsNotNone(pattern_analysis)
        self.assertIn("tag_patterns", pattern_analysis)
        self.assertIn("service_patterns", pattern_analysis)
        self.assertIn("region_patterns", pattern_analysis)
        self.assertIn("cost_distribution", pattern_analysis)
        self.assertIn("allocation_recommendations", pattern_analysis)
        
        # Check that patterns were detected
        self.assertGreater(len(pattern_analysis["tag_patterns"]), 0)
        self.assertGreater(len(pattern_analysis["service_patterns"]), 0)

    def test_hierarchical_structure_setup(self):
        """Test hierarchical structure configuration."""
        hierarchy = {
            "organization": "TechCorp",
            "levels": ["organization", "business_unit", "team", "project"],
            "business_units": {
                "engineering": ["web-team", "mobile-team"],
                "data": ["analytics-team", "ml-team"]
            }
        }
        
        result = self.engine.setup_hierarchical_structure(hierarchy)
        
        self.assertIsNotNone(result)
        self.assertTrue(result["validation"]["is_valid"])
        self.assertIn("rollup_paths", result)

    def test_allocation_rule_conflict_detection(self):
        """Test detection of conflicting allocation rules."""
        # Create two rules with same priority and overlapping conditions
        self.engine.create_allocation_rule(
            rule_id="rule1",
            name="Rule 1",
            method=AllocationMethod.TAG_BASED,
            scope=AllocationScope.TEAM,
            priority=10,
            conditions={"tags": {"Environment": ["production"]}}
        )
        
        self.engine.create_allocation_rule(
            rule_id="rule2",
            name="Rule 2",
            method=AllocationMethod.PROPORTIONAL,
            scope=AllocationScope.PROJECT,
            priority=10,  # Same priority
            conditions={"tags": {"Environment": ["production"]}},  # Overlapping condition
            allocation_targets={"project1": 50.0, "project2": 50.0}
        )
        
        # Validate rules to detect conflicts
        validation_results = self.engine.validate_allocation_rules()
        
        self.assertGreater(len(validation_results["detected_conflicts"]), 0)

    def test_conflict_resolution(self):
        """Test allocation rule conflict resolution."""
        # Create conflicting rules
        self.engine.create_allocation_rule(
            rule_id="high_priority",
            name="High Priority Rule",
            method=AllocationMethod.TAG_BASED,
            scope=AllocationScope.TEAM,
            priority=5  # Higher priority (lower number)
        )
        
        self.engine.create_allocation_rule(
            rule_id="low_priority",
            name="Low Priority Rule",
            method=AllocationMethod.TAG_BASED,
            scope=AllocationScope.TEAM,
            priority=15  # Lower priority (higher number)
        )
        
        # Simulate conflict
        conflicts = [
            {
                "type": "priority_conflict",
                "rule1": "high_priority",
                "rule2": "low_priority",
                "description": "Rules have same conditions"
            }
        ]
        
        resolution_results = self.engine.resolve_allocation_conflicts(
            conflicts, "highest_priority"
        )
        
        self.assertGreater(resolution_results["resolved_conflicts"], 0)

    def test_allocation_report_generation(self):
        """Test comprehensive allocation report generation."""
        # Create allocation rule and allocate costs
        self.engine.create_allocation_rule(
            rule_id="report_test_rule",
            name="Report Test Rule",
            method=AllocationMethod.TAG_BASED,
            scope=AllocationScope.TEAM,
            priority=10
        )
        
        allocation_results = self.engine.allocate_costs(
            self.sample_cost_data,
            allocation_period="2024-01"
        )
        
        # Generate report
        report = self.engine.generate_allocation_report(
            period="2024-01",
            include_details=True
        )
        
        self.assertIsNotNone(report)
        self.assertEqual(report["period"], "2024-01")
        self.assertIn("executive_summary", report)
        self.assertIn("allocation_metrics", report)
        self.assertIn("cost_breakdown", report)
        self.assertIn("recommendations", report)
        self.assertIn("detailed_breakdowns", report)

    def test_minimum_allocation_threshold(self):
        """Test minimum allocation threshold handling."""
        # Create rule
        self.engine.create_allocation_rule(
            rule_id="threshold_test",
            name="Threshold Test",
            method=AllocationMethod.TAG_BASED,
            scope=AllocationScope.TEAM,
            priority=10
        )
        
        # Test with cost below threshold
        small_cost_data = [
            {
                "resource_id": "tiny-resource",
                "service": "lambda",
                "region": "us-east-1",
                "cost": 0.005,  # Below default threshold of 0.01
                "tags": {"Team": "engineering"},
                "timestamp": "2024-01-15T10:00:00Z"
            }
        ]
        
        allocation_results = self.engine.allocate_costs(small_cost_data, "2024-01")
        
        # Should not be allocated due to threshold
        self.assertEqual(allocation_results["allocated_costs"], 0.0)
        self.assertGreater(allocation_results["unallocated_costs"], 0.0)

    def test_allocation_summary(self):
        """Test allocation engine summary functionality."""
        # Create some rules and allocations
        self.engine.create_allocation_rule(
            rule_id="summary_test_rule",
            name="Summary Test Rule",
            method=AllocationMethod.TAG_BASED,
            scope=AllocationScope.TEAM,
            priority=10
        )
        
        self.engine.allocate_costs(self.sample_cost_data, "2024-01")
        
        summary = self.engine.get_allocation_summary()
        
        self.assertIsNotNone(summary)
        self.assertIn("total_rules", summary)
        self.assertIn("active_rules", summary)
        self.assertIn("allocation_history_records", summary)
        self.assertIn("configuration", summary)
        self.assertEqual(summary["total_rules"], 1)
        self.assertEqual(summary["active_rules"], 1)


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)