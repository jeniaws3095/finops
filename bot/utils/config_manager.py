#!/usr/bin/env python3
"""
Configuration Management for Advanced FinOps Platform

This module handles loading and managing configuration from YAML files,
environment variables, and command-line overrides.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AWSConfig:
    """AWS configuration settings."""
    regions: List[str]
    default_region: str


@dataclass
class ServiceThresholds:
    """Service-specific threshold configurations."""
    ec2: Dict[str, float]
    rds: Dict[str, float]
    lambda_: Dict[str, float]  # lambda is a reserved keyword
    s3: Dict[str, float]
    ebs: Dict[str, float]
    elb: Dict[str, float]
    cloudwatch: Dict[str, float]


@dataclass
class OptimizationConfig:
    """Optimization configuration settings."""
    auto_approve_risk_levels: List[str]
    cost_thresholds: Dict[str, float]
    minimum_savings_threshold: float
    minimum_savings_percentage: float
    ml_rightsizing: Dict[str, Any]
    pricing: Dict[str, Any]


@dataclass
class AnomalyDetectionConfig:
    """Anomaly detection configuration settings."""
    baseline_days: int
    seasonal_adjustment: bool
    thresholds: Dict[str, float]
    alerts: Dict[str, Any]


@dataclass
class BudgetManagementConfig:
    """Budget management configuration settings."""
    default_budget_period: int
    alert_thresholds: List[float]
    forecasting: Dict[str, Any]
    approval_workflows: Dict[str, Any]


@dataclass
class SchedulingConfig:
    """Scheduling configuration settings."""
    continuous_monitoring: Dict[str, Any]
    daily_optimization: Dict[str, Any]
    weekly_reporting: Dict[str, Any]


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str
    file: Dict[str, Any]
    console: Dict[str, Any]
    components: Dict[str, str]


@dataclass
class SafetyConfig:
    """Safety configuration settings."""
    dry_run: Dict[str, Any]
    rollback: Dict[str, Any]
    limits: Dict[str, Any]


class ConfigManager:
    """
    Manages configuration loading and access for the Advanced FinOps Platform.
    
    Configuration is loaded from multiple sources in order of precedence:
    1. Command-line arguments (highest priority)
    2. Environment variables
    3. Configuration file (config.yaml)
    4. Default values (lowest priority)
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to configuration file (default: config.yaml)
        """
        self.logger = logging.getLogger(__name__)
        
        # Determine config file path
        if config_file is None:
            config_file = self._find_config_file()
        
        self.config_file = config_file
        self._config = {}
        self._load_configuration()
    
    def _find_config_file(self) -> str:
        """Find the configuration file: system path first, then user, then cwd."""
        possible_paths = [
            "/etc/advanced-finops/config.yaml",  # system config first
            os.path.expanduser("~/.advanced-finops/config.yaml"),
            "config.yaml",
            "config.yml",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return "config.yaml"
    
    def _load_configuration(self) -> None:
        """Load configuration from file and environment variables."""
        try:
            # Load from YAML file
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self._config = yaml.safe_load(f) or {}
                self.logger.info(f"Loaded configuration from {self.config_file}")
            else:
                self.logger.warning(f"Configuration file {self.config_file} not found, using defaults")
                self._config = self._get_default_config()
            
            # Override with environment variables
            self._apply_environment_overrides()
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self._config = self._get_default_config()
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            'FINOPS_AWS_REGION': ['aws', 'default_region'],
            'FINOPS_DRY_RUN': ['safety', 'dry_run', 'default'],
            'FINOPS_LOG_LEVEL': ['logging', 'level'],
            'FINOPS_BACKEND_URL': ['backend_api', 'base_url'],
            'FINOPS_CONTINUOUS_MONITORING': ['scheduling', 'continuous_monitoring', 'enabled'],
            'FINOPS_MONITORING_INTERVAL': ['scheduling', 'continuous_monitoring', 'interval_minutes'],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif self._is_float(value):
                    value = float(value)
                
                # Set the configuration value
                self._set_nested_value(self._config, config_path, value)
                self.logger.info(f"Applied environment override: {env_var} = {value}")
    
    def _is_float(self, value: str) -> bool:
        """Check if a string represents a float."""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _set_nested_value(self, config: Dict[str, Any], path: List[str], value: Any) -> None:
        """Set a nested configuration value."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'aws': {
                'regions': ['us-east-1'],
                'default_region': 'us-east-1'
            },
            'services': {
                'enabled': ['ec2', 'rds', 'lambda', 's3', 'ebs', 'elb', 'cloudwatch'],
                'thresholds': {
                    'ec2': {
                        'cpu_utilization_threshold': 5.0,
                        'memory_utilization_threshold': 10.0,
                        'idle_days_threshold': 7
                    },
                    'rds': {
                        'cpu_utilization_threshold': 10.0,
                        'connection_utilization_threshold': 20.0,
                        'idle_days_threshold': 14
                    },
                    'lambda': {
                        'memory_utilization_threshold': 50.0,
                        'duration_efficiency_threshold': 80.0,
                        'invocation_threshold': 10,
                        'idle_days_threshold': 30
                    },
                    'cloudwatch': {
                         'alarm_evaluation_periods': 3,
                         'alarm_period_seconds': 300,
                         'metric_retention_days': 14
                    }
                }
            },
            'optimization': {
                'auto_approve_risk_levels': ['LOW'],
                'cost_thresholds': {
                    'LOW': 50.0,
                    'MEDIUM': 200.0,
                    'HIGH': 1000.0,
                    'CRITICAL': 5000.0
                },
                'minimum_savings_threshold': 10.0,
                'minimum_savings_percentage': 5.0
            },
            'scheduling': {
                'continuous_monitoring': {
                    'enabled': False,
                    'interval_minutes': 60
                },
                'daily_optimization': {
                    'enabled': False,
                    'time': '02:00'
                }
            },
            'logging': {
                'level': 'INFO',
                'file': {
                    'enabled': True,
                    'path': 'advanced_finops.log'
                },
                'console': {
                    'enabled': True
                }
            },
            'safety': {
                'dry_run': {
                    'default': True,
                    'confirmation_required': True
                },
                'rollback': {
                    'enabled': True,
                    'timeout_minutes': 30
                }
            },
            'backend_api': {
                'base_url': 'http://localhost:5000',
                'timeout_seconds': 30,
                'retry_attempts': 3
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to the configuration key (e.g., 'aws.default_region')
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        current = self._config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to the configuration key
            value: Value to set
        """
        keys = key_path.split('.')
        self._set_nested_value(self._config, keys, value)
    
    def get_aws_config(self) -> AWSConfig:
        """Get AWS configuration."""
        aws_config = self.get('aws', {})
        return AWSConfig(
            regions=aws_config.get('regions', ['us-east-1']),
            default_region=aws_config.get('default_region', 'us-east-1')
        )
    
    def get_service_thresholds(self) -> ServiceThresholds:
        """Get service threshold configurations."""
        thresholds = self.get('services.thresholds', {})
        return ServiceThresholds(
            ec2=thresholds.get('ec2', {}),
            rds=thresholds.get('rds', {}),
            lambda_=thresholds.get('lambda', {}),
            s3=thresholds.get('s3', {}),
            ebs=thresholds.get('ebs', {}),
            elb=thresholds.get('elb', {}),
            cloudwatch=thresholds.get('cloudwatch', {})
        )
    
    def get_optimization_config(self) -> OptimizationConfig:
        """Get optimization configuration."""
        opt_config = self.get('optimization', {})
        return OptimizationConfig(
            auto_approve_risk_levels=opt_config.get('auto_approve_risk_levels', ['LOW']),
            cost_thresholds=opt_config.get('cost_thresholds', {}),
            minimum_savings_threshold=opt_config.get('minimum_savings_threshold', 10.0),
            minimum_savings_percentage=opt_config.get('minimum_savings_percentage', 5.0),
            ml_rightsizing=opt_config.get('ml_rightsizing', {}),
            pricing=opt_config.get('pricing', {})
        )
    
    def get_anomaly_detection_config(self) -> AnomalyDetectionConfig:
        """Get anomaly detection configuration."""
        anomaly_config = self.get('anomaly_detection', {})
        return AnomalyDetectionConfig(
            baseline_days=anomaly_config.get('baseline_days', 30),
            seasonal_adjustment=anomaly_config.get('seasonal_adjustment', True),
            thresholds=anomaly_config.get('thresholds', {}),
            alerts=anomaly_config.get('alerts', {})
        )
    
    def get_budget_management_config(self) -> BudgetManagementConfig:
        """Get budget management configuration."""
        budget_config = self.get('budget_management', {})
        return BudgetManagementConfig(
            default_budget_period=budget_config.get('default_budget_period', 12),
            alert_thresholds=budget_config.get('alert_thresholds', [50.0, 75.0, 90.0, 100.0]),
            forecasting=budget_config.get('forecasting', {}),
            approval_workflows=budget_config.get('approval_workflows', {})
        )
    
    def get_scheduling_config(self) -> SchedulingConfig:
        """Get scheduling configuration."""
        sched_config = self.get('scheduling', {})
        return SchedulingConfig(
            continuous_monitoring=sched_config.get('continuous_monitoring', {}),
            daily_optimization=sched_config.get('daily_optimization', {}),
            weekly_reporting=sched_config.get('weekly_reporting', {})
        )
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration."""
        log_config = self.get('logging', {})
        return LoggingConfig(
            level=log_config.get('level', 'INFO'),
            file=log_config.get('file', {}),
            console=log_config.get('console', {}),
            components=log_config.get('components', {})
        )
    
    def get_safety_config(self) -> SafetyConfig:
        """Get safety configuration."""
        safety_config = self.get('safety', {})
        return SafetyConfig(
            dry_run=safety_config.get('dry_run', {}),
            rollback=safety_config.get('rollback', {}),
            limits=safety_config.get('limits', {})
        )
    
    def is_service_enabled(self, service: str) -> bool:
        """Check if a service is enabled."""
        enabled_services = self.get('services.enabled', [])
        return service in enabled_services
    
    def get_service_threshold(self, service: str, threshold_name: str, default: float = 0.0) -> float:
        """Get a specific service threshold."""
        return self.get(f'services.thresholds.{service}.{threshold_name}', default)
    
    def is_continuous_monitoring_enabled(self) -> bool:
        """Check if continuous monitoring is enabled."""
        return self.get('scheduling.continuous_monitoring.enabled', False)
    
    def get_monitoring_interval(self) -> int:
        """Get monitoring interval in minutes."""
        return self.get('scheduling.continuous_monitoring.interval_minutes', 60)
    
    def is_dry_run_default(self) -> bool:
        """Check if dry run is the default mode."""
        return self.get('safety.dry_run.default', True)
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_configuration()
        self.logger.info("Configuration reloaded")
    
    def save(self, file_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            file_path: Path to save configuration (default: current config file)
        """
        if file_path is None:
            file_path = self.config_file
        
        try:
            with open(file_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
            self.logger.info(f"Configuration saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of issues.
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        # Validate AWS configuration
        aws_config = self.get('aws', {})
        if not aws_config.get('default_region'):
            issues.append("AWS default_region is required")
        
        if not aws_config.get('regions'):
            issues.append("AWS regions list cannot be empty")
        
        # Validate service thresholds
        services = self.get('services.enabled', [])
        thresholds = self.get('services.thresholds', {})
        
        for service in services:
            if service not in thresholds:
                issues.append(f"Missing thresholds for enabled service: {service}")
        
        # Validate optimization configuration
        opt_config = self.get('optimization', {})
        cost_thresholds = opt_config.get('cost_thresholds', {})
        
        required_risk_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        for level in required_risk_levels:
            if level not in cost_thresholds:
                issues.append(f"Missing cost threshold for risk level: {level}")
        
        # Validate scheduling configuration
        if self.is_continuous_monitoring_enabled():
            interval = self.get_monitoring_interval()
            if interval < 1:
                issues.append("Monitoring interval must be at least 1 minute")
        
        return issues
    
    def get_all(self) -> Dict[str, Any]:
        """Get the complete configuration dictionary."""
        return self._config.copy()
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"ConfigManager(config_file={self.config_file})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"ConfigManager(config_file='{self.config_file}', keys={list(self._config.keys())})"