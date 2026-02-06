#!/usr/bin/env python3
"""
Cost Explorer Integration for Advanced FinOps Platform

Comprehensive AWS Cost Explorer integration that provides:
- Historical cost analysis with custom dimensions and filtering
- Cost and usage report generation with detailed breakdowns
- Cost trend analysis and forecasting with confidence intervals
- Cost anomaly detection integration with AWS Cost Anomaly Detection
- Multi-dimensional cost analysis across services, regions, and time periods

Requirements: 10.1, 5.1
"""

import logging
import statistics
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
import json
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class CostMetric(Enum):
    """Cost Explorer metrics."""
    UNBLENDED_COST = "UnblendedCost"
    BLENDED_COST = "BlendedCost"
    AMORTIZED_COST = "AmortizedCost"
    NET_UNBLENDED_COST = "NetUnblendedCost"
    NET_AMORTIZED_COST = "NetAmortizedCost"
    USAGE_QUANTITY = "UsageQuantity"


class Granularity(Enum):
    """Time granularity for cost analysis."""
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    HOURLY = "HOURLY"


class GroupByType(Enum):
    """Group by types for cost analysis."""
    DIMENSION = "DIMENSION"
    TAG = "TAG"
    COST_CATEGORY = "COST_CATEGORY"


class DimensionKey(Enum):
    """Available dimension keys for grouping and filtering."""
    SERVICE = "SERVICE"
    LINKED_ACCOUNT = "LINKED_ACCOUNT"
    REGION = "REGION"
    AVAILABILITY_ZONE = "AZ"
    INSTANCE_TYPE = "INSTANCE_TYPE"
    INSTANCE_TYPE_FAMILY = "INSTANCE_TYPE_FAMILY"
    USAGE_TYPE = "USAGE_TYPE"
    USAGE_TYPE_GROUP = "USAGE_TYPE_GROUP"
    OPERATION = "OPERATION"
    PLATFORM = "PLATFORM"
    TENANCY = "TENANCY"
    RECORD_TYPE = "RECORD_TYPE"
    RESOURCE_ID = "RESOURCE_ID"


class CostExplorer:
    """
    AWS Cost Explorer integration for comprehensive cost analysis and forecasting.
    
    Provides historical cost analysis, trend detection, forecasting with confidence intervals,
    and integration with AWS Cost Anomaly Detection service.
    
    Requirements: 10.1, 5.1
    """
    
    def __init__(self, aws_config=None, region: str = 'us-east-1', dry_run: bool = True):
        """
        Initialize Cost Explorer client.
        
        Args:
            aws_config: AWS configuration instance
            region: AWS region (Cost Explorer requires us-east-1)
            dry_run: Safety flag for testing
        """
        self.region = region
        self.aws_config = aws_config
        self.dry_run = dry_run
        self._client = None
        self._anomaly_client = None
        
        # Cost analysis configuration
        self.default_metrics = [CostMetric.UNBLENDED_COST.value]
        
        logger.info(f"Initialized Cost Explorer for region: {region}")
    
    @property
    def client(self):
        """Get Cost Explorer client (lazy initialization)."""
        if self._client is None:
            if self.aws_config:
                self._client = self.aws_config.get_cost_explorer_client()
            else:
                self._client = boto3.client('ce', region_name=self.region)
        return self._client
    
    @property
    def anomaly_client(self):
        """Get Cost Anomaly Detection client (lazy initialization)."""
        if self._anomaly_client is None:
            if self.aws_config:
                self._anomaly_client = self.aws_config.get_cost_anomaly_client()
            else:
                self._anomaly_client = boto3.client('ce', region_name=self.region)
        return self._anomaly_client 
    
    def get_cost_and_usage(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: Granularity = Granularity.DAILY,
        metrics: List[str] = None,
        group_by: List[Dict[str, str]] = None,
        filter_expression: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get cost and usage data for specified time period.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            granularity: Time granularity (DAILY, MONTHLY, HOURLY)
            metrics: List of metrics to retrieve
            group_by: Grouping dimensions
            filter_expression: Filtering criteria
            
        Returns:
            Dict containing cost and usage data with metadata
        """
        try:
            if metrics is None:
                metrics = self.default_metrics
            
            # Format dates for API
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Build request parameters
            params = {
                'TimePeriod': {
                    'Start': start_str,
                    'End': end_str
                },
                'Granularity': granularity.value,
                'Metrics': metrics
            }
            
            if group_by:
                params['GroupBy'] = group_by
            
            if filter_expression:
                params['Filter'] = filter_expression
            
            logger.info(f"Retrieving cost and usage data from {start_str} to {end_str}")
            
            if self.dry_run:
                logger.info("DRY_RUN: Would retrieve cost and usage data")
                return self._generate_mock_cost_data(start_date, end_date, granularity, metrics)
            
            response = self.client.get_cost_and_usage(**params)
            
            # Process and enrich response
            processed_data = self._process_cost_and_usage_response(response, start_date, end_date)
            
            logger.info(f"Retrieved {len(processed_data.get('results_by_time', []))} time periods of cost data")
            
            return processed_data
            
        except ClientError as e:
            logger.error(f"AWS API error retrieving cost data: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving cost and usage data: {e}")
            raise
    
    def get_dimension_values(
        self,
        dimension: DimensionKey,
        start_date: datetime,
        end_date: datetime,
        search_string: str = None,
        context: str = "COST_AND_USAGE"
    ) -> List[str]:
        """
        Get available values for a specific dimension.
        
        Args:
            dimension: Dimension to get values for
            start_date: Start date for analysis
            end_date: End date for analysis
            search_string: Optional search filter
            context: Context for dimension values
            
        Returns:
            List of available dimension values
        """
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            params = {
                'TimePeriod': {
                    'Start': start_str,
                    'End': end_str
                },
                'Dimension': dimension.value,
                'Context': context
            }
            
            if search_string:
                params['SearchString'] = search_string
            
            logger.info(f"Getting dimension values for {dimension.value}")
            
            if self.dry_run:
                logger.info("DRY_RUN: Would retrieve dimension values")
                return self._generate_mock_dimension_values(dimension)
            
            response = self.client.get_dimension_values(**params)
            
            values = [item['Value'] for item in response.get('DimensionValues', [])]
            
            logger.info(f"Retrieved {len(values)} values for dimension {dimension.value}")
            
            return values
            
        except ClientError as e:
            logger.error(f"AWS API error retrieving dimension values: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving dimension values: {e}")
            raise
    
    def get_cost_forecast(
        self,
        start_date: datetime,
        end_date: datetime,
        metric: CostMetric = CostMetric.UNBLENDED_COST,
        granularity: Granularity = Granularity.MONTHLY,
        filter_expression: Dict[str, Any] = None,
        prediction_interval_level: int = 80
    ) -> Dict[str, Any]:
        """
        Get cost forecast for future time period.
        
        Args:
            start_date: Start date for forecast (should be today or future)
            end_date: End date for forecast
            metric: Cost metric to forecast
            granularity: Time granularity
            filter_expression: Filtering criteria
            prediction_interval_level: Confidence level (80 or 95)
            
        Returns:
            Dict containing forecast data with confidence intervals
        """
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            params = {
                'TimePeriod': {
                    'Start': start_str,
                    'End': end_str
                },
                'Metric': metric.value,
                'Granularity': granularity.value,
                'PredictionIntervalLevel': prediction_interval_level
            }
            
            if filter_expression:
                params['Filter'] = filter_expression
            
            logger.info(f"Getting cost forecast from {start_str} to {end_str}")
            
            if self.dry_run:
                logger.info("DRY_RUN: Would retrieve cost forecast")
                return self._generate_mock_forecast_data(start_date, end_date, granularity, prediction_interval_level)
            
            response = self.client.get_cost_forecast(**params)
            
            # Process forecast response
            processed_forecast = self._process_forecast_response(response, start_date, end_date)
            
            logger.info(f"Retrieved forecast with {len(processed_forecast.get('forecast_results_by_time', []))} time periods")
            
            return processed_forecast
            
        except ClientError as e:
            logger.error(f"AWS API error retrieving cost forecast: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving cost forecast: {e}")
            raise
    
    def get_usage_forecast(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: Granularity = Granularity.MONTHLY,
        filter_expression: Dict[str, Any] = None,
        prediction_interval_level: int = 80
    ) -> Dict[str, Any]:
        """
        Get usage forecast for future time period.
        
        Args:
            start_date: Start date for forecast
            end_date: End date for forecast
            granularity: Time granularity
            filter_expression: Filtering criteria (required for usage forecasts)
            prediction_interval_level: Confidence level
            
        Returns:
            Dict containing usage forecast data
        """
        try:
            if not filter_expression:
                raise ValueError("Filter expression is required for usage forecasts")
            
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            params = {
                'TimePeriod': {
                    'Start': start_str,
                    'End': end_str
                },
                'Metric': 'USAGE_QUANTITY',
                'Granularity': granularity.value,
                'Filter': filter_expression,
                'PredictionIntervalLevel': prediction_interval_level
            }
            
            logger.info(f"Getting usage forecast from {start_str} to {end_str}")
            
            if self.dry_run:
                logger.info("DRY_RUN: Would retrieve usage forecast")
                return self._generate_mock_usage_forecast(start_date, end_date, granularity)
            
            response = self.client.get_usage_forecast(**params)
            
            # Process usage forecast response
            processed_forecast = self._process_usage_forecast_response(response, start_date, end_date)
            
            logger.info(f"Retrieved usage forecast with {len(processed_forecast.get('forecast_results_by_time', []))} time periods")
            
            return processed_forecast
            
        except ClientError as e:
            logger.error(f"AWS API error retrieving usage forecast: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving usage forecast: {e}")
            raise
    
    def analyze_cost_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: Granularity = Granularity.DAILY,
        group_by: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze cost trends over time period.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            granularity: Time granularity
            group_by: Grouping dimensions
            
        Returns:
            Dict containing trend analysis with statistics
        """
        try:
            # Get historical cost data
            cost_data = self.get_cost_and_usage(
                start_date=start_date,
                end_date=end_date,
                granularity=granularity,
                group_by=group_by
            )
            
            # Analyze trends
            trend_analysis = self._analyze_trends(cost_data, granularity)
            
            logger.info(f"Completed trend analysis for period {start_date.date()} to {end_date.date()}")
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing cost trends: {e}")
            raise
    
    def get_cost_anomalies(
        self,
        start_date: datetime,
        end_date: datetime,
        monitor_arn: str = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get cost anomalies from AWS Cost Anomaly Detection.
        
        Args:
            start_date: Start date for anomaly search
            end_date: End date for anomaly search
            monitor_arn: Optional monitor ARN to filter by
            max_results: Maximum number of results
            
        Returns:
            List of detected cost anomalies
        """
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            params = {
                'DateInterval': {
                    'StartDate': start_str,
                    'EndDate': end_str
                },
                'MaxResults': max_results
            }
            
            if monitor_arn:
                params['MonitorArn'] = monitor_arn
            
            logger.info(f"Getting cost anomalies from {start_str} to {end_str}")
            
            if self.dry_run:
                logger.info("DRY_RUN: Would retrieve cost anomalies")
                return self._generate_mock_anomalies(start_date, end_date)
            
            response = self.anomaly_client.get_anomalies(**params)
            
            anomalies = response.get('Anomalies', [])
            
            # Process and enrich anomaly data
            processed_anomalies = self._process_anomalies(anomalies)
            
            logger.info(f"Retrieved {len(processed_anomalies)} cost anomalies")
            
            return processed_anomalies
            
        except ClientError as e:
            logger.error(f"AWS API error retrieving cost anomalies: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving cost anomalies: {e}")
            raise
    
    def generate_cost_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "comprehensive",
        include_forecast: bool = True,
        include_anomalies: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive cost report with analysis.
        
        Args:
            start_date: Start date for report
            end_date: End date for report
            report_type: Type of report (comprehensive, summary, detailed)
            include_forecast: Whether to include forecast data
            include_anomalies: Whether to include anomaly data
            
        Returns:
            Dict containing comprehensive cost report
        """
        try:
            logger.info(f"Generating {report_type} cost report for {start_date.date()} to {end_date.date()}")
            
            report = {
                'report_metadata': {
                    'report_type': report_type,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'include_forecast': include_forecast,
                    'include_anomalies': include_anomalies
                },
                'cost_summary': {},
                'cost_by_service': {},
                'cost_by_region': {},
                'trend_analysis': {},
                'forecast_data': {},
                'anomalies': []
            }
            
            # Get cost summary
            cost_data = self.get_cost_and_usage(
                start_date=start_date,
                end_date=end_date,
                granularity=Granularity.DAILY
            )
            report['cost_summary'] = self._generate_cost_summary(cost_data)
            
            # Get cost by service
            service_costs = self.get_cost_and_usage(
                start_date=start_date,
                end_date=end_date,
                granularity=Granularity.MONTHLY,
                group_by=[{'Type': GroupByType.DIMENSION.value, 'Key': DimensionKey.SERVICE.value}]
            )
            report['cost_by_service'] = self._process_grouped_costs(service_costs, 'service')
            
            # Get cost by region
            region_costs = self.get_cost_and_usage(
                start_date=start_date,
                end_date=end_date,
                granularity=Granularity.MONTHLY,
                group_by=[{'Type': GroupByType.DIMENSION.value, 'Key': DimensionKey.REGION.value}]
            )
            report['cost_by_region'] = self._process_grouped_costs(region_costs, 'region')
            
            # Analyze trends
            report['trend_analysis'] = self.analyze_cost_trends(
                start_date=start_date,
                end_date=end_date,
                granularity=Granularity.DAILY
            )
            
            # Include forecast if requested
            if include_forecast:
                forecast_start = end_date + timedelta(days=1)
                forecast_end = forecast_start + timedelta(days=30)  # 30-day forecast
                
                try:
                    forecast_data = self.get_cost_forecast(
                        start_date=forecast_start,
                        end_date=forecast_end,
                        granularity=Granularity.DAILY
                    )
                    report['forecast_data'] = forecast_data
                except Exception as e:
                    logger.warning(f"Could not generate forecast: {e}")
                    report['forecast_data'] = {'error': str(e)}
            
            # Include anomalies if requested
            if include_anomalies:
                try:
                    anomalies = self.get_cost_anomalies(
                        start_date=start_date,
                        end_date=end_date
                    )
                    report['anomalies'] = anomalies
                except Exception as e:
                    logger.warning(f"Could not retrieve anomalies: {e}")
                    report['anomalies'] = []
            
            logger.info(f"Generated comprehensive cost report with {len(report)} sections")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating cost report: {e}")
            raise
    
    def _process_cost_and_usage_response(
        self,
        response: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Process and enrich cost and usage API response."""
        try:
            processed = {
                'metadata': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'processed_at': datetime.now(timezone.utc).isoformat(),
                    'total_periods': len(response.get('ResultsByTime', []))
                },
                'results_by_time': [],
                'group_definitions': response.get('GroupDefinitions', []),
                'dimension_key': response.get('DimensionKey'),
                'total_cost': 0.0,
                'currency': 'USD'
            }
            
            total_cost = 0.0
            
            for result in response.get('ResultsByTime', []):
                period_data = {
                    'time_period': result.get('TimePeriod', {}),
                    'estimated': result.get('Estimated', False),
                    'total': result.get('Total', {}),
                    'groups': result.get('Groups', [])
                }
                
                # Extract total cost for this period
                if 'UnblendedCost' in result.get('Total', {}):
                    period_cost = float(result['Total']['UnblendedCost'].get('Amount', 0))
                    total_cost += period_cost
                    period_data['period_cost'] = period_cost
                
                processed['results_by_time'].append(period_data)
            
            processed['total_cost'] = total_cost
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing cost and usage response: {e}")
            raise
    
    def _process_forecast_response(
        self,
        response: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Process and enrich forecast API response."""
        try:
            processed = {
                'metadata': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'processed_at': datetime.now(timezone.utc).isoformat(),
                    'total_periods': len(response.get('ForecastResultsByTime', []))
                },
                'total_forecast': response.get('Total', {}),
                'forecast_results_by_time': [],
                'confidence_level': response.get('PredictionIntervalLevel', 80)
            }
            
            for result in response.get('ForecastResultsByTime', []):
                period_data = {
                    'time_period': result.get('TimePeriod', {}),
                    'mean_value': result.get('MeanValue'),
                    'prediction_interval_lower_bound': result.get('PredictionIntervalLowerBound'),
                    'prediction_interval_upper_bound': result.get('PredictionIntervalUpperBound')
                }
                
                processed['forecast_results_by_time'].append(period_data)
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing forecast response: {e}")
            raise
    
    def _process_usage_forecast_response(
        self,
        response: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Process and enrich usage forecast API response."""
        try:
            processed = {
                'metadata': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'processed_at': datetime.now(timezone.utc).isoformat(),
                    'forecast_type': 'usage',
                    'total_periods': len(response.get('ForecastResultsByTime', []))
                },
                'total_forecast': response.get('Total', {}),
                'forecast_results_by_time': [],
                'confidence_level': response.get('PredictionIntervalLevel', 80)
            }
            
            for result in response.get('ForecastResultsByTime', []):
                period_data = {
                    'time_period': result.get('TimePeriod', {}),
                    'mean_value': result.get('MeanValue'),
                    'prediction_interval_lower_bound': result.get('PredictionIntervalLowerBound'),
                    'prediction_interval_upper_bound': result.get('PredictionIntervalUpperBound')
                }
                
                processed['forecast_results_by_time'].append(period_data)
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing usage forecast response: {e}")
            raise
    
    def _process_anomalies(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and enrich anomaly data."""
        try:
            processed_anomalies = []
            
            for anomaly in anomalies:
                processed = {
                    'anomaly_id': anomaly.get('AnomalyId'),
                    'anomaly_score': anomaly.get('AnomalyScore', {}).get('CurrentScore', 0),
                    'impact': anomaly.get('Impact', {}),
                    'monitor_arn': anomaly.get('MonitorArn'),
                    'feedback': anomaly.get('Feedback'),
                    'dimension_key': anomaly.get('DimensionKey'),
                    'root_causes': anomaly.get('RootCauses', []),
                    'anomaly_start_date': anomaly.get('AnomalyStartDate'),
                    'anomaly_end_date': anomaly.get('AnomalyEndDate'),
                    'processed_at': datetime.now(timezone.utc).isoformat()
                }
                
                # Calculate severity based on impact
                impact_total = float(anomaly.get('Impact', {}).get('TotalImpact', 0))
                if impact_total > 1000:
                    processed['severity'] = 'HIGH'
                elif impact_total > 100:
                    processed['severity'] = 'MEDIUM'
                else:
                    processed['severity'] = 'LOW'
                
                processed_anomalies.append(processed)
            
            return processed_anomalies
            
        except Exception as e:
            logger.error(f"Error processing anomalies: {e}")
            raise
    
    def _analyze_trends(
        self,
        cost_data: Dict[str, Any],
        granularity: Granularity
    ) -> Dict[str, Any]:
        """Analyze cost trends from historical data."""
        try:
            results_by_time = cost_data.get('results_by_time', [])
            
            if not results_by_time:
                return {'error': 'No data available for trend analysis'}
            
            # Extract daily costs
            daily_costs = []
            dates = []
            
            for result in results_by_time:
                if 'period_cost' in result:
                    daily_costs.append(result['period_cost'])
                    dates.append(result['time_period'].get('Start'))
            
            if len(daily_costs) < 2:
                return {'error': 'Insufficient data for trend analysis'}
            
            # Calculate trend statistics
            trend_analysis = {
                'period_count': len(daily_costs),
                'total_cost': sum(daily_costs),
                'average_daily_cost': statistics.mean(daily_costs),
                'median_daily_cost': statistics.median(daily_costs),
                'min_daily_cost': min(daily_costs),
                'max_daily_cost': max(daily_costs),
                'cost_variance': statistics.variance(daily_costs) if len(daily_costs) > 1 else 0,
                'cost_std_dev': statistics.stdev(daily_costs) if len(daily_costs) > 1 else 0
            }
            
            # Calculate trend direction
            if len(daily_costs) >= 7:  # Need at least a week of data
                first_week_avg = statistics.mean(daily_costs[:7])
                last_week_avg = statistics.mean(daily_costs[-7:])
                
                trend_analysis['trend_direction'] = 'increasing' if last_week_avg > first_week_avg else 'decreasing'
                trend_analysis['trend_percentage'] = ((last_week_avg - first_week_avg) / first_week_avg) * 100
            else:
                trend_analysis['trend_direction'] = 'insufficient_data'
                trend_analysis['trend_percentage'] = 0
            
            # Identify cost spikes (days with cost > 2 std devs above mean)
            if trend_analysis['cost_std_dev'] > 0:
                threshold = trend_analysis['average_daily_cost'] + (2 * trend_analysis['cost_std_dev'])
                spikes = [
                    {'date': dates[i], 'cost': cost}
                    for i, cost in enumerate(daily_costs)
                    if cost > threshold
                ]
                trend_analysis['cost_spikes'] = spikes
                trend_analysis['spike_count'] = len(spikes)
            else:
                trend_analysis['cost_spikes'] = []
                trend_analysis['spike_count'] = 0
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {'error': str(e)}
    
    def _generate_cost_summary(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cost summary from cost data."""
        try:
            return {
                'total_cost': cost_data.get('total_cost', 0),
                'currency': cost_data.get('currency', 'USD'),
                'period_count': cost_data.get('metadata', {}).get('total_periods', 0),
                'average_daily_cost': cost_data.get('total_cost', 0) / max(1, cost_data.get('metadata', {}).get('total_periods', 1))
            }
        except Exception as e:
            logger.error(f"Error generating cost summary: {e}")
            return {'error': str(e)}
    
    def _process_grouped_costs(self, cost_data: Dict[str, Any], group_type: str) -> Dict[str, Any]:
        """Process grouped cost data."""
        try:
            grouped_costs = {}
            
            for result in cost_data.get('results_by_time', []):
                for group in result.get('groups', []):
                    keys = group.get('Keys', [])
                    if keys:
                        key = keys[0]  # Use first key as identifier
                        
                        if key not in grouped_costs:
                            grouped_costs[key] = {
                                'total_cost': 0,
                                'periods': []
                            }
                        
                        # Extract cost for this group
                        metrics = group.get('Metrics', {})
                        if 'UnblendedCost' in metrics:
                            cost = float(metrics['UnblendedCost'].get('Amount', 0))
                            grouped_costs[key]['total_cost'] += cost
                            grouped_costs[key]['periods'].append({
                                'period': result.get('time_period', {}),
                                'cost': cost
                            })
            
            return grouped_costs
            
        except Exception as e:
            logger.error(f"Error processing grouped costs: {e}")
            return {'error': str(e)}
    
    # Mock data generation methods for DRY_RUN mode
    def _generate_mock_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: Granularity,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Generate mock cost data for testing."""
        days = (end_date - start_date).days
        
        mock_data = {
            'metadata': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'total_periods': days,
                'mock_data': True
            },
            'results_by_time': [],
            'total_cost': 0.0,
            'currency': 'USD'
        }
        
        total_cost = 0.0
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            daily_cost = 100 + (i * 5) + (i % 7 * 10)  # Simulate varying costs
            total_cost += daily_cost
            
            period_data = {
                'time_period': {
                    'Start': current_date.strftime('%Y-%m-%d'),
                    'End': (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
                },
                'estimated': False,
                'total': {
                    'UnblendedCost': {
                        'Amount': str(daily_cost),
                        'Unit': 'USD'
                    }
                },
                'period_cost': daily_cost,
                'groups': []
            }
            
            mock_data['results_by_time'].append(period_data)
        
        mock_data['total_cost'] = total_cost
        
        return mock_data
    
    def _generate_mock_dimension_values(self, dimension: DimensionKey) -> List[str]:
        """Generate mock dimension values for testing."""
        mock_values = {
            DimensionKey.SERVICE: ['Amazon Elastic Compute Cloud - Compute', 'Amazon Simple Storage Service', 'Amazon Relational Database Service'],
            DimensionKey.REGION: ['us-east-1', 'us-west-2', 'eu-west-1'],
            DimensionKey.INSTANCE_TYPE: ['t3.micro', 't3.small', 'm5.large', 'c5.xlarge'],
            DimensionKey.LINKED_ACCOUNT: ['123456789012', '123456789013', '123456789014']
        }
        
        return mock_values.get(dimension, ['mock-value-1', 'mock-value-2', 'mock-value-3'])
    
    def _generate_mock_forecast_data(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: Granularity,
        prediction_interval_level: int
    ) -> Dict[str, Any]:
        """Generate mock forecast data for testing."""
        days = (end_date - start_date).days
        
        mock_forecast = {
            'metadata': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'total_periods': days,
                'mock_data': True
            },
            'total_forecast': {
                'MeanValue': str(days * 120),  # Mock total forecast
                'PredictionIntervalLowerBound': str(days * 100),
                'PredictionIntervalUpperBound': str(days * 140)
            },
            'forecast_results_by_time': [],
            'confidence_level': prediction_interval_level
        }
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            base_cost = 120
            
            period_data = {
                'time_period': {
                    'Start': current_date.strftime('%Y-%m-%d'),
                    'End': (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
                },
                'mean_value': str(base_cost),
                'prediction_interval_lower_bound': str(base_cost * 0.8),
                'prediction_interval_upper_bound': str(base_cost * 1.2)
            }
            
            mock_forecast['forecast_results_by_time'].append(period_data)
        
        return mock_forecast
    
    def _generate_mock_usage_forecast(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: Granularity
    ) -> Dict[str, Any]:
        """Generate mock usage forecast data for testing."""
        days = (end_date - start_date).days
        
        return {
            'metadata': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'forecast_type': 'usage',
                'total_periods': days,
                'mock_data': True
            },
            'total_forecast': {
                'MeanValue': str(days * 100),
                'PredictionIntervalLowerBound': str(days * 80),
                'PredictionIntervalUpperBound': str(days * 120)
            },
            'forecast_results_by_time': [
                {
                    'time_period': {
                        'Start': (start_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                        'End': (start_date + timedelta(days=i+1)).strftime('%Y-%m-%d')
                    },
                    'mean_value': '100',
                    'prediction_interval_lower_bound': '80',
                    'prediction_interval_upper_bound': '120'
                }
                for i in range(days)
            ],
            'confidence_level': 80
        }
    
    def _generate_mock_anomalies(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate mock anomaly data for testing."""
        return [
            {
                'anomaly_id': 'mock-anomaly-1',
                'anomaly_score': 85.5,
                'impact': {
                    'TotalImpact': 250.0,
                    'MaxImpact': 300.0
                },
                'monitor_arn': 'arn:aws:ce::123456789012:anomaly-monitor/mock-monitor',
                'feedback': 'PLANNED_ACTIVITY',
                'dimension_key': 'SERVICE',
                'root_causes': [
                    {
                        'Service': 'Amazon Elastic Compute Cloud - Compute',
                        'Region': 'us-east-1',
                        'UsageType': 'BoxUsage:m5.large'
                    }
                ],
                'anomaly_start_date': start_date.strftime('%Y-%m-%d'),
                'anomaly_end_date': (start_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                'severity': 'MEDIUM',
                'processed_at': datetime.now(timezone.utc).isoformat()
            }
        ]


def create_cost_explorer(aws_config=None, region: str = 'us-east-1', dry_run: bool = True) -> CostExplorer:
    """
    Factory function to create Cost Explorer instance.
    
    Args:
        aws_config: AWS configuration instance
        region: AWS region
        dry_run: Safety flag for testing
        
    Returns:
        Configured CostExplorer instance
    """
    return CostExplorer(aws_config=aws_config, region=region, dry_run=dry_run)


if __name__ == "__main__":
    # Example usage and testing
    import sys
    import os
    
    # Add parent directory to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create Cost Explorer instance
    cost_explorer = create_cost_explorer(dry_run=True)
    
    # Test basic functionality
    try:
        # Test cost and usage retrieval
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)
        
        print("Testing Cost Explorer integration...")
        
        # Get cost and usage data
        cost_data = cost_explorer.get_cost_and_usage(
            start_date=start_date,
            end_date=end_date,
            granularity=Granularity.DAILY
        )
        print(f"✓ Retrieved cost data for {cost_data['metadata']['total_periods']} periods")
        
        # Test trend analysis
        trends = cost_explorer.analyze_cost_trends(
            start_date=start_date,
            end_date=end_date
        )
        print(f"✓ Analyzed cost trends: {trends.get('trend_direction', 'unknown')} trend")
        
        # Test forecast
        forecast_start = end_date + timedelta(days=1)
        forecast_end = forecast_start + timedelta(days=7)
        
        forecast = cost_explorer.get_cost_forecast(
            start_date=forecast_start,
            end_date=forecast_end
        )
        print(f"✓ Generated forecast for {forecast['metadata']['total_periods']} periods")
        
        # Test anomaly detection
        anomalies = cost_explorer.get_cost_anomalies(
            start_date=start_date,
            end_date=end_date
        )
        print(f"✓ Retrieved {len(anomalies)} cost anomalies")
        
        # Generate comprehensive report
        report = cost_explorer.generate_cost_report(
            start_date=start_date,
            end_date=end_date,
            include_forecast=True,
            include_anomalies=True
        )
        print(f"✓ Generated comprehensive cost report with {len(report)} sections")
        
        print("\n✅ Cost Explorer integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing Cost Explorer: {e}")
        sys.exit(1)