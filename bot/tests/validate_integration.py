#!/usr/bin/env python3
"""
Integration Validation Script for Advanced FinOps Platform

This script validates the complete Python-to-API integration by:
1. Testing data validation and schema compliance
2. Validating real-time data flow and synchronization
3. Testing error handling and recovery mechanisms
4. Verifying all API endpoints are working correctly
5. Testing complete workflow integration

Requirements: 9.1, 15.1
"""

import requests
import json
import time
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List

class IntegrationValidator:
    """Validates the complete Python-to-API integration."""
    
    def __init__(self, base_url: str = "http://localhost:5002"):
        """Initialize the validator."""
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'FinOps-Integration-Validator/1.0'
        })
        
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        
        if success:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {message}")
    
    def test_backend_health(self) -> bool:
        """Test backend server health."""
        print("\n🏥 Testing Backend Health...")
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Backend Health Check", data.get('success', False), 
                             f"Server is running on port {data.get('data', {}).get('port', 'unknown')}")
                return True
            else:
                self.log_test("Backend Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Connection error: {e}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test all required API endpoints."""
        print("\n🌐 Testing API Endpoints...")
        
        endpoints = [
            ('/api/resources', 'GET'),
            ('/api/resources', 'POST'),
            ('/api/optimizations', 'GET'),
            ('/api/optimizations', 'POST'),
            ('/api/anomalies', 'GET'),
            ('/api/anomalies', 'POST'),
            ('/api/budgets', 'GET'),
            ('/api/budgets', 'POST'),
            ('/api/savings', 'GET'),
            ('/api/pricing', 'GET'),
            ('/api/integration/status', 'GET'),
            ('/api/optimization-analysis', 'POST'),
            ('/api/anomaly-analysis', 'POST'),
            ('/api/budget-analysis', 'POST'),
            ('/api/execution-results', 'POST'),
            ('/api/reports', 'POST')
        ]
        
        all_passed = True
        
        for endpoint, method in endpoints:
            try:
                if method == 'GET':
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                else:  # POST
                    test_data = {'test': True, 'timestamp': datetime.now(timezone.utc).isoformat()}
                    response = self.session.post(f"{self.base_url}{endpoint}", 
                                               json=test_data, timeout=5)
                
                success = response.status_code in [200, 201, 400]  # 400 is OK for invalid test data
                self.log_test(f"{method} {endpoint}", success, 
                             f"HTTP {response.status_code}")
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"{method} {endpoint}", False, f"Error: {e}")
                all_passed = False
        
        return all_passed
    
    def test_data_validation(self) -> bool:
        """Test data validation and schema compliance."""
        print("\n🔍 Testing Data Validation...")
        
        # Test valid resource data
        valid_resource = {
            'resourceId': 'i-test123456789abcdef',
            'resourceType': 'ec2',
            'region': 'us-east-1',
            'currentCost': 125.50,
            'utilizationMetrics': {
                'averageUtilization': 15.5,
                'maxUtilization': 45.2,
                'minUtilization': 2.1
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/resources", 
                                       json=valid_resource, timeout=5)
            success = response.status_code in [200, 201]
            self.log_test("Valid Resource Data", success, 
                         f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Valid Resource Data", False, f"Error: {e}")
            return False
        
        # Test invalid resource data (missing required fields)
        invalid_resource = {
            'resourceType': 'ec2',
            'currentCost': 125.50
            # Missing resourceId and region
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/resources", 
                                       json=invalid_resource, timeout=5)
            success = response.status_code == 400  # Should reject invalid data
            self.log_test("Invalid Resource Data Rejection", success, 
                         f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Resource Data Rejection", False, f"Error: {e}")
            return False
        
        # Test optimization data
        valid_optimization = {
            'optimizationId': 'opt-test123',
            'resourceId': 'i-test123456789abcdef',
            'optimizationType': 'rightsizing',
            'estimatedSavings': 45.30,
            'riskLevel': 'LOW',
            'confidenceScore': 85,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/optimizations", 
                                       json=valid_optimization, timeout=5)
            success = response.status_code in [200, 201]
            self.log_test("Valid Optimization Data", success, 
                         f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Valid Optimization Data", False, f"Error: {e}")
            return False
        
        return True
    
    def test_data_flow(self) -> bool:
        """Test complete data flow from Python to API."""
        print("\n🔄 Testing Data Flow...")
        
        # Test resource posting and retrieval
        test_resource = {
            'resourceId': f'i-flow-test-{int(time.time())}',
            'resourceType': 'ec2',
            'region': 'us-east-1',
            'currentCost': 99.99,
            'state': 'running',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Post resource
            post_response = self.session.post(f"{self.base_url}/api/resources", 
                                            json=test_resource, timeout=5)
            post_success = post_response.status_code in [200, 201]
            self.log_test("Resource Data Post", post_success, 
                         f"HTTP {post_response.status_code}")
            
            if not post_success:
                return False
            
            # Retrieve resources
            get_response = self.session.get(f"{self.base_url}/api/resources", timeout=5)
            get_success = get_response.status_code == 200
            
            if get_success:
                data = get_response.json()
                resources = data.get('data', [])
                found = any(r.get('resourceId') == test_resource['resourceId'] for r in resources)
                self.log_test("Resource Data Retrieval", found, 
                             f"Found {len(resources)} resources, test resource {'found' if found else 'not found'}")
            else:
                self.log_test("Resource Data Retrieval", False, 
                             f"HTTP {get_response.status_code}")
                return False
            
        except Exception as e:
            self.log_test("Data Flow Test", False, f"Error: {e}")
            return False
        
        return True
    
    def test_integration_endpoints(self) -> bool:
        """Test integration-specific endpoints."""
        print("\n🔗 Testing Integration Endpoints...")
        
        # Test optimization analysis endpoint
        analysis_data = {
            'summary': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'region': 'us-east-1',
                'optimizations_found': 5,
                'potential_monthly_savings': 250.75,
                'categories': {
                    'cost_optimization': {'recommendations': []},
                    'pricing_intelligence': {'recommendations': []},
                    'ml_rightsizing': {'recommendations': []}
                }
            },
            'source': 'integration-test'
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/optimization-analysis", 
                                       json=analysis_data, timeout=5)
            success = response.status_code in [200, 201]
            self.log_test("Optimization Analysis Endpoint", success, 
                         f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Optimization Analysis Endpoint", False, f"Error: {e}")
            return False
        
        # Test anomaly analysis endpoint
        anomaly_data = {
            'summary': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'region': 'us-east-1',
                'anomalies_detected': 2,
                'severity_breakdown': {'HIGH': 1, 'MEDIUM': 1},
                'total_cost_impact': 150.00
            },
            'source': 'integration-test'
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/anomaly-analysis", 
                                       json=anomaly_data, timeout=5)
            success = response.status_code in [200, 201]
            self.log_test("Anomaly Analysis Endpoint", success, 
                         f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Anomaly Analysis Endpoint", False, f"Error: {e}")
            return False
        
        # Test integration status endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/integration/status", timeout=5)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                status_data = data.get('data', {})
                self.log_test("Integration Status Endpoint", success, 
                             f"Health: {status_data.get('integrationHealth', 'unknown')}")
            else:
                self.log_test("Integration Status Endpoint", False, 
                             f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Integration Status Endpoint", False, f"Error: {e}")
            return False
        
        return True
    
    def test_error_handling(self) -> bool:
        """Test error handling capabilities."""
        print("\n🚨 Testing Error Handling...")
        
        # Test invalid JSON
        try:
            response = self.session.post(f"{self.base_url}/api/resources", 
                                       data="invalid json", 
                                       headers={'Content-Type': 'application/json'},
                                       timeout=5)
            success = response.status_code == 400
            self.log_test("Invalid JSON Handling", success, 
                         f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Invalid JSON Handling", False, f"Error: {e}")
            return False
        
        # Test non-existent endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/nonexistent", timeout=5)
            success = response.status_code == 404
            self.log_test("Non-existent Endpoint Handling", success, 
                         f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Non-existent Endpoint Handling", False, f"Error: {e}")
            return False
        
        return True
    
    def test_real_time_capabilities(self) -> bool:
        """Test real-time update capabilities."""
        print("\n⚡ Testing Real-time Capabilities...")
        
        # Test multiple rapid requests
        try:
            start_time = time.time()
            
            for i in range(5):
                test_data = {
                    'resourceId': f'i-realtime-{i}-{int(time.time())}',
                    'resourceType': 'ec2',
                    'region': 'us-east-1',
                    'currentCost': 10.0 + i,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                response = self.session.post(f"{self.base_url}/api/resources", 
                                           json=test_data, timeout=5)
                if response.status_code not in [200, 201]:
                    self.log_test("Real-time Data Processing", False, 
                                 f"Failed on request {i+1}")
                    return False
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.log_test("Real-time Data Processing", True, 
                         f"Processed 5 requests in {duration:.2f}s")
            
        except Exception as e:
            self.log_test("Real-time Data Processing", False, f"Error: {e}")
            return False
        
        return True
    
    def run_validation(self) -> bool:
        """Run complete integration validation."""
        print("🚀 Starting Advanced FinOps Platform Integration Validation")
        print("=" * 70)
        
        # Run all validation tests
        tests = [
            self.test_backend_health,
            self.test_api_endpoints,
            self.test_data_validation,
            self.test_data_flow,
            self.test_integration_endpoints,
            self.test_error_handling,
            self.test_real_time_capabilities
        ]
        
        all_passed = True
        
        for test in tests:
            try:
                result = test()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
                all_passed = False
        
        # Print summary
        print("\n" + "=" * 70)
        print("🏁 Integration Validation Summary")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results['errors']:
            print("\n🚨 Errors:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        if all_passed:
            print("\n🎉 All integration tests passed! Python-to-API integration is working correctly.")
        else:
            print("\n⚠️  Some integration tests failed. Please review the errors above.")
        
        return all_passed


def main():
    """Main entry point."""
    validator = IntegrationValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()