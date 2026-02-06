#!/usr/bin/env python3
"""
Cost Allocation Engine for Advanced FinOps Platform

Core expense distribution engine that:
- Implements tag-based cost allocation logic with fallback rules
- Provides usage pattern analysis for automatic cost distribution
- Supports team and project cost tracking with hierarchical rollup
- Includes allocation rule validation and conflict resolution
- Handles untagged resources with intelligent fallback mechanisms

Requirements: 6.2 - Automated Cost Allocation
"""

import logging
import statistics
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
import json
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class AllocationMethod(Enum):
    """Methods for cost allocation."""
    TAG_BASED = "tag_based"
    USAGE_PATTERN = "usage_pattern"
    EQUAL_SPLIT = "equal_split"
    PROPORTIONAL = "proportional"
    CUSTOM_RULE = "custom_rule"


class AllocationScope(Enum):
    """Scope levels for cost allocation."""
    ORGANIZATION = "organization"
    BUSINESS_UNIT = "business_unit"
    TEAM = "team"
    PROJECT = "project"
    ENVIRONMENT = "environment"
    SERVICE = "service"


class FallbackStrategy(Enum):
    """Fallback strategies for untagged resources."""
    UNALLOCATED_POOL = "unallocated_pool"
    EQUAL_DISTRIBUTION = "equal_distribution"
    USAGE_BASED = "usage_based"
    DEFAULT_ALLOCATION = "default_allocation"
    MANUAL_REVIEW = "manual_review"


class AllocationRule:
    """Represents a cost allocation rule."""
    
    def __init__(self, rule_id: str, name: str, method: AllocationMethod,
                 scope: AllocationScope, priority: int = 100,
                 conditions: Optional[Dict[str, Any]] = None,
                 allocation_targets: Optional[Dict[str, float]] = None):
        self.rule_id = rule_id
        self.name = name
        self.method = method
        self.scope = scope
        self.priority = priority  # Lower number = higher priority
        self.conditions = conditions or {}
        self.allocation_targets = allocation_targets or {}
        self.created_at = datetime.now(timezone.utc)
        self.is_active = True

class CostAllocationEngine:
    """
    Advanced cost allocation engine with tag-based allocation, usage pattern analysis,
    and hierarchical cost tracking with comprehensive fallback mechanisms.
    """

    def __init__(self, dry_run: bool = True):
        """
        Initialize the Cost Allocation Engine.
        
        Args:
            dry_run: If True, no actual allocations will be persisted
        """
        self.dry_run = dry_run
        self.allocation_rules = {}  # Rule storage by rule_id
        self.allocation_history = []  # Historical allocation records
        self.unallocated_costs = {}  # Costs that couldn't be allocated
        self.allocation_conflicts = []  # Detected rule conflicts
        self.hierarchical_structure = {}  # Organizational hierarchy
        self.tag_mappings = {}  # Tag value mappings and aliases
        self.usage_patterns = {}  # Learned usage patterns for allocation
        
        # Default allocation configuration
        self.default_config = {
            "primary_allocation_tags": ["Team", "Project", "Environment", "CostCenter"],
            "fallback_strategy": FallbackStrategy.UNALLOCATED_POOL,
            "minimum_allocation_threshold": 0.01,  # $0.01 minimum
            "allocation_precision": 2,  # Decimal places
            "enable_usage_pattern_learning": True,
            "conflict_resolution_strategy": "highest_priority"
        }
        
        logger.info(f"Cost Allocation Engine initialized (DRY_RUN: {dry_run})")

    def create_allocation_rule(
        self,
        rule_id: str,
        name: str,
        method: AllocationMethod,
        scope: AllocationScope,
        priority: int = 100,
        conditions: Optional[Dict[str, Any]] = None,
        allocation_targets: Optional[Dict[str, float]] = None,
        fallback_strategy: Optional[FallbackStrategy] = None
    ) -> Dict[str, Any]:
        """
        Create a new cost allocation rule.
        
        Args:
            rule_id: Unique identifier for the rule
            name: Human-readable name for the rule
            method: Allocation method to use
            scope: Scope level for allocation
            priority: Rule priority (lower = higher priority)
            conditions: Conditions that must be met for rule to apply
            allocation_targets: Target allocation percentages/amounts
            fallback_strategy: Strategy for handling unallocated costs
            
        Returns:
            Dict containing rule configuration and validation results
        """
        try:
            # Validate rule doesn't already exist
            if rule_id in self.allocation_rules:
                raise ValueError(f"Allocation rule {rule_id} already exists")
            
            # Create rule instance
            rule = AllocationRule(
                rule_id=rule_id,
                name=name,
                method=method,
                scope=scope,
                priority=priority,
                conditions=conditions,
                allocation_targets=allocation_targets
            )
            
            # Validate rule configuration
            validation_result = self._validate_allocation_rule(rule)
            if not validation_result["is_valid"]:
                raise ValueError(f"Rule validation failed: {validation_result['errors']}")
            
            # Check for conflicts with existing rules
            conflicts = self._detect_rule_conflicts(rule)
            if conflicts:
                logger.warning(f"Rule {rule_id} has conflicts: {conflicts}")
            
            # Store rule
            rule_config = {
                "rule_id": rule_id,
                "name": name,
                "method": method.value,
                "scope": scope.value,
                "priority": priority,
                "conditions": conditions or {},
                "allocation_targets": allocation_targets or {},
                "fallback_strategy": fallback_strategy.value if fallback_strategy else None,
                "created_at": rule.created_at.isoformat(),
                "is_active": True,
                "validation_result": validation_result,
                "detected_conflicts": conflicts
            }
            
            self.allocation_rules[rule_id] = rule_config
            
            if self.dry_run:
                logger.info(f"DRY_RUN: Created allocation rule {rule_id}")
            else:
                logger.info(f"Created allocation rule: {rule_id} ({method.value})")
            
            return rule_config
            
        except Exception as e:
            logger.error(f"Error creating allocation rule {rule_id}: {str(e)}")
            raise

    def allocate_costs(
        self,
        cost_data: List[Dict[str, Any]],
        allocation_period: str,
        force_reallocation: bool = False
    ) -> Dict[str, Any]:
        """
        Allocate costs based on configured rules and patterns.
        
        Args:
            cost_data: List of cost records with resource information
            allocation_period: Period identifier (e.g., "2024-01")
            force_reallocation: Force reallocation even if already processed
            
        Returns:
            Dict containing allocation results and summary
        """
        try:
            logger.info(f"Starting cost allocation for period {allocation_period}")
            logger.info(f"Processing {len(cost_data)} cost records")
            
            # Initialize allocation tracking
            allocation_results = {
                "period": allocation_period,
                "total_costs": 0.0,
                "allocated_costs": 0.0,
                "unallocated_costs": 0.0,
                "allocation_breakdown": defaultdict(lambda: defaultdict(float)),
                "rule_applications": [],
                "unallocated_resources": [],
                "allocation_conflicts": [],
                "processing_summary": {}
            }
            
            # Process each cost record
            for cost_record in cost_data:
                try:
                    record_allocation = self._allocate_single_cost_record(
                        cost_record, allocation_period
                    )
                    
                    # Update allocation results
                    cost_amount = cost_record.get("cost", 0.0)
                    allocation_results["total_costs"] += cost_amount
                    
                    if record_allocation["allocated"]:
                        allocation_results["allocated_costs"] += cost_amount
                        
                        # Update breakdown by allocation targets
                        for target, amount in record_allocation["allocations"].items():
                            scope = record_allocation.get("scope", "unknown")
                            allocation_results["allocation_breakdown"][scope][target] += amount
                    else:
                        allocation_results["unallocated_costs"] += cost_amount
                        allocation_results["unallocated_resources"].append({
                            "resource_id": cost_record.get("resource_id"),
                            "cost": cost_amount,
                            "reason": record_allocation.get("reason", "unknown")
                        })
                    
                    # Track rule applications
                    if record_allocation.get("applied_rule"):
                        allocation_results["rule_applications"].append({
                            "resource_id": cost_record.get("resource_id"),
                            "rule_id": record_allocation["applied_rule"],
                            "method": record_allocation.get("method"),
                            "allocated_amount": cost_amount
                        })
                
                except Exception as e:
                    logger.error(f"Error allocating cost for resource {cost_record.get('resource_id')}: {e}")
                    allocation_results["unallocated_costs"] += cost_record.get("cost", 0.0)
                    continue
            
            # Generate hierarchical rollup
            hierarchical_allocation = self._generate_hierarchical_rollup(
                allocation_results["allocation_breakdown"]
            )
            
            # Calculate allocation metrics
            allocation_percentage = (
                (allocation_results["allocated_costs"] / allocation_results["total_costs"] * 100)
                if allocation_results["total_costs"] > 0 else 0
            )
            
            # Update processing summary
            allocation_results.update({
                "hierarchical_allocation": hierarchical_allocation,
                "allocation_percentage": allocation_percentage,
                "processing_summary": {
                    "total_records_processed": len(cost_data),
                    "successfully_allocated": len(allocation_results["rule_applications"]),
                    "unallocated_records": len(allocation_results["unallocated_resources"]),
                    "allocation_efficiency": allocation_percentage,
                    "processing_timestamp": datetime.now(timezone.utc).isoformat()
                }
            })
            
            # Store allocation history (even in dry_run for testing/demo purposes)
            self.allocation_history.append(allocation_results)
            
            logger.info(f"Cost allocation completed: {allocation_percentage:.1f}% allocated")
            logger.info(f"Total allocated: ${allocation_results['allocated_costs']:,.2f}")
            logger.info(f"Unallocated: ${allocation_results['unallocated_costs']:,.2f}")
            
            return allocation_results
            
        except Exception as e:
            logger.error(f"Error in cost allocation for period {allocation_period}: {str(e)}")
            raise
    def analyze_usage_patterns(
        self,
        historical_cost_data: List[Dict[str, Any]],
        analysis_period_months: int = 6
    ) -> Dict[str, Any]:
        """
        Analyze usage patterns for automatic cost distribution.
        
        Args:
            historical_cost_data: Historical cost data with resource metadata
            analysis_period_months: Number of months to analyze
            
        Returns:
            Dict containing usage pattern analysis and recommendations
        """
        try:
            logger.info(f"Analyzing usage patterns for {len(historical_cost_data)} records")
            
            # Group data by resource attributes for pattern analysis
            pattern_analysis = {
                "tag_patterns": defaultdict(lambda: defaultdict(float)),
                "service_patterns": defaultdict(float),
                "region_patterns": defaultdict(float),
                "time_patterns": defaultdict(lambda: defaultdict(float)),
                "cost_distribution": {},
                "allocation_recommendations": []
            }
            
            total_cost = 0.0
            
            # Analyze patterns in historical data
            for record in historical_cost_data:
                cost = record.get("cost", 0.0)
                total_cost += cost
                
                # Analyze tag patterns
                tags = record.get("tags", {})
                for tag_key, tag_value in tags.items():
                    pattern_analysis["tag_patterns"][tag_key][tag_value] += cost
                
                # Analyze service patterns
                service = record.get("service", "unknown")
                pattern_analysis["service_patterns"][service] += cost
                
                # Analyze region patterns
                region = record.get("region", "unknown")
                pattern_analysis["region_patterns"][region] += cost
                
                # Analyze time patterns
                timestamp = record.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        month_key = dt.strftime("%Y-%m")
                        pattern_analysis["time_patterns"][month_key][service] += cost
                    except:
                        continue
            
            # Calculate cost distribution percentages
            if total_cost > 0:
                pattern_analysis["cost_distribution"] = {
                    "by_service": {
                        service: (cost / total_cost * 100)
                        for service, cost in pattern_analysis["service_patterns"].items()
                    },
                    "by_region": {
                        region: (cost / total_cost * 100)
                        for region, cost in pattern_analysis["region_patterns"].items()
                    },
                    "by_tags": {}
                }
                
                # Calculate tag-based distribution
                for tag_key, tag_values in pattern_analysis["tag_patterns"].items():
                    pattern_analysis["cost_distribution"]["by_tags"][tag_key] = {
                        tag_value: (cost / total_cost * 100)
                        for tag_value, cost in tag_values.items()
                    }
            
            # Generate allocation recommendations based on patterns
            recommendations = self._generate_pattern_based_recommendations(
                pattern_analysis, total_cost
            )
            pattern_analysis["allocation_recommendations"] = recommendations
            
            # Store learned patterns for future use
            if self.default_config["enable_usage_pattern_learning"]:
                self.usage_patterns[f"analysis_{datetime.now(timezone.utc).strftime('%Y%m%d')}"] = {
                    "patterns": pattern_analysis,
                    "total_cost": total_cost,
                    "analysis_period": analysis_period_months,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            
            logger.info(f"Usage pattern analysis completed for ${total_cost:,.2f} in costs")
            
            return pattern_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing usage patterns: {str(e)}")
            raise

    def setup_hierarchical_structure(
        self,
        organizational_hierarchy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Set up hierarchical structure for cost rollup.
        
        Args:
            organizational_hierarchy: Organizational structure definition
            
        Returns:
            Dict containing configured hierarchy and validation results
        """
        try:
            logger.info("Setting up hierarchical cost allocation structure")
            
            # Validate hierarchy structure
            validation_result = self._validate_hierarchy_structure(organizational_hierarchy)
            if not validation_result["is_valid"]:
                raise ValueError(f"Invalid hierarchy structure: {validation_result['errors']}")
            
            # Store hierarchy configuration
            self.hierarchical_structure = {
                "structure": organizational_hierarchy,
                "validation": validation_result,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "rollup_paths": self._generate_rollup_paths(organizational_hierarchy)
            }
            
            logger.info("Hierarchical structure configured successfully")
            
            return self.hierarchical_structure
            
        except Exception as e:
            logger.error(f"Error setting up hierarchical structure: {str(e)}")
            raise

    def validate_allocation_rules(
        self,
        rule_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate allocation rules and detect conflicts.
        
        Args:
            rule_ids: Optional list of specific rule IDs to validate
            
        Returns:
            Dict containing validation results and conflict analysis
        """
        try:
            rules_to_validate = rule_ids or list(self.allocation_rules.keys())
            logger.info(f"Validating {len(rules_to_validate)} allocation rules")
            
            validation_results = {
                "total_rules": len(rules_to_validate),
                "valid_rules": 0,
                "invalid_rules": 0,
                "rule_validations": {},
                "detected_conflicts": [],
                "recommendations": []
            }
            
            # Validate each rule
            for rule_id in rules_to_validate:
                if rule_id not in self.allocation_rules:
                    logger.warning(f"Rule {rule_id} not found")
                    continue
                
                rule_config = self.allocation_rules[rule_id]
                
                # Create rule object for validation
                rule = AllocationRule(
                    rule_id=rule_id,
                    name=rule_config["name"],
                    method=AllocationMethod(rule_config["method"]),
                    scope=AllocationScope(rule_config["scope"]),
                    priority=rule_config["priority"],
                    conditions=rule_config.get("conditions"),
                    allocation_targets=rule_config.get("allocation_targets")
                )
                
                # Validate rule
                rule_validation = self._validate_allocation_rule(rule)
                validation_results["rule_validations"][rule_id] = rule_validation
                
                if rule_validation["is_valid"]:
                    validation_results["valid_rules"] += 1
                else:
                    validation_results["invalid_rules"] += 1
                
                # Check for conflicts with other rules
                conflicts = self._detect_rule_conflicts(rule)
                if conflicts:
                    validation_results["detected_conflicts"].extend(conflicts)
            
            # Generate recommendations for improvements
            recommendations = self._generate_rule_recommendations(validation_results)
            validation_results["recommendations"] = recommendations
            
            logger.info(f"Rule validation completed: {validation_results['valid_rules']} valid, {validation_results['invalid_rules']} invalid")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating allocation rules: {str(e)}")
            raise

    def resolve_allocation_conflicts(
        self,
        conflicts: List[Dict[str, Any]],
        resolution_strategy: str = "highest_priority"
    ) -> Dict[str, Any]:
        """
        Resolve conflicts between allocation rules.
        
        Args:
            conflicts: List of detected conflicts
            resolution_strategy: Strategy for resolving conflicts
            
        Returns:
            Dict containing conflict resolution results
        """
        try:
            logger.info(f"Resolving {len(conflicts)} allocation conflicts using {resolution_strategy}")
            
            resolution_results = {
                "total_conflicts": len(conflicts),
                "resolved_conflicts": 0,
                "unresolved_conflicts": 0,
                "resolution_actions": [],
                "updated_rules": []
            }
            
            for conflict in conflicts:
                try:
                    resolution_action = self._resolve_single_conflict(
                        conflict, resolution_strategy
                    )
                    
                    if resolution_action["resolved"]:
                        resolution_results["resolved_conflicts"] += 1
                        resolution_results["resolution_actions"].append(resolution_action)
                        
                        # Apply resolution if not in dry_run mode
                        if not self.dry_run and resolution_action.get("rule_updates"):
                            for rule_id, updates in resolution_action["rule_updates"].items():
                                if rule_id in self.allocation_rules:
                                    self.allocation_rules[rule_id].update(updates)
                                    resolution_results["updated_rules"].append(rule_id)
                    else:
                        resolution_results["unresolved_conflicts"] += 1
                
                except Exception as e:
                    logger.error(f"Error resolving conflict: {e}")
                    resolution_results["unresolved_conflicts"] += 1
                    continue
            
            logger.info(f"Conflict resolution completed: {resolution_results['resolved_conflicts']} resolved")
            
            return resolution_results
            
        except Exception as e:
            logger.error(f"Error resolving allocation conflicts: {str(e)}")
            raise

    def generate_allocation_report(
        self,
        period: str,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive allocation report for a period.
        
        Args:
            period: Period identifier (e.g., "2024-01")
            include_details: Whether to include detailed breakdowns
            
        Returns:
            Dict containing comprehensive allocation report
        """
        try:
            logger.info(f"Generating allocation report for period {period}")
            
            # Find allocation data for the period
            period_allocation = None
            for allocation in self.allocation_history:
                if allocation.get("period") == period:
                    period_allocation = allocation
                    break
            
            if not period_allocation:
                logger.warning(f"No allocation data found for period {period}")
                return {"error": f"No allocation data found for period {period}"}
            
            # Generate comprehensive report
            report = {
                "period": period,
                "report_generated_at": datetime.now(timezone.utc).isoformat(),
                "executive_summary": self._generate_executive_summary(period_allocation),
                "allocation_metrics": self._calculate_allocation_metrics(period_allocation),
                "cost_breakdown": period_allocation.get("allocation_breakdown", {}),
                "hierarchical_view": period_allocation.get("hierarchical_allocation", {}),
                "unallocated_analysis": self._analyze_unallocated_costs(period_allocation),
                "rule_performance": self._analyze_rule_performance(period_allocation),
                "recommendations": self._generate_allocation_recommendations(period_allocation)
            }
            
            # Add detailed breakdowns if requested
            if include_details:
                report["detailed_breakdowns"] = {
                    "by_service": self._generate_service_breakdown(period_allocation),
                    "by_region": self._generate_region_breakdown(period_allocation),
                    "by_team": self._generate_team_breakdown(period_allocation),
                    "by_project": self._generate_project_breakdown(period_allocation)
                }
            
            logger.info(f"Allocation report generated for period {period}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating allocation report: {str(e)}")
            raise
    # Helper methods for internal operations

    def _allocate_single_cost_record(
        self,
        cost_record: Dict[str, Any],
        allocation_period: str
    ) -> Dict[str, Any]:
        """Allocate a single cost record using applicable rules."""
        resource_id = cost_record.get("resource_id", "unknown")
        cost_amount = cost_record.get("cost", 0.0)
        
        # Skip if cost is below minimum threshold
        if cost_amount < self.default_config["minimum_allocation_threshold"]:
            return {
                "allocated": False,
                "reason": "below_minimum_threshold",
                "allocations": {}
            }
        
        # Find applicable rules (sorted by priority)
        applicable_rules = self._find_applicable_rules(cost_record)
        
        if not applicable_rules:
            # Apply fallback strategy
            return self._apply_fallback_allocation(cost_record)
        
        # Apply highest priority rule
        primary_rule = applicable_rules[0]
        allocation_result = self._apply_allocation_rule(cost_record, primary_rule)
        
        return allocation_result

    def _find_applicable_rules(self, cost_record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find rules applicable to a cost record."""
        applicable_rules = []
        
        for rule_id, rule_config in self.allocation_rules.items():
            if not rule_config.get("is_active", True):
                continue
            
            # Check if rule conditions are met
            if self._evaluate_rule_conditions(cost_record, rule_config):
                applicable_rules.append(rule_config)
        
        # Sort by priority (lower number = higher priority)
        applicable_rules.sort(key=lambda r: r.get("priority", 100))
        
        return applicable_rules

    def _evaluate_rule_conditions(
        self, cost_record: Dict[str, Any], rule_config: Dict[str, Any]
    ) -> bool:
        """Evaluate if rule conditions are met for a cost record."""
        conditions = rule_config.get("conditions", {})
        
        if not conditions:
            return True  # No conditions means rule applies to all
        
        # Check tag conditions
        tag_conditions = conditions.get("tags", {})
        if tag_conditions:
            record_tags = cost_record.get("tags", {})
            for tag_key, expected_values in tag_conditions.items():
                if isinstance(expected_values, str):
                    expected_values = [expected_values]
                
                record_value = record_tags.get(tag_key)
                if record_value not in expected_values:
                    return False
        
        # Check service conditions
        service_conditions = conditions.get("services", [])
        if service_conditions:
            record_service = cost_record.get("service", "")
            if record_service not in service_conditions:
                return False
        
        # Check region conditions
        region_conditions = conditions.get("regions", [])
        if region_conditions:
            record_region = cost_record.get("region", "")
            if record_region not in region_conditions:
                return False
        
        # Check cost threshold conditions
        cost_conditions = conditions.get("cost_thresholds", {})
        if cost_conditions:
            record_cost = cost_record.get("cost", 0.0)
            min_cost = cost_conditions.get("min", 0.0)
            max_cost = cost_conditions.get("max", float('inf'))
            
            if not (min_cost <= record_cost <= max_cost):
                return False
        
        return True

    def _apply_allocation_rule(
        self, cost_record: Dict[str, Any], rule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a specific allocation rule to a cost record."""
        method = AllocationMethod(rule_config["method"])
        cost_amount = cost_record.get("cost", 0.0)
        
        if method == AllocationMethod.TAG_BASED:
            return self._apply_tag_based_allocation(cost_record, rule_config)
        elif method == AllocationMethod.USAGE_PATTERN:
            return self._apply_usage_pattern_allocation(cost_record, rule_config)
        elif method == AllocationMethod.EQUAL_SPLIT:
            return self._apply_equal_split_allocation(cost_record, rule_config)
        elif method == AllocationMethod.PROPORTIONAL:
            return self._apply_proportional_allocation(cost_record, rule_config)
        elif method == AllocationMethod.CUSTOM_RULE:
            return self._apply_custom_rule_allocation(cost_record, rule_config)
        else:
            return {
                "allocated": False,
                "reason": f"unsupported_method_{method.value}",
                "allocations": {}
            }

    def _apply_tag_based_allocation(
        self, cost_record: Dict[str, Any], rule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply tag-based allocation logic."""
        tags = cost_record.get("tags", {})
        cost_amount = cost_record.get("cost", 0.0)
        
        # Check primary allocation tags in order of preference
        for tag_key in self.default_config["primary_allocation_tags"]:
            if tag_key in tags:
                tag_value = tags[tag_key]
                
                # Apply tag mappings if configured
                mapped_value = self.tag_mappings.get(tag_key, {}).get(tag_value, tag_value)
                
                return {
                    "allocated": True,
                    "method": "tag_based",
                    "applied_rule": rule_config["rule_id"],
                    "scope": rule_config["scope"],
                    "allocation_key": tag_key,
                    "allocation_value": mapped_value,
                    "allocations": {mapped_value: cost_amount}
                }
        
        # No suitable tags found
        return {
            "allocated": False,
            "reason": "no_allocation_tags",
            "allocations": {}
        }

    def _apply_usage_pattern_allocation(
        self, cost_record: Dict[str, Any], rule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply usage pattern-based allocation."""
        # Use learned patterns to allocate costs
        service = cost_record.get("service", "unknown")
        region = cost_record.get("region", "unknown")
        cost_amount = cost_record.get("cost", 0.0)
        
        # Find matching usage patterns
        matching_patterns = self._find_matching_usage_patterns(cost_record)
        
        if matching_patterns:
            # Use the most recent pattern
            pattern = matching_patterns[0]
            allocation_distribution = pattern.get("allocation_distribution", {})
            
            allocations = {}
            for target, percentage in allocation_distribution.items():
                allocations[target] = cost_amount * (percentage / 100)
            
            return {
                "allocated": True,
                "method": "usage_pattern",
                "applied_rule": rule_config["rule_id"],
                "scope": rule_config["scope"],
                "pattern_used": pattern.get("pattern_id"),
                "allocations": allocations
            }
        
        return {
            "allocated": False,
            "reason": "no_matching_patterns",
            "allocations": {}
        }

    def _apply_equal_split_allocation(
        self, cost_record: Dict[str, Any], rule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply equal split allocation among targets."""
        allocation_targets = rule_config.get("allocation_targets", {})
        cost_amount = cost_record.get("cost", 0.0)
        
        if not allocation_targets:
            return {
                "allocated": False,
                "reason": "no_allocation_targets",
                "allocations": {}
            }
        
        # Split equally among all targets
        num_targets = len(allocation_targets)
        amount_per_target = cost_amount / num_targets
        
        allocations = {}
        for target in allocation_targets.keys():
            allocations[target] = amount_per_target
        
        return {
            "allocated": True,
            "method": "equal_split",
            "applied_rule": rule_config["rule_id"],
            "scope": rule_config["scope"],
            "allocations": allocations
        }

    def _apply_proportional_allocation(
        self, cost_record: Dict[str, Any], rule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply proportional allocation based on configured percentages."""
        allocation_targets = rule_config.get("allocation_targets", {})
        cost_amount = cost_record.get("cost", 0.0)
        
        if not allocation_targets:
            return {
                "allocated": False,
                "reason": "no_allocation_targets",
                "allocations": {}
            }
        
        # Normalize percentages to ensure they sum to 100%
        total_percentage = sum(allocation_targets.values())
        if total_percentage == 0:
            return self._apply_equal_split_allocation(cost_record, rule_config)
        
        allocations = {}
        for target, percentage in allocation_targets.items():
            normalized_percentage = percentage / total_percentage
            allocations[target] = cost_amount * normalized_percentage
        
        return {
            "allocated": True,
            "method": "proportional",
            "applied_rule": rule_config["rule_id"],
            "scope": rule_config["scope"],
            "allocations": allocations
        }

    def _apply_custom_rule_allocation(
        self, cost_record: Dict[str, Any], rule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply custom allocation rule logic."""
        # Placeholder for custom rule implementation
        # In practice, this would execute custom allocation logic
        return {
            "allocated": False,
            "reason": "custom_rule_not_implemented",
            "allocations": {}
        }

    def _apply_fallback_allocation(self, cost_record: Dict[str, Any]) -> Dict[str, Any]:
        """Apply fallback allocation strategy for unmatched resources."""
        fallback_strategy = self.default_config["fallback_strategy"]
        cost_amount = cost_record.get("cost", 0.0)
        
        if fallback_strategy == FallbackStrategy.UNALLOCATED_POOL:
            return {
                "allocated": False,
                "reason": "moved_to_unallocated_pool",
                "allocations": {}
            }
        elif fallback_strategy == FallbackStrategy.DEFAULT_ALLOCATION:
            return {
                "allocated": True,
                "method": "fallback_default",
                "scope": "organization",
                "allocations": {"unallocated": cost_amount}
            }
        else:
            return {
                "allocated": False,
                "reason": f"fallback_strategy_{fallback_strategy.value}",
                "allocations": {}
            }

    def _generate_hierarchical_rollup(
        self, allocation_breakdown: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """Generate hierarchical cost rollup."""
        if not self.hierarchical_structure:
            return {"error": "No hierarchical structure configured"}
        
        rollup = {}
        structure = self.hierarchical_structure.get("structure", {})
        
        # Implement hierarchical rollup logic based on organizational structure
        # This is a simplified implementation
        for scope, allocations in allocation_breakdown.items():
            rollup[scope] = {
                "direct_allocations": allocations,
                "total": sum(allocations.values()),
                "rollup_path": self._get_rollup_path(scope)
            }
        
        return rollup

    def _get_rollup_path(self, scope: str) -> List[str]:
        """Get hierarchical rollup path for a scope."""
        rollup_paths = self.hierarchical_structure.get("rollup_paths", {})
        return rollup_paths.get(scope, [scope])

    def _validate_allocation_rule(self, rule: AllocationRule) -> Dict[str, Any]:
        """Validate an allocation rule configuration."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate rule ID
        if not rule.rule_id or not isinstance(rule.rule_id, str):
            validation_result["errors"].append("Rule ID must be a non-empty string")
        
        # Validate allocation targets for methods that require them
        if rule.method in [AllocationMethod.PROPORTIONAL, AllocationMethod.EQUAL_SPLIT]:
            if not rule.allocation_targets:
                validation_result["errors"].append(f"Method {rule.method.value} requires allocation targets")
        
        # Validate proportional percentages
        if rule.method == AllocationMethod.PROPORTIONAL and rule.allocation_targets:
            total_percentage = sum(rule.allocation_targets.values())
            if abs(total_percentage - 100.0) > 0.01:  # Allow small floating point errors
                validation_result["warnings"].append(
                    f"Proportional allocation percentages sum to {total_percentage}%, not 100%"
                )
        
        # Set validation status
        validation_result["is_valid"] = len(validation_result["errors"]) == 0
        
        return validation_result

    def _detect_rule_conflicts(self, rule: AllocationRule) -> List[Dict[str, Any]]:
        """Detect conflicts between allocation rules."""
        conflicts = []
        
        for existing_rule_id, existing_rule_config in self.allocation_rules.items():
            if existing_rule_id == rule.rule_id:
                continue
            
            # Check for overlapping conditions and same priority
            if (existing_rule_config.get("priority") == rule.priority and
                self._rules_have_overlapping_conditions(rule, existing_rule_config)):
                
                conflicts.append({
                    "type": "priority_conflict",
                    "rule1": rule.rule_id,
                    "rule2": existing_rule_id,
                    "description": f"Rules have same priority ({rule.priority}) and overlapping conditions"
                })
        
        return conflicts

    def _rules_have_overlapping_conditions(
        self, rule: AllocationRule, existing_rule_config: Dict[str, Any]
    ) -> bool:
        """Check if two rules have overlapping conditions."""
        # Simplified overlap detection - in practice would be more sophisticated
        rule_conditions = rule.conditions or {}
        existing_conditions = existing_rule_config.get("conditions", {})
        
        # If either rule has no conditions, they overlap (apply to everything)
        if not rule_conditions or not existing_conditions:
            return True
        
        # Check for overlapping tag conditions
        rule_tags = rule_conditions.get("tags", {})
        existing_tags = existing_conditions.get("tags", {})
        
        if rule_tags and existing_tags:
            for tag_key in rule_tags.keys():
                if tag_key in existing_tags:
                    rule_values = set(rule_tags[tag_key] if isinstance(rule_tags[tag_key], list) else [rule_tags[tag_key]])
                    existing_values = set(existing_tags[tag_key] if isinstance(existing_tags[tag_key], list) else [existing_tags[tag_key]])
                    
                    if rule_values.intersection(existing_values):
                        return True
        
        return False

    def _generate_pattern_based_recommendations(
        self, pattern_analysis: Dict[str, Any], total_cost: float
    ) -> List[Dict[str, Any]]:
        """Generate allocation recommendations based on usage patterns."""
        recommendations = []
        
        # Analyze tag patterns for potential allocation rules
        tag_patterns = pattern_analysis.get("tag_patterns", {})
        
        for tag_key, tag_values in tag_patterns.items():
            if tag_key in self.default_config["primary_allocation_tags"]:
                total_tag_cost = sum(tag_values.values())
                tag_coverage = (total_tag_cost / total_cost * 100) if total_cost > 0 else 0
                
                if tag_coverage > 70:  # High coverage threshold
                    recommendations.append({
                        "type": "create_tag_based_rule",
                        "tag_key": tag_key,
                        "coverage_percentage": tag_coverage,
                        "estimated_allocation": total_tag_cost,
                        "priority": "high",
                        "description": f"Create tag-based allocation rule for {tag_key} (covers {tag_coverage:.1f}% of costs)"
                    })
        
        return recommendations

    def _validate_hierarchy_structure(self, hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """Validate organizational hierarchy structure."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Basic structure validation
        if not isinstance(hierarchy, dict):
            validation_result["errors"].append("Hierarchy must be a dictionary")
            validation_result["is_valid"] = False
            return validation_result
        
        # Check for required fields
        required_fields = ["organization", "levels"]
        for field in required_fields:
            if field not in hierarchy:
                validation_result["errors"].append(f"Missing required field: {field}")
        
        validation_result["is_valid"] = len(validation_result["errors"]) == 0
        
        return validation_result

    def _generate_rollup_paths(self, hierarchy: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate rollup paths for hierarchical structure."""
        rollup_paths = {}
        
        # Simplified rollup path generation
        levels = hierarchy.get("levels", [])
        
        for i, level in enumerate(levels):
            path = levels[:i+1]
            rollup_paths[level] = path
        
        return rollup_paths

    def get_allocation_summary(self) -> Dict[str, Any]:
        """Get summary of allocation engine status and configuration."""
        return {
            "total_rules": len(self.allocation_rules),
            "active_rules": sum(1 for rule in self.allocation_rules.values() if rule.get("is_active", True)),
            "allocation_history_records": len(self.allocation_history),
            "unallocated_cost_pools": len(self.unallocated_costs),
            "detected_conflicts": len(self.allocation_conflicts),
            "hierarchical_structure_configured": bool(self.hierarchical_structure),
            "usage_patterns_learned": len(self.usage_patterns),
            "configuration": self.default_config,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    # Additional helper methods for reporting and analysis

    def _resolve_single_conflict(
        self, conflict: Dict[str, Any], resolution_strategy: str
    ) -> Dict[str, Any]:
        """Resolve a single rule conflict."""
        if resolution_strategy == "highest_priority":
            # Keep rule with highest priority (lowest number)
            rule1_id = conflict.get("rule1")
            rule2_id = conflict.get("rule2")
            
            if rule1_id in self.allocation_rules and rule2_id in self.allocation_rules:
                rule1_priority = self.allocation_rules[rule1_id].get("priority", 100)
                rule2_priority = self.allocation_rules[rule2_id].get("priority", 100)
                
                if rule1_priority < rule2_priority:
                    # Deactivate rule2
                    return {
                        "resolved": True,
                        "action": "deactivate_lower_priority",
                        "deactivated_rule": rule2_id,
                        "rule_updates": {rule2_id: {"is_active": False}}
                    }
                else:
                    # Deactivate rule1
                    return {
                        "resolved": True,
                        "action": "deactivate_lower_priority",
                        "deactivated_rule": rule1_id,
                        "rule_updates": {rule1_id: {"is_active": False}}
                    }
        
        return {"resolved": False, "reason": "unsupported_resolution_strategy"}

    def _find_matching_usage_patterns(self, cost_record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find usage patterns that match a cost record."""
        matching_patterns = []
        
        service = cost_record.get("service", "")
        region = cost_record.get("region", "")
        
        for pattern_id, pattern_data in self.usage_patterns.items():
            patterns = pattern_data.get("patterns", {})
            
            # Check if service matches pattern
            service_patterns = patterns.get("service_patterns", {})
            if service in service_patterns:
                matching_patterns.append({
                    "pattern_id": pattern_id,
                    "match_score": service_patterns[service],
                    "allocation_distribution": self._calculate_pattern_distribution(patterns, service)
                })
        
        # Sort by match score (descending)
        matching_patterns.sort(key=lambda p: p.get("match_score", 0), reverse=True)
        
        return matching_patterns

    def _calculate_pattern_distribution(
        self, patterns: Dict[str, Any], service: str
    ) -> Dict[str, float]:
        """Calculate allocation distribution based on patterns."""
        # Simplified pattern-based distribution calculation
        tag_patterns = patterns.get("tag_patterns", {})
        
        distribution = {}
        for tag_key in self.default_config["primary_allocation_tags"]:
            if tag_key in tag_patterns:
                tag_values = tag_patterns[tag_key]
                total_cost = sum(tag_values.values())
                
                for tag_value, cost in tag_values.items():
                    percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                    if percentage > 5:  # Only include significant allocations
                        distribution[tag_value] = percentage
        
        return distribution

    def _generate_executive_summary(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of allocation results."""
        total_costs = allocation_data.get("total_costs", 0.0)
        allocated_costs = allocation_data.get("allocated_costs", 0.0)
        allocation_percentage = (allocated_costs / total_costs * 100) if total_costs > 0 else 0
        
        return {
            "total_costs": total_costs,
            "allocated_costs": allocated_costs,
            "unallocated_costs": allocation_data.get("unallocated_costs", 0.0),
            "allocation_efficiency": allocation_percentage,
            "total_resources_processed": len(allocation_data.get("rule_applications", [])),
            "allocation_quality": "excellent" if allocation_percentage > 90 else "good" if allocation_percentage > 75 else "needs_improvement"
        }

    def _calculate_allocation_metrics(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed allocation metrics."""
        rule_applications = allocation_data.get("rule_applications", [])
        
        # Calculate rule usage statistics
        rule_usage = defaultdict(int)
        for application in rule_applications:
            rule_id = application.get("rule_id")
            if rule_id:
                rule_usage[rule_id] += 1
        
        return {
            "total_rule_applications": len(rule_applications),
            "unique_rules_used": len(rule_usage),
            "most_used_rule": max(rule_usage.items(), key=lambda x: x[1]) if rule_usage else None,
            "rule_usage_distribution": dict(rule_usage),
            "average_allocations_per_rule": len(rule_applications) / len(rule_usage) if rule_usage else 0
        }

    def _analyze_unallocated_costs(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze unallocated costs and reasons."""
        unallocated_resources = allocation_data.get("unallocated_resources", [])
        
        # Group by reason
        reasons = defaultdict(lambda: {"count": 0, "total_cost": 0.0})
        
        for resource in unallocated_resources:
            reason = resource.get("reason", "unknown")
            cost = resource.get("cost", 0.0)
            
            reasons[reason]["count"] += 1
            reasons[reason]["total_cost"] += cost
        
        return {
            "total_unallocated_resources": len(unallocated_resources),
            "total_unallocated_cost": sum(r.get("cost", 0.0) for r in unallocated_resources),
            "unallocation_reasons": dict(reasons),
            "top_unallocation_reason": max(reasons.items(), key=lambda x: x[1]["total_cost"]) if reasons else None
        }

    def _analyze_rule_performance(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance of allocation rules."""
        rule_applications = allocation_data.get("rule_applications", [])
        
        # Calculate performance metrics per rule
        rule_performance = defaultdict(lambda: {
            "applications": 0,
            "total_allocated": 0.0,
            "average_allocation": 0.0
        })
        
        for application in rule_applications:
            rule_id = application.get("rule_id")
            allocated_amount = application.get("allocated_amount", 0.0)
            
            if rule_id:
                rule_performance[rule_id]["applications"] += 1
                rule_performance[rule_id]["total_allocated"] += allocated_amount
        
        # Calculate averages
        for rule_id, metrics in rule_performance.items():
            if metrics["applications"] > 0:
                metrics["average_allocation"] = metrics["total_allocated"] / metrics["applications"]
        
        return dict(rule_performance)

    def _generate_allocation_recommendations(self, allocation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for improving allocation."""
        recommendations = []
        
        allocation_percentage = allocation_data.get("processing_summary", {}).get("allocation_efficiency", 0)
        
        if allocation_percentage < 75:
            recommendations.append({
                "type": "improve_allocation_coverage",
                "priority": "high",
                "description": f"Allocation efficiency is {allocation_percentage:.1f}%. Consider adding more allocation rules.",
                "suggested_actions": [
                    "Review unallocated resources for common patterns",
                    "Create additional tag-based allocation rules",
                    "Implement usage pattern-based allocation"
                ]
            })
        
        unallocated_analysis = self._analyze_unallocated_costs(allocation_data)
        if unallocated_analysis["total_unallocated_resources"] > 0:
            recommendations.append({
                "type": "address_unallocated_costs",
                "priority": "medium",
                "description": f"{unallocated_analysis['total_unallocated_resources']} resources remain unallocated",
                "suggested_actions": [
                    "Review tagging strategy for unallocated resources",
                    "Implement fallback allocation rules",
                    "Consider default allocation for untagged resources"
                ]
            })
        
        return recommendations

    def _generate_service_breakdown(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed service breakdown."""
        # Placeholder implementation - would analyze allocation by service
        return {"placeholder": "service_breakdown_not_implemented"}

    def _generate_region_breakdown(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed region breakdown."""
        # Placeholder implementation - would analyze allocation by region
        return {"placeholder": "region_breakdown_not_implemented"}

    def _generate_team_breakdown(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed team breakdown."""
        # Placeholder implementation - would analyze allocation by team
        return {"placeholder": "team_breakdown_not_implemented"}

    def _generate_project_breakdown(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed project breakdown."""
        # Placeholder implementation - would analyze allocation by project
        return {"placeholder": "project_breakdown_not_implemented"}

    def _generate_rule_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for rule improvements."""
        recommendations = []
        
        if validation_results["invalid_rules"] > 0:
            recommendations.append("Fix invalid allocation rules before proceeding")
        
        if validation_results["detected_conflicts"]:
            recommendations.append("Resolve rule conflicts to ensure consistent allocation")
        
        if validation_results["valid_rules"] == 0:
            recommendations.append("Create allocation rules to enable automatic cost distribution")
        
        return recommendations