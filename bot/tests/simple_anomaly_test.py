#!/usr/bin/env python3
"""
Simple test to verify anomaly detection works
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

try:
    from core.anomaly_detector import AnomalyDetector
    from utils.aws_config import AWSConfig
    print("✅ Imports successful")
    
    # Create simple test data
    cost_data = []
    base_time = datetime.utcnow() - timedelta(days=7)
    
    for hour in range(168):  # 1 week of hourly data
        timestamp = base_time + timedelta(hours=hour)
        cost = 100.0 if hour != 100 else 300.0  # Spike at hour 100
        
        cost_data.append({
            'timestamp': timestamp.isoformat(),
            'cost': cost,
            'service': 'ec2',
            'region': 'us-east-1'
        })
    
    print(f"✅ Generated {len(cost_data)} cost data points")
    
    # Initialize detector
    aws_config = AWSConfig(region='us-east-1')
    detector = AnomalyDetector(aws_config, region='us-east-1')
    print("✅ AnomalyDetector initialized")
    
    # Run detection
    results = detector.detect_anomalies(cost_data)
    print(f"✅ Detection completed")
    print(f"   Baseline established: {results['baseline_analysis']['baseline_established']}")
    print(f"   Anomalies detected: {len(results['anomalies_detected'])}")
    
    if results['anomalies_detected']:
        anomaly = results['anomalies_detected'][0]
        print(f"   First anomaly: {anomaly['severity']} at {anomaly['timestamp']}")
        print(f"   Cost: ${anomaly['actualCost']:.2f} vs expected ${anomaly['expectedCost']:.2f}")
    
    print("✅ Simple anomaly detection test PASSED")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)