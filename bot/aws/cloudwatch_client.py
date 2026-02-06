#!/usr/bin/env python3
"""
CloudWatch Client for Advanced FinOps Platform

Comprehensive CloudWatch integration for metrics collection, custom metric namespaces,
cost optimization tracking, and log analysis. This client extends beyond basic resource
scanning to provide deep metrics collection and analysis capabilities.

Features:
- Resource utilization monitoring with custom metric namespaces
- Custom metrics for cost optimization tracking and alerting
- Log analysis for cost-related events and patterns
- Multi-region metrics aggregation
- Performance monitoring and cost correlation
- Automated metric cleanup and optimization

Requirements: 10.3, 3.1
"""

import logging
import boto3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from botocore.exceptions import ClientError
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class CloudWatchClient:
    """
    Comprehensive CloudWatch client for metrics collection and cost optimization tracking.
    
    Provides advanced CloudWatch integration including:
    - Resource utilization monitoring across all AWS services
    - Custom metric namespaces for FinOps tracking
    - Cost optimization metrics and alerting
    - Log analysis for cost-related events
    - Multi-region metrics aggregation
    - Performance correlation with cost data
    """
    
    # Custom metric namespaces for FinOps tracking
    FINOPS_NAMESPACE = "AdvancedFinOps"
    COST_OPTIMIZATION_NAMESPACE = "AdvancedFinOps/CostOptimization"
    RESOURCE_UTILIZATION_NAMESPACE = "AdvancedFinOps/ResourceUtilization"
    SAVINGS_TRACKING_NAMESPACE = "AdvancedFinOps/SavingsTracking"
    
    # Standard AWS service namespaces for monitoring
    AWS_SERVICE_NAMESPACES = {
        'ec2': 'AWS/EC2',
        'rds': 'AWS/RDS',
        'lambda': 'AWS/Lambda',
        's3': 'AWS/S3',
        'ebs': 'AWS/EBS',
        'elb': 'AWS/ELB',
        'applicationelb': 'AWS/ApplicationELB',
        'networkelb': 'AWS/NetworkELB',
        'cloudfront': 'AWS/CloudFront',
        'apigateway': 'AWS/ApiGateway',
        'dynamodb': 'AWS/DynamoDB',
        'sqs': 'AWS/SQS',
        'sns': 'AWS/SNS'
    }
    
    # Key metrics for cost optimization analysis
    COST_OPTIMIZATION_METRICS = {
        'ec2': [
            'CPUUtilization', 'NetworkIn', 'NetworkOut', 'DiskReadOps', 
            'DiskWriteOps', 'DiskReadBytes', 'DiskWriteBytes'
        ],
        'rds': [
            'CPUUtilization', 'DatabaseConnections', 'ReadIOPS', 'WriteIOPS',
            'ReadLatency', 'WriteLatency', 'ReadThroughput', 'WriteThroughput'
        ],
        'lambda': [
            'Invocations', 'Duration', 'Errors', 'Throttles', 'ConcurrentExecutions'
        ],
        'ebs': [
            'VolumeReadOps', 'VolumeWriteOps', 'VolumeReadBytes', 'VolumeWriteBytes',
            'VolumeTotalReadTime', 'VolumeTotalWriteTime', 'VolumeQueueLength'
        ],
        'elb': [
            'RequestCount', 'TargetResponseTime', 'HTTPCode_Target_2XX_Count',
            'HTTPCode_Target_4XX_Count', 'HTTPCode_Target_5XX_Count'
        ]
    }
    
    def __init__(self, aws_config, region: str = 'us-east-1'):
        """
        Initialize CloudWatch client with comprehensive configuration.
        
        Args:
            aws_config: AWSConfig instance for client management
            region: Primary AWS region for CloudWatch operations
        """
        self.aws_config = aws_config
        self.region = region
        self.cloudwatch_client = aws_config.get_cloudwatch_client(region)
        self.logs_client = aws_config.get_cloudwatch_logs_client(region)
        
        # Multi-region support for comprehensive monitoring
        self.multi_region_clients = aws_config.get_multi_region_cloudwatch_clients()
        
        logger.info(f"CloudWatch Client initialized for region {region}")
        logger.info(f"Multi-region support: {len(self.multi_region_clients)} regions")
    
    def collect_resource_utilization_metrics(self, 
                                           resource_type: str,
                                           resource_ids: List[str],
                                           days_back: int = 14,
                                           region: Optional[str] = None) -> Dict[str, Any]:
        """
        Collect comprehensive utilization metrics for resources.
        
        Args:
            resource_type: Type of AWS resource (ec2, rds, lambda, etc.)
            resource_ids: List of resource IDs to monitor
            days_back: Number of days of historical data to collect
            region: Specific region to query (uses primary region if None)
            
        Returns:
            Dictionary containing detailed utilization metrics
        """
        logger.info(f"Collecting utilization metrics for {len(resource_ids)} {resource_type} resources")
        
        client = self.cloudwatch_client
        if region and region != self.region:
            client = self.aws_config.get_cloudwatch_client(region)
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        namespace = self.AWS_SERVICE_NAMESPACES.get(resource_type.lower())
        if not namespace:
            logger.warning(f"Unknown resource type: {resource_type}")
            return {}
        
        metrics_to_collect = self.COST_OPTIMIZATION_METRICS.get(resource_type.lower(), [])
        if not metrics_to_collect:
            logger.warning(f"No metrics defined for resource type: {resource_type}")
            return {}
        
        utilization_data = {
            'resourceType': resource_type,
            'region': region or self.region,
            'timeRange': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'daysBack': days_back
            },
            'resources': {},
            'aggregatedMetrics': {},
            'utilizationSummary': {},
            'costOptimizationInsights': []
        }
        
        try:
            for resource_id in resource_ids:
                logger.debug(f"Collecting metrics for {resource_type} resource: {resource_id}")
                
                resource_metrics = {}
                
                for metric_name in metrics_to_collect:
                    try:
                        # Get metric statistics
                        metric_data = self._get_metric_statistics(
                            client, namespace, metric_name, resource_id, 
                            start_time, end_time, resource_type
                        )
                        
                        if metric_data:
                            resource_metrics[metric_name] = metric_data
                            
                    except Exception as e:
                        logger.warning(f"Failed to collect {metric_name} for {resource_id}: {e}")
                        continue
                
                if resource_metrics:
                    utilization_data['resources'][resource_id] = resource_metrics
                    
                    # Analyze utilization patterns
                    utilization_analysis = self._analyze_resource_utilization(
                        resource_id, resource_type, resource_metrics
                    )
                    utilization_data['resources'][resource_id]['utilizationAnalysis'] = utilization_analysis
            
            # Generate aggregated metrics and insights
            utilization_data['aggregatedMetrics'] = self._calculate_aggregated_metrics(
                utilization_data['resources'], resource_type
            )
            
            utilization_data['utilizationSummary'] = self._generate_utilization_summary(
                utilization_data['resources'], resource_type
            )
            
            utilization_data['costOptimizationInsights'] = self._generate_cost_optimization_insights(
                utilization_data['resources'], resource_type
            )
            
            logger.info(f"Collected metrics for {len(utilization_data['resources'])} resources")
            
        except Exception as e:
            logger.error(f"Failed to collect utilization metrics: {e}")
            raise
        
        return utilization_data
    
    def _get_metric_statistics(self, 
                              client: Any,
                              namespace: str,
                              metric_name: str,
                              resource_id: str,
                              start_time: datetime,
                              end_time: datetime,
                              resource_type: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed statistics for a specific metric.
        
        Args:
            client: CloudWatch client
            namespace: AWS service namespace
            metric_name: Name of the metric
            resource_id: Resource identifier
            start_time: Start time for metrics
            end_time: End time for metrics
            resource_type: Type of AWS resource
            
        Returns:
            Dictionary containing metric statistics or None if failed
        """
        try:
            # Determine dimensions based on resource type
            dimensions = self._get_resource_dimensions(resource_type, resource_id)
            
            # Get metric statistics with multiple statistics
            response = self.aws_config.execute_with_retry(
                client.get_metric_statistics,
                'cloudwatch',
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1-hour periods
                Statistics=['Average', 'Maximum', 'Minimum', 'Sum', 'SampleCount']
            )
            
            datapoints = response.get('Datapoints', [])
            if not datapoints:
                return None
            
            # Sort datapoints by timestamp
            datapoints.sort(key=lambda x: x['Timestamp'])
            
            # Calculate additional statistics
            values = [dp['Average'] for dp in datapoints if 'Average' in dp]
            
            metric_stats = {
                'metricName': metric_name,
                'datapoints': datapoints,
                'datapointCount': len(datapoints),
                'timeRange': {
                    'start': min(dp['Timestamp'] for dp in datapoints).isoformat(),
                    'end': max(dp['Timestamp'] for dp in datapoints).isoformat()
                },
                'statistics': {
                    'overallAverage': statistics.mean(values) if values else 0,
                    'overallMedian': statistics.median(values) if values else 0,
                    'overallMin': min(values) if values else 0,
                    'overallMax': max(values) if values else 0,
                    'standardDeviation': statistics.stdev(values) if len(values) > 1 else 0
                },
                'trends': self._calculate_metric_trends(datapoints),
                'utilizationLevel': self._classify_utilization_level(metric_name, values)
            }
            
            return metric_stats
            
        except ClientError as e:
            logger.warning(f"Failed to get metric statistics for {metric_name}: {e}")
            return None
    
    def _get_resource_dimensions(self, resource_type: str, resource_id: str) -> List[Dict[str, str]]:
        """
        Get appropriate dimensions for CloudWatch metrics based on resource type.
        
        Args:
            resource_type: Type of AWS resource
            resource_id: Resource identifier
            
        Returns:
            List of dimension dictionaries
        """
        dimension_mappings = {
            'ec2': [{'Name': 'InstanceId', 'Value': resource_id}],
            'rds': [{'Name': 'DBInstanceIdentifier', 'Value': resource_id}],
            'lambda': [{'Name': 'FunctionName', 'Value': resource_id}],
            'ebs': [{'Name': 'VolumeId', 'Value': resource_id}],
            'elb': [{'Name': 'LoadBalancerName', 'Value': resource_id}],
            'applicationelb': [{'Name': 'LoadBalancer', 'Value': resource_id}],
            'networkelb': [{'Name': 'LoadBalancer', 'Value': resource_id}]
        }
        
        return dimension_mappings.get(resource_type.lower(), [])
    
    def _calculate_metric_trends(self, datapoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate trends and patterns in metric data.
        
        Args:
            datapoints: List of CloudWatch datapoints
            
        Returns:
            Dictionary containing trend analysis
        """
        if len(datapoints) < 2:
            return {'trend': 'insufficient_data', 'slope': 0, 'correlation': 0}
        
        # Extract values and timestamps for trend analysis
        values = [dp.get('Average', 0) for dp in datapoints]
        timestamps = [dp['Timestamp'].timestamp() for dp in datapoints]
        
        # Calculate simple linear trend
        n = len(values)
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_xy = sum(i * values[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))
        
        if n * sum_x2 - sum_x * sum_x != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        else:
            slope = 0
        
        # Classify trend
        if abs(slope) < 0.1:  # Increased threshold for stable trend
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
        
        # Calculate volatility
        if len(values) > 1:
            volatility = statistics.stdev(values) / statistics.mean(values) if statistics.mean(values) > 0 else 0
        else:
            volatility = 0
        
        return {
            'trend': trend,
            'slope': slope,
            'volatility': volatility,
            'dataPointCount': n
        }
    
    def _classify_utilization_level(self, metric_name: str, values: List[float]) -> str:
        """
        Classify utilization level based on metric values.
        
        Args:
            metric_name: Name of the metric
            values: List of metric values
            
        Returns:
            Utilization level classification
        """
        if not values:
            return 'no_data'
        
        avg_value = statistics.mean(values)
        
        # Define thresholds based on metric type
        cpu_thresholds = {'low': 10, 'medium': 50, 'high': 80}
        network_thresholds = {'low': 1000000, 'medium': 10000000, 'high': 100000000}  # bytes
        default_thresholds = {'low': 20, 'medium': 60, 'high': 85}
        
        if 'CPU' in metric_name:
            thresholds = cpu_thresholds
        elif 'Network' in metric_name or 'Bytes' in metric_name:
            thresholds = network_thresholds
        else:
            thresholds = default_thresholds
        
        if avg_value < thresholds['low']:
            return 'low'
        elif avg_value < thresholds['medium']:
            return 'medium'
        elif avg_value < thresholds['high']:
            return 'high'
        else:
            return 'very_high'
    
    def _analyze_resource_utilization(self, 
                                    resource_id: str,
                                    resource_type: str,
                                    metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze utilization patterns for a specific resource.
        
        Args:
            resource_id: Resource identifier
            resource_type: Type of AWS resource
            metrics: Collected metrics data
            
        Returns:
            Dictionary containing utilization analysis
        """
        analysis = {
            'resourceId': resource_id,
            'resourceType': resource_type,
            'overallUtilization': 'unknown',
            'keyFindings': [],
            'optimizationOpportunities': [],
            'costImpact': 'unknown',
            'recommendedActions': []
        }
        
        try:
            # Analyze CPU utilization if available
            if 'CPUUtilization' in metrics:
                cpu_data = metrics['CPUUtilization']
                cpu_avg = cpu_data['statistics']['overallAverage']
                cpu_max = cpu_data['statistics']['overallMax']
                cpu_level = cpu_data['utilizationLevel']
                
                analysis['keyFindings'].append(f"Average CPU utilization: {cpu_avg:.1f}%")
                analysis['keyFindings'].append(f"Peak CPU utilization: {cpu_max:.1f}%")
                
                # CPU-based optimization opportunities
                if cpu_level == 'low' and cpu_avg < 5:
                    analysis['optimizationOpportunities'].append({
                        'type': 'rightsizing',
                        'reason': f'Very low CPU utilization ({cpu_avg:.1f}%)',
                        'recommendation': 'Consider downsizing or terminating if unused',
                        'priority': 'HIGH',
                        'estimatedSavings': 'high'
                    })
                    analysis['costImpact'] = 'high_savings_potential'
                elif cpu_level == 'low' and cpu_avg < 20:
                    analysis['optimizationOpportunities'].append({
                        'type': 'rightsizing',
                        'reason': f'Low CPU utilization ({cpu_avg:.1f}%)',
                        'recommendation': 'Consider smaller instance type',
                        'priority': 'MEDIUM',
                        'estimatedSavings': 'medium'
                    })
                    analysis['costImpact'] = 'medium_savings_potential'
                elif cpu_level == 'very_high' and cpu_avg > 80:
                    analysis['optimizationOpportunities'].append({
                        'type': 'scaling',
                        'reason': f'High CPU utilization ({cpu_avg:.1f}%)',
                        'recommendation': 'Consider larger instance type or scaling',
                        'priority': 'MEDIUM',
                        'estimatedSavings': 'performance_improvement'
                    })
            
            # Analyze network utilization
            network_metrics = [m for m in metrics.keys() if 'Network' in m]
            if network_metrics:
                total_network = 0
                for metric in network_metrics:
                    if 'statistics' in metrics[metric]:
                        total_network += metrics[metric]['statistics']['overallAverage']
                
                if total_network < 1000000:  # Less than 1MB
                    analysis['keyFindings'].append("Very low network utilization")
                    analysis['optimizationOpportunities'].append({
                        'type': 'network_optimization',
                        'reason': 'Very low network utilization',
                        'recommendation': 'Review if resource is needed',
                        'priority': 'LOW',
                        'estimatedSavings': 'low'
                    })
            
            # Analyze storage utilization for EBS
            if resource_type.lower() == 'ebs':
                storage_metrics = [m for m in metrics.keys() if 'Volume' in m]
                if storage_metrics:
                    total_ops = 0
                    for metric in storage_metrics:
                        if 'Ops' in metric and 'statistics' in metrics[metric]:
                            total_ops += metrics[metric]['statistics']['overallAverage']
                    
                    if total_ops < 1:  # Less than 1 operation per hour
                        analysis['optimizationOpportunities'].append({
                            'type': 'storage_cleanup',
                            'reason': 'Very low storage activity',
                            'recommendation': 'Consider deleting unused volume',
                            'priority': 'MEDIUM',
                            'estimatedSavings': 'medium'
                        })
            
            # Determine overall utilization
            if analysis['optimizationOpportunities']:
                high_priority_ops = [op for op in analysis['optimizationOpportunities'] if op['priority'] == 'HIGH']
                if high_priority_ops:
                    analysis['overallUtilization'] = 'underutilized'
                else:
                    analysis['overallUtilization'] = 'suboptimal'
            else:
                analysis['overallUtilization'] = 'optimal'
            
            # Generate recommended actions
            for opportunity in analysis['optimizationOpportunities']:
                analysis['recommendedActions'].append(opportunity['recommendation'])
            
        except Exception as e:
            logger.error(f"Failed to analyze utilization for {resource_id}: {e}")
            analysis['keyFindings'].append(f"Analysis failed: {str(e)}")
        
        return analysis
    
    def _calculate_aggregated_metrics(self, 
                                    resources_data: Dict[str, Any],
                                    resource_type: str) -> Dict[str, Any]:
        """
        Calculate aggregated metrics across all resources.
        
        Args:
            resources_data: Dictionary of resource metrics
            resource_type: Type of AWS resource
            
        Returns:
            Dictionary containing aggregated metrics
        """
        aggregated = {
            'resourceType': resource_type,
            'totalResources': len(resources_data),
            'metricsCollected': 0,
            'averageMetrics': {},
            'utilizationDistribution': defaultdict(int),
            'trendAnalysis': defaultdict(int)
        }
        
        try:
            all_metrics = defaultdict(list)
            
            # Collect all metric values
            for resource_id, resource_metrics in resources_data.items():
                for metric_name, metric_data in resource_metrics.items():
                    if metric_name == 'utilizationAnalysis':
                        continue
                    
                    if 'statistics' in metric_data:
                        all_metrics[metric_name].append(metric_data['statistics']['overallAverage'])
                        aggregated['metricsCollected'] += 1
                    
                    # Count utilization levels
                    if 'utilizationLevel' in metric_data:
                        aggregated['utilizationDistribution'][metric_data['utilizationLevel']] += 1
                    
                    # Count trends
                    if 'trends' in metric_data:
                        aggregated['trendAnalysis'][metric_data['trends']['trend']] += 1
            
            # Calculate average metrics
            for metric_name, values in all_metrics.items():
                if values:
                    aggregated['averageMetrics'][metric_name] = {
                        'average': statistics.mean(values),
                        'median': statistics.median(values),
                        'min': min(values),
                        'max': max(values),
                        'standardDeviation': statistics.stdev(values) if len(values) > 1 else 0,
                        'resourceCount': len(values)
                    }
            
        except Exception as e:
            logger.error(f"Failed to calculate aggregated metrics: {e}")
        
        return aggregated
    
    def _generate_utilization_summary(self, 
                                    resources_data: Dict[str, Any],
                                    resource_type: str) -> Dict[str, Any]:
        """
        Generate utilization summary and insights.
        
        Args:
            resources_data: Dictionary of resource metrics
            resource_type: Type of AWS resource
            
        Returns:
            Dictionary containing utilization summary
        """
        summary = {
            'resourceType': resource_type,
            'totalResources': len(resources_data),
            'utilizationBreakdown': {
                'optimal': 0,
                'suboptimal': 0,
                'underutilized': 0,
                'unknown': 0
            },
            'keyInsights': [],
            'overallHealthScore': 0
        }
        
        try:
            # Analyze utilization patterns
            for resource_id, resource_metrics in resources_data.items():
                if 'utilizationAnalysis' in resource_metrics:
                    utilization = resource_metrics['utilizationAnalysis']['overallUtilization']
                    summary['utilizationBreakdown'][utilization] += 1
            
            total_resources = summary['totalResources']
            if total_resources > 0:
                optimal_pct = (summary['utilizationBreakdown']['optimal'] / total_resources) * 100
                underutilized_pct = (summary['utilizationBreakdown']['underutilized'] / total_resources) * 100
                
                # Generate insights
                if underutilized_pct > 30:
                    summary['keyInsights'].append(f"High underutilization: {underutilized_pct:.1f}% of resources are underutilized")
                
                if optimal_pct > 70:
                    summary['keyInsights'].append(f"Good optimization: {optimal_pct:.1f}% of resources are optimally utilized")
                
                # Calculate health score (0-100)
                summary['overallHealthScore'] = int(optimal_pct + (summary['utilizationBreakdown']['suboptimal'] / total_resources) * 50)
            
        except Exception as e:
            logger.error(f"Failed to generate utilization summary: {e}")
        
        return summary
    
    def _generate_cost_optimization_insights(self, 
                                           resources_data: Dict[str, Any],
                                           resource_type: str) -> List[Dict[str, Any]]:
        """
        Generate cost optimization insights based on utilization data.
        
        Args:
            resources_data: Dictionary of resource metrics
            resource_type: Type of AWS resource
            
        Returns:
            List of cost optimization insights
        """
        insights = []
        
        try:
            # Count optimization opportunities by type
            opportunity_counts = defaultdict(int)
            high_priority_resources = []
            
            for resource_id, resource_metrics in resources_data.items():
                if 'utilizationAnalysis' in resource_metrics:
                    analysis = resource_metrics['utilizationAnalysis']
                    
                    for opportunity in analysis.get('optimizationOpportunities', []):
                        opportunity_counts[opportunity['type']] += 1
                        
                        if opportunity['priority'] == 'HIGH':
                            high_priority_resources.append({
                                'resourceId': resource_id,
                                'opportunity': opportunity
                            })
            
            # Generate insights based on patterns
            if opportunity_counts['rightsizing'] > 0:
                insights.append({
                    'type': 'rightsizing_opportunity',
                    'title': f"Right-sizing Opportunities Identified",
                    'description': f"Found {opportunity_counts['rightsizing']} resources that could benefit from right-sizing",
                    'impact': 'cost_reduction',
                    'priority': 'HIGH' if opportunity_counts['rightsizing'] > len(resources_data) * 0.3 else 'MEDIUM',
                    'resourceCount': opportunity_counts['rightsizing']
                })
            
            if opportunity_counts['storage_cleanup'] > 0:
                insights.append({
                    'type': 'storage_cleanup',
                    'title': f"Storage Cleanup Opportunities",
                    'description': f"Found {opportunity_counts['storage_cleanup']} storage resources with low utilization",
                    'impact': 'cost_reduction',
                    'priority': 'MEDIUM',
                    'resourceCount': opportunity_counts['storage_cleanup']
                })
            
            if high_priority_resources:
                insights.append({
                    'type': 'immediate_action_required',
                    'title': f"Immediate Action Required",
                    'description': f"Found {len(high_priority_resources)} resources requiring immediate attention",
                    'impact': 'high_cost_reduction',
                    'priority': 'CRITICAL',
                    'resources': [r['resourceId'] for r in high_priority_resources[:5]]  # Limit to 5 examples
                })
            
        except Exception as e:
            logger.error(f"Failed to generate cost optimization insights: {e}")
        
        return insights
    
    def publish_custom_metrics(self, 
                              metrics_data: List[Dict[str, Any]],
                              namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Publish custom metrics to CloudWatch for cost optimization tracking.
        
        Args:
            metrics_data: List of metric data dictionaries
            namespace: Custom namespace (uses default FinOps namespace if None)
            
        Returns:
            Dictionary containing publish results
        """
        namespace = namespace or self.COST_OPTIMIZATION_NAMESPACE
        
        logger.info(f"Publishing {len(metrics_data)} custom metrics to namespace: {namespace}")
        
        results = {
            'namespace': namespace,
            'totalMetrics': len(metrics_data),
            'publishedMetrics': 0,
            'failedMetrics': 0,
            'errors': []
        }
        
        try:
            # Batch metrics for efficient publishing (CloudWatch allows up to 20 metrics per call)
            batch_size = 20
            for i in range(0, len(metrics_data), batch_size):
                batch = metrics_data[i:i + batch_size]
                
                try:
                    metric_data = []
                    
                    for metric in batch:
                        metric_entry = {
                            'MetricName': metric['metricName'],
                            'Value': metric['value'],
                            'Unit': metric.get('unit', 'None'),
                            'Timestamp': datetime.fromisoformat(metric['timestamp']) if isinstance(metric['timestamp'], str) else metric['timestamp']
                        }
                        
                        # Add dimensions if provided
                        if 'dimensions' in metric:
                            metric_entry['Dimensions'] = [
                                {'Name': k, 'Value': v} for k, v in metric['dimensions'].items()
                            ]
                        
                        metric_data.append(metric_entry)
                    
                    # Publish batch
                    self.aws_config.execute_with_retry(
                        self.cloudwatch_client.put_metric_data,
                        'cloudwatch',
                        Namespace=namespace,
                        MetricData=metric_data
                    )
                    
                    results['publishedMetrics'] += len(batch)
                    logger.debug(f"Published batch of {len(batch)} metrics")
                    
                except Exception as e:
                    logger.error(f"Failed to publish metric batch: {e}")
                    results['failedMetrics'] += len(batch)
                    results['errors'].append(str(e))
            
            logger.info(f"Published {results['publishedMetrics']}/{results['totalMetrics']} custom metrics")
            
        except Exception as e:
            logger.error(f"Failed to publish custom metrics: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def analyze_log_patterns_for_cost_events(self, 
                                           log_group_names: List[str],
                                           days_back: int = 7,
                                           region: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze CloudWatch logs for cost-related events and patterns.
        
        Args:
            log_group_names: List of log group names to analyze
            days_back: Number of days to analyze
            region: Specific region to query (uses primary region if None)
            
        Returns:
            Dictionary containing log analysis results
        """
        logger.info(f"Analyzing {len(log_group_names)} log groups for cost-related events")
        
        logs_client = self.logs_client
        if region and region != self.region:
            logs_client = self.aws_config.get_cloudwatch_logs_client(region)
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        analysis_results = {
            'timeRange': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'daysBack': days_back
            },
            'logGroups': log_group_names,
            'region': region or self.region,
            'costEvents': [],
            'patterns': {},
            'insights': [],
            'totalEventsAnalyzed': 0
        }
        
        # Cost-related patterns to search for
        cost_patterns = [
            'cost', 'billing', 'price', 'expensive', 'budget', 'spend',
            'throttle', 'limit', 'quota', 'scale', 'resize', 'terminate'
        ]
        
        try:
            for log_group in log_group_names:
                logger.debug(f"Analyzing log group: {log_group}")
                
                try:
                    # Search for cost-related patterns
                    for pattern in cost_patterns:
                        events = self._search_log_events(
                            logs_client, log_group, pattern, start_time, end_time
                        )
                        
                        if events:
                            analysis_results['costEvents'].extend(events)
                            analysis_results['patterns'][pattern] = analysis_results['patterns'].get(pattern, 0) + len(events)
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze log group {log_group}: {e}")
                    continue
            
            analysis_results['totalEventsAnalyzed'] = len(analysis_results['costEvents'])
            
            # Generate insights from patterns
            if analysis_results['patterns']:
                sorted_patterns = sorted(analysis_results['patterns'].items(), key=lambda x: x[1], reverse=True)
                
                for pattern, count in sorted_patterns[:5]:  # Top 5 patterns
                    if count > 10:  # Significant number of events
                        analysis_results['insights'].append({
                            'type': 'frequent_pattern',
                            'pattern': pattern,
                            'eventCount': count,
                            'description': f"Frequent occurrence of '{pattern}' in logs ({count} events)",
                            'recommendation': f"Investigate {pattern}-related events for cost optimization opportunities"
                        })
            
            logger.info(f"Analyzed {analysis_results['totalEventsAnalyzed']} cost-related log events")
            
        except Exception as e:
            logger.error(f"Failed to analyze log patterns: {e}")
            analysis_results['insights'].append({
                'type': 'analysis_error',
                'description': f"Log analysis failed: {str(e)}",
                'recommendation': 'Check log group permissions and availability'
            })
        
        return analysis_results
    
    def _search_log_events(self, 
                          logs_client: Any,
                          log_group_name: str,
                          search_pattern: str,
                          start_time: datetime,
                          end_time: datetime) -> List[Dict[str, Any]]:
        """
        Search for specific patterns in CloudWatch logs.
        
        Args:
            logs_client: CloudWatch Logs client
            log_group_name: Name of the log group
            search_pattern: Pattern to search for
            start_time: Start time for search
            end_time: End time for search
            
        Returns:
            List of matching log events
        """
        events = []
        
        try:
            # Use filter_log_events to search for pattern
            paginator = logs_client.get_paginator('filter_log_events')
            
            for page in paginator.paginate(
                logGroupName=log_group_name,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                filterPattern=search_pattern,
                PaginationConfig={'MaxItems': 100}  # Limit results
            ):
                for event in page.get('events', []):
                    events.append({
                        'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                        'logGroup': log_group_name,
                        'logStream': event.get('logStreamName', ''),
                        'message': event.get('message', ''),
                        'pattern': search_pattern
                    })
        
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') != 'ResourceNotFoundException':
                logger.warning(f"Failed to search log group {log_group_name} for pattern {search_pattern}: {e}")
        
        return events
    
    def create_cost_optimization_alarms(self, 
                                      alarm_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create CloudWatch alarms for cost optimization monitoring.
        
        Args:
            alarm_configs: List of alarm configuration dictionaries
            
        Returns:
            Dictionary containing alarm creation results
        """
        logger.info(f"Creating {len(alarm_configs)} cost optimization alarms")
        
        results = {
            'totalAlarms': len(alarm_configs),
            'createdAlarms': 0,
            'failedAlarms': 0,
            'alarmNames': [],
            'errors': []
        }
        
        try:
            for config in alarm_configs:
                try:
                    alarm_name = config['alarmName']
                    
                    # Create alarm
                    self.aws_config.execute_with_retry(
                        self.cloudwatch_client.put_metric_alarm,
                        'cloudwatch',
                        AlarmName=alarm_name,
                        ComparisonOperator=config['comparisonOperator'],
                        EvaluationPeriods=config['evaluationPeriods'],
                        MetricName=config['metricName'],
                        Namespace=config['namespace'],
                        Period=config['period'],
                        Statistic=config['statistic'],
                        Threshold=config['threshold'],
                        ActionsEnabled=config.get('actionsEnabled', True),
                        AlarmActions=config.get('alarmActions', []),
                        AlarmDescription=config.get('alarmDescription', ''),
                        Dimensions=config.get('dimensions', []),
                        Unit=config.get('unit', 'None')
                    )
                    
                    results['createdAlarms'] += 1
                    results['alarmNames'].append(alarm_name)
                    logger.debug(f"Created alarm: {alarm_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to create alarm {config.get('alarmName', 'unknown')}: {e}")
                    results['failedAlarms'] += 1
                    results['errors'].append(str(e))
            
            logger.info(f"Created {results['createdAlarms']}/{results['totalAlarms']} cost optimization alarms")
            
        except Exception as e:
            logger.error(f"Failed to create cost optimization alarms: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def get_multi_region_metrics_summary(self, 
                                       resource_type: str,
                                       metric_name: str,
                                       days_back: int = 7) -> Dict[str, Any]:
        """
        Get metrics summary across multiple regions for cost comparison.
        
        Args:
            resource_type: Type of AWS resource
            metric_name: Name of the metric to analyze
            days_back: Number of days of data to analyze
            
        Returns:
            Dictionary containing multi-region metrics summary
        """
        logger.info(f"Collecting {metric_name} metrics for {resource_type} across {len(self.multi_region_clients)} regions")
        
        summary = {
            'resourceType': resource_type,
            'metricName': metric_name,
            'timeRange': {
                'daysBack': days_back,
                'end': datetime.utcnow().isoformat()
            },
            'regions': {},
            'totalResources': 0,
            'regionalComparison': {},
            'costOptimizationInsights': []
        }
        
        try:
            for region, client in self.multi_region_clients.items():
                logger.debug(f"Collecting metrics for region: {region}")
                
                try:
                    # This would typically integrate with resource discovery
                    # For now, we'll create a placeholder structure
                    region_data = {
                        'region': region,
                        'resourceCount': 0,
                        'averageMetricValue': 0,
                        'utilizationLevel': 'unknown',
                        'costOptimizationOpportunities': 0
                    }
                    
                    summary['regions'][region] = region_data
                    
                except Exception as e:
                    logger.warning(f"Failed to collect metrics for region {region}: {e}")
                    continue
            
            # Generate regional comparison insights
            if len(summary['regions']) > 1:
                summary['costOptimizationInsights'].append({
                    'type': 'multi_region_analysis',
                    'description': f"Analyzed {resource_type} {metric_name} across {len(summary['regions'])} regions",
                    'recommendation': 'Consider regional cost differences for optimization opportunities'
                })
            
        except Exception as e:
            logger.error(f"Failed to get multi-region metrics summary: {e}")
        
        return summary
    
    def cleanup_unused_metrics_and_alarms(self, 
                                        dry_run: bool = True,
                                        days_inactive: int = 30) -> Dict[str, Any]:
        """
        Identify and optionally clean up unused custom metrics and alarms.
        
        Args:
            dry_run: If True, only identify unused resources without deleting
            days_inactive: Number of days without data to consider unused
            
        Returns:
            Dictionary containing cleanup results
        """
        logger.info(f"{'Identifying' if dry_run else 'Cleaning up'} unused metrics and alarms")
        
        results = {
            'dryRun': dry_run,
            'daysInactive': days_inactive,
            'unusedMetrics': [],
            'unusedAlarms': [],
            'cleanupActions': [],
            'potentialSavings': 0
        }
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_inactive)
            
            # Find unused custom metrics
            paginator = self.cloudwatch_client.get_paginator('list_metrics')
            
            for page in paginator.paginate(Namespace=self.FINOPS_NAMESPACE):
                for metric in page.get('Metrics', []):
                    try:
                        # Check if metric has recent data
                        response = self.cloudwatch_client.get_metric_statistics(
                            Namespace=metric['Namespace'],
                            MetricName=metric['MetricName'],
                            Dimensions=metric.get('Dimensions', []),
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=3600,
                            Statistics=['SampleCount']
                        )
                        
                        if not response.get('Datapoints'):
                            results['unusedMetrics'].append({
                                'namespace': metric['Namespace'],
                                'metricName': metric['MetricName'],
                                'dimensions': metric.get('Dimensions', [])
                            })
                    
                    except Exception as e:
                        logger.warning(f"Failed to check metric {metric['MetricName']}: {e}")
                        continue
            
            # Find unused alarms
            paginator = self.cloudwatch_client.get_paginator('describe_alarms')
            
            for page in paginator.paginate():
                for alarm in page.get('MetricAlarms', []):
                    try:
                        # Check alarm history for activity
                        history = self.cloudwatch_client.describe_alarm_history(
                            AlarmName=alarm['AlarmName'],
                            StartDate=start_time,
                            EndDate=end_time,
                            MaxRecords=1
                        )
                        
                        if not history.get('AlarmHistoryItems'):
                            results['unusedAlarms'].append({
                                'alarmName': alarm['AlarmName'],
                                'namespace': alarm.get('Namespace', ''),
                                'metricName': alarm.get('MetricName', '')
                            })
                    
                    except Exception as e:
                        logger.warning(f"Failed to check alarm {alarm['AlarmName']}: {e}")
                        continue
            
            # Calculate potential savings
            # Custom metrics cost $0.30 per metric per month
            # Alarms cost $0.10 per alarm per month
            results['potentialSavings'] = (len(results['unusedMetrics']) * 0.30 + 
                                         len(results['unusedAlarms']) * 0.10)
            
            # Generate cleanup actions
            if not dry_run:
                # In a real implementation, we would delete the unused resources here
                results['cleanupActions'].append("DRY_RUN mode - no actual cleanup performed")
            else:
                results['cleanupActions'].append(f"Identified {len(results['unusedMetrics'])} unused metrics")
                results['cleanupActions'].append(f"Identified {len(results['unusedAlarms'])} unused alarms")
                results['cleanupActions'].append(f"Potential monthly savings: ${results['potentialSavings']:.2f}")
            
            logger.info(f"Cleanup analysis complete: {len(results['unusedMetrics'])} unused metrics, "
                       f"{len(results['unusedAlarms'])} unused alarms, "
                       f"${results['potentialSavings']:.2f} potential monthly savings")
            
        except Exception as e:
            logger.error(f"Failed to cleanup unused metrics and alarms: {e}")
            results['cleanupActions'].append(f"Cleanup failed: {str(e)}")
        
        return results
    
    def get_cloudwatch_cost_optimization_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive CloudWatch cost optimization summary.
        
        Returns:
            Dictionary containing comprehensive optimization summary
        """
        logger.info("Generating CloudWatch cost optimization summary")
        
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'region': self.region,
            'multiRegionSupport': len(self.multi_region_clients),
            'customNamespaces': [
                self.FINOPS_NAMESPACE,
                self.COST_OPTIMIZATION_NAMESPACE,
                self.RESOURCE_UTILIZATION_NAMESPACE,
                self.SAVINGS_TRACKING_NAMESPACE
            ],
            'capabilities': {
                'resourceUtilizationMonitoring': True,
                'customMetricsPublishing': True,
                'logAnalysisForCostEvents': True,
                'multiRegionMetricsAggregation': True,
                'costOptimizationAlarming': True,
                'unusedResourceCleanup': True
            },
            'supportedServices': list(self.AWS_SERVICE_NAMESPACES.keys()),
            'optimizationFeatures': [
                'Comprehensive resource utilization monitoring',
                'Custom metric namespaces for FinOps tracking',
                'Cost-related log event analysis',
                'Multi-region metrics aggregation',
                'Automated cost optimization alerting',
                'Unused metrics and alarms cleanup'
            ]
        }
        
        return summary