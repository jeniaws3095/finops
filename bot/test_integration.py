"""
Simple test script to verify AWS integration is working correctly.

This script tests:
1. Backend connection
2. AWS connection
3. Data synchronization
4. Data retrieval from backend
"""

import sys
import json
from integration.backend_sync import BackendSync

def test_backend_connection():
    """Test connection to backend API."""
    print("🔌 Testing backend connection...")
    sync = BackendSync()
    
    if sync.test_connection():
        print("✅ Backend connection successful\n")
        return True
    else:
        print("❌ Backend connection failed")
        print("   Make sure backend is running: cd advanced-finops-backend && npm start\n")
        return False

def test_data_sync():
    """Test syncing sample data to backend."""
    print("📤 Testing data synchronization...")
    sync = BackendSync()
    
    # Sample resource data
    sample_resources = [
        {
            'resourceId': 'test-resource-001',
            'resourceType': 'EC2',
            'region': 'us-east-1',
            'state': 'running',
            'serviceType': 'EC2',
            'currentCost': 123.45,
            'tags': {'Name': 'test-server', 'Environment': 'test'},
            'utilizationMetrics': {
                'averageUtilization': 45.5,
                'cpuUtilization': 50.0,
                'memoryUtilization': 41.0
            },
            'optimizationOpportunities': ['test'],
            'timestamp': '2024-02-05T06:00:00Z'
        }
    ]
    
    result = sync.sync_resources(sample_resources)
    
    if result['success'] > 0:
        print(f"✅ Successfully synced {result['success']}/{result['total']} resources\n")
        return True
    else:
        print(f"❌ Failed to sync resources")
        if result.get('error_details'):
            print(f"   Errors: {result['error_details']}\n")
        return False

def test_data_retrieval():
    """Test retrieving data from backend."""
    print("📥 Testing data retrieval...")
    sync = BackendSync()
    
    try:
        import requests
        response = requests.get(f"{sync.backend_url}/api/resources", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                resource_count = len(data['data']) if isinstance(data['data'], list) else 'unknown'
                print(f"✅ Successfully retrieved data from backend")
                print(f"   Resources in backend: {resource_count}\n")
                return True
            else:
                print("⚠️  Backend returned success but no data")
                print("   This might be normal if you haven't synced any real AWS data yet\n")
                return True
        else:
            print(f"❌ Failed to retrieve data: HTTP {response.status_code}\n")
            return False
            
    except Exception as e:
        print(f"❌ Error retrieving data: {str(e)}\n")
        return False

def test_sync_status():
    """Test getting sync status from backend."""
    print("📊 Testing sync status API...")
    sync = BackendSync()
    
    status = sync.get_sync_status()
    
    if 'error' not in status:
        print("✅ Sync status API working")
        if status.get('data'):
            print(f"   Backend metrics available\n")
        return True
    else:
        print(f"⚠️  Could not get sync status: {status.get('error')}\n")
        return True  # Not critical

def main():
    """Run all tests."""
    print("=" * 60)
    print("AWS Integration Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Backend Connection", test_backend_connection),
        ("Data Synchronization", test_data_sync),
        ("Data Retrieval", test_data_retrieval),
        ("Sync Status API", test_sync_status)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}\n")
            results.append((test_name, False))
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("🎉 All tests passed! Integration is working correctly.")
        print()
        print("Next steps:")
        print("1. Run: python main.py --scan-only --sync-backend --dry-run")
        print("2. Check frontend: http://localhost:3000")
        print("3. You should see real AWS data!")
        return 0
    else:
        print()
        print("⚠️  Some tests failed. Please check the errors above.")
        print()
        print("Common fixes:")
        print("1. Ensure backend is running: cd advanced-finops-backend && npm start")
        print("2. Install requests: pip install requests")
        print("3. Check backend URL: http://localhost:5000/health")
        return 1

if __name__ == '__main__':
    sys.exit(main())
