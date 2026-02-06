#!/usr/bin/env python3
"""
RDS Resource Scanner for Advanced FinOps Platform

Discovers and analyzes RDS database instances across regions, collecting:
- Database instance metadata and configuration
- Database utilization and performance metrics from CloudWatch
- Cost data and optimization opportunities
- Unused databases and optimization recommendations

Requirements: 1.1, 7.1
"""

import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class RDSScanner:
    """Scans RDS database instances for cost optimization opportunities."""
    
    def __init__(self, aws_config, region: str = 'us-east-1'):
        """
        Initialize RDS scanner.
        
        Args:
            aws_config: AWSConfig instance for client management
            region: AWS region to scan
        """
        self.aws_config = aws_config
        self.region = region
        self.rds_client = aws_config.get_client('rds')
        self.cloudwatch_client = aws_config.get_client('cloudwatch')
        
        logger.info(f"RDS Scanner initialized for region {region}")
    
    def scan_databases(self, days_back: int = 14) -> List[Dict[str, Any]]:
        """
        Scan all RDS database instances in the region.
        
        Args:
            days_back: Number of days to look back for metrics
            
        Returns:
            List of database instance data with utilization metrics
        """
        logger.info(f"Starting RDS database scan in region {self.region}")
        
        databases = []
        
        try:
            # Get all RDS instances
            paginator = self.rds_client.get_paginator('describe_db_instances')
            
            for page in paginator.paginate():
                for db_instance in page['DBInstances']:
                    db_data = self._analyze_database(db_instance, days_back)
                    if db_data:
                        databases.append(db_data)
            
            logger.info(f"Scanned {len(databases)} RDS database instances")
            
        except ClientError as e:
            logger.error(f"Failed to scan RDS instances: {e}")
            raise
        
        return databases
    
    def _analyze_database(self, db_instance: Dict[str, Any], days_back: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single RDS database instance.
        
        Args:
            db_instance: RDS instance data from describe_db_instances
            days_back: Number of days to analyze metrics
            
        Returns:
            Database analysis data or None if analysis fails
        """
        db_identifier = db_instance['DBInstanceIdentifier']
        
        try:
            # Basic database information
            db_data = {
                'resourceId': db_identifier,
                'resourceType': 'rds',
                'region': self.region,
                'dbInstanceClass': db_instance.get('DBInstanceClass', 'unknown'),
                'engine': db_instance.get('Engine', 'unknown'),
                'engineVersion': db_instance.get('EngineVersion', 'unknown'),
                'status': db_instance.get('DBInstanceStatus', 'unknown'),
                'allocatedStorage': db_instance.get('AllocatedStorage', 0),
                'storageType': db_instance.get('StorageType', 'unknown'),
                'multiAZ': db_instance.get('MultiAZ', False),
                'publiclyAccessible': db_instance.get('PubliclyAccessible', False),
                'storageEncrypted': db_instance.get('StorageEncrypted', False),
                'availabilityZone': db_instance.get('AvailabilityZone'),
                'vpcId': db_instance.get('DBSubnetGroup', {}).get('VpcId') if db_instance.get('DBSubnetGroup') else None,
                'instanceCreateTime': db_instance.get('InstanceCreateTime', datetime.utcnow()).isoformat(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Extract tags
            try:
                tags_response = self.rds_client.list_tags_for_resource(
                    ResourceName=db_instance['DBInstanceArn']
                )
                tags = {}
                for tag in tags_response.get('TagList', []):
                    tags[tag['Key']] = tag['Value']
                db_data['tags'] = tags
            except ClientError as e:
                logger.warning(f"Failed to get tags for {db_identifier}: {e}")
                db_data['tags'] = {}
            
            # Get utilization metrics only for available databases
            if db_data['status'] == 'available':
                metrics = self._get_database_metrics(db_identifier, days_back)
                db_data['utilizationMetrics'] = metrics
                
                # Calculate optimization opportunities
                opportunities = self._identify_optimization_opportunities(db_data, metrics)
                db_data['optimizationOpportunities'] = opportunities
                
                # Estimate current cost
                db_data['currentCost'] = self._estimate_database_cost(
                    db_data['dbInstanceClass'],
                    db_data['engine'],
                    db_data['allocatedStorage'],
                    db_data['storageType'],
                    db_data['multiAZ']
                )
            else:
                # For non-available databases, mark as potential issues
                db_data['utilizationMetrics'] = {}
                db_data['optimizationOpportunities'] = [{
                    'type': 'monitoring',
                    'reason': f'Database in {db_data["status"]} state',
                    'priority': 'MEDIUM' if db_data['status'] in ['stopped', 'stopping'] else 'HIGH',
                    'estimatedSavings': 0,
                    'action': 'investigate_status'
                }]
                db_data['currentCost'] = 0.0
            
            return db_data
            
        except Exception as e:
            logger.error(f"Failed to analyze database {db_identifier}: {e}")
            return None
    
    def _get_database_metrics(self, db_identifier: str, days_back: int) -> Dict[str, Any]:
        """
        Get CloudWatch metrics for an RDS database instance.
        
        Args:
            db_identifier: RDS database identifier
            days_back: Number of days to retrieve metrics
            
        Returns:
            Dictionary containing utilization metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        metrics = {
            'cpuUtilization': [],
            'databaseConnections': [],
            'freeableMemory': [],
            'freeStorageSpace': [],
            'readIOPS': [],
            'writeIOPS': [],
            'readLatency': [],
            'writeLatency': [],
            'period': f"{days_back} days",
            'dataPoints': 0
        }
        
        try:
            # CPU Utilization
            cpu_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db_identifier
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['Average', 'Maximum']
            )
            
            cpu_datapoints = sorted(cpu_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['cpuUtilization'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average'],
                    'maximum': dp['Maximum']
                }
                for dp in cpu_datapoints
            ]
            
            # Database Connections
            connections_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='DatabaseConnections',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db_identifier
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            connections_datapoints = sorted(connections_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['databaseConnections'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average'],
                    'maximum': dp['Maximum']
                }
                for dp in connections_datapoints
            ]
            
            # Freeable Memory
            memory_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='FreeableMemory',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db_identifier
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Minimum']
            )
            
            memory_datapoints = sorted(memory_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['freeableMemory'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average'],
                    'minimum': dp['Minimum']
                }
                for dp in memory_datapoints
            ]
            
            # Free Storage Space
            storage_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='FreeStorageSpace',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db_identifier
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Minimum']
            )
            
            storage_datapoints = sorted(storage_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['freeStorageSpace'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average'],
                    'minimum': dp['Minimum']
                }
                for dp in storage_datapoints
            ]
            
            # Read IOPS
            read_iops_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='ReadIOPS',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db_identifier
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            read_iops_datapoints = sorted(read_iops_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['readIOPS'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average'],
                    'maximum': dp['Maximum']
                }
                for dp in read_iops_datapoints
            ]
            
            # Write IOPS
            write_iops_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='WriteIOPS',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db_identifier
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            write_iops_datapoints = sorted(write_iops_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['writeIOPS'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average'],
                    'maximum': dp['Maximum']
                }
                for dp in write_iops_datapoints
            ]
            
            # Calculate summary statistics
            if metrics['cpuUtilization']:
                cpu_averages = [dp['average'] for dp in metrics['cpuUtilization']]
                metrics['avgCpuUtilization'] = sum(cpu_averages) / len(cpu_averages)
                metrics['maxCpuUtilization'] = max(dp['maximum'] for dp in metrics['cpuUtilization'])
                metrics['dataPoints'] = len(cpu_averages)
            else:
                metrics['avgCpuUtilization'] = 0.0
                metrics['maxCpuUtilization'] = 0.0
                metrics['dataPoints'] = 0
            
            # Connection statistics
            if metrics['databaseConnections']:
                connection_averages = [dp['average'] for dp in metrics['databaseConnections']]
                metrics['avgConnections'] = sum(connection_averages) / len(connection_averages)
                metrics['maxConnections'] = max(dp['maximum'] for dp in metrics['databaseConnections'])
            else:
                metrics['avgConnections'] = 0.0
                metrics['maxConnections'] = 0.0
            
            logger.debug(f"Retrieved {metrics['dataPoints']} metric data points for database {db_identifier}")
            
        except ClientError as e:
            logger.warning(f"Failed to retrieve metrics for database {db_identifier}: {e}")
            # Return empty metrics on failure
            metrics['avgCpuUtilization'] = 0.0
            metrics['maxCpuUtilization'] = 0.0
            metrics['avgConnections'] = 0.0
            metrics['maxConnections'] = 0.0
        
        return metrics
    
    def _identify_optimization_opportunities(self, db_data: Dict[str, Any], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities for a database instance.
        
        Args:
            db_data: Database metadata
            metrics: Utilization metrics
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        # CPU and connection-based optimizations
        avg_cpu = metrics.get('avgCpuUtilization', 0)
        max_cpu = metrics.get('maxCpuUtilization', 0)
        avg_connections = metrics.get('avgConnections', 0)
        max_connections = metrics.get('maxConnections', 0)
        data_points = metrics.get('dataPoints', 0)
        
        # Only analyze if we have sufficient data
        if data_points >= 24:  # At least 24 hours of data
            
            # Unused database (very low CPU and connections)
            if avg_cpu < 5.0 and max_cpu < 20.0 and avg_connections < 1.0:
                opportunities.append({
                    'type': 'cleanup',
                    'reason': f'Very low utilization: {avg_cpu:.1f}% avg CPU, {avg_connections:.1f} avg connections',
                    'priority': 'HIGH',
                    'estimatedSavings': db_data.get('currentCost', 0) * 0.95,  # 95% savings
                    'confidence': 'HIGH',
                    'action': 'consider_deletion'
                })
            
            # Underutilized database (low CPU and connections)
            elif avg_cpu < 20.0 and max_cpu < 50.0 and avg_connections < 10.0:
                opportunities.append({
                    'type': 'rightsizing',
                    'reason': f'Low utilization: {avg_cpu:.1f}% avg CPU, {avg_connections:.1f} avg connections',
                    'priority': 'MEDIUM',
                    'estimatedSavings': db_data.get('currentCost', 0) * 0.4,  # 40% savings
                    'confidence': 'MEDIUM',
                    'action': 'downsize',
                    'recommendedInstanceClass': self._recommend_smaller_instance_class(db_data['dbInstanceClass'])
                })
            
            # Over-provisioned storage
            free_storage_points = metrics.get('freeStorageSpace', [])
            if free_storage_points:
                # Convert bytes to GB and calculate average free space percentage
                allocated_storage_bytes = db_data.get('allocatedStorage', 0) * 1024 * 1024 * 1024  # GB to bytes
                if allocated_storage_bytes > 0:
                    avg_free_storage = sum(dp['average'] for dp in free_storage_points) / len(free_storage_points)
                    free_storage_percentage = (avg_free_storage / allocated_storage_bytes) * 100
                    
                    if free_storage_percentage > 70:  # More than 70% free
                        opportunities.append({
                            'type': 'storage_optimization',
                            'reason': f'Over-provisioned storage: {free_storage_percentage:.1f}% free space',
                            'priority': 'MEDIUM',
                            'estimatedSavings': db_data.get('currentCost', 0) * 0.2,  # 20% savings
                            'confidence': 'MEDIUM',
                            'action': 'reduce_storage'
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
        
        # Multi-AZ optimization for non-production workloads
        if db_data.get('multiAZ', False):
            # Check if this might be a development/test database
            tags = db_data.get('tags', {})
            environment = tags.get('Environment', '').lower()
            if environment in ['dev', 'test', 'development', 'testing', 'staging']:
                opportunities.append({
                    'type': 'configuration',
                    'reason': f'Multi-AZ enabled for {environment} environment',
                    'priority': 'MEDIUM',
                    'estimatedSavings': db_data.get('currentCost', 0) * 0.5,  # 50% savings
                    'confidence': 'HIGH',
                    'action': 'disable_multi_az'
                })
        
        # Storage type optimization
        storage_type = db_data.get('storageType', '')
        if storage_type == 'io1' and avg_cpu < 30:  # Provisioned IOPS but low utilization
            opportunities.append({
                'type': 'storage_optimization',
                'reason': 'Provisioned IOPS storage with low utilization',
                'priority': 'MEDIUM',
                'estimatedSavings': db_data.get('currentCost', 0) * 0.3,  # 30% savings
                'confidence': 'MEDIUM',
                'action': 'change_to_gp2'
            })
        
        # Security optimization
        if db_data.get('publiclyAccessible', False):
            opportunities.append({
                'type': 'security',
                'reason': 'Database is publicly accessible',
                'priority': 'HIGH',
                'estimatedSavings': 0,
                'confidence': 'HIGH',
                'action': 'make_private'
            })
        
        # Encryption optimization
        if not db_data.get('storageEncrypted', False):
            opportunities.append({
                'type': 'security',
                'reason': 'Database storage is not encrypted',
                'priority': 'MEDIUM',
                'estimatedSavings': 0,
                'confidence': 'HIGH',
                'action': 'enable_encryption'
            })
        
        # Check for missing tags (cost allocation)
        required_tags = ['Environment', 'Project', 'Owner']
        missing_tags = [tag for tag in required_tags if tag not in db_data.get('tags', {})]
        
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
    
    def _recommend_smaller_instance_class(self, current_class: str) -> str:
        """
        Recommend a smaller RDS instance class for right-sizing.
        
        Args:
            current_class: Current RDS instance class
            
        Returns:
            Recommended smaller instance class
        """
        # Simple mapping for common instance classes
        downsize_map = {
            # General Purpose
            'db.t3.large': 'db.t3.medium',
            'db.t3.medium': 'db.t3.small',
            'db.t3.small': 'db.t3.micro',
            'db.t3.xlarge': 'db.t3.large',
            'db.t3.2xlarge': 'db.t3.xlarge',
            
            'db.m5.large': 'db.m5.medium',
            'db.m5.xlarge': 'db.m5.large',
            'db.m5.2xlarge': 'db.m5.xlarge',
            'db.m5.4xlarge': 'db.m5.2xlarge',
            
            # Memory Optimized
            'db.r5.large': 'db.r5.medium',
            'db.r5.xlarge': 'db.r5.large',
            'db.r5.2xlarge': 'db.r5.xlarge',
            'db.r5.4xlarge': 'db.r5.2xlarge',
        }
        
        return downsize_map.get(current_class, current_class)
    
    def _estimate_database_cost(self, instance_class: str, engine: str, allocated_storage: int, 
                               storage_type: str, multi_az: bool) -> float:
        """
        Estimate monthly cost for an RDS database instance.
        
        Args:
            instance_class: RDS instance class
            engine: Database engine
            allocated_storage: Storage size in GB
            storage_type: Storage type (gp2, io1, etc.)
            multi_az: Whether Multi-AZ is enabled
            
        Returns:
            Estimated monthly cost in USD
        """
        # Simplified cost estimation (would use AWS Price List API in production)
        # These are approximate costs for us-east-1 region
        
        instance_costs = {
            # General Purpose
            'db.t3.micro': 14.02,
            'db.t3.small': 28.03,
            'db.t3.medium': 56.06,
            'db.t3.large': 112.13,
            'db.t3.xlarge': 224.26,
            'db.t3.2xlarge': 448.51,
            
            'db.m5.large': 175.20,
            'db.m5.xlarge': 350.40,
            'db.m5.2xlarge': 700.80,
            'db.m5.4xlarge': 1401.60,
            
            # Memory Optimized
            'db.r5.large': 230.69,
            'db.r5.xlarge': 461.38,
            'db.r5.2xlarge': 922.75,
            'db.r5.4xlarge': 1845.50,
        }
        
        # Base instance cost
        instance_cost = instance_costs.get(instance_class, 200.0)  # Default fallback
        
        # Storage cost (approximate)
        storage_cost_per_gb = {
            'gp2': 0.115,
            'io1': 0.125,
            'standard': 0.10
        }
        storage_cost = allocated_storage * storage_cost_per_gb.get(storage_type, 0.115) * 24 * 30 / 1000  # Monthly
        
        # Multi-AZ doubles the cost
        if multi_az:
            instance_cost *= 2
            storage_cost *= 2
        
        # Engine-specific adjustments
        if engine in ['oracle-ee', 'sqlserver-ee']:
            instance_cost *= 2  # License costs
        elif engine in ['oracle-se2', 'sqlserver-se']:
            instance_cost *= 1.5
        
        return instance_cost + storage_cost
    
    def get_database_count_by_status(self) -> Dict[str, int]:
        """
        Get count of databases by status.
        
        Returns:
            Dictionary with status counts
        """
        try:
            response = self.rds_client.describe_db_instances()
            
            status_counts = {}
            for db_instance in response['DBInstances']:
                status = db_instance.get('DBInstanceStatus', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return status_counts
            
        except ClientError as e:
            logger.error(f"Failed to get database counts: {e}")
            return {}
    
    def get_optimization_summary(self, databases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate optimization summary for scanned databases.
        
        Args:
            databases: List of analyzed databases
            
        Returns:
            Optimization summary
        """
        summary = {
            'totalDatabases': len(databases),
            'availableDatabases': 0,
            'stoppedDatabases': 0,
            'totalMonthlyCost': 0.0,
            'potentialMonthlySavings': 0.0,
            'optimizationOpportunities': {
                'cleanup': 0,
                'rightsizing': 0,
                'storage_optimization': 0,
                'configuration': 0,
                'security': 0,
                'governance': 0,
                'monitoring': 0
            },
            'priorityBreakdown': {
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'engineBreakdown': {}
        }
        
        for database in databases:
            # Count by status
            if database['status'] == 'available':
                summary['availableDatabases'] += 1
            elif database['status'] == 'stopped':
                summary['stoppedDatabases'] += 1
            
            # Sum costs
            summary['totalMonthlyCost'] += database.get('currentCost', 0)
            
            # Engine breakdown
            engine = database.get('engine', 'unknown')
            summary['engineBreakdown'][engine] = summary['engineBreakdown'].get(engine, 0) + 1
            
            # Analyze opportunities
            for opportunity in database.get('optimizationOpportunities', []):
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
    
    def analyze_backup_costs(self, databases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze backup costs and optimization opportunities.
        
        Args:
            databases: List of analyzed databases
            
        Returns:
            Backup cost analysis summary
        """
        backup_analysis = {
            'totalDatabases': len(databases),
            'backupCostEstimate': 0.0,
            'snapshotOptimizations': [],
            'retentionOptimizations': [],
            'crossRegionBackupCosts': 0.0,
            'recommendations': []
        }
        
        for database in databases:
            db_id = database.get('resourceId', 'unknown')
            allocated_storage = database.get('allocatedStorage', 0)
            multi_az = database.get('multiAZ', False)
            
            # Estimate backup storage costs (approximate)
            # Automated backups are typically 100% of allocated storage for retention period
            backup_storage_cost = allocated_storage * 0.095 * 30 / 1000  # $0.095/GB-month
            
            # Multi-AZ doubles backup storage
            if multi_az:
                backup_storage_cost *= 2
            
            backup_analysis['backupCostEstimate'] += backup_storage_cost
            
            # Check for snapshot optimization opportunities
            if allocated_storage > 500:  # Large databases
                backup_analysis['snapshotOptimizations'].append({
                    'databaseId': db_id,
                    'currentStorage': allocated_storage,
                    'estimatedBackupCost': backup_storage_cost,
                    'recommendation': 'Consider lifecycle policies for automated snapshots',
                    'potentialSavings': backup_storage_cost * 0.3  # 30% savings with lifecycle
                })
            
            # Check retention period optimization
            # Default retention is 7 days, but many databases could use shorter retention
            tags = database.get('tags', {})
            environment = tags.get('Environment', '').lower()
            
            if environment in ['dev', 'test', 'development', 'testing']:
                backup_analysis['retentionOptimizations'].append({
                    'databaseId': db_id,
                    'environment': environment,
                    'currentRetentionCost': backup_storage_cost,
                    'recommendation': 'Reduce backup retention to 1-3 days for non-production',
                    'potentialSavings': backup_storage_cost * 0.6  # 60% savings with shorter retention
                })
        
        # Generate overall recommendations
        if backup_analysis['snapshotOptimizations']:
            backup_analysis['recommendations'].append({
                'type': 'snapshot_lifecycle',
                'priority': 'MEDIUM',
                'description': 'Implement automated snapshot lifecycle policies',
                'affectedDatabases': len(backup_analysis['snapshotOptimizations']),
                'estimatedSavings': sum(opt['potentialSavings'] for opt in backup_analysis['snapshotOptimizations'])
            })
        
        if backup_analysis['retentionOptimizations']:
            backup_analysis['recommendations'].append({
                'type': 'retention_optimization',
                'priority': 'MEDIUM',
                'description': 'Optimize backup retention periods for non-production databases',
                'affectedDatabases': len(backup_analysis['retentionOptimizations']),
                'estimatedSavings': sum(opt['potentialSavings'] for opt in backup_analysis['retentionOptimizations'])
            })
        
        # Cross-region backup cost estimation (if applicable)
        # This would require additional API calls to check for cross-region automated backups
        backup_analysis['crossRegionBackupCosts'] = backup_analysis['backupCostEstimate'] * 0.1  # Estimate 10% for cross-region
        
        return backup_analysis