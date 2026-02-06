#!/usr/bin/env python3
"""
Test suite for main.py workflow orchestration enhancements.

Tests the new features implemented for task 13.1:
- Configuration file support
- Scheduling and continuous monitoring
- Enhanced command-line arguments
- Comprehensive error handling and logging
- Progress reporting
"""

import pytest
import tempfile
import os
import yaml
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Import the modules to test
from main import AdvancedFinOpsOrchestrator
from utils.config_manager import ConfigManager
from utils.scheduler import FinOpsScheduler, ScheduleType


class TestConfigManager:
    """Test configuration management functionality."""
    
    @patch('os.path.exists')
    def test_config_manager_initialization(self, mock_exists):
        """Test ConfigManager initialization with default config."""
        # Ensure it doesn't find the local config.yaml
        mock_exists.return_value = False
        config_manager = ConfigManager()
        
        # Should have default configuration
        assert config_manager.get('aws.default_region') == 'us-east-1'
        assert config_manager.get('safety.dry_run.default') is True
        assert config_manager.is_service_enabled('ec2') is True
    
    def test_config_manager_with_custom_file(self):
        """Test ConfigManager with custom configuration file."""
        # Create temporary config file
        config_data = {
            'aws': {
                'default_region': 'us-west-2',
                'regions': ['us-west-2', 'eu-west-1']
            },
            'services': {
                'enabled': ['ec2', 'rds'],
                'thresholds': {
                    'ec2': {
                        'cpu_utilization_threshold': 10.0
                    }
                }
            },
            'scheduling': {
                'continuous_monitoring': {
                    'enabled': True,
                    'interval_minutes': 30
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            config_manager = ConfigManager(config_file)
            
            # Test custom values
            assert config_manager.get('aws.default_region') == 'us-west-2'
            assert config_manager.get('services.thresholds.ec2.cpu_utilization_threshold') == 10.0
            assert config_manager.is_continuous_monitoring_enabled() is True
            assert config_manager.get_monitoring_interval() == 30
            
        finally:
            os.unlink(config_file)
    
    def test_environment_variable_overrides(self):
        """Test environment variable overrides."""
        with patch.dict(os.environ, {
            'FINOPS_AWS_REGION': 'eu-central-1',
            'FINOPS_DRY_RUN': 'false',
            'FINOPS_LOG_LEVEL': 'DEBUG'
        }):
            config_manager = ConfigManager()
            
            # Environment variables should override defaults
            assert config_manager.get('aws.default_region') == 'eu-central-1'
            assert config_manager.get('safety.dry_run.default') is False
            assert config_manager.get('logging.level') == 'DEBUG'
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Create invalid config
        config_data = {
            'aws': {
                'regions': []  # Empty regions list should be invalid
            },
            'services': {
                'enabled': ['ec2', 'invalid_service'],  # Invalid service
                'thresholds': {}  # Missing thresholds for enabled services
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            config_manager = ConfigManager(config_file)
            issues = config_manager.validate()
            
            # Should have validation issues
            assert len(issues) > 0
            assert any('regions list cannot be empty' in issue for issue in issues)
            
        finally:
            os.unlink(config_file)


class TestScheduler:
    """Test scheduler functionality."""
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        scheduler = FinOpsScheduler()
        
        assert not scheduler.is_running()
        assert len(scheduler.tasks) == 0
    
    def test_add_continuous_task(self):
        """Test adding continuous monitoring task."""
        scheduler = FinOpsScheduler()
        
        # Mock callback function
        callback = Mock(return_value={'success': True})
        
        scheduler.add_continuous_task(
            task_id='test_continuous',
            name='Test Continuous Task',
            interval_minutes=5,
            callback=callback
        )
        
        assert 'test_continuous' in scheduler.tasks
        task = scheduler.tasks['test_continuous']
        assert task.schedule_type == ScheduleType.CONTINUOUS
        assert task.interval_minutes == 5
        assert task.enabled is True
        assert task.next_run is not None
    
    def test_add_daily_task(self):
        """Test adding daily scheduled task."""
        scheduler = FinOpsScheduler()
        
        callback = Mock(return_value={'success': True})
        
        scheduler.add_daily_task(
            task_id='test_daily',
            name='Test Daily Task',
            time_of_day='02:00',
            callback=callback
        )
        
        assert 'test_daily' in scheduler.tasks
        task = scheduler.tasks['test_daily']
        assert task.schedule_type == ScheduleType.DAILY
        assert task.time_of_day == '02:00'
        assert task.next_run is not None
    
    def test_add_weekly_task(self):
        """Test adding weekly scheduled task."""
        scheduler = FinOpsScheduler()
        
        callback = Mock(return_value={'success': True})
        
        scheduler.add_weekly_task(
            task_id='test_weekly',
            name='Test Weekly Task',
            day_of_week='sunday',
            time_of_day='06:00',
            callback=callback
        )
        
        assert 'test_weekly' in scheduler.tasks
        task = scheduler.tasks['test_weekly']
        assert task.schedule_type == ScheduleType.WEEKLY
        assert task.day_of_week == 'sunday'
        assert task.time_of_day == '06:00'
    
    def test_invalid_time_format(self):
        """Test invalid time format handling."""
        scheduler = FinOpsScheduler()
        callback = Mock()
        
        with pytest.raises(ValueError, match="Invalid time format"):
            scheduler.add_daily_task(
                task_id='test_invalid',
                name='Test Invalid Time',
                time_of_day='25:00',  # Invalid hour
                callback=callback
            )
    
    def test_invalid_day_of_week(self):
        """Test invalid day of week handling."""
        scheduler = FinOpsScheduler()
        callback = Mock()
        
        with pytest.raises(ValueError, match="Invalid day of week"):
            scheduler.add_weekly_task(
                task_id='test_invalid',
                name='Test Invalid Day',
                day_of_week='invalid_day',
                time_of_day='06:00',
                callback=callback
            )
    
    def test_task_management(self):
        """Test task enable/disable/remove operations."""
        scheduler = FinOpsScheduler()
        callback = Mock()
        
        scheduler.add_continuous_task(
            task_id='test_task',
            name='Test Task',
            interval_minutes=10,
            callback=callback
        )
        
        # Test disable
        assert scheduler.disable_task('test_task') is True
        assert scheduler.tasks['test_task'].enabled is False
        
        # Test enable
        assert scheduler.enable_task('test_task') is True
        assert scheduler.tasks['test_task'].enabled is True
        
        # Test remove
        assert scheduler.remove_task('test_task') is True
        assert 'test_task' not in scheduler.tasks
        
        # Test operations on non-existent task
        assert scheduler.disable_task('non_existent') is False
        assert scheduler.enable_task('non_existent') is False
        assert scheduler.remove_task('non_existent') is False
    
    def test_run_task_now(self):
        """Test immediate task execution."""
        scheduler = FinOpsScheduler()
        callback = Mock(return_value={'success': True})
        
        scheduler.add_continuous_task(
            task_id='test_immediate',
            name='Test Immediate Task',
            interval_minutes=60,
            callback=callback
        )
        
        # Run task immediately
        result = scheduler.run_task_now('test_immediate')
        assert result is True
        callback.assert_called_once()
        
        # Test with disabled task
        scheduler.disable_task('test_immediate')
        callback.reset_mock()
        result = scheduler.run_task_now('test_immediate')
        assert result is False
        callback.assert_not_called()


class TestAdvancedFinOpsOrchestrator:
    """Test enhanced orchestrator functionality."""
    
    @patch('main.AWSConfig')
    @patch('main.SafetyControls')
    @patch('main.HTTPClient')
    def test_orchestrator_with_config(self, mock_http, mock_safety, mock_aws):
        """Test orchestrator initialization with configuration."""
        # Create test config
        config_data = {
            'aws': {'default_region': 'us-west-2'},
            'safety': {'dry_run': {'default': False}},
            'logging': {'level': 'DEBUG'}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            with patch('main.logging'):
                orchestrator = AdvancedFinOpsOrchestrator(
                    config_file=config_file
                )
                
                # Should use config values
                assert orchestrator.region == 'us-west-2'
                assert orchestrator.config_manager.get('logging.level') == 'DEBUG'
                
        finally:
            os.unlink(config_file)
    
    @patch('main.AWSConfig')
    @patch('main.SafetyControls')
    @patch('main.HTTPClient')
    def test_scheduler_setup(self, mock_http, mock_safety, mock_aws):
        """Test scheduler setup based on configuration."""
        config_data = {
            'scheduling': {
                'continuous_monitoring': {
                    'enabled': True,
                    'interval_minutes': 30
                },
                'daily_optimization': {
                    'enabled': True,
                    'time': '03:00'
                },
                'weekly_reporting': {
                    'enabled': True,
                    'day': 'monday',
                    'time': '07:00'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            with patch('main.logging'):
                orchestrator = AdvancedFinOpsOrchestrator(
                    config_file=config_file
                )
                
                # Setup scheduler
                orchestrator.setup_scheduler()
                
                # Should have scheduled tasks
                tasks = orchestrator.scheduler.list_tasks()
                task_ids = [task['task_id'] for task in tasks]
                
                assert 'continuous_monitoring' in task_ids
                assert 'daily_optimization' in task_ids
                assert 'weekly_reporting' in task_ids
                
        finally:
            os.unlink(config_file)
    
    @patch('main.AWSConfig')
    @patch('main.SafetyControls')
    @patch('main.HTTPClient')
    def test_continuous_monitoring_callback(self, mock_http, mock_safety, mock_aws):
        """Test continuous monitoring callback."""
        with patch('main.logging'):
            orchestrator = AdvancedFinOpsOrchestrator()
            
            # Mock the methods that would be called
            orchestrator.run_discovery = Mock(return_value={
                'resources_discovered': 10,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            orchestrator.run_anomaly_detection = Mock(return_value={
                'anomalies_detected': 2,
                'detailed_results': {
                    'anomalies_detected': [
                        {'severity': 'LOW'},
                        {'severity': 'CRITICAL'}
                    ]
                }
            })
            
            # Call the callback
            result = orchestrator._continuous_monitoring_callback()
            
            # Should have called both methods
            orchestrator.run_discovery.assert_called_once()
            orchestrator.run_anomaly_detection.assert_called_once()
            
            # Should return success with metrics
            assert result['success'] is True
            assert result['resources_discovered'] == 10
            assert result['anomalies_detected'] == 2
            assert result['critical_anomalies'] == 1
    
    @patch('main.AWSConfig')
    @patch('main.SafetyControls')
    @patch('main.HTTPClient')
    def test_discovery_with_config_thresholds(self, mock_http, mock_safety, mock_aws):
        """Test discovery using configuration-based thresholds."""
        config_data = {
            'services': {
                'enabled': ['ec2', 'rds'],
                'thresholds': {
                    'ec2': {
                        'cpu_utilization_threshold': 15.0,
                        'idle_days_threshold': 10
                    },
                    'rds': {
                        'cpu_utilization_threshold': 20.0,
                        'connection_utilization_threshold': 30.0
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            with patch('main.logging'):
                orchestrator = AdvancedFinOpsOrchestrator(config_file=config_file)
                
                # Mock scanners
                mock_ec2_scanner = Mock()
                mock_ec2_scanner.scan_instances.return_value = [
                    {'resourceId': 'i-123', 'resourceType': 'ec2'}
                ]
                
                mock_rds_scanner = Mock()
                mock_rds_scanner.scan_databases.return_value = [
                    {'resourceId': 'db-456', 'resourceType': 'rds'}
                ]
                
                with patch('main.EC2Scanner', return_value=mock_ec2_scanner), \
                     patch('main.RDSScanner', return_value=mock_rds_scanner):
                    
                    # Mock HTTP client health check
                    orchestrator.http_client.health_check.return_value = True
                    orchestrator.http_client.post_resources = Mock()
                    
                    # Run discovery
                    results = orchestrator.run_discovery()
                    
                    # Should have scanned enabled services
                    assert 'ec2' in results['services']
                    assert 'rds' in results['services']
                    assert results['resources_discovered'] == 2
                    
                    # Should include configuration info
                    assert 'configuration_used' in results
                    assert 'thresholds' in results['configuration_used']
                    
        finally:
            os.unlink(config_file)


def test_main_function_argument_parsing():
    """Test main function argument parsing and validation."""
    import sys
    from unittest.mock import patch
    
    # Test configuration validation mode
    test_args = ['main.py', '--validate-config', '--config', 'test.yaml']
    
    with patch.object(sys, 'argv', test_args), \
         patch('main.AdvancedFinOpsOrchestrator') as mock_orchestrator:
        
        mock_config_manager = Mock()
        mock_config_manager.validate.return_value = []  # No issues
        mock_orchestrator.return_value.config_manager = mock_config_manager
        
        with patch('sys.exit') as mock_exit:
            try:
                from main import main
                # Reset mock to clear any previous calls during import
                mock_orchestrator.return_value.config_manager.validate.reset_mock()
                main()
            except SystemExit:
                pass
            
            # Should exit with code 0 (success)
            mock_exit.assert_called_with(0)
            mock_orchestrator.return_value.config_manager.validate.assert_called_once()


def test_main_function_connection_test():
    """Test connection testing mode."""
    import sys
    from unittest.mock import patch
    
    test_args = ['main.py', '--test-connection']
    
    with patch.object(sys, 'argv', test_args), \
         patch('main.AdvancedFinOpsOrchestrator') as mock_orchestrator:
        
        # Mock successful connections
        mock_aws_config = Mock()
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_session.client.return_value = mock_sts_client
        mock_aws_config.get_session.return_value = mock_session
        
        mock_http_client = Mock()
        mock_http_client.health_check.return_value = True
        
        mock_orchestrator.return_value.aws_config = mock_aws_config
        mock_orchestrator.return_value.http_client = mock_http_client
        
        with patch('sys.exit') as mock_exit, \
             patch('builtins.print') as mock_print:
            try:
                from main import main
                main()
            except SystemExit:
                pass
            
            # Should exit with code 0
            mock_exit.assert_called_with(0)
            
            # Verify prints
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            found_aws = any('AWS connection successful' in str(call) for call in print_calls)
            found_backend = any('Backend API connection successful' in str(call) for call in print_calls)
            
            assert found_aws or found_backend, f"Expected connection success messages in: {print_calls}"


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])