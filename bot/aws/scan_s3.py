#!/usr/bin/env python3
"""
S3 Bucket Scanner for Advanced FinOps Platform

Discovers and analyzes S3 buckets across regions, collecting:
- Bucket metadata and configuration
- Storage classes, lifecycle policies, and access patterns
- Cost data and optimization opportunities
- Unused buckets and storage optimization recommendations

Requirements: 1.1, 7.3
"""

import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Scanner:
    """Scans S3 buckets for cost optimization opportunities."""
    
    def __init__(self, aws_config, region: str = 'us-east-1'):
        """
        Initialize S3 scanner.
        
        Args:
            aws_config: AWSConfig instance for client management
            region: AWS region to scan (S3 is global but we track region for organization)
        """
        self.aws_config = aws_config
        self.region = region
        self.s3_client = aws_config.get_client('s3')
        self.cloudwatch_client = aws_config.get_client('cloudwatch')
        
        logger.info(f"S3 Scanner initialized for region {region}")
    
    def scan_buckets(self, days_back: int = 14) -> List[Dict[str, Any]]:
        """
        Scan all S3 buckets accessible to the account.
        
        Args:
            days_back: Number of days to look back for metrics
            
        Returns:
            List of bucket data with utilization metrics
        """
        logger.info("Starting S3 bucket scan")
        
        buckets = []
        
        try:
            # Get all S3 buckets
            response = self.s3_client.list_buckets()
            
            for bucket in response['Buckets']:
                bucket_data = self._analyze_bucket(bucket, days_back)
                if bucket_data:
                    buckets.append(bucket_data)
            
            logger.info(f"Scanned {len(buckets)} S3 buckets")
            
        except ClientError as e:
            logger.error(f"Failed to scan S3 buckets: {e}")
            raise
        
        return buckets
    
    def _analyze_bucket(self, bucket: Dict[str, Any], days_back: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single S3 bucket.
        
        Args:
            bucket: S3 bucket data from list_buckets
            days_back: Number of days to analyze metrics
            
        Returns:
            Bucket analysis data or None if analysis fails
        """
        bucket_name = bucket['Name']
        
        try:
            # Basic bucket information
            bucket_data = {
                'resourceId': bucket_name,
                'resourceType': 's3',
                'region': self.region,  # Will be updated with actual region
                'bucketName': bucket_name,
                'creationDate': bucket.get('CreationDate', datetime.utcnow()).isoformat(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Get bucket location
            try:
                location_response = self.s3_client.get_bucket_location(Bucket=bucket_name)
                bucket_region = location_response.get('LocationConstraint')
                if bucket_region is None:
                    bucket_region = 'us-east-1'  # Default for us-east-1
                bucket_data['region'] = bucket_region
            except ClientError as e:
                logger.warning(f"Failed to get location for bucket {bucket_name}: {e}")
                bucket_data['region'] = 'unknown'
            
            # Get bucket versioning
            try:
                versioning_response = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
                bucket_data['versioning'] = versioning_response.get('Status', 'Disabled')
            except ClientError as e:
                logger.warning(f"Failed to get versioning for bucket {bucket_name}: {e}")
                bucket_data['versioning'] = 'unknown'
            
            # Get bucket encryption
            try:
                encryption_response = self.s3_client.get_bucket_encryption(Bucket=bucket_name)
                bucket_data['encryption'] = 'Enabled'
                bucket_data['encryptionRules'] = encryption_response.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    bucket_data['encryption'] = 'Disabled'
                    bucket_data['encryptionRules'] = []
                else:
                    logger.warning(f"Failed to get encryption for bucket {bucket_name}: {e}")
                    bucket_data['encryption'] = 'unknown'
                    bucket_data['encryptionRules'] = []
            
            # Get bucket lifecycle configuration
            try:
                lifecycle_response = self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                bucket_data['lifecycleRules'] = lifecycle_response.get('Rules', [])
                bucket_data['hasLifecyclePolicy'] = len(bucket_data['lifecycleRules']) > 0
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
                    bucket_data['lifecycleRules'] = []
                    bucket_data['hasLifecyclePolicy'] = False
                else:
                    logger.warning(f"Failed to get lifecycle for bucket {bucket_name}: {e}")
                    bucket_data['lifecycleRules'] = []
                    bucket_data['hasLifecyclePolicy'] = False
            
            # Get bucket public access block
            try:
                public_access_response = self.s3_client.get_public_access_block(Bucket=bucket_name)
                bucket_data['publicAccessBlock'] = public_access_response.get('PublicAccessBlockConfiguration', {})
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                    bucket_data['publicAccessBlock'] = {}
                else:
                    logger.warning(f"Failed to get public access block for bucket {bucket_name}: {e}")
                    bucket_data['publicAccessBlock'] = {}
            
            # Get bucket tags
            try:
                tags_response = self.s3_client.get_bucket_tagging(Bucket=bucket_name)
                tags = {}
                for tag in tags_response.get('TagSet', []):
                    tags[tag['Key']] = tag['Value']
                bucket_data['tags'] = tags
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchTagSet':
                    bucket_data['tags'] = {}
                else:
                    logger.warning(f"Failed to get tags for bucket {bucket_name}: {e}")
                    bucket_data['tags'] = {}
            
            # Get bucket size and object count
            storage_metrics = self._get_bucket_storage_metrics(bucket_name, days_back)
            bucket_data['storageMetrics'] = storage_metrics
            
            # Get access metrics
            access_metrics = self._get_bucket_access_metrics(bucket_name, days_back)
            bucket_data['accessMetrics'] = access_metrics
            
            # Analyze storage classes
            storage_class_analysis = self._analyze_storage_classes(bucket_name)
            bucket_data['storageClassAnalysis'] = storage_class_analysis
            
            # Calculate optimization opportunities
            opportunities = self._identify_optimization_opportunities(bucket_data, storage_metrics, access_metrics)
            bucket_data['optimizationOpportunities'] = opportunities
            
            # Estimate current cost
            bucket_data['currentCost'] = self._estimate_bucket_cost(
                storage_metrics,
                access_metrics,
                bucket_data['region']
            )
            
            return bucket_data
            
        except Exception as e:
            logger.error(f"Failed to analyze bucket {bucket_name}: {e}")
            return None
    
    def _get_bucket_storage_metrics(self, bucket_name: str, days_back: int) -> Dict[str, Any]:
        """
        Get storage metrics for an S3 bucket.
        
        Args:
            bucket_name: S3 bucket name
            days_back: Number of days to retrieve metrics
            
        Returns:
            Dictionary containing storage metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        metrics = {
            'bucketSizeBytes': [],
            'numberOfObjects': [],
            'period': f"{days_back} days",
            'dataPoints': 0
        }
        
        try:
            # Bucket Size in Bytes
            size_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='BucketSizeBytes',
                Dimensions=[
                    {
                        'Name': 'BucketName',
                        'Value': bucket_name
                    },
                    {
                        'Name': 'StorageType',
                        'Value': 'StandardStorage'
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # Daily periods for S3 metrics
                Statistics=['Average']
            )
            
            size_datapoints = sorted(size_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['bucketSizeBytes'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average']
                }
                for dp in size_datapoints
            ]
            
            # Number of Objects
            objects_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='NumberOfObjects',
                Dimensions=[
                    {
                        'Name': 'BucketName',
                        'Value': bucket_name
                    },
                    {
                        'Name': 'StorageType',
                        'Value': 'AllStorageTypes'
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
            )
            
            objects_datapoints = sorted(objects_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['numberOfObjects'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'average': dp['Average']
                }
                for dp in objects_datapoints
            ]
            
            # Calculate summary statistics
            if metrics['bucketSizeBytes']:
                latest_size = metrics['bucketSizeBytes'][-1]['average']
                metrics['currentSizeBytes'] = latest_size
                metrics['currentSizeGB'] = latest_size / (1024 ** 3)
                metrics['dataPoints'] = len(metrics['bucketSizeBytes'])
            else:
                metrics['currentSizeBytes'] = 0
                metrics['currentSizeGB'] = 0
                metrics['dataPoints'] = 0
            
            if metrics['numberOfObjects']:
                metrics['currentObjectCount'] = int(metrics['numberOfObjects'][-1]['average'])
            else:
                metrics['currentObjectCount'] = 0
            
            logger.debug(f"Retrieved {metrics['dataPoints']} storage metric data points for bucket {bucket_name}")
            
        except ClientError as e:
            logger.warning(f"Failed to retrieve storage metrics for bucket {bucket_name}: {e}")
            # Return empty metrics on failure
            metrics.update({
                'currentSizeBytes': 0,
                'currentSizeGB': 0,
                'currentObjectCount': 0
            })
        
        return metrics
    
    def _get_bucket_access_metrics(self, bucket_name: str, days_back: int) -> Dict[str, Any]:
        """
        Get access metrics for an S3 bucket.
        
        Args:
            bucket_name: S3 bucket name
            days_back: Number of days to retrieve metrics
            
        Returns:
            Dictionary containing access metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        metrics = {
            'allRequests': [],
            'getRequests': [],
            'putRequests': [],
            'deleteRequests': [],
            'period': f"{days_back} days",
            'dataPoints': 0
        }
        
        try:
            # All Requests
            all_requests_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='AllRequests',
                Dimensions=[
                    {
                        'Name': 'BucketName',
                        'Value': bucket_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # Daily periods
                Statistics=['Sum']
            )
            
            all_requests_datapoints = sorted(all_requests_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['allRequests'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in all_requests_datapoints
            ]
            
            # GET Requests
            get_requests_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='GetRequests',
                Dimensions=[
                    {
                        'Name': 'BucketName',
                        'Value': bucket_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Sum']
            )
            
            get_requests_datapoints = sorted(get_requests_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['getRequests'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in get_requests_datapoints
            ]
            
            # PUT Requests
            put_requests_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='PutRequests',
                Dimensions=[
                    {
                        'Name': 'BucketName',
                        'Value': bucket_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Sum']
            )
            
            put_requests_datapoints = sorted(put_requests_response['Datapoints'], key=lambda x: x['Timestamp'])
            metrics['putRequests'] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'sum': dp['Sum']
                }
                for dp in put_requests_datapoints
            ]
            
            # Calculate summary statistics
            if metrics['allRequests']:
                metrics['totalRequests'] = sum(dp['sum'] for dp in metrics['allRequests'])
                metrics['avgRequestsPerDay'] = metrics['totalRequests'] / len(metrics['allRequests'])
                metrics['dataPoints'] = len(metrics['allRequests'])
            else:
                metrics['totalRequests'] = 0
                metrics['avgRequestsPerDay'] = 0
                metrics['dataPoints'] = 0
            
            if metrics['getRequests']:
                metrics['totalGetRequests'] = sum(dp['sum'] for dp in metrics['getRequests'])
            else:
                metrics['totalGetRequests'] = 0
            
            if metrics['putRequests']:
                metrics['totalPutRequests'] = sum(dp['sum'] for dp in metrics['putRequests'])
            else:
                metrics['totalPutRequests'] = 0
            
            logger.debug(f"Retrieved {metrics['dataPoints']} access metric data points for bucket {bucket_name}")
            
        except ClientError as e:
            logger.warning(f"Failed to retrieve access metrics for bucket {bucket_name}: {e}")
            # Return empty metrics on failure
            metrics.update({
                'totalRequests': 0,
                'avgRequestsPerDay': 0,
                'totalGetRequests': 0,
                'totalPutRequests': 0
            })
        
        return metrics
    
    def _analyze_storage_classes(self, bucket_name: str) -> Dict[str, Any]:
        """
        Analyze storage classes used in the bucket.
        
        Args:
            bucket_name: S3 bucket name
            
        Returns:
            Dictionary containing storage class analysis
        """
        analysis = {
            'storageClasses': {},
            'totalObjects': 0,
            'hasIntelligentTiering': False,
            'hasGlacierObjects': False
        }
        
        try:
            # Sample objects to analyze storage classes (limit to avoid performance issues)
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=bucket_name,
                PaginationConfig={'MaxItems': 1000}  # Limit for performance
            )
            
            for page in page_iterator:
                for obj in page.get('Contents', []):
                    storage_class = obj.get('StorageClass', 'STANDARD')
                    analysis['storageClasses'][storage_class] = analysis['storageClasses'].get(storage_class, 0) + 1
                    analysis['totalObjects'] += 1
                    
                    if storage_class == 'INTELLIGENT_TIERING':
                        analysis['hasIntelligentTiering'] = True
                    elif storage_class in ['GLACIER', 'DEEP_ARCHIVE']:
                        analysis['hasGlacierObjects'] = True
            
        except ClientError as e:
            logger.warning(f"Failed to analyze storage classes for bucket {bucket_name}: {e}")
        
        return analysis
    
    def _identify_optimization_opportunities(self, bucket_data: Dict[str, Any], 
                                           storage_metrics: Dict[str, Any], 
                                           access_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities for an S3 bucket.
        
        Args:
            bucket_data: Bucket metadata
            storage_metrics: Storage utilization metrics
            access_metrics: Access pattern metrics
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        current_size_gb = storage_metrics.get('currentSizeGB', 0)
        object_count = storage_metrics.get('currentObjectCount', 0)
        total_requests = access_metrics.get('totalRequests', 0)
        avg_requests_per_day = access_metrics.get('avgRequestsPerDay', 0)
        data_points = storage_metrics.get('dataPoints', 0)
        
        # Only analyze if we have sufficient data
        if data_points >= 7:  # At least 7 days of data
            
            # Empty bucket
            if object_count == 0:
                opportunities.append({
                    'type': 'cleanup',
                    'reason': 'Bucket is empty',
                    'priority': 'MEDIUM',
                    'estimatedSavings': bucket_data.get('currentCost', 0),
                    'confidence': 'HIGH',
                    'action': 'consider_deletion'
                })
            
            # Unused bucket (no access)
            elif total_requests == 0 and object_count > 0:
                opportunities.append({
                    'type': 'cleanup',
                    'reason': f'Bucket has {object_count} objects but no access requests',
                    'priority': 'HIGH',
                    'estimatedSavings': bucket_data.get('currentCost', 0) * 0.8,  # 80% savings
                    'confidence': 'HIGH',
                    'action': 'review_necessity'
                })
            
            # Low access bucket
            elif avg_requests_per_day < 1 and object_count > 0:
                opportunities.append({
                    'type': 'storage_optimization',
                    'reason': f'Low access pattern: {avg_requests_per_day:.1f} requests/day',
                    'priority': 'MEDIUM',
                    'estimatedSavings': bucket_data.get('currentCost', 0) * 0.4,  # 40% savings
                    'confidence': 'MEDIUM',
                    'action': 'consider_ia_or_glacier'
                })
        
        # Lifecycle policy optimization
        if not bucket_data.get('hasLifecyclePolicy', False) and current_size_gb > 1:  # > 1GB
            opportunities.append({
                'type': 'storage_optimization',
                'reason': f'No lifecycle policy for {current_size_gb:.1f}GB bucket',
                'priority': 'MEDIUM',
                'estimatedSavings': bucket_data.get('currentCost', 0) * 0.3,  # 30% savings
                'confidence': 'MEDIUM',
                'action': 'implement_lifecycle_policy'
            })
        
        # Versioning optimization
        if bucket_data.get('versioning') == 'Enabled' and not bucket_data.get('hasLifecyclePolicy', False):
            opportunities.append({
                'type': 'storage_optimization',
                'reason': 'Versioning enabled without lifecycle policy for old versions',
                'priority': 'MEDIUM',
                'estimatedSavings': bucket_data.get('currentCost', 0) * 0.2,  # 20% savings
                'confidence': 'HIGH',
                'action': 'add_version_lifecycle_policy'
            })
        
        # Storage class optimization
        storage_class_analysis = bucket_data.get('storageClassAnalysis', {})
        storage_classes = storage_class_analysis.get('storageClasses', {})
        
        if 'STANDARD' in storage_classes and not storage_class_analysis.get('hasIntelligentTiering', False):
            standard_objects = storage_classes['STANDARD']
            if standard_objects > 100 and avg_requests_per_day < 10:  # Many objects, low access
                opportunities.append({
                    'type': 'storage_optimization',
                    'reason': f'{standard_objects} objects in STANDARD class with low access',
                    'priority': 'MEDIUM',
                    'estimatedSavings': bucket_data.get('currentCost', 0) * 0.25,  # 25% savings
                    'confidence': 'MEDIUM',
                    'action': 'enable_intelligent_tiering'
                })
        
        # Security optimizations
        if bucket_data.get('encryption') == 'Disabled':
            opportunities.append({
                'type': 'security',
                'reason': 'Bucket encryption is disabled',
                'priority': 'HIGH',
                'estimatedSavings': 0,
                'confidence': 'HIGH',
                'action': 'enable_encryption'
            })
        
        # Public access optimization
        public_access_block = bucket_data.get('publicAccessBlock', {})
        if not all([
            public_access_block.get('BlockPublicAcls', False),
            public_access_block.get('IgnorePublicAcls', False),
            public_access_block.get('BlockPublicPolicy', False),
            public_access_block.get('RestrictPublicBuckets', False)
        ]):
            opportunities.append({
                'type': 'security',
                'reason': 'Public access block not fully configured',
                'priority': 'HIGH',
                'estimatedSavings': 0,
                'confidence': 'HIGH',
                'action': 'configure_public_access_block'
            })
        
        # Check for missing tags (cost allocation)
        required_tags = ['Environment', 'Project', 'Owner']
        missing_tags = [tag for tag in required_tags if tag not in bucket_data.get('tags', {})]
        
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
    
    def _estimate_bucket_cost(self, storage_metrics: Dict[str, Any], 
                             access_metrics: Dict[str, Any], region: str) -> float:
        """
        Estimate monthly cost for an S3 bucket.
        
        Args:
            storage_metrics: Storage metrics
            access_metrics: Access metrics
            region: AWS region
            
        Returns:
            Estimated monthly cost in USD
        """
        # Simplified cost estimation (would use AWS Price List API in production)
        # These are approximate costs for us-east-1 region
        
        current_size_gb = storage_metrics.get('currentSizeGB', 0)
        total_requests = access_metrics.get('totalRequests', 0)
        get_requests = access_metrics.get('totalGetRequests', 0)
        put_requests = access_metrics.get('totalPutRequests', 0)
        
        if current_size_gb == 0:
            return 0.0
        
        # Storage cost (STANDARD class)
        # First 50 TB: $0.023 per GB
        # Next 450 TB: $0.022 per GB
        # Over 500 TB: $0.021 per GB
        if current_size_gb <= 50 * 1024:  # 50 TB
            storage_cost = current_size_gb * 0.023
        elif current_size_gb <= 500 * 1024:  # 500 TB
            storage_cost = (50 * 1024 * 0.023) + ((current_size_gb - 50 * 1024) * 0.022)
        else:
            storage_cost = (50 * 1024 * 0.023) + (450 * 1024 * 0.022) + ((current_size_gb - 500 * 1024) * 0.021)
        
        # Request costs (monthly estimate)
        # GET requests: $0.0004 per 1,000 requests
        # PUT requests: $0.005 per 1,000 requests
        monthly_get_requests = get_requests * (30 / 14)  # Scale to monthly
        monthly_put_requests = put_requests * (30 / 14)
        
        get_request_cost = (monthly_get_requests / 1000) * 0.0004
        put_request_cost = (monthly_put_requests / 1000) * 0.005
        
        total_cost = storage_cost + get_request_cost + put_request_cost
        
        # Regional pricing adjustments (simplified)
        regional_multipliers = {
            'us-east-1': 1.0,
            'us-west-1': 1.05,
            'us-west-2': 1.02,
            'eu-west-1': 1.08,
            'ap-southeast-1': 1.12
        }
        
        multiplier = regional_multipliers.get(region, 1.1)  # Default 10% higher
        
        return total_cost * multiplier
    
    def get_bucket_count_by_region(self) -> Dict[str, int]:
        """
        Get count of buckets by region.
        
        Returns:
            Dictionary with region counts
        """
        region_counts = {}
        
        try:
            response = self.s3_client.list_buckets()
            
            for bucket in response['Buckets']:
                try:
                    location_response = self.s3_client.get_bucket_location(Bucket=bucket['Name'])
                    region = location_response.get('LocationConstraint')
                    if region is None:
                        region = 'us-east-1'
                    region_counts[region] = region_counts.get(region, 0) + 1
                except ClientError:
                    region_counts['unknown'] = region_counts.get('unknown', 0) + 1
            
        except ClientError as e:
            logger.error(f"Failed to get bucket counts: {e}")
        
        return region_counts
    
    def get_optimization_summary(self, buckets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate optimization summary for scanned buckets.
        
        Args:
            buckets: List of analyzed buckets
            
        Returns:
            Optimization summary
        """
        summary = {
            'totalBuckets': len(buckets),
            'emptyBuckets': 0,
            'unusedBuckets': 0,
            'totalStorageGB': 0.0,
            'totalMonthlyCost': 0.0,
            'potentialMonthlySavings': 0.0,
            'optimizationOpportunities': {
                'cleanup': 0,
                'storage_optimization': 0,
                'security': 0,
                'governance': 0
            },
            'priorityBreakdown': {
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'regionBreakdown': {}
        }
        
        for bucket in buckets:
            # Count by usage
            object_count = bucket.get('storageMetrics', {}).get('currentObjectCount', 0)
            total_requests = bucket.get('accessMetrics', {}).get('totalRequests', 0)
            
            if object_count == 0:
                summary['emptyBuckets'] += 1
            elif total_requests == 0:
                summary['unusedBuckets'] += 1
            
            # Sum storage and costs
            storage_gb = bucket.get('storageMetrics', {}).get('currentSizeGB', 0)
            summary['totalStorageGB'] += storage_gb
            summary['totalMonthlyCost'] += bucket.get('currentCost', 0)
            
            # Region breakdown
            region = bucket.get('region', 'unknown')
            summary['regionBreakdown'][region] = summary['regionBreakdown'].get(region, 0) + 1
            
            # Analyze opportunities
            for opportunity in bucket.get('optimizationOpportunities', []):
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