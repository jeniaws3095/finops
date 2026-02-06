#!/usr/bin/env python3
"""
CloudWatch Scanner for Advanced FinOps Platform

Discovers and analyzes CloudWatch resources across regions, collecting:
- Log groups and retention policies
- Custom metrics and alarms
- Dashboard usage and costs
- Log retention optimization opportunities
- Unused metrics and alarm cleanup

Requirements: 1.1, 7.5
"""

import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CloudWatchScanner:
    """Scans CloudWatch resources for cost optimization opportunities."""
    
    def __init__(self, aws_config, region: str = 'us-east-1'):
        """
        Initialize CloudWatch scanner.
        
        Args:
            aws_config: AWSConfig instance for client management
            region: AWS region to scan
        """
        self.aws_config = aws_config
        self.region = region
        self.cloudwatch_client = aws_config.get_client('cloudwatch')
        self.logs_client = aws_config.get_client('logs')
        
        logger.info(f"CloudWatch Scanner initialized for region {region}")
    
    def scan_cloudwatch_resources(self, days_back: int = 14) -> List[Dict[str, Any]]:
        """
        Scan all CloudWatch resources in the region.
        
        Args:
            days_back: Number of days to look back for metrics
            
        Returns:
            List of CloudWatch resource data with optimization opportunities
        """
        logger.info(f"Starting CloudWatch resource scan in region {self.region}")
        
        resources = []
        
        try:
            # Scan log groups
            log_groups = self._scan_log_groups(days_back)
            resources.extend(log_groups)
            
            # Scan custom metrics
            custom_metrics = self._scan_custom_metrics(days_back)
            resources.extend(custom_metrics)
            
            # Scan alarms
            alarms = self._scan_alarms(days_back)
            resources.extend(alarms)
            
            # Scan dashboards
            dashboards = self._scan_dashboards()
            resources.extend(dashboards)
            
            logger.info(f"Scanned {len(resources)} CloudWatch resources")
            
        except ClientError as e:
            logger.error(f"Failed to scan CloudWatch resources: {e}")
            raise
        
        return resources
    
    def _scan_log_groups(self, days_back: int) -> List[Dict[str, Any]]:
        """
        Scan CloudWatch Log Groups.
        
        Args:
            days_back: Number of days to analyze metrics
            
        Returns:
            List of log group data
        """
        log_groups = []
        
        try:
            # Get all log groups
            paginator = self.logs_client.get_paginator('describe_log_groups')
            
            for page in paginator.paginate():
                for log_group in page['logGroups']:
                    log_group_data = self._analyze_log_group(log_group, days_back)
                    if log_group_data:
                        log_groups.append(log_group_data)
            
        except ClientError as e:
            logger.error(f"Failed to scan log groups: {e}")
            raise
        
        return log_groups
    
    def _scan_custom_metrics(self, days_back: int) -> List[Dict[str, Any]]:
        """
        Scan custom CloudWatch metrics.
        
        Args:
            days_back: Number of days to analyze metrics
            
        Returns:
            List of custom metric data
        """
        custom_metrics = []
        
        try:
            # Get all custom metrics (non-AWS namespaces)
            paginator = self.cloudwatch_client.get_paginator('list_metrics')
            
            aws_namespaces = {
                'AWS/EC2', 'AWS/S3', 'AWS/RDS', 'AWS/Lambda', 'AWS/ELB', 'AWS/ApplicationELB',
                'AWS/NetworkELB', 'AWS/EBS', 'AWS/CloudWatch', 'AWS/Logs', 'AWS/DynamoDB',
                'AWS/SQS', 'AWS/SNS', 'AWS/CloudFront', 'AWS/Route53', 'AWS/ApiGateway'
            }
            
            for page in paginator.paginate():
                for metric in page['Metrics']:
                    namespace = metric.get('Namespace', '')
                    
                    # Only analyze custom metrics (non-AWS namespaces)
                    if namespace and not namespace.startswith('AWS/'):
                        metric_data = self._analyze_custom_metric(metric, days_back)
                        if metric_data:
                            custom_metrics.append(metric_data)
            
        except ClientError as e:
            logger.error(f"Failed to scan custom metrics: {e}")
            raise
        
        return custom_metrics
    
    def _scan_alarms(self, days_back: int) -> List[Dict[str, Any]]:
        """
        Scan CloudWatch alarms.
        
        Args:
            days_back: Number of days to analyze alarm activity
            
        Returns:
            List of alarm data
        """
        alarms = []
        
        try:
            # Get all alarms
            paginator = self.cloudwatch_client.get_paginator('describe_alarms')
            
            for page in paginator.paginate():
                for alarm in page['MetricAlarms']:
                    alarm_data = self._analyze_alarm(alarm, days_back)
                    if alarm_data:
                        alarms.append(alarm_data)
            
        except ClientError as e:
            logger.error(f"Failed to scan alarms: {e}")
            raise
        
        return alarms
    
    def _scan_dashboards(self) -> List[Dict[str, Any]]:
        """
        Scan CloudWatch dashboards.
        
        Returns:
            List of dashboard data
        """
        dashboards = []
        
        try:
            # Get all dashboards
            paginator = self.cloudwatch_client.get_paginator('list_dashboards')
            
            for page in paginator.paginate():
                for dashboard in page['DashboardEntries']:
                    dashboard_data = self._analyze_dashboard(dashboard)
                    if dashboard_data:
                        dashboards.append(dashboard_data)
            
        except ClientError as e:
            logger.error(f"Failed to scan dashboards: {e}")
            raise
        
        return dashboards
    
    def _analyze_log_group(self, log_group: Dict[str, Any], days_back: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single CloudWatch Log Group.
        
        Args:
            log_group: Log group data from describe_log_groups
            days_back: Number of days to analyze metrics
            
        Returns:
            Log group analysis data or None if analysis fails
        """
        log_group_name = log_group['logGroupName']
        
        try:
            # Basic log group information
            log_group_data = {
                'resourceId': log_group_name,
                'resourceType': 'cloudwatch_log_group',
                'region': self.region,
                'logGroupName': log_group_name,
                'retentionInDays': log_group.get('retentionInDays'),
                'storedBytes': log_group.get('storedBytes', 0),
                'creationTime': log_group.get('creationTime', 0),
                'metricFilterCount': log_group.get('metricFilterCount', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Convert creation time from epoch to ISO format
            if log_group_data['creationTime']:
                creation_date = datetime.fromtimestamp(log_group_data['creationTime'] / 1000)
                log_group_data['creationDate'] = creation_date.isoformat()
            else:
                log_group_data['creationDate'] = datetime.utcnow().isoformat()
            
            # Get log group tags
            try:
                tags_response = self.logs_client.list_tags_log_group(logGroupName=log_group_name)
                log_group_data['tags'] = tags_response.get('tags', {})
            except ClientError as e:
                logger.warning(f"Failed to get tags for log group {log_group_name}: {e}")
                log_group_data['tags'] = {}
            
            # Get log streams count and activity
            log_stream_metrics = self._get_log_group_activity(log_group_name, days_back)
            log_group_data['activityMetrics'] = log_stream_metrics
            
            # Calculate optimization opportunities
            opportunities = self._identify_log_group_opportunities(log_group_data, log_stream_metrics)
            log_group_data['optimizationOpportunities'] = opportunities
            
            # Estimate current cost
            log_group_data['currentCost'] = self._estimate_log_group_cost(
                log_group_data['storedBytes'],
                log_stream_metrics.get('ingestedBytes', 0)
            )
            
            return log_group_data
            
        except Exception as e:
            logger.error(f"Failed to analyze log group {log_group_name}: {e}")
            return None
    
    def _analyze_custom_metric(self, metric: Dict[str, Any], days_back: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single custom CloudWatch metric.
        
        Args:
            metric: Metric data from list_metrics
            days_back: Number of days to analyze metrics
            
        Returns:
            Custom metric analysis data or None if analysis fails
        """
        namespace = metric.get('Namespace', '')
        metric_name = metric.get('MetricName', '')
        dimensions = metric.get('Dimensions', [])
        
        # Create a unique identifier for the metric
        dimension_str = '_'.join([f"{d['Name']}={d['Value']}" for d in dimensions])
        metric_id = f"{namespace}_{metric_name}_{dimension_str}" if dimension_str else f"{namespace}_{metric_name}"
        
        try:
            # Basic metric information
            metric_data = {
                'resourceId': metric_id,
                'resourceType': 'cloudwatch_custom_metric',
                'region': self.region,
                'namespace': namespace,
                'metricName': metric_name,
                'dimensions': dimensions,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Get metric statistics to check usage
            usage_metrics = self._get_metric_usage(namespace, metric_name, dimensions, days_back)
            metric_data['usageMetrics'] = usage_metrics
            
            # Calculate optimization opportunities
            opportunities = self._identify_metric_opportunities(metric_data, usage_metrics)
            metric_data['optimizationOpportunities'] = opportunities
            
            # Estimate current cost (custom metrics cost $0.30 per metric per month)
            metric_data['currentCost'] = 0.30  # Base cost per custom metric
            
            return metric_data
            
        except Exception as e:
            logger.error(f"Failed to analyze custom metric {metric_id}: {e}")
            return None
    
    def _analyze_alarm(self, alarm: Dict[str, Any], days_back: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single CloudWatch alarm.
        
        Args:
            alarm: Alarm data from describe_alarms
            days_back: Number of days to analyze alarm activity
            
        Returns:
            Alarm analysis data or None if analysis fails
        """
        alarm_name = alarm['AlarmName']
        
        try:
            # Basic alarm information
            alarm_data = {
                'resourceId': alarm_name,
                'resourceType': 'cloudwatch_alarm',
                'region': self.region,
                'alarmName': alarm_name,
                'alarmDescription': alarm.get('AlarmDescription', ''),
                'metricName': alarm.get('MetricName', ''),
                'namespace': alarm.get('Namespace', ''),
                'statistic': alarm.get('Statistic', ''),
                'comparisonOperator': alarm.get('ComparisonOperator', ''),
                'threshold': alarm.get('Threshold', 0),
                'evaluationPeriods': alarm.get('EvaluationPeriods', 0),
                'period': alarm.get('Period', 0),
                'stateValue': alarm.get('StateValue', 'INSUFFICIENT_DATA'),
                'stateReason': alarm.get('StateReason', ''),
                'stateUpdatedTimestamp': alarm.get('StateUpdatedTimestamp', datetime.utcnow()).isoformat(),
                'actionsEnabled': alarm.get('ActionsEnabled', False),
                'alarmActions': alarm.get('AlarmActions', []),
                'okActions': alarm.get('OKActions', []),
                'insufficientDataActions': alarm.get('InsufficientDataActions', []),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Get alarm history to check activity
            alarm_history = self._get_alarm_history(alarm_name, days_back)
            alarm_data['historyMetrics'] = alarm_history
            
            # Calculate optimization opportunities
            opportunities = self._identify_alarm_opportunities(alarm_data, alarm_history)
            alarm_data['optimizationOpportunities'] = opportunities
            
            # Estimate current cost (alarms cost $0.10 per alarm per month)
            alarm_data['currentCost'] = 0.10  # Base cost per alarm
            
            return alarm_data
            
        except Exception as e:
            logger.error(f"Failed to analyze alarm {alarm_name}: {e}")
            return None
    
    def _analyze_dashboard(self, dashboard: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a single CloudWatch dashboard.
        
        Args:
            dashboard: Dashboard data from list_dashboards
            
        Returns:
            Dashboard analysis data or None if analysis fails
        """
        dashboard_name = dashboard['DashboardName']
        
        try:
            # Get dashboard details
            dashboard_response = self.cloudwatch_client.get_dashboard(DashboardName=dashboard_name)
            dashboard_body = dashboard_response.get('DashboardBody', '{}')
            
            # Basic dashboard information
            dashboard_data = {
                'resourceId': dashboard_name,
                'resourceType': 'cloudwatch_dashboard',
                'region': self.region,
                'dashboardName': dashboard_name,
                'lastModified': dashboard.get('LastModified', datetime.utcnow()).isoformat(),
                'size': dashboard.get('Size', 0),
                'dashboardBody': dashboard_body,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Parse dashboard body to count widgets (simplified)
            widget_count = dashboard_body.count('"type"')  # Simple widget count
            dashboard_data['widgetCount'] = widget_count
            
            # Calculate optimization opportunities
            opportunities = self._identify_dashboard_opportunities(dashboard_data)
            dashboard_data['optimizationOpportunities'] = opportunities
            
            # Estimate current cost (dashboards cost $3 per dashboard per month)
            dashboard_data['currentCost'] = 3.0  # Base cost per dashboard
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to analyze dashboard {dashboard_name}: {e}")
            return None
    
    def _get_log_group_activity(self, log_group_name: str, days_back: int) -> Dict[str, Any]:
        """
        Get activity metrics for a log group.
        
        Args:
            log_group_name: Log group name
            days_back: Number of days to analyze
            
        Returns:
            Dictionary containing activity metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        metrics = {
            'logStreamCount': 0,
            'recentLogStreams': 0,
            'ingestedBytes': 0,
            'ingestedEvents': 0,
            'period': f"{days_back} days"
        }
        
        try:
            # Get log streams
            paginator = self.logs_client.get_paginator('describe_log_streams')
            log_streams = []
            
            for page in paginator.paginate(logGroupName=log_group_name):
                log_streams.extend(page['logStreams'])
            
            metrics['logStreamCount'] = len(log_streams)
            
            # Count recent log streams (active in the last period)
            start_timestamp = int(start_time.timestamp() * 1000)
            recent_streams = [
                stream for stream in log_streams 
                if stream.get('lastEventTime', 0) >= start_timestamp
            ]
            metrics['recentLogStreams'] = len(recent_streams)
            
            # Estimate ingested data (simplified - would use CloudWatch metrics in production)
            for stream in recent_streams:
                metrics['ingestedBytes'] += stream.get('storedBytes', 0)
            
            logger.debug(f"Retrieved activity metrics for log group {log_group_name}")
            
        except ClientError as e:
            logger.warning(f"Failed to retrieve activity metrics for log group {log_group_name}: {e}")
        
        return metrics
    
    def _get_metric_usage(self, namespace: str, metric_name: str, dimensions: List[Dict[str, str]], days_back: int) -> Dict[str, Any]:
        """
        Get usage statistics for a custom metric.
        
        Args:
            namespace: Metric namespace
            metric_name: Metric name
            dimensions: Metric dimensions
            days_back: Number of days to analyze
            
        Returns:
            Dictionary containing usage metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        metrics = {
            'dataPoints': 0,
            'hasRecentData': False,
            'period': f"{days_back} days"
        }
        
        try:
            # Get metric statistics to check if it's being used
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['SampleCount']
            )
            
            datapoints = response.get('Datapoints', [])
            metrics['dataPoints'] = len(datapoints)
            metrics['hasRecentData'] = len(datapoints) > 0
            
            if datapoints:
                total_samples = sum(dp.get('SampleCount', 0) for dp in datapoints)
                metrics['totalSamples'] = total_samples
                metrics['avgSamplesPerHour'] = total_samples / len(datapoints) if datapoints else 0
            else:
                metrics['totalSamples'] = 0
                metrics['avgSamplesPerHour'] = 0
            
            logger.debug(f"Retrieved usage metrics for custom metric {namespace}/{metric_name}")
            
        except ClientError as e:
            logger.warning(f"Failed to retrieve usage metrics for custom metric {namespace}/{metric_name}: {e}")
            metrics.update({
                'totalSamples': 0,
                'avgSamplesPerHour': 0
            })
        
        return metrics
    
    def _get_alarm_history(self, alarm_name: str, days_back: int) -> Dict[str, Any]:
        """
        Get alarm history and activity.
        
        Args:
            alarm_name: Alarm name
            days_back: Number of days to analyze
            
        Returns:
            Dictionary containing alarm history metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        metrics = {
            'historyItems': 0,
            'stateChanges': 0,
            'alarmTriggers': 0,
            'hasRecentActivity': False,
            'period': f"{days_back} days"
        }
        
        try:
            # Get alarm history
            paginator = self.cloudwatch_client.get_paginator('describe_alarm_history')
            
            history_items = []
            for page in paginator.paginate(
                AlarmName=alarm_name,
                StartDate=start_time,
                EndDate=end_time
            ):
                history_items.extend(page['AlarmHistoryItems'])
            
            metrics['historyItems'] = len(history_items)
            metrics['hasRecentActivity'] = len(history_items) > 0
            
            # Count different types of history items
            state_changes = [item for item in history_items if item.get('HistoryItemType') == 'StateUpdate']
            alarm_triggers = [item for item in history_items if 'ALARM' in item.get('HistorySummary', '')]
            
            metrics['stateChanges'] = len(state_changes)
            metrics['alarmTriggers'] = len(alarm_triggers)
            
            logger.debug(f"Retrieved history metrics for alarm {alarm_name}")
            
        except ClientError as e:
            logger.warning(f"Failed to retrieve history metrics for alarm {alarm_name}: {e}")
        
        return metrics
    
    def _identify_log_group_opportunities(self, log_group_data: Dict[str, Any], 
                                        activity_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities for a log group.
        
        Args:
            log_group_data: Log group metadata
            activity_metrics: Activity metrics
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        retention_days = log_group_data.get('retentionInDays')
        stored_bytes = log_group_data.get('storedBytes', 0)
        recent_streams = activity_metrics.get('recentLogStreams', 0)
        total_streams = activity_metrics.get('logStreamCount', 0)
        
        # No retention policy set
        if retention_days is None:
            opportunities.append({
                'type': 'retention_optimization',
                'reason': 'No retention policy set - logs stored indefinitely',
                'priority': 'HIGH',
                'estimatedSavings': log_group_data.get('currentCost', 0) * 0.5,  # 50% potential savings
                'confidence': 'HIGH',
                'action': 'set_retention_policy',
                'recommendedRetention': '30 days'
            })
        
        # Very long retention period
        elif retention_days and retention_days > 365:
            opportunities.append({
                'type': 'retention_optimization',
                'reason': f'Very long retention period: {retention_days} days',
                'priority': 'MEDIUM',
                'estimatedSavings': log_group_data.get('currentCost', 0) * 0.3,  # 30% potential savings
                'confidence': 'MEDIUM',
                'action': 'reduce_retention_period',
                'currentRetention': f'{retention_days} days',
                'recommendedRetention': '90 days'
            })
        
        # Unused log group (no recent activity)
        if total_streams > 0 and recent_streams == 0:
            opportunities.append({
                'type': 'cleanup',
                'reason': f'No recent activity ({total_streams} streams, 0 recent)',
                'priority': 'MEDIUM',
                'estimatedSavings': log_group_data.get('currentCost', 0),
                'confidence': 'HIGH',
                'action': 'consider_deletion'
            })
        
        # Empty log group
        elif total_streams == 0:
            opportunities.append({
                'type': 'cleanup',
                'reason': 'Empty log group with no log streams',
                'priority': 'LOW',
                'estimatedSavings': log_group_data.get('currentCost', 0),
                'confidence': 'HIGH',
                'action': 'consider_deletion'
            })
        
        # Large log group with long retention
        if stored_bytes > 10 * 1024 * 1024 * 1024 and retention_days and retention_days > 90:  # > 10GB
            opportunities.append({
                'type': 'retention_optimization',
                'reason': f'Large log group ({stored_bytes / (1024**3):.1f}GB) with long retention',
                'priority': 'MEDIUM',
                'estimatedSavings': log_group_data.get('currentCost', 0) * 0.4,
                'confidence': 'MEDIUM',
                'action': 'optimize_retention_for_size'
            })
        
        # Check for missing tags (cost allocation)
        required_tags = ['Environment', 'Project', 'Owner']
        missing_tags = [tag for tag in required_tags if tag not in log_group_data.get('tags', {})]
        
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
    
    def _identify_metric_opportunities(self, metric_data: Dict[str, Any], 
                                     usage_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities for a custom metric.
        
        Args:
            metric_data: Metric metadata
            usage_metrics: Usage metrics
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        has_recent_data = usage_metrics.get('hasRecentData', False)
        total_samples = usage_metrics.get('totalSamples', 0)
        
        # Unused custom metric
        if not has_recent_data:
            opportunities.append({
                'type': 'cleanup',
                'reason': 'No recent data points - metric may be unused',
                'priority': 'MEDIUM',
                'estimatedSavings': metric_data.get('currentCost', 0),
                'confidence': 'HIGH',
                'action': 'consider_deletion'
            })
        
        # Very low usage metric
        elif total_samples < 10:  # Very few samples
            opportunities.append({
                'type': 'cleanup',
                'reason': f'Very low usage: {total_samples} samples in monitoring period',
                'priority': 'LOW',
                'estimatedSavings': metric_data.get('currentCost', 0),
                'confidence': 'MEDIUM',
                'action': 'review_necessity'
            })
        
        return opportunities
    
    def _identify_alarm_opportunities(self, alarm_data: Dict[str, Any], 
                                    history_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities for an alarm.
        
        Args:
            alarm_data: Alarm metadata
            history_metrics: Alarm history metrics
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        has_recent_activity = history_metrics.get('hasRecentActivity', False)
        state_changes = history_metrics.get('stateChanges', 0)
        alarm_triggers = history_metrics.get('alarmTriggers', 0)
        actions_enabled = alarm_data.get('actionsEnabled', False)
        alarm_actions = alarm_data.get('alarmActions', [])
        state_value = alarm_data.get('stateValue', 'INSUFFICIENT_DATA')
        
        # Alarm with insufficient data
        if state_value == 'INSUFFICIENT_DATA':
            opportunities.append({
                'type': 'optimization',
                'reason': 'Alarm in INSUFFICIENT_DATA state - may need configuration review',
                'priority': 'MEDIUM',
                'estimatedSavings': 0,
                'confidence': 'MEDIUM',
                'action': 'review_alarm_configuration'
            })
        
        # Unused alarm (no recent activity)
        if not has_recent_activity:
            opportunities.append({
                'type': 'cleanup',
                'reason': 'No recent activity - alarm may be unused',
                'priority': 'LOW',
                'estimatedSavings': alarm_data.get('currentCost', 0),
                'confidence': 'MEDIUM',
                'action': 'consider_deletion'
            })
        
        # Alarm with no actions
        if actions_enabled and not alarm_actions:
            opportunities.append({
                'type': 'optimization',
                'reason': 'Alarm has actions enabled but no actions configured',
                'priority': 'LOW',
                'estimatedSavings': 0,
                'confidence': 'HIGH',
                'action': 'configure_actions_or_disable'
            })
        
        # Alarm that never triggers
        if has_recent_activity and alarm_triggers == 0 and state_changes > 0:
            opportunities.append({
                'type': 'optimization',
                'reason': 'Alarm has activity but never triggers - threshold may need adjustment',
                'priority': 'LOW',
                'estimatedSavings': 0,
                'confidence': 'MEDIUM',
                'action': 'review_threshold'
            })
        
        return opportunities
    
    def _identify_dashboard_opportunities(self, dashboard_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities for a dashboard.
        
        Args:
            dashboard_data: Dashboard metadata
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        widget_count = dashboard_data.get('widgetCount', 0)
        last_modified = dashboard_data.get('lastModified', '')
        
        # Parse last modified date
        try:
            if isinstance(last_modified, str):
                last_modified_date = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
            else:
                last_modified_date = last_modified
            
            days_since_modified = (datetime.utcnow().replace(tzinfo=last_modified_date.tzinfo) - last_modified_date).days
            
            # Dashboard not modified recently
            if days_since_modified > 90:  # 3 months
                opportunities.append({
                    'type': 'cleanup',
                    'reason': f'Dashboard not modified for {days_since_modified} days',
                    'priority': 'LOW',
                    'estimatedSavings': dashboard_data.get('currentCost', 0),
                    'confidence': 'MEDIUM',
                    'action': 'review_necessity'
                })
        except Exception:
            # If we can't parse the date, skip this check
            pass
        
        # Empty or minimal dashboard
        if widget_count == 0:
            opportunities.append({
                'type': 'cleanup',
                'reason': 'Dashboard has no widgets',
                'priority': 'MEDIUM',
                'estimatedSavings': dashboard_data.get('currentCost', 0),
                'confidence': 'HIGH',
                'action': 'consider_deletion'
            })
        elif widget_count < 3:
            opportunities.append({
                'type': 'optimization',
                'reason': f'Dashboard has only {widget_count} widgets - consider consolidation',
                'priority': 'LOW',
                'estimatedSavings': dashboard_data.get('currentCost', 0) * 0.5,
                'confidence': 'LOW',
                'action': 'consider_consolidation'
            })
        
        return opportunities
    
    def _estimate_log_group_cost(self, stored_bytes: int, ingested_bytes: int) -> float:
        """
        Estimate monthly cost for a log group.
        
        Args:
            stored_bytes: Bytes currently stored
            ingested_bytes: Bytes ingested in the period
            
        Returns:
            Estimated monthly cost in USD
        """
        # CloudWatch Logs pricing (simplified for us-east-1)
        # Ingestion: $0.50 per GB
        # Storage: $0.03 per GB per month
        
        stored_gb = stored_bytes / (1024 ** 3)
        ingested_gb = ingested_bytes / (1024 ** 3)
        
        # Scale ingested data to monthly (assuming 14-day period)
        monthly_ingested_gb = ingested_gb * (30 / 14)
        
        storage_cost = stored_gb * 0.03
        ingestion_cost = monthly_ingested_gb * 0.50
        
        return storage_cost + ingestion_cost
    
    def get_cloudwatch_summary(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate optimization summary for scanned CloudWatch resources.
        
        Args:
            resources: List of analyzed CloudWatch resources
            
        Returns:
            Optimization summary
        """
        summary = {
            'totalResources': len(resources),
            'resourceBreakdown': {
                'cloudwatch_log_group': 0,
                'cloudwatch_custom_metric': 0,
                'cloudwatch_alarm': 0,
                'cloudwatch_dashboard': 0
            },
            'totalMonthlyCost': 0.0,
            'potentialMonthlySavings': 0.0,
            'optimizationOpportunities': {
                'cleanup': 0,
                'retention_optimization': 0,
                'optimization': 0,
                'governance': 0
            },
            'priorityBreakdown': {
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'retentionIssues': 0,
            'unusedResources': 0
        }
        
        for resource in resources:
            # Count by type
            resource_type = resource.get('resourceType', 'unknown')
            if resource_type in summary['resourceBreakdown']:
                summary['resourceBreakdown'][resource_type] += 1
            
            # Sum costs
            summary['totalMonthlyCost'] += resource.get('currentCost', 0)
            
            # Check for specific issues
            if resource_type == 'cloudwatch_log_group':
                if resource.get('retentionInDays') is None:
                    summary['retentionIssues'] += 1
                
                recent_streams = resource.get('activityMetrics', {}).get('recentLogStreams', 0)
                total_streams = resource.get('activityMetrics', {}).get('logStreamCount', 0)
                if total_streams > 0 and recent_streams == 0:
                    summary['unusedResources'] += 1
            
            elif resource_type == 'cloudwatch_custom_metric':
                if not resource.get('usageMetrics', {}).get('hasRecentData', False):
                    summary['unusedResources'] += 1
            
            elif resource_type == 'cloudwatch_alarm':
                if not resource.get('historyMetrics', {}).get('hasRecentActivity', False):
                    summary['unusedResources'] += 1
            
            # Analyze opportunities
            for opportunity in resource.get('optimizationOpportunities', []):
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