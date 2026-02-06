#!/usr/bin/env python3
"""
Test HTTP Client for Backend Communication

Tests the HTTP client functionality including:
- Data posting to API endpoints
- Error handling and retry logic
- Response validation
- Connection management

Requirements: 9.1
"""

import pytest
import requests
import json
import time
from unittest.mock import Mock, patch, MagicMock
from utils.http_client import HTTPClient


class TestHTTPClient:
    """Test suite for HTTP client functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = HTTPClient(base_url="http://localhost:5002", timeout=10, max_retries=2)
        
        # Sample test data
        self.sample_resources = [
            {
                "resourceId": "i-1234567890abcdef0",
                "resourceType": "ec2",
                "region": "us-east-1",
                "currentCost": 50.0,
                "utilizationMetrics": {"cpu": 15.5, "memory": 45.2},
                "optimizationOpportunities": ["rightsizing"],
                "timestamp": "2024-01-01T12:00:00Z"
            }
        ]
        
        self.sample_optimizations = [
            {
                "optimizationId": "opt-123",
                "resourceId": "i-1234567890abcdef0",
                "optimizationType": "rightsizing",
                "currentCost": 50.0,
                "projectedCost": 30.0,
                "estimatedSavings": 20.0,
                "confidenceScore": 85,
                "riskLevel": "LOW",
                "status": "pending",
                "approvalRequired": False,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        ]
        
        self.sample_anomalies = [
            {
                "anomalyId": "anom-456",
                "detectedAt": "2024-01-01T12:00:00Z",
                "serviceType": "ec2",
                "region": "us-east-1",
                "anomalyType": "spike",
                "severity": "HIGH",
                "baselineCost": 100.0,
                "actualCost": 250.0,
                "deviationPercentage": 150.0,
                "rootCause": "Unexpected instance scaling",
                "affectedResources": ["i-1234567890abcdef0"],
                "resolved": False
            }
        ]
        
        self.sample_forecasts = [
            {
                "forecastId": "forecast-789",
                "budgetCategory": "team",
                "budgetName": "engineering-team",
                "currentSpend": 1000.0,
                "forecastedSpend": 1200.0,
                "budgetLimit": 1500.0,
                "confidenceInterval": {"lower": 1100.0, "upper": 1300.0},
                "projectionPeriod": "monthly",
                "lastUpdated": "2024-01-01T12:00:00Z"
            }
        ]
    
    def test_client_initialization(self):
        """Test HTTP client initialization."""
        client = HTTPClient()
        assert client.base_url == "http://localhost:5002"
        assert client.timeout == 30
        assert client.max_retries == 3
        
        custom_client = HTTPClient(base_url="http://test:8080", timeout=15, max_retries=5)
        assert custom_client.base_url == "http://test:8080"
        assert custom_client.timeout == 15
        assert custom_client.max_retries == 5
    
    @patch('requests.Session.request')
    def test_successful_request(self, mock_request):
        """Test successful HTTP request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {"test": "data"},
            "message": "Success",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        mock_request.return_value = mock_response
        
        result = self.client._make_request('GET', '/api/test')
        
        assert result["success"] is True
        assert result["data"]["test"] == "data"
        mock_request.assert_called_once()
    
    @patch('requests.Session.request')
    def test_retry_logic_on_server_error(self, mock_request):
        """Test retry logic on server errors."""
        # Mock server error responses followed by success
        error_response = Mock()
        error_response.status_code = 500
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"success": True, "data": {}}
        
        mock_request.side_effect = [error_response, success_response]
        
        with patch('time.sleep'):  # Speed up test by mocking sleep
            result = self.client._make_request('GET', '/api/test')
        
        assert result["success"] is True
        assert mock_request.call_count == 2
    
    @patch('requests.Session.request')
    def test_retry_exhaustion(self, mock_request):
        """Test behavior when all retries are exhausted."""
        # Mock consistent server errors
        error_response = Mock()
        error_response.status_code = 500
        mock_request.return_value = error_response
        
        with patch('time.sleep'):  # Speed up test
            with pytest.raises(Exception, match="Server error after .* retries"):
                self.client._make_request('GET', '/api/test')
        
        # Should try max_retries + 1 times (initial + retries)
        assert mock_request.call_count == self.client.max_retries + 1
    
    @patch('requests.Session.request')
    def test_connection_error_retry(self, mock_request):
        """Test retry logic on connection errors."""
        # Mock connection error followed by success
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"success": True, "data": {}}
        
        mock_request.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            success_response
        ]
        
        with patch('time.sleep'):
            result = self.client._make_request('GET', '/api/test')
        
        assert result["success"] is True
        assert mock_request.call_count == 2
    
    @patch('requests.Session.request')
    def test_timeout_error_retry(self, mock_request):
        """Test retry logic on timeout errors."""
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"success": True, "data": {}}
        
        mock_request.side_effect = [
            requests.exceptions.Timeout("Request timeout"),
            success_response
        ]
        
        with patch('time.sleep'):
            result = self.client._make_request('GET', '/api/test')
        
        assert result["success"] is True
        assert mock_request.call_count == 2
    
    @patch('requests.Session.request')
    def test_404_error_handling(self, mock_request):
        """Test handling of 404 errors (no retry)."""
        error_response = Mock()
        error_response.status_code = 404
        mock_request.return_value = error_response
        
        with pytest.raises(Exception, match="API endpoint not found"):
            self.client._make_request('GET', '/api/nonexistent')
        
        # Should not retry on 404
        assert mock_request.call_count == 1
    
    @patch('utils.http_client.HTTPClient._make_request')
    def test_post_resources(self, mock_request):
        """Test posting resources to backend."""
        mock_request.return_value = {
            "success": True,
            "data": self.sample_resources[0],
            "message": "Resource added successfully"
        }
        
        result = self.client.post_resources(self.sample_resources)
        
        assert result["success"] is True
        # Should call _make_request once for each resource
        assert mock_request.call_count == len(self.sample_resources)
        # Check that the individual resource was posted (not wrapped in array)
        mock_request.assert_called_with('POST', '/api/resources', data=self.sample_resources[0])
    
    @patch('utils.http_client.HTTPClient._make_request')
    def test_post_optimizations(self, mock_request):
        """Test posting optimizations to backend."""
        mock_request.return_value = {
            "success": True,
            "data": self.sample_optimizations[0],
            "message": "Optimization created successfully"
        }
        
        result = self.client.post_optimizations(self.sample_optimizations)
        
        assert result["success"] is True
        # Should call _make_request once for each optimization
        assert mock_request.call_count == len(self.sample_optimizations)
        # Check that the individual optimization was posted (not wrapped in array)
        mock_request.assert_called_with('POST', '/api/optimizations', data=self.sample_optimizations[0])
    
    @patch('utils.http_client.HTTPClient._make_request')
    def test_post_anomalies(self, mock_request):
        """Test posting anomalies to backend."""
        mock_request.return_value = {
            "success": True,
            "data": self.sample_anomalies[0],
            "message": "Anomaly reported successfully"
        }
        
        result = self.client.post_anomalies(self.sample_anomalies)
        
        assert result["success"] is True
        mock_request.assert_called_once_with('POST', '/api/anomalies', data={
            'anomalies': self.sample_anomalies,
            'timestamp': mock_request.call_args[1]['data']['timestamp'],
            'source': 'finops-bot'
        })
    
    @patch('utils.http_client.HTTPClient._make_request')
    def test_post_budget_forecasts(self, mock_request):
        """Test posting budget forecasts to backend."""
        mock_request.return_value = {
            "success": True,
            "data": self.sample_forecasts[0],
            "message": "Forecast created successfully"
        }
        
        result = self.client.post_budget_forecasts(self.sample_forecasts)
        
        assert result["success"] is True
        mock_request.assert_called_once_with('POST', '/api/budgets', data={
            'forecasts': self.sample_forecasts,
            'timestamp': mock_request.call_args[1]['data']['timestamp'],
            'source': 'finops-bot'
        })
    
    @patch('utils.http_client.HTTPClient._make_request')
    def test_get_resources(self, mock_request):
        """Test getting resources from backend."""
        mock_request.return_value = {
            "success": True,
            "data": self.sample_resources,
            "message": "Retrieved 1 resources"
        }
        
        filters = {"resourceType": "ec2", "region": "us-east-1"}
        result = self.client.get_resources(filters)
        
        assert result["success"] is True
        assert len(result["data"]) == 1
        mock_request.assert_called_once_with('GET', '/api/resources', params=filters)
    
    @patch('utils.http_client.HTTPClient._make_request')
    def test_get_optimizations(self, mock_request):
        """Test getting optimizations from backend."""
        mock_request.return_value = {
            "success": True,
            "data": self.sample_optimizations,
            "message": "Retrieved 1 optimization recommendations"
        }
        
        filters = {"status": "pending", "riskLevel": "LOW"}
        result = self.client.get_optimizations(filters)
        
        assert result["success"] is True
        assert len(result["data"]) == 1
        mock_request.assert_called_once_with('GET', '/api/optimizations', params=filters)
    
    @patch('utils.http_client.HTTPClient._make_request')
    def test_approve_optimization(self, mock_request):
        """Test approving optimization."""
        mock_request.return_value = {
            "success": True,
            "data": {"optimizationId": "opt-123", "status": "approved"},
            "message": "Optimization approved successfully"
        }
        
        result = self.client.approve_optimization("opt-123", approved=True)
        
        assert result["success"] is True
        mock_request.assert_called_once_with('POST', '/api/optimizations/approve', data={
            'optimization_id': 'opt-123',
            'approved': True,
            'timestamp': mock_request.call_args[1]['data']['timestamp']
        })
    
    @patch('utils.http_client.HTTPClient._make_request')
    def test_health_check_success(self, mock_request):
        """Test successful health check."""
        mock_request.return_value = {
            "success": True,
            "data": {"status": "healthy"},
            "message": "API is healthy"
        }
        
        result = self.client.health_check()
        
        assert result is True
        mock_request.assert_called_once_with('GET', '/api/health')
    
    @patch('utils.http_client.HTTPClient._make_request')
    def test_health_check_failure(self, mock_request):
        """Test health check failure."""
        mock_request.side_effect = Exception("Connection failed")
        
        result = self.client.health_check()
        
        assert result is False
    
    def test_exponential_backoff_timing(self):
        """Test that exponential backoff timing works correctly."""
        with patch('requests.Session.request') as mock_request, \
             patch('time.sleep') as mock_sleep:
            
            # Mock consistent failures
            error_response = Mock()
            error_response.status_code = 500
            mock_request.return_value = error_response
            
            try:
                self.client._make_request('GET', '/api/test')
            except Exception:
                pass  # Expected to fail
            
            # Check that sleep was called with exponential backoff
            expected_sleeps = [2**i for i in range(self.client.max_retries)]
            actual_sleeps = [call[0][0] for call in mock_sleep.call_args_list]
            assert actual_sleeps == expected_sleeps


def test_http_client_integration():
    """Integration test to verify HTTP client works with actual backend structure."""
    # This test verifies the client is compatible with the backend API structure
    client = HTTPClient()
    
    # Test that client methods exist and have correct signatures
    assert hasattr(client, 'post_resources')
    assert hasattr(client, 'post_optimizations')
    assert hasattr(client, 'post_anomalies')
    assert hasattr(client, 'post_budget_forecasts')
    assert hasattr(client, 'get_resources')
    assert hasattr(client, 'get_optimizations')
    assert hasattr(client, 'approve_optimization')
    assert hasattr(client, 'health_check')
    
    # Test that base URL is correctly configured for Advanced FinOps Platform
    assert client.base_url == "http://localhost:5002"
    
    # Test that session headers are properly configured
    assert 'Content-Type' in client.session.headers
    assert client.session.headers['Content-Type'] == 'application/json'
    assert 'User-Agent' in client.session.headers
    assert 'AdvancedFinOps-Bot' in client.session.headers['User-Agent']


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])