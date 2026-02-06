#!/usr/bin/env python3
"""
Pricing Intelligence Engine for Advanced FinOps Platform

Analyzes pricing strategies and recommends cost-effective alternatives:
- Reserved Instance recommendations based on historical utilization
- Spot Instance opportunity detection and savings calculation
- Savings Plans analysis with ROI calculations
- Regional pricing comparison and cost-effective alternatives

Requirements: 2.1, 2.2, 2.3, 2.4
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import json

logger = logging.getLogger(__name__)


class PricingStrategy(Enum):
    """Types of pricing strategies."""
    RESERVED_INSTANCE = "reserved_instance"
    SPOT_INSTANCE = "spot_instance"
    SAVINGS_PLAN = "savings_plan"
    REGIONAL_OPTIMIZATION = "regional_optimization"
    ON_DEMAND = "on_demand"


class ReservationTerm(Enum):
    """Reserved Instance and Savings Plan terms."""
    ONE_YEAR = "1_year"
    THREE_YEAR = "3_year"


class PaymentOption(Enum):
    """Payment options for Reserved Instances and Savings Plans."""
    NO_UPFRONT = "no_upfront"
    PARTIAL_UPFRONT = "partial_upfront"
    ALL_UPFRONT = "all_upfront"


class PricingIntelligenceEngine:
    """
    Pricing intelligence engine that analyzes pricing strategies and recommends
    cost-effective alternatives including Reserved Instances, Spot Instances,
    and Savings Plans with ROI calculations.
    """
    
    def __init__(self, aws_config, region: str = 'us-east-1'):
        """
        Initialize pricing intelligence engine.
        
        Args:
            aws_config: AWSConfig instance for client management
            region: AWS region for pricing analysis
        """
        self.aws_config = aws_config
        self.region = region
        self.pricing_thresholds = self._initialize_pricing_thresholds()
        self.regional_pricing_cache = {}
        
        # Initialize cost calculator for accurate pricing data
        try:
            from utils.cost_calculator import CostCalculator, Currency
            self.cost_calculator = CostCalculator(aws_config, Currency.USD)
        except Exception as e:
            logger.warning(f"Could not initialize cost calculator: {e}")
            self.cost_calculator = None
        
        logger.info(f"Pricing Intelligence Engine initialized for region {region}")
        logger.info("Integrated with Cost Calculator for accurate pricing data")
    
    def _initialize_pricing_thresholds(self) -> Dict[str, Any]:
        """
        Initialize pricing analysis thresholds and parameters.
        
        Returns:
            Dictionary of pricing thresholds and parameters
        """
        return {
            'reserved_instance': {
                'min_utilization_threshold': 70.0,  # % utilization to recommend RI
                'min_runtime_hours_monthly': 500,   # Minimum hours per month
                'min_historical_months': 3,         # Minimum months of data
                'break_even_months': 12,            # Months to break even
                'confidence_threshold': 80.0        # % confidence for recommendation
            },
            'spot_instance': {
                'max_interruption_tolerance': 10.0,  # % acceptable interruption rate
                'min_savings_threshold': 50.0,       # % minimum savings to recommend
                'workload_stability_days': 7,        # Days of stable usage pattern
                'fault_tolerance_required': True     # Workload must be fault tolerant
            },
            'savings_plan': {
                'min_compute_spend_monthly': 100.0,  # $ minimum monthly compute spend
                'min_utilization_threshold': 60.0,   # % utilization to recommend SP
                'min_historical_months': 6,          # Minimum months of data
                'coverage_target': 80.0              # % target coverage
            },
            'regional_optimization': {
                'min_cost_difference': 15.0,         # % minimum cost difference
                'data_transfer_cost_factor': 0.09,   # $/GB data transfer cost
                'latency_penalty_factor': 1.1,      # Multiplier for latency concerns
                'compliance_regions': ['us-east-1', 'us-west-2', 'eu-west-1']
            }
        }
    
    def analyze_pricing_opportunities(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze all pricing opportunities for given resources.
        
        Args:
            resources: List of resources with utilization and cost data
            
        Returns:
            Comprehensive pricing analysis with recommendations
        """
        logger.info(f"Analyzing pricing opportunities for {len(resources)} resources")
        
        # Group resources by type for analysis
        resources_by_type = self._group_resources_by_type(resources)
        
        # Analyze each pricing strategy
        ri_recommendations = self._analyze_reserved_instances(resources_by_type.get('ec2', []))
        spot_recommendations = self._analyze_spot_opportunities(resources_by_type.get('ec2', []))
        sp_recommendations = self._analyze_savings_plans(resources)
        regional_recommendations = self._analyze_regional_optimization(resources)
        
        # Combine and prioritize recommendations
        all_recommendations = (
            ri_recommendations + 
            spot_recommendations + 
            sp_recommendations + 
            regional_recommendations
        )
        
        prioritized_recommendations = self._prioritize_pricing_recommendations(all_recommendations)
        
        # Generate comprehensive analysis
        analysis_summary = self._generate_pricing_analysis_summary(
            resources, all_recommendations, prioritized_recommendations
        )
        
        logger.info(f"Generated {len(all_recommendations)} pricing recommendations")
        
        return {
            'summary': analysis_summary,
            'recommendations': prioritized_recommendations,
            'reservedInstanceRecommendations': ri_recommendations,
            'spotInstanceRecommendations': spot_recommendations,
            'savingsPlansRecommendations': sp_recommendations,
            'regionalOptimizationRecommendations': regional_recommendations,
            'totalRecommendations': len(all_recommendations),
            'timestamp': datetime.utcnow().isoformat(),
            'region': self.region
        }
    
    def _group_resources_by_type(self, resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group resources by their type for targeted analysis."""
        grouped = {}
        
        for resource in resources:
            resource_type = resource.get('resourceType', 'unknown')
            if resource_type not in grouped:
                grouped[resource_type] = []
            grouped[resource_type].append(resource)
        
        return grouped
    
    def _analyze_reserved_instances(self, ec2_resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze Reserved Instance opportunities for EC2 instances.
        
        Requirements: 2.1 - Reserved Instance recommendations based on historical utilization
        """
        recommendations = []
        thresholds = self.pricing_thresholds['reserved_instance']
        
        # Group instances by type and analyze patterns
        instance_groups = self._group_instances_by_type(ec2_resources)
        
        for instance_type, instances in instance_groups.items():
            if len(instances) == 0:
                continue
            
            # Analyze utilization patterns
            utilization_analysis = self._analyze_instance_utilization_patterns(instances)
            
            if not utilization_analysis['sufficient_data']:
                continue
            
            avg_utilization = utilization_analysis['avg_utilization']
            monthly_runtime_hours = utilization_analysis['monthly_runtime_hours']
            confidence_score = utilization_analysis['confidence_score']
            
            # Check if RI recommendation criteria are met
            if (avg_utilization >= thresholds['min_utilization_threshold'] and
                monthly_runtime_hours >= thresholds['min_runtime_hours_monthly'] and
                confidence_score >= thresholds['confidence_threshold']):
                
                # Calculate RI savings for different terms and payment options
                ri_options = self._calculate_ri_savings(instance_type, instances, utilization_analysis)
                
                # Find best RI option
                best_option = max(ri_options, key=lambda x: x['total_savings'])
                
                recommendations.append(self._create_pricing_recommendation(
                    strategy=PricingStrategy.RESERVED_INSTANCE,
                    title=f"Purchase Reserved Instances for {instance_type}",
                    description=f"High utilization pattern detected: {avg_utilization:.1f}% avg utilization, {monthly_runtime_hours:.0f} hours/month",
                    affected_resources=instances,
                    current_monthly_cost=sum(inst.get('currentCost', 0) for inst in instances),
                    projected_monthly_cost=best_option['monthly_cost_with_ri'],
                    estimated_monthly_savings=best_option['monthly_savings'],
                    total_savings_over_term=best_option['total_savings'],
                    upfront_cost=best_option['upfront_cost'],
                    payback_period_months=best_option['payback_months'],
                    confidence_score=confidence_score,
                    risk_level="LOW",
                    implementation_details={
                        'instanceType': instance_type,
                        'recommendedQuantity': len(instances),
                        'term': best_option['term'],
                        'paymentOption': best_option['payment_option'],
                        'utilizationAnalysis': utilization_analysis,
                        'allRIOptions': ri_options
                    }
                ))
        
        return recommendations
    
    def _analyze_spot_opportunities(self, ec2_resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze Spot Instance opportunities for EC2 instances.
        
        Requirements: 2.2 - Spot Instance opportunity detection and savings calculation
        """
        recommendations = []
        thresholds = self.pricing_thresholds['spot_instance']
        
        for resource in ec2_resources:
            resource_id = resource.get('resourceId')
            instance_type = resource.get('instanceType', '')
            current_cost = resource.get('currentCost', 0)
            
            # Analyze workload characteristics
            workload_analysis = self._analyze_spot_suitability(resource)
            
            if not workload_analysis['suitable_for_spot']:
                continue
            
            # Calculate spot pricing and savings
            spot_pricing = self._get_spot_pricing_data(instance_type, self.region)
            
            if not spot_pricing:
                continue
            
            avg_spot_price = spot_pricing['avg_price']
            interruption_rate = spot_pricing['interruption_rate']
            potential_savings = spot_pricing['savings_percentage']
            
            # Check if spot recommendation criteria are met
            if (interruption_rate <= thresholds['max_interruption_tolerance'] and
                potential_savings >= thresholds['min_savings_threshold'] and
                workload_analysis['fault_tolerant']):
                
                projected_monthly_cost = current_cost * (1 - potential_savings / 100)
                monthly_savings = current_cost - projected_monthly_cost
                
                recommendations.append(self._create_pricing_recommendation(
                    strategy=PricingStrategy.SPOT_INSTANCE,
                    title=f"Convert to Spot Instance: {resource_id}",
                    description=f"Fault-tolerant workload suitable for Spot: {potential_savings:.1f}% savings, {interruption_rate:.1f}% interruption rate",
                    affected_resources=[resource],
                    current_monthly_cost=current_cost,
                    projected_monthly_cost=projected_monthly_cost,
                    estimated_monthly_savings=monthly_savings,
                    total_savings_over_term=monthly_savings * 12,  # Annual savings
                    upfront_cost=0.0,
                    payback_period_months=0,  # Immediate savings
                    confidence_score=workload_analysis['confidence_score'],
                    risk_level="MEDIUM",  # Spot instances have interruption risk
                    implementation_details={
                        'instanceType': instance_type,
                        'currentOnDemandPrice': spot_pricing['on_demand_price'],
                        'avgSpotPrice': avg_spot_price,
                        'interruptionRate': interruption_rate,
                        'workloadAnalysis': workload_analysis,
                        'spotPricingHistory': spot_pricing['price_history']
                    }
                ))
        
        return recommendations
    
    def _analyze_savings_plans(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze Savings Plans opportunities across compute resources.
        
        Requirements: 2.3 - Savings Plans analysis with ROI calculations
        """
        recommendations = []
        thresholds = self.pricing_thresholds['savings_plan']
        
        # Calculate total compute spend across eligible services
        compute_resources = [r for r in resources if r.get('resourceType') in ['ec2', 'lambda', 'fargate']]
        
        if not compute_resources:
            return recommendations
        
        # Analyze compute spending patterns
        spending_analysis = self._analyze_compute_spending_patterns(compute_resources)
        
        if not spending_analysis['sufficient_data']:
            return recommendations
        
        monthly_compute_spend = spending_analysis['monthly_compute_spend']
        utilization_consistency = spending_analysis['utilization_consistency']
        
        # Check if Savings Plan recommendation criteria are met
        if (monthly_compute_spend >= thresholds['min_compute_spend_monthly'] and
            utilization_consistency >= thresholds['min_utilization_threshold']):
            
            # Calculate Savings Plan options
            sp_options = self._calculate_savings_plan_options(spending_analysis)
            
            # Find best Savings Plan option
            best_option = max(sp_options, key=lambda x: x['roi_percentage'])
            
            recommendations.append(self._create_pricing_recommendation(
                strategy=PricingStrategy.SAVINGS_PLAN,
                title=f"Purchase Compute Savings Plan",
                description=f"Consistent compute usage: ${monthly_compute_spend:.0f}/month, {utilization_consistency:.1f}% consistency",
                affected_resources=compute_resources,
                current_monthly_cost=monthly_compute_spend,
                projected_monthly_cost=best_option['monthly_cost_with_sp'],
                estimated_monthly_savings=best_option['monthly_savings'],
                total_savings_over_term=best_option['total_savings'],
                upfront_cost=best_option['upfront_cost'],
                payback_period_months=best_option['payback_months'],
                confidence_score=spending_analysis['confidence_score'],
                risk_level="LOW",
                implementation_details={
                    'savingsPlanType': best_option['plan_type'],
                    'commitmentAmount': best_option['hourly_commitment'],
                    'term': best_option['term'],
                    'paymentOption': best_option['payment_option'],
                    'coveragePercentage': best_option['coverage_percentage'],
                    'roiPercentage': best_option['roi_percentage'],
                    'spendingAnalysis': spending_analysis,
                    'allSPOptions': sp_options
                }
            ))
        
        return recommendations
    
    def _analyze_regional_optimization(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze regional pricing optimization opportunities.
        
        Requirements: 2.4 - Regional pricing comparison and cost-effective alternatives
        """
        recommendations = []
        thresholds = self.pricing_thresholds['regional_optimization']
        
        # Group resources by type for regional analysis
        resources_by_type = self._group_resources_by_type(resources)
        
        for resource_type, type_resources in resources_by_type.items():
            if resource_type not in ['ec2', 'rds', 'lambda']:
                continue  # Focus on compute resources for regional optimization
            
            # Analyze current regional costs
            current_regional_cost = sum(r.get('currentCost', 0) for r in type_resources)
            
            if current_regional_cost < 100:  # Skip small workloads
                continue
            
            # Compare pricing across regions
            regional_comparison = self._compare_regional_pricing(resource_type, type_resources)
            
            for target_region, comparison_data in regional_comparison.items():
                cost_difference_percentage = comparison_data['cost_difference_percentage']
                
                if cost_difference_percentage >= thresholds['min_cost_difference']:
                    # Calculate total cost including data transfer
                    data_transfer_cost = self._estimate_data_transfer_costs(
                        type_resources, self.region, target_region
                    )
                    
                    net_monthly_savings = comparison_data['monthly_savings'] - data_transfer_cost
                    
                    if net_monthly_savings > 0:
                        recommendations.append(self._create_pricing_recommendation(
                            strategy=PricingStrategy.REGIONAL_OPTIMIZATION,
                            title=f"Migrate {resource_type} resources to {target_region}",
                            description=f"Regional pricing advantage: {cost_difference_percentage:.1f}% cost reduction",
                            affected_resources=type_resources,
                            current_monthly_cost=current_regional_cost,
                            projected_monthly_cost=current_regional_cost - net_monthly_savings,
                            estimated_monthly_savings=net_monthly_savings,
                            total_savings_over_term=net_monthly_savings * 12,
                            upfront_cost=comparison_data['migration_cost'],
                            payback_period_months=comparison_data['migration_cost'] / net_monthly_savings if net_monthly_savings > 0 else float('inf'),
                            confidence_score=comparison_data['confidence_score'],
                            risk_level="HIGH",  # Regional migration is high risk
                            implementation_details={
                                'sourceRegion': self.region,
                                'targetRegion': target_region,
                                'resourceType': resource_type,
                                'resourceCount': len(type_resources),
                                'costDifferencePercentage': cost_difference_percentage,
                                'dataTransferCost': data_transfer_cost,
                                'migrationComplexity': comparison_data['migration_complexity'],
                                'complianceConsiderations': comparison_data['compliance_considerations']
                            }
                        ))
        
        return recommendations
    
    def _group_instances_by_type(self, instances: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group EC2 instances by instance type."""
        grouped = {}
        
        for instance in instances:
            instance_type = instance.get('instanceType', 'unknown')
            if instance_type not in grouped:
                grouped[instance_type] = []
            grouped[instance_type].append(instance)
        
        return grouped
    
    def _analyze_instance_utilization_patterns(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze utilization patterns for Reserved Instance recommendations.
        """
        if not instances:
            return {'sufficient_data': False}
        
        thresholds = self.pricing_thresholds['reserved_instance']
        
        # Aggregate utilization data across instances
        total_data_points = 0
        total_utilization = 0
        total_runtime_hours = 0
        utilization_variance = 0
        
        for instance in instances:
            metrics = instance.get('utilizationMetrics', {})
            data_points = metrics.get('dataPoints', 0)
            
            if data_points < thresholds['min_historical_months'] * 30:  # Rough monthly data points
                continue
            
            avg_cpu = metrics.get('avgCpuUtilization', 0)
            runtime_hours = metrics.get('runtimeHours', 0)
            
            total_data_points += data_points
            total_utilization += avg_cpu * data_points
            total_runtime_hours += runtime_hours
            
            # Calculate variance for confidence scoring
            cpu_values = metrics.get('cpuUtilizationHistory', [avg_cpu])
            variance = sum((x - avg_cpu) ** 2 for x in cpu_values) / len(cpu_values)
            utilization_variance += variance
        
        if total_data_points == 0:
            return {'sufficient_data': False}
        
        avg_utilization = total_utilization / total_data_points
        monthly_runtime_hours = total_runtime_hours / max(1, len(instances))
        avg_variance = utilization_variance / len(instances)
        
        # Calculate confidence score based on data consistency
        confidence_score = max(0, min(100, 100 - (avg_variance * 2)))
        
        return {
            'sufficient_data': total_data_points >= thresholds['min_historical_months'] * 30,
            'avg_utilization': avg_utilization,
            'monthly_runtime_hours': monthly_runtime_hours,
            'confidence_score': confidence_score,
            'data_points': total_data_points,
            'utilization_variance': avg_variance,
            'instance_count': len(instances)
        }
    
    def _calculate_ri_savings(self, instance_type: str, instances: List[Dict[str, Any]], 
                             utilization_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate Reserved Instance savings for different terms and payment options.
        """
        ri_options = []
        current_monthly_cost = sum(inst.get('currentCost', 0) for inst in instances)
        
        # Mock pricing data - in real implementation, use AWS Price List API
        on_demand_hourly = self._get_on_demand_pricing(instance_type)
        
        for term in [ReservationTerm.ONE_YEAR, ReservationTerm.THREE_YEAR]:
            for payment in [PaymentOption.NO_UPFRONT, PaymentOption.PARTIAL_UPFRONT, PaymentOption.ALL_UPFRONT]:
                ri_pricing = self._get_ri_pricing(instance_type, term, payment)
                
                if not ri_pricing:
                    continue
                
                # Calculate costs and savings
                monthly_ri_cost = ri_pricing['monthly_cost'] * len(instances)
                upfront_cost = ri_pricing['upfront_cost'] * len(instances)
                
                monthly_savings = current_monthly_cost - monthly_ri_cost
                term_months = 12 if term == ReservationTerm.ONE_YEAR else 36
                total_savings = (monthly_savings * term_months) - upfront_cost
                
                payback_months = upfront_cost / monthly_savings if monthly_savings > 0 else float('inf')
                
                ri_options.append({
                    'term': term.value,
                    'payment_option': payment.value,
                    'monthly_cost_with_ri': monthly_ri_cost,
                    'monthly_savings': monthly_savings,
                    'upfront_cost': upfront_cost,
                    'total_savings': total_savings,
                    'payback_months': payback_months,
                    'roi_percentage': (total_savings / (upfront_cost + monthly_ri_cost * term_months)) * 100 if upfront_cost + monthly_ri_cost * term_months > 0 else 0
                })
        
        return ri_options
    
    def _analyze_spot_suitability(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze if a workload is suitable for Spot instances.
        """
        # Analyze workload characteristics
        tags = resource.get('tags', {})
        metrics = resource.get('utilizationMetrics', {})
        
        # Check for fault tolerance indicators
        fault_tolerant_indicators = [
            'batch', 'processing', 'analytics', 'test', 'dev', 'staging'
        ]
        
        workload_name = tags.get('Name', '').lower()
        environment = tags.get('Environment', '').lower()
        
        fault_tolerant = any(indicator in workload_name or indicator in environment 
                           for indicator in fault_tolerant_indicators)
        
        # Check usage pattern stability
        cpu_history = metrics.get('cpuUtilizationHistory', [])
        usage_stability = self._calculate_usage_stability(cpu_history)
        
        # Determine suitability
        suitable_for_spot = (
            fault_tolerant and 
            usage_stability > 70 and  # Stable usage pattern
            not any(critical in workload_name for critical in ['prod', 'production', 'critical'])
        )
        
        confidence_score = 70 if suitable_for_spot else 30
        if fault_tolerant:
            confidence_score += 20
        if usage_stability > 80:
            confidence_score += 10
        
        return {
            'suitable_for_spot': suitable_for_spot,
            'fault_tolerant': fault_tolerant,
            'usage_stability': usage_stability,
            'confidence_score': min(100, confidence_score),
            'workload_characteristics': {
                'name': workload_name,
                'environment': environment,
                'fault_tolerant_indicators': fault_tolerant_indicators
            }
        }
    
    def _get_spot_pricing_data(self, instance_type: str, region: str) -> Optional[Dict[str, Any]]:
        """
        Get Spot instance pricing data and interruption rates.
        In real implementation, this would use AWS APIs.
        """
        # Mock data - replace with actual AWS Spot pricing API calls
        spot_pricing_data = {
            't3.micro': {'avg_price': 0.003, 'on_demand_price': 0.0104, 'interruption_rate': 5.0},
            't3.small': {'avg_price': 0.006, 'on_demand_price': 0.0208, 'interruption_rate': 7.0},
            't3.medium': {'avg_price': 0.012, 'on_demand_price': 0.0416, 'interruption_rate': 8.0},
            't3.large': {'avg_price': 0.024, 'on_demand_price': 0.0832, 'interruption_rate': 10.0},
            'm5.large': {'avg_price': 0.028, 'on_demand_price': 0.096, 'interruption_rate': 12.0},
            'm5.xlarge': {'avg_price': 0.056, 'on_demand_price': 0.192, 'interruption_rate': 15.0},
        }
        
        if instance_type not in spot_pricing_data:
            return None
        
        data = spot_pricing_data[instance_type]
        savings_percentage = ((data['on_demand_price'] - data['avg_price']) / data['on_demand_price']) * 100
        
        return {
            'avg_price': data['avg_price'],
            'on_demand_price': data['on_demand_price'],
            'interruption_rate': data['interruption_rate'],
            'savings_percentage': savings_percentage,
            'price_history': [data['avg_price']] * 30  # Mock 30-day history
        }
    
    def _analyze_compute_spending_patterns(self, compute_resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze compute spending patterns for Savings Plans recommendations.
        """
        if not compute_resources:
            return {'sufficient_data': False}
        
        thresholds = self.pricing_thresholds['savings_plan']
        
        # Calculate monthly compute spend
        monthly_compute_spend = sum(r.get('currentCost', 0) for r in compute_resources)
        
        # Analyze spending consistency over time
        spending_history = []
        for resource in compute_resources:
            cost_history = resource.get('costHistory', [resource.get('currentCost', 0)])
            spending_history.extend(cost_history)
        
        if len(spending_history) < thresholds['min_historical_months']:
            return {'sufficient_data': False}
        
        # Calculate utilization consistency
        avg_spend = sum(spending_history) / len(spending_history)
        variance = sum((x - avg_spend) ** 2 for x in spending_history) / len(spending_history)
        coefficient_of_variation = (variance ** 0.5) / avg_spend if avg_spend > 0 else 1
        
        utilization_consistency = max(0, 100 - (coefficient_of_variation * 100))
        confidence_score = min(100, utilization_consistency + 20)
        
        return {
            'sufficient_data': True,
            'monthly_compute_spend': monthly_compute_spend,
            'utilization_consistency': utilization_consistency,
            'confidence_score': confidence_score,
            'spending_history': spending_history,
            'coefficient_of_variation': coefficient_of_variation,
            'resource_count': len(compute_resources)
        }
    
    def _calculate_savings_plan_options(self, spending_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate Savings Plan options with ROI calculations.
        """
        sp_options = []
        monthly_spend = spending_analysis['monthly_compute_spend']
        
        # Calculate hourly commitment (monthly spend / 730 hours)
        hourly_commitment = monthly_spend / 730
        
        for term in [ReservationTerm.ONE_YEAR, ReservationTerm.THREE_YEAR]:
            for payment in [PaymentOption.NO_UPFRONT, PaymentOption.PARTIAL_UPFRONT, PaymentOption.ALL_UPFRONT]:
                sp_pricing = self._get_savings_plan_pricing(hourly_commitment, term, payment)
                
                if not sp_pricing:
                    continue
                
                # Calculate costs and savings
                monthly_sp_cost = sp_pricing['monthly_cost']
                upfront_cost = sp_pricing['upfront_cost']
                coverage_percentage = min(100, (hourly_commitment * 730 / monthly_spend) * 100)
                
                monthly_savings = monthly_spend - monthly_sp_cost
                term_months = 12 if term == ReservationTerm.ONE_YEAR else 36
                total_savings = (monthly_savings * term_months) - upfront_cost
                
                payback_months = upfront_cost / monthly_savings if monthly_savings > 0 else float('inf')
                roi_percentage = (total_savings / (upfront_cost + monthly_sp_cost * term_months)) * 100 if upfront_cost + monthly_sp_cost * term_months > 0 else 0
                
                sp_options.append({
                    'plan_type': 'compute',
                    'term': term.value,
                    'payment_option': payment.value,
                    'hourly_commitment': hourly_commitment,
                    'monthly_cost_with_sp': monthly_sp_cost,
                    'monthly_savings': monthly_savings,
                    'upfront_cost': upfront_cost,
                    'total_savings': total_savings,
                    'payback_months': payback_months,
                    'roi_percentage': roi_percentage,
                    'coverage_percentage': coverage_percentage
                })
        
        return sp_options
    
    def _compare_regional_pricing(self, resource_type: str, resources: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Compare pricing across different AWS regions.
        """
        regional_comparisons = {}
        current_cost = sum(r.get('currentCost', 0) for r in resources)
        
        # Target regions for comparison
        target_regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
        
        for target_region in target_regions:
            if target_region == self.region:
                continue
            
            # Get regional pricing (mock data - use AWS Price List API in real implementation)
            regional_pricing = self._get_regional_pricing(resource_type, target_region)
            
            if not regional_pricing:
                continue
            
            cost_multiplier = regional_pricing['cost_multiplier']
            projected_cost = current_cost * cost_multiplier
            cost_difference = current_cost - projected_cost
            cost_difference_percentage = (cost_difference / current_cost) * 100 if current_cost > 0 else 0
            
            # Estimate migration costs
            migration_cost = self._estimate_migration_cost(resources, target_region)
            
            regional_comparisons[target_region] = {
                'projected_monthly_cost': projected_cost,
                'monthly_savings': cost_difference,
                'cost_difference_percentage': cost_difference_percentage,
                'migration_cost': migration_cost,
                'confidence_score': regional_pricing['confidence_score'],
                'migration_complexity': regional_pricing['migration_complexity'],
                'compliance_considerations': regional_pricing['compliance_considerations']
            }
        
        return regional_comparisons
    
    def _estimate_data_transfer_costs(self, resources: List[Dict[str, Any]], 
                                    source_region: str, target_region: str) -> float:
        """
        Estimate data transfer costs for regional migration.
        """
        # Mock calculation - in real implementation, analyze actual data transfer patterns
        total_storage = sum(r.get('storageSizeGB', 0) for r in resources)
        monthly_data_transfer = total_storage * 0.1  # Assume 10% of storage transferred monthly
        
        transfer_cost_per_gb = 0.09  # AWS inter-region transfer cost
        return monthly_data_transfer * transfer_cost_per_gb
    
    def _calculate_usage_stability(self, usage_history: List[float]) -> float:
        """
        Calculate usage pattern stability for Spot instance suitability.
        """
        if len(usage_history) < 7:
            return 50.0  # Default moderate stability
        
        avg_usage = sum(usage_history) / len(usage_history)
        variance = sum((x - avg_usage) ** 2 for x in usage_history) / len(usage_history)
        coefficient_of_variation = (variance ** 0.5) / avg_usage if avg_usage > 0 else 1
        
        # Convert to stability percentage (lower variation = higher stability)
        stability = max(0, 100 - (coefficient_of_variation * 100))
        return stability
    
    def _get_on_demand_pricing(self, instance_type: str) -> float:
        """Get On-Demand pricing for instance type (mock data)."""
        pricing_map = {
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            't3.large': 0.0832,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
        }
        return pricing_map.get(instance_type, 0.1)
    
    def _get_ri_pricing(self, instance_type: str, term: ReservationTerm, 
                       payment: PaymentOption) -> Optional[Dict[str, Any]]:
        """Get Reserved Instance pricing (mock data)."""
        on_demand_price = self._get_on_demand_pricing(instance_type)
        
        # Mock RI pricing calculations
        if term == ReservationTerm.ONE_YEAR:
            if payment == PaymentOption.ALL_UPFRONT:
                return {'monthly_cost': on_demand_price * 0.6 * 730, 'upfront_cost': on_demand_price * 0.6 * 730 * 12}
            elif payment == PaymentOption.PARTIAL_UPFRONT:
                return {'monthly_cost': on_demand_price * 0.65 * 730, 'upfront_cost': on_demand_price * 0.3 * 730 * 12}
            else:  # NO_UPFRONT
                return {'monthly_cost': on_demand_price * 0.7 * 730, 'upfront_cost': 0}
        else:  # THREE_YEAR
            if payment == PaymentOption.ALL_UPFRONT:
                return {'monthly_cost': on_demand_price * 0.5 * 730, 'upfront_cost': on_demand_price * 0.5 * 730 * 36}
            elif payment == PaymentOption.PARTIAL_UPFRONT:
                return {'monthly_cost': on_demand_price * 0.55 * 730, 'upfront_cost': on_demand_price * 0.25 * 730 * 36}
            else:  # NO_UPFRONT
                return {'monthly_cost': on_demand_price * 0.6 * 730, 'upfront_cost': 0}
    
    def _get_savings_plan_pricing(self, hourly_commitment: float, term: ReservationTerm, 
                                 payment: PaymentOption) -> Optional[Dict[str, Any]]:
        """Get Savings Plan pricing (mock data)."""
        monthly_commitment = hourly_commitment * 730
        
        # Mock SP pricing calculations
        if term == ReservationTerm.ONE_YEAR:
            if payment == PaymentOption.ALL_UPFRONT:
                return {'monthly_cost': monthly_commitment * 0.65, 'upfront_cost': monthly_commitment * 0.65 * 12}
            elif payment == PaymentOption.PARTIAL_UPFRONT:
                return {'monthly_cost': monthly_commitment * 0.7, 'upfront_cost': monthly_commitment * 0.35 * 12}
            else:  # NO_UPFRONT
                return {'monthly_cost': monthly_commitment * 0.75, 'upfront_cost': 0}
        else:  # THREE_YEAR
            if payment == PaymentOption.ALL_UPFRONT:
                return {'monthly_cost': monthly_commitment * 0.55, 'upfront_cost': monthly_commitment * 0.55 * 36}
            elif payment == PaymentOption.PARTIAL_UPFRONT:
                return {'monthly_cost': monthly_commitment * 0.6, 'upfront_cost': monthly_commitment * 0.3 * 36}
            else:  # NO_UPFRONT
                return {'monthly_cost': monthly_commitment * 0.65, 'upfront_cost': 0}
    
    def _get_regional_pricing(self, resource_type: str, region: str) -> Optional[Dict[str, Any]]:
        """Get regional pricing multipliers (mock data)."""
        regional_multipliers = {
            'us-east-1': {'cost_multiplier': 1.0, 'confidence_score': 95},
            'us-west-2': {'cost_multiplier': 1.05, 'confidence_score': 90},
            'eu-west-1': {'cost_multiplier': 1.1, 'confidence_score': 85},
            'ap-southeast-1': {'cost_multiplier': 1.15, 'confidence_score': 80},
        }
        
        if region not in regional_multipliers:
            return None
        
        data = regional_multipliers[region]
        return {
            'cost_multiplier': data['cost_multiplier'],
            'confidence_score': data['confidence_score'],
            'migration_complexity': 'Medium',
            'compliance_considerations': ['Data residency', 'Latency requirements']
        }
    
    def _estimate_migration_cost(self, resources: List[Dict[str, Any]], target_region: str) -> float:
        """Estimate one-time migration costs."""
        # Mock calculation based on resource count and complexity
        base_cost_per_resource = 50.0  # Base migration cost per resource
        total_storage = sum(r.get('storageSizeGB', 0) for r in resources)
        storage_transfer_cost = total_storage * 0.09  # One-time transfer cost
        
        return (len(resources) * base_cost_per_resource) + storage_transfer_cost
    
    def _create_pricing_recommendation(self, 
                                     strategy: PricingStrategy,
                                     title: str,
                                     description: str,
                                     affected_resources: List[Dict[str, Any]],
                                     current_monthly_cost: float,
                                     projected_monthly_cost: float,
                                     estimated_monthly_savings: float,
                                     total_savings_over_term: float,
                                     upfront_cost: float,
                                     payback_period_months: float,
                                     confidence_score: float,
                                     risk_level: str,
                                     implementation_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create a standardized pricing recommendation record."""
        
        return {
            'recommendationId': f"{strategy.value}-{int(datetime.utcnow().timestamp())}",
            'strategy': strategy.value,
            'title': title,
            'description': description,
            'affectedResources': [r.get('resourceId') for r in affected_resources],
            'resourceCount': len(affected_resources),
            'currentMonthlyCost': current_monthly_cost,
            'projectedMonthlyCost': projected_monthly_cost,
            'estimatedMonthlySavings': estimated_monthly_savings,
            'totalSavingsOverTerm': total_savings_over_term,
            'upfrontCost': upfront_cost,
            'paybackPeriodMonths': payback_period_months,
            'savingsPercentage': (estimated_monthly_savings / current_monthly_cost * 100) if current_monthly_cost > 0 else 0,
            'confidenceScore': confidence_score,
            'riskLevel': risk_level,
            'implementationComplexity': implementation_details.get('migrationComplexity', 'Medium'),
            'region': self.region,
            'timestamp': datetime.utcnow().isoformat(),
            'implementationDetails': implementation_details,
            'status': 'pending'
        }
    
    def _prioritize_pricing_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prioritize pricing recommendations based on savings potential, risk, and ROI.
        """
        def priority_score(rec):
            monthly_savings = rec.get('estimatedMonthlySavings', 0)
            confidence = rec.get('confidenceScore', 50) / 100
            payback_months = rec.get('paybackPeriodMonths', float('inf'))
            
            # Risk penalty
            risk_multiplier = {
                'LOW': 1.0,
                'MEDIUM': 0.8,
                'HIGH': 0.6,
                'CRITICAL': 0.4
            }.get(rec.get('riskLevel', 'MEDIUM'), 0.8)
            
            # Payback period bonus (shorter payback = higher priority)
            payback_bonus = 1.0 if payback_months == 0 else min(1.0, 12 / max(1, payback_months))
            
            return monthly_savings * confidence * risk_multiplier * payback_bonus
        
        return sorted(recommendations, key=priority_score, reverse=True)
    
    def _generate_pricing_analysis_summary(self, 
                                         resources: List[Dict[str, Any]],
                                         all_recommendations: List[Dict[str, Any]],
                                         prioritized_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive pricing analysis summary."""
        
        total_current_cost = sum(r.get('currentCost', 0) for r in resources)
        total_potential_savings = sum(rec.get('estimatedMonthlySavings', 0) for rec in all_recommendations)
        
        # Group by strategy
        strategy_breakdown = {}
        for rec in all_recommendations:
            strategy = rec.get('strategy', 'unknown')
            if strategy not in strategy_breakdown:
                strategy_breakdown[strategy] = {
                    'count': 0,
                    'totalSavings': 0.0,
                    'avgConfidence': 0.0
                }
            strategy_breakdown[strategy]['count'] += 1
            strategy_breakdown[strategy]['totalSavings'] += rec.get('estimatedMonthlySavings', 0)
            strategy_breakdown[strategy]['avgConfidence'] += rec.get('confidenceScore', 0)
        
        # Calculate averages
        for strategy_data in strategy_breakdown.values():
            if strategy_data['count'] > 0:
                strategy_data['avgConfidence'] /= strategy_data['count']
        
        # Risk analysis
        risk_breakdown = {}
        for rec in all_recommendations:
            risk_level = rec.get('riskLevel', 'MEDIUM')
            if risk_level not in risk_breakdown:
                risk_breakdown[risk_level] = {'count': 0, 'totalSavings': 0.0}
            risk_breakdown[risk_level]['count'] += 1
            risk_breakdown[risk_level]['totalSavings'] += rec.get('estimatedMonthlySavings', 0)
        
        return {
            'totalCurrentMonthlyCost': total_current_cost,
            'totalPotentialMonthlySavings': total_potential_savings,
            'potentialSavingsPercentage': (total_potential_savings / total_current_cost * 100) if total_current_cost > 0 else 0,
            'totalRecommendations': len(all_recommendations),
            'strategyBreakdown': strategy_breakdown,
            'riskBreakdown': risk_breakdown,
            'topRecommendations': prioritized_recommendations[:5],
            'quickWins': [
                rec for rec in prioritized_recommendations 
                if rec.get('riskLevel') == 'LOW' and rec.get('paybackPeriodMonths', float('inf')) <= 6
            ][:3],
            'highImpactOpportunities': [
                rec for rec in prioritized_recommendations 
                if rec.get('estimatedMonthlySavings', 0) > total_potential_savings * 0.1
            ][:3]
        }