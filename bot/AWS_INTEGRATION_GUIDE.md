# AWS Integration Setup Guide

## Overview

This guide explains how to connect the Python FinOps bot to the Node.js backend so that the frontend displays **real AWS data** instead of mock data.

---

## 🔧 Installation

### 1. Install Python Dependencies

The backend sync module requires the `requests` library:

```bash
cd advanced-finops-bot
pip install requests
```

Or add to `requirements.txt`:
```
requests>=2.31.0
```

---

## 🚀 Usage

### Quick Start: Scan AWS and Sync to Backend

```bash
# Scan AWS resources and sync to backend
python main.py --scan-only --sync-backend --dry-run

# Scan specific services
python main.py --scan-only --sync-backend --services ec2,rds,lambda

# Full workflow with backend sync
python main.py --sync-backend --dry-run
```

### Command-Line Arguments

| Argument | Description |
|----------|-------------|
| `--sync-backend` | Enable automatic data synchronization to backend API |
| `--backend-url URL` | Backend API URL (default: http://localhost:5000) |
| `--scan-only` | Only scan AWS resources (no optimization) |
| `--dry-run` | Safe mode - no AWS modifications |
| `--services LIST` | Comma-separated list of services to scan |

---

## 📊 Data Flow

### Before Integration
```
Frontend → Backend API → Returns [] → Frontend shows MOCK data
```

### After Integration
```
AWS Resources
    ↓ (boto3)
Python Bot scans AWS
    ↓ (HTTP POST)
Backend API stores data
    ↓ (HTTP GET)
Frontend displays REAL data
```

---

## 🔍 Verification

### 1. Start Backend Server
```bash
cd advanced-finops-backend
npm start
```

### 2. Test Backend Connection
```bash
cd advanced-finops-bot
python main.py --test-connection
```

Expected output:
```
Testing connections...
  AWS config: region=us-east-1, regions=['us-east-1']
✓ AWS connection successful
✓ Backend API connection successful
```

### 3. Scan AWS and Sync Data
```bash
python main.py --scan-only --sync-backend --dry-run
```

Expected output:
```
📤 Syncing 45 resources to backend...
✅ Resource sync complete: 45/45 successful
📤 Syncing 12 optimizations to backend...
✅ Optimization sync complete: 12/12 successful
...
```

### 4. Verify Data in Backend
```bash
curl http://localhost:5000/api/resources
```

Should return actual AWS resources instead of empty array.

### 5. Check Frontend
Open http://localhost:3000 in browser - you should now see real AWS data!

---

## 🔄 Automated Sync

### Option 1: Continuous Monitoring
Run the bot in continuous mode with backend sync:

```bash
python main.py --continuous --sync-backend --interval 60
```

This will:
- Scan AWS every 60 minutes
- Automatically sync data to backend
- Keep frontend updated with latest data

### Option 2: Scheduled Sync (Cron)
Add to crontab:

```bash
# Sync every hour
0 * * * * cd /path/to/advanced-finops-bot && python main.py --scan-only --sync-backend --dry-run
```

### Option 3: Systemd Service
Create `/etc/systemd/system/finops-sync.service`:

```ini
[Unit]
Description=FinOps AWS Data Sync
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/advanced-finops-bot
ExecStart=/usr/bin/python3 main.py --continuous --sync-backend --interval 60
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable finops-sync
sudo systemctl start finops-sync
```

---

## 🛠️ Programmatic Usage

### Using BackendSync Directly

```python
from integration.backend_sync import BackendSync

# Initialize sync client
sync = BackendSync(backend_url='http://localhost:5000')

# Test connection
if sync.test_connection():
    print("✅ Backend connected")

# Sync resources
resources = [
    {
        'resourceId': 'i-1234567890abcdef0',
        'resourceType': 'EC2',
        'region': 'us-east-1',
        'state': 'running',
        'currentCost': 45.67,
        # ... more fields
    }
]

result = sync.sync_resources(resources)
print(f"Synced {result['success']}/{result['total']} resources")

# Sync all data types at once
all_data = {
    'resources': resources_list,
    'optimizations': optimizations_list,
    'anomalies': anomalies_list,
    'budgets': budgets_list,
    'savings': savings_list
}

summary = sync.sync_all(all_data)
print(f"Total: {summary['total_success']}/{summary['total_records']} synced")
```

---

## 📋 Data Format

### Resource Format
```python
{
    'resourceId': 'i-1234567890abcdef0',
    'resourceType': 'EC2',
    'region': 'us-east-1',
    'state': 'running',
    'serviceType': 'EC2',
    'currentCost': 45.67,
    'tags': {'Name': 'web-server', 'Environment': 'production'},
    'utilizationMetrics': {
        'averageUtilization': 35.5,
        'cpuUtilization': 40.0,
        'memoryUtilization': 31.0
    },
    'optimizationOpportunities': ['rightsizing', 'reserved_instance'],
    'timestamp': '2024-02-05T06:00:00Z'
}
```

### Optimization Format
```python
{
    'optimizationId': 'opt-12345',
    'resourceId': 'i-1234567890abcdef0',
    'optimizationType': 'rightsizing',
    'currentState': 't3.large',
    'recommendedState': 't3.medium',
    'estimatedSavings': 15.50,
    'confidence': 85.5,
    'riskLevel': 'LOW',
    'status': 'pending',
    'timestamp': '2024-02-05T06:00:00Z'
}
```

---

## 🐛 Troubleshooting

### Backend Connection Failed
```
✗ Backend API connection failed
```

**Solutions:**
1. Ensure backend is running: `cd advanced-finops-backend && npm start`
2. Check backend URL: `--backend-url http://localhost:5000`
3. Verify firewall/network settings

### AWS Connection Failed
```
✗ AWS connection failed: Unable to locate credentials
```

**Solutions:**
1. Configure AWS credentials: `aws configure`
2. Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_DEFAULT_REGION=us-east-1
   ```

### Sync Errors
```
❌ Failed to sync resource i-12345: 400 Bad Request
```

**Solutions:**
1. Check backend logs for validation errors
2. Ensure resource data matches expected format
3. Verify all required fields are present

### No Data in Frontend
1. Check backend has data: `curl http://localhost:5000/api/resources`
2. Clear browser cache and reload
3. Check browser console for API errors
4. Verify frontend is pointing to correct backend URL

---

## 📊 Monitoring

### Check Sync Status
```bash
curl http://localhost:5000/api/monitoring/metrics
```

### View Sync Logs
```bash
# Python bot logs
tail -f advanced_finops.log

# Backend logs
tail -f combined.log
```

---

## 🎯 Next Steps

1. **Set up automated sync** using cron or systemd
2. **Configure AWS credentials** for production
3. **Customize sync interval** based on your needs
4. **Monitor sync health** using backend metrics API
5. **Implement error notifications** for failed syncs

---

## 📚 Related Documentation

- [DATA_FLOW_ANALYSIS.md](../DATA_FLOW_ANALYSIS.md) - Complete data flow analysis
- [Backend API Documentation](../advanced-finops-backend/README.md)
- [Python Bot Documentation](./README.md)
