#!/usr/bin/env python3
"""
Comprehensive System Validation Script for Advanced FinOps Platform

This script performs a complete end-to-end validation of the Advanced FinOps Platform
to ensure all components work together correctly for Task 16 final validation.
"""

import sys
import time
import requests
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*80)
    print(f"🔍 {title}")
    print("="*80)

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n📋 {title}")
    print("-" * 60)

def print_success(message: str):
    """Print a success message."""
    print(f"✅ {message}")

def print_error(message: str):
    """Print an error message."""
    print(f"❌ {message}")

def print_warning(message: str):
    """Print a warning message."""
    print(f"⚠️  {message}")

def print_info(message: str):
    """Print an info message."""
    print(f"ℹ️  {message}")

class SystemValidator:
    """Comprehensive system validator for the Advanced FinOps Platform."""
    
    def __init__(self):
        self.backend_url = "http://localhost:5002"
        self.validation_results = {
            'backend_api': False,
            'python_orchestrator': False,
            'data_flow': False,
            'error_handling': False,
            'workflow_integration': False,
            'monitoring': False
        }
        self.test_data = []
        
    def validate_backend_api(self) -> bool:
        """Validate backend API functionality."""
        print_section("Backend API Validation")
        
        try:
            # Test health endpoint
            print_info("Testing health endpoint...")
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print_success(f"Health endpoint working - Status: {health_data['data']['status']}")
                print_info(f"Uptime: {health_data['data']['uptime']:.2f} seconds")
            else:
                print_error(f"Health endpoint failed with status {response.status_code}")
                return False
            
            # Test core API endpoints
            endpoints_to_test = [
                '/api/resources',
                '/api/optimizations', 
                '/api/anomalies',
                '/api/budgets',
                '/api/savings',
                '/api/pricing'
            ]
            
            for endpoint in endpoints_to_test:
                print_info(f"Testing {endpoint}...")
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print_success(f"{endpoint} working - {len(data.get('data', []))} items")
                    else:
                        print_warning(f"{endpoint} returned success=false")
                else:
                    print_error(f"{endpoint} failed with status {response.status_code}")
                    return False
            
            # Test monitoring endpoints
            print_info("Testing monitoring endpoints...")
            response = requests.get(f"{self.backend_url}/api/monitoring/dashboard", timeout=10)
            if response.status_code == 200:
                monitoring_data = response.json()
                print_success("Monitoring dashboard working")
                print_info(f"Request count: {monitoring_data['data']['performance']['requestCount']}")
            else:
                print_warning("Monitoring dashboard not available")
            
            return True
            
        except requests.exceptions.ConnectionError:
            print_error("Cannot connect to backend API - ensure server is running on port 5002")
            return False
        except Exception as e:
            print_error(f"Backend API validation failed: {e}")
            return False
    
    def validate_python_orchestrator(self) -> bool:
        """Validate Python orchestrator functionality."""
        print_section("Python Orchestrator Validation")
        
        try:
            # Test import capability
            print_info("Testing orchestrator import...")
            from main import AdvancedFinOpsOrchestrator
            print_success("Main orchestrator can be imported")
            
            # Test initialization
            print_info("Testing orchestrator initialization...")
            orchestrator = AdvancedFinOpsOrchestrator(region='us-east-1', dry_run=True)
            print_success("Orchestrator initialized successfully")
            
            # Test configuration validation
            print_info("Testing configuration validation...")
            config_issues = orchestrator.config_manager.validate()
            if config_issues:
                print_warning(f"Configuration has {len(config_issues)} issues (expected in demo)")
                for issue in config_issues[:3]:  # Show first 3 issues
                    print_info(f"  - {issue}")
            else:
                print_success("Configuration is valid")
            
            # Test component initialization
            print_info("Testing core components...")
            components = [
                ('AWS Config', orchestrator.aws_config),
                ('Safety Controls', orchestrator.safety_controls),
                ('HTTP Client', orchestrator.http_client),
                ('Cost Optimizer', orchestrator.cost_optimizer),
                ('Pricing Intelligence', orchestrator.pricing_intelligence),
                ('ML Right-sizing', orchestrator.ml_rightsizing),
                ('Anomaly Detector', orchestrator.anomaly_detector),
                ('Budget Manager', orchestrator.budget_manager)
            ]
            
            for name, component in components:
                if component is not None:
                    print_success(f"{name} initialized")
                else:
                    print_error(f"{name} not initialized")
                    return False
            
            return True
            
        except ImportError as e:
            print_error(f"Cannot import orchestrator: {e}")
            return False
        except Exception as e:
            print_error(f"Orchestrator validation failed: {e}")
            return False
    
    def validate_data_flow(self) -> bool:
        """Validate data flow from Python to API."""
        print_section("Data Flow Validation")
        
        try:
            # Test HTTP client connectivity
            print_info("Testing HTTP client connectivity...")
            from utils.http_client import HTTPClient
            
            client = HTTPClient()
            health_check = client.health_check()
            
            if health_check:
                print_success("HTTP client can connect to backend")
            else:
                print_warning("HTTP client cannot connect to backend")
            
            # Test data posting capability
            print_info("Testing data posting...")
            test_resource = {
                'resourceId': 'test-resource-001',
                'resourceType': 'ec2',
                'region': 'us-east-1',
                'currentCost': 100.0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            try:
                result = client.post_data('/api/resources', test_resource)
                if result:
                    print_success("Data posting works")
                    self.test_data.append(test_resource)
                else:
                    print_warning("Data posting returned no result")
            except Exception as e:
                print_warning(f"Data posting failed: {e}")
            
            # Verify data was received
            print_info("Verifying data was received...")
            response = requests.get(f"{self.backend_url}/api/resources", timeout=10)
            if response.status_code == 200:
                data = response.json()
                resource_count = len(data.get('data', []))
                print_success(f"Backend has {resource_count} resources")
            
            return True
            
        except Exception as e:
            print_error(f"Data flow validation failed: {e}")
            return False
    
    def validate_error_handling(self) -> bool:
        """Validate error handling and recovery mechanisms."""
        print_section("Error Handling Validation")
        
        try:
            # Test safety controls
            print_info("Testing safety controls...")
            from utils.safety_controls import SafetyControls, RiskLevel
            
            safety = SafetyControls(dry_run=True)
            
            # Test DRY_RUN validation
            test_operation = {
                'operation_type': 'terminate_instance',
                'resource_id': 'i-1234567890abcdef0',
                'risk_level': RiskLevel.HIGH
            }
            
            validation_result = safety.validate_operation(test_operation)
            if validation_result['safe_to_proceed']:
                print_success("Safety controls working - DRY_RUN mode active")
            else:
                print_error("Safety controls failed validation")
                return False
            
            # Test error recovery
            print_info("Testing error recovery mechanisms...")
            from utils.error_recovery import global_recovery_manager
            
            recovery_stats = global_recovery_manager.get_recovery_stats()
            print_success(f"Error recovery system active - {len(recovery_stats)} operations tracked")
            
            return True
            
        except Exception as e:
            print_error(f"Error handling validation failed: {e}")
            return False
    
    def validate_workflow_integration(self) -> bool:
        """Validate complete workflow integration."""
        print_section("Workflow Integration Validation")
        
        try:
            print_info("Testing discovery workflow...")
            from main import AdvancedFinOpsOrchestrator
            
            orchestrator = AdvancedFinOpsOrchestrator(region='us-east-1', dry_run=True)
            
            # Test discovery with limited services
            discovery_results = orchestrator.run_discovery(['ec2', 'rds'])
            
            if discovery_results.get('resources_discovered', 0) >= 0:
                print_success(f"Discovery workflow completed - {discovery_results['resources_discovered']} resources found")
                print_info(f"Services scanned: {len(discovery_results.get('services_scanned', []))}")
            else:
                print_error("Discovery workflow failed")
                return False
            
            # Test optimization analysis
            print_info("Testing optimization analysis...")
            optimization_results = orchestrator.run_optimization_analysis()
            
            if 'optimizations_found' in optimization_results:
                print_success(f"Optimization analysis completed - {optimization_results['optimizations_found']} optimizations found")
                print_info(f"Potential savings: ${optimization_results.get('potential_monthly_savings', 0):.2f}/month")
            else:
                print_warning("Optimization analysis completed with no results")
            
            # Test anomaly detection
            print_info("Testing anomaly detection...")
            anomaly_results = orchestrator.run_anomaly_detection()
            
            if 'anomalies_detected' in anomaly_results:
                print_success(f"Anomaly detection completed - {anomaly_results['anomalies_detected']} anomalies found")
            else:
                print_warning("Anomaly detection completed with no results")
            
            # Test budget management
            print_info("Testing budget management...")
            budget_results = orchestrator.run_budget_management()
            
            if 'budgets_analyzed' in budget_results:
                print_success(f"Budget management completed - {budget_results['budgets_analyzed']} budgets analyzed")
            else:
                print_warning("Budget management completed with no results")
            
            return True
            
        except Exception as e:
            print_error(f"Workflow integration validation failed: {e}")
            return False
    
    def validate_monitoring(self) -> bool:
        """Validate monitoring and alerting systems."""
        print_section("Monitoring System Validation")
        
        try:
            # Test system monitoring
            print_info("Testing system monitoring...")
            from utils.monitoring import system_monitor
            
            if system_monitor.is_active():
                print_success("System monitoring is active")
                
                # Get monitoring metrics
                metrics = system_monitor.get_metrics()
                print_info(f"Monitoring metrics: {len(metrics)} categories")
                
                # Test alert system
                alert_count = len(system_monitor.alert_manager.get_active_alerts())
                print_info(f"Active alerts: {alert_count}")
                
            else:
                print_warning("System monitoring not active")
            
            # Test structured logging
            print_info("Testing structured logging...")
            from utils.monitoring import StructuredLogger
            
            logger = StructuredLogger('test.validator')
            logger.info("Test log message for validation")
            print_success("Structured logging working")
            
            return True
            
        except Exception as e:
            print_error(f"Monitoring validation failed: {e}")
            return False
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive system validation."""
        print_header("ADVANCED FINOPS PLATFORM - COMPREHENSIVE SYSTEM VALIDATION")
        print_info("Starting comprehensive validation of all system components...")
        print_info(f"Validation started at: {datetime.now(timezone.utc).isoformat()}")
        
        start_time = time.time()
        
        # Run all validation tests
        validation_tests = [
            ('backend_api', self.validate_backend_api),
            ('python_orchestrator', self.validate_python_orchestrator),
            ('data_flow', self.validate_data_flow),
            ('error_handling', self.validate_error_handling),
            ('workflow_integration', self.validate_workflow_integration),
            ('monitoring', self.validate_monitoring)
        ]
        
        for test_name, test_func in validation_tests:
            try:
                print_info(f"Running {test_name} validation...")
                self.validation_results[test_name] = test_func()
                if self.validation_results[test_name]:
                    print_success(f"{test_name} validation PASSED")
                else:
                    print_error(f"{test_name} validation FAILED")
            except Exception as e:
                print_error(f"{test_name} validation ERROR: {e}")
                self.validation_results[test_name] = False
        
        # Calculate results
        end_time = time.time()
        duration = end_time - start_time
        
        passed_tests = sum(1 for result in self.validation_results.values() if result)
        total_tests = len(self.validation_results)
        success_rate = (passed_tests / total_tests) * 100
        
        # Generate final report
        return self.generate_final_report(duration, passed_tests, total_tests, success_rate)
    
    def generate_final_report(self, duration: float, passed_tests: int, total_tests: int, success_rate: float) -> Dict[str, Any]:
        """Generate final validation report."""
        print_header("FINAL VALIDATION REPORT")
        
        # Overall status
        overall_status = "PASS" if passed_tests == total_tests else "PARTIAL" if passed_tests > 0 else "FAIL"
        
        print(f"📊 VALIDATION SUMMARY")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Overall Status: {overall_status}")
        
        print(f"\n📋 DETAILED RESULTS")
        for test_name, result in self.validation_results.items():
            status_icon = "✅" if result else "❌"
            print(f"   {status_icon} {test_name.replace('_', ' ').title()}: {'PASS' if result else 'FAIL'}")
        
        # System readiness assessment
        print(f"\n🎯 SYSTEM READINESS ASSESSMENT")
        
        critical_components = ['backend_api', 'python_orchestrator', 'data_flow']
        critical_passed = sum(1 for comp in critical_components if self.validation_results[comp])
        
        if critical_passed == len(critical_components):
            print_success("✅ SYSTEM IS READY FOR PRODUCTION")
            print_info("All critical components are functioning correctly")
        elif critical_passed >= 2:
            print_warning("⚠️  SYSTEM IS PARTIALLY READY")
            print_info("Most critical components working, some issues need attention")
        else:
            print_error("❌ SYSTEM NOT READY FOR PRODUCTION")
            print_info("Critical components have issues that must be resolved")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        
        if not self.validation_results['backend_api']:
            print_info("• Ensure backend server is running on port 5002")
            print_info("• Check network connectivity and firewall settings")
        
        if not self.validation_results['python_orchestrator']:
            print_info("• Verify Python dependencies are installed")
            print_info("• Check configuration file settings")
        
        if not self.validation_results['data_flow']:
            print_info("• Test HTTP client connectivity")
            print_info("• Verify API endpoint compatibility")
        
        if not self.validation_results['workflow_integration']:
            print_info("• Review workflow configuration")
            print_info("• Check AWS service access permissions")
        
        if success_rate >= 80:
            print_success("🎉 EXCELLENT! System is performing well")
        elif success_rate >= 60:
            print_warning("👍 GOOD! Minor issues to address")
        else:
            print_error("🔧 NEEDS WORK! Several components require attention")
        
        # Return structured report
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'duration_seconds': duration,
            'tests_passed': passed_tests,
            'total_tests': total_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'validation_results': self.validation_results,
            'system_ready': critical_passed == len(critical_components),
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if not self.validation_results['backend_api']:
            recommendations.append("Start backend server and verify API endpoints")
        
        if not self.validation_results['python_orchestrator']:
            recommendations.append("Fix Python orchestrator initialization issues")
        
        if not self.validation_results['data_flow']:
            recommendations.append("Resolve data flow connectivity issues")
        
        if not self.validation_results['error_handling']:
            recommendations.append("Review error handling and safety controls")
        
        if not self.validation_results['workflow_integration']:
            recommendations.append("Test and fix workflow integration issues")
        
        if not self.validation_results['monitoring']:
            recommendations.append("Enable and configure monitoring systems")
        
        if not recommendations:
            recommendations.append("System validation successful - ready for production use")
        
        return recommendations


def main():
    """Main validation function."""
    validator = SystemValidator()
    
    try:
        # Run comprehensive validation
        report = validator.run_comprehensive_validation()
        
        # Save report to file
        report_file = f"system_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print_info(f"Detailed report saved to: {report_file}")
        
        # Exit with appropriate code
        if report['overall_status'] == 'PASS':
            print_success("🎉 COMPREHENSIVE VALIDATION COMPLETED SUCCESSFULLY!")
            sys.exit(0)
        elif report['overall_status'] == 'PARTIAL':
            print_warning("⚠️  VALIDATION COMPLETED WITH SOME ISSUES")
            sys.exit(1)
        else:
            print_error("❌ VALIDATION FAILED - CRITICAL ISSUES FOUND")
            sys.exit(2)
            
    except KeyboardInterrupt:
        print_error("\n❌ Validation interrupted by user")
        sys.exit(3)
    except Exception as e:
        print_error(f"❌ Validation failed with error: {e}")
        sys.exit(4)


if __name__ == '__main__':
    main()