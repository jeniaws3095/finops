#!/usr/bin/env python3
"""
AWS Configuration and Client Management

Handles AWS credential management, region configuration, and client initialization
with comprehensive error handling, retry logic, and rate limiting for AWS Cost Management APIs.

Enhanced for Advanced FinOps Platform with:
- IAM role support and credential handling
- Multi-region configuration and aggregation (Requirement 1.5)
- AWS Cost Explorer API integration (Requirement 10.1)
- AWS Billing and Cost Management APIs (Requirement 10.2)
- CloudWatch metrics collection (Requirement 10.3)
- Advanced rate limiting and exponential backoff
- Comprehensive error handling for AWS API calls

Supports Requirements 1.5, 10.1, 10.2, 10.3
"""

import boto3
import logging
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from botocore.exceptions import (
    ClientError, 
    NoCredentialsError, 
    PartialCredentialsError,
    BotoCoreError,
    EndpointConnectionError,
    TokenRetrievalError,
    ProfileNotFound
)
from botocore.config import Config
from typing import Dict, Any, Optional, List, Union, Tuple

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Advanced rate limiter with exponential backoff for AWS API throttling.
    
    Implements per-service rate limiting with adaptive backoff based on
    AWS service-specific throttling patterns and error responses.
    """
    
    def __init__(self):
        self._service_limits = defaultdict(lambda: {'calls': 0, 'window_start': time.time()})
        self._backoff_state = defaultdict(lambda: {'consecutive_throttles': 0, 'last_throttle': 0})
        self._lock = threading.Lock()
        
        # Service-specific rate limits (calls per second)
        self._default_limits = {
            'ce': 20,  # Cost Explorer - conservative limit
            'budgets': 10,  # AWS Budgets - lower limit
            'pricing': 10,  # Price List API - conservative
            'cloudwatch': 100,  # CloudWatch - higher limit
            'ec2': 100,  # EC2 - standard limit
            'rds': 50,  # RDS - moderate limit
            'lambda': 100,  # Lambda - standard limit
            's3': 100,  # S3 - standard limit
            'sts': 50,  # STS - moderate limit
        }
    
    def wait_if_needed(self, service_name: str) -> None:
        """
        Wait if rate limit would be exceeded for the service.
        
        Args:
            service_name: AWS service name
        """
        with self._lock:
            now = time.time()
            service_state = self._service_limits[service_name]
            limit = self._default_limits.get(service_name, 50)
            
            # Reset window if needed (1-second windows)
            if now - service_state['window_start'] >= 1.0:
                service_state['calls'] = 0
                service_state['window_start'] = now
            
            # Check if we need to wait
            if service_state['calls'] >= limit:
                wait_time = 1.0 - (now - service_state['window_start'])
                if wait_time > 0:
                    logger.debug(f"Rate limiting {service_name}: waiting {wait_time:.2f}s")
                    time.sleep(wait_time)
                    # Reset after waiting
                    service_state['calls'] = 0
                    service_state['window_start'] = time.time()
            
            service_state['calls'] += 1
    
    def handle_throttle(self, service_name: str) -> float:
        """
        Handle throttling response and return wait time.
        
        Args:
            service_name: AWS service name
            
        Returns:
            Wait time in seconds
        """
        with self._lock:
            backoff_state = self._backoff_state[service_name]
            backoff_state['consecutive_throttles'] += 1
            backoff_state['last_throttle'] = time.time()
            
            # Exponential backoff with jitter
            base_wait = min(2 ** backoff_state['consecutive_throttles'], 60)  # Cap at 60s
            jitter = base_wait * 0.1 * (time.time() % 1)  # Add jitter
            wait_time = base_wait + jitter
            
            logger.warning(f"Throttling {service_name}: consecutive={backoff_state['consecutive_throttles']}, waiting {wait_time:.1f}s")
            return wait_time
    
    def reset_throttle(self, service_name: str) -> None:
        """Reset throttle state after successful call."""
        with self._lock:
            if service_name in self._backoff_state:
                self._backoff_state[service_name]['consecutive_throttles'] = 0


class AWSConfig:
    """
    Enhanced AWS configuration and client management with comprehensive error handling.
    
    Provides centralized AWS client management with:
    - IAM role support and credential validation
    - Multi-region configuration and aggregation (Requirement 1.5)
    - Client caching and connection pooling for performance
    - Advanced rate limiting and exponential backoff for API throttling
    - Specialized support for AWS Cost Management APIs (Requirements 10.1, 10.2, 10.3)
    - Comprehensive error handling and retry logic
    """
    
    # AWS Cost Management services that require special handling
    COST_MANAGEMENT_SERVICES = {
        'ce',  # Cost Explorer
        'budgets',  # AWS Budgets
        'pricing',  # Price List API
        'cur',  # Cost and Usage Reports
        'billing',  # Billing Conductor
        'cloudwatch'  # CloudWatch (for resource utilization metrics)
    }
    
    # Services that must use us-east-1 region
    US_EAST_1_ONLY_SERVICES = {
        'ce',  # Cost Explorer
        'cur',  # Cost and Usage Reports
        'pricing',  # Price List API (global pricing data)
    }
    
    def __init__(self, 
                 region: str = 'us-east-1', 
                 max_retries: int = 3,
                 profile_name: Optional[str] = None,
                 role_arn: Optional[str] = None,
                 role_session_name: Optional[str] = None,
                 regions: Optional[List[str]] = None):
        """
        Initialize enhanced AWS configuration with IAM role support.
        
        Args:
            region: Primary AWS region to use (default: us-east-1)
            max_retries: Maximum number of retries for failed API calls
            profile_name: AWS CLI profile name to use (optional)
            role_arn: IAM role ARN to assume (optional)
            role_session_name: Session name for role assumption (optional)
            regions: List of regions for multi-region operations (Requirement 1.5)
        """
        self.region = region
        self.max_retries = max_retries
        self.profile_name = profile_name
        self.role_arn = role_arn
        self.role_session_name = role_session_name or f"advanced-finops-{int(time.time())}"
        
        # Multi-region support for Requirement 1.5
        self.regions = regions or [region]
        if region not in self.regions:
            self.regions.append(region)
        
        self._clients = {}
        self._session = None
        self._assumed_role_credentials = None
        self._credentials_expiry = None
        self._rate_limiter = RateLimiter()
        
        # Enhanced boto3 configuration with connection pooling
        self._base_config = {
            'retries': {
                'max_attempts': max_retries,
                'mode': 'adaptive'
            },
            'max_pool_connections': 100,  # Increased for multi-region operations
            'connect_timeout': 60,
            'read_timeout': 60
        }
        
        self._validate_credentials()
    
    def _get_session(self) -> boto3.Session:
        """Get or create boto3 session with profile and role support."""
        if self._session is None:
            try:
                # Create session with profile if specified
                if self.profile_name:
                    logger.info(f"Using AWS profile: {self.profile_name}")
                    self._session = boto3.Session(profile_name=self.profile_name)
                else:
                    self._session = boto3.Session()
                    
                # Assume role if specified
                if self.role_arn:
                    self._assume_role()
                    
            except ProfileNotFound as e:
                error_msg = f"AWS profile '{self.profile_name}' not found. Available profiles: {boto3.Session().available_profiles}"
                logger.error(error_msg)
                raise Exception(error_msg) from e
                
        return self._session
    
    def _assume_role(self) -> None:
        """
        Assume IAM role and cache credentials.
        
        Raises:
            Exception: If role assumption fails
        """
        try:
            # Check if credentials are still valid
            if (self._assumed_role_credentials and 
                self._credentials_expiry and 
                datetime.now() < self._credentials_expiry - timedelta(minutes=5)):
                return
            
            logger.info(f"Assuming IAM role: {self.role_arn}")
            
            # Use base session to assume role
            base_session = boto3.Session(profile_name=self.profile_name) if self.profile_name else boto3.Session()
            sts_client = base_session.client('sts')
            
            response = sts_client.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName=self.role_session_name,
                DurationSeconds=3600  # 1 hour
            )
            
            credentials = response['Credentials']
            self._assumed_role_credentials = {
                'aws_access_key_id': credentials['AccessKeyId'],
                'aws_secret_access_key': credentials['SecretAccessKey'],
                'aws_session_token': credentials['SessionToken']
            }
            self._credentials_expiry = credentials['Expiration']
            
            # Create new session with assumed role credentials
            self._session = boto3.Session(**self._assumed_role_credentials)
            
            # Clear client cache to use new credentials
            self._clients.clear()
            
            logger.info(f"Successfully assumed role. Credentials expire at: {self._credentials_expiry}")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = f"Failed to assume role {self.role_arn} [{error_code}]: {e}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def _validate_credentials(self) -> None:
        """
        Enhanced credential validation with IAM role support.
        
        Raises:
            Exception: If credentials are not configured or invalid
        """
        try:
            session = self._get_session()
            sts_client = session.client('sts', config=Config(**self._base_config))
            identity = sts_client.get_caller_identity()
            
            account_id = identity.get('Account')
            user_arn = identity.get('Arn', 'Unknown')
            user_id = identity.get('UserId', 'Unknown')
            
            logger.info(f"AWS credentials validated for account: {account_id}")
            logger.info(f"Using identity: {user_arn}")
            logger.info(f"User ID: {user_id}")
            logger.info(f"Primary region: {self.region}")
            logger.info(f"Multi-region support: {len(self.regions)} regions - {self.regions}")
            
            if self.role_arn:
                logger.info(f"Using assumed role: {self.role_arn}")
            if self.profile_name:
                logger.info(f"Using AWS profile: {self.profile_name}")
            
        except (NoCredentialsError, PartialCredentialsError) as e:
            error_msg = (
                "AWS credentials not configured properly. "
                "Please run 'aws configure' to set up your credentials or specify a profile."
            )
            logger.error(error_msg)
            raise Exception(error_msg) from e
            
        except TokenRetrievalError as e:
            error_msg = f"Failed to retrieve AWS credentials token: {e}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
            
        except EndpointConnectionError as e:
            error_msg = f"Cannot connect to AWS endpoints. Check network connectivity: {e}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = f"AWS credential validation failed [{error_code}]: {e}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def get_client(self, service_name: str, region: Optional[str] = None) -> Any:
        """
        Get or create AWS service client with enhanced caching and error handling.
        
        Args:
            service_name: AWS service name (e.g., 'ec2', 'rds', 'lambda', 'ce', 'budgets')
            region: Override region for this client (optional)
            
        Returns:
            Boto3 client for the specified service
            
        Raises:
            Exception: If client creation fails
        """
        # Refresh assumed role credentials if needed
        if self.role_arn:
            self._assume_role()
        
        # Determine region to use
        client_region = region or self.region
        
        # Force us-east-1 for services that require it
        if service_name in self.US_EAST_1_ONLY_SERVICES:
            client_region = 'us-east-1'
            logger.debug(f"Using us-east-1 for {service_name} service (required)")
        
        cache_key = f"{service_name}:{client_region}"
        
        if cache_key not in self._clients:
            try:
                session = self._get_session()
                
                # Create enhanced config for this client
                config_params = self._base_config.copy()
                config_params['region_name'] = client_region
                
                # Service-specific configuration
                if service_name in self.COST_MANAGEMENT_SERVICES:
                    # More conservative settings for cost management APIs
                    config_params['retries']['max_attempts'] = min(self.max_retries + 2, 5)
                    config_params['connect_timeout'] = 120
                    config_params['read_timeout'] = 120
                
                config = Config(**config_params)
                
                self._clients[cache_key] = session.client(service_name, config=config)
                logger.debug(f"Created {service_name} client for region {client_region}")
                
            except Exception as e:
                error_msg = f"Failed to create {service_name} client: {e}"
                logger.error(error_msg)
                raise Exception(error_msg) from e
        
        return self._clients[cache_key]
    
    def get_resource(self, service_name: str, region: Optional[str] = None) -> Any:
        """
        Get AWS service resource with enhanced error handling.
        
        Args:
            service_name: AWS service name (e.g., 'ec2', 's3')
            region: Override region for this resource (optional)
            
        Returns:
            Boto3 resource for the specified service
            
        Raises:
            Exception: If resource creation fails
        """
        try:
            # Refresh assumed role credentials if needed
            if self.role_arn:
                self._assume_role()
                
            session = self._get_session()
            resource_region = region or self.region
            
            config_params = self._base_config.copy()
            config_params['region_name'] = resource_region
            config = Config(**config_params)
            
            return session.resource(service_name, config=config)
            
        except Exception as e:
            error_msg = f"Failed to create {service_name} resource: {e}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def get_multi_region_clients(self, service_name: str, regions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get clients for multiple regions (Requirement 1.5).
        
        Args:
            service_name: AWS service name
            regions: List of regions (uses self.regions if not provided)
            
        Returns:
            Dictionary mapping region names to boto3 clients
        """
        target_regions = regions or self.regions
        clients = {}
        
        for region in target_regions:
            try:
                clients[region] = self.get_client(service_name, region)
                logger.debug(f"Created {service_name} client for region {region}")
            except Exception as e:
                logger.warning(f"Failed to create {service_name} client for region {region}: {e}")
                # Continue with other regions
                continue
        
        logger.info(f"Created {service_name} clients for {len(clients)} regions: {list(clients.keys())}")
        return clients
    
    def get_account_id(self) -> str:
        """
        Get current AWS account ID.
        
        Returns:
            AWS account ID string
            
        Raises:
            Exception: If unable to retrieve account ID
        """
        try:
            sts_client = self.get_client('sts')
            return sts_client.get_caller_identity()['Account']
        except Exception as e:
            error_msg = f"Failed to get account ID: {e}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def list_regions(self, service_name: str = 'ec2') -> List[str]:
        """
        List available AWS regions for a service.
        
        Args:
            service_name: AWS service to check regions for
            
        Returns:
            List of region names
        """
        try:
            client = self.get_client(service_name)
            response = client.describe_regions()
            regions = [region['RegionName'] for region in response['Regions']]
            logger.debug(f"Found {len(regions)} regions for {service_name}")
            return regions
            
        except Exception as e:
            logger.warning(f"Failed to list regions for {service_name}: {e}")
            return [self.region]  # Fallback to current region
    
    def get_all_enabled_regions(self) -> List[str]:
        """
        Get all enabled AWS regions for the account.
        
        Returns:
            List of enabled region names
        """
        try:
            ec2_client = self.get_client('ec2')
            response = ec2_client.describe_regions(
                Filters=[{'Name': 'opt-in-status', 'Values': ['opt-in-not-required', 'opted-in']}]
            )
            regions = [region['RegionName'] for region in response['Regions']]
            logger.info(f"Found {len(regions)} enabled regions")
            return sorted(regions)
        except Exception as e:
            logger.warning(f"Failed to get enabled regions: {e}")
            return self.regions
    
    # Enhanced AWS Cost Management API methods (Requirements 10.1, 10.2, 10.3)
    
    def get_cost_explorer_client(self) -> Any:
        """
        Get Cost Explorer client with enhanced configuration (Requirement 10.1).
        
        Returns:
            Cost Explorer boto3 client
            
        Note:
            Cost Explorer API only works in us-east-1 region
        """
        return self.get_client('ce', region='us-east-1')
    
    def get_cost_anomaly_client(self) -> Any:
        """
        Get Cost Anomaly Detection client (Requirement 10.1).
        
        Returns:
            Cost Anomaly Detection boto3 client (uses Cost Explorer service)
            
        Note:
            Cost Anomaly Detection uses the same 'ce' service as Cost Explorer
        """
        return self.get_client('ce', region='us-east-1')
    
    def get_budgets_client(self) -> Any:
        """
        Get AWS Budgets client with enhanced configuration (Requirement 10.2).
        
        Returns:
            AWS Budgets boto3 client
        """
        return self.get_client('budgets')
    
    def get_billing_client(self) -> Any:
        """
        Get AWS Billing Conductor client (Requirement 10.2).
        
        Returns:
            AWS Billing Conductor boto3 client
        """
        return self.get_client('billingconductor', region='us-east-1')
    
    def get_cur_client(self) -> Any:
        """
        Get Cost and Usage Reports client (Requirement 10.2).
        
        Returns:
            AWS Cost and Usage Reports boto3 client
        """
        return self.get_client('cur', region='us-east-1')
    
    def get_pricing_client(self) -> Any:
        """
        Get AWS Price List API client (Requirement 10.2).
        
        Returns:
            AWS Pricing boto3 client
            
        Note:
            Price List API uses us-east-1 for global pricing data
        """
        return self.get_client('pricing', region='us-east-1')
    
    def get_cloudwatch_client(self, region: Optional[str] = None) -> Any:
        """
        Get CloudWatch client for metrics collection (Requirement 10.3).
        
        Args:
            region: AWS region for CloudWatch client (optional)
            
        Returns:
            CloudWatch boto3 client
        """
        return self.get_client('cloudwatch', region=region)
    
    def get_cloudwatch_logs_client(self, region: Optional[str] = None) -> Any:
        """
        Get CloudWatch Logs client for log analysis (Requirement 10.3).
        
        Args:
            region: AWS region for CloudWatch Logs client (optional)
            
        Returns:
            CloudWatch Logs boto3 client
        """
        return self.get_client('logs', region=region)
    
    def get_multi_region_cloudwatch_clients(self, regions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get CloudWatch clients for multiple regions (Requirements 1.5, 10.3).
        
        Args:
            regions: List of regions (uses self.regions if not provided)
            
        Returns:
            Dictionary mapping region names to CloudWatch clients
        """
        return self.get_multi_region_clients('cloudwatch', regions)
    
    def execute_with_retry(self, operation, service_name: str = 'unknown', *args, **kwargs) -> Any:
        """
        Execute AWS API operation with advanced retry logic and rate limiting.
        
        Args:
            operation: AWS API operation to execute
            service_name: AWS service name for rate limiting
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Operation result
            
        Raises:
            Exception: If operation fails after all retries
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Apply rate limiting before making the call
                self._rate_limiter.wait_if_needed(service_name)
                
                # Execute the operation
                result = operation(*args, **kwargs)
                
                # Reset throttle state on success
                self._rate_limiter.reset_throttle(service_name)
                
                return result
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', str(e))
                
                # Don't retry certain errors
                non_retryable_errors = {
                    'AccessDenied', 'InvalidUserID.NotFound', 'ValidationException',
                    'InvalidParameterValue', 'InvalidParameterCombination', 'MissingParameter',
                    'UnauthorizedOperation', 'Forbidden', 'ResourceNotFound'
                }
                
                if error_code in non_retryable_errors:
                    logger.error(f"Non-retryable error [{error_code}]: {error_message}")
                    raise Exception(f"AWS API error [{error_code}]: {error_message}") from e
                
                # Handle throttling with exponential backoff
                throttling_errors = {
                    'Throttling', 'ThrottlingException', 'RequestLimitExceeded', 
                    'TooManyRequestsException', 'ProvisionedThroughputExceededException',
                    'RequestThrottledException', 'SlowDown'
                }
                
                if error_code in throttling_errors:
                    if attempt < self.max_retries:
                        wait_time = self._rate_limiter.handle_throttle(service_name)
                        logger.warning(f"Throttling detected for {service_name}, retrying in {wait_time:.1f}s (attempt {attempt + 1})")
                        time.sleep(wait_time)
                        last_exception = e
                        continue
                    else:
                        logger.error(f"Throttling persisted after {self.max_retries} retries for {service_name}")
                        raise Exception(f"AWS API throttling [{error_code}]: {error_message}") from e
                
                # Handle server errors with exponential backoff
                server_errors = {
                    'InternalError', 'InternalFailure', 'ServiceUnavailable', 
                    'InternalServerError', 'RequestTimeout'
                }
                
                if error_code in server_errors or error_code.startswith('5'):
                    if attempt < self.max_retries:
                        wait_time = min((2 ** attempt) + (attempt * 0.1), 30)  # Cap at 30s
                        logger.warning(f"Server error for {service_name}, retrying in {wait_time:.1f}s (attempt {attempt + 1}): {error_code}")
                        time.sleep(wait_time)
                        last_exception = e
                        continue
                    else:
                        logger.error(f"Server error persisted after {self.max_retries} retries for {service_name}")
                        raise Exception(f"AWS server error [{error_code}]: {error_message}") from e
                
                # Don't retry other client errors
                logger.error(f"Client error for {service_name} [{error_code}]: {error_message}")
                raise Exception(f"AWS API error [{error_code}]: {error_message}") from e
                
            except (EndpointConnectionError, BotoCoreError) as e:
                if attempt < self.max_retries:
                    wait_time = min((2 ** attempt), 30)  # Cap at 30s
                    logger.warning(f"Connection error for {service_name}, retrying in {wait_time:.1f}s (attempt {attempt + 1}): {e}")
                    time.sleep(wait_time)
                    last_exception = e
                    continue
                else:
                    logger.error(f"Connection failed for {service_name} after {self.max_retries} retries: {e}")
                    raise Exception(f"AWS connection failed for {service_name}: {e}") from e
            
            except Exception as e:
                # Handle unexpected errors
                if attempt < self.max_retries:
                    wait_time = min((2 ** attempt), 30)
                    logger.warning(f"Unexpected error for {service_name}, retrying in {wait_time:.1f}s (attempt {attempt + 1}): {e}")
                    time.sleep(wait_time)
                    last_exception = e
                    continue
                else:
                    logger.error(f"Unexpected error for {service_name} after {self.max_retries} retries: {e}")
                    raise Exception(f"Unexpected error for {service_name}: {e}") from e
        
        # If we get here, all retries failed
        error_msg = f"Operation failed for {service_name} after {self.max_retries} retries"
        if last_exception:
            error_msg += f": {last_exception}"
        logger.error(error_msg)
        raise Exception(error_msg) from last_exception
    
    def validate_service_access(self, service_name: str, region: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Enhanced validation of access to a specific AWS service.
        
        Args:
            service_name: AWS service name to validate
            region: Specific region to validate (optional)
            
        Returns:
            Tuple of (is_accessible, error_message)
        """
        try:
            client = self.get_client(service_name, region)
            
            # Service-specific validation operations
            validation_operations = {
                'ec2': lambda c: c.describe_regions(),
                'rds': lambda c: c.describe_db_instances(MaxRecords=1),
                'lambda': lambda c: c.list_functions(MaxItems=1),
                's3': lambda c: c.list_buckets(),
                'ce': lambda c: c.get_dimension_values(
                    TimePeriod={'Start': '2024-12-01', 'End': '2025-01-01'},  # Use valid recent dates
                    Dimension='SERVICE'
                ),
                'budgets': lambda c: c.describe_budgets(AccountId=self.get_account_id(), MaxResults=1),
                'pricing': lambda c: c.describe_services(MaxResults=1),
                'cloudwatch': lambda c: c.list_metrics(),  # Remove MaxRecords parameter
                'logs': lambda c: c.describe_log_groups(limit=1),
                'sts': lambda c: c.get_caller_identity()
            }
            
            # Execute validation operation
            if service_name in validation_operations:
                self.execute_with_retry(
                    validation_operations[service_name], 
                    service_name, 
                    client
                )
            
            logger.debug(f"Validated access to {service_name}" + (f" in {region}" if region else ""))
            return True, None
            
        except Exception as e:
            error_msg = f"Cannot access {service_name}" + (f" in {region}" if region else "") + f": {e}"
            logger.warning(error_msg)
            return False, error_msg
    
    def validate_multi_region_access(self, service_name: str, regions: Optional[List[str]] = None) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Validate access to a service across multiple regions (Requirement 1.5).
        
        Args:
            service_name: AWS service name to validate
            regions: List of regions to validate (uses self.regions if not provided)
            
        Returns:
            Dictionary mapping region names to (is_accessible, error_message) tuples
        """
        target_regions = regions or self.regions
        results = {}
        
        for region in target_regions:
            results[region] = self.validate_service_access(service_name, region)
        
        accessible_regions = [r for r, (accessible, _) in results.items() if accessible]
        logger.info(f"Service {service_name} accessible in {len(accessible_regions)}/{len(target_regions)} regions: {accessible_regions}")
        
        return results
    
    def validate_cost_management_access(self) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Validate access to all AWS Cost Management APIs (Requirements 10.1, 10.2, 10.3).
        
        Returns:
            Dictionary mapping service names to (is_accessible, error_message) tuples
        """
        cost_services = ['ce', 'budgets', 'pricing', 'cur', 'cloudwatch']
        results = {}
        
        for service in cost_services:
            results[service] = self.validate_service_access(service)
        
        accessible_services = [s for s, (accessible, _) in results.items() if accessible]
        logger.info(f"Cost Management APIs accessible: {len(accessible_services)}/{len(cost_services)} - {accessible_services}")
        
        return results
    
    def get_service_quotas_client(self, region: Optional[str] = None) -> Any:
        """
        Get Service Quotas client for monitoring API limits.
        
        Args:
            region: AWS region for Service Quotas client (optional)
            
        Returns:
            Service Quotas boto3 client
        """
        return self.get_client('service-quotas', region=region)
    
    def refresh_credentials(self) -> None:
        """
        Force refresh of AWS credentials and clear client cache.
        
        Useful when credentials have been updated or when switching roles.
        """
        logger.info("Refreshing AWS credentials and clearing client cache")
        
        # Clear cached credentials and session
        self._session = None
        self._assumed_role_credentials = None
        self._credentials_expiry = None
        
        # Clear all cached clients
        self._clients.clear()
        
        # Re-validate credentials
        self._validate_credentials()
        
        logger.info("AWS credentials refreshed successfully")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get summary of current AWS configuration.
        
        Returns:
            Dictionary containing configuration details
        """
        try:
            account_id = self.get_account_id()
            identity = self.get_client('sts').get_caller_identity()
            
            return {
                'account_id': account_id,
                'user_arn': identity.get('Arn'),
                'user_id': identity.get('UserId'),
                'primary_region': self.region,
                'regions': self.regions,
                'profile_name': self.profile_name,
                'role_arn': self.role_arn,
                'max_retries': self.max_retries,
                'cached_clients': len(self._clients),
                'cost_management_services': list(self.COST_MANAGEMENT_SERVICES),
                'us_east_1_only_services': list(self.US_EAST_1_ONLY_SERVICES)
            }
        except Exception as e:
            logger.error(f"Failed to get configuration summary: {e}")
            return {'error': str(e)}