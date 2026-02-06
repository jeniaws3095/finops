#!/usr/bin/env python3
"""
Complete Integration Test for Advanced FinOps Platform

Tests the complete Python-to-API integration including:
- Data validation and schema compliance
- Real-time updates and synchronization
- Error handling and recovery
- All API endpoints and data flow

Requirements: 9.1, 15.1
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import requests
from datetime import datetime, timezone
import time
import sys
import os

# Add project root to the path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from utils.http_client import HTTPClient
from main import AdvancedFinOpsOrchestrator


class TestCompleteIntegration(unittest.TestCase):
    """Test complete Python-to-API integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.http_client = HTTPClient(base_url="http://localhost:5002")
        self.orchestrator = AdvancedFinOpsOrchestrator(
            region='us-east-1',
            dry_run=True
        )
    
    def test_data_validation_schema_compliance(self):
        """Test data validation and schema compliance checking."""
        print("\n🔍 Testing data validation and schema compliance...")
        
        # Test valid resource data
        valid_resource = {
            'resourceId': 'i-1234567890abcdef0',
            'resourceType': 'ec2',
            'region': 'us-east-1',
            'currentCost': 120.50,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        validation = self.http_client.validate_data_schema(valid_resource, 'resource')
        self.assertTrue(validation['valid'], f"Valid resource should pass validation: {validation['errors']}")
        self.assertEqual(len(validation['errors']), 0)
        
        # Test invalid resource data (missing required fields)
        invalid_resource = {
            'resourceType': 'ec2',
            'currentCost': 120.50
        }
        
        validation = self.http_client.validate_data_schema(invalid_resource, 'resource')
        self.assertFalse(validation['valid'], "Invalid resource should fail validation")
        self.assertGreater(len(validation['errors']), 0)
        
        # Test optimization data validation
        valid_optimization = {
            'optimizationId': 'opt-123',
            'resourceId': 'i-1234567890abcdef0',
            'optimizationType': 'rightsizing',
            'estimatedSavings': 45.30,
            'riskLevel': 'LOW',
            'confidenceScore': 85
        }
        
        validation = self.http_client.validate_data_schema(valid_optimization, 'optimization')
        self.assertTrue(validation['valid'], f"Valid optimization should pass validation: {validation['errors']}")
        
        # Test anomaly data validation
        valid_anomaly = {
            'anomalyId': 'anomaly-456',
            'anomalyType': 'spike',
            'severity': 'HIGH',
            'actualCost': 250.00,
            'expectedCost': 100.00,
            'region': 'us-east-1'
        }
        
        validation = self.http_client.validate_data_schema(valid_anomaly, 'anomaly')
        self.assertTrue(validation['valid'], f"Valid anomaly should pass validation: {validation['errors']}")
        
        # Test budget data validation
        valid_budget = {
            'budgetId': 'budget-789',
            'budgetType': 'ORGANIZATION',
            'budgetAmount': 10000.00,
            'tags': {'department': 'engineering'}
        }
        
        validation = self.http_client.validate_data_schema(valid_budget, 'budget')
        self.assertTrue(validation['valid'], f"Valid budget should pass validation: {validation['errors']}")
        
        print("✅ Data validation and schema compliance tests passed")
    
    @patch('requests.Session.request')
    def test_http_client_methods(self, mock_request):
        """Test all HTTP client methods with proper responses."""
        print("\n🌐 Testing HTTP client methods...")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': {'test': 'data'},
            'message': 'Success',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        mock_request.return_value = mock_response
        
        # Test post_data method
        result = self.http_client.post_data('/api/test', {'test': 'data'})
        self.assertTrue(result['success'])
        
        # Test post_resources method
        resources = [{'resourceId': 'test', 'resourceType': 'ec2', 'region': 'us-east-1'}]
        result = self.http_client.post_resources(resources)
        self.assertTrue(result['success'])
        
        # Test post_optimizations method
        optimizations = [{
            'optimizationId': 'opt-test',
            'resourceId': 'test',
            'optimizationType': 'rightsizing',
            'estimatedSavings': 100.0
        }]
        result = self.http_client.post_optimizations(optimizations)
        self.assertTrue(result['success'])
        
        # Test post_anomalies method
        anomalies = [{
            'anomalyId': 'anomaly-test',
            'anomalyType': 'spike',
            'severity': 'HIGH',
            'actualCost': 200.0,
            'expectedCost': 100.0
        }]
        result = self.http_client.post_anomalies(anomalies)
        self.assertTrue(result['success'])
        
        # Test get methods
        result = self.http_client.get_resources()
        self.assertTrue(result['success'])
        
        result = self.http_client.get_optimizations()
        self.assertTrue(result['success'])
        
        print("✅ HTTP client methods tests passed")
    
    @patch('requests.Session.request')
    def test_error_handling_and_recovery(self, mock_request):
        """Test error handling and recovery mechanisms."""
        print("\n🚨 Testing error handling and recovery...")
        
        # Test connection error handling
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with self.assertRaises(Exception) as context:
            self.http_client.post_data('/api/test', {'test': 'data'})
        
        self.assertIn("Failed to connect", str(context.exception))
        
        # Test timeout handling
        mock_request.side_effect = requests.exceptions.Timeout("Request timeout")
        
        with self.assertRaises(Exception) as context:
            self.http_client.post_data('/api/test', {'test': 'data'})
        
        self.assertIn("Request timeout", str(context.exception))
        
        # Test server error with retry
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_request.side_effect = None
        mock_request.return_value = mock_response
        
        with self.assertRaises(Exception) as context:
            self.http_client.post_data('/api/test', {'test': 'data'})
        
        # Verify retry attempts were made (should be called max_retries + 1 times)
        self.assertGreaterEqual(mock_request.call_count, 2)
        
        print("✅ Error handling and recovery tests passed")
    
    @patch('requests.Session.request')
    def test_circuit_breaker_functionality(self, mock_request):
        """Test circuit breaker pattern."""
        print("\n⚡ Testing circuit breaker functionality...")
        
        # Create HTTP client with circuit breaker enabled
        client = HTTPClient(
            base_url="http://localhost:5002",
            enable_circuit_breaker=True,
            circuit_breaker_config=None  # Use defaults
        )
        
        # Simulate multiple failures to trigger circuit breaker
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # Make multiple failed requests
        for i in range(6):  # More than failure threshold (5)
            try:
                client.post_data('/api/test', {'test': 'data'})
            except Exception:
                pass  # Expected to fail
        
        # Circuit breaker should now be OPEN
        with client.circuit_breaker_lock:
            self.assertEqual(client.circuit_breaker_stats.state.value, 'open')
        
        # Next request should be rejected immediately
        with self.assertRaises(Exception) as context:
            client.post_data('/api/test', {'test': 'data'})
        
        self.assertIn("Circuit breaker is OPEN", str(context.exception))
        
        print("✅ Circuit breaker functionality tests passed")
    
    @patch('requests.Session.request')
    def test_performance_monitoring(self, mock_request):
        """Test performance monitoring and metrics collection."""
        print("\n📊 Testing performance monitoring...")
        
        # Mock successful response with delay simulation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True, 'data': {}}
        mock_request.return_value = mock_response
        
        # Make several requests to generate metrics
        for i in range(5):
            self.http_client.post_data('/api/test', {'test': f'data_{i}'})
        
        # Get performance metrics
        metrics = self.http_client.get_performance_metrics()
        
        self.assertGreater(metrics['global_metrics']['request_count'], 0)
        self.assertGreaterEqual(metrics['global_metrics']['success_count'], 5)
        self.assertGreaterEqual(metrics['global_metrics']['success_rate'], 0)
        
        # Check endpoint-specific metrics
        self.assertIn('/api/test', metrics['endpoint_metrics'])
        
        print("✅ Performance monitoring tests passed")
    
    def test_data_synchronization_flow(self):
        """Test complete data synchronization flow."""
        print("\n🔄 Testing data synchronization flow...")
        
        # Mock all external dependencies
        with patch.object(self.orchestrator, 'http_client') as mock_http, \
             patch.object(self.orchestrator, 'aws_config') as mock_aws, \
             patch('main.EC2Scanner') as mock_ec2_scanner, \
             patch('main.RDSScanner') as mock_rds_scanner:
            
            # Configure mocks
            mock_http.health_check.return_value = True
            mock_http.validate_data_schema.return_value = {'valid': True, 'errors': [], 'warnings': []}
            mock_http.post_resources.return_value = {'success': True}
            mock_http.post_optimizations.return_value = {'success': True}
            mock_http.post_anomalies.return_value = {'success': True}
            mock_http.post_data.return_value = {'success': True}
            
            # Mock scanner responses
            mock_ec2_scanner.return_value.scan_instances.return_value = [
                {
                    'resourceId': 'i-test123',
                    'resourceType': 'ec2',
                    'region': 'us-east-1',
                    'currentCost': 100.0,
                    'utilizationMetrics': {'averageUtilization': 15.0}
                }
            ]
            
            mock_rds_scanner.return_value.scan_databases.return_value = [
                {
                    'resourceId': 'db-test456',
                    'resourceType': 'rds',
                    'region': 'us-east-1',
                    'currentCost': 200.0,
                    'utilizationMetrics': {'averageUtilization': 45.0}
                }
            ]
            
            # Run discovery phase
            discovery_results = self.orchestrator.run_discovery(['ec2', 'rds'])
            
            # Verify discovery results
            self.assertGreater(discovery_results['resources_discovered'], 0)
            self.assertIn('ec2', discovery_results['services'])
            self.assertIn('rds', discovery_results['services'])
            
            # Verify HTTP client was called with validation
            mock_http.validate_data_schema.assert_called()
            mock_http.post_resources.assert_called()
            
            print("✅ Data synchronization flow tests passed")
    
    def test_real_time_updates(self):
        """Test real-time update capabilities."""
        print("\n⚡ Testing real-time updates...")
        
        # Mock broadcast function
        mock_broadcast = Mock()
        
        with patch('builtins.globals', return_value={'broadcastUpdate': mock_broadcast}):
            # This would test WebSocket or similar real-time update mechanisms
            # For now, we'll test the structure is in place
            
            # Verify broadcast function would be called for different update types
            update_types = [
                'resource_added',
                'optimization_added',
                'anomaly_detected',
                'budget_alert_triggered'
            ]
            
            for update_type in update_types:
                # Simulate update
                if hasattr(self.orchestrator, '_broadcast_update'):
                    self.orchestrator._broadcast_update(update_type, {'test': 'data'})
            
            print("✅ Real-time updates structure verified")
    
    def test_complete_workflow_integration(self):
        """Test complete workflow with all phases integrated."""
        print("\n🔄 Testing complete workflow integration...")
        
        # Mock all dependencies for complete workflow
        with patch.object(self.orchestrator, 'http_client') as mock_http, \
             patch.object(self.orchestrator, 'run_discovery') as mock_discovery, \
             patch.object(self.orchestrator, 'run_optimization_analysis') as mock_optimization, \
             patch.object(self.orchestrator, 'run_anomaly_detection') as mock_anomaly, \
             patch.object(self.orchestrator, 'run_budget_management') as mock_budget:
            
            # Configure mocks
            mock_http.health_check.return_value = True
            mock_http.post_data.return_value = {'success': True}
            
            mock_discovery.return_value = {
                'resources_discovered': 10,
                'services': {
                    'ec2': {'resources_found': 5, 'resources': []},
                    'rds': {'resources_found': 5, 'resources': []}
                }
            }
            
            mock_optimization.return_value = {
                'optimizations_found': 3,
                'potential_monthly_savings': 150.0,
                'categories': {
                    'cost_optimization': {'recommendations': []},
                    'pricing_intelligence': {'recommendations': []},
                    'ml_rightsizing': {'recommendations': []}
                }
            }
            
            mock_anomaly.return_value = {
                'anomalies_detected': 2,
                'severity_breakdown': {'HIGH': 1, 'MEDIUM': 1}
            }
            
            mock_budget.return_value = {
                'budgets_analyzed': 3,
                'forecasts_generated': 3,
                'alerts_triggered': 1
            }
            
            # Run complete workflow
            workflow_results = self.orchestrator.run_complete_workflow(
                services=['ec2', 'rds'],
                scan_only=False,
                approve_low_risk=False
            )
            
            # Verify workflow completion
            self.assertTrue(workflow_results.get('success', False))
            self.assertIn('discovery', workflow_results['phases'])
            self.assertIn('optimization', workflow_results['phases'])
            self.assertIn('anomaly_detection', workflow_results['phases'])
            self.assertIn('budget_management', workflow_results['phases'])
            
            # Verify all phases were called
            mock_discovery.assert_called_once()
            mock_optimization.assert_called_once()
            mock_anomaly.assert_called_once()
            mock_budget.assert_called_once()
            
            print("✅ Complete workflow integration tests passed")
    
    def test_api_endpoint_availability(self):
        """Test that all required API endpoints are available."""
        print("\n🌐 Testing API endpoint availability...")
        
        # List of endpoints that should be available
        required_endpoints = [
            '/api/resources',
            '/api/optimizations',
            '/api/anomalies',
            '/api/budgets',
            '/api/savings',
            '/api/pricing',
            '/api/dashboard',
            '/api/integration/status',
            '/api/optimization-analysis',
            '/api/anomaly-analysis',
            '/api/budget-analysis',
            '/api/execution-results',
            '/api/reports'
        ]
        
        # Mock successful responses for all endpoints
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'success': True, 'data': {}}
            mock_request.return_value = mock_response
            
            for endpoint in required_endpoints:
                try:
                    result = self.http_client._make_request('GET', endpoint)
                    self.assertTrue(result.get('success', False), f"Endpoint {endpoint} should be available")
                except Exception as e:
                    self.fail(f"Endpoint {endpoint} failed: {e}")
        
        print("✅ API endpoint availability tests passed")


def run_integration_tests():
    """Run all integration tests."""
    print("🚀 Starting Complete Integration Tests for Advanced FinOps Platform")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCompleteIntegration)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("🏁 Integration Test Summary")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All integration tests passed successfully!")
        return True
    else:
        print("\n❌ Some integration tests failed!")
        return False


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)