#!/usr/bin/env python3
"""
AWS Billing Client for Advanced FinOps Platform

Provides comprehensive access to AWS billing data including:
- Detailed billing information via AWS Billing and Cost Management APIs
- Cost and Usage Reports (CUR) integration
- Billing Conductor integration for complex billing scenarios
- Account-level billing data aggregation
- Multi-account billing analysis for organizations

Requirements: 10.2 - AWS Billing and Cost Management APIs integration
"""

import logging
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BillingClient:
    """
    Comprehensive AWS Billing client with detailed billing data access.
    
    Provides access to AWS billing information through multiple APIs:
    - AWS Cost Explorer for historical cost analysis
    - AWS Billing Conductor for complex billing scenarios
    - Cost and Usage Reports (CUR) for detailed usage data
    - Account-level billing aggregation
    """
    
    def __init__(self, aws_config):
        """
        Initialize billing client.
        
        Args:
            aws_config: AWSConfig instance for client management
        """
        self.aws_config = aws_config
        self.billing_cache = {}
        self.cache_ttl = 1800  # 30 minutes cache TTL for billing data
        
        # Initialize AWS clients
        self.cost_explorer_client = aws_config.get_cost_explorer_client()
        self.budgets_client = aws_config.get_budgets_client()
        
        # Initialize Billing Conductor client (if available)
        try:
            self.billing_conductor_client = aws_config.get_billing_client()
        except Exception as e:
            logger.warning(f"Billing Conductor not available: {e}")
            self.billing_conductor_client = None
        
        # Initialize CUR client
        try:
            self.cur_client = aws_config.get_cur_client()
        except Exception as e:
            logger.warning(f"Cost and Usage Reports not available: {e}")
            self.cur_client = None
        
        logger.info("Billing Client initialized successfully")
    
    def get_account_billing_summary(self, start_date: str, end_date: str,
                                  granularity: str = 'MONTHLY') -> Dict[str, Any]:
        """
        Get comprehensive billing summary for the account.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: Time granularity (DAILY, MONTHLY)
            
        Returns:
            Account billing summary with cost breakdowns
        """
        logger.info(f"Getting account billing summary from {start_date} to {end_date}")
        
        cache_key = f"billing_summary:{start_date}:{end_date}:{granularity}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.debug("Using cached billing summary")
            return self.billing_cache[cache_key]['data']
        
        try:
            # Get cost and usage data
            cost_response = self.aws_config.execute_with_retry(
                self.cost_explorer_client.get_cost_and_usage,
                'ce',
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity,
                Metrics=['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'RECORD_TYPE'}
                ]
            )
            
            # Parse billing data
            billing_summary = self._parse_billing_summary(cost_response, start_date, end_date)
            
            # Get additional billing details
            billing_summary.update(self._get_billing_details(start_date, end_date))
            
            # Cache the results
            self.billing_cache[cache_key] = {
                'data': billing_summary,
                'timestamp': datetime.now(timezone.utc),
                'ttl': self.cache_ttl
            }
            
            logger.info(f"Retrieved billing summary with total cost: ${billing_summary.get('totalCost', 0):.2f}")
            return billing_summary
            
        except Exception as e:
            logger.error(f"Failed to get account billing summary: {e}")
            return self._get_fallback_billing_summary(start_date, end_date)
    
    def get_service_billing_breakdown(self, start_date: str, end_date: str,
                                    service_codes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get detailed billing breakdown by AWS service.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            service_codes: Optional list of specific service codes to analyze
            
        Returns:
            Service-level billing breakdown
        """
        logger.info(f"Getting service billing breakdown from {start_date} to {end_date}")
        
        try:
            # Build filters for specific services if provided
            filters = None
            if service_codes:
                filters = {
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': service_codes,
                        'MatchOptions': ['EQUALS']
                    }
                }
            
            # Get cost data grouped by service
            response = self.aws_config.execute_with_retry(
                self.cost_explorer_client.get_cost_and_usage,
                'ce',
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ],
                Filter=filters
            )
            
            # Parse service breakdown
            service_breakdown = self._parse_service_breakdown(response)
            
            # Get usage type details for each service
            for service_name in service_breakdown.get('services', {}):
                usage_details = self._get_service_usage_details(
                    service_name, start_date, end_date
                )
                service_breakdown['services'][service_name]['usageDetails'] = usage_details
            
            return service_breakdown
            
        except Exception as e:
            logger.error(f"Failed to get service billing breakdown: {e}")
            return {'services': {}, 'totalCost': 0.0, 'error': str(e)}
    
    def get_regional_billing_analysis(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get billing analysis by AWS region.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Regional billing analysis
        """
        logger.info(f"Getting regional billing analysis from {start_date} to {end_date}")
        
        try:
            # Get cost data grouped by region
            response = self.aws_config.execute_with_retry(
                self.cost_explorer_client.get_cost_and_usage,
                'ce',
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'REGION'},
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            # Parse regional data
            regional_analysis = self._parse_regional_breakdown(response)
            
            # Add regional cost comparison
            regional_analysis['costComparison'] = self._analyze_regional_costs(
                regional_analysis.get('regions', {})
            )
            
            return regional_analysis
            
        except Exception as e:
            logger.error(f"Failed to get regional billing analysis: {e}")
            return {'regions': {}, 'totalCost': 0.0, 'error': str(e)}
    
    def get_billing_trends(self, months_back: int = 12) -> Dict[str, Any]:
        """
        Get billing trends over time.
        
        Args:
            months_back: Number of months to analyze
            
        Returns:
            Billing trend analysis
        """
        logger.info(f"Getting billing trends for last {months_back} months")
        
        try:
            # Calculate date range
            end_date = datetime.now().replace(day=1)  # First day of current month
            start_date = end_date - timedelta(days=months_back * 30)
            
            # Get monthly cost data
            response = self.aws_config.execute_with_retry(
                self.cost_explorer_client.get_cost_and_usage,
                'ce',
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            # Analyze trends
            trend_analysis = self._analyze_billing_trends(response)
            
            # Add forecasting
            trend_analysis['forecast'] = self._generate_cost_forecast(
                trend_analysis.get('monthlyData', [])
            )
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Failed to get billing trends: {e}")
            return {'monthlyData': [], 'trends': {}, 'error': str(e)}
    
    def get_cost_anomalies(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get cost anomalies detected by AWS Cost Anomaly Detection.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Cost anomaly analysis
        """
        logger.info(f"Getting cost anomalies from {start_date} to {end_date}")
        
        try:
            # Get anomalies from Cost Explorer
            response = self.aws_config.execute_with_retry(
                self.cost_explorer_client.get_anomalies,
                'ce',
                DateInterval={
                    'StartDate': start_date,
                    'EndDate': end_date
                }
            )
            
            # Parse anomaly data
            anomaly_analysis = self._parse_cost_anomalies(response)
            
            # Add impact analysis
            for anomaly in anomaly_analysis.get('anomalies', []):
                anomaly['impactAnalysis'] = self._analyze_anomaly_impact(anomaly)
            
            return anomaly_analysis
            
        except Exception as e:
            logger.error(f"Failed to get cost anomalies: {e}")
            return {'anomalies': [], 'totalImpact': 0.0, 'error': str(e)}
    
    def get_reserved_instance_utilization(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get Reserved Instance utilization and coverage.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            RI utilization analysis
        """
        logger.info(f"Getting RI utilization from {start_date} to {end_date}")
        
        try:
            # Get RI utilization
            utilization_response = self.aws_config.execute_with_retry(
                self.cost_explorer_client.get_reservation_utilization,
                'ce',
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY'
            )
            
            # Get RI coverage
            coverage_response = self.aws_config.execute_with_retry(
                self.cost_explorer_client.get_reservation_coverage,
                'ce',
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY'
            )
            
            # Parse RI data
            ri_analysis = self._parse_ri_utilization(utilization_response, coverage_response)
            
            # Add recommendations
            ri_analysis['recommendations'] = self._generate_ri_recommendations(ri_analysis)
            
            return ri_analysis
            
        except Exception as e:
            logger.error(f"Failed to get RI utilization: {e}")
            return {'utilization': {}, 'coverage': {}, 'error': str(e)}
    
    def get_savings_plans_utilization(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get Savings Plans utilization and coverage.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Savings Plans utilization analysis
        """
        logger.info(f"Getting Savings Plans utilization from {start_date} to {end_date}")
        
        try:
            # Get Savings Plans utilization
            utilization_response = self.aws_config.execute_with_retry(
                self.cost_explorer_client.get_savings_plans_utilization,
                'ce',
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY'
            )
            
            # Get Savings Plans coverage
            coverage_response = self.aws_config.execute_with_retry(
                self.cost_explorer_client.get_savings_plans_coverage,
                'ce',
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY'
            )
            
            # Parse Savings Plans data
            sp_analysis = self._parse_savings_plans_utilization(
                utilization_response, coverage_response
            )
            
            # Add recommendations
            sp_analysis['recommendations'] = self._generate_sp_recommendations(sp_analysis)
            
            return sp_analysis
            
        except Exception as e:
            logger.error(f"Failed to get Savings Plans utilization: {e}")
            return {'utilization': {}, 'coverage': {}, 'error': str(e)}
    
    def get_cost_allocation_tags(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get cost allocation by tags.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Cost allocation by tags
        """
        logger.info(f"Getting cost allocation by tags from {start_date} to {end_date}")
        
        try:
            # Get available cost allocation tags
            tags_response = self.aws_config.execute_with_retry(
                self.cost_explorer_client.get_cost_categories,
                'ce',
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                }
            )
            
            # Get cost data grouped by tags
            cost_response = self.aws_config.execute_with_retry(
                self.cost_explorer_client.get_cost_and_usage,
                'ce',
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UnblendedCost'],
                GroupBy=[
                    {'Type': 'TAG', 'Key': 'Environment'},
                    {'Type': 'TAG', 'Key': 'Project'},
                    {'Type': 'TAG', 'Key': 'Team'}
                ]
            )
            
            # Parse tag allocation data
            tag_allocation = self._parse_tag_allocation(cost_response)
            
            return tag_allocation
            
        except Exception as e:
            logger.error(f"Failed to get cost allocation by tags: {e}")
            return {'tagAllocation': {}, 'untaggedCosts': 0.0, 'error': str(e)}
    
    def _parse_billing_summary(self, response: Dict[str, Any], 
                             start_date: str, end_date: str) -> Dict[str, Any]:
        """Parse billing summary from Cost Explorer response."""
        try:
            results_by_time = response.get('ResultsByTime', [])
            
            total_blended_cost = 0.0
            total_unblended_cost = 0.0
            service_costs = {}
            record_type_costs = {}
            
            for result in results_by_time:
                for group in result.get('Groups', []):
                    keys = group.get('Keys', [])
                    metrics = group.get('Metrics', {})
                    
                    if len(keys) >= 2:
                        service = keys[0]
                        record_type = keys[1]
                        
                        blended_cost = float(metrics.get('BlendedCost', {}).get('Amount', 0))
                        unblended_cost = float(metrics.get('UnblendedCost', {}).get('Amount', 0))
                        
                        total_blended_cost += blended_cost
                        total_unblended_cost += unblended_cost
                        
                        # Aggregate by service
                        if service not in service_costs:
                            service_costs[service] = {'blended': 0.0, 'unblended': 0.0}
                        service_costs[service]['blended'] += blended_cost
                        service_costs[service]['unblended'] += unblended_cost
                        
                        # Aggregate by record type
                        if record_type not in record_type_costs:
                            record_type_costs[record_type] = {'blended': 0.0, 'unblended': 0.0}
                        record_type_costs[record_type]['blended'] += blended_cost
                        record_type_costs[record_type]['unblended'] += unblended_cost
            
            return {
                'period': {'start': start_date, 'end': end_date},
                'totalCost': total_unblended_cost,
                'totalBlendedCost': total_blended_cost,
                'totalUnblendedCost': total_unblended_cost,
                'serviceCosts': service_costs,
                'recordTypeCosts': record_type_costs,
                'currency': 'USD',
                'retrievalTimestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to parse billing summary: {e}")
            return {'totalCost': 0.0, 'error': str(e)}
    
    def _get_billing_details(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get additional billing details."""
        details = {}
        
        try:
            # Get account information
            account_id = self.aws_config.get_account_id()
            details['accountId'] = account_id
            
            # Get billing period info
            details['billingPeriod'] = {
                'start': start_date,
                'end': end_date,
                'daysInPeriod': (datetime.fromisoformat(end_date) - 
                               datetime.fromisoformat(start_date)).days
            }
            
            # Get currency information
            details['currency'] = 'USD'  # Default to USD
            
        except Exception as e:
            logger.warning(f"Failed to get billing details: {e}")
        
        return details
    
    def _parse_service_breakdown(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse service breakdown from Cost Explorer response."""
        try:
            results_by_time = response.get('ResultsByTime', [])
            services = {}
            total_cost = 0.0
            
            for result in results_by_time:
                for group in result.get('Groups', []):
                    keys = group.get('Keys', [])
                    metrics = group.get('Metrics', {})
                    
                    if len(keys) >= 2:
                        service = keys[0]
                        usage_type = keys[1]
                        
                        unblended_cost = float(metrics.get('UnblendedCost', {}).get('Amount', 0))
                        usage_quantity = float(metrics.get('UsageQuantity', {}).get('Amount', 0))
                        
                        total_cost += unblended_cost
                        
                        if service not in services:
                            services[service] = {
                                'totalCost': 0.0,
                                'usageTypes': {},
                                'totalUsage': 0.0
                            }
                        
                        services[service]['totalCost'] += unblended_cost
                        services[service]['totalUsage'] += usage_quantity
                        services[service]['usageTypes'][usage_type] = {
                            'cost': unblended_cost,
                            'usage': usage_quantity,
                            'unit': metrics.get('UsageQuantity', {}).get('Unit', 'Unknown')
                        }
            
            return {
                'services': services,
                'totalCost': total_cost,
                'serviceCount': len(services),
                'currency': 'USD'
            }
            
        except Exception as e:
            logger.error(f"Failed to parse service breakdown: {e}")
            return {'services': {}, 'totalCost': 0.0, 'error': str(e)}
    
    def _get_service_usage_details(self, service_name: str, 
                                 start_date: str, end_date: str) -> Dict[str, Any]:
        """Get detailed usage information for a specific service."""
        try:
            response = self.aws_config.execute_with_retry(
                self.cost_explorer_client.get_cost_and_usage,
                'ce',
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='DAILY',
                Metrics=['UsageQuantity'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': [service_name],
                        'MatchOptions': ['EQUALS']
                    }
                }
            )
            
            # Parse usage details
            usage_details = {}
            for result in response.get('ResultsByTime', []):
                date = result.get('TimePeriod', {}).get('Start')
                daily_usage = {}
                
                for group in result.get('Groups', []):
                    usage_type = group.get('Keys', ['Unknown'])[0]
                    usage_amount = float(group.get('Metrics', {}).get('UsageQuantity', {}).get('Amount', 0))
                    
                    daily_usage[usage_type] = usage_amount
                
                usage_details[date] = daily_usage
            
            return usage_details
            
        except Exception as e:
            logger.warning(f"Failed to get usage details for {service_name}: {e}")
            return {}
    
    def _parse_regional_breakdown(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse regional breakdown from Cost Explorer response."""
        try:
            results_by_time = response.get('ResultsByTime', [])
            regions = {}
            total_cost = 0.0
            
            for result in results_by_time:
                for group in result.get('Groups', []):
                    keys = group.get('Keys', [])
                    metrics = group.get('Metrics', {})
                    
                    if len(keys) >= 2:
                        region = keys[0]
                        service = keys[1]
                        
                        unblended_cost = float(metrics.get('UnblendedCost', {}).get('Amount', 0))
                        total_cost += unblended_cost
                        
                        if region not in regions:
                            regions[region] = {'totalCost': 0.0, 'services': {}}
                        
                        regions[region]['totalCost'] += unblended_cost
                        regions[region]['services'][service] = unblended_cost
            
            return {
                'regions': regions,
                'totalCost': total_cost,
                'regionCount': len(regions),
                'currency': 'USD'
            }
            
        except Exception as e:
            logger.error(f"Failed to parse regional breakdown: {e}")
            return {'regions': {}, 'totalCost': 0.0, 'error': str(e)}
    
    def _analyze_regional_costs(self, regions: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze regional cost distribution."""
        if not regions:
            return {}
        
        costs = [(region, data['totalCost']) for region, data in regions.items()]
        costs.sort(key=lambda x: x[1], reverse=True)
        
        total_cost = sum(cost for _, cost in costs)
        
        return {
            'mostExpensiveRegion': costs[0][0] if costs else None,
            'leastExpensiveRegion': costs[-1][0] if costs else None,
            'costDistribution': [
                {
                    'region': region,
                    'cost': cost,
                    'percentage': (cost / total_cost * 100) if total_cost > 0 else 0
                }
                for region, cost in costs
            ]
        }
    
    def _analyze_billing_trends(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze billing trends over time."""
        try:
            results_by_time = response.get('ResultsByTime', [])
            monthly_data = []
            
            for result in results_by_time:
                period = result.get('TimePeriod', {})
                total_cost = 0.0
                service_costs = {}
                
                for group in result.get('Groups', []):
                    service = group.get('Keys', ['Unknown'])[0]
                    cost = float(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', 0))
                    
                    total_cost += cost
                    service_costs[service] = cost
                
                monthly_data.append({
                    'period': period,
                    'totalCost': total_cost,
                    'serviceCosts': service_costs
                })
            
            # Calculate trends
            trends = self._calculate_cost_trends(monthly_data)
            
            return {
                'monthlyData': monthly_data,
                'trends': trends,
                'dataPoints': len(monthly_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze billing trends: {e}")
            return {'monthlyData': [], 'trends': {}, 'error': str(e)}
    
    def _calculate_cost_trends(self, monthly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cost trends from monthly data."""
        if len(monthly_data) < 2:
            return {'trend': 'insufficient_data'}
        
        costs = [data['totalCost'] for data in monthly_data]
        
        # Calculate month-over-month growth
        mom_growth = []
        for i in range(1, len(costs)):
            if costs[i-1] > 0:
                growth = ((costs[i] - costs[i-1]) / costs[i-1]) * 100
                mom_growth.append(growth)
        
        avg_growth = sum(mom_growth) / len(mom_growth) if mom_growth else 0
        
        # Determine trend direction
        if avg_growth > 5:
            trend = 'increasing'
        elif avg_growth < -5:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'averageMonthlyGrowth': avg_growth,
            'monthlyGrowthRates': mom_growth,
            'totalGrowth': ((costs[-1] - costs[0]) / costs[0] * 100) if costs[0] > 0 else 0
        }
    
    def _generate_cost_forecast(self, monthly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate cost forecast based on historical data."""
        if len(monthly_data) < 3:
            return {'forecast': [], 'confidence': 'low'}
        
        costs = [data['totalCost'] for data in monthly_data]
        
        # Simple linear regression for forecast
        n = len(costs)
        x_values = list(range(n))
        
        # Calculate trend
        x_mean = sum(x_values) / n
        y_mean = sum(costs) / n
        
        numerator = sum((x_values[i] - x_mean) * (costs[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        # Generate 3-month forecast
        forecast = []
        for i in range(3):
            future_x = n + i
            predicted_cost = intercept + slope * future_x
            forecast.append(max(0, predicted_cost))  # Ensure non-negative
        
        return {
            'forecast': forecast,
            'confidence': 'medium' if len(costs) >= 6 else 'low',
            'trend_slope': slope
        }
    
    def _parse_cost_anomalies(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse cost anomalies from response."""
        try:
            anomalies = response.get('Anomalies', [])
            parsed_anomalies = []
            total_impact = 0.0
            
            for anomaly in anomalies:
                impact = anomaly.get('Impact', {})
                max_impact = float(impact.get('MaxImpact', 0))
                total_impact += max_impact
                
                parsed_anomalies.append({
                    'anomalyId': anomaly.get('AnomalyId'),
                    'anomalyStartDate': anomaly.get('AnomalyStartDate'),
                    'anomalyEndDate': anomaly.get('AnomalyEndDate'),
                    'dimensionKey': anomaly.get('DimensionKey'),
                    'maxImpact': max_impact,
                    'totalImpact': float(impact.get('TotalImpact', 0)),
                    'feedback': anomaly.get('Feedback'),
                    'rootCauses': anomaly.get('RootCauses', [])
                })
            
            return {
                'anomalies': parsed_anomalies,
                'totalImpact': total_impact,
                'anomalyCount': len(parsed_anomalies)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse cost anomalies: {e}")
            return {'anomalies': [], 'totalImpact': 0.0, 'error': str(e)}
    
    def _analyze_anomaly_impact(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the impact of a cost anomaly."""
        max_impact = anomaly.get('maxImpact', 0)
        
        # Categorize impact severity
        if max_impact > 1000:
            severity = 'CRITICAL'
        elif max_impact > 500:
            severity = 'HIGH'
        elif max_impact > 100:
            severity = 'MEDIUM'
        else:
            severity = 'LOW'
        
        return {
            'severity': severity,
            'impactCategory': self._categorize_impact(max_impact),
            'recommendedAction': self._get_anomaly_action(severity)
        }
    
    def _categorize_impact(self, impact: float) -> str:
        """Categorize anomaly impact."""
        if impact > 1000:
            return 'Major Cost Spike'
        elif impact > 500:
            return 'Significant Increase'
        elif impact > 100:
            return 'Notable Change'
        else:
            return 'Minor Variation'
    
    def _get_anomaly_action(self, severity: str) -> str:
        """Get recommended action for anomaly."""
        actions = {
            'CRITICAL': 'Immediate investigation required',
            'HIGH': 'Review within 24 hours',
            'MEDIUM': 'Review within 3 days',
            'LOW': 'Monitor for trends'
        }
        return actions.get(severity, 'Monitor')
    
    def _parse_ri_utilization(self, utilization_response: Dict[str, Any],
                            coverage_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Reserved Instance utilization data."""
        try:
            utilization_data = {}
            coverage_data = {}
            
            # Parse utilization
            for result in utilization_response.get('UtilizationsByTime', []):
                period = result.get('TimePeriod', {})
                total = result.get('Total', {})
                
                utilization_data[period.get('Start')] = {
                    'utilizationPercentage': float(total.get('UtilizationPercentage', 0)),
                    'purchasedHours': float(total.get('PurchasedHours', 0)),
                    'usedHours': float(total.get('UsedHours', 0)),
                    'unusedHours': float(total.get('UnusedHours', 0))
                }
            
            # Parse coverage
            for result in coverage_response.get('CoveragesByTime', []):
                period = result.get('TimePeriod', {})
                total = result.get('Total', {})
                
                coverage_data[period.get('Start')] = {
                    'coveragePercentage': float(total.get('CoverageHours', {}).get('CoverageHoursPercentage', 0)),
                    'onDemandHours': float(total.get('CoverageHours', {}).get('OnDemandHours', 0)),
                    'reservedHours': float(total.get('CoverageHours', {}).get('ReservedHours', 0)),
                    'totalRunningHours': float(total.get('CoverageHours', {}).get('TotalRunningHours', 0))
                }
            
            return {
                'utilization': utilization_data,
                'coverage': coverage_data
            }
            
        except Exception as e:
            logger.error(f"Failed to parse RI utilization: {e}")
            return {'utilization': {}, 'coverage': {}, 'error': str(e)}
    
    def _parse_savings_plans_utilization(self, utilization_response: Dict[str, Any],
                                       coverage_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Savings Plans utilization data."""
        try:
            utilization_data = {}
            coverage_data = {}
            
            # Parse utilization
            for result in utilization_response.get('SavingsPlansUtilizationsByTime', []):
                period = result.get('TimePeriod', {})
                total = result.get('Total', {})
                
                utilization_data[period.get('Start')] = {
                    'utilizationPercentage': float(total.get('Utilization', {}).get('UtilizationPercentage', 0)),
                    'usedCommitment': float(total.get('Utilization', {}).get('UsedCommitment', 0)),
                    'unusedCommitment': float(total.get('Utilization', {}).get('UnusedCommitment', 0)),
                    'totalCommitment': float(total.get('Utilization', {}).get('TotalCommitment', 0))
                }
            
            # Parse coverage
            for result in coverage_response.get('SavingsPlansCoverages', []):
                period = result.get('TimePeriod', {})
                total = result.get('Coverage', {})
                
                coverage_data[period.get('Start')] = {
                    'coveragePercentage': float(total.get('CoveragePercentage', 0)),
                    'onDemandCost': float(total.get('OnDemandCost', 0)),
                    'spendCoveredBySavingsPlans': float(total.get('SpendCoveredBySavingsPlans', 0))
                }
            
            return {
                'utilization': utilization_data,
                'coverage': coverage_data
            }
            
        except Exception as e:
            logger.error(f"Failed to parse Savings Plans utilization: {e}")
            return {'utilization': {}, 'coverage': {}, 'error': str(e)}
    
    def _generate_ri_recommendations(self, ri_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Reserved Instance recommendations."""
        recommendations = []
        
        utilization_data = ri_analysis.get('utilization', {})
        coverage_data = ri_analysis.get('coverage', {})
        
        # Analyze utilization patterns
        avg_utilization = 0
        if utilization_data:
            utilizations = [data.get('utilizationPercentage', 0) for data in utilization_data.values()]
            avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0
        
        # Generate recommendations based on utilization
        if avg_utilization < 70:
            recommendations.append({
                'type': 'REDUCE_RI_COMMITMENT',
                'priority': 'HIGH',
                'description': f'RI utilization is low ({avg_utilization:.1f}%). Consider reducing commitment.',
                'potentialSavings': 'TBD'
            })
        elif avg_utilization > 95:
            recommendations.append({
                'type': 'INCREASE_RI_COMMITMENT',
                'priority': 'MEDIUM',
                'description': f'RI utilization is high ({avg_utilization:.1f}%). Consider increasing commitment.',
                'potentialSavings': 'TBD'
            })
        
        return recommendations
    
    def _generate_sp_recommendations(self, sp_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Savings Plans recommendations."""
        recommendations = []
        
        utilization_data = sp_analysis.get('utilization', {})
        
        # Analyze utilization patterns
        avg_utilization = 0
        if utilization_data:
            utilizations = [data.get('utilizationPercentage', 0) for data in utilization_data.values()]
            avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0
        
        # Generate recommendations based on utilization
        if avg_utilization < 70:
            recommendations.append({
                'type': 'REDUCE_SP_COMMITMENT',
                'priority': 'HIGH',
                'description': f'Savings Plans utilization is low ({avg_utilization:.1f}%). Consider reducing commitment.',
                'potentialSavings': 'TBD'
            })
        elif avg_utilization > 95:
            recommendations.append({
                'type': 'INCREASE_SP_COMMITMENT',
                'priority': 'MEDIUM',
                'description': f'Savings Plans utilization is high ({avg_utilization:.1f}%). Consider increasing commitment.',
                'potentialSavings': 'TBD'
            })
        
        return recommendations
    
    def _parse_tag_allocation(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse cost allocation by tags."""
        try:
            results_by_time = response.get('ResultsByTime', [])
            tag_allocation = {}
            untagged_costs = 0.0
            total_cost = 0.0
            
            for result in results_by_time:
                for group in result.get('Groups', []):
                    keys = group.get('Keys', [])
                    metrics = group.get('Metrics', {})
                    
                    cost = float(metrics.get('UnblendedCost', {}).get('Amount', 0))
                    total_cost += cost
                    
                    if keys and keys[0] != 'No tag':
                        tag_value = keys[0]
                        if tag_value not in tag_allocation:
                            tag_allocation[tag_value] = 0.0
                        tag_allocation[tag_value] += cost
                    else:
                        untagged_costs += cost
            
            return {
                'tagAllocation': tag_allocation,
                'untaggedCosts': untagged_costs,
                'totalCost': total_cost,
                'taggedPercentage': ((total_cost - untagged_costs) / total_cost * 100) if total_cost > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to parse tag allocation: {e}")
            return {'tagAllocation': {}, 'untaggedCosts': 0.0, 'error': str(e)}
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self.billing_cache:
            return False
        
        cache_entry = self.billing_cache[cache_key]
        cache_age = (datetime.now(timezone.utc) - cache_entry['timestamp']).total_seconds()
        
        return cache_age < cache_entry['ttl']
    
    def _get_fallback_billing_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get fallback billing summary when API calls fail."""
        logger.warning("Using fallback billing summary")
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'totalCost': 0.0,
            'totalBlendedCost': 0.0,
            'totalUnblendedCost': 0.0,
            'serviceCosts': {},
            'recordTypeCosts': {},
            'currency': 'USD',
            'retrievalTimestamp': datetime.now(timezone.utc).isoformat(),
            'fallback': True,
            'error': 'API unavailable'
        }