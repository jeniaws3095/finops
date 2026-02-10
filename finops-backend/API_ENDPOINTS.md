# FinOps Backend API Endpoints

## Overview
Complete REST API endpoints for the AWS FinOps automation platform. All endpoints accept and return JSON.

## Base URL
```
http://localhost:5000
```

---

## EC2 Instances Endpoints

### POST /api/instances
Save EC2 instance data from the bot.

**Request Body:**
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

**Response:**
```json
{
  "status": "success",
  "message": "Instance data saved",
  "data": {
    "instance_id": "i-1234567890abcdef0",
    "region": "us-east-1",
    "instance_type": "t2.large"
  }
}
```

### GET /api/instances
Retrieve all EC2 instances.

**Response:**
```json
{
  "status": "success",
  "data": [],
  "total": 0
}
```

### GET /api/instances/:instanceId
Retrieve a specific EC2 instance.

**Response:**
```json
{
  "status": "success",
  "data": null
}
```

---

## Savings Endpoints

### POST /api/savings
Record cost savings from optimization actions.

**Request Body:**
```json
{
  "resource_id": "i-1234567890abcdef0",
  "cloud": "AWS",
  "money_saved": 0.0928,
  "region": "us-east-1",
  "state": "stopped",
  "instance_type": "t2.large",
  "pricing_model": "on-demand",
  "estimated_hours_saved": 1,
  "date": "2025-02-10T12:00:00Z"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Savings recorded",
  "data": {
    "resource_id": "i-1234567890abcdef0",
    "money_saved": 0.0928,
    "cloud": "AWS"
  }
}
```

### GET /api/savings
Retrieve all savings records with optional filters.

**Query Parameters:**
- `startDate` (optional): Filter by start date (ISO 8601)
- `endDate` (optional): Filter by end date (ISO 8601)
- `cloud` (optional): Filter by cloud provider (e.g., "AWS")

**Response:**
```json
{
  "status": "success",
  "data": [],
  "total": 0,
  "totalSavings": 0
}
```

### GET /api/savings/summary
Get savings summary statistics.

**Response:**
```json
{
  "status": "success",
  "data": {
    "totalSavings": 0,
    "monthlySavings": 0,
    "annualSavings": 0,
    "resourceCount": 0
  }
}
```

---

## Load Balancers Endpoints

### POST /api/load-balancers
Save load balancer data.

**Request Body:**
```json
{
  "load_balancer_name": "my-alb",
  "load_balancer_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb/1234567890abcdef",
  "load_balancer_type": "application",
  "region": "us-east-1",
  "state": "active",
  "scheme": "internet-facing",
  "vpc_id": "vpc-12345678",
  "metrics": {
    "RequestCount": 1000,
    "HealthyHostCount": 2
  },
  "hourly_cost": 0.0225,
  "monthly_cost": 16.2,
  "annual_cost": 194.4
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Load balancer data saved",
  "data": {
    "load_balancer_name": "my-alb",
    "load_balancer_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb/1234567890abcdef",
    "region": "us-east-1"
  }
}
```

### GET /api/load-balancers
Retrieve all load balancers.

**Response:**
```json
{
  "status": "success",
  "data": [],
  "total": 0
}
```

### GET /api/load-balancers/:lbArn
Retrieve a specific load balancer.

**Response:**
```json
{
  "status": "success",
  "data": null
}
```

---

## Auto Scaling Groups Endpoints

### POST /api/auto-scaling-groups
Save Auto Scaling Group data.

**Request Body:**
```json
{
  "asg_name": "my-asg",
  "asg_arn": "arn:aws:autoscaling:us-east-1:123456789012:autoScalingGroup:12345678-1234-1234-1234-123456789012:autoScalingGroupName/my-asg",
  "region": "us-east-1",
  "min_size": 1,
  "max_size": 10,
  "desired_capacity": 3,
  "current_instances": 3,
  "instance_ids": ["i-1234567890abcdef0", "i-0987654321fedcba0"],
  "health_check_type": "ELB",
  "metrics": {
    "InstanceUtilizationPercent": 45.5
  },
  "hourly_cost": 0.2784,
  "monthly_cost": 200.45,
  "annual_cost": 2405.4,
  "instance_costs": [0.0928, 0.0928, 0.0928]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "ASG data saved",
  "data": {
    "asg_name": "my-asg",
    "asg_arn": "arn:aws:autoscaling:us-east-1:123456789012:autoScalingGroup:12345678-1234-1234-1234-123456789012:autoScalingGroupName/my-asg",
    "region": "us-east-1"
  }
}
```

### GET /api/auto-scaling-groups
Retrieve all Auto Scaling Groups.

**Response:**
```json
{
  "status": "success",
  "data": [],
  "total": 0
}
```

### GET /api/auto-scaling-groups/:asgArn
Retrieve a specific Auto Scaling Group.

**Response:**
```json
{
  "status": "success",
  "data": null
}
```

---

## EBS Volumes Endpoints

### POST /api/ebs-volumes
Save EBS volume data.

**Request Body:**
```json
{
  "volume_id": "vol-1234567890abcdef0",
  "volume_type": "gp2",
  "size_gb": 100,
  "region": "us-east-1",
  "state": "in-use",
  "availability_zone": "us-east-1a",
  "encrypted": true,
  "iops": 100,
  "throughput": null,
  "attached_instance_id": "i-1234567890abcdef0",
  "attached_device": "/dev/sda1",
  "metrics": {
    "VolumeReadOps": 1000,
    "VolumeWriteOps": 500
  },
  "hourly_cost": 0.0333,
  "monthly_cost": 24,
  "annual_cost": 288,
  "tags": {
    "Name": "root-volume",
    "Environment": "production"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "EBS volume data saved",
  "data": {
    "volume_id": "vol-1234567890abcdef0",
    "volume_type": "gp2",
    "region": "us-east-1"
  }
}
```

### GET /api/ebs-volumes
Retrieve all EBS volumes.

**Response:**
```json
{
  "status": "success",
  "data": [],
  "total": 0
}
```

### GET /api/ebs-volumes/:volumeId
Retrieve a specific EBS volume.

**Response:**
```json
{
  "status": "success",
  "data": null
}
```

---

## RDS Instances Endpoints

### POST /api/rds-instances
Save RDS instance data.

**Request Body:**
```json
{
  "db_instance_id": "mydb",
  "db_instance_arn": "arn:aws:rds:us-east-1:123456789012:db:mydb",
  "engine": "mysql",
  "engine_version": "8.0.28",
  "db_instance_class": "db.t3.large",
  "region": "us-east-1",
  "status": "available",
  "allocated_storage_gb": 100,
  "storage_type": "gp2",
  "multi_az": false,
  "backup_retention_days": 7,
  "publicly_accessible": false,
  "read_replicas": [],
  "metrics": {
    "CPUUtilizationPercent": 5.2,
    "DatabaseConnections": 3
  },
  "instance_hourly_cost": 0.12,
  "storage_hourly_cost": 0.0096,
  "hourly_cost": 0.1296,
  "monthly_cost": 93.31,
  "annual_cost": 1119.72,
  "tags": {
    "Name": "production-db",
    "Environment": "production"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "RDS instance data saved",
  "data": {
    "db_instance_id": "mydb",
    "db_instance_arn": "arn:aws:rds:us-east-1:123456789012:db:mydb",
    "region": "us-east-1"
  }
}
```

### GET /api/rds-instances
Retrieve all RDS instances.

**Response:**
```json
{
  "status": "success",
  "data": [],
  "total": 0
}
```

### GET /api/rds-instances/:dbInstanceId
Retrieve a specific RDS instance.

**Response:**
```json
{
  "status": "success",
  "data": null
}
```

---

## Error Responses

All endpoints return error responses in the following format:

```json
{
  "error": "Error message",
  "message": "Detailed error message"
}
```

### Common HTTP Status Codes
- `200 OK` - Successful GET request
- `201 Created` - Successful POST request
- `400 Bad Request` - Missing or invalid required fields
- `500 Internal Server Error` - Server error

---

## Implementation Notes

- All endpoints currently accept data but store it in memory (TODO: Database integration)
- Timestamps are automatically added to all records
- All cost calculations are performed by the bot before sending to backend
- Metrics are stored as-is from CloudWatch
- Tags are optional for all resources

---

## Next Steps

1. Implement MongoDB repositories for each resource type
2. Add database persistence to all endpoints
3. Add filtering and pagination to GET endpoints
4. Add update (PUT/PATCH) endpoints for resources
5. Add delete endpoints with audit trail
6. Add validation middleware for request bodies
7. Add authentication/authorization
