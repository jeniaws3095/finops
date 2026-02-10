# Bot to Backend Integration Guide

## Overview

The FinOps bot (`finops-bot/main.py`) discovers AWS resources and sends data to the backend API for storage, analysis, and cost calculations.

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Cloud Environment                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ EC2 Instances│  │ Load Balancers│  │ RDS Instances│           │
│  │ EBS Volumes  │  │ Auto Scaling  │  │ CloudWatch   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                    boto3 API Calls
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              FinOps Bot (finops-bot/main.py)                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. Discover Resources (list_*.py)                        │   │
│  │ 2. Collect Metrics (check_*_metrics.py)                  │   │
│  │ 3. Calculate Costs (get_current_costs.py)                │   │
│  │ 4. Analyze Recommendations (recommendation_engine.py)    │   │
│  │ 5. Send Data to Backend (HTTP POST)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                    HTTP POST Requests
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│           FinOps Backend (finops-backend/server.js)              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Express Routes (routes/*.js)                             │   │
│  │ ├─ /api/instances                                        │   │
│  │ ├─ /api/load-balancers                                   │   │
│  │ ├─ /api/auto-scaling-groups                              │   │
│  │ ├─ /api/ebs-volumes                                      │   │
│  │ ├─ /api/rds-instances                                    │   │
│  │ ├─ /api/savings                                          │   │
│  │ └─ /api/costing/*                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Shared Data Store (store.js)                             │   │
│  │ ├─ instances[]                                           │   │
│  │ ├─ loadBalancers[]                                       │   │
│  │ ├─ autoScalingGroups[]                                   │   │
│  │ ├─ ebsVolumes[]                                          │   │
│  │ ├─ rdsInstances[]                                        │   │
│  │ └─ savings[]                                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                    Costing Calculations
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│         FinOps Frontend (finops-frontend/)                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Dashboard Components                                     │   │
│  │ ├─ Cost Summary                                          │   │
│  │ ├─ Resource Breakdown                                    │   │
│  │ ├─ Savings History                                       │   │
│  │ └─ Optimization Recommendations                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Bot Modules

### Discovery Modules (`finops-bot/aws/`)

#### list_ec2.py
- Discovers all EC2 instances across regions
- Returns: instance_id, instance_type, state, region, cpu, etc.

#### list_load_balancers.py
- Discovers all load balancers
- Returns: load_balancer_name, arn, type, region, state, etc.

#### list_auto_scaling_groups.py
- Discovers all Auto Scaling Groups
- Returns: asg_name, arn, region, min_size, max_size, desired_capacity, etc.

#### list_ebs_volumes.py
- Discovers all EBS volumes
- Returns: volume_id, type, size_gb, region, state, attached_instance, etc.

#### list_rds_instances.py
- Discovers all RDS instances
- Returns: db_instance_id, arn, engine, class, region, status, etc.

### Metrics Collection Modules

#### check_cpu.py
- Retrieves CPU utilization from CloudWatch
- Used for EC2 instance analysis

#### check_load_balancer_metrics.py
- Retrieves load balancer metrics (RequestCount, HealthyHostCount, etc.)

#### check_asg_metrics.py
- Retrieves ASG metrics (InstanceUtilizationPercent, etc.)

#### check_ebs_metrics.py
- Retrieves EBS volume metrics (VolumeReadOps, VolumeWriteOps, etc.)

#### check_rds_metrics.py
- Retrieves RDS metrics (CPUUtilizationPercent, DatabaseConnections, etc.)

### Cost Calculation Modules

#### get_current_costs.py
- Calculates costs for each resource type
- Returns: hourly_cost, monthly_cost, annual_cost

#### utils/pricing.py
- Pricing lookup tables for all instance types
- Supports: t2, t3, t4g, m5, m6g, m7g, c5, c6g, c7g, r6g, r7g, g4dn, g5, g6
- Includes Graviton processor pricing

### Analysis Modules

#### core/recommendation_engine.py
- Analyzes metrics and generates recommendations
- EC2Recommendation: Resize or stop underutilized instances
- RDSRecommendation: Resize, stop, or delete underutilized databases

#### core/rules_engine.py
- Business logic for identifying waste
- Thresholds for CPU, memory, network utilization

### Resize Modules

#### aws/resize_ec2.py
- Provides resize options for EC2 instances
- Executes resize with approval workflow
- Supports all instance families including Graviton

#### aws/stop_rds.py
- Stops or deletes RDS instances
- Modifies RDS instance class

## Backend API Endpoints

### Resource Endpoints

#### POST /api/instances
Saves EC2 instance data from bot
```json
{
  "instance_id": "i-1234567890abcdef0",
  "state": "running",
  "region": "us-east-1",
  "cpu": 5.2,
  "instance_type": "t2.large",
  "hourly_cost": 0.0928,
  "monthly_cost": 66.82,
  "annual_cost": 801.84
}
```

#### POST /api/load-balancers
Saves load balancer data
```json
{
  "load_balancer_name": "my-alb",
  "load_balancer_arn": "arn:aws:elasticloadbalancing:...",
  "load_balancer_type": "application",
  "region": "us-east-1",
  "state": "active",
  "scheme": "internet-facing",
  "vpc_id": "vpc-12345",
  "metrics": { "RequestCount": 1000 },
  "hourly_cost": 0.0225,
  "monthly_cost": 16.2,
  "annual_cost": 194.4
}
```

#### POST /api/auto-scaling-groups
Saves ASG data
```json
{
  "asg_name": "my-asg",
  "asg_arn": "arn:aws:autoscaling:...",
  "region": "us-east-1",
  "min_size": 1,
  "max_size": 10,
  "desired_capacity": 3,
  "current_instances": 3,
  "instance_ids": ["i-123", "i-456", "i-789"],
  "health_check_type": "ELB",
  "metrics": { "InstanceUtilizationPercent": 25.5 },
  "hourly_cost": 0.2784,
  "monthly_cost": 200.45,
  "annual_cost": 2405.4,
  "instance_costs": [...]
}
```

#### POST /api/ebs-volumes
Saves EBS volume data
```json
{
  "volume_id": "vol-1234567890abcdef0",
  "volume_type": "gp2",
  "size_gb": 100,
  "region": "us-east-1",
  "state": "in-use",
  "availability_zone": "us-east-1a",
  "encrypted": true,
  "iops": 300,
  "throughput": 125,
  "attached_instance_id": "i-1234567890abcdef0",
  "attached_device": "/dev/sda1",
  "metrics": { "VolumeReadOps": 100, "VolumeWriteOps": 50 },
  "hourly_cost": 0.1,
  "monthly_cost": 7.2,
  "annual_cost": 86.4,
  "tags": { "Name": "root-volume" }
}
```

#### POST /api/rds-instances
Saves RDS instance data
```json
{
  "db_instance_id": "mydb",
  "db_instance_arn": "arn:aws:rds:...",
  "engine": "mysql",
  "engine_version": "8.0.28",
  "db_instance_class": "db.t3.medium",
  "region": "us-east-1",
  "status": "available",
  "allocated_storage_gb": 100,
  "storage_type": "gp2",
  "multi_az": false,
  "backup_retention_days": 7,
  "publicly_accessible": false,
  "read_replicas": [],
  "metrics": { "CPUUtilizationPercent": 8.5, "DatabaseConnections": 12 },
  "instance_hourly_cost": 0.168,
  "storage_hourly_cost": 0.023,
  "hourly_cost": 0.191,
  "monthly_cost": 137.52,
  "annual_cost": 1650.24,
  "tags": { "Environment": "production" }
}
```

#### POST /api/savings
Records cost savings from optimization
```json
{
  "resource_id": "i-1234567890abcdef0",
  "cloud": "AWS",
  "money_saved": 33.41,
  "region": "us-east-1",
  "state": "stopped",
  "instance_type": "t2.large",
  "pricing_model": "on-demand",
  "estimated_hours_saved": 1,
  "date": "2026-02-10T12:21:53.487Z"
}
```

### Analytics Endpoints

#### GET /api/costing/current
Returns total costs with breakdown by service
```json
{
  "status": "success",
  "data": {
    "summary": {
      "totalMonthlyCost": 227.74,
      "totalDailyCost": 7.59,
      "totalAnnualCost": 2732.88
    },
    "breakdown": {
      "ec2Instances": { "cost": 66.82, "count": 1, "percentage": 29.34 },
      "loadBalancers": { "cost": 16.2, "count": 1, "percentage": 7.11 },
      "autoScalingGroups": { "cost": 0, "count": 0, "percentage": 0 },
      "ebsVolumes": { "cost": 7.2, "count": 1, "percentage": 3.16 },
      "rdsInstances": { "cost": 137.52, "count": 1, "percentage": 60.38 }
    },
    "timestamp": "2026-02-10T12:21:54.057Z"
  }
}
```

#### GET /api/costing/by-region
Returns costs aggregated by region

#### GET /api/costing/by-service
Returns costs aggregated by service type

## Integration Checklist

- [x] Bot discovers EC2 instances
- [x] Bot discovers load balancers
- [x] Bot discovers Auto Scaling Groups
- [x] Bot discovers EBS volumes
- [x] Bot discovers RDS instances
- [x] Bot collects CloudWatch metrics
- [x] Bot calculates costs
- [x] Bot sends data to backend
- [x] Backend stores data in shared store
- [x] Backend calculates costing
- [x] Backend provides analytics endpoints
- [x] Resize functionality implemented
- [ ] Frontend displays data
- [ ] Approval workflow implemented
- [ ] Audit trail logging

## Running the Integration

### 1. Start Backend
```bash
cd finops-backend
npm start
# Server runs on http://localhost:5000
```

### 2. Run Bot
```bash
cd finops-bot
python main.py
# Bot discovers resources and sends data to backend
```

### 3. Verify Data
```bash
# In another terminal
cd finops-backend
node test-api.js
# Runs comprehensive API tests
```

### 4. Check Costing
```bash
curl http://localhost:5000/api/costing/current
# Returns total costs and breakdown
```

## Troubleshooting

### Bot Cannot Connect to Backend
- Ensure backend is running: `npm start`
- Check backend is listening on port 5000
- Verify firewall allows localhost:5000

### Data Not Appearing in Backend
- Check bot console for error messages
- Verify data format matches API requirements
- Check backend logs for validation errors

### Incorrect Cost Calculations
- Verify pricing data in `finops-bot/utils/pricing.py`
- Check instance types are supported
- Verify region pricing is configured

## Next Steps

1. **Frontend Integration**: Connect React dashboard to backend
2. **MongoDB Persistence**: Replace in-memory store with database
3. **Approval Workflow**: Implement approval system for optimizations
4. **Audit Trail**: Log all actions and decisions
5. **Advanced Analytics**: Add trend analysis and forecasting
