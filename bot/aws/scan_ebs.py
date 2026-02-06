#!/usr/bin/env python3
"""
EBS Volume Scanner for Advanced FinOps Platform

Discovers and analyzes EBS volumes across regions, collecting:
- Volume metadata and configuration
- Volume utilization and performance metrics
- Cost data and optimization opportunities
- Unused volumes and snapshot cleanup recommendations

Requirements: 1.1, 7.4
"""

import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class EBSScanner:
    """Scans EBS volumes for cost optimization opportunities."""
    
    def __init__(self, aws_config, region: str = 'us-east-1'):
        """
        Initialize EBS scanner.
        
        Args:
            aws_config: AWSConfig instance for client management
            region: AWS region to scan
        """
        self.aws_config = aws_config
        self.region = region
        self.ec2_client = aws_config.get_client('ec2')
        self.cloudwatch_client = aws_config.get_client('cloudwatch')
        
        logger.info(f"EBS Scanner initialized for region {region}")
    
    def scan_volumes(self, days_back: int = 14) -> List[Dict[str, Any]]:
        """
        Scan all EBS volumes in the region.
        
        Args:
            days_back: Number of days to look back for metrics
            
        Returns:
            List of volume data with utilization metrics
        """
        logger.info(f"Starting EBS volume scan in region {self.region}")
        
        volumes = []
        
        try:
            # Get all EBS volumes
            paginator = self.ec2_client.get_paginator('describe_volumes')
            
            for page in paginator.paginate():
                for volume in page['Volumes']:
                    volume_data = self._analyze_volume(volume, days_back)
                    if volume_data:
                        volumes.append(volume_data)
            
            logger.info(f"Scanned {len(volumes)} EBS volumes")
            
        except ClientError as e:
            logger.error(f"Failed to scan EBS volumes: {e}")
            raise
        
        return volumes
    
    def scan_snapshots(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Scan EBS snapshots for cleanup opportunities.
        
        Args:
            days_back: Number of days to look back for snapshot analysis
            
        Returns:
            List of snapshot data with optimization opportunities
        """
        logger.info(f"Starting EBS snapshot scan in region {self.region}")
        
        snapshots = []
        
        try:
            # Get snapshots owned by this account
            paginator = self.ec2_client.get_paginator('describe_snapshots')
            
            for page in paginator.paginate(OwnerIds=['self']):
                for snapshot in page['Snapshots']:
                    snapshot_data = self._analyze_snapshot(snapshot, days_back)
                    if snapshot_data:
                        snapshots.append(snapshot_data)
            
            logger.info(f"Scanned {len(snapshots)} EBS snapshots")
            
        except ClientError as e:
            logger.error(f"Failed to scan EBS snapshots: {e}")
            raise
        
        return snapshots
    
    def _analyze_volume(self, volume: Dict[str, Any], days_back: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single EBS volume.
        
        Args:
            volume: EBS volume data from describe_volumes
            days_back: Number of days to analyze metrics
            
        Returns:
            Volume analysis data or None if analysis fails
        """
        volume_id = volume['VolumeId']
        
        try:
            # Basic volume information
            volume_data = {
                'resourceId': volume_id,
                'resourceType': 'ebs',
                'region': self.region,
                'volumeId': volume_id,
                'volumeType': volume.get('VolumeType', 'unknown'),
                'size': volume.get('Size', 0),  # Size in GB
                'state': volume.get('State', 'unknown'),
                'encrypted': volume.get('Encrypted', False),
                'iops': volume.get('Iops', 0),
                'throughput': volume.get('Throughput', 0),
                'availabilityZone': volume.get('AvailabilityZone'),
                'createTime': volume.get('CreateTime', datetime.utcnow()).isoformat(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Check if volume is attached
            attachments = volume.get('Attachments', [])
            if attachments:
                attachment = attachments[0]  # Usually only one attachment
                volume_data.update({
                    'attached': True,
                    'instanceId': attachment.get('InstanceId'),
                    'device': attachment.get('Device'),
                    'attachTime': attachment.get('AttachTime', datetime.utcnow()).isoformat(),
                    'deleteOnTermination': attachment.get('DeleteOnTermination', False)
                })
            else:
                volume_data.update({
                    'attached': False,
                    'instanceId': None,
                    'device': None,
                    'attachTime': None,
                    'deleteOnTermination': False
                })
            
            # Extract tags
            tags = {}
            for tag in volume.get('Tags', []):
                tags[tag['Key']] = tag['Value']
            volume_data['tags'] = tags
            
            # Get utilization metrics only for attached volumes
            if volume_data['attached'] and volume_data['state'] == 'in-use':
                metrics = self._get_volume_metrics(volume_id, days_back)
                volume_data['utilizationMetrics'] = metrics
            else:
                volume_data['utilizationMetrics'] = {}
            
            # Calculate optimization opportunities
            opportunities = self._identify_volume_optimization_opportunities(volume_data)
            volume_data['optimizationOpportunities'] = opportunities
            
            # Estimate current cost
            volume_data['currentCost'] = self._estimate_volume_cost(
                volume_data['volumeType'],
                volume_data['size'],
                volume_data['iops'],
                volume_data['throughput']
            )
            
            return volume_data
            
        except Exception as e:
            logger.error(f"Failed to analyze volume {volume_id}: {e}")
            return None
    
    def _analyze_snapshot(self, snapshot: Dict[str, Any], days_back: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single EBS snapshot.
        
        Args:
            snapshot: EBS snapshot data from describe_snapshots
            days_back: Number of days to analyze for cleanup opportunities
            
        Returns:
            Snapshot analysis data or None if analysis fails
        """
        snapshot_id = snapshot['SnapshotId']
        
        try:
            # Basic snapshot information
            snapshot_data = {
                'resourceId': snapshot_id,
                'resourceType': 'ebs-snapshot',
                'region': self.region,
                'snapshotId': snapshot_id,
                'volumeId': snapshot.get('VolumeId'),
                'volumeSize': snapshot.get('VolumeSize', 0),
                'state': snapshot.get('State', 'unknown'),
                'progress': snapshot.get('Progress', '0%'),
                'startTime': snapshot.get('StartTime', datetime.utcnow()).isoformat(),
                'description': snapshot.get('Description', ''),
                'encrypted': snapshot.get('Encrypted', False),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Calculate age
            start_time = snapshot.get('StartTime', datetime.utcnow())
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            age_days = (datetime.utcnow().replace(tzinfo=start_time.tzinfo) - start_time).days
            snapshot_data['ageDays'] = age_days
            
            # Extract tags
            tags = {}
            for tag in snapshot.get('Tags', []):
                tags[tag['Key']] = tag['Value']
            snapshot_data['tags'] = tags
            
            # Check if source volume still exists
            try:
                self.ec2_client.describe_volumes(VolumeIds=[snapshot['VolumeId']])
                snapshot_data['sourceVolumeExists'] = True
            except ClientError as e:
                if e.response['Error']['Code'] == 'InvalidVolume.NotFound':
                    snapshot_data['sourceVolumeExists'] = False
                else:
                    snapshot_data['sourceVolumeExists'] = 'unknown'
            
            # Calculate optimization opportunities
            opportunities = self._identify_snapshot_optimization_opportunities(snapshot_data, days_back)
            snapshot_data['optimizationOpportunities'] = opportunities
            
            # Estimate current cost
            snapshot_data['currentCost'] = self._estimate_snapshot_cost(snapshot_data['volumeSize'])
            
            return snapshot_data
            
        except Exception as e:
            logger.error(f"Failed to analyze snapshot {snapshot_id}: {e}")
            return None
    
    def _get_volume_metrics(self, volume_id: str, days_back: int) -> Dict[str, Any]:
        """
        Get CloudWatch metrics for an EBS volume.
        
        Args:
            volume_id: EBS volume ID
            days_back: Number of days to retrieve metrics
            
        Returns:
            Dictionary containing utilization metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        metrics = {
            'volumeReadOps': [],
            'volumeWriteOps': [],
            'volumeReadBytes': [],
            'volumeWriteBytes': [],
            'volumeQueueLength': [],
            'volumeTotalReadTime': [],
            'volumeTotalWriteTime': [],
            'period': f"{days_back} days",
            'dataPoints': 0
        }
        
        try:
            # Volume Read Ops
            read_ops_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EBS',
                MetricName='VolumeReadOps',
                Dimensions=[
                    {
                        'Name': 'VolumeId',
                        'Value': volume_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['Sum']
            )
            
            read_ops_datapoints = sorted(read_ops_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['volumeReadOps'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in read_ops_datapoints
            ]
            
            # Volume Write Ops
            write_ops_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EBS',
                MetricName='VolumeWriteOps',
                Dimensions=[
                    {
                        'Name': 'VolumeId',
                        'Value': volume_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            write_ops_datapoints = sorted(write_ops_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['volumeWriteOps'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in write_ops_datapoints
            ]
            
            # Volume Read Bytes
            read_bytes_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EBS',
                MetricName='VolumeReadBytes',
                Dimensions=[
                    {
                        'Name': 'VolumeId',
                        'Value': volume_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            read_bytes_datapoints = sorted(read_bytes_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['volumeReadBytes'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in read_bytes_datapoints
            ]
            
            # Volume Write Bytes
            write_bytes_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EBS',
                MetricName='VolumeWriteBytes',
                Dimensions=[
                    {
                        'Name': 'VolumeId',
                        'Value': volume_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            write_bytes_datapoints = sorted(write_bytes_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['volumeWriteBytes'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in write_bytes_datapoints
            ]
            
            # Volume Queue Length
            queue_length_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EBS',
                MetricName='VolumeQueueLength',
                Dimensions=[
                    {
                        'Name': 'VolumeId',
                        'Value': volume_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )
            
            queue_length_datapoints = sorted(queue_length_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['volumeQueueLength'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average']
                }
                for dp in queue_length_datapoints
            ]
            
            # Calculate summary statistics
            if metrics['volumeReadOps']:
                metrics['totalReadOps'] = sum(dp['sum'] for dp in metrics['volumeReadOps'])
                metrics['avgReadOpsPerHour'] = metrics['totalReadOps'] / len(metrics['volumeReadOps'])
                metrics['dataPoints'] = len(metrics['volumeReadOps'])
            else:
                metrics['totalReadOps'] = 0
                metrics['avgReadOpsPerHour'] = 0
                metrics['dataPoints'] = 0
            
            if metrics['volumeWriteOps']:
                metrics['totalWriteOps'] = sum(dp['sum'] for dp in metrics['volumeWriteOps'])
                metrics['avgWriteOpsPerHour'] = metrics['totalWriteOps'] / len(metrics['volumeWriteOps'])
            else:
                metrics['totalWriteOps'] = 0
                metrics['avgWriteOpsPerHour'] = 0
            
            if metrics['volumeReadBytes']:
                metrics['totalReadBytes'] = sum(dp['sum'] for dp in metrics['volumeReadBytes'])
                metrics['totalReadGB'] = metrics['totalReadBytes'] / (1024 ** 3)
            else:
                metrics['totalReadBytes'] = 0
                metrics['totalReadGB'] = 0
            
            if metrics['volumeWriteBytes']:
                metrics['totalWriteBytes'] = sum(dp['sum'] for dp in metrics['volumeWriteBytes'])
                metrics['totalWriteGB'] = metrics['totalWriteBytes'] / (1024 ** 3)
            else:
                metrics['totalWriteBytes'] = 0
                metrics['totalWriteGB'] = 0
            
            if metrics['volumeQueueLength']:
                queue_averages = [dp['average'] for dp in metrics['volumeQueueLength']]
                metrics['avgQueueLength'] = sum(queue_averages) / len(queue_averages)
            else:
                metrics['avgQueueLength'] = 0
            
            # Calculate total I/O activity
            metrics['totalIOPS'] = metrics['totalReadOps'] + metrics['totalWriteOps']
            metrics['avgIOPSPerHour'] = metrics['avgReadOpsPerHour'] + metrics['avgWriteOpsPerHour']
            
            logger.debug(f"Retrieved {metrics['dataPoints']} metric data points for volume {volume_id}")
            
        except ClientError as e:
            logger.warning(f"Failed to retrieve metrics for volume {volume_id}: {e}")
            # Return empty metrics on failure
            metrics.update({
                'totalReadOps': 0,
                'totalWriteOps': 0,
                'totalIOPS': 0,
                'avgIOPSPerHour': 0,
                'totalReadGB': 0,
                'totalWriteGB': 0,
                'avgQueueLength': 0
            })
        
        return metrics
    
    def _identify_volume_optimization_opportunities(self, volume_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities for an EBS volume.
        
        Args:
            volume_data: Volume metadata and metrics
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        volume_type = volume_data.get('volumeType', '')
        size = volume_data.get('size', 0)
        attached = volume_data.get('attached', False)
        state = volume_data.get('state', '')
        iops = volume_data.get('iops', 0)
        
        metrics = volume_data.get('utilizationMetrics', {})
        total_iops = metrics.get('totalIOPS', 0)
        avg_iops_per_hour = metrics.get('avgIOPSPerHour', 0)
        avg_queue_length = metrics.get('avgQueueLength', 0)
        data_points = metrics.get('dataPoints', 0)
        
        # Unattached volume
        if not attached:
            opportunities.append({
                'type': 'cleanup',
                'reason': f'Volume is not attached to any instance (state: {state})',
                'priority': 'HIGH',
                'estimatedSavings': volume_data.get('currentCost', 0),  # Full cost savings
                'confidence': 'HIGH',
                'action': 'consider_deletion'
            })
        
        # Attached volume with sufficient metrics
        elif attached and data_points >= 24:  # At least 24 hours of data
            
            # Unused volume (no I/O activity)
            if total_iops == 0:
                opportunities.append({
                    'type': 'cleanup',
                    'reason': 'Volume has no I/O activity',
                    'priority': 'HIGH',
                    'estimatedSavings': volume_data.get('currentCost', 0) * 0.9,  # 90% savings
                    'confidence': 'HIGH',
                    'action': 'review_necessity'
                })
            
            # Low utilization volume
            elif avg_iops_per_hour < 10:
                opportunities.append({
                    'type': 'rightsizing',
                    'reason': f'Very low I/O activity: {avg_iops_per_hour:.1f} IOPS/hour',
                    'priority': 'MEDIUM',
                    'estimatedSavings': volume_data.get('currentCost', 0) * 0.3,  # 30% savings
                    'confidence': 'MEDIUM',
                    'action': 'consider_gp2_to_gp3'
                })
            
            # Over-provisioned IOPS
            if volume_type == 'io1' or volume_type == 'io2':
                if avg_iops_per_hour < (iops * 0.1):  # Using less than 10% of provisioned IOPS
                    opportunities.append({
                        'type': 'rightsizing',
                        'reason': f'Over-provisioned IOPS: {avg_iops_per_hour:.1f} avg vs {iops} provisioned',
                        'priority': 'HIGH',
                        'estimatedSavings': volume_data.get('currentCost', 0) * 0.5,  # 50% savings
                        'confidence': 'HIGH',
                        'action': 'reduce_provisioned_iops'
                    })
            
            # Volume type optimization
            if volume_type == 'gp2' and avg_iops_per_hour > 0:
                opportunities.append({
                    'type': 'configuration',
                    'reason': 'GP2 volume could benefit from GP3 for better price/performance',
                    'priority': 'MEDIUM',
                    'estimatedSavings': volume_data.get('currentCost', 0) * 0.2,  # 20% savings
                    'confidence': 'MEDIUM',
                    'action': 'convert_gp2_to_gp3'
                })
            
            # Performance optimization - high queue length
            if avg_queue_length > 5:
                opportunities.append({
                    'type': 'performance',
                    'reason': f'High average queue length: {avg_queue_length:.1f}',
                    'priority': 'MEDIUM',
                    'estimatedSavings': 0,
                    'confidence': 'MEDIUM',
                    'action': 'increase_iops_or_throughput'
                })
        
        # Insufficient metrics data
        elif attached and data_points < 24:
            opportunities.append({
                'type': 'monitoring',
                'reason': f'Insufficient metrics data ({data_points} data points)',
                'priority': 'LOW',
                'estimatedSavings': 0,
                'confidence': 'LOW',
                'action': 'monitor_longer'
            })
        
        # Encryption optimization
        if not volume_data.get('encrypted', False):
            opportunities.append({
                'type': 'security',
                'reason': 'Volume is not encrypted',
                'priority': 'MEDIUM',
                'estimatedSavings': 0,
                'confidence': 'HIGH',
                'action': 'enable_encryption'
            })
        
        # Snapshot optimization
        if not volume_data.get('deleteOnTermination', False) and attached:
            opportunities.append({
                'type': 'configuration',
                'reason': 'Volume will not be deleted when instance terminates',
                'priority': 'LOW',
                'estimatedSavings': 0,
                'confidence': 'HIGH',
                'action': 'enable_delete_on_termination'
            })
        
        # Check for missing tags (cost allocation)
        required_tags = ['Environment', 'Project', 'Owner']
        missing_tags = [tag for tag in required_tags if tag not in volume_data.get('tags', {})]
        
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
    
    def _identify_snapshot_optimization_opportunities(self, snapshot_data: Dict[str, Any], days_back: int) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities for an EBS snapshot.
        
        Args:
            snapshot_data: Snapshot metadata
            days_back: Number of days for analysis
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        age_days = snapshot_data.get('ageDays', 0)
        source_volume_exists = snapshot_data.get('sourceVolumeExists', True)
        state = snapshot_data.get('state', '')
        
        # Old snapshots
        if age_days > 365:  # Older than 1 year
            opportunities.append({
                'type': 'cleanup',
                'reason': f'Snapshot is {age_days} days old',
                'priority': 'MEDIUM',
                'estimatedSavings': snapshot_data.get('currentCost', 0),
                'confidence': 'MEDIUM',
                'action': 'consider_deletion'
            })
        elif age_days > 90:  # Older than 3 months
            opportunities.append({
                'type': 'cleanup',
                'reason': f'Snapshot is {age_days} days old - review retention policy',
                'priority': 'LOW',
                'estimatedSavings': snapshot_data.get('currentCost', 0),
                'confidence': 'LOW',
                'action': 'review_retention_policy'
            })
        
        # Orphaned snapshots (source volume no longer exists)
        if not source_volume_exists:
            opportunities.append({
                'type': 'cleanup',
                'reason': 'Source volume no longer exists',
                'priority': 'HIGH',
                'estimatedSavings': snapshot_data.get('currentCost', 0),
                'confidence': 'HIGH',
                'action': 'consider_deletion'
            })
        
        # Failed snapshots
        if state == 'error':
            opportunities.append({
                'type': 'cleanup',
                'reason': 'Snapshot is in error state',
                'priority': 'HIGH',
                'estimatedSavings': snapshot_data.get('currentCost', 0),
                'confidence': 'HIGH',
                'action': 'delete_failed_snapshot'
            })
        
        # Check for missing tags (cost allocation)
        required_tags = ['Environment', 'Project', 'Owner']
        missing_tags = [tag for tag in required_tags if tag not in snapshot_data.get('tags', {})]
        
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
    
    def _estimate_volume_cost(self, volume_type: str, size: int, iops: int = 0, throughput: int = 0) -> float:
        """
        Estimate monthly cost for an EBS volume.
        
        Args:
            volume_type: EBS volume type
            size: Volume size in GB
            iops: Provisioned IOPS (for io1/io2 volumes)
            throughput: Provisioned throughput (for gp3 volumes)
            
        Returns:
            Estimated monthly cost in USD
        """
        # Simplified cost estimation (would use AWS Price List API in production)
        # These are approximate costs for us-east-1 region
        
        if size == 0:
            return 0.0
        
        # Storage costs per GB per month
        storage_costs = {
            'gp2': 0.10,
            'gp3': 0.08,
            'io1': 0.125,
            'io2': 0.125,
            'st1': 0.045,
            'sc1': 0.025,
            'standard': 0.05
        }
        
        storage_cost = size * storage_costs.get(volume_type, 0.10)
        
        # IOPS costs (for io1/io2)
        if volume_type in ['io1', 'io2'] and iops > 0:
            iops_cost = iops * 0.065  # $0.065 per provisioned IOPS per month
            storage_cost += iops_cost
        
        # Throughput costs (for gp3)
        if volume_type == 'gp3' and throughput > 125:  # Base throughput is 125 MB/s
            additional_throughput = throughput - 125
            throughput_cost = additional_throughput * 0.04  # $0.04 per MB/s per month
            storage_cost += throughput_cost
        
        return storage_cost
    
    def _estimate_snapshot_cost(self, volume_size: int) -> float:
        """
        Estimate monthly cost for an EBS snapshot.
        
        Args:
            volume_size: Original volume size in GB
            
        Returns:
            Estimated monthly cost in USD
        """
        # Simplified estimation - actual cost depends on data changes
        # Assume snapshot is 50% of original volume size on average
        estimated_size = volume_size * 0.5
        
        # EBS snapshot cost: $0.05 per GB per month
        return estimated_size * 0.05
    
    def get_volume_count_by_type(self) -> Dict[str, int]:
        """
        Get count of volumes by type.
        
        Returns:
            Dictionary with volume type counts
        """
        try:
            response = self.ec2_client.describe_volumes()
            
            type_counts = {}
            for volume in response['Volumes']:
                volume_type = volume.get('VolumeType', 'unknown')
                type_counts[volume_type] = type_counts.get(volume_type, 0) + 1
            
            return type_counts
            
        except ClientError as e:
            logger.error(f"Failed to get volume counts: {e}")
            return {}
    
    def get_optimization_summary(self, volumes: List[Dict[str, Any]], snapshots: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate optimization summary for scanned volumes and snapshots.
        
        Args:
            volumes: List of analyzed volumes
            snapshots: List of analyzed snapshots (optional)
            
        Returns:
            Optimization summary
        """
        summary = {
            'totalVolumes': len(volumes),
            'attachedVolumes': 0,
            'unattachedVolumes': 0,
            'totalStorageGB': 0,
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
            'volumeTypeBreakdown': {}
        }
        
        # Analyze volumes
        for volume in volumes:
            # Count by attachment status
            if volume.get('attached', False):
                summary['attachedVolumes'] += 1
            else:
                summary['unattachedVolumes'] += 1
            
            # Sum storage and costs
            summary['totalStorageGB'] += volume.get('size', 0)
            summary['totalMonthlyCost'] += volume.get('currentCost', 0)
            
            # Volume type breakdown
            volume_type = volume.get('volumeType', 'unknown')
            summary['volumeTypeBreakdown'][volume_type] = summary['volumeTypeBreakdown'].get(volume_type, 0) + 1
            
            # Analyze opportunities
            for opportunity in volume.get('optimizationOpportunities', []):
                opp_type = opportunity.get('type', 'unknown')
                priority = opportunity.get('priority', 'LOW')
                savings = opportunity.get('estimatedSavings', 0)
                
                if opp_type in summary['optimizationOpportunities']:
                    summary['optimizationOpportunities'][opp_type] += 1
                
                if priority in summary['priorityBreakdown']:
                    summary['priorityBreakdown'][priority] += 1
                
                summary['potentialMonthlySavings'] += savings
        
        # Analyze snapshots if provided
        if snapshots:
            summary['totalSnapshots'] = len(snapshots)
            summary['orphanedSnapshots'] = 0
            summary['oldSnapshots'] = 0
            
            for snapshot in snapshots:
                summary['totalMonthlyCost'] += snapshot.get('currentCost', 0)
                
                # Count orphaned and old snapshots
                if not snapshot.get('sourceVolumeExists', True):
                    summary['orphanedSnapshots'] += 1
                
                if snapshot.get('ageDays', 0) > 90:
                    summary['oldSnapshots'] += 1
                
                # Analyze snapshot opportunities
                for opportunity in snapshot.get('optimizationOpportunities', []):
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