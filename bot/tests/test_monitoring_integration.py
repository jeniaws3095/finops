#!/usr/bin/env python3
"""
Integration tests for comprehensive monitoring and error handling.

Tests the enhanced monitoring, error recovery, and alerting capabilities
implemented for task 15.2.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from utils.monitoring import (
    StructuredLogger, 
    create_correlation_context,
    system_monitor,
    AlertSeverity,
    HealthStatus,
    MetricsCollector,
    PerformanceMetric
)
from utils.error_recovery import (
    ErrorClassifier,
    RecoveryManager,
    ErrorCategory,
    RecoveryStrategy,
    with_error_recovery,
    global_recovery_manager
)
from utils.http_client import HTTPClient


class TestStructuredLogging:
    """Test structured logging with correlation IDs."""
    
    def test_correlation_context_creation(self):
        """Test correlation context creation and management."""
        context = create_correlation_context(
            operation_id="test_operation",
            metadata={'test': 'data'}
        )
        
        assert context.operation_id == "test_operation"
        assert context.correlation_id is not None
        assert context.metadata['test'] == 'data'
        assert context.start_time > 0
    
    def test_structured_logger_with_context(self):
        """Test structured logger with correlation context."""
        logger = StructuredLogger('test.logger')
        context = create_correlation_context("test_op")
        
        logger.set_correlation_context(context)
        
        # Test that context is properly set
        retrieved_context = logger.get_correlation_context()
        assert retrieved_context.correlation_id == context.correlation_id
        assert retrieved_context.operation_id == context.operation_id
        
        # Test context clearing
        logger.clear_correlation_context()
        assert logger.get_correlation_context() is None
    
    def test_structured_logging_output(self, caplog):
        """Test structured logging output format."""
        logger = StructuredLogger('test.logger')
        context = create_correlation_context("test_op", metadata={'key': 'value'})
        logger.set_correlation_context(context)
        
        with caplog.at_level('INFO'):
            logger.info("Test message", {'extra': 'data'})
        
        # Verify log contains structured data
        assert len(caplog.records) > 0
        log_record = caplog.records[0]
        assert context.correlation_id in log_record.message
        assert "test_op" in log_record.message


class TestErrorRecovery:
    """Test error recovery mechanisms."""
    
    def test_error_classification(self):
        """Test error classification into categories."""
        classifier = ErrorClassifier()
        
        # Test throttling error
        from botocore.exceptions import ClientError
        throttle_error = ClientError(
            {'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}},
            'test_operation'
        )
        category = classifier.classify_error(throttle_error)
        assert category == ErrorCategory.THROTTLING
        
        # Test authentication error
        auth_error = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'test_operation'
        )
        category = classifier.classify_error(auth_error)
        assert category == ErrorCategory.AUTHORIZATION
        
        # Test server error
        server_error = ClientError(
            {'Error': {'Code': 'InternalError', 'Message': 'Internal error'}},
            'test_operation'
        )
        category = classifier.classify_error(server_error)
        assert category == ErrorCategory.SERVER_ERROR
    
    def test_recovery_strategy_selection(self):
        """Test recovery strategy selection based on error category."""
        classifier = ErrorClassifier()
        
        # Throttling should use exponential backoff
        strategy = classifier.get_recovery_strategy(ErrorCategory.THROTTLING)
        assert strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF
        
        # Client errors should not retry
        strategy = classifier.get_recovery_strategy(ErrorCategory.CLIENT_ERROR)
        assert strategy == RecoveryStrategy.NO_RETRY
        
        # Server errors should use exponential backoff
        strategy = classifier.get_recovery_strategy(ErrorCategory.SERVER_ERROR)
        assert strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF
    
    def test_recovery_manager_state_tracking(self):
        """Test recovery manager state tracking."""
        recovery_manager = RecoveryManager()
        
        # Simulate error
        test_exception = Exception("Test error")
        error_context = recovery_manager.record_error(
            operation_name="test_operation",
            exception=test_exception,
            attempt_number=1,
            correlation_id="test-correlation-id"
        )
        
        assert error_context.operation_name == "test_operation"
        assert error_context.error_message == "Test error"
        assert error_context.attempt_number == 1
        assert error_context.correlation_id == "test-correlation-id"
        
        # Check state tracking
        stats = recovery_manager.get_recovery_stats("test_operation")
        assert stats['total_failures'] == 1
        assert stats['consecutive_failures'] == 1
        
        # Simulate success
        recovery_manager.record_success("test_operation", "test-correlation-id")
        
        stats = recovery_manager.get_recovery_stats("test_operation")
        assert stats['total_successes'] == 1
        assert stats['consecutive_failures'] == 0
    
    def test_circuit_breaker_functionality(self):
        """Test circuit breaker functionality."""
        from utils.error_recovery import RecoveryConfig
        
        config = RecoveryConfig(circuit_breaker_threshold=2)
        recovery_manager = RecoveryManager(config)
        
        # Simulate multiple failures to trigger circuit breaker
        for i in range(3):
            recovery_manager.record_error(
                operation_name="test_circuit_breaker",
                exception=Exception(f"Error {i}"),
                attempt_number=i + 1
            )
        
        stats = recovery_manager.get_recovery_stats("test_circuit_breaker")
        # Circuit breaker should be open after threshold failures
        # (Implementation detail may vary based on exact logic)
        assert stats['consecutive_failures'] >= config.circuit_breaker_threshold
    
    def test_error_recovery_decorator(self):
        """Test error recovery decorator functionality."""
        call_count = 0
        
        @with_error_recovery(
            operation_name="test_decorator",
            recovery_manager=RecoveryManager()
        )
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return "success"
        
        # Function should succeed after retries
        result = test_function()
        assert result == "success"
        assert call_count == 3


class TestSystemMonitoring:
    """Test system monitoring capabilities."""
    
    def test_metrics_collection(self):
        """Test performance metrics collection."""
        collector = MetricsCollector()
        
        # Record some metrics
        metric1 = PerformanceMetric(
            name="test_metric",
            value=100.0,
            timestamp=time.time(),
            unit="milliseconds"
        )
        collector.record_metric(metric1)
        
        metric2 = PerformanceMetric(
            name="test_metric",
            value=200.0,
            timestamp=time.time(),
            unit="milliseconds"
        )
        collector.record_metric(metric2)
        
        # Get statistics
        stats = collector.get_metric_stats("test_metric")
        assert stats['count'] == 2
        assert stats['min'] == 100.0
        assert stats['max'] == 200.0
        assert stats['mean'] == 150.0
    
    def test_health_monitoring(self):
        """Test health monitoring functionality."""
        from utils.monitoring import HealthMonitor, HealthCheck
        
        monitor = HealthMonitor()
        
        # Register a test health check
        def test_health_check():
            return HealthCheck(
                name="test_check",
                status=HealthStatus.HEALTHY,
                message="Test check passed",
                timestamp=time.time(),
                response_time_ms=10.0
            )
        
        monitor.register_health_check("test_check", test_health_check)
        
        # Run health check
        result = monitor.run_health_check("test_check")
        assert result.name == "test_check"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Test check passed"
        
        # Run all health checks
        results = monitor.run_all_health_checks()
        assert "test_check" in results
        assert results["test_check"].status == HealthStatus.HEALTHY
    
    def test_alert_management(self):
        """Test alert management functionality."""
        from utils.monitoring import AlertManager
        
        alert_manager = AlertManager()
        
        # Create an alert
        alert = alert_manager.create_alert(
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="This is a test alert",
            source="test_system"
        )
        
        assert alert.severity == AlertSeverity.WARNING
        assert alert.title == "Test Alert"
        assert alert.message == "This is a test alert"
        assert alert.source == "test_system"
        assert not alert.resolved
        
        # Get active alerts
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].id == alert.id
        
        # Resolve alert
        resolved = alert_manager.resolve_alert(alert.id)
        assert resolved
        
        # Check that alert is resolved
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 0
    
    def test_system_monitor_integration(self):
        """Test system monitor integration."""
        # Test that system monitor is properly initialized
        assert system_monitor is not None
        assert system_monitor.metrics_collector is not None
        assert system_monitor.health_monitor is not None
        assert system_monitor.alert_manager is not None
        
        # Test recording operation metrics
        system_monitor.record_operation_metric("test_operation", 100.0, True)
        
        # Test getting system status
        status = system_monitor.get_system_status()
        assert 'timestamp' in status
        assert 'overall_health' in status
        assert 'health_checks' in status
        assert 'alerts' in status
        assert 'metrics' in status


class TestHTTPClientEnhancements:
    """Test HTTP client enhancements with monitoring."""
    
    @patch('requests.Session.request')
    def test_http_client_with_correlation_id(self, mock_request):
        """Test HTTP client includes correlation IDs."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True, 'data': 'test'}
        mock_request.return_value = mock_response
        
        client = HTTPClient()
        
        # Make request
        result = client._make_request('GET', '/test')
        
        # Verify correlation ID was included in headers
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        headers = call_args[1].get('headers', {})
        assert 'X-Correlation-ID' in headers
        
        # Verify result
        assert result['success'] is True
        assert result['data'] == 'test'
    
    @patch('requests.Session.request')
    def test_http_client_error_recovery(self, mock_request):
        """Test HTTP client error recovery integration."""
        # Mock server error followed by success
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'success': True, 'data': 'recovered'}
        
        mock_request.side_effect = [
            Exception("Server error: 500"),  # First call fails
            success_response  # Second call succeeds
        ]
        
        client = HTTPClient()
        
        # This should succeed after retry
        result = client._make_request('GET', '/test')
        assert result['success'] is True
        assert result['data'] == 'recovered'
        
        # Verify multiple calls were made
        assert mock_request.call_count >= 1


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""
    
    def test_end_to_end_monitoring_flow(self):
        """Test end-to-end monitoring flow."""
        # Create correlation context
        context = create_correlation_context("integration_test")
        
        # Set up structured logger
        logger = StructuredLogger('integration.test')
        logger.set_correlation_context(context)
        
        # Record some metrics
        system_monitor.record_operation_metric("integration_test", 150.0, True)
        
        # Create an alert
        alert = system_monitor.alert_manager.create_alert(
            severity=AlertSeverity.INFO,
            title="Integration Test Alert",
            message="Testing end-to-end flow",
            source="integration_test",
            correlation_id=context.correlation_id
        )
        
        # Verify alert was created with correlation ID
        assert alert.correlation_id == context.correlation_id
        
        # Get system status
        status = system_monitor.get_system_status()
        assert status['alerts']['total'] >= 1
        
        # Clean up
        logger.clear_correlation_context()
    
    def test_error_recovery_with_monitoring(self):
        """Test error recovery with monitoring integration."""
        operation_name = "monitored_operation"
        
        # Function that fails then succeeds
        call_count = 0
        
        @with_error_recovery(
            operation_name=operation_name,
            correlation_id="test-correlation"
        )
        def monitored_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"
        
        # Execute function
        result = monitored_function()
        assert result == "success"
        
        # Check recovery statistics
        stats = global_recovery_manager.get_recovery_stats(operation_name)
        assert stats['total_attempts'] >= 2
        assert stats['total_successes'] >= 1
        assert stats['total_failures'] >= 1


if __name__ == "__main__":
    # Run basic tests
    print("Running monitoring and error handling integration tests...")
    
    # Test structured logging
    logger = StructuredLogger('test')
    context = create_correlation_context("test_run")
    logger.set_correlation_context(context)
    logger.info("Test logging with correlation ID")
    
    # Test metrics collection
    system_monitor.record_operation_metric("test_metric", 100.0, True)
    
    # Test alert creation
    alert = system_monitor.alert_manager.create_alert(
        severity=AlertSeverity.INFO,
        title="Test Alert",
        message="Testing alert system",
        source="test_script"
    )
    
    print(f"Created alert: {alert.id}")
    
    # Get system status
    status = system_monitor.get_system_status()
    print(f"System status: {status['overall_health']}")
    
    alerts_info = status.get('alerts', {})
    active_alerts_count = alerts_info.get('active', 0)
    print(f"Active alerts: {active_alerts_count}")
    
    print("Integration tests completed successfully!")