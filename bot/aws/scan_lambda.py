#!/usr/bin/env python3
"""
Lambda Function Scanner for Advanced FinOps Platform

Discovers and analyzes Lambda functions across regions, collecting:
- Function metadata and configuration
- Memory usage, duration, and invocation metrics from CloudWatch
- Cost data and optimization opportunities
- Unused functions and optimization recommendations

Requirements: 1.1, 7.2
"""

import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class LambdaScanner:
    """Scans Lambda functions for cost optimization opportunities."""
    
    def __init__(self, aws_config, region: str = 'us-east-1'):
        """
        Initialize Lambda scanner.
        
        Args:
            aws_config: AWSConfig instance for client management
            region: AWS region to scan
        """
        self.aws_config = aws_config
        self.region = region
        self.lambda_client = aws_config.get_client('lambda')
        self.cloudwatch_client = aws_config.get_client('cloudwatch')
        
        logger.info(f"Lambda Scanner initialized for region {region}")
    
    def scan_functions(self, days_back: int = 14) -> List[Dict[str, Any]]:
        """
        Scan all Lambda functions in the region.
        
        Args:
            days_back: Number of days to look back for metrics
            
        Returns:
            List of function data with utilization metrics
        """
        logger.info(f"Starting Lambda function scan in region {self.region}")
        
        functions = []
        
        try:
            # Get all Lambda functions
            paginator = self.lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page['Functions']:
                    function_data = self._analyze_function(function, days_back)
                    if function_data:
                        functions.append(function_data)
            
            logger.info(f"Scanned {len(functions)} Lambda functions")
            
        except ClientError as e:
            logger.error(f"Failed to scan Lambda functions: {e}")
            raise
        
        return functions
    
    def _analyze_function(self, function: Dict[str, Any], days_back: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single Lambda function.
        
        Args:
            function: Lambda function data from list_functions
            days_back: Number of days to analyze metrics
            
        Returns:
            Function analysis data or None if analysis fails
        """
        function_name = function['FunctionName']
        
        try:
            # Basic function information
            function_data = {
                'resourceId': function_name,
                'resourceType': 'lambda',
                'region': self.region,
                'functionName': function_name,
                'runtime': function.get('Runtime', 'unknown'),
                'memorySize': function.get('MemorySize', 128),
                'timeout': function.get('Timeout', 3),
                'codeSize': function.get('CodeSize', 0),
                'lastModified': function.get('LastModified', datetime.utcnow().isoformat()),
                'state': function.get('State', 'Active'),
                'stateReason': function.get('StateReason', ''),
                'packageType': function.get('PackageType', 'Zip'),
                'architectures': function.get('Architectures', ['x86_64']),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Get function configuration details
            try:
                config_response = self.lambda_client.get_function_configuration(
                    FunctionName=function_name
                )
                function_data.update({
                    'description': config_response.get('Description', ''),
                    'handler': config_response.get('Handler', ''),
                    'role': config_response.get('Role', ''),
                    'vpcConfig': config_response.get('VpcConfig', {}),
                    'environment': config_response.get('Environment', {}),
                    'deadLetterConfig': config_response.get('DeadLetterConfig', {}),
                    'tracingConfig': config_response.get('TracingConfig', {}),
                    'layers': config_response.get('Layers', [])
                })
            except ClientError as e:
                logger.warning(f"Failed to get configuration for {function_name}: {e}")
            
            # Get function tags
            try:
                tags_response = self.lambda_client.list_tags(
                    Resource=function['FunctionArn']
                )
                function_data['tags'] = tags_response.get('Tags', {})
            except ClientError as e:
                logger.warning(f"Failed to get tags for {function_name}: {e}")
                function_data['tags'] = {}
            
            # Get utilization metrics
            metrics = self._get_function_metrics(function_name, days_back)
            function_data['utilizationMetrics'] = metrics
            
            # Calculate optimization opportunities
            opportunities = self._identify_optimization_opportunities(function_data, metrics)
            function_data['optimizationOpportunities'] = opportunities
            
            # Estimate current cost
            function_data['currentCost'] = self._estimate_function_cost(
                function_data['memorySize'],
                metrics.get('totalInvocations', 0),
                metrics.get('avgDuration', 0),
                days_back
            )
            
            return function_data
            
        except Exception as e:
            logger.error(f"Failed to analyze function {function_name}: {e}")
            return None
    
    def _get_function_metrics(self, function_name: str, days_back: int) -> Dict[str, Any]:
        """
        Get CloudWatch metrics for a Lambda function.
        
        Args:
            function_name: Lambda function name
            days_back: Number of days to retrieve metrics
            
        Returns:
            Dictionary containing utilization metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        metrics = {
            'invocations': [],
            'duration': [],
            'errors': [],
            'throttles': [],
            'deadLetterErrors': [],
            'concurrentExecutions': [],
            'period': f"{days_back} days",
            'dataPoints': 0
        }
        
        try:
            # Invocations
            invocations_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['Sum']
            )
            
            invocations_datapoints = sorted(invocations_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['invocations'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in invocations_datapoints
            ]
            
            # Duration
            duration_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            duration_datapoints = sorted(duration_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['duration'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average'],
                    'maximum': dp['Maximum']
                }
                for dp in duration_datapoints
            ]
            
            # Errors
            errors_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            errors_datapoints = sorted(errors_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['errors'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in errors_datapoints
            ]
            
            # Throttles
            throttles_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Throttles',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            throttles_datapoints = sorted(throttles_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['throttles'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in throttles_datapoints
            ]
            
            # Concurrent Executions
            concurrent_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='ConcurrentExecutions',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            concurrent_datapoints = sorted(concurrent_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['concurrentExecutions'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average'],
                    'maximum': dp['Maximum']
                }
                for dp in concurrent_datapoints
            ]
            
            # Calculate summary statistics
            if metrics['invocations']:
                total_invocations = sum(dp['sum'] for dp in metrics['invocations'])
                metrics['totalInvocations'] = total_invocations
                metrics['avgInvocationsPerHour'] = total_invocations / len(metrics['invocations']) if metrics['invocations'] else 0
                metrics['dataPoints'] = len(metrics['invocations'])
            else:
                metrics['totalInvocations'] = 0
                metrics['avgInvocationsPerHour'] = 0
                metrics['dataPoints'] = 0
            
            if metrics['duration']:
                duration_averages = [dp['average'] for dp in metrics['duration']]
                metrics['avgDuration'] = sum(duration_averages) / len(duration_averages)
                metrics['maxDuration'] = max(dp['maximum'] for dp in metrics['duration'])
            else:
                metrics['avgDuration'] = 0.0
                metrics['maxDuration'] = 0.0
            
            if metrics['errors']:
                metrics['totalErrors'] = sum(dp['sum'] for dp in metrics['errors'])
                metrics['errorRate'] = (metrics['totalErrors'] / metrics['totalInvocations']) * 100 if metrics['totalInvocations'] > 0 else 0
            else:
                metrics['totalErrors'] = 0
                metrics['errorRate'] = 0.0
            
            if metrics['throttles']:
                metrics['totalThrottles'] = sum(dp['sum'] for dp in metrics['throttles'])
            else:
                metrics['totalThrottles'] = 0
            
            logger.debug(f"Retrieved {metrics['dataPoints']} metric data points for function {function_name}")
            
        except ClientError as e:
            logger.warning(f"Failed to retrieve metrics for function {function_name}: {e}")
            # Return empty metrics on failure
            metrics.update({
                'totalInvocations': 0,
                'avgInvocationsPerHour': 0,
                'avgDuration': 0.0,
                'maxDuration': 0.0,
                'totalErrors': 0,
                'errorRate': 0.0,
                'totalThrottles': 0
            })
        
        return metrics
    
    def _identify_optimization_opportunities(self, function_data: Dict[str, Any], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities for a Lambda function.
        
        Args:
            function_data: Function metadata
            metrics: Utilization metrics
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        total_invocations = metrics.get('totalInvocations', 0)
        avg_duration = metrics.get('avgDuration', 0)
        max_duration = metrics.get('maxDuration', 0)
        error_rate = metrics.get('errorRate', 0)
        total_throttles = metrics.get('totalThrottles', 0)
        data_points = metrics.get('dataPoints', 0)
        
        memory_size = function_data.get('memorySize', 128)
        timeout = function_data.get('timeout', 3)
        
        # Only analyze if we have sufficient data
        if data_points >= 24:  # At least 24 hours of data
            
            # Unused function (no invocations)
            if total_invocations == 0:
                opportunities.append({
                    'type': 'cleanup',
                    'reason': 'Function has not been invoked in the monitoring period',
                    'priority': 'HIGH',
                    'estimatedSavings': function_data.get('currentCost', 0),  # Full cost savings
                    'confidence': 'HIGH',
                    'action': 'consider_deletion'
                })
            
            # Rarely used function (very few invocations)
            elif total_invocations < 10:
                opportunities.append({
                    'type': 'cleanup',
                    'reason': f'Function rarely used: {total_invocations} invocations in {data_points} hours',
                    'priority': 'MEDIUM',
                    'estimatedSavings': function_data.get('currentCost', 0) * 0.8,  # 80% savings
                    'confidence': 'MEDIUM',
                    'action': 'review_necessity'
                })
            
            # Memory optimization - over-provisioned memory
            elif avg_duration > 0 and max_duration < (timeout * 1000 * 0.5):  # Using less than 50% of timeout
                if memory_size > 512:  # Only suggest for functions with significant memory
                    recommended_memory = max(128, int(memory_size * 0.7))  # Reduce by 30%
                    opportunities.append({
                        'type': 'rightsizing',
                        'reason': f'Over-provisioned memory: {avg_duration:.0f}ms avg duration vs {timeout}s timeout',
                        'priority': 'MEDIUM',
                        'estimatedSavings': function_data.get('currentCost', 0) * 0.3,  # 30% savings
                        'confidence': 'MEDIUM',
                        'action': 'reduce_memory',
                        'recommendedMemorySize': recommended_memory
                    })
            
            # Timeout optimization - over-provisioned timeout
            elif max_duration > 0 and max_duration < (timeout * 1000 * 0.3):  # Using less than 30% of timeout
                recommended_timeout = max(3, int((max_duration / 1000) * 1.5))  # 50% buffer
                opportunities.append({
                    'type': 'configuration',
                    'reason': f'Over-provisioned timeout: {max_duration:.0f}ms max duration vs {timeout}s timeout',
                    'priority': 'LOW',
                    'estimatedSavings': 0,  # No direct cost savings but better resource management
                    'confidence': 'MEDIUM',
                    'action': 'reduce_timeout',
                    'recommendedTimeout': recommended_timeout
                })
            
            # Performance optimization - high error rate
            if error_rate > 5:  # More than 5% error rate
                opportunities.append({
                    'type': 'performance',
                    'reason': f'High error rate: {error_rate:.1f}%',
                    'priority': 'HIGH',
                    'estimatedSavings': 0,
                    'confidence': 'HIGH',
                    'action': 'investigate_errors'
                })
            
            # Performance optimization - throttling issues
            if total_throttles > 0:
                opportunities.append({
                    'type': 'performance',
                    'reason': f'Function experiencing throttling: {total_throttles} throttles',
                    'priority': 'HIGH',
                    'estimatedSavings': 0,
                    'confidence': 'HIGH',
                    'action': 'increase_concurrency_limit'
                })
        
        else:
            # Insufficient data
            opportunities.append({
                'type': 'monitoring',
                'reason': f'Insufficient metrics data ({data_points} data points)',
                'priority': 'LOW',
                'estimatedSavings': 0,
                'confidence': 'LOW',
                'action': 'monitor_longer'
            })
        
        # Runtime optimization
        runtime = function_data.get('runtime', '')
        if runtime in ['python2.7', 'nodejs8.10', 'nodejs10.x', 'dotnetcore2.1']:
            opportunities.append({
                'type': 'security',
                'reason': f'Using deprecated runtime: {runtime}',
                'priority': 'HIGH',
                'estimatedSavings': 0,
                'confidence': 'HIGH',
                'action': 'upgrade_runtime'
            })
        
        # VPC configuration optimization
        vpc_config = function_data.get('vpcConfig', {})
        if vpc_config and not vpc_config.get('SubnetIds'):
            opportunities.append({
                'type': 'configuration',
                'reason': 'Function in VPC may have cold start performance issues',
                'priority': 'LOW',
                'estimatedSavings': 0,
                'confidence': 'MEDIUM',
                'action': 'review_vpc_necessity'
            })
        
        # Dead letter queue configuration
        if not function_data.get('deadLetterConfig', {}).get('TargetArn') and error_rate > 1:
            opportunities.append({
                'type': 'configuration',
                'reason': 'No dead letter queue configured despite errors',
                'priority': 'MEDIUM',
                'estimatedSavings': 0,
                'confidence': 'HIGH',
                'action': 'configure_dlq'
            })
        
        # Check for missing tags (cost allocation)
        required_tags = ['Environment', 'Project', 'Owner']
        missing_tags = [tag for tag in required_tags if tag not in function_data.get('tags', {})]
        
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
    
    def _estimate_function_cost(self, memory_size: int, total_invocations: int, avg_duration: float, days_back: int) -> float:
        """
        Estimate cost for a Lambda function based on usage.
        
        Args:
            memory_size: Function memory size in MB
            total_invocations: Total invocations in the period
            avg_duration: Average duration in milliseconds
            days_back: Number of days the metrics cover
            
        Returns:
            Estimated cost for the period in USD
        """
        # AWS Lambda pricing (approximate for us-east-1)
        # $0.0000166667 per GB-second
        # $0.20 per 1M requests
        
        if total_invocations == 0 or avg_duration == 0:
            return 0.0
        
        # Convert memory to GB
        memory_gb = memory_size / 1024.0
        
        # Convert duration to seconds
        avg_duration_seconds = avg_duration / 1000.0
        
        # Calculate GB-seconds
        gb_seconds = total_invocations * memory_gb * avg_duration_seconds
        
        # Calculate costs
        compute_cost = gb_seconds * 0.0000166667
        request_cost = (total_invocations / 1000000.0) * 0.20
        
        total_cost = compute_cost + request_cost
        
        # Scale to monthly cost if needed
        if days_back != 30:
            monthly_cost = total_cost * (30.0 / days_back)
        else:
            monthly_cost = total_cost
        
        return monthly_cost
    
    def get_function_count_by_runtime(self) -> Dict[str, int]:
        """
        Get count of functions by runtime.
        
        Returns:
            Dictionary with runtime counts
        """
        try:
            response = self.lambda_client.list_functions()
            
            runtime_counts = {}
            for function in response['Functions']:
                runtime = function.get('Runtime', 'unknown')
                runtime_counts[runtime] = runtime_counts.get(runtime, 0) + 1
            
            return runtime_counts
            
        except ClientError as e:
            logger.error(f"Failed to get function counts: {e}")
            return {}
    
    def get_optimization_summary(self, functions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate optimization summary for scanned functions.
        
        Args:
            functions: List of analyzed functions
            
        Returns:
            Optimization summary
        """
        summary = {
            'totalFunctions': len(functions),
            'activeFunctions': 0,
            'unusedFunctions': 0,
            'totalMonthlyCost': 0.0,
            'potentialMonthlySavings': 0.0,
            'optimizationOpportunities': {
                'cleanup': 0,
                'rightsizing': 0,
                'configuration': 0,
                'performance': 0,
                'security': 0,
                'governance': 0,
                'monitoring': 0
            },
            'priorityBreakdown': {
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'runtimeBreakdown': {}
        }
        
        for function in functions:
            # Count by usage
            total_invocations = function.get('utilizationMetrics', {}).get('totalInvocations', 0)
            if total_invocations > 0:
                summary['activeFunctions'] += 1
            else:
                summary['unusedFunctions'] += 1
            
            # Sum costs
            summary['totalMonthlyCost'] += function.get('currentCost', 0)
            
            # Runtime breakdown
            runtime = function.get('runtime', 'unknown')
            summary['runtimeBreakdown'][runtime] = summary['runtimeBreakdown'].get(runtime, 0) + 1
            
            # Analyze opportunities
            for opportunity in function.get('optimizationOpportunities', []):
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