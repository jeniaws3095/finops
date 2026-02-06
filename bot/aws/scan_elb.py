#!/usr/bin/env python3
"""
ELB (Elastic Load Balancer) Scanner for Advanced FinOps Platform

Discovers and analyzes Elastic Load Balancers across regions, collecting:
- Load balancer metadata and configuration
- Target group health and utilization metrics
- Request patterns and connection metrics from CloudWatch
- Cost data and optimization opportunities
- Unused load balancers and target group analysis

Requirements: 1.1, 7.5
"""

import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class ELBScanner:
    """Scans Elastic Load Balancers for cost optimization opportunities."""
    
    def __init__(self, aws_config, region: str = 'us-east-1'):
        """
        Initialize ELB scanner.
        
        Args:
            aws_config: AWSConfig instance for client management
            region: AWS region to scan
        """
        self.aws_config = aws_config
        self.region = region
        self.elbv2_client = aws_config.get_client('elbv2')  # Application/Network Load Balancers
        self.elb_client = aws_config.get_client('elb')      # Classic Load Balancers
        self.cloudwatch_client = aws_config.get_client('cloudwatch')
        
        logger.info(f"ELB Scanner initialized for region {region}")
    
    def scan_load_balancers(self, days_back: int = 14) -> List[Dict[str, Any]]:
        """
        Scan all load balancers in the region.
        
        Args:
            days_back: Number of days to look back for metrics
            
        Returns:
            List of load balancer data with utilization metrics
        """
        logger.info(f"Starting ELB scan in region {self.region}")
        
        load_balancers = []
        
        try:
            # Scan Application and Network Load Balancers (ELBv2)
            alb_nlb_data = self._scan_application_network_load_balancers(days_back)
            load_balancers.extend(alb_nlb_data)
            
            # Scan Classic Load Balancers (ELBv1)
            clb_data = self._scan_classic_load_balancers(days_back)
            load_balancers.extend(clb_data)
            
            logger.info(f"Scanned {len(load_balancers)} load balancers")
            
        except ClientError as e:
            logger.error(f"Failed to scan load balancers: {e}")
            raise
        
        return load_balancers
    
    def _scan_application_network_load_balancers(self, days_back: int) -> List[Dict[str, Any]]:
        """
        Scan Application and Network Load Balancers (ELBv2).
        
        Args:
            days_back: Number of days to analyze metrics
            
        Returns:
            List of ALB/NLB data
        """
        load_balancers = []
        
        try:
            # Get all ALBs and NLBs
            paginator = self.elbv2_client.get_paginator('describe_load_balancers')
            
            for page in paginator.paginate():
                for lb in page['LoadBalancers']:
                    lb_data = self._analyze_application_network_load_balancer(lb, days_back)
                    if lb_data:
                        load_balancers.append(lb_data)
            
        except ClientError as e:
            logger.error(f"Failed to scan ALB/NLB load balancers: {e}")
            raise
        
        return load_balancers
    
    def _scan_classic_load_balancers(self, days_back: int) -> List[Dict[str, Any]]:
        """
        Scan Classic Load Balancers (ELBv1).
        
        Args:
            days_back: Number of days to analyze metrics
            
        Returns:
            List of CLB data
        """
        load_balancers = []
        
        try:
            # Get all Classic Load Balancers
            paginator = self.elb_client.get_paginator('describe_load_balancers')
            
            for page in paginator.paginate():
                for lb in page['LoadBalancerDescriptions']:
                    lb_data = self._analyze_classic_load_balancer(lb, days_back)
                    if lb_data:
                        load_balancers.append(lb_data)
            
        except ClientError as e:
            logger.error(f"Failed to scan Classic load balancers: {e}")
            raise
        
        return load_balancers
    
    def _analyze_application_network_load_balancer(self, lb: Dict[str, Any], days_back: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single Application or Network Load Balancer.
        
        Args:
            lb: Load balancer data from describe_load_balancers
            days_back: Number of days to analyze metrics
            
        Returns:
            Load balancer analysis data or None if analysis fails
        """
        lb_arn = lb['LoadBalancerArn']
        lb_name = lb['LoadBalancerName']
        
        try:
            # Basic load balancer information
            lb_data = {
                'resourceId': lb_arn,
                'resourceType': 'elb',
                'region': self.region,
                'loadBalancerName': lb_name,
                'loadBalancerType': lb.get('Type', 'application'),  # application, network, gateway
                'scheme': lb.get('Scheme', 'internet-facing'),
                'state': lb.get('State', {}).get('Code', 'unknown'),
                'vpcId': lb.get('VpcId'),
                'availabilityZones': [az.get('ZoneName') for az in lb.get('AvailabilityZones', [])],
                'createdTime': lb.get('CreatedTime', datetime.utcnow()).isoformat(),
                'dnsName': lb.get('DNSName'),
                'canonicalHostedZoneId': lb.get('CanonicalHostedZoneId'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Get load balancer attributes
            try:
                attributes_response = self.elbv2_client.describe_load_balancer_attributes(
                    LoadBalancerArn=lb_arn
                )
                attributes = {}
                for attr in attributes_response.get('Attributes', []):
                    attributes[attr['Key']] = attr['Value']
                lb_data['attributes'] = attributes
            except ClientError as e:
                logger.warning(f"Failed to get attributes for load balancer {lb_name}: {e}")
                lb_data['attributes'] = {}
            
            # Get target groups
            target_groups = self._get_target_groups(lb_arn)
            lb_data['targetGroups'] = target_groups
            lb_data['targetGroupCount'] = len(target_groups)
            
            # Calculate total healthy targets
            total_healthy_targets = sum(tg.get('healthyTargetCount', 0) for tg in target_groups)
            total_targets = sum(tg.get('totalTargetCount', 0) for tg in target_groups)
            lb_data['totalHealthyTargets'] = total_healthy_targets
            lb_data['totalTargets'] = total_targets
            
            # Get load balancer tags
            try:
                tags_response = self.elbv2_client.describe_tags(ResourceArns=[lb_arn])
                tags = {}
                for tag_description in tags_response.get('TagDescriptions', []):
                    for tag in tag_description.get('Tags', []):
                        tags[tag['Key']] = tag['Value']
                lb_data['tags'] = tags
            except ClientError as e:
                logger.warning(f"Failed to get tags for load balancer {lb_name}: {e}")
                lb_data['tags'] = {}
            
            # Get utilization metrics only for active load balancers
            if lb_data['state'] == 'active':
                metrics = self._get_load_balancer_metrics(lb_name, lb_data['loadBalancerType'], days_back)
                lb_data['utilizationMetrics'] = metrics
                
                # Calculate optimization opportunities
                opportunities = self._identify_optimization_opportunities(lb_data, metrics, target_groups)
                lb_data['optimizationOpportunities'] = opportunities
                
                # Estimate current cost
                lb_data['currentCost'] = self._estimate_load_balancer_cost(
                    lb_data['loadBalancerType'],
                    len(lb_data['availabilityZones']),
                    metrics
                )
            else:
                # For inactive load balancers, mark as potential cleanup
                lb_data['utilizationMetrics'] = {}
                lb_data['optimizationOpportunities'] = [{
                    'type': 'cleanup',
                    'reason': f'Load balancer in {lb_data["state"]} state',
                    'priority': 'HIGH',
                    'estimatedSavings': self._estimate_load_balancer_cost(
                        lb_data['loadBalancerType'],
                        len(lb_data['availabilityZones']),
                        {}
                    ),
                    'confidence': 'HIGH',
                    'action': 'review_necessity'
                }]
                lb_data['currentCost'] = 0.0
            
            return lb_data
            
        except Exception as e:
            logger.error(f"Failed to analyze load balancer {lb_name}: {e}")
            return None
    
    def _analyze_classic_load_balancer(self, lb: Dict[str, Any], days_back: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single Classic Load Balancer.
        
        Args:
            lb: Load balancer data from describe_load_balancers
            days_back: Number of days to analyze metrics
            
        Returns:
            Load balancer analysis data or None if analysis fails
        """
        lb_name = lb['LoadBalancerName']
        
        try:
            # Basic load balancer information
            lb_data = {
                'resourceId': lb_name,  # Classic LBs use name as ID
                'resourceType': 'elb',
                'region': self.region,
                'loadBalancerName': lb_name,
                'loadBalancerType': 'classic',
                'scheme': lb.get('Scheme', 'internet-facing'),
                'state': 'active',  # Classic LBs don't have state in API response
                'vpcId': lb.get('VPCId'),
                'availabilityZones': lb.get('AvailabilityZones', []),
                'createdTime': lb.get('CreatedTime', datetime.utcnow()).isoformat(),
                'dnsName': lb.get('DNSName'),
                'canonicalHostedZoneId': lb.get('CanonicalHostedZoneNameID'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Get load balancer attributes
            try:
                attributes_response = self.elb_client.describe_load_balancer_attributes(
                    LoadBalancerName=lb_name
                )
                lb_data['attributes'] = attributes_response.get('LoadBalancerAttributes', {})
            except ClientError as e:
                logger.warning(f"Failed to get attributes for Classic load balancer {lb_name}: {e}")
                lb_data['attributes'] = {}
            
            # Get instance health
            try:
                health_response = self.elb_client.describe_instance_health(
                    LoadBalancerName=lb_name
                )
                instance_states = health_response.get('InstanceStates', [])
                healthy_instances = [inst for inst in instance_states if inst.get('State') == 'InService']
                
                lb_data['totalTargets'] = len(instance_states)
                lb_data['totalHealthyTargets'] = len(healthy_instances)
                lb_data['instanceStates'] = instance_states
            except ClientError as e:
                logger.warning(f"Failed to get instance health for Classic load balancer {lb_name}: {e}")
                lb_data['totalTargets'] = 0
                lb_data['totalHealthyTargets'] = 0
                lb_data['instanceStates'] = []
            
            # Get load balancer tags
            try:
                tags_response = self.elb_client.describe_tags(LoadBalancerNames=[lb_name])
                tags = {}
                for tag_description in tags_response.get('TagDescriptions', []):
                    for tag in tag_description.get('Tags', []):
                        tags[tag['Key']] = tag['Value']
                lb_data['tags'] = tags
            except ClientError as e:
                logger.warning(f"Failed to get tags for Classic load balancer {lb_name}: {e}")
                lb_data['tags'] = {}
            
            # Get utilization metrics
            metrics = self._get_classic_load_balancer_metrics(lb_name, days_back)
            lb_data['utilizationMetrics'] = metrics
            
            # Calculate optimization opportunities
            opportunities = self._identify_classic_optimization_opportunities(lb_data, metrics)
            lb_data['optimizationOpportunities'] = opportunities
            
            # Estimate current cost
            lb_data['currentCost'] = self._estimate_load_balancer_cost(
                'classic',
                len(lb_data['availabilityZones']),
                metrics
            )
            
            return lb_data
            
        except Exception as e:
            logger.error(f"Failed to analyze Classic load balancer {lb_name}: {e}")
            return None
    
    def _get_target_groups(self, lb_arn: str) -> List[Dict[str, Any]]:
        """
        Get target groups for an Application/Network Load Balancer.
        
        Args:
            lb_arn: Load balancer ARN
            
        Returns:
            List of target group data
        """
        target_groups = []
        
        try:
            # Get target groups for this load balancer
            response = self.elbv2_client.describe_target_groups(LoadBalancerArn=lb_arn)
            
            for tg in response.get('TargetGroups', []):
                tg_arn = tg['TargetGroupArn']
                tg_name = tg['TargetGroupName']
                
                # Get target health
                try:
                    health_response = self.elbv2_client.describe_target_health(
                        TargetGroupArn=tg_arn
                    )
                    target_health = health_response.get('TargetHealthDescriptions', [])
                    healthy_targets = [t for t in target_health if t.get('TargetHealth', {}).get('State') == 'healthy']
                    
                    target_group_data = {
                        'targetGroupArn': tg_arn,
                        'targetGroupName': tg_name,
                        'protocol': tg.get('Protocol'),
                        'port': tg.get('Port'),
                        'targetType': tg.get('TargetType', 'instance'),
                        'healthCheckPath': tg.get('HealthCheckPath'),
                        'healthCheckProtocol': tg.get('HealthCheckProtocol'),
                        'totalTargetCount': len(target_health),
                        'healthyTargetCount': len(healthy_targets),
                        'targets': target_health
                    }
                    
                    target_groups.append(target_group_data)
                    
                except ClientError as e:
                    logger.warning(f"Failed to get target health for target group {tg_name}: {e}")
                    target_groups.append({
                        'targetGroupArn': tg_arn,
                        'targetGroupName': tg_name,
                        'protocol': tg.get('Protocol'),
                        'port': tg.get('Port'),
                        'targetType': tg.get('TargetType', 'instance'),
                        'totalTargetCount': 0,
                        'healthyTargetCount': 0,
                        'targets': []
                    })
            
        except ClientError as e:
            logger.warning(f"Failed to get target groups for load balancer: {e}")
        
        return target_groups
    
    def _get_load_balancer_metrics(self, lb_name: str, lb_type: str, days_back: int) -> Dict[str, Any]:
        """
        Get CloudWatch metrics for an Application/Network Load Balancer.
        
        Args:
            lb_name: Load balancer name
            lb_type: Load balancer type (application, network)
            days_back: Number of days to retrieve metrics
            
        Returns:
            Dictionary containing utilization metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        metrics = {
            'requestCount': [],
            'targetResponseTime': [],
            'httpCodeTarget2XX': [],
            'httpCodeTarget4XX': [],
            'httpCodeTarget5XX': [],
            'activeConnectionCount': [],
            'newConnectionCount': [],
            'period': f"{days_back} days",
            'dataPoints': 0
        }
        
        try:
            # Request Count
            request_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApplicationELB' if lb_type == 'application' else 'AWS/NetworkELB',
                MetricName='RequestCount',
                Dimensions=[
                    {
                        'Name': 'LoadBalancer',
                        'Value': lb_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['Sum']
            )
            
            request_datapoints = sorted(request_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['requestCount'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in request_datapoints
            ]
            
            # Target Response Time (ALB only)
            if lb_type == 'application':
                response_time_response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/ApplicationELB',
                    MetricName='TargetResponseTime',
                    Dimensions=[
                        {
                            'Name': 'LoadBalancer',
                            'Value': lb_name
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average']
                )
                
                response_time_datapoints = sorted(response_time_response['Datapoints'], key=lambda x: x['Timestamp'])
                metrics['targetResponseTime'] = [
                    {
                        'timestamp': dp['Timestamp'].isoformat(),
                        'average': dp['Average']
                    }
                    for dp in response_time_datapoints
                ]
                
                # HTTP response codes (ALB only)
                for code in ['2XX', '4XX', '5XX']:
                    try:
                        code_response = self.cloudwatch_client.get_metric_statistics(
                            Namespace='AWS/ApplicationELB',
                            MetricName=f'HTTPCode_Target_{code}_Count',
                            Dimensions=[
                                {
                                    'Name': 'LoadBalancer',
                                    'Value': lb_name
                                }
                            ],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=3600,
                            Statistics=['Sum']
                        )
                        
                        code_datapoints = sorted(code_response['Datapoints'], key=lambda x: x['Timestamp'])
                        metrics[f'httpCodeTarget{code}'] = [
                            {
                                'timestamp': dp['Timestamp'].isoformat(),
                                'sum': dp['Sum']
                            }
                            for dp in code_datapoints
                        ]
                    except ClientError:
                        metrics[f'httpCodeTarget{code}'] = []
            
            # Active Connection Count
            active_conn_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApplicationELB' if lb_type == 'application' else 'AWS/NetworkELB',
                MetricName='ActiveConnectionCount',
                Dimensions=[
                    {
                        'Name': 'LoadBalancer',
                        'Value': lb_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )
            
            active_conn_datapoints = sorted(active_conn_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['activeConnectionCount'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average']
                }
                for dp in active_conn_datapoints
            ]
            
            # New Connection Count
            new_conn_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApplicationELB' if lb_type == 'application' else 'AWS/NetworkELB',
                MetricName='NewConnectionCount',
                Dimensions=[
                    {
                        'Name': 'LoadBalancer',
                        'Value': lb_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            new_conn_datapoints = sorted(new_conn_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['newConnectionCount'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in new_conn_datapoints
            ]
            
            # Calculate summary statistics
            if metrics['requestCount']:
                total_requests = sum(dp['sum'] for dp in metrics['requestCount'])
                metrics['totalRequests'] = total_requests
                metrics['avgRequestsPerHour'] = total_requests / len(metrics['requestCount'])
                metrics['dataPoints'] = len(metrics['requestCount'])
            else:
                metrics['totalRequests'] = 0
                metrics['avgRequestsPerHour'] = 0
                metrics['dataPoints'] = 0
            
            if metrics['activeConnectionCount']:
                avg_connections = sum(dp['average'] for dp in metrics['activeConnectionCount']) / len(metrics['activeConnectionCount'])
                metrics['avgActiveConnections'] = avg_connections
            else:
                metrics['avgActiveConnections'] = 0
            
            if metrics['targetResponseTime']:
                avg_response_time = sum(dp['average'] for dp in metrics['targetResponseTime']) / len(metrics['targetResponseTime'])
                metrics['avgResponseTime'] = avg_response_time
            else:
                metrics['avgResponseTime'] = 0
            
            logger.debug(f"Retrieved {metrics['dataPoints']} metric data points for load balancer {lb_name}")
            
        except ClientError as e:
            logger.warning(f"Failed to retrieve metrics for load balancer {lb_name}: {e}")
            # Return empty metrics on failure
            metrics.update({
                'totalRequests': 0,
                'avgRequestsPerHour': 0,
                'avgActiveConnections': 0,
                'avgResponseTime': 0
            })
        
        return metrics
    
    def _get_classic_load_balancer_metrics(self, lb_name: str, days_back: int) -> Dict[str, Any]:
        """
        Get CloudWatch metrics for a Classic Load Balancer.
        
        Args:
            lb_name: Load balancer name
            days_back: Number of days to retrieve metrics
            
        Returns:
            Dictionary containing utilization metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        metrics = {
            'requestCount': [],
            'latency': [],
            'httpCodeELB4XX': [],
            'httpCodeELB5XX': [],
            'httpCodeBackend2XX': [],
            'httpCodeBackend4XX': [],
            'httpCodeBackend5XX': [],
            'period': f"{days_back} days",
            'dataPoints': 0
        }
        
        try:
            # Request Count
            request_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ELB',
                MetricName='RequestCount',
                Dimensions=[
                    {
                        'Name': 'LoadBalancerName',
                        'Value': lb_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['Sum']
            )
            
            request_datapoints = sorted(request_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['requestCount'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in request_datapoints
            ]
            
            # Latency
            latency_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ELB',
                MetricName='Latency',
                Dimensions=[
                    {
                        'Name': 'LoadBalancerName',
                        'Value': lb_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )
            
            latency_datapoints = sorted(latency_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['latency'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average']
                }
                for dp in latency_datapoints
            ]
            
            # Calculate summary statistics
            if metrics['requestCount']:
                total_requests = sum(dp['sum'] for dp in metrics['requestCount'])
                metrics['totalRequests'] = total_requests
                metrics['avgRequestsPerHour'] = total_requests / len(metrics['requestCount'])
                metrics['dataPoints'] = len(metrics['requestCount'])
            else:
                metrics['totalRequests'] = 0
                metrics['avgRequestsPerHour'] = 0
                metrics['dataPoints'] = 0
            
            if metrics['latency']:
                avg_latency = sum(dp['average'] for dp in metrics['latency']) / len(metrics['latency'])
                metrics['avgLatency'] = avg_latency
            else:
                metrics['avgLatency'] = 0
            
            logger.debug(f"Retrieved {metrics['dataPoints']} metric data points for Classic load balancer {lb_name}")
            
        except ClientError as e:
            logger.warning(f"Failed to retrieve metrics for Classic load balancer {lb_name}: {e}")
            # Return empty metrics on failure
            metrics.update({
                'totalRequests': 0,
                'avgRequestsPerHour': 0,
                'avgLatency': 0
            })
        
        return metrics
    
    def _identify_optimization_opportunities(self, lb_data: Dict[str, Any], 
                                           metrics: Dict[str, Any], 
                                           target_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities for an Application/Network Load Balancer.
        
        Args:
            lb_data: Load balancer metadata
            metrics: Utilization metrics
            target_groups: Target group data
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        total_requests = metrics.get('totalRequests', 0)
        avg_requests_per_hour = metrics.get('avgRequestsPerHour', 0)
        avg_connections = metrics.get('avgActiveConnections', 0)
        data_points = metrics.get('dataPoints', 0)
        total_healthy_targets = lb_data.get('totalHealthyTargets', 0)
        total_targets = lb_data.get('totalTargets', 0)
        
        # Only analyze if we have sufficient data
        if data_points >= 24:  # At least 24 hours of data
            
            # Unused load balancer (no requests)
            if total_requests == 0:
                opportunities.append({
                    'type': 'cleanup',
                    'reason': 'No requests received in monitoring period',
                    'priority': 'HIGH',
                    'estimatedSavings': lb_data.get('currentCost', 0),
                    'confidence': 'HIGH',
                    'action': 'consider_deletion'
                })
            
            # Very low utilization
            elif avg_requests_per_hour < 1:
                opportunities.append({
                    'type': 'cleanup',
                    'reason': f'Very low utilization: {avg_requests_per_hour:.1f} requests/hour',
                    'priority': 'MEDIUM',
                    'estimatedSavings': lb_data.get('currentCost', 0) * 0.8,
                    'confidence': 'HIGH',
                    'action': 'review_necessity'
                })
            
            # Low utilization
            elif avg_requests_per_hour < 10:
                opportunities.append({
                    'type': 'optimization',
                    'reason': f'Low utilization: {avg_requests_per_hour:.1f} requests/hour',
                    'priority': 'LOW',
                    'estimatedSavings': lb_data.get('currentCost', 0) * 0.3,
                    'confidence': 'MEDIUM',
                    'action': 'consider_consolidation'
                })
        
        # No healthy targets
        if total_targets > 0 and total_healthy_targets == 0:
            opportunities.append({
                'type': 'cleanup',
                'reason': f'No healthy targets ({total_targets} total targets)',
                'priority': 'HIGH',
                'estimatedSavings': lb_data.get('currentCost', 0),
                'confidence': 'HIGH',
                'action': 'fix_targets_or_delete'
            })
        
        # Empty target groups
        empty_target_groups = [tg for tg in target_groups if tg.get('totalTargetCount', 0) == 0]
        if empty_target_groups:
            opportunities.append({
                'type': 'cleanup',
                'reason': f'{len(empty_target_groups)} empty target groups',
                'priority': 'MEDIUM',
                'estimatedSavings': 0,  # Target groups don't have direct cost
                'confidence': 'HIGH',
                'action': 'remove_empty_target_groups',
                'emptyTargetGroups': [tg['targetGroupName'] for tg in empty_target_groups]
            })
        
        # Classic Load Balancer migration opportunity
        if lb_data.get('loadBalancerType') == 'classic':
            opportunities.append({
                'type': 'modernization',
                'reason': 'Classic Load Balancer can be migrated to ALB/NLB',
                'priority': 'LOW',
                'estimatedSavings': lb_data.get('currentCost', 0) * 0.1,  # 10% potential savings
                'confidence': 'MEDIUM',
                'action': 'migrate_to_alb_nlb'
            })
        
        # Multi-AZ optimization
        az_count = len(lb_data.get('availabilityZones', []))
        if az_count > 2 and avg_requests_per_hour < 100:
            opportunities.append({
                'type': 'optimization',
                'reason': f'Load balancer spans {az_count} AZs with low traffic',
                'priority': 'LOW',
                'estimatedSavings': lb_data.get('currentCost', 0) * 0.2,
                'confidence': 'LOW',
                'action': 'consider_reducing_azs'
            })
        
        # Check for missing tags (cost allocation)
        required_tags = ['Environment', 'Project', 'Owner']
        missing_tags = [tag for tag in required_tags if tag not in lb_data.get('tags', {})]
        
        if missing_tags:
            opportunities.append({
                'type': 'governance',
                'reason': f'Missing required tags: {", ".join(missing_tags)}',
                'priority': 'LOW',
                'estimatedSavings': 0,
                'confidence': 'HIGH',
                'action': 'add_tags',
                'missingTags': missing_tags
            })
        
        return opportunities
    
    def _identify_classic_optimization_opportunities(self, lb_data: Dict[str, Any], 
                                                   metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities for a Classic Load Balancer.
        
        Args:
            lb_data: Load balancer metadata
            metrics: Utilization metrics
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        total_requests = metrics.get('totalRequests', 0)
        avg_requests_per_hour = metrics.get('avgRequestsPerHour', 0)
        data_points = metrics.get('dataPoints', 0)
        total_healthy_targets = lb_data.get('totalHealthyTargets', 0)
        total_targets = lb_data.get('totalTargets', 0)
        
        # Classic Load Balancer migration (high priority)
        opportunities.append({
            'type': 'modernization',
            'reason': 'Classic Load Balancer should be migrated to ALB/NLB',
            'priority': 'MEDIUM',
            'estimatedSavings': lb_data.get('currentCost', 0) * 0.15,  # 15% potential savings
            'confidence': 'HIGH',
            'action': 'migrate_to_alb_nlb'
        })
        
        # Only analyze utilization if we have sufficient data
        if data_points >= 24:  # At least 24 hours of data
            
            # Unused load balancer (no requests)
            if total_requests == 0:
                opportunities.append({
                    'type': 'cleanup',
                    'reason': 'No requests received in monitoring period',
                    'priority': 'HIGH',
                    'estimatedSavings': lb_data.get('currentCost', 0),
                    'confidence': 'HIGH',
                    'action': 'consider_deletion'
                })
            
            # Very low utilization
            elif avg_requests_per_hour < 1:
                opportunities.append({
                    'type': 'cleanup',
                    'reason': f'Very low utilization: {avg_requests_per_hour:.1f} requests/hour',
                    'priority': 'MEDIUM',
                    'estimatedSavings': lb_data.get('currentCost', 0) * 0.8,
                    'confidence': 'HIGH',
                    'action': 'review_necessity'
                })
        
        # No healthy targets
        if total_targets > 0 and total_healthy_targets == 0:
            opportunities.append({
                'type': 'cleanup',
                'reason': f'No healthy instances ({total_targets} total instances)',
                'priority': 'HIGH',
                'estimatedSavings': lb_data.get('currentCost', 0),
                'confidence': 'HIGH',
                'action': 'fix_instances_or_delete'
            })
        
        # Check for missing tags (cost allocation)
        required_tags = ['Environment', 'Project', 'Owner']
        missing_tags = [tag for tag in required_tags if tag not in lb_data.get('tags', {})]
        
        if missing_tags:
            opportunities.append({
                'type': 'governance',
                'reason': f'Missing required tags: {", ".join(missing_tags)}',
                'priority': 'LOW',
                'estimatedSavings': 0,
                'confidence': 'HIGH',
                'action': 'add_tags',
                'missingTags': missing_tags
            })
        
        return opportunities
    
    def _estimate_load_balancer_cost(self, lb_type: str, az_count: int, metrics: Dict[str, Any]) -> float:
        """
        Estimate monthly cost for a load balancer.
        
        Args:
            lb_type: Load balancer type (application, network, classic)
            az_count: Number of availability zones
            metrics: Utilization metrics
            
        Returns:
            Estimated monthly cost in USD
        """
        # Simplified cost estimation (would use AWS Price List API in production)
        # These are approximate costs for us-east-1 region
        
        if lb_type == 'application':
            # ALB: $0.0225 per hour + $0.008 per LCU-hour
            base_cost = 0.0225 * 24 * 30  # Monthly base cost
            
            # Estimate LCU usage (simplified)
            total_requests = metrics.get('totalRequests', 0)
            monthly_requests = total_requests * (30 / 14)  # Scale to monthly
            
            # 1 LCU = 25 new connections/sec, 3000 active connections, 1 GB/hour, 1000 rule evaluations/sec
            # Simplified: assume 1 LCU per 1000 requests per hour
            estimated_lcus = max(1, monthly_requests / (1000 * 24 * 30))
            lcu_cost = estimated_lcus * 0.008 * 24 * 30
            
            return base_cost + lcu_cost
        
        elif lb_type == 'network':
            # NLB: $0.0225 per hour + $0.006 per NLCU-hour
            base_cost = 0.0225 * 24 * 30  # Monthly base cost
            
            # Estimate NLCU usage (simplified)
            avg_connections = metrics.get('avgActiveConnections', 0)
            # 1 NLCU = 800 new connections/sec, 100,000 active connections, 1 GB/hour
            estimated_nlcus = max(1, avg_connections / 100000)
            nlcu_cost = estimated_nlcus * 0.006 * 24 * 30
            
            return base_cost + nlcu_cost
        
        elif lb_type == 'classic':
            # Classic LB: $0.025 per hour + $0.008 per GB processed
            base_cost = 0.025 * 24 * 30  # Monthly base cost
            
            # Estimate data processing (simplified - assume 1GB per 1000 requests)
            total_requests = metrics.get('totalRequests', 0)
            monthly_requests = total_requests * (30 / 14)  # Scale to monthly
            estimated_gb = monthly_requests / 1000
            data_cost = estimated_gb * 0.008
            
            return base_cost + data_cost
        
        else:
            # Default fallback
            return 50.0  # $50/month default
    
    def get_load_balancer_count_by_type(self) -> Dict[str, int]:
        """
        Get count of load balancers by type.
        
        Returns:
            Dictionary with type counts
        """
        type_counts = {'application': 0, 'network': 0, 'gateway': 0, 'classic': 0}
        
        try:
            # Count ALB/NLB
            response = self.elbv2_client.describe_load_balancers()
            for lb in response['LoadBalancers']:
                lb_type = lb.get('Type', 'application')
                type_counts[lb_type] = type_counts.get(lb_type, 0) + 1
            
            # Count Classic LBs
            response = self.elb_client.describe_load_balancers()
            type_counts['classic'] = len(response['LoadBalancerDescriptions'])
            
        except ClientError as e:
            logger.error(f"Failed to get load balancer counts: {e}")
        
        return type_counts
    
    def get_optimization_summary(self, load_balancers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate optimization summary for scanned load balancers.
        
        Args:
            load_balancers: List of analyzed load balancers
            
        Returns:
            Optimization summary
        """
        summary = {
            'totalLoadBalancers': len(load_balancers),
            'activeLoadBalancers': 0,
            'unusedLoadBalancers': 0,
            'classicLoadBalancers': 0,
            'totalMonthlyCost': 0.0,
            'potentialMonthlySavings': 0.0,
            'optimizationOpportunities': {
                'cleanup': 0,
                'optimization': 0,
                'modernization': 0,
                'governance': 0
            },
            'priorityBreakdown': {
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'typeBreakdown': {
                'application': 0,
                'network': 0,
                'classic': 0,
                'gateway': 0
            }
        }
        
        for lb in load_balancers:
            # Count by state and type
            if lb['state'] == 'active':
                summary['activeLoadBalancers'] += 1
            
            lb_type = lb.get('loadBalancerType', 'unknown')
            if lb_type in summary['typeBreakdown']:
                summary['typeBreakdown'][lb_type] += 1
            
            if lb_type == 'classic':
                summary['classicLoadBalancers'] += 1
            
            # Check if unused (no requests)
            total_requests = lb.get('utilizationMetrics', {}).get('totalRequests', 0)
            if total_requests == 0:
                summary['unusedLoadBalancers'] += 1
            
            # Sum costs
            summary['totalMonthlyCost'] += lb.get('currentCost', 0)
            
            # Analyze opportunities
            for opportunity in lb.get('optimizationOpportunities', []):
                opp_type = opportunity.get('type', 'unknown')
                priority = opportunity.get('priority', 'LOW')
                savings = opportunity.get('estimatedSavings', 0)
                
                if opp_type in summary['optimizationOpportunities']:
                    summary['optimizationOpportunities'][opp_type] += 1
                
                if priority in summary['priorityBreakdown']:
                    summary['priorityBreakdown'][priority] += 1
                
                summary['potentialMonthlySavings'] += savings
        
        # Calculate savings percentage
        if summary['totalMonthlyCost'] > 0:
            summary['savingsPercentage'] = (summary['potentialMonthlySavings'] / summary['totalMonthlyCost']) * 100
        else:
            summary['savingsPercentage'] = 0.0
        
        return summary