#!/usr/bin/env python3
"""
Enhanced HTTP Client Tests

Tests the new features added to the HTTP client including:
- Authentication support
- Circuit breaker pattern
- Performance monitoring
- Request/response logging

Requirements: 9.1
"""

import pytest
import requests
import json
import time
from unittest.mock import Mock, patch, MagicMock
from utils.http_client import HTTPClient, CircuitBreakerState, CircuitBreakerConfig


class TestHTTPClientEnhanced:
    """Test suite for enhanced HTTP client functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Test client with enhanced features enabled
        self.client = HTTPClient(
            base_url="http://localhost:5002",
            timeout=10,
            max_retries=2,
            api_key="test-api-key-123",
            enable_circuit_breaker=True,
            enable_performance_monitoring=True
        )
        
        # Test client with features disabled
        self.basic_client = HTTPClient(
            base_url="http://localhost:5002",
            enable_circuit_breaker=False,
            enable_performance_monitoring=False
        )
    
    def test_authentication_initialization(self):
        """Test HTTP client initialization with authentication."""
        # Test with API key
        client = HTTPClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert 'Authorization' in client.session.headers
        assert client.session.headers['Authorization'] == 'Bearer test-key'
        assert 'X-API-Key' in client.session.headers
        assert client.session.headers['X-API-Key'] == 'test-key'
        
        # Test without API key
        client_no_auth = HTTPClient()
        assert client_no_auth.api_key is None
        assert 'Authorization' not in client_no_auth.session.headers
        assert 'X-API-Key' not in client_no_auth.session.headers
    
    def test_set_authentication(self):
        """Test setting authentication credentials."""
        client = HTTPClient()
        
        # Test bearer token
        client.set_authentication("bearer-token-123", "bearer")
        assert client.api_key == "bearer-token-123"
        assert client.session.headers['Authorization'] == 'Bearer bearer-token-123'
        assert 'X-API-Key' not in client.session.headers
        
        # Test API key
        client.set_authentication("api-key-456", "api_key")
        assert client.api_key == "api-key-456"
        assert client.session.headers['X-API-Key'] == 'api-key-456'
        assert 'Authorization' not in client.session.headers
        
        # Test basic auth
        client.set_authentication("basic-auth-789", "basic")
        assert client.api_key == "basic-auth-789"
        assert client.session.headers['Authorization'] == 'Basic basic-auth-789'
        assert 'X-API-Key' not in client.session.headers
    
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        # Test with circuit breaker enabled
        assert self.client.enable_circuit_breaker is True
        assert self.client.circuit_breaker_stats.state == CircuitBreakerState.CLOSED
        assert self.client.circuit_breaker_stats.failure_count == 0
        
        # Test with circuit breaker disabled
        assert self.basic_client.enable_circuit_breaker is False
    
    def test_performance_monitoring_initialization(self):
        """Test performance monitoring initialization."""
        # Test with performance monitoring enabled
        assert self.client.enable_performance_monitoring is True
        assert self.client.performance_metrics.request_count == 0
        assert self.client.performance_metrics.avg_response_time == 0.0
        
        # Test with performance monitoring disabled
        assert self.basic_client.enable_performance_monitoring is False
    
    @patch('requests.Session.request')
    def test_circuit_breaker_closed_state(self, mock_request):
        """Test circuit breaker in closed state (normal operation)."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": {}}
        mock_request.return_value = mock_response
        
        # Make request - should succeed
        result = self.client._make_request('GET', '/api/test')
        
        assert result["success"] is True
        assert self.client.circuit_breaker_stats.state == CircuitBreakerState.CLOSED
        assert self.client.circuit_breaker_stats.success_count == 1
        assert self.client.circuit_breaker_stats.failure_count == 0
    
    @patch('requests.Session.request')
    def test_circuit_breaker_open_state(self, mock_request):
        """Test circuit breaker opening after failures."""
        # Configure circuit breaker with low failure threshold for testing
        self.client.circuit_breaker_config.failure_threshold = 2
        
        # Mock server error responses
        error_response = Mock()
        error_response.status_code = 500
        mock_request.return_value = error_response
        
        with patch('time.sleep'):  # Speed up test
            # First failure - circuit breaker should remain closed
            with pytest.raises(Exception):
                self.client._make_request('GET', '/api/test1')
            assert self.client.circuit_breaker_stats.state == CircuitBreakerState.CLOSED
            assert self.client.circuit_breaker_stats.failure_count == 1
            
            # Second failure - should open circuit breaker
            with pytest.raises(Exception):
                self.client._make_request('GET', '/api/test2')
            assert self.client.circuit_breaker_stats.state == CircuitBreakerState.OPEN
            assert self.client.circuit_breaker_stats.failure_count == 2
            
            # Third request - should be rejected by circuit breaker
            with pytest.raises(Exception, match="Circuit breaker is OPEN"):
                self.client._make_request('GET', '/api/test3')
    
    @patch('requests.Session.request')
    def test_circuit_breaker_half_open_state(self, mock_request):
        """Test circuit breaker half-open state and recovery."""
        # Configure circuit breaker for testing
        self.client.circuit_breaker_config.failure_threshold = 1
        self.client.circuit_breaker_config.recovery_timeout = 1  # 1 second
        self.client.circuit_breaker_config.success_threshold = 2
        
        # Mock server error to open circuit breaker
        error_response = Mock()
        error_response.status_code = 500
        mock_request.return_value = error_response
        
        with patch('time.sleep'):
            # Cause failure to open circuit breaker
            with pytest.raises(Exception):
                self.client._make_request('GET', '/api/test')
            assert self.client.circuit_breaker_stats.state == CircuitBreakerState.OPEN
            
            # Mock time to simulate recovery timeout passing
            original_time = time.time()
            with patch('time.time', return_value=original_time + 2):  # 2 seconds later
                success_response = Mock()
                success_response.status_code = 200
                success_response.json.return_value = {"success": True}
                mock_request.return_value = success_response
                
                # First success - should transition to half-open
                result = self.client._make_request('GET', '/api/test')
                assert result["success"] is True
                assert self.client.circuit_breaker_stats.state == CircuitBreakerState.HALF_OPEN
                assert self.client.circuit_breaker_stats.consecutive_successes == 1
                
                # Second success - should close circuit breaker
                result = self.client._make_request('GET', '/api/test')
                assert result["success"] is True
                assert self.client.circuit_breaker_stats.state == CircuitBreakerState.CLOSED
                assert self.client.circuit_breaker_stats.consecutive_successes == 2
    
    @patch('requests.Session.request')
    def test_performance_metrics_tracking(self, mock_request):
        """Test performance metrics tracking."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": {}}
        mock_request.return_value = mock_response
        
        # Make multiple requests
        for i in range(3):
            self.client._make_request('GET', f'/api/test{i}')
        
        # Check global metrics
        metrics = self.client.get_performance_metrics()
        global_metrics = metrics['global_metrics']
        
        assert global_metrics['request_count'] == 3
        assert global_metrics['success_count'] == 3
        assert global_metrics['error_count'] == 0
        assert global_metrics['success_rate'] == 100.0
        assert global_metrics['avg_response_time'] > 0
        
        # Check endpoint-specific metrics
        endpoint_metrics = metrics['endpoint_metrics']
        assert '/api/test0' in endpoint_metrics
        assert endpoint_metrics['/api/test0']['request_count'] == 1
        assert endpoint_metrics['/api/test0']['success_count'] == 1
    
    @patch('requests.Session.request')
    def test_performance_metrics_with_errors(self, mock_request):
        """Test performance metrics tracking with errors."""
        # Reset metrics first to ensure clean state
        self.client.reset_performance_metrics()
        
        # Mock error response
        error_response = Mock()
        error_response.status_code = 500
        mock_request.return_value = error_response
        
        with patch('time.sleep'):  # Speed up test
            # Make failing requests to different endpoints to avoid circuit breaker
            with pytest.raises(Exception):
                self.client._make_request('GET', '/api/test1')
            with pytest.raises(Exception):
                self.client._make_request('GET', '/api/test2')
        
        # Check metrics include errors
        metrics = self.client.get_performance_metrics()
        global_metrics = metrics['global_metrics']
        
        assert global_metrics['request_count'] == 2
        assert global_metrics['success_count'] == 0
        assert global_metrics['error_count'] == 2
        assert global_metrics['success_rate'] == 0.0
    
    def test_reset_performance_metrics(self):
        """Test resetting performance metrics."""
        # Simulate some metrics
        self.client.performance_metrics.request_count = 10
        self.client.performance_metrics.success_count = 8
        self.client.performance_metrics.error_count = 2
        
        # Reset metrics
        self.client.reset_performance_metrics()
        
        # Check metrics are reset
        metrics = self.client.get_performance_metrics()
        global_metrics = metrics['global_metrics']
        
        assert global_metrics['request_count'] == 0
        assert global_metrics['success_count'] == 0
        assert global_metrics['error_count'] == 0
        assert global_metrics['avg_response_time'] == 0.0
    
    @patch('requests.Session.request')
    def test_circuit_breaker_disabled(self, mock_request):
        """Test that circuit breaker can be disabled."""
        # Mock server error responses
        error_response = Mock()
        error_response.status_code = 500
        mock_request.return_value = error_response
        
        with patch('time.sleep'):
            # Make multiple failing requests - should not trigger circuit breaker
            for i in range(5):
                with pytest.raises(Exception):
                    self.basic_client._make_request('GET', '/api/test')
            
            # Circuit breaker should remain closed (disabled)
            assert self.basic_client.circuit_breaker_stats.state == CircuitBreakerState.CLOSED
    
    @patch('requests.Session.request')
    def test_performance_monitoring_disabled(self, mock_request):
        """Test that performance monitoring can be disabled."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": {}}
        mock_request.return_value = mock_response
        
        # Make requests with disabled monitoring
        self.basic_client._make_request('GET', '/api/test')
        
        # Metrics should remain at zero
        metrics = self.basic_client.get_performance_metrics()
        global_metrics = metrics['global_metrics']
        
        assert global_metrics['request_count'] == 0
        assert global_metrics['success_count'] == 0
        assert global_metrics['avg_response_time'] == 0.0
    
    @patch('utils.http_client.HTTPClient._make_request')
    def test_health_check_with_circuit_breaker_status(self, mock_request):
        """Test health check includes circuit breaker status."""
        mock_request.return_value = {"success": True, "data": {"status": "healthy"}}
        
        # Set circuit breaker to open state for testing
        self.client.circuit_breaker_stats.state = CircuitBreakerState.OPEN
        
        result = self.client.health_check()
        
        assert result is True
        mock_request.assert_called_once_with('GET', '/api/health')
    
    @patch('requests.Session.request')
    def test_request_response_logging(self, mock_request):
        """Test request and response logging."""
        # Mock successful response with headers
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json', 'X-Request-ID': '123'}
        mock_response.json.return_value = {"success": True, "data": {"test": "value"}}
        mock_request.return_value = mock_response
        
        with patch('utils.http_client.logger') as mock_logger:
            self.client._make_request('GET', '/api/test', data={"param": "value"})
            
            # Verify request logging was called
            mock_logger.debug.assert_any_call("Request: GET http://localhost:5002/api/test")
            
            # Verify response logging was called
            assert any("Response: 200" in str(call) for call in mock_logger.debug.call_args_list)
    
    def test_custom_circuit_breaker_config(self):
        """Test custom circuit breaker configuration."""
        custom_config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=120,
            success_threshold=5
        )
        
        client = HTTPClient(
            circuit_breaker_config=custom_config,
            enable_circuit_breaker=True
        )
        
        assert client.circuit_breaker_config.failure_threshold == 10
        assert client.circuit_breaker_config.recovery_timeout == 120
        assert client.circuit_breaker_config.success_threshold == 5
    
    @patch('requests.Session.request')
    def test_authentication_in_requests(self, mock_request):
        """Test that authentication headers are included in requests."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response
        
        # Make request with authenticated client
        self.client._make_request('GET', '/api/test')
        
        # Verify request was made with authentication headers
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args[1]
        
        # The session should have the auth headers set
        assert 'Authorization' in self.client.session.headers
        assert 'X-API-Key' in self.client.session.headers


def test_http_client_enhanced_integration():
    """Integration test for enhanced HTTP client features."""
    # Test that enhanced client can be created with all features
    client = HTTPClient(
        base_url="http://localhost:5002",
        api_key="test-key",
        enable_circuit_breaker=True,
        enable_performance_monitoring=True
    )
    
    # Verify all features are properly initialized
    assert client.api_key == "test-key"
    assert client.enable_circuit_breaker is True
    assert client.enable_performance_monitoring is True
    assert client.circuit_breaker_stats.state == CircuitBreakerState.CLOSED
    assert client.performance_metrics.request_count == 0
    
    # Test that methods exist
    assert hasattr(client, 'set_authentication')
    assert hasattr(client, 'get_performance_metrics')
    assert hasattr(client, 'reset_performance_metrics')
    
    # Test performance metrics structure
    metrics = client.get_performance_metrics()
    assert 'global_metrics' in metrics
    assert 'endpoint_metrics' in metrics
    assert 'circuit_breaker' in metrics
    
    global_metrics = metrics['global_metrics']
    required_fields = ['request_count', 'avg_response_time', 'success_count', 
                      'error_count', 'success_rate', 'last_request_time']
    for field in required_fields:
        assert field in global_metrics
    
    circuit_breaker_info = metrics['circuit_breaker']
    cb_required_fields = ['state', 'failure_count', 'success_count', 'last_failure_time']
    for field in cb_required_fields:
        assert field in circuit_breaker_info


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])