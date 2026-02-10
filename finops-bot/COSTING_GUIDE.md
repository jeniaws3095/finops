# AWS FinOps Bot - Costing Module Guide

## Overview

The costing module provides real-time cost calculation for EC2 instances, Load Balancers, Auto Scaling Groups, and EBS volumes across all AWS regions. It integrates with the bot's discovery and metrics collection to provide comprehensive cost visibility.

## Cost Calculation Components

### 1. EC2 Instance Costing (`get_ec2_instance_cost`)

Calculates hourly, daily, monthly, and annual costs for EC2 instances based on:
- **Instance Type**: t2.micro, t3.large, m5.xlarge, c5.2xlarge, etc.
- **Region**: us-east-1, us-west-2, eu-west-1, etc.
- **State**: Only running instances incur charges

**Pricing Model**:
- On-demand hourly rates (simplified pricing table)
- Charges only apply to running instances
- Stopped instances have $0 cost

**Example Rates** (us-east-1):
```
t2.micro:    $0.0116/hour  ($8.41/month)
t2.medium:   $0.0464/hour  ($33.69/month)
m5.large:    $0.096/hour   ($69.12/month)
c5.xlarge:   $0.17/hour    ($122.64/month)
```

**Output**:
```python
{
    "hourly_cost": 0.096,
    "daily_cost": 2.304,
    "monthly_cost": 69.12,
    "annual_cost": 829.44
}
```

### 2. Load Balancer Costing (`get_load_balancer_cost`)

Calculates costs for Application Load Balancers (ALB), Network Load Balancers (NLB), and Classic Load Balancers.

**Cost Components**:
1. **Hourly Base Charge**: Fixed hourly rate per LB type
   - ALB: $0.0225/hour
   - NLB: $0.0325/hour
   - Classic: $0.025/hour

2. **Data Processing Charge**: Per GB of data processed
   - Rate: $0.006/GB (varies by region)
   - Calculated from ProcessedBytes metric

3. **New Connections Charge**: Per million new connections
   - Rate: $0.006 per million connections
   - Calculated from RequestCount metric

**Example Calculation**:
```
ALB with 1000 requests/hour and 100GB processed:
- Base: $0.0225/hour
- Data: (100 GB * $0.006) = $0.60/hour
- Connections: (1000 / 1,000,000 * $0.006) = $0.000006/hour
- Total: $0.622506/hour = $448.20/month
```

**Output**:
```python
{
    "hourly_base_cost": 0.0225,
    "data_processing_cost": 0.60,
    "new_connections_cost": 0.000006,
    "hourly_cost": 0.622506,
    "daily_cost": 14.94,
    "monthly_cost": 448.20,
    "annual_cost": 5378.40
}
```

### 3. Auto Scaling Group Costing (`get_asg_cost`)

Calculates total cost for an ASG by summing costs of all instances.

**Process**:
1. Retrieves all instance IDs in the ASG
2. Fetches instance details (type, state) from EC2 API
3. Calculates cost for each instance
4. Sums all instance costs

**Output**:
```python
{
    "instance_count": 5,
    "running_instances": 4,
    "instance_costs": [
        {
            "instance_id": "i-1234567890abcdef0",
            "instance_type": "t3.large",
            "state": "running",
            "hourly_cost": 0.0832
        },
        # ... more instances
    ],
    "hourly_cost": 0.3328,
    "daily_cost": 7.99,
    "monthly_cost": 239.42,
    "annual_cost": 2873.04
}
```

### 4. EBS Volume Costing (`get_ebs_volume_cost`)

Calculates costs for all EBS volumes in a region.

**Pricing by Volume Type** (per GB-month):
- **gp2** (General Purpose): $0.10/GB-month
- **gp3** (General Purpose 3): $0.08/GB-month
- **io1** (Provisioned IOPS): $0.125/GB-month
- **io2** (Provisioned IOPS 2): $0.125/GB-month
- **st1** (Throughput Optimized): $0.045/GB-month
- **sc1** (Cold Storage): $0.015/GB-month

**Example Calculation**:
```
100 GB gp2 volume:
- Cost: 100 GB * $0.10/GB-month = $10/month
- Hourly: $10 / 30 / 24 = $0.0139/hour
```

**Output**:
```python
{
    "volume_count": 3,
    "volume_costs": [
        {
            "volume_id": "vol-1234567890abcdef0",
            "volume_type": "gp2",
            "size_gb": 100,
            "state": "in-use",
            "monthly_cost": 10.00
        },
        # ... more volumes
    ],
    "monthly_cost": 35.00,
    "daily_cost": 1.17,
    "hourly_cost": 0.0486,
    "annual_cost": 420.00
}
```

### 5. Total Region Cost (`get_total_region_cost`)

Aggregates all costs for a region.

**Includes**:
- EC2 instances
- Load Balancers
- EBS volumes

**Output**:
```python
{
    "region": "us-east-1",
    "ec2_cost": 0.384,
    "load_balancer_cost": 0.0225,
    "asg_cost": 0.0,
    "ebs_cost": 0.0486,
    "total_hourly": 0.4551,
    "total_daily": 10.92,
    "total_monthly": 327.66,
    "total_annual": 3931.92,
    "breakdown": {
        "ec2": 0.384,
        "load_balancers": 0.0225,
        "ebs": 0.0486
    }
}
```

## Integration with Bot

### Data Flow

```
finops-bot/main.py
├── EC2 Discovery
│   ├── get_instances()
│   ├── get_cpu()
│   └── get_ec2_instance_cost()  ← Cost calculation
│
├── Load Balancer Discovery
│   ├── get_load_balancers()
│   ├── get_load_balancer_metrics()
│   └── get_load_balancer_cost()  ← Cost calculation
│
├── ASG Discovery
│   ├── get_auto_scaling_groups()
│   ├── get_asg_metrics()
│   └── get_asg_cost()  ← Cost calculation
│
└── Cost Summary
    ├── Total monthly cost
    ├── Cost by region
    └── Cost breakdown by service
```

### Output Example

```
Starting AWS FinOps Bot...

Instance: i-1234567890abcdef0 | Type: t3.large | Region: us-east-1 | CPU: 5.23% | State: running | Cost: $0.0832/hr ($59.90/mo)
📦 Instance data saved

Load Balancer: my-app-alb | Type: application | Region: us-east-1 | State: active | Requests: 1250.0 | Cost: $0.0225/hr ($16.20/mo)
📦 Load Balancer data saved

ASG: web-servers | Region: us-east-1 | Desired: 5 | Current: 5 | Utilization: 100.0% | Cost: $0.4160/hr ($299.52/mo)
📦 Auto Scaling Group data saved

================================================================================
COST SUMMARY
================================================================================

💰 Total Monthly Cost: $375.62
💰 Total Daily Cost: $12.52
💰 Total Annual Cost: $4507.44

================================================================================
COST BY REGION
================================================================================

us-east-1:
  EC2 Instances: $59.90/month
  Load Balancers: $16.20/month
  EBS Volumes: $10.00/month
  Total: $86.10/month

us-west-2:
  EC2 Instances: $139.80/month
  Load Balancers: $0.00/month
  EBS Volumes: $5.00/month
  Total: $144.80/month
```

## Backend API Integration

The bot sends cost data to the backend via these endpoints:

### EC2 Instance Cost
```json
POST /api/instances
{
    "instance_id": "i-1234567890abcdef0",
    "instance_type": "t3.large",
    "region": "us-east-1",
    "state": "running",
    "cpu": 5.23,
    "hourly_cost": 0.0832,
    "monthly_cost": 59.90,
    "annual_cost": 718.80
}
```

### Load Balancer Cost
```json
POST /api/load-balancers
{
    "load_balancer_name": "my-app-alb",
    "load_balancer_type": "application",
    "region": "us-east-1",
    "state": "active",
    "metrics": { ... },
    "hourly_cost": 0.0225,
    "monthly_cost": 16.20,
    "annual_cost": 194.40
}
```

### Auto Scaling Group Cost
```json
POST /api/auto-scaling-groups
{
    "asg_name": "web-servers",
    "region": "us-east-1",
    "desired_capacity": 5,
    "current_instances": 5,
    "metrics": { ... },
    "hourly_cost": 0.4160,
    "monthly_cost": 299.52,
    "annual_cost": 3594.24,
    "instance_costs": [
        {
            "instance_id": "i-xxx",
            "instance_type": "t3.large",
            "state": "running",
            "hourly_cost": 0.0832
        }
    ]
}
```

## Cost Optimization Opportunities

### 1. Underutilized EC2 Instances
- **Indicator**: CPU < 5% for extended period
- **Action**: Stop or terminate
- **Savings**: 100% of instance cost

### 2. Idle Load Balancers
- **Indicator**: Request count < 100/hour
- **Action**: Remove or consolidate
- **Savings**: 100% of LB cost + data processing

### 3. Over-provisioned ASGs
- **Indicator**: Instance utilization < 20%
- **Action**: Reduce desired capacity
- **Savings**: Proportional to capacity reduction

### 4. Unused EBS Volumes
- **Indicator**: No I/O activity
- **Action**: Delete or archive
- **Savings**: 100% of volume cost

## Pricing Accuracy

**Current Implementation**:
- Uses simplified pricing tables
- Covers major instance types and regions
- Defaults to reasonable estimates for unknown types

**Production Recommendations**:
1. Integrate AWS Pricing API for real-time rates
2. Account for Reserved Instances and Savings Plans
3. Include data transfer costs
4. Factor in support plan costs
5. Consider spot instance pricing

## Future Enhancements

1. **Real-time Pricing**: Integrate AWS Pricing API
2. **Reserved Instance Tracking**: Calculate RI utilization and savings
3. **Savings Plans**: Track SP coverage and discounts
4. **Data Transfer Costs**: Include inter-region and internet egress
5. **Cost Anomaly Detection**: Alert on unusual spending patterns
6. **Cost Forecasting**: Predict future costs based on trends
7. **Budget Alerts**: Notify when approaching budget thresholds
8. **Cost Allocation Tags**: Track costs by team/project/environment
