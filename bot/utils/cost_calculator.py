#!/usr/bin/env python3
"""
Cost Calculation Utilities for Advanced FinOps Platform

Provides comprehensive cost calculation capabilities including:
- AWS Price List API integration for accurate pricing data
- Regional pricing comparison logic
- Currency handling and conversion
- Cost projections and forecasting
- Pricing calculations for optimization recommendations

Requirements: 2.4, 10.5, 5.3
"""

import logging
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class Currency(Enum):
    """Supported currencies for cost calculations."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"


class PricingModel(Enum):
    """AWS pricing models."""
    ON_DEMAND = "OnDemand"
    RESERVED = "Reserved"
    SPOT = "Spot"
    SAVINGS_PLAN = "SavingsPlan"


class CostCalculator:
    """
    Comprehensive cost calculation engine with AWS Price List API integration.
    
    Provides accurate pricing data, regional comparisons, currency handling,
    and cost projections for optimization recommendations.
    """
    
    def __init__(self, aws_config, default_currency: Currency = Currency.USD):
        """
        Initialize cost calculator.
        
        Args:
            aws_config: AWSConfig instance for client management
            default_currency: Default currency for calculations
        """
        self.aws_config = aws_config
        self.default_currency = default_currency
        self.pricing_cache = {}
        self.exchange_rates = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
        
        # Initialize pricing client (always uses us-east-1)
        self.pricing_client = aws_config.get_pricing_client()
        
        logger.info(f"Cost Calculator initialized with currency: {default_currency.value}")
    
    def get_service_pricing(self, service_code: str, region: str, 
                          filters: Optional[List[Dict[str, Any]]] = None,
                          pricing_model: PricingModel = PricingModel.ON_DEMAND) -> Dict[str, Any]:
        """
        Get pricing information for AWS service using Price List API.
        
        Args:
            service_code: AWS service code (e.g., 'AmazonEC2', 'AmazonRDS')
            region: AWS region for pricing
            filters: Additional filters for pricing query
            pricing_model: Pricing model to retrieve
            
        Returns:
            Pricing information dictionary
            
        Requirements: 10.5 - AWS Price List API integration
        """
        cache_key = f"{service_code}:{region}:{pricing_model.value}:{hash(str(filters))}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.debug(f"Using cached pricing for {service_code} in {region}")
            return self.pricing_cache[cache_key]['data']
        
        try:
            logger.info(f"Fetching pricing for {service_code} in {region}")
            
            # Build filters for pricing query
            pricing_filters = self._build_pricing_filters(service_code, region, filters, pricing_model)
            
            # Query AWS Price List API
            response = self.aws_config.execute_with_retry(
                self.pricing_client.get_products,
                ServiceCode=service_code,
                Filters=pricing_filters,
                MaxResults=100
            )
            
            # Parse pricing data
            pricing_data = self._parse_pricing_response(response, service_code, region)
            
            # Cache the results
            self.pricing_cache[cache_key] = {
                'data': pricing_data,
                'timestamp': datetime.now(timezone.utc),
                'ttl': self.cache_ttl
            }
            
            logger.debug(f"Cached pricing data for {service_code} in {region}")
            return pricing_data
            
        except Exception as e:
            logger.error(f"Failed to get pricing for {service_code} in {region}: {e}")
            # Return fallback pricing if available
            return self._get_fallback_pricing(service_code, region, pricing_model)
    
    def compare_regional_pricing(self, service_code: str, instance_type: str,
                               regions: List[str], pricing_model: PricingModel = PricingModel.ON_DEMAND) -> Dict[str, Any]:
        """
        Compare pricing across multiple AWS regions.
        
        Args:
            service_code: AWS service code
            instance_type: Instance type to compare
            regions: List of regions to compare
            pricing_model: Pricing model for comparison
            
        Returns:
            Regional pricing comparison data
            
        Requirements: 2.4 - Regional pricing comparison logic
        """
        logger.info(f"Comparing {instance_type} pricing across {len(regions)} regions")
        
        regional_pricing = {}
        base_price = None
        base_region = None
        
        for region in regions:
            try:
                # Get pricing for this region
                filters = [
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type}
                ]
                
                pricing_data = self.get_service_pricing(service_code, region, filters, pricing_model)
                
                if not pricing_data or 'hourlyPrice' not in pricing_data:
                    logger.warning(f"No pricing data available for {instance_type} in {region}")
                    continue
                
                hourly_price = pricing_data['hourlyPrice']
                monthly_price = hourly_price * 730  # Average hours per month
                
                # Set base price for comparison (first valid price)
                if base_price is None:
                    base_price = hourly_price
                    base_region = region
                
                # Calculate price difference from base
                price_difference = hourly_price - base_price
                price_difference_percentage = (price_difference / base_price * 100) if base_price > 0 else 0
                
                regional_pricing[region] = {
                    'hourlyPrice': hourly_price,
                    'monthlyPrice': monthly_price,
                    'annualPrice': monthly_price * 12,
                    'priceDifference': price_difference,
                    'priceDifferencePercentage': price_difference_percentage,
                    'currency': pricing_data.get('currency', self.default_currency.value),
                    'priceUnit': pricing_data.get('priceUnit', 'Hrs'),
                    'lastUpdated': datetime.now(timezone.utc).isoformat()
                }
                
            except Exception as e:
                logger.error(f"Failed to get pricing for {instance_type} in {region}: {e}")
                continue
        
        if not regional_pricing:
            logger.error(f"No pricing data available for {instance_type} in any region")
            return {}
        
        # Find cheapest and most expensive regions
        cheapest_region = min(regional_pricing.keys(), 
                            key=lambda r: regional_pricing[r]['hourlyPrice'])
        most_expensive_region = max(regional_pricing.keys(), 
                                  key=lambda r: regional_pricing[r]['hourlyPrice'])
        
        # Calculate potential savings
        cheapest_price = regional_pricing[cheapest_region]['hourlyPrice']
        most_expensive_price = regional_pricing[most_expensive_region]['hourlyPrice']
        max_potential_savings = ((most_expensive_price - cheapest_price) / most_expensive_price * 100) if most_expensive_price > 0 else 0
        
        return {
            'instanceType': instance_type,
            'serviceCode': service_code,
            'pricingModel': pricing_model.value,
            'baseRegion': base_region,
            'basePrice': base_price,
            'regionalPricing': regional_pricing,
            'cheapestRegion': cheapest_region,
            'mostExpensiveRegion': most_expensive_region,
            'maxPotentialSavingsPercentage': max_potential_savings,
            'comparisonTimestamp': datetime.now(timezone.utc).isoformat(),
            'currency': self.default_currency.value
        }
    
    def calculate_reserved_instance_savings(self, instance_type: str, region: str,
                                          quantity: int, term_years: int = 1,
                                          payment_option: str = 'No Upfront') -> Dict[str, Any]:
        """
        Calculate Reserved Instance savings compared to On-Demand pricing.
        
        Args:
            instance_type: EC2 instance type
            region: AWS region
            quantity: Number of instances
            term_years: Reservation term (1 or 3 years)
            payment_option: Payment option ('No Upfront', 'Partial Upfront', 'All Upfront')
            
        Returns:
            Reserved Instance savings calculation
        """
        logger.info(f"Calculating RI savings for {quantity}x {instance_type} in {region}")
        
        try:
            # Get On-Demand pricing
            od_filters = [
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'}
            ]
            
            od_pricing = self.get_service_pricing('AmazonEC2', region, od_filters, PricingModel.ON_DEMAND)
            
            # Get Reserved Instance pricing
            ri_filters = [
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                {'Type': 'TERM_MATCH', 'Field': 'offeringClass', 'Value': 'standard'},
                {'Type': 'TERM_MATCH', 'Field': 'leaseContractLength', 'Value': f'{term_years}yr'}
            ]
            
            ri_pricing = self.get_service_pricing('AmazonEC2', region, ri_filters, PricingModel.RESERVED)
            
            if not od_pricing or not ri_pricing:
                raise Exception("Unable to retrieve pricing data")
            
            # Calculate costs
            od_hourly_price = od_pricing['hourlyPrice']
            ri_hourly_price = ri_pricing.get('hourlyPrice', od_hourly_price * 0.7)  # Fallback estimate
            ri_upfront_cost = ri_pricing.get('upfrontCost', 0)
            
            # Calculate total costs over term
            term_hours = term_years * 365 * 24
            od_total_cost = od_hourly_price * term_hours * quantity
            ri_total_cost = (ri_hourly_price * term_hours * quantity) + (ri_upfront_cost * quantity)
            
            # Calculate savings
            total_savings = od_total_cost - ri_total_cost
            savings_percentage = (total_savings / od_total_cost * 100) if od_total_cost > 0 else 0
            
            # Calculate payback period
            monthly_od_cost = od_hourly_price * 730 * quantity
            monthly_ri_cost = ri_hourly_price * 730 * quantity
            monthly_savings = monthly_od_cost - monthly_ri_cost
            payback_months = (ri_upfront_cost * quantity / monthly_savings) if monthly_savings > 0 else float('inf')
            
            return {
                'instanceType': instance_type,
                'region': region,
                'quantity': quantity,
                'termYears': term_years,
                'paymentOption': payment_option,
                'onDemandHourlyPrice': od_hourly_price,
                'reservedHourlyPrice': ri_hourly_price,
                'upfrontCostPerInstance': ri_upfront_cost,
                'totalUpfrontCost': ri_upfront_cost * quantity,
                'onDemandTotalCost': od_total_cost,
                'reservedTotalCost': ri_total_cost,
                'totalSavings': total_savings,
                'savingsPercentage': savings_percentage,
                'monthlyOnDemandCost': monthly_od_cost,
                'monthlyReservedCost': monthly_ri_cost,
                'monthlySavings': monthly_savings,
                'paybackPeriodMonths': payback_months,
                'currency': self.default_currency.value,
                'calculationTimestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate RI savings: {e}")
            return self._get_fallback_ri_calculation(instance_type, region, quantity, term_years)
    
    def calculate_spot_instance_savings(self, instance_type: str, region: str,
                                      current_monthly_cost: float) -> Dict[str, Any]:
        """
        Calculate potential Spot Instance savings.
        
        Args:
            instance_type: EC2 instance type
            region: AWS region
            current_monthly_cost: Current monthly On-Demand cost
            
        Returns:
            Spot Instance savings calculation
        """
        logger.info(f"Calculating Spot savings for {instance_type} in {region}")
        
        try:
            # Get current On-Demand pricing
            od_filters = [
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type}
            ]
            
            od_pricing = self.get_service_pricing('AmazonEC2', region, od_filters, PricingModel.ON_DEMAND)
            
            if not od_pricing:
                raise Exception("Unable to retrieve On-Demand pricing")
            
            od_hourly_price = od_pricing['hourlyPrice']
            
            # Get historical Spot pricing (mock data - in real implementation use EC2 describe_spot_price_history)
            spot_pricing_data = self._get_spot_pricing_history(instance_type, region)
            
            avg_spot_price = spot_pricing_data['averagePrice']
            min_spot_price = spot_pricing_data['minimumPrice']
            max_spot_price = spot_pricing_data['maximumPrice']
            interruption_rate = spot_pricing_data['interruptionRate']
            
            # Calculate savings
            avg_savings_percentage = ((od_hourly_price - avg_spot_price) / od_hourly_price * 100) if od_hourly_price > 0 else 0
            max_savings_percentage = ((od_hourly_price - min_spot_price) / od_hourly_price * 100) if od_hourly_price > 0 else 0
            
            # Calculate monthly costs and savings
            monthly_od_cost = od_hourly_price * 730
            monthly_spot_cost = avg_spot_price * 730
            monthly_savings = monthly_od_cost - monthly_spot_cost
            
            # Adjust for interruption risk
            effective_monthly_savings = monthly_savings * (1 - interruption_rate / 100)
            
            return {
                'instanceType': instance_type,
                'region': region,
                'onDemandHourlyPrice': od_hourly_price,
                'averageSpotPrice': avg_spot_price,
                'minimumSpotPrice': min_spot_price,
                'maximumSpotPrice': max_spot_price,
                'interruptionRate': interruption_rate,
                'averageSavingsPercentage': avg_savings_percentage,
                'maximumSavingsPercentage': max_savings_percentage,
                'monthlyOnDemandCost': monthly_od_cost,
                'monthlySpotCost': monthly_spot_cost,
                'monthlySavings': monthly_savings,
                'effectiveMonthlySavings': effective_monthly_savings,
                'annualSavings': effective_monthly_savings * 12,
                'currency': self.default_currency.value,
                'calculationTimestamp': datetime.now(timezone.utc).isoformat(),
                'riskAdjusted': True
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate Spot savings: {e}")
            return self._get_fallback_spot_calculation(instance_type, region, current_monthly_cost)
    
    def project_cost_forecast(self, historical_costs: List[float], 
                            forecast_months: int = 12,
                            growth_rate: Optional[float] = None,
                            seasonal_factors: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Project future costs based on historical data and growth assumptions.
        
        Args:
            historical_costs: List of historical monthly costs
            forecast_months: Number of months to forecast
            growth_rate: Optional monthly growth rate (as decimal)
            seasonal_factors: Optional seasonal adjustment factors
            
        Returns:
            Cost forecast with confidence intervals
        """
        logger.info(f"Projecting cost forecast for {forecast_months} months")
        
        if len(historical_costs) < 3:
            logger.warning("Insufficient historical data for accurate forecasting")
            return self._get_simple_forecast(historical_costs, forecast_months)
        
        try:
            # Calculate trend and seasonality
            trend_analysis = self._analyze_cost_trend(historical_costs)
            
            # Use provided growth rate or calculate from trend
            if growth_rate is None:
                growth_rate = trend_analysis['monthly_growth_rate']
            
            # Generate forecast
            forecast = []
            last_cost = historical_costs[-1]
            
            for month in range(1, forecast_months + 1):
                # Apply growth rate
                projected_cost = last_cost * ((1 + growth_rate) ** month)
                
                # Apply seasonal factors if provided
                if seasonal_factors and len(seasonal_factors) >= 12:
                    seasonal_index = (month - 1) % 12
                    projected_cost *= seasonal_factors[seasonal_index]
                
                forecast.append(projected_cost)
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_forecast_confidence(
                historical_costs, forecast, trend_analysis
            )
            
            # Calculate summary statistics
            total_forecast_cost = sum(forecast)
            avg_monthly_cost = total_forecast_cost / forecast_months
            total_historical_cost = sum(historical_costs)
            projected_growth = ((total_forecast_cost - total_historical_cost) / total_historical_cost * 100) if total_historical_cost > 0 else 0
            
            return {
                'forecastMonths': forecast_months,
                'monthlyForecast': forecast,
                'confidenceIntervals': confidence_intervals,
                'totalForecastCost': total_forecast_cost,
                'averageMonthlyCost': avg_monthly_cost,
                'projectedGrowthPercentage': projected_growth,
                'monthlyGrowthRate': growth_rate,
                'trendAnalysis': trend_analysis,
                'forecastAccuracy': trend_analysis['r_squared'],
                'currency': self.default_currency.value,
                'forecastTimestamp': datetime.now(timezone.utc).isoformat(),
                'assumptions': {
                    'growthRate': growth_rate,
                    'seasonalAdjustment': seasonal_factors is not None,
                    'historicalDataPoints': len(historical_costs)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate cost forecast: {e}")
            return self._get_simple_forecast(historical_costs, forecast_months)
    
    def convert_currency(self, amount: float, from_currency: Currency, 
                        to_currency: Currency) -> Dict[str, Any]:
        """
        Convert amount between currencies using current exchange rates.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Currency conversion result
        """
        if from_currency == to_currency:
            return {
                'originalAmount': amount,
                'convertedAmount': amount,
                'fromCurrency': from_currency.value,
                'toCurrency': to_currency.value,
                'exchangeRate': 1.0,
                'conversionTimestamp': datetime.now(timezone.utc).isoformat()
            }
        
        try:
            # Get current exchange rate
            exchange_rate = self._get_exchange_rate(from_currency, to_currency)
            
            # Convert amount
            converted_amount = amount * exchange_rate
            
            return {
                'originalAmount': amount,
                'convertedAmount': round(converted_amount, 2),
                'fromCurrency': from_currency.value,
                'toCurrency': to_currency.value,
                'exchangeRate': exchange_rate,
                'conversionTimestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Currency conversion failed: {e}")
            # Return original amount if conversion fails
            return {
                'originalAmount': amount,
                'convertedAmount': amount,
                'fromCurrency': from_currency.value,
                'toCurrency': to_currency.value,
                'exchangeRate': 1.0,
                'conversionTimestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e)
            }
    
    def calculate_cost_per_unit(self, total_cost: float, usage_metrics: Dict[str, float],
                              unit_type: str = 'hour') -> Dict[str, Any]:
        """
        Calculate cost per unit of usage (hour, GB, request, etc.).
        
        Args:
            total_cost: Total cost for the period
            usage_metrics: Dictionary of usage metrics
            unit_type: Type of unit for calculation
            
        Returns:
            Cost per unit calculations
        """
        logger.debug(f"Calculating cost per {unit_type}")
        
        try:
            cost_per_unit_breakdown = {}
            
            for metric_name, metric_value in usage_metrics.items():
                if metric_value > 0:
                    cost_per_unit = total_cost / metric_value
                    cost_per_unit_breakdown[metric_name] = {
                        'costPerUnit': round(cost_per_unit, 6),
                        'totalUsage': metric_value,
                        'unitType': unit_type,
                        'totalCost': total_cost
                    }
            
            # Calculate primary cost per unit (based on unit_type)
            primary_usage = usage_metrics.get(f'{unit_type}s', usage_metrics.get(unit_type, 0))
            primary_cost_per_unit = total_cost / primary_usage if primary_usage > 0 else 0
            
            return {
                'totalCost': total_cost,
                'primaryUnitType': unit_type,
                'primaryUsage': primary_usage,
                'primaryCostPerUnit': round(primary_cost_per_unit, 6),
                'costPerUnitBreakdown': cost_per_unit_breakdown,
                'currency': self.default_currency.value,
                'calculationTimestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate cost per unit: {e}")
            return {
                'totalCost': total_cost,
                'primaryUnitType': unit_type,
                'primaryUsage': 0,
                'primaryCostPerUnit': 0,
                'costPerUnitBreakdown': {},
                'currency': self.default_currency.value,
                'calculationTimestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e)
            }
    
    def calculate_prorated_cost(self, monthly_cost: float, start_date: datetime, 
                              end_date: datetime, billing_cycle_start: int = 1) -> Dict[str, Any]:
        """
        Calculate pro-rated costs for partial billing periods.
        
        Args:
            monthly_cost: Full monthly cost
            start_date: Start date of the period
            end_date: End date of the period
            billing_cycle_start: Day of month when billing cycle starts (1-28)
            
        Returns:
            Pro-rated cost calculation with billing cycle alignment
            
        Requirements: 5.3 - Billing cycle alignment and pro-rated cost calculations
        """
        logger.info(f"Calculating pro-rated cost from {start_date} to {end_date}")
        
        try:
            # Validate billing cycle start day
            if not 1 <= billing_cycle_start <= 28:
                billing_cycle_start = 1
                logger.warning("Invalid billing cycle start day, defaulting to 1st")
            
            # Calculate the billing period boundaries
            billing_start = start_date.replace(day=billing_cycle_start)
            if billing_start > start_date:
                # Billing cycle started in previous month
                if billing_start.month == 1:
                    billing_start = billing_start.replace(year=billing_start.year - 1, month=12)
                else:
                    billing_start = billing_start.replace(month=billing_start.month - 1)
            
            # Calculate next billing cycle start
            if billing_start.month == 12:
                next_billing_start = billing_start.replace(year=billing_start.year + 1, month=1)
            else:
                next_billing_start = billing_start.replace(month=billing_start.month + 1)
            
            # Calculate total days in the billing cycle
            billing_cycle_days = (next_billing_start - billing_start).days
            
            # Calculate actual usage days within the billing period
            actual_start = max(start_date, billing_start)
            actual_end = min(end_date, next_billing_start)
            usage_days = (actual_end - actual_start).days
            
            # Handle partial days
            if actual_end.hour > 0 or actual_end.minute > 0 or actual_end.second > 0:
                usage_days += (actual_end.hour * 3600 + actual_end.minute * 60 + actual_end.second) / 86400
            
            # Calculate pro-rated cost
            proration_factor = usage_days / billing_cycle_days if billing_cycle_days > 0 else 0
            prorated_cost = monthly_cost * proration_factor
            
            # Calculate daily cost for reference
            daily_cost = monthly_cost / billing_cycle_days if billing_cycle_days > 0 else 0
            
            return {
                'originalMonthlyCost': monthly_cost,
                'proratedCost': round(prorated_cost, 2),
                'prorationFactor': round(proration_factor, 4),
                'usageDays': round(usage_days, 2),
                'billingCycleDays': billing_cycle_days,
                'dailyCost': round(daily_cost, 4),
                'billingPeriod': {
                    'start': billing_start.isoformat(),
                    'end': next_billing_start.isoformat(),
                    'cycleStartDay': billing_cycle_start
                },
                'usagePeriod': {
                    'start': actual_start.isoformat(),
                    'end': actual_end.isoformat()
                },
                'currency': self.default_currency.value,
                'calculationTimestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate pro-rated cost: {e}")
            return {
                'originalMonthlyCost': monthly_cost,
                'proratedCost': monthly_cost,
                'prorationFactor': 1.0,
                'error': str(e),
                'currency': self.default_currency.value,
                'calculationTimestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def align_costs_to_billing_cycle(self, costs_by_date: Dict[str, float], 
                                   billing_cycle_start: int = 1) -> Dict[str, Any]:
        """
        Align cost data to billing cycle boundaries for accurate reporting.
        
        Args:
            costs_by_date: Dictionary of costs by date (YYYY-MM-DD format)
            billing_cycle_start: Day of month when billing cycle starts
            
        Returns:
            Costs aligned to billing cycle periods
            
        Requirements: 5.3 - Billing cycle alignment
        """
        logger.info(f"Aligning costs to billing cycle starting on day {billing_cycle_start}")
        
        try:
            if not costs_by_date:
                return {
                    'billingPeriods': [],
                    'totalCost': 0.0,
                    'currency': self.default_currency.value,
                    'billingCycleStartDay': billing_cycle_start
                }
            
            # Parse dates and sort
            date_costs = []
            for date_str, cost in costs_by_date.items():
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_costs.append((date_obj.date(), cost))
                except ValueError:
                    logger.warning(f"Invalid date format: {date_str}")
                    continue
            
            date_costs.sort(key=lambda x: x[0])
            
            if not date_costs:
                return {
                    'billingPeriods': [],
                    'totalCost': 0.0,
                    'currency': self.default_currency.value,
                    'billingCycleStartDay': billing_cycle_start
                }
            
            # Group costs by billing periods
            billing_periods = []
            current_period_start = None
            current_period_costs = []
            
            for date, cost in date_costs:
                # Determine billing period for this date
                if date.day >= billing_cycle_start:
                    period_start = date.replace(day=billing_cycle_start)
                else:
                    # This date belongs to previous month's billing cycle
                    if date.month == 1:
                        period_start = date.replace(year=date.year - 1, month=12, day=billing_cycle_start)
                    else:
                        period_start = date.replace(month=date.month - 1, day=billing_cycle_start)
                
                # Check if we need to start a new billing period
                if current_period_start != period_start:
                    # Save previous period if it exists
                    if current_period_start and current_period_costs:
                        period_end = current_period_start
                        if period_end.month == 12:
                            period_end = period_end.replace(year=period_end.year + 1, month=1)
                        else:
                            period_end = period_end.replace(month=period_end.month + 1)
                        
                        billing_periods.append({
                            'periodStart': current_period_start.isoformat(),
                            'periodEnd': period_end.isoformat(),
                            'totalCost': round(sum(current_period_costs), 2),
                            'dailyCosts': len(current_period_costs),
                            'averageDailyCost': round(sum(current_period_costs) / len(current_period_costs), 2)
                        })
                    
                    # Start new period
                    current_period_start = period_start
                    current_period_costs = []
                
                current_period_costs.append(cost)
            
            # Add the last period
            if current_period_start and current_period_costs:
                period_end = current_period_start
                if period_end.month == 12:
                    period_end = period_end.replace(year=period_end.year + 1, month=1)
                else:
                    period_end = period_end.replace(month=period_end.month + 1)
                
                billing_periods.append({
                    'periodStart': current_period_start.isoformat(),
                    'periodEnd': period_end.isoformat(),
                    'totalCost': round(sum(current_period_costs), 2),
                    'dailyCosts': len(current_period_costs),
                    'averageDailyCost': round(sum(current_period_costs) / len(current_period_costs), 2)
                })
            
            # Calculate summary statistics
            total_cost = sum(period['totalCost'] for period in billing_periods)
            
            return {
                'billingPeriods': billing_periods,
                'totalCost': round(total_cost, 2),
                'numberOfPeriods': len(billing_periods),
                'averagePeriodCost': round(total_cost / len(billing_periods), 2) if billing_periods else 0,
                'currency': self.default_currency.value,
                'billingCycleStartDay': billing_cycle_start,
                'alignmentTimestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to align costs to billing cycle: {e}")
            return {
                'billingPeriods': [],
                'totalCost': 0.0,
                'currency': self.default_currency.value,
                'billingCycleStartDay': billing_cycle_start,
                'error': str(e)
            }
    
    def _build_pricing_filters(self, service_code: str, region: str, 
                             additional_filters: Optional[List[Dict[str, Any]]], 
                             pricing_model: PricingModel) -> List[Dict[str, Any]]:
        """Build filters for AWS Price List API query."""
        filters = [
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_location_name(region)}
        ]
        
        # Add service-specific filters
        if service_code == 'AmazonEC2':
            filters.extend([
                {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
            ])
            
            if pricing_model == PricingModel.ON_DEMAND:
                filters.append({'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'OnDemand'})
            elif pricing_model == PricingModel.RESERVED:
                filters.append({'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'Reserved'})
        
        # Add additional filters
        if additional_filters:
            filters.extend(additional_filters)
        
        return filters
    
    def _parse_pricing_response(self, response: Dict[str, Any], service_code: str, region: str) -> Dict[str, Any]:
        """Parse AWS Price List API response."""
        try:
            price_list = response.get('PriceList', [])
            
            if not price_list:
                logger.warning(f"No pricing data found for {service_code} in {region}")
                return {}
            
            # Parse first pricing item (most relevant)
            pricing_item = json.loads(price_list[0])
            
            # Extract pricing information
            terms = pricing_item.get('terms', {})
            on_demand_terms = terms.get('OnDemand', {})
            reserved_terms = terms.get('Reserved', {})
            
            # Get On-Demand pricing
            hourly_price = 0.0
            currency = 'USD'
            price_unit = 'Hrs'
            
            if on_demand_terms:
                for term_key, term_data in on_demand_terms.items():
                    price_dimensions = term_data.get('priceDimensions', {})
                    for dim_key, dim_data in price_dimensions.items():
                        price_per_unit = dim_data.get('pricePerUnit', {})
                        if 'USD' in price_per_unit:
                            hourly_price = float(price_per_unit['USD'])
                            currency = 'USD'
                            price_unit = dim_data.get('unit', 'Hrs')
                            break
                    if hourly_price > 0:
                        break
            
            # Get Reserved Instance pricing if available
            upfront_cost = 0.0
            if reserved_terms:
                for term_key, term_data in reserved_terms.items():
                    price_dimensions = term_data.get('priceDimensions', {})
                    for dim_key, dim_data in price_dimensions.items():
                        if 'Upfront' in dim_data.get('description', ''):
                            price_per_unit = dim_data.get('pricePerUnit', {})
                            if 'USD' in price_per_unit:
                                upfront_cost = float(price_per_unit['USD'])
            
            return {
                'hourlyPrice': hourly_price,
                'upfrontCost': upfront_cost,
                'currency': currency,
                'priceUnit': price_unit,
                'serviceCode': service_code,
                'region': region,
                'lastUpdated': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to parse pricing response: {e}")
            return {}
    
    def _get_location_name(self, region: str) -> str:
        """Convert AWS region code to location name for Price List API."""
        location_map = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'Europe (Ireland)',
            'eu-west-2': 'Europe (London)',
            'eu-central-1': 'Europe (Frankfurt)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
        }
        return location_map.get(region, region)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached pricing data is still valid."""
        if cache_key not in self.pricing_cache:
            return False
        
        cache_entry = self.pricing_cache[cache_key]
        cache_age = (datetime.now(timezone.utc) - cache_entry['timestamp']).total_seconds()
        
        return cache_age < cache_entry['ttl']
    
    def _get_fallback_pricing(self, service_code: str, region: str, pricing_model: PricingModel) -> Dict[str, Any]:
        """Get fallback pricing when API calls fail."""
        logger.warning(f"Using fallback pricing for {service_code} in {region}")
        
        # Mock fallback pricing data
        fallback_prices = {
            'AmazonEC2': {
                't3.micro': 0.0104,
                't3.small': 0.0208,
                't3.medium': 0.0416,
                't3.large': 0.0832,
                'm5.large': 0.096,
                'm5.xlarge': 0.192,
            }
        }
        
        base_price = fallback_prices.get(service_code, {}).get('t3.medium', 0.05)
        
        return {
            'hourlyPrice': base_price,
            'upfrontCost': 0.0,
            'currency': 'USD',
            'priceUnit': 'Hrs',
            'serviceCode': service_code,
            'region': region,
            'lastUpdated': datetime.now(timezone.utc).isoformat(),
            'fallback': True
        }
    
    def _get_spot_pricing_history(self, instance_type: str, region: str) -> Dict[str, Any]:
        """Get Spot pricing history (mock implementation)."""
        # In real implementation, use EC2 describe_spot_price_history API
        base_price = self._get_fallback_pricing('AmazonEC2', region, PricingModel.ON_DEMAND)['hourlyPrice']
        
        return {
            'averagePrice': base_price * 0.3,  # Spot typically 70% cheaper
            'minimumPrice': base_price * 0.1,
            'maximumPrice': base_price * 0.8,
            'interruptionRate': 5.0,  # 5% interruption rate
            'priceHistory': [base_price * 0.3] * 30  # 30-day history
        }
    
    def _analyze_cost_trend(self, historical_costs: List[float]) -> Dict[str, Any]:
        """Analyze cost trend from historical data."""
        if len(historical_costs) < 2:
            return {'monthly_growth_rate': 0.0, 'r_squared': 0.0, 'trend': 'stable'}
        
        # Simple linear regression for trend analysis
        n = len(historical_costs)
        x_values = list(range(n))
        y_values = historical_costs
        
        # Calculate slope (growth rate)
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Convert slope to monthly growth rate
        monthly_growth_rate = slope / y_mean if y_mean != 0 else 0
        
        # Calculate R-squared
        y_pred = [y_mean + slope * (x - x_mean) for x in x_values]
        ss_res = sum((y_values[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y_values[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine trend direction
        if abs(monthly_growth_rate) < 0.01:
            trend = 'stable'
        elif monthly_growth_rate > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
        
        return {
            'monthly_growth_rate': monthly_growth_rate,
            'r_squared': max(0, r_squared),
            'trend': trend,
            'slope': slope,
            'confidence': 'high' if r_squared > 0.8 else 'medium' if r_squared > 0.5 else 'low'
        }
    
    def _calculate_forecast_confidence(self, historical_costs: List[float], 
                                     forecast: List[float], 
                                     trend_analysis: Dict[str, Any]) -> List[Dict[str, float]]:
        """Calculate confidence intervals for cost forecast."""
        confidence_intervals = []
        
        # Calculate standard deviation of historical data
        if len(historical_costs) > 1:
            mean_cost = sum(historical_costs) / len(historical_costs)
            variance = sum((cost - mean_cost) ** 2 for cost in historical_costs) / (len(historical_costs) - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0
        
        # Generate confidence intervals for each forecast month
        for i, forecast_cost in enumerate(forecast):
            # Confidence decreases with time
            confidence_factor = 1.0 - (i * 0.05)  # 5% decrease per month
            confidence_factor = max(0.5, confidence_factor)  # Minimum 50% confidence
            
            # Adjust by trend analysis confidence
            if trend_analysis['confidence'] == 'high':
                confidence_factor *= 1.0
            elif trend_analysis['confidence'] == 'medium':
                confidence_factor *= 0.8
            else:
                confidence_factor *= 0.6
            
            # Calculate confidence interval
            margin = std_dev * 1.96 * (1 - confidence_factor)  # 95% confidence interval
            
            confidence_intervals.append({
                'forecast': forecast_cost,
                'lowerBound': max(0, forecast_cost - margin),
                'upperBound': forecast_cost + margin,
                'confidenceLevel': confidence_factor * 100
            })
        
        return confidence_intervals
    
    def _get_simple_forecast(self, historical_costs: List[float], forecast_months: int) -> Dict[str, Any]:
        """Generate simple forecast when advanced analysis fails."""
        if not historical_costs:
            return {
                'forecastMonths': forecast_months,
                'monthlyForecast': [0.0] * forecast_months,
                'totalForecastCost': 0.0,
                'error': 'No historical data available'
            }
        
        # Use average of historical costs
        avg_cost = sum(historical_costs) / len(historical_costs)
        forecast = [avg_cost] * forecast_months
        
        return {
            'forecastMonths': forecast_months,
            'monthlyForecast': forecast,
            'totalForecastCost': sum(forecast),
            'averageMonthlyCost': avg_cost,
            'currency': self.default_currency.value,
            'forecastTimestamp': datetime.now(timezone.utc).isoformat(),
            'method': 'simple_average'
        }
    
    def _get_exchange_rate(self, from_currency: Currency, to_currency: Currency) -> float:
        """Get exchange rate between currencies (mock implementation)."""
        # In real implementation, use a currency exchange API
        exchange_rates = {
            ('USD', 'EUR'): 0.85,
            ('USD', 'GBP'): 0.75,
            ('USD', 'JPY'): 110.0,
            ('USD', 'CAD'): 1.25,
            ('USD', 'AUD'): 1.35,
            ('EUR', 'USD'): 1.18,
            ('GBP', 'USD'): 1.33,
            ('JPY', 'USD'): 0.009,
            ('CAD', 'USD'): 0.80,
            ('AUD', 'USD'): 0.74,
        }
        
        rate_key = (from_currency.value, to_currency.value)
        return exchange_rates.get(rate_key, 1.0)
    
    def _get_fallback_ri_calculation(self, instance_type: str, region: str, 
                                   quantity: int, term_years: int) -> Dict[str, Any]:
        """Fallback RI calculation when API fails."""
        # Mock calculation with typical RI savings
        base_hourly_cost = 0.1  # Fallback hourly cost
        ri_discount = 0.3 if term_years == 1 else 0.5  # 30% or 50% discount
        
        od_total_cost = base_hourly_cost * 8760 * term_years * quantity  # 8760 hours per year
        ri_total_cost = od_total_cost * (1 - ri_discount)
        
        return {
            'instanceType': instance_type,
            'region': region,
            'quantity': quantity,
            'termYears': term_years,
            'onDemandTotalCost': od_total_cost,
            'reservedTotalCost': ri_total_cost,
            'totalSavings': od_total_cost - ri_total_cost,
            'savingsPercentage': ri_discount * 100,
            'currency': self.default_currency.value,
            'calculationTimestamp': datetime.now(timezone.utc).isoformat(),
            'fallback': True
        }
    
    def _get_fallback_spot_calculation(self, instance_type: str, region: str, 
                                     current_monthly_cost: float) -> Dict[str, Any]:
        """Fallback Spot calculation when API fails."""
        # Typical Spot savings of 70%
        spot_savings_percentage = 70.0
        monthly_savings = current_monthly_cost * (spot_savings_percentage / 100)
        
        return {
            'instanceType': instance_type,
            'region': region,
            'averageSavingsPercentage': spot_savings_percentage,
            'monthlyOnDemandCost': current_monthly_cost,
            'monthlySpotCost': current_monthly_cost - monthly_savings,
            'monthlySavings': monthly_savings,
            'annualSavings': monthly_savings * 12,
            'currency': self.default_currency.value,
            'calculationTimestamp': datetime.now(timezone.utc).isoformat(),
            'fallback': True
        }