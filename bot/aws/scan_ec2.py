#!/usr/bin/env python3
"""
EC2 Resource Scanner for Advanced FinOps Platform

Discovers and analyzes EC2 instances across regions, collecting:
- Instance metadata and configuration
- CPU, memory, network utilization metrics from CloudWatch with configurable time ranges
- Cost data and regional cost comparison
- Unused and underutilized instance identification based on configurable thresholds
- Instance type analysis and right-sizing recommendations

Requirements: 1.1, 1.2, 3.1, 2.4
"""

import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from botocore.exceptions import ClientError
import statistics

logger = logging.getLogger(__name__)


class EC2Scanner:
    """Scans EC2 instances for cost optimization opportunities."""
    
    # Configurable thresholds for optimization analysis
    DEFAULT_THRESHOLDS = {
        'unused_cpu_avg': 2.0,      # Average CPU < 2% = unused
        'unused_cpu_max': 10.0,     # Max CPU < 10% = unused
        'underutilized_cpu_avg': 10.0,  # Average CPU < 10% = underutilized
        'underutilized_cpu_max': 30.0,  # Max CPU < 30% = underutilized
        'unused_memory_avg': 20.0,      # Average memory < 20% = unused
        'underutilized_memory_avg': 40.0,  # Average memory < 40% = underutilized
        'minimum_data_points': 24,      # Minimum hours of data required
        'network_threshold_mb': 100,    # Network usage threshold in MB/hour
    }
    
    def __init__(self, aws_config, region: str = 'us-east-1', thresholds: Dict[str, float] = None):
        """
        Initialize EC2 scanner.
        
        Args:
            aws_config: AWSConfig instance for client management
            region: AWS region to scan
            thresholds: Custom thresholds for optimization analysis
        """
        self.aws_config = aws_config
        self.region = region
        self.ec2_client = aws_config.get_client('ec2')
        self.cloudwatch_client = aws_config.get_client('cloudwatch')
        self.pricing_client = aws_config.get_client('pricing', region='us-east-1')  # Pricing API only in us-east-1
        
        # Use custom thresholds or defaults
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
        
        # Regional pricing cache
        self.regional_pricing_cache = {}
        
        logger.info(f"EC2 Scanner initialized for region {region}")
        logger.debug(f"Using thresholds: {self.thresholds}")
    
    def scan_instances(self, 
                      days_back: int = 14, 
                      hours_back: int = None,
                      metric_period: int = 3600,
                      include_regional_comparison: bool = True) -> List[Dict[str, Any]]:
        """
        Scan all EC2 instances in the region with configurable time ranges.
        
        Args:
            days_back: Number of days to look back for metrics (ignored if hours_back is set)
            hours_back: Number of hours to look back for metrics (overrides days_back)
            metric_period: CloudWatch metric period in seconds (300, 900, 3600, etc.)
            include_regional_comparison: Whether to include regional cost comparison
            
        Returns:
            List of instance data with utilization metrics and cost analysis
        """
        logger.info(f"Starting EC2 instance scan in region {self.region}")
        
        # Calculate time range
        if hours_back:
            time_range_hours = hours_back
            logger.info(f"Using custom time range: {hours_back} hours")
        else:
            time_range_hours = days_back * 24
            logger.info(f"Using time range: {days_back} days ({time_range_hours} hours)")
        
        instances = []
        
        try:
            # Get all instances
            paginator = self.ec2_client.get_paginator('describe_instances')
            
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        instance_data = self._analyze_instance(
                            instance, 
                            time_range_hours, 
                            metric_period,
                            include_regional_comparison
                        )
                        if instance_data:
                            instances.append(instance_data)
            
            logger.info(f"Scanned {len(instances)} EC2 instances")
            
            # Add regional cost comparison summary if requested
            if include_regional_comparison and instances:
                regional_summary = self._generate_regional_cost_summary(instances)
                logger.info(f"Generated regional cost comparison for {len(regional_summary)} regions")
            
        except ClientError as e:
            logger.error(f"Failed to scan EC2 instances: {e}")
            raise
        
        return instances
    
    def _analyze_instance(self, 
                         instance: Dict[str, Any], 
                         time_range_hours: int,
                         metric_period: int = 3600,
                         include_regional_comparison: bool = True) -> Optional[Dict[str, Any]]:
        """
        Analyze a single EC2 instance with enhanced metrics and cost analysis.
        
        Args:
            instance: EC2 instance data from describe_instances
            time_range_hours: Number of hours to analyze metrics
            metric_period: CloudWatch metric period in seconds
            include_regional_comparison: Whether to include regional cost comparison
            
        Returns:
            Instance analysis data or None if analysis fails
        """
        instance_id = instance['InstanceId']
        
        try:
            # Basic instance information
            instance_data = {
                'resourceId': instance_id,
                'resourceType': 'ec2',
                'region': self.region,
                'instanceType': instance.get('InstanceType', 'unknown'),
                'state': instance.get('State', {}).get('Name', 'unknown'),
                'launchTime': instance.get('LaunchTime', datetime.utcnow()).isoformat(),
                'platform': instance.get('Platform', 'linux'),
                'vpcId': instance.get('VpcId'),
                'subnetId': instance.get('SubnetId'),
                'availabilityZone': instance.get('Placement', {}).get('AvailabilityZone'),
                'architecture': instance.get('Architecture', 'x86_64'),
                'virtualizationType': instance.get('VirtualizationType', 'hvm'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Extract tags
            tags = {}
            for tag in instance.get('Tags', []):
                tags[tag['Key']] = tag['Value']
            instance_data['tags'] = tags
            
            # Get instance specifications
            instance_specs = self._get_instance_specifications(instance_data['instanceType'])
            instance_data['specifications'] = instance_specs
            
            # Get utilization metrics only for running instances
            if instance_data['state'] == 'running':
                metrics = self._get_enhanced_instance_metrics(instance_id, time_range_hours, metric_period)
                instance_data['utilizationMetrics'] = metrics
                
                # Calculate optimization opportunities with enhanced analysis
                opportunities = self._identify_enhanced_optimization_opportunities(instance_data, metrics)
                instance_data['optimizationOpportunities'] = opportunities
                
                # Get current cost with regional comparison
                cost_analysis = self._get_comprehensive_cost_analysis(
                    instance_data['instanceType'], 
                    instance_data['platform'],
                    include_regional_comparison
                )
                instance_data.update(cost_analysis)
            else:
                # For stopped instances, mark as potential cleanup
                instance_data['utilizationMetrics'] = {}
                cost_analysis = self._get_comprehensive_cost_analysis(
                    instance_data['instanceType'], 
                    instance_data['platform'],
                    include_regional_comparison
                )
                
                instance_data['optimizationOpportunities'] = [{
                    'type': 'cleanup',
                    'reason': f'Instance in {instance_data["state"]} state',
                    'priority': 'HIGH' if instance_data['state'] == 'stopped' else 'MEDIUM',
                    'estimatedSavings': cost_analysis.get('currentCost', 0),
                    'confidence': 'HIGH',
                    'action': 'terminate' if instance_data['state'] == 'stopped' else 'investigate'
                }]
                instance_data.update(cost_analysis)
                instance_data['currentCost'] = 0.0  # No cost for stopped instances
            
            return instance_data
            
        except Exception as e:
            logger.error(f"Failed to analyze instance {instance_id}: {e}")
            return None
    
    def _get_enhanced_instance_metrics(self, 
                                      instance_id: str, 
                                      time_range_hours: int,
                                      metric_period: int = 3600) -> Dict[str, Any]:
        """
        Get comprehensive CloudWatch metrics for an EC2 instance including memory.
        
        Args:
            instance_id: EC2 instance ID
            time_range_hours: Number of hours to retrieve metrics
            metric_period: CloudWatch metric period in seconds
            
        Returns:
            Dictionary containing comprehensive utilization metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        metrics = {
            'cpuUtilization': [],
            'memoryUtilization': [],
            'networkIn': [],
            'networkOut': [],
            'diskReadOps': [],
            'diskWriteOps': [],
            'diskReadBytes': [],
            'diskWriteBytes': [],
            'networkPacketsIn': [],
            'networkPacketsOut': [],
            'period': f"{time_range_hours} hours",
            'dataPoints': 0,
            'metricPeriod': metric_period
        }
        
        try:
            # CPU Utilization
            cpu_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=metric_period,
                Statistics=['Average', 'Maximum', 'Minimum']
            )
            
            cpu_datapoints = sorted(cpu_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['cpuUtilization'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average'],
                    'maximum': dp['Maximum'],
                    'minimum': dp['Minimum']
                }
                for dp in cpu_datapoints
            ]
            
            # Memory Utilization (requires CloudWatch agent)
            try:
                memory_response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='CWAgent',
                    MetricName='mem_used_percent',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=metric_period,
                    Statistics=['Average', 'Maximum', 'Minimum']
                )
                
                memory_datapoints = sorted(memory_response['Datapoints'], key=lambda x: x['Timestamp'])
                metrics['memoryUtilization'] = [
                    {
                        'timestamp': dp['Timestamp'].isoformat(),
                        'average': dp['Average'],
                        'maximum': dp['Maximum'],
                        'minimum': dp['Minimum']
                    }
                    for dp in memory_datapoints
                ]
            except ClientError:
                # Memory metrics not available (CloudWatch agent not installed)
                logger.debug(f"Memory metrics not available for instance {instance_id}")
                metrics['memoryUtilization'] = []
            
            # Network In
            network_in_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='NetworkIn',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=metric_period,
                Statistics=['Sum', 'Average']
            )
            
            network_in_datapoints = sorted(network_in_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['networkIn'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum'],
                    'average': dp['Average']
                }
                for dp in network_in_datapoints
            ]
            
            # Network Out
            network_out_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='NetworkOut',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=metric_period,
                Statistics=['Sum', 'Average']
            )
            
            network_out_datapoints = sorted(network_out_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['networkOut'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum'],
                    'average': dp['Average']
                }
                for dp in network_out_datapoints
            ]
            
            # Disk Read Operations and Bytes
            for metric_name, key in [('DiskReadOps', 'diskReadOps'), ('DiskReadBytes', 'diskReadBytes')]:
                response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName=metric_name,
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=metric_period,
                    Statistics=['Sum', 'Average']
                )
                
                datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
                metrics[key] = [
                    {
                        'timestamp': dp['Timestamp'].isoformat(),
                        'sum': dp['Sum'],
                        'average': dp['Average']
                    }
                    for dp in datapoints
                ]
            
            # Disk Write Operations and Bytes
            for metric_name, key in [('DiskWriteOps', 'diskWriteOps'), ('DiskWriteBytes', 'diskWriteBytes')]:
                response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName=metric_name,
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=metric_period,
                    Statistics=['Sum', 'Average']
                )
                
                datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
                metrics[key] = [
                    {
                        'timestamp': dp['Timestamp'].isoformat(),
                        'sum': dp['Sum'],
                        'average': dp['Average']
                    }
                    for dp in datapoints
                ]
            
            # Network Packets In/Out
            for metric_name, key in [('NetworkPacketsIn', 'networkPacketsIn'), ('NetworkPacketsOut', 'networkPacketsOut')]:
                try:
                    response = self.cloudwatch_client.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName=metric_name,
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=metric_period,
                        Statistics=['Sum', 'Average']
                    )
                    
                    datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
                    metrics[key] = [
                        {
                            'timestamp': dp['Timestamp'].isoformat(),
                            'sum': dp['Sum'],
                            'average': dp['Average']
                        }
                        for dp in datapoints
                    ]
                except ClientError:
                    # Network packet metrics might not be available for all instance types
                    metrics[key] = []
            
            # Calculate comprehensive summary statistics
            if metrics['cpuUtilization']:
                cpu_averages = [dp['average'] for dp in metrics['cpuUtilization']]
                cpu_maximums = [dp['maximum'] for dp in metrics['cpuUtilization']]
                cpu_minimums = [dp['minimum'] for dp in metrics['cpuUtilization']]
                
                metrics['avgCpuUtilization'] = statistics.mean(cpu_averages)
                metrics['maxCpuUtilization'] = max(cpu_maximums)
                metrics['minCpuUtilization'] = min(cpu_minimums)
                metrics['medianCpuUtilization'] = statistics.median(cpu_averages)
                metrics['cpuUtilizationStdDev'] = statistics.stdev(cpu_averages) if len(cpu_averages) > 1 else 0
                metrics['dataPoints'] = len(cpu_averages)
            else:
                metrics.update({
                    'avgCpuUtilization': 0.0,
                    'maxCpuUtilization': 0.0,
                    'minCpuUtilization': 0.0,
                    'medianCpuUtilization': 0.0,
                    'cpuUtilizationStdDev': 0.0,
                    'dataPoints': 0
                })
            
            # Memory statistics (if available)
            if metrics['memoryUtilization']:
                memory_averages = [dp['average'] for dp in metrics['memoryUtilization']]
                memory_maximums = [dp['maximum'] for dp in metrics['memoryUtilization']]
                memory_minimums = [dp['minimum'] for dp in metrics['memoryUtilization']]
                
                metrics['avgMemoryUtilization'] = statistics.mean(memory_averages)
                metrics['maxMemoryUtilization'] = max(memory_maximums)
                metrics['minMemoryUtilization'] = min(memory_minimums)
                metrics['medianMemoryUtilization'] = statistics.median(memory_averages)
                metrics['memoryUtilizationStdDev'] = statistics.stdev(memory_averages) if len(memory_averages) > 1 else 0
                metrics['memoryDataAvailable'] = True
            else:
                metrics.update({
                    'avgMemoryUtilization': None,
                    'maxMemoryUtilization': None,
                    'minMemoryUtilization': None,
                    'medianMemoryUtilization': None,
                    'memoryUtilizationStdDev': None,
                    'memoryDataAvailable': False
                })
            
            # Network statistics
            if metrics['networkIn'] and metrics['networkOut']:
                network_in_totals = [dp['sum'] for dp in metrics['networkIn']]
                network_out_totals = [dp['sum'] for dp in metrics['networkOut']]
                
                metrics['totalNetworkInBytes'] = sum(network_in_totals)
                metrics['totalNetworkOutBytes'] = sum(network_out_totals)
                metrics['avgNetworkInMBPerHour'] = (sum(network_in_totals) / len(network_in_totals)) / (1024 * 1024) if network_in_totals else 0
                metrics['avgNetworkOutMBPerHour'] = (sum(network_out_totals) / len(network_out_totals)) / (1024 * 1024) if network_out_totals else 0
            else:
                metrics.update({
                    'totalNetworkInBytes': 0,
                    'totalNetworkOutBytes': 0,
                    'avgNetworkInMBPerHour': 0,
                    'avgNetworkOutMBPerHour': 0
                })
            
            logger.debug(f"Retrieved {metrics['dataPoints']} metric data points for instance {instance_id}")
            
        except ClientError as e:
            logger.warning(f"Failed to retrieve metrics for instance {instance_id}: {e}")
            # Return empty metrics on failure
            metrics.update({
                'avgCpuUtilization': 0.0,
                'maxCpuUtilization': 0.0,
                'dataPoints': 0,
                'avgMemoryUtilization': None,
                'memoryDataAvailable': False
            })
        
        return metrics
    
    def _identify_enhanced_optimization_opportunities(self, 
                                                     instance_data: Dict[str, Any], 
                                                     metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities using enhanced analysis with configurable thresholds.
        
        Args:
            instance_data: Instance metadata
            metrics: Comprehensive utilization metrics
            
        Returns:
            List of optimization opportunities with detailed analysis
        """
        opportunities = []
        
        # CPU-based optimizations
        avg_cpu = metrics.get('avgCpuUtilization', 0)
        max_cpu = metrics.get('maxCpuUtilization', 0)
        median_cpu = metrics.get('medianCpuUtilization', 0)
        cpu_std_dev = metrics.get('cpuUtilizationStdDev', 0)
        data_points = metrics.get('dataPoints', 0)
        
        # Memory-based optimizations (if available)
        avg_memory = metrics.get('avgMemoryUtilization')
        max_memory = metrics.get('maxMemoryUtilization')
        memory_available = metrics.get('memoryDataAvailable', False)
        
        # Network usage analysis
        avg_network_in_mb = metrics.get('avgNetworkInMBPerHour', 0)
        avg_network_out_mb = metrics.get('avgNetworkOutMBPerHour', 0)
        total_network_mb = avg_network_in_mb + avg_network_out_mb
        
        # Only analyze if we have sufficient data
        if data_points >= self.thresholds['minimum_data_points']:
            
            # Unused instance analysis (very low utilization)
            if (avg_cpu < self.thresholds['unused_cpu_avg'] and 
                max_cpu < self.thresholds['unused_cpu_max']):
                
                confidence = 'HIGH'
                if memory_available and avg_memory and avg_memory < self.thresholds['unused_memory_avg']:
                    confidence = 'VERY_HIGH'
                    reason = f'Very low utilization: {avg_cpu:.1f}% avg CPU, {max_cpu:.1f}% max CPU, {avg_memory:.1f}% avg memory'
                else:
                    reason = f'Very low utilization: {avg_cpu:.1f}% avg CPU, {max_cpu:.1f}% max CPU'
                
                opportunities.append({
                    'type': 'cleanup',
                    'reason': reason,
                    'priority': 'HIGH',
                    'estimatedSavings': instance_data.get('currentCost', 0) * 0.95,
                    'confidence': confidence,
                    'action': 'terminate',
                    'riskLevel': 'LOW',
                    'implementationEffort': 'LOW',
                    'metrics': {
                        'avgCpu': avg_cpu,
                        'maxCpu': max_cpu,
                        'avgMemory': avg_memory,
                        'dataPoints': data_points
                    }
                })
            
            # Underutilized instance analysis (low but not unused)
            elif (avg_cpu < self.thresholds['underutilized_cpu_avg'] and 
                  max_cpu < self.thresholds['underutilized_cpu_max']):
                
                confidence = 'MEDIUM'
                savings_percentage = 0.3  # Default 30% savings
                
                # Enhanced analysis with memory data
                if memory_available and avg_memory:
                    if avg_memory < self.thresholds['underutilized_memory_avg']:
                        confidence = 'HIGH'
                        savings_percentage = 0.4  # 40% savings with both CPU and memory low
                        reason = f'Low utilization: {avg_cpu:.1f}% avg CPU, {max_cpu:.1f}% max CPU, {avg_memory:.1f}% avg memory'
                    else:
                        reason = f'Low CPU but normal memory: {avg_cpu:.1f}% avg CPU, {avg_memory:.1f}% avg memory'
                        savings_percentage = 0.2  # Lower savings if memory is utilized
                else:
                    reason = f'Low utilization: {avg_cpu:.1f}% avg CPU, {max_cpu:.1f}% max CPU'
                
                recommended_type = self._get_intelligent_instance_recommendation(
                    instance_data['instanceType'], 
                    avg_cpu, 
                    max_cpu, 
                    avg_memory
                )
                
                opportunities.append({
                    'type': 'rightsizing',
                    'reason': reason,
                    'priority': 'MEDIUM',
                    'estimatedSavings': instance_data.get('currentCost', 0) * savings_percentage,
                    'confidence': confidence,
                    'action': 'downsize',
                    'recommendedInstanceType': recommended_type,
                    'riskLevel': 'MEDIUM',
                    'implementationEffort': 'MEDIUM',
                    'metrics': {
                        'avgCpu': avg_cpu,
                        'maxCpu': max_cpu,
                        'avgMemory': avg_memory,
                        'cpuStdDev': cpu_std_dev,
                        'dataPoints': data_points
                    }
                })
            
            # Spot instance opportunity analysis
            elif (avg_cpu > 5.0 and max_cpu < 80.0 and cpu_std_dev < 15.0):
                # Stable workload suitable for Spot instances
                opportunities.append({
                    'type': 'pricing',
                    'reason': f'Stable workload suitable for Spot instances (CPU: {avg_cpu:.1f}% avg, {max_cpu:.1f}% max, {cpu_std_dev:.1f} std dev)',
                    'priority': 'LOW',
                    'estimatedSavings': instance_data.get('currentCost', 0) * 0.7,  # 70% savings
                    'confidence': 'MEDIUM',
                    'action': 'convert_to_spot',
                    'riskLevel': 'MEDIUM',
                    'implementationEffort': 'HIGH',
                    'metrics': {
                        'avgCpu': avg_cpu,
                        'maxCpu': max_cpu,
                        'cpuStdDev': cpu_std_dev,
                        'workloadStability': 'STABLE' if cpu_std_dev < 10.0 else 'MODERATE'
                    }
                })
            
            # Reserved Instance opportunity analysis
            elif avg_cpu > 20.0 and data_points >= 168:  # At least 1 week of consistent usage
                # Calculate uptime percentage
                launch_time = datetime.fromisoformat(instance_data['launchTime'].replace('Z', '+00:00'))
                uptime_days = (datetime.utcnow().replace(tzinfo=launch_time.tzinfo) - launch_time).days
                
                if uptime_days >= 30:  # Instance running for at least 30 days
                    opportunities.append({
                        'type': 'pricing',
                        'reason': f'Consistent usage pattern suitable for Reserved Instance (running {uptime_days} days)',
                        'priority': 'LOW',
                        'estimatedSavings': instance_data.get('currentCost', 0) * 0.3,  # 30% RI savings
                        'confidence': 'HIGH',
                        'action': 'purchase_reserved_instance',
                        'riskLevel': 'LOW',
                        'implementationEffort': 'LOW',
                        'metrics': {
                            'avgCpu': avg_cpu,
                            'uptimeDays': uptime_days,
                            'dataPoints': data_points
                        }
                    })
            
            # Network optimization opportunities
            if total_network_mb > self.thresholds['network_threshold_mb']:
                opportunities.append({
                    'type': 'networking',
                    'reason': f'High network usage: {total_network_mb:.1f} MB/hour average',
                    'priority': 'LOW',
                    'estimatedSavings': 0,  # Potential data transfer cost savings
                    'confidence': 'MEDIUM',
                    'action': 'optimize_network',
                    'riskLevel': 'LOW',
                    'implementationEffort': 'MEDIUM',
                    'metrics': {
                        'avgNetworkInMB': avg_network_in_mb,
                        'avgNetworkOutMB': avg_network_out_mb,
                        'totalNetworkMB': total_network_mb
                    }
                })
        
        else:
            # Insufficient data
            opportunities.append({
                'type': 'monitoring',
                'reason': f'Insufficient metrics data ({data_points} data points, need {self.thresholds["minimum_data_points"]})',
                'priority': 'LOW',
                'estimatedSavings': 0,
                'confidence': 'LOW',
                'action': 'monitor_longer',
                'riskLevel': 'LOW',
                'implementationEffort': 'LOW',
                'metrics': {
                    'dataPoints': data_points,
                    'requiredDataPoints': self.thresholds['minimum_data_points']
                }
            })
        
        # Governance opportunities
        governance_opportunities = self._identify_governance_opportunities(instance_data)
        opportunities.extend(governance_opportunities)
        
        return opportunities
    
    def _identify_governance_opportunities(self, instance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify governance and compliance opportunities.
        
        Args:
            instance_data: Instance metadata
            
        Returns:
            List of governance opportunities
        """
        opportunities = []
        
        # Check for missing tags (cost allocation)
        required_tags = ['Environment', 'Project', 'Owner', 'CostCenter']
        missing_tags = [tag for tag in required_tags if tag not in instance_data.get('tags', {})]
        
        if missing_tags:
            opportunities.append({
                'type': 'governance',
                'reason': f'Missing required tags: {", ".join(missing_tags)}',
                'priority': 'LOW',
                'estimatedSavings': 0,
                'confidence': 'HIGH',
                'action': 'add_tags',
                'riskLevel': 'LOW',
                'implementationEffort': 'LOW',
                'missingTags': missing_tags,
                'recommendedTags': {
                    'Environment': 'production|staging|development',
                    'Project': 'project-name',
                    'Owner': 'team-name',
                    'CostCenter': 'cost-center-id'
                }
            })
        
        # Check for old instances that might need updates (only if launchTime is available)
        if 'launchTime' in instance_data:
            try:
                launch_time = datetime.fromisoformat(instance_data['launchTime'].replace('Z', '+00:00'))
                age_days = (datetime.utcnow().replace(tzinfo=launch_time.tzinfo) - launch_time).days
                
                if age_days > 365:  # Instance older than 1 year
                    opportunities.append({
                        'type': 'governance',
                        'reason': f'Instance is {age_days} days old - consider updating or replacing',
                        'priority': 'LOW',
                        'estimatedSavings': 0,
                        'confidence': 'MEDIUM',
                        'action': 'review_age',
                        'riskLevel': 'LOW',
                        'implementationEffort': 'MEDIUM',
                        'ageDays': age_days
                    })
            except (ValueError, TypeError) as e:
                # Invalid launch time format - skip age analysis
                logger.debug(f"Could not parse launch time for governance analysis: {e}")
        
        return opportunities
    
    def _get_instance_specifications(self, instance_type: str) -> Dict[str, Any]:
        """
        Get detailed specifications for an EC2 instance type.
        
        Args:
            instance_type: EC2 instance type
            
        Returns:
            Dictionary containing instance specifications
        """
        # Comprehensive instance specifications database
        # In production, this would be fetched from AWS APIs or maintained database
        instance_specs = {
            # General Purpose - T3
            't3.nano': {'vcpus': 2, 'memory_gb': 0.5, 'network': 'Up to 5 Gigabit', 'family': 'general_purpose'},
            't3.micro': {'vcpus': 2, 'memory_gb': 1, 'network': 'Up to 5 Gigabit', 'family': 'general_purpose'},
            't3.small': {'vcpus': 2, 'memory_gb': 2, 'network': 'Up to 5 Gigabit', 'family': 'general_purpose'},
            't3.medium': {'vcpus': 2, 'memory_gb': 4, 'network': 'Up to 5 Gigabit', 'family': 'general_purpose'},
            't3.large': {'vcpus': 2, 'memory_gb': 8, 'network': 'Up to 5 Gigabit', 'family': 'general_purpose'},
            't3.xlarge': {'vcpus': 4, 'memory_gb': 16, 'network': 'Up to 5 Gigabit', 'family': 'general_purpose'},
            't3.2xlarge': {'vcpus': 8, 'memory_gb': 32, 'network': 'Up to 5 Gigabit', 'family': 'general_purpose'},
            
            # General Purpose - M5
            'm5.large': {'vcpus': 2, 'memory_gb': 8, 'network': 'Up to 10 Gigabit', 'family': 'general_purpose'},
            'm5.xlarge': {'vcpus': 4, 'memory_gb': 16, 'network': 'Up to 10 Gigabit', 'family': 'general_purpose'},
            'm5.2xlarge': {'vcpus': 8, 'memory_gb': 32, 'network': 'Up to 10 Gigabit', 'family': 'general_purpose'},
            'm5.4xlarge': {'vcpus': 16, 'memory_gb': 64, 'network': 'Up to 10 Gigabit', 'family': 'general_purpose'},
            'm5.8xlarge': {'vcpus': 32, 'memory_gb': 128, 'network': '10 Gigabit', 'family': 'general_purpose'},
            
            # Compute Optimized - C5
            'c5.large': {'vcpus': 2, 'memory_gb': 4, 'network': 'Up to 10 Gigabit', 'family': 'compute_optimized'},
            'c5.xlarge': {'vcpus': 4, 'memory_gb': 8, 'network': 'Up to 10 Gigabit', 'family': 'compute_optimized'},
            'c5.2xlarge': {'vcpus': 8, 'memory_gb': 16, 'network': 'Up to 10 Gigabit', 'family': 'compute_optimized'},
            'c5.4xlarge': {'vcpus': 16, 'memory_gb': 32, 'network': 'Up to 10 Gigabit', 'family': 'compute_optimized'},
            
            # Memory Optimized - R5
            'r5.large': {'vcpus': 2, 'memory_gb': 16, 'network': 'Up to 10 Gigabit', 'family': 'memory_optimized'},
            'r5.xlarge': {'vcpus': 4, 'memory_gb': 32, 'network': 'Up to 10 Gigabit', 'family': 'memory_optimized'},
            'r5.2xlarge': {'vcpus': 8, 'memory_gb': 64, 'network': 'Up to 10 Gigabit', 'family': 'memory_optimized'},
            'r5.4xlarge': {'vcpus': 16, 'memory_gb': 128, 'network': 'Up to 10 Gigabit', 'family': 'memory_optimized'},
        }
        
        return instance_specs.get(instance_type, {
            'vcpus': 'unknown',
            'memory_gb': 'unknown',
            'network': 'unknown',
            'family': 'unknown'
        })
    
    def _get_intelligent_instance_recommendation(self, 
                                               current_type: str, 
                                               avg_cpu: float, 
                                               max_cpu: float,
                                               avg_memory: Optional[float] = None) -> str:
        """
        Get intelligent instance type recommendation based on utilization patterns.
        
        Args:
            current_type: Current EC2 instance type
            avg_cpu: Average CPU utilization
            max_cpu: Maximum CPU utilization
            avg_memory: Average memory utilization (if available)
            
        Returns:
            Recommended instance type
        """
        current_specs = self._get_instance_specifications(current_type)
        current_vcpus = current_specs.get('vcpus', 2)
        current_memory = current_specs.get('memory_gb', 4)
        
        # Calculate recommended resources based on utilization
        # Add 20% buffer for safety
        recommended_cpu_ratio = max(max_cpu / 100.0 * 1.2, 0.1)  # At least 10% utilization target
        
        if avg_memory:
            recommended_memory_ratio = max(avg_memory / 100.0 * 1.2, 0.2)  # At least 20% utilization target
        else:
            recommended_memory_ratio = 0.5  # Conservative estimate if no memory data
        
        # Instance type recommendations based on family and utilization
        recommendations = {
            # T3 family downsizing
            't3.2xlarge': 't3.xlarge' if recommended_cpu_ratio < 0.4 else 't3.2xlarge',
            't3.xlarge': 't3.large' if recommended_cpu_ratio < 0.4 else 't3.xlarge',
            't3.large': 't3.medium' if recommended_cpu_ratio < 0.4 else 't3.large',
            't3.medium': 't3.small' if recommended_cpu_ratio < 0.4 else 't3.medium',
            't3.small': 't3.micro' if recommended_cpu_ratio < 0.4 else 't3.small',
            
            # M5 family downsizing
            'm5.4xlarge': 'm5.2xlarge' if recommended_cpu_ratio < 0.4 else 'm5.4xlarge',
            'm5.2xlarge': 'm5.xlarge' if recommended_cpu_ratio < 0.4 else 'm5.2xlarge',
            'm5.xlarge': 'm5.large' if recommended_cpu_ratio < 0.4 else 'm5.xlarge',
            'm5.large': 't3.large' if recommended_cpu_ratio < 0.3 else 'm5.large',
            
            # C5 family downsizing
            'c5.4xlarge': 'c5.2xlarge' if recommended_cpu_ratio < 0.4 else 'c5.4xlarge',
            'c5.2xlarge': 'c5.xlarge' if recommended_cpu_ratio < 0.4 else 'c5.2xlarge',
            'c5.xlarge': 'c5.large' if recommended_cpu_ratio < 0.4 else 'c5.xlarge',
            'c5.large': 't3.medium' if recommended_cpu_ratio < 0.3 else 'c5.large',
            
            # R5 family downsizing (consider memory usage)
            'r5.4xlarge': 'r5.2xlarge' if recommended_memory_ratio < 0.4 else 'r5.4xlarge',
            'r5.2xlarge': 'r5.xlarge' if recommended_memory_ratio < 0.4 else 'r5.2xlarge',
            'r5.xlarge': 'r5.large' if recommended_memory_ratio < 0.4 else 'r5.xlarge',
            'r5.large': 'm5.large' if recommended_memory_ratio < 0.3 else 'r5.large',
        }
        
        return recommendations.get(current_type, current_type)
    
    def _get_comprehensive_cost_analysis(self, 
                                       instance_type: str, 
                                       platform: str = 'linux',
                                       include_regional_comparison: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive cost analysis including regional comparison.
        
        Args:
            instance_type: EC2 instance type
            platform: Operating system platform
            include_regional_comparison: Whether to include regional cost comparison
            
        Returns:
            Dictionary containing cost analysis
        """
        cost_analysis = {
            'currentCost': self._estimate_instance_cost(instance_type, platform),
            'platform': platform,
            'instanceType': instance_type,
            'region': self.region
        }
        
        if include_regional_comparison:
            regional_costs = self._get_regional_cost_comparison(instance_type, platform)
            cost_analysis['regionalComparison'] = regional_costs
            
            # Find cheapest region
            if regional_costs:
                cheapest_region = min(regional_costs.items(), key=lambda x: x[1]['monthlyCost'])
                cost_analysis['cheapestRegion'] = {
                    'region': cheapest_region[0],
                    'monthlyCost': cheapest_region[1]['monthlyCost'],
                    'potentialSavings': cost_analysis['currentCost'] - cheapest_region[1]['monthlyCost']
                }
        
        return cost_analysis
    
    def _get_regional_cost_comparison(self, instance_type: str, platform: str = 'linux') -> Dict[str, Dict[str, Any]]:
        """
        Get cost comparison across AWS regions for an instance type.
        
        Args:
            instance_type: EC2 instance type
            platform: Operating system platform
            
        Returns:
            Dictionary with regional cost comparison
        """
        # Major AWS regions for cost comparison
        regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-central-1',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
        ]
        
        regional_costs = {}
        
        for region in regions:
            try:
                # Use cached pricing if available
                cache_key = f"{region}_{instance_type}_{platform}"
                if cache_key in self.regional_pricing_cache:
                    regional_costs[region] = self.regional_pricing_cache[cache_key]
                    continue
                
                # Estimate cost for region (simplified - would use AWS Price List API in production)
                base_cost = self._estimate_instance_cost(instance_type, platform)
                
                # Regional pricing multipliers (approximate)
                regional_multipliers = {
                    'us-east-1': 1.0,      # Base region
                    'us-east-2': 0.95,     # Slightly cheaper
                    'us-west-1': 1.15,     # More expensive
                    'us-west-2': 1.05,     # Slightly more expensive
                    'eu-west-1': 1.10,     # Europe premium
                    'eu-west-2': 1.12,     # UK premium
                    'eu-central-1': 1.08,  # Germany
                    'ap-southeast-1': 1.20, # Singapore premium
                    'ap-southeast-2': 1.18, # Sydney
                    'ap-northeast-1': 1.15, # Tokyo
                }
                
                multiplier = regional_multipliers.get(region, 1.0)
                regional_cost = base_cost * multiplier
                
                cost_data = {
                    'monthlyCost': regional_cost,
                    'multiplier': multiplier,
                    'currency': 'USD'
                }
                
                regional_costs[region] = cost_data
                self.regional_pricing_cache[cache_key] = cost_data
                
            except Exception as e:
                logger.debug(f"Failed to get pricing for {region}: {e}")
                continue
        
        return regional_costs
    
    def _generate_regional_cost_summary(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate regional cost comparison summary for all instances.
        
        Args:
            instances: List of analyzed instances
            
        Returns:
            Regional cost summary
        """
        regional_summary = {}
        total_current_cost = 0
        total_potential_savings = 0
        
        for instance in instances:
            if 'regionalComparison' in instance:
                total_current_cost += instance.get('currentCost', 0)
                
                cheapest_region_data = instance.get('cheapestRegion', {})
                if cheapest_region_data:
                    potential_savings = cheapest_region_data.get('potentialSavings', 0)
                    if potential_savings > 0:
                        total_potential_savings += potential_savings
                        
                        region = cheapest_region_data['region']
                        if region not in regional_summary:
                            regional_summary[region] = {
                                'instanceCount': 0,
                                'totalSavings': 0,
                                'instances': []
                            }
                        
                        regional_summary[region]['instanceCount'] += 1
                        regional_summary[region]['totalSavings'] += potential_savings
                        regional_summary[region]['instances'].append({
                            'instanceId': instance['resourceId'],
                            'instanceType': instance['instanceType'],
                            'currentCost': instance.get('currentCost', 0),
                            'potentialSavings': potential_savings
                        })
        
        return {
            'totalCurrentCost': total_current_cost,
            'totalPotentialSavings': total_potential_savings,
            'savingsPercentage': (total_potential_savings / total_current_cost * 100) if total_current_cost > 0 else 0,
            'recommendedRegions': regional_summary
        }
    
    def _estimate_instance_cost(self, instance_type: str, platform: str = 'linux') -> float:
        """
        Estimate monthly cost for an EC2 instance with enhanced pricing data.
        
        Args:
            instance_type: EC2 instance type
            platform: Operating system platform
            
        Returns:
            Estimated monthly cost in USD
        """
        # Enhanced cost estimation with more instance types and current pricing
        # These are approximate costs for us-east-1 region (as of 2024)
        
        base_costs = {
            # General Purpose - T3 (Burstable)
            't3.nano': 3.80,
            't3.micro': 7.59,
            't3.small': 15.18,
            't3.medium': 30.37,
            't3.large': 60.74,
            't3.xlarge': 121.47,
            't3.2xlarge': 242.94,
            
            # General Purpose - M5
            'm5.large': 87.60,
            'm5.xlarge': 175.20,
            'm5.2xlarge': 350.40,
            'm5.4xlarge': 700.80,
            'm5.8xlarge': 1401.60,
            'm5.12xlarge': 2102.40,
            'm5.16xlarge': 2803.20,
            'm5.24xlarge': 4204.80,
            
            # Compute Optimized - C5
            'c5.large': 78.84,
            'c5.xlarge': 157.68,
            'c5.2xlarge': 315.36,
            'c5.4xlarge': 630.72,
            'c5.9xlarge': 1419.12,
            'c5.12xlarge': 1892.16,
            'c5.18xlarge': 2838.24,
            'c5.24xlarge': 3784.32,
            
            # Memory Optimized - R5
            'r5.large': 115.34,
            'r5.xlarge': 230.69,
            'r5.2xlarge': 461.38,
            'r5.4xlarge': 922.75,
            'r5.8xlarge': 1845.50,
            'r5.12xlarge': 2768.26,
            'r5.16xlarge': 3691.01,
            'r5.24xlarge': 5536.51,
            
            # Storage Optimized - I3
            'i3.large': 142.56,
            'i3.xlarge': 285.12,
            'i3.2xlarge': 570.24,
            'i3.4xlarge': 1140.48,
            'i3.8xlarge': 2280.96,
            'i3.16xlarge': 4561.92,
        }
        
        base_cost = base_costs.get(instance_type, 100.0)  # Default fallback
        
        # Platform-specific pricing adjustments
        if platform == 'windows':
            base_cost *= 1.5  # Windows licensing cost
        elif platform == 'rhel':
            base_cost *= 1.2  # Red Hat licensing cost
        elif platform == 'suse':
            base_cost *= 1.15  # SUSE licensing cost
        
        return round(base_cost, 2)
    
    def get_enhanced_optimization_summary(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive optimization summary for scanned instances.
        
        Args:
            instances: List of analyzed instances
            
        Returns:
            Enhanced optimization summary with detailed metrics
        """
        summary = {
            'totalInstances': len(instances),
            'runningInstances': 0,
            'stoppedInstances': 0,
            'totalMonthlyCost': 0.0,
            'potentialMonthlySavings': 0.0,
            'regionalSavingsOpportunity': 0.0,
            'optimizationOpportunities': {
                'cleanup': 0,
                'rightsizing': 0,
                'pricing': 0,
                'governance': 0,
                'monitoring': 0,
                'networking': 0
            },
            'priorityBreakdown': {
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'confidenceBreakdown': {
                'VERY_HIGH': 0,
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'riskBreakdown': {
                'LOW': 0,
                'MEDIUM': 0,
                'HIGH': 0,
                'CRITICAL': 0
            },
            'instanceFamilyBreakdown': {},
            'utilizationStats': {
                'avgCpuUtilization': 0.0,
                'avgMemoryUtilization': 0.0,
                'instancesWithMemoryData': 0,
                'underutilizedInstances': 0,
                'unusedInstances': 0
            },
            'costOptimizationPotential': {
                'immediateActions': 0,
                'mediumTermActions': 0,
                'longTermActions': 0
            }
        }
        
        cpu_utilizations = []
        memory_utilizations = []
        
        for instance in instances:
            # Count by state
            if instance['state'] == 'running':
                summary['runningInstances'] += 1
            elif instance['state'] == 'stopped':
                summary['stoppedInstances'] += 1
            
            # Sum costs
            current_cost = instance.get('currentCost', 0)
            summary['totalMonthlyCost'] += current_cost
            
            # Regional savings opportunity
            cheapest_region = instance.get('cheapestRegion', {})
            if cheapest_region:
                regional_savings = cheapest_region.get('potentialSavings', 0)
                if regional_savings > 0:
                    summary['regionalSavingsOpportunity'] += regional_savings
            
            # Instance family breakdown
            instance_type = instance.get('instanceType', 'unknown')
            family = instance_type.split('.')[0] if '.' in instance_type else 'unknown'
            if family not in summary['instanceFamilyBreakdown']:
                summary['instanceFamilyBreakdown'][family] = {
                    'count': 0,
                    'totalCost': 0,
                    'avgUtilization': 0
                }
            summary['instanceFamilyBreakdown'][family]['count'] += 1
            summary['instanceFamilyBreakdown'][family]['totalCost'] += current_cost
            
            # Utilization statistics
            metrics = instance.get('utilizationMetrics', {})
            avg_cpu = metrics.get('avgCpuUtilization', 0)
            avg_memory = metrics.get('avgMemoryUtilization')
            
            if avg_cpu > 0:
                cpu_utilizations.append(avg_cpu)
                summary['instanceFamilyBreakdown'][family]['avgUtilization'] += avg_cpu
                
                # Categorize utilization
                if avg_cpu < self.thresholds['unused_cpu_avg']:
                    summary['utilizationStats']['unusedInstances'] += 1
                elif avg_cpu < self.thresholds['underutilized_cpu_avg']:
                    summary['utilizationStats']['underutilizedInstances'] += 1
            
            if avg_memory is not None:
                memory_utilizations.append(avg_memory)
                summary['utilizationStats']['instancesWithMemoryData'] += 1
            
            # Analyze opportunities
            for opportunity in instance.get('optimizationOpportunities', []):
                opp_type = opportunity.get('type', 'unknown')
                priority = opportunity.get('priority', 'LOW')
                confidence = opportunity.get('confidence', 'LOW')
                risk_level = opportunity.get('riskLevel', 'LOW')
                savings = opportunity.get('estimatedSavings', 0)
                
                # Count by type
                if opp_type in summary['optimizationOpportunities']:
                    summary['optimizationOpportunities'][opp_type] += 1
                
                # Count by priority
                if priority in summary['priorityBreakdown']:
                    summary['priorityBreakdown'][priority] += 1
                
                # Count by confidence
                if confidence in summary['confidenceBreakdown']:
                    summary['confidenceBreakdown'][confidence] += 1
                
                # Count by risk
                if risk_level in summary['riskBreakdown']:
                    summary['riskBreakdown'][risk_level] += 1
                
                # Categorize by implementation timeline
                if priority == 'HIGH' and confidence in ['HIGH', 'VERY_HIGH']:
                    summary['costOptimizationPotential']['immediateActions'] += 1
                elif priority == 'MEDIUM':
                    summary['costOptimizationPotential']['mediumTermActions'] += 1
                else:
                    summary['costOptimizationPotential']['longTermActions'] += 1
                
                summary['potentialMonthlySavings'] += savings
        
        # Calculate average utilizations
        if cpu_utilizations:
            summary['utilizationStats']['avgCpuUtilization'] = statistics.mean(cpu_utilizations)
        
        if memory_utilizations:
            summary['utilizationStats']['avgMemoryUtilization'] = statistics.mean(memory_utilizations)
        
        # Calculate average utilization per family
        for family_data in summary['instanceFamilyBreakdown'].values():
            if family_data['count'] > 0:
                family_data['avgUtilization'] /= family_data['count']
        
        # Calculate savings percentages
        if summary['totalMonthlyCost'] > 0:
            summary['savingsPercentage'] = (summary['potentialMonthlySavings'] / summary['totalMonthlyCost']) * 100
            summary['regionalSavingsPercentage'] = (summary['regionalSavingsOpportunity'] / summary['totalMonthlyCost']) * 100
        else:
            summary['savingsPercentage'] = 0.0
            summary['regionalSavingsPercentage'] = 0.0
        
        # Add recommendations summary
        summary['recommendations'] = {
            'topPriority': 'Terminate unused instances' if summary['utilizationStats']['unusedInstances'] > 0 else 'Right-size underutilized instances',
            'quickWins': summary['costOptimizationPotential']['immediateActions'],
            'totalOpportunities': sum(summary['optimizationOpportunities'].values()),
            'estimatedImplementationTime': self._estimate_implementation_time(summary)
        }
        
        return summary
    
    def _estimate_implementation_time(self, summary: Dict[str, Any]) -> str:
        """
        Estimate total implementation time for all optimizations.
        
        Args:
            summary: Optimization summary
            
        Returns:
            Estimated implementation time
        """
        immediate = summary['costOptimizationPotential']['immediateActions']
        medium_term = summary['costOptimizationPotential']['mediumTermActions']
        long_term = summary['costOptimizationPotential']['longTermActions']
        
        # Rough time estimates
        immediate_hours = immediate * 0.5  # 30 minutes per immediate action
        medium_hours = medium_term * 2    # 2 hours per medium-term action
        long_hours = long_term * 8        # 8 hours per long-term action
        
        total_hours = immediate_hours + medium_hours + long_hours
        
        if total_hours < 8:
            return f"{total_hours:.1f} hours"
        elif total_hours < 40:
            return f"{total_hours/8:.1f} days"
        else:
            return f"{total_hours/40:.1f} weeks"
    
    def get_instance_count_by_state(self) -> Dict[str, int]:
        """
        Get count of instances by state.
        
        Returns:
            Dictionary with state counts
        """
        try:
            response = self.ec2_client.describe_instances()
            
            state_counts = {}
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    state = instance.get('State', {}).get('Name', 'unknown')
                    state_counts[state] = state_counts.get(state, 0) + 1
            
            return state_counts
            
        except ClientError as e:
            logger.error(f"Failed to get instance counts: {e}")
            return {}
    
    def get_optimization_summary(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate optimization summary for scanned instances (legacy method).
        
        Args:
            instances: List of analyzed instances
            
        Returns:
            Optimization summary (calls enhanced version)
        """
        # Delegate to enhanced method for backward compatibility
        return self.get_enhanced_optimization_summary(instances)