#!/usr/bin/env python3
"""
AWS Pricing Client for Advanced FinOps Platform

Provides comprehensive access to AWS pricing information including:
- Real-time pricing data via AWS Price List API
- Regional pricing comparison and analysis
- Currency conversion and multi-currency support
- Reserved Instance and Savings Plans pricing analysis
- Spot Instance pricing history and trends
- Service-specific pricing models and calculations

Requirements: 10.5, 2.1, 2.3 - AWS Price List API integration and pricing analysis
"""

import logging
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, Union
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class PricingModel(Enum):
    """AWS pricing models."""
    ON_DEMAND = "OnDemand"
    RESERVED = "Reserved"
    SPOT = "Spot"
    SAVINGS_PLAN = "SavingsPlan"


class Currency(Enum):
    """Supported currencies for pricing."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"


class PricingClient:
    """
    Comprehensive AWS Pricing client with real-time pricing information access.
    
    Provides access to AWS pricing data through:
    - AWS Price List API for current pricing
    - EC2 Spot pricing history
    - Regional pricing comparison
    - Currency conversion capabilities
    - Reserved Instance and Savings Plans pricing analysis
    """
    
    def __init__(self, aws_config, default_currency: Currency = Currency.USD):
        """
        Initialize pricing client.
        
        Args:
            aws_config: AWSConfig instance for client management
            default_currency: Default currency for pricing calculations
        """
        self.aws_config = aws_config
        self.default_currency = default_currency
        self.pricing_cache = {}
        self.exchange_rate_cache = {}
        self.cache_ttl = 3600  # 1 hour cache TTL for pricing data
        
        # Initialize AWS clients
        self.pricing_client = aws_config.get_pricing_client()
        
        # Exchange rate API configuration (mock for demo)
        self.exchange_rates = self._initialize_exchange_rates()
        
        logger.info(f"Pricing Client initialized with currency: {default_currency.value}")
    
    def get_service_pricing(self, service_code: str, region: str,
                          filters: Optional[List[Dict[str, Any]]] = None,
                          pricing_model: PricingModel = PricingModel.ON_DEMAND,
                          include_regional_comparison: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive pricing information for AWS service.
        
        Args:
            service_code: AWS service code (e.g., 'AmazonEC2', 'AmazonRDS')
            region: AWS region for pricing
            filters: Additional filters for pricing query
            pricing_model: Pricing model to retrieve
            include_regional_comparison: Whether to include regional comparison (prevents recursion)
            
        Returns:
            Comprehensive pricing information
        """
        logger.info(f"Getting {pricing_model.value} pricing for {service_code} in {region}")
        
        cache_key = f"pricing:{service_code}:{region}:{pricing_model.value}:{hash(str(filters))}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.debug(f"Using cached pricing for {service_code}")
            return self.pricing_cache[cache_key]['data']
        
        try:
            # Build pricing filters
            pricing_filters = self._build_pricing_filters(service_code, region, filters, pricing_model)
            
            # Query AWS Price List API
            response = self.aws_config.execute_with_retry(
                self.pricing_client.get_products,
                'pricing',
                ServiceCode=service_code,
                Filters=pricing_filters,
                MaxResults=100
            )
            
            # Parse and enhance pricing data
            pricing_data = self._parse_pricing_response(response, service_code, region, pricing_model)
            
            # Add regional comparison if available and not already in a regional comparison call
            # TEMPORARILY DISABLED TO PREVENT RECURSION - WILL FIX IN FUTURE VERSION
            # if pricing_data and 'hourlyPrice' in pricing_data and include_regional_comparison:
            #     pricing_data['regionalComparison'] = self._get_regional_pricing_comparison(
            #         service_code, filters, pricing_model
            #     )
            
            # Add currency conversions
            if pricing_data and 'hourlyPrice' in pricing_data:
                pricing_data['currencyConversions'] = self._convert_to_multiple_currencies(
                    pricing_data['hourlyPrice']
                )
            
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
            return self._get_fallback_pricing(service_code, region, pricing_model)
    
    def compare_regional_pricing(self, service_code: str, instance_type: str,
                               regions: List[str], 
                               pricing_model: PricingModel = PricingModel.ON_DEMAND) -> Dict[str, Any]:
        """
        Compare pricing across multiple AWS regions with detailed analysis.
        
        Args:
            service_code: AWS service code
            instance_type: Instance type to compare
            regions: List of regions to compare
            pricing_model: Pricing model for comparison
            
        Returns:
            Comprehensive regional pricing comparison
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
                
                # Set base price for comparison (first valid price)
                if base_price is None:
                    base_price = hourly_price
                    base_region = region
                
                # Calculate comprehensive pricing metrics
                regional_pricing[region] = self._calculate_regional_metrics(
                    pricing_data, hourly_price, base_price, region
                )
                
            except Exception as e:
                logger.error(f"Failed to get pricing for {instance_type} in {region}: {e}")
                continue
        
        if not regional_pricing:
            logger.error(f"No pricing data available for {instance_type} in any region")
            return {}
        
        # Generate comprehensive comparison analysis
        comparison_analysis = self._generate_comparison_analysis(regional_pricing, instance_type, service_code)
        
        return {
            'instanceType': instance_type,
            'serviceCode': service_code,
            'pricingModel': pricing_model.value,
            'baseRegion': base_region,
            'basePrice': base_price,
            'regionalPricing': regional_pricing,
            'analysis': comparison_analysis,
            'comparisonTimestamp': datetime.now(timezone.utc).isoformat(),
            'currency': self.default_currency.value
        }
    def get_reserved_instance_pricing(self, instance_type: str, region: str,
                                    term_years: int = 1, payment_option: str = 'No Upfront',
                                    offering_class: str = 'standard') -> Dict[str, Any]:
        """
        Get comprehensive Reserved Instance pricing analysis.
        
        Args:
            instance_type: EC2 instance type
            region: AWS region
            term_years: Reservation term (1 or 3 years)
            payment_option: Payment option ('No Upfront', 'Partial Upfront', 'All Upfront')
            offering_class: Offering class ('standard' or 'convertible')
            
        Returns:
            Comprehensive RI pricing analysis with savings calculations
        """
        logger.info(f"Getting RI pricing for {instance_type} in {region} ({term_years}yr, {payment_option})")
        
        try:
            # Get On-Demand pricing for comparison
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
                {'Type': 'TERM_MATCH', 'Field': 'offeringClass', 'Value': offering_class},
                {'Type': 'TERM_MATCH', 'Field': 'leaseContractLength', 'Value': f'{term_years}yr'},
                {'Type': 'TERM_MATCH', 'Field': 'purchaseOption', 'Value': payment_option}
            ]
            
            ri_pricing = self.get_service_pricing('AmazonEC2', region, ri_filters, PricingModel.RESERVED)
            
            if not od_pricing or not ri_pricing:
                raise Exception("Unable to retrieve complete pricing data")
            
            # Calculate comprehensive RI analysis
            ri_analysis = self._calculate_ri_analysis(
                od_pricing, ri_pricing, instance_type, region, term_years, payment_option, offering_class
            )
            
            # Add break-even analysis
            ri_analysis['breakEvenAnalysis'] = self._calculate_ri_break_even(ri_analysis)
            
            # Add risk assessment
            ri_analysis['riskAssessment'] = self._assess_ri_risk(ri_analysis, term_years, offering_class)
            
            return ri_analysis
            
        except Exception as e:
            logger.error(f"Failed to get RI pricing: {e}")
            return self._get_fallback_ri_pricing(instance_type, region, term_years, payment_option)
    
    def get_savings_plans_pricing(self, compute_type: str = 'EC2Instance',
                                commitment_amount: float = 100.0,
                                term_years: int = 1,
                                payment_option: str = 'No Upfront') -> Dict[str, Any]:
        """
        Get Savings Plans pricing analysis.
        
        Args:
            compute_type: Compute type ('EC2Instance', 'Fargate', 'Lambda')
            commitment_amount: Hourly commitment amount in USD
            term_years: Commitment term (1 or 3 years)
            payment_option: Payment option ('No Upfront', 'Partial Upfront', 'All Upfront')
            
        Returns:
            Savings Plans pricing analysis
        """
        logger.info(f"Getting Savings Plans pricing for {compute_type} (${commitment_amount}/hr, {term_years}yr)")
        
        try:
            # Calculate Savings Plans analysis (simplified implementation)
            sp_analysis = self._calculate_savings_plans_analysis(
                compute_type, commitment_amount, term_years, payment_option
            )
            
            # Add flexibility analysis
            sp_analysis['flexibilityAnalysis'] = self._analyze_sp_flexibility(compute_type, term_years)
            
            # Add coverage recommendations
            sp_analysis['coverageRecommendations'] = self._generate_sp_coverage_recommendations(
                commitment_amount, compute_type
            )
            
            return sp_analysis
            
        except Exception as e:
            logger.error(f"Failed to get Savings Plans pricing: {e}")
            return self._get_fallback_sp_pricing(compute_type, commitment_amount, term_years)
    
    def get_spot_pricing_analysis(self, instance_type: str, region: str,
                                availability_zone: Optional[str] = None,
                                days_back: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive Spot Instance pricing analysis.
        
        Args:
            instance_type: EC2 instance type
            region: AWS region
            availability_zone: Specific AZ (optional)
            days_back: Number of days of history to analyze
            
        Returns:
            Comprehensive Spot pricing analysis
        """
        logger.info(f"Getting Spot pricing analysis for {instance_type} in {region}")
        
        try:
            # Get EC2 client for Spot pricing history
            ec2_client = self.aws_config.get_client('ec2', region)
            
            # Calculate date range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=days_back)
            
            # Get Spot price history
            spot_filters = [
                {'Name': 'instance-type', 'Values': [instance_type]},
                {'Name': 'product-description', 'Values': ['Linux/UNIX']}
            ]
            
            if availability_zone:
                spot_filters.append({'Name': 'availability-zone', 'Values': [availability_zone]})
            
            spot_response = self.aws_config.execute_with_retry(
                ec2_client.describe_spot_price_history,
                'ec2',
                Filters=spot_filters,
                StartTime=start_time,
                EndTime=end_time,
                MaxResults=1000
            )
            
            # Get On-Demand pricing for comparison
            od_filters = [
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type}
            ]
            od_pricing = self.get_service_pricing('AmazonEC2', region, od_filters, PricingModel.ON_DEMAND)
            
            # Analyze Spot pricing data
            spot_analysis = self._analyze_spot_pricing(
                spot_response, od_pricing, instance_type, region, days_back
            )
            
            # Add interruption risk analysis
            spot_analysis['interruptionRisk'] = self._analyze_interruption_risk(
                instance_type, region, availability_zone
            )
            
            # Add cost optimization recommendations
            spot_analysis['recommendations'] = self._generate_spot_recommendations(spot_analysis)
            
            return spot_analysis
            
        except Exception as e:
            logger.error(f"Failed to get Spot pricing analysis: {e}")
            return self._get_fallback_spot_analysis(instance_type, region)
    
    def convert_currency(self, amount: float, from_currency: Currency,
                        to_currency: Currency, rate_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert amount between currencies with historical rate support.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency
            rate_date: Specific date for exchange rate (YYYY-MM-DD, optional)
            
        Returns:
            Currency conversion result with rate information
        """
        if from_currency == to_currency:
            return {
                'originalAmount': amount,
                'convertedAmount': amount,
                'fromCurrency': from_currency.value,
                'toCurrency': to_currency.value,
                'exchangeRate': 1.0,
                'rateDate': rate_date or datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                'conversionTimestamp': datetime.now(timezone.utc).isoformat()
            }
        
        try:
            # Get exchange rate
            exchange_rate = self._get_exchange_rate(from_currency, to_currency, rate_date)
            
            # Convert amount
            converted_amount = amount * exchange_rate
            
            # Calculate conversion fees (mock - typically 0.5-2%)
            conversion_fee_rate = 0.01  # 1%
            conversion_fee = converted_amount * conversion_fee_rate
            final_amount = converted_amount - conversion_fee
            
            return {
                'originalAmount': amount,
                'convertedAmount': round(converted_amount, 2),
                'finalAmount': round(final_amount, 2),
                'conversionFee': round(conversion_fee, 2),
                'conversionFeeRate': conversion_fee_rate,
                'fromCurrency': from_currency.value,
                'toCurrency': to_currency.value,
                'exchangeRate': exchange_rate,
                'rateDate': rate_date or datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                'conversionTimestamp': datetime.now(timezone.utc).isoformat(),
                'rateSource': 'mock_exchange_api'
            }
            
        except Exception as e:
            logger.error(f"Currency conversion failed: {e}")
            return {
                'originalAmount': amount,
                'convertedAmount': amount,
                'fromCurrency': from_currency.value,
                'toCurrency': to_currency.value,
                'exchangeRate': 1.0,
                'error': str(e),
                'conversionTimestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_pricing_trends(self, service_code: str, instance_type: str,
                         region: str, months_back: int = 12) -> Dict[str, Any]:
        """
        Analyze pricing trends over time.
        
        Args:
            service_code: AWS service code
            instance_type: Instance type to analyze
            region: AWS region
            months_back: Number of months to analyze
            
        Returns:
            Pricing trend analysis
        """
        logger.info(f"Analyzing pricing trends for {instance_type} in {region}")
        
        try:
            # Get historical pricing data (mock implementation)
            historical_data = self._get_historical_pricing_data(
                service_code, instance_type, region, months_back
            )
            
            # Analyze trends
            trend_analysis = self._analyze_pricing_trends(historical_data)
            
            # Generate forecast
            price_forecast = self._forecast_pricing(historical_data, months_ahead=3)
            
            return {
                'serviceCode': service_code,
                'instanceType': instance_type,
                'region': region,
                'analysisPeriod': f'{months_back} months',
                'historicalData': historical_data,
                'trendAnalysis': trend_analysis,
                'priceForecast': price_forecast,
                'analysisTimestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze pricing trends: {e}")
            return {'error': str(e), 'analysisTimestamp': datetime.now(timezone.utc).isoformat()}
    
    def calculate_total_cost_of_ownership(self, instance_type: str, region: str,
                                        usage_hours_per_month: float = 730,
                                        months: int = 12,
                                        include_storage: bool = True,
                                        include_network: bool = True) -> Dict[str, Any]:
        """
        Calculate Total Cost of Ownership (TCO) for different pricing models.
        
        Args:
            instance_type: EC2 instance type
            region: AWS region
            usage_hours_per_month: Expected usage hours per month
            months: Analysis period in months
            include_storage: Include EBS storage costs
            include_network: Include data transfer costs
            
        Returns:
            Comprehensive TCO analysis
        """
        logger.info(f"Calculating TCO for {instance_type} in {region} over {months} months")
        
        try:
            # Get pricing for different models
            od_pricing = self.get_service_pricing('AmazonEC2', region, 
                [{'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type}],
                PricingModel.ON_DEMAND)
            
            ri_pricing = self.get_reserved_instance_pricing(instance_type, region, 1)
            spot_analysis = self.get_spot_pricing_analysis(instance_type, region)
            
            # Calculate TCO for each model
            tco_analysis = {}
            
            # On-Demand TCO
            if od_pricing and 'hourlyPrice' in od_pricing:
                tco_analysis['onDemand'] = self._calculate_model_tco(
                    od_pricing['hourlyPrice'], usage_hours_per_month, months,
                    'On-Demand', include_storage, include_network
                )
            
            # Reserved Instance TCO
            if ri_pricing and 'reservedHourlyPrice' in ri_pricing:
                tco_analysis['reservedInstance'] = self._calculate_ri_tco(
                    ri_pricing, usage_hours_per_month, months,
                    include_storage, include_network
                )
            
            # Spot Instance TCO
            if spot_analysis and 'averageSpotPrice' in spot_analysis:
                tco_analysis['spotInstance'] = self._calculate_spot_tco(
                    spot_analysis, usage_hours_per_month, months,
                    include_storage, include_network
                )
            
            # Generate recommendations
            recommendations = self._generate_tco_recommendations(tco_analysis)
            
            return {
                'instanceType': instance_type,
                'region': region,
                'analysisParameters': {
                    'usageHoursPerMonth': usage_hours_per_month,
                    'analysisMonths': months,
                    'includeStorage': include_storage,
                    'includeNetwork': include_network
                },
                'tcoAnalysis': tco_analysis,
                'recommendations': recommendations,
                'calculationTimestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate TCO: {e}")
            return {'error': str(e), 'calculationTimestamp': datetime.now(timezone.utc).isoformat()}
    
    # Private helper methods
    
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
        
        elif service_code == 'AmazonRDS':
            filters.extend([
                {'Type': 'TERM_MATCH', 'Field': 'deploymentOption', 'Value': 'Single-AZ'},
                {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': 'MySQL'}
            ])
        
        # Add additional filters
        if additional_filters:
            filters.extend(additional_filters)
        
        return filters
    
    def _parse_pricing_response(self, response: Dict[str, Any], service_code: str,
                              region: str, pricing_model: PricingModel) -> Dict[str, Any]:
        """Parse AWS Price List API response with enhanced data extraction."""
        try:
            price_list = response.get('PriceList', [])
            
            if not price_list:
                logger.warning(f"No pricing data found for {service_code} in {region}")
                return {}
            
            # Parse first pricing item (most relevant)
            pricing_item = json.loads(price_list[0])
            
            # Extract comprehensive pricing information
            product = pricing_item.get('product', {})
            terms = pricing_item.get('terms', {})
            
            # Get product attributes
            attributes = product.get('attributes', {})
            
            # Extract pricing based on model
            pricing_data = {
                'serviceCode': service_code,
                'region': region,
                'pricingModel': pricing_model.value,
                'productAttributes': attributes,
                'currency': 'USD',
                'lastUpdated': datetime.now(timezone.utc).isoformat()
            }
            
            # Parse On-Demand pricing
            on_demand_terms = terms.get('OnDemand', {})
            if on_demand_terms:
                pricing_data.update(self._extract_on_demand_pricing(on_demand_terms))
            
            # Parse Reserved pricing
            reserved_terms = terms.get('Reserved', {})
            if reserved_terms:
                pricing_data.update(self._extract_reserved_pricing(reserved_terms))
            
            return pricing_data
            
        except Exception as e:
            logger.error(f"Failed to parse pricing response: {e}")
            return {}
    
    def _extract_on_demand_pricing(self, on_demand_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Extract On-Demand pricing from terms."""
        pricing_data = {}
        
        for term_key, term_data in on_demand_terms.items():
            price_dimensions = term_data.get('priceDimensions', {})
            
            for dim_key, dim_data in price_dimensions.items():
                price_per_unit = dim_data.get('pricePerUnit', {})
                
                if 'USD' in price_per_unit:
                    pricing_data.update({
                        'hourlyPrice': float(price_per_unit['USD']),
                        'priceUnit': dim_data.get('unit', 'Hrs'),
                        'description': dim_data.get('description', ''),
                        'beginRange': dim_data.get('beginRange', '0'),
                        'endRange': dim_data.get('endRange', 'Inf')
                    })
                    break
            
            if 'hourlyPrice' in pricing_data:
                break
        
        return pricing_data
    
    def _extract_reserved_pricing(self, reserved_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Reserved Instance pricing from terms."""
        pricing_data = {}
        
        for term_key, term_data in reserved_terms.items():
            term_attributes = term_data.get('termAttributes', {})
            price_dimensions = term_data.get('priceDimensions', {})
            
            # Extract term information
            pricing_data.update({
                'leaseContractLength': term_attributes.get('LeaseContractLength'),
                'offeringClass': term_attributes.get('OfferingClass'),
                'purchaseOption': term_attributes.get('PurchaseOption')
            })
            
            # Extract pricing dimensions
            for dim_key, dim_data in price_dimensions.items():
                price_per_unit = dim_data.get('pricePerUnit', {})
                description = dim_data.get('description', '').lower()
                
                if 'USD' in price_per_unit:
                    price_value = float(price_per_unit['USD'])
                    
                    if 'upfront' in description:
                        pricing_data['upfrontCost'] = price_value
                    elif 'hourly' in description or dim_data.get('unit') == 'Hrs':
                        pricing_data['reservedHourlyPrice'] = price_value
        
        return pricing_data
    
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
            'eu-north-1': 'Europe (Stockholm)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
            'ap-northeast-2': 'Asia Pacific (Seoul)',
            'ap-south-1': 'Asia Pacific (Mumbai)',
            'ca-central-1': 'Canada (Central)',
            'sa-east-1': 'South America (São Paulo)'
        }
        return location_map.get(region, region)
    
    def _get_regional_pricing_comparison(self, service_code: str,
                                       filters: Optional[List[Dict[str, Any]]],
                                       pricing_model: PricingModel) -> Dict[str, Any]:
        """Get pricing comparison across major regions."""
        major_regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
        regional_prices = {}
        
        for region in major_regions:
            try:
                # Prevent recursion by not including regional comparison in nested calls
                pricing_data = self.get_service_pricing(service_code, region, filters, pricing_model, include_regional_comparison=False)
                if pricing_data and 'hourlyPrice' in pricing_data:
                    regional_prices[region] = pricing_data['hourlyPrice']
            except Exception as e:
                logger.warning(f"Failed to get pricing for {region}: {e}")
                continue
        
        if not regional_prices:
            return {}
        
        # Find cheapest and most expensive regions
        cheapest_region = min(regional_prices.keys(), key=lambda r: regional_prices[r])
        most_expensive_region = max(regional_prices.keys(), key=lambda r: regional_prices[r])
        
        return {
            'regionalPrices': regional_prices,
            'cheapestRegion': cheapest_region,
            'mostExpensiveRegion': most_expensive_region,
            'maxSavingsPercentage': ((regional_prices[most_expensive_region] - regional_prices[cheapest_region]) / 
                                   regional_prices[most_expensive_region] * 100) if regional_prices[most_expensive_region] > 0 else 0
        }
    
    def _convert_to_multiple_currencies(self, usd_amount: float) -> Dict[str, Any]:
        """Convert USD amount to multiple currencies."""
        currencies = [Currency.EUR, Currency.GBP, Currency.JPY, Currency.CAD, Currency.AUD]
        conversions = {}
        
        for currency in currencies:
            try:
                conversion = self.convert_currency(usd_amount, Currency.USD, currency)
                conversions[currency.value] = {
                    'amount': conversion['convertedAmount'],
                    'rate': conversion['exchangeRate']
                }
            except Exception as e:
                logger.warning(f"Failed to convert to {currency.value}: {e}")
                continue
        
        return conversions
    
    def _calculate_regional_metrics(self, pricing_data: Dict[str, Any], hourly_price: float,
                                  base_price: float, region: str) -> Dict[str, Any]:
        """Calculate comprehensive regional pricing metrics."""
        # Calculate price differences
        price_difference = hourly_price - base_price
        price_difference_percentage = (price_difference / base_price * 100) if base_price > 0 else 0
        
        # Calculate various time period costs
        daily_price = hourly_price * 24
        weekly_price = daily_price * 7
        monthly_price = hourly_price * 730  # Average hours per month
        annual_price = monthly_price * 12
        
        return {
            'hourlyPrice': hourly_price,
            'dailyPrice': daily_price,
            'weeklyPrice': weekly_price,
            'monthlyPrice': monthly_price,
            'annualPrice': annual_price,
            'priceDifference': price_difference,
            'priceDifferencePercentage': price_difference_percentage,
            'currency': pricing_data.get('currency', 'USD'),
            'priceUnit': pricing_data.get('priceUnit', 'Hrs'),
            'lastUpdated': pricing_data.get('lastUpdated'),
            'productAttributes': pricing_data.get('productAttributes', {})
        }
    
    def _generate_comparison_analysis(self, regional_pricing: Dict[str, Any],
                                    instance_type: str, service_code: str) -> Dict[str, Any]:
        """Generate comprehensive comparison analysis."""
        if not regional_pricing:
            return {}
        
        # Extract prices for analysis
        prices = [(region, data['hourlyPrice']) for region, data in regional_pricing.items()]
        prices.sort(key=lambda x: x[1])
        
        cheapest_region, cheapest_price = prices[0]
        most_expensive_region, most_expensive_price = prices[-1]
        
        # Calculate statistics
        all_prices = [price for _, price in prices]
        avg_price = sum(all_prices) / len(all_prices)
        price_variance = sum((price - avg_price) ** 2 for price in all_prices) / len(all_prices)
        price_std_dev = price_variance ** 0.5
        
        # Calculate potential savings
        max_savings_percentage = ((most_expensive_price - cheapest_price) / most_expensive_price * 100) if most_expensive_price > 0 else 0
        max_monthly_savings = (most_expensive_price - cheapest_price) * 730
        max_annual_savings = max_monthly_savings * 12
        
        return {
            'cheapestRegion': cheapest_region,
            'cheapestPrice': cheapest_price,
            'mostExpensiveRegion': most_expensive_region,
            'mostExpensivePrice': most_expensive_price,
            'averagePrice': avg_price,
            'priceStandardDeviation': price_std_dev,
            'maxSavingsPercentage': max_savings_percentage,
            'maxMonthlySavings': max_monthly_savings,
            'maxAnnualSavings': max_annual_savings,
            'priceSpread': most_expensive_price - cheapest_price,
            'regionCount': len(regional_pricing),
            'recommendations': self._generate_regional_recommendations(
                cheapest_region, max_savings_percentage, max_annual_savings
            )
        }
    
    def _generate_regional_recommendations(self, cheapest_region: str,
                                         max_savings_percentage: float,
                                         max_annual_savings: float) -> List[Dict[str, Any]]:
        """Generate regional pricing recommendations."""
        recommendations = []
        
        if max_savings_percentage > 20:
            recommendations.append({
                'type': 'REGION_MIGRATION',
                'priority': 'HIGH',
                'description': f'Consider migrating to {cheapest_region} for {max_savings_percentage:.1f}% cost savings',
                'potentialAnnualSavings': max_annual_savings,
                'action': f'Evaluate migration feasibility to {cheapest_region}'
            })
        elif max_savings_percentage > 10:
            recommendations.append({
                'type': 'REGION_EVALUATION',
                'priority': 'MEDIUM',
                'description': f'Evaluate {cheapest_region} for {max_savings_percentage:.1f}% potential savings',
                'potentialAnnualSavings': max_annual_savings,
                'action': f'Assess latency and compliance requirements for {cheapest_region}'
            })
        
        return recommendations
    
    def _calculate_ri_analysis(self, od_pricing: Dict[str, Any], ri_pricing: Dict[str, Any],
                             instance_type: str, region: str, term_years: int,
                             payment_option: str, offering_class: str) -> Dict[str, Any]:
        """Calculate comprehensive RI analysis."""
        od_hourly_price = od_pricing.get('hourlyPrice', 0)
        ri_hourly_price = ri_pricing.get('reservedHourlyPrice', od_hourly_price * 0.7)
        ri_upfront_cost = ri_pricing.get('upfrontCost', 0)
        
        # Calculate costs over term
        term_hours = term_years * 365 * 24
        od_total_cost = od_hourly_price * term_hours
        ri_total_cost = (ri_hourly_price * term_hours) + ri_upfront_cost
        
        # Calculate savings
        total_savings = od_total_cost - ri_total_cost
        savings_percentage = (total_savings / od_total_cost * 100) if od_total_cost > 0 else 0
        
        # Calculate monthly metrics
        monthly_od_cost = od_hourly_price * 730
        monthly_ri_cost = ri_hourly_price * 730
        monthly_savings = monthly_od_cost - monthly_ri_cost
        
        # Calculate break-even period
        break_even_months = (ri_upfront_cost / monthly_savings) if monthly_savings > 0 else float('inf')
        
        return {
            'instanceType': instance_type,
            'region': region,
            'termYears': term_years,
            'paymentOption': payment_option,
            'offeringClass': offering_class,
            'onDemandHourlyPrice': od_hourly_price,
            'reservedHourlyPrice': ri_hourly_price,
            'upfrontCost': ri_upfront_cost,
            'onDemandTotalCost': od_total_cost,
            'reservedTotalCost': ri_total_cost,
            'totalSavings': total_savings,
            'savingsPercentage': savings_percentage,
            'monthlyOnDemandCost': monthly_od_cost,
            'monthlyReservedCost': monthly_ri_cost,
            'monthlySavings': monthly_savings,
            'breakEvenMonths': break_even_months,
            'currency': 'USD',
            'calculationTimestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_ri_break_even(self, ri_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed break-even analysis for RI."""
        upfront_cost = ri_analysis.get('upfrontCost', 0)
        monthly_savings = ri_analysis.get('monthlySavings', 0)
        term_years = ri_analysis.get('termYears', 1)
        
        if monthly_savings <= 0:
            return {
                'breakEvenAchievable': False,
                'reason': 'No monthly savings with current pricing'
            }
        
        break_even_months = upfront_cost / monthly_savings
        break_even_achievable = break_even_months <= (term_years * 12)
        
        return {
            'breakEvenAchievable': break_even_achievable,
            'breakEvenMonths': break_even_months,
            'breakEvenDate': (datetime.now() + timedelta(days=break_even_months * 30)).strftime('%Y-%m-%d'),
            'remainingTermAfterBreakEven': max(0, (term_years * 12) - break_even_months),
            'totalSavingsAfterBreakEven': max(0, ((term_years * 12) - break_even_months) * monthly_savings)
        }
    
    def _assess_ri_risk(self, ri_analysis: Dict[str, Any], term_years: int, offering_class: str) -> Dict[str, Any]:
        """Assess risk factors for RI purchase."""
        break_even_months = ri_analysis.get('breakEvenMonths', float('inf'))
        savings_percentage = ri_analysis.get('savingsPercentage', 0)
        
        # Calculate risk score (0-100, lower is better)
        risk_score = 0
        risk_factors = []
        
        # Term length risk
        if term_years == 3:
            risk_score += 30
            risk_factors.append('Long-term commitment (3 years)')
        elif term_years == 1:
            risk_score += 10
            risk_factors.append('Medium-term commitment (1 year)')
        
        # Break-even risk
        if break_even_months > (term_years * 12):
            risk_score += 40
            risk_factors.append('Break-even not achievable within term')
        elif break_even_months > (term_years * 6):
            risk_score += 20
            risk_factors.append('Late break-even (>50% of term)')
        
        # Savings risk
        if savings_percentage < 10:
            risk_score += 20
            risk_factors.append('Low savings percentage')
        elif savings_percentage < 20:
            risk_score += 10
            risk_factors.append('Moderate savings percentage')
        
        # Flexibility risk
        if offering_class == 'standard':
            risk_score += 10
            risk_factors.append('Limited flexibility (standard class)')
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = 'HIGH'
        elif risk_score >= 40:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'riskLevel': risk_level,
            'riskScore': risk_score,
            'riskFactors': risk_factors,
            'recommendation': self._get_ri_risk_recommendation(risk_level, risk_score)
        }
    
    def _get_ri_risk_recommendation(self, risk_level: str, risk_score: int) -> str:
        """Get RI recommendation based on risk assessment."""
        if risk_level == 'HIGH':
            return 'High risk - consider On-Demand or Spot instances instead'
        elif risk_level == 'MEDIUM':
            return 'Moderate risk - evaluate carefully and consider shorter term'
        else:
            return 'Low risk - good candidate for Reserved Instance purchase'
    
    def _initialize_exchange_rates(self) -> Dict[str, float]:
        """Initialize mock exchange rates."""
        return {
            'USD_EUR': 0.85,
            'USD_GBP': 0.75,
            'USD_JPY': 110.0,
            'USD_CAD': 1.25,
            'USD_AUD': 1.35,
            'EUR_USD': 1.18,
            'GBP_USD': 1.33,
            'JPY_USD': 0.009,
            'CAD_USD': 0.80,
            'AUD_USD': 0.74
        }
    
    def _get_exchange_rate(self, from_currency: Currency, to_currency: Currency,
                          rate_date: Optional[str] = None) -> float:
        """Get exchange rate between currencies."""
        rate_key = f"{from_currency.value}_{to_currency.value}"
        return self.exchange_rates.get(rate_key, 1.0)
    
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
                'c5.large': 0.085,
                'r5.large': 0.126
            },
            'AmazonRDS': {
                'db.t3.micro': 0.017,
                'db.t3.small': 0.034,
                'db.m5.large': 0.192
            }
        }
        
        base_price = fallback_prices.get(service_code, {}).get('t3.medium', 0.05)
        
        return {
            'hourlyPrice': base_price,
            'currency': 'USD',
            'priceUnit': 'Hrs',
            'serviceCode': service_code,
            'region': region,
            'pricingModel': pricing_model.value,
            'lastUpdated': datetime.now(timezone.utc).isoformat(),
            'fallback': True
        }
    
    # Additional helper methods for Savings Plans, Spot analysis, TCO calculation, etc.
    
    def _calculate_savings_plans_analysis(self, compute_type: str, commitment_amount: float,
                                        term_years: int, payment_option: str) -> Dict[str, Any]:
        """Calculate Savings Plans analysis (simplified implementation)."""
        # Mock Savings Plans discount rates
        discount_rates = {
            1: {'EC2Instance': 0.17, 'Fargate': 0.20, 'Lambda': 0.17},
            3: {'EC2Instance': 0.28, 'Fargate': 0.35, 'Lambda': 0.28}
        }
        
        discount_rate = discount_rates.get(term_years, {}).get(compute_type, 0.15)
        
        # Calculate savings
        on_demand_equivalent = commitment_amount / (1 - discount_rate)
        annual_commitment = commitment_amount * 8760  # Hours per year
        annual_savings = annual_commitment * discount_rate
        
        return {
            'computeType': compute_type,
            'commitmentAmount': commitment_amount,
            'termYears': term_years,
            'paymentOption': payment_option,
            'discountRate': discount_rate,
            'onDemandEquivalent': on_demand_equivalent,
            'annualCommitment': annual_commitment,
            'annualSavings': annual_savings,
            'totalSavings': annual_savings * term_years,
            'currency': 'USD',
            'calculationTimestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _analyze_sp_flexibility(self, compute_type: str, term_years: int) -> Dict[str, Any]:
        """Analyze Savings Plans flexibility."""
        flexibility_score = 100  # Start with maximum flexibility
        
        # Reduce score based on term length
        if term_years == 3:
            flexibility_score -= 30
        elif term_years == 1:
            flexibility_score -= 10
        
        # Compute type flexibility
        if compute_type == 'EC2Instance':
            flexibility_features = [
                'Instance family flexibility',
                'Instance size flexibility',
                'Operating system flexibility',
                'Tenancy flexibility'
            ]
        elif compute_type == 'Fargate':
            flexibility_features = [
                'CPU and memory flexibility',
                'Operating system flexibility'
            ]
        else:
            flexibility_features = ['Limited flexibility']
            flexibility_score -= 20
        
        return {
            'flexibilityScore': flexibility_score,
            'flexibilityLevel': 'HIGH' if flexibility_score >= 80 else 'MEDIUM' if flexibility_score >= 60 else 'LOW',
            'flexibilityFeatures': flexibility_features
        }
    
    def _generate_sp_coverage_recommendations(self, commitment_amount: float, compute_type: str) -> List[Dict[str, Any]]:
        """Generate Savings Plans coverage recommendations."""
        recommendations = []
        
        if commitment_amount < 50:
            recommendations.append({
                'type': 'INCREASE_COMMITMENT',
                'priority': 'MEDIUM',
                'description': 'Consider increasing commitment for better savings',
                'suggestedAmount': 100
            })
        elif commitment_amount > 1000:
            recommendations.append({
                'type': 'EVALUATE_COMMITMENT',
                'priority': 'HIGH',
                'description': 'High commitment - ensure utilization monitoring',
                'action': 'Monitor utilization closely'
            })
        
        return recommendations
    
    def _analyze_spot_pricing(self, spot_response: Dict[str, Any], od_pricing: Dict[str, Any],
                            instance_type: str, region: str, days_back: int) -> Dict[str, Any]:
        """Analyze Spot pricing data."""
        spot_prices = spot_response.get('SpotPriceHistory', [])
        
        if not spot_prices:
            return {'error': 'No Spot pricing data available'}
        
        # Extract price values
        prices = [float(item['SpotPrice']) for item in spot_prices]
        
        # Calculate statistics
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        # Calculate savings vs On-Demand
        od_price = od_pricing.get('hourlyPrice', 0) if od_pricing else avg_price * 3
        avg_savings_percentage = ((od_price - avg_price) / od_price * 100) if od_price > 0 else 0
        
        return {
            'instanceType': instance_type,
            'region': region,
            'analysisWindow': f'{days_back} days',
            'averageSpotPrice': avg_price,
            'minimumSpotPrice': min_price,
            'maximumSpotPrice': max_price,
            'onDemandPrice': od_price,
            'averageSavingsPercentage': avg_savings_percentage,
            'priceVolatility': (max_price - min_price) / avg_price if avg_price > 0 else 0,
            'dataPoints': len(prices),
            'currency': 'USD'
        }
    
    def _analyze_interruption_risk(self, instance_type: str, region: str,
                                 availability_zone: Optional[str] = None) -> Dict[str, Any]:
        """Analyze Spot instance interruption risk."""
        # Mock interruption rates based on instance type and region
        base_interruption_rates = {
            't3': 2.0,   # Low interruption
            'm5': 5.0,   # Medium interruption
            'c5': 8.0,   # Higher interruption (compute optimized)
            'r5': 6.0,   # Medium-high interruption
            'p3': 15.0,  # High interruption (GPU instances)
            'x1': 12.0   # High interruption (memory optimized)
        }
        
        instance_family = instance_type.split('.')[0]
        base_rate = base_interruption_rates.get(instance_family, 7.0)
        
        # Adjust for region (some regions have higher demand)
        region_multipliers = {
            'us-east-1': 1.2,
            'us-west-2': 1.0,
            'eu-west-1': 1.1,
            'ap-southeast-1': 1.3
        }
        
        region_multiplier = region_multipliers.get(region, 1.0)
        estimated_interruption_rate = base_rate * region_multiplier
        
        # Determine risk level
        if estimated_interruption_rate < 5:
            risk_level = 'LOW'
        elif estimated_interruption_rate < 10:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'
        
        return {
            'estimatedInterruptionRate': estimated_interruption_rate,
            'riskLevel': risk_level,
            'instanceFamily': instance_family,
            'regionFactor': region_multiplier,
            'recommendations': self._get_interruption_recommendations(risk_level, estimated_interruption_rate)
        }
    
    def _get_interruption_recommendations(self, risk_level: str, interruption_rate: float) -> List[str]:
        """Get recommendations based on interruption risk."""
        recommendations = []
        
        if risk_level == 'HIGH':
            recommendations.extend([
                'Use Spot Fleet with multiple instance types',
                'Implement robust checkpointing',
                'Consider mixed On-Demand/Spot strategy'
            ])
        elif risk_level == 'MEDIUM':
            recommendations.extend([
                'Monitor interruption notifications',
                'Use diversified Spot strategy',
                'Implement graceful shutdown procedures'
            ])
        else:
            recommendations.extend([
                'Good candidate for Spot instances',
                'Monitor for cost optimization opportunities'
            ])
        
        return recommendations
    
    def _generate_spot_recommendations(self, spot_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Spot instance recommendations."""
        recommendations = []
        
        savings_percentage = spot_analysis.get('averageSavingsPercentage', 0)
        interruption_risk = spot_analysis.get('interruptionRisk', {})
        risk_level = interruption_risk.get('riskLevel', 'MEDIUM')
        
        if savings_percentage > 50 and risk_level in ['LOW', 'MEDIUM']:
            recommendations.append({
                'type': 'USE_SPOT_INSTANCES',
                'priority': 'HIGH',
                'description': f'Excellent Spot candidate with {savings_percentage:.1f}% savings',
                'expectedSavings': savings_percentage
            })
        elif savings_percentage > 30:
            recommendations.append({
                'type': 'EVALUATE_SPOT_USAGE',
                'priority': 'MEDIUM',
                'description': f'Consider Spot instances for {savings_percentage:.1f}% savings',
                'considerations': ['Monitor interruption patterns', 'Implement fault tolerance']
            })
        
        return recommendations
    
    def _get_historical_pricing_data(self, service_code: str, instance_type: str,
                                   region: str, months_back: int) -> List[Dict[str, Any]]:
        """Get historical pricing data (mock implementation)."""
        # Mock historical pricing data with slight variations
        base_price = 0.1  # Base hourly price
        historical_data = []
        
        for i in range(months_back):
            # Add some realistic price variation
            price_variation = 1 + (0.05 * (i % 3 - 1))  # ±5% variation
            monthly_price = base_price * price_variation
            
            date = datetime.now() - timedelta(days=30 * i)
            
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'hourlyPrice': round(monthly_price, 4),
                'monthlyPrice': round(monthly_price * 730, 2),
                'priceChange': round((monthly_price - base_price) / base_price * 100, 2)
            })
        
        return list(reversed(historical_data))  # Chronological order
    
    def _analyze_pricing_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze pricing trends from historical data."""
        if len(historical_data) < 2:
            return {'trend': 'insufficient_data'}
        
        prices = [data['hourlyPrice'] for data in historical_data]
        
        # Calculate trend
        n = len(prices)
        x_values = list(range(n))
        
        # Simple linear regression
        x_mean = sum(x_values) / n
        y_mean = sum(prices) / n
        
        numerator = sum((x_values[i] - x_mean) * (prices[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Determine trend direction
        if slope > 0.001:
            trend = 'increasing'
        elif slope < -0.001:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # Calculate volatility
        price_changes = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
        volatility = sum(price_changes) / len(price_changes) if price_changes else 0
        
        return {
            'trend': trend,
            'slope': slope,
            'volatility': volatility,
            'priceRange': {
                'min': min(prices),
                'max': max(prices),
                'average': y_mean
            },
            'totalPriceChange': ((prices[-1] - prices[0]) / prices[0] * 100) if prices[0] > 0 else 0
        }
    
    def _forecast_pricing(self, historical_data: List[Dict[str, Any]], months_ahead: int = 3) -> List[Dict[str, Any]]:
        """Generate pricing forecast based on historical data."""
        if len(historical_data) < 3:
            return []
        
        prices = [data['hourlyPrice'] for data in historical_data]
        
        # Simple trend-based forecast
        recent_trend = (prices[-1] - prices[-3]) / 2  # Average change over last 2 months
        
        forecast = []
        last_price = prices[-1]
        
        for i in range(months_ahead):
            forecasted_price = last_price + (recent_trend * (i + 1))
            forecasted_price = max(0.001, forecasted_price)  # Ensure positive price
            
            forecast_date = datetime.now() + timedelta(days=30 * (i + 1))
            
            forecast.append({
                'date': forecast_date.strftime('%Y-%m-%d'),
                'forecastedHourlyPrice': round(forecasted_price, 4),
                'forecastedMonthlyPrice': round(forecasted_price * 730, 2),
                'confidence': max(0.5, 0.9 - (i * 0.1))  # Decreasing confidence
            })
        
        return forecast
    
    def _calculate_model_tco(self, hourly_price: float, usage_hours_per_month: float,
                           months: int, model_name: str, include_storage: bool,
                           include_network: bool) -> Dict[str, Any]:
        """Calculate TCO for a specific pricing model."""
        # Base compute costs
        monthly_compute_cost = hourly_price * usage_hours_per_month
        total_compute_cost = monthly_compute_cost * months
        
        # Additional costs (mock estimates)
        monthly_storage_cost = 50.0 if include_storage else 0.0  # $50/month for EBS
        monthly_network_cost = 20.0 if include_network else 0.0  # $20/month for data transfer
        
        monthly_additional_costs = monthly_storage_cost + monthly_network_cost
        total_additional_costs = monthly_additional_costs * months
        
        total_tco = total_compute_cost + total_additional_costs
        
        return {
            'model': model_name,
            'hourlyPrice': hourly_price,
            'monthlyComputeCost': monthly_compute_cost,
            'monthlyStorageCost': monthly_storage_cost,
            'monthlyNetworkCost': monthly_network_cost,
            'monthlyTotalCost': monthly_compute_cost + monthly_additional_costs,
            'totalComputeCost': total_compute_cost,
            'totalAdditionalCosts': total_additional_costs,
            'totalTCO': total_tco,
            'currency': 'USD'
        }
    
    def _calculate_ri_tco(self, ri_pricing: Dict[str, Any], usage_hours_per_month: float,
                        months: int, include_storage: bool, include_network: bool) -> Dict[str, Any]:
        """Calculate TCO for Reserved Instances."""
        hourly_price = ri_pricing.get('reservedHourlyPrice', 0)
        upfront_cost = ri_pricing.get('upfrontCost', 0)
        
        # Base compute costs
        monthly_compute_cost = hourly_price * usage_hours_per_month
        total_compute_cost = (monthly_compute_cost * months) + upfront_cost
        
        # Additional costs
        monthly_storage_cost = 50.0 if include_storage else 0.0
        monthly_network_cost = 20.0 if include_network else 0.0
        monthly_additional_costs = monthly_storage_cost + monthly_network_cost
        total_additional_costs = monthly_additional_costs * months
        
        total_tco = total_compute_cost + total_additional_costs
        
        return {
            'model': 'Reserved Instance',
            'hourlyPrice': hourly_price,
            'upfrontCost': upfront_cost,
            'monthlyComputeCost': monthly_compute_cost,
            'monthlyStorageCost': monthly_storage_cost,
            'monthlyNetworkCost': monthly_network_cost,
            'monthlyTotalCost': monthly_compute_cost + monthly_additional_costs,
            'totalComputeCost': total_compute_cost,
            'totalAdditionalCosts': total_additional_costs,
            'totalTCO': total_tco,
            'currency': 'USD'
        }
    
    def _calculate_spot_tco(self, spot_analysis: Dict[str, Any], usage_hours_per_month: float,
                          months: int, include_storage: bool, include_network: bool) -> Dict[str, Any]:
        """Calculate TCO for Spot Instances."""
        avg_spot_price = spot_analysis.get('averageSpotPrice', 0)
        interruption_risk = spot_analysis.get('interruptionRisk', {}).get('estimatedInterruptionRate', 5.0)
        
        # Adjust for interruption risk (additional costs for handling interruptions)
        interruption_overhead = 0.1 * (interruption_risk / 100)  # 10% overhead per 100% interruption rate
        effective_hourly_price = avg_spot_price * (1 + interruption_overhead)
        
        # Base compute costs
        monthly_compute_cost = effective_hourly_price * usage_hours_per_month
        total_compute_cost = monthly_compute_cost * months
        
        # Additional costs
        monthly_storage_cost = 50.0 if include_storage else 0.0
        monthly_network_cost = 20.0 if include_network else 0.0
        monthly_additional_costs = monthly_storage_cost + monthly_network_cost
        total_additional_costs = monthly_additional_costs * months
        
        total_tco = total_compute_cost + total_additional_costs
        
        return {
            'model': 'Spot Instance',
            'averageSpotPrice': avg_spot_price,
            'effectiveHourlyPrice': effective_hourly_price,
            'interruptionOverhead': interruption_overhead,
            'monthlyComputeCost': monthly_compute_cost,
            'monthlyStorageCost': monthly_storage_cost,
            'monthlyNetworkCost': monthly_network_cost,
            'monthlyTotalCost': monthly_compute_cost + monthly_additional_costs,
            'totalComputeCost': total_compute_cost,
            'totalAdditionalCosts': total_additional_costs,
            'totalTCO': total_tco,
            'currency': 'USD'
        }
    
    def _generate_tco_recommendations(self, tco_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate TCO-based recommendations."""
        recommendations = []
        
        if not tco_analysis:
            return recommendations
        
        # Find the most cost-effective option
        models = list(tco_analysis.keys())
        if len(models) < 2:
            return recommendations
        
        # Sort by total TCO
        sorted_models = sorted(models, key=lambda m: tco_analysis[m].get('totalTCO', float('inf')))
        
        cheapest_model = sorted_models[0]
        most_expensive_model = sorted_models[-1]
        
        cheapest_tco = tco_analysis[cheapest_model]['totalTCO']
        most_expensive_tco = tco_analysis[most_expensive_model]['totalTCO']
        
        savings_amount = most_expensive_tco - cheapest_tco
        savings_percentage = (savings_amount / most_expensive_tco * 100) if most_expensive_tco > 0 else 0
        
        if savings_percentage > 20:
            recommendations.append({
                'type': 'PRICING_MODEL_OPTIMIZATION',
                'priority': 'HIGH',
                'description': f'Switch to {cheapest_model} for {savings_percentage:.1f}% TCO savings',
                'potentialSavings': savings_amount,
                'recommendedModel': cheapest_model,
                'currentModel': most_expensive_model
            })
        elif savings_percentage > 10:
            recommendations.append({
                'type': 'PRICING_MODEL_EVALUATION',
                'priority': 'MEDIUM',
                'description': f'Consider {cheapest_model} for {savings_percentage:.1f}% TCO savings',
                'potentialSavings': savings_amount,
                'recommendedModel': cheapest_model
            })
        
        return recommendations
    
    def _get_fallback_ri_pricing(self, instance_type: str, region: str,
                               term_years: int, payment_option: str) -> Dict[str, Any]:
        """Get fallback RI pricing when API calls fail."""
        # Mock RI discount rates
        discount_rates = {1: 0.30, 3: 0.50}  # 30% for 1yr, 50% for 3yr
        
        base_od_price = 0.1  # Fallback On-Demand price
        discount = discount_rates.get(term_years, 0.30)
        ri_hourly_price = base_od_price * (1 - discount)
        
        # Mock upfront costs based on payment option
        upfront_multipliers = {
            'No Upfront': 0.0,
            'Partial Upfront': 0.5,
            'All Upfront': 1.0
        }
        
        upfront_multiplier = upfront_multipliers.get(payment_option, 0.0)
        upfront_cost = base_od_price * term_years * 8760 * discount * upfront_multiplier
        
        return {
            'instanceType': instance_type,
            'region': region,
            'termYears': term_years,
            'paymentOption': payment_option,
            'onDemandHourlyPrice': base_od_price,
            'reservedHourlyPrice': ri_hourly_price,
            'upfrontCost': upfront_cost,
            'currency': 'USD',
            'calculationTimestamp': datetime.now(timezone.utc).isoformat(),
            'fallback': True
        }
    
    def _get_fallback_sp_pricing(self, compute_type: str, commitment_amount: float, term_years: int) -> Dict[str, Any]:
        """Get fallback Savings Plans pricing when API calls fail."""
        discount_rate = 0.20 if term_years == 1 else 0.35  # 20% for 1yr, 35% for 3yr
        
        return {
            'computeType': compute_type,
            'commitmentAmount': commitment_amount,
            'termYears': term_years,
            'discountRate': discount_rate,
            'annualSavings': commitment_amount * 8760 * discount_rate,
            'currency': 'USD',
            'calculationTimestamp': datetime.now(timezone.utc).isoformat(),
            'fallback': True
        }
    
    def _get_fallback_spot_analysis(self, instance_type: str, region: str) -> Dict[str, Any]:
        """Get fallback Spot analysis when API calls fail."""
        # Mock Spot pricing (typically 70% cheaper than On-Demand)
        base_od_price = 0.1
        avg_spot_price = base_od_price * 0.3
        
        return {
            'instanceType': instance_type,
            'region': region,
            'averageSpotPrice': avg_spot_price,
            'onDemandPrice': base_od_price,
            'averageSavingsPercentage': 70.0,
            'interruptionRisk': {
                'riskLevel': 'MEDIUM',
                'estimatedInterruptionRate': 7.0
            },
            'currency': 'USD',
            'fallback': True
        }