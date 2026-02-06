"""
Backend Synchronization Module

Handles sending AWS resource data, optimizations, anomalies, and other
FinOps data from the Python bot to the Node.js backend API.

This enables the frontend to display real AWS data instead of mock data.
"""

import requests
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class BackendSync:
    """
    Synchronizes FinOps data with the Node.js backend API.
    """
    
    def __init__(self, backend_url: str = "http://localhost:5000", timeout: int = 30):
        """
        Initialize the backend sync client.
        
        Args:
            backend_url: Base URL of the backend API
            timeout: Request timeout in seconds
        """
        self.backend_url = backend_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'FinOps-Python-Bot/1.0'
        })
        
        logger.info(f"Backend sync initialized: {self.backend_url}")
    
    def test_connection(self) -> bool:
        """
        Test connection to the backend API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.backend_url}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Backend connection successful: {data.get('message', 'OK')}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Backend connection failed: {str(e)}")
            return False
    
    def sync_resources(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sync AWS resource inventory to backend.
        
        Args:
            resources: List of resource dictionaries
            
        Returns:
            Summary of sync operation
        """
        logger.info(f"📤 Syncing {len(resources)} resources to backend...")
        
        success_count = 0
        error_count = 0
        errors = []
        
        for resource in resources:
            try:
                response = self.session.post(
                    f"{self.backend_url}/api/resources",
                    json=resource,
                    timeout=self.timeout
                )
                response.raise_for_status()
                success_count += 1
                
            except requests.exceptions.RequestException as e:
                error_count += 1
                error_msg = f"Failed to sync resource {resource.get('resourceId', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        summary = {
            'total': len(resources),
            'success': success_count,
            'errors': error_count,
            'error_details': errors[:10]  # Limit to first 10 errors
        }
        
        logger.info(f"✅ Resource sync complete: {success_count}/{len(resources)} successful")
        return summary
    
    def sync_optimizations(self, optimizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sync cost optimizations to backend.
        
        Args:
            optimizations: List of optimization dictionaries
            
        Returns:
            Summary of sync operation
        """
        logger.info(f"📤 Syncing {len(optimizations)} optimizations to backend...")
        
        success_count = 0
        error_count = 0
        errors = []
        
        for optimization in optimizations:
            try:
                response = self.session.post(
                    f"{self.backend_url}/api/optimizations",
                    json=optimization,
                    timeout=self.timeout
                )
                response.raise_for_status()
                success_count += 1
                
            except requests.exceptions.RequestException as e:
                error_count += 1
                error_msg = f"Failed to sync optimization {optimization.get('optimizationId', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        summary = {
            'total': len(optimizations),
            'success': success_count,
            'errors': error_count,
            'error_details': errors[:10]
        }
        
        logger.info(f"✅ Optimization sync complete: {success_count}/{len(optimizations)} successful")
        return summary
    
    def sync_anomalies(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sync cost anomalies to backend.
        
        Args:
            anomalies: List of anomaly dictionaries
            
        Returns:
            Summary of sync operation
        """
        logger.info(f"📤 Syncing {len(anomalies)} anomalies to backend...")
        
        success_count = 0
        error_count = 0
        errors = []
        
        for anomaly in anomalies:
            try:
                response = self.session.post(
                    f"{self.backend_url}/api/anomalies",
                    json=anomaly,
                    timeout=self.timeout
                )
                response.raise_for_status()
                success_count += 1
                
            except requests.exceptions.RequestException as e:
                error_count += 1
                error_msg = f"Failed to sync anomaly {anomaly.get('anomalyId', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        summary = {
            'total': len(anomalies),
            'success': success_count,
            'errors': error_count,
            'error_details': errors[:10]
        }
        
        logger.info(f"✅ Anomaly sync complete: {success_count}/{len(anomalies)} successful")
        return summary
    
    def sync_budgets(self, budgets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sync budget forecasts to backend.
        
        Args:
            budgets: List of budget dictionaries
            
        Returns:
            Summary of sync operation
        """
        logger.info(f"📤 Syncing {len(budgets)} budgets to backend...")
        
        success_count = 0
        error_count = 0
        errors = []
        
        for budget in budgets:
            try:
                response = self.session.post(
                    f"{self.backend_url}/api/budgets",
                    json=budget,
                    timeout=self.timeout
                )
                response.raise_for_status()
                success_count += 1
                
            except requests.exceptions.RequestException as e:
                error_count += 1
                error_msg = f"Failed to sync budget {budget.get('forecastId', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        summary = {
            'total': len(budgets),
            'success': success_count,
            'errors': error_count,
            'error_details': errors[:10]
        }
        
        logger.info(f"✅ Budget sync complete: {success_count}/{len(budgets)} successful")
        return summary
    
    def sync_savings(self, savings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sync savings records to backend.
        
        Args:
            savings: List of savings dictionaries
            
        Returns:
            Summary of sync operation
        """
        logger.info(f"📤 Syncing {len(savings)} savings records to backend...")
        
        success_count = 0
        error_count = 0
        errors = []
        
        for saving in savings:
            try:
                response = self.session.post(
                    f"{self.backend_url}/api/savings",
                    json=saving,
                    timeout=self.timeout
                )
                response.raise_for_status()
                success_count += 1
                
            except requests.exceptions.RequestException as e:
                error_count += 1
                error_msg = f"Failed to sync savings record: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        summary = {
            'total': len(savings),
            'success': success_count,
            'errors': error_count,
            'error_details': errors[:10]
        }
        
        logger.info(f"✅ Savings sync complete: {success_count}/{len(savings)} successful")
        return summary
    
    def sync_all(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Sync all FinOps data to backend in one operation.
        
        Args:
            data: Dictionary containing all data types:
                - resources: List of resources
                - optimizations: List of optimizations
                - anomalies: List of anomalies
                - budgets: List of budgets
                - savings: List of savings
        
        Returns:
            Summary of all sync operations
        """
        logger.info("🚀 Starting full data sync to backend...")
        start_time = time.time()
        
        results = {}
        
        # Sync resources
        if 'resources' in data and data['resources']:
            results['resources'] = self.sync_resources(data['resources'])
        
        # Sync optimizations
        if 'optimizations' in data and data['optimizations']:
            results['optimizations'] = self.sync_optimizations(data['optimizations'])
        
        # Sync anomalies
        if 'anomalies' in data and data['anomalies']:
            results['anomalies'] = self.sync_anomalies(data['anomalies'])
        
        # Sync budgets
        if 'budgets' in data and data['budgets']:
            results['budgets'] = self.sync_budgets(data['budgets'])
        
        # Sync savings
        if 'savings' in data and data['savings']:
            results['savings'] = self.sync_savings(data['savings'])
        
        elapsed_time = time.time() - start_time
        
        # Calculate totals
        total_records = sum(r.get('total', 0) for r in results.values())
        total_success = sum(r.get('success', 0) for r in results.values())
        total_errors = sum(r.get('errors', 0) for r in results.values())
        
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'elapsed_time_seconds': round(elapsed_time, 2),
            'total_records': total_records,
            'total_success': total_success,
            'total_errors': total_errors,
            'success_rate': round((total_success / total_records * 100) if total_records > 0 else 0, 2),
            'details': results
        }
        
        logger.info(f"✅ Full sync complete: {total_success}/{total_records} records synced in {elapsed_time:.2f}s")
        
        return summary
    
    def clear_all_data(self) -> bool:
        """
        Clear all data from backend (useful for testing).
        
        Returns:
            True if successful, False otherwise
        """
        logger.warning("⚠️ Clearing all data from backend...")
        
        try:
            # Note: This requires backend to implement DELETE endpoints
            endpoints = [
                '/api/resources/clear',
                '/api/optimizations/clear',
                '/api/anomalies/clear',
                '/api/budgets/clear',
                '/api/savings/clear'
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.delete(
                        f"{self.backend_url}{endpoint}",
                        timeout=self.timeout
                    )
                    # 404 is OK if endpoint doesn't exist
                    if response.status_code not in [200, 404]:
                        response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Clear endpoint {endpoint} not available: {str(e)}")
            
            logger.info("✅ Backend data cleared")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear backend data: {str(e)}")
            return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current sync status from backend.
        
        Returns:
            Status information from backend
        """
        try:
            response = self.session.get(
                f"{self.backend_url}/api/monitoring/metrics",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get sync status: {str(e)}")
            return {'error': str(e)}
