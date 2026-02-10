"""
AWS FinOps Bot - Mock Data Version
Demonstrates the bot functionality without requiring AWS credentials
"""

import requests
from datetime import datetime, timedelta
import random

DRY_RUN = False

print("Starting AWS FinOps Bot (Mock Data Mode)...")

# Mock data for demonstration
mock_instances = [
    {"instance_id": "i-0a1b2c3d4e5f6g7h8", "region": "us-east-1", "state": "running", "instance_type": "t2.large", "cpu": 5.2},
    {"instance_id": "i-1b2c3d4e5f6g7h8i9", "region": "us-east-1", "state": "running", "instance_type": "t2.medium", "cpu": 8.1},
    {"instance_id": "i-2c3d4e5f6g7h8i9j0", "region": "us-west-2", "state": "running", "instance_type": "m5.large", "cpu": 15.3},
    {"instance_id": "i-3d4e5f6g7h8i9j0k1", "region": "eu-west-1", "state": "running", "instance_type": "t3.small", "cpu": 3.7},
]

mock_load_balancers = [
    {"name": "web-lb-prod", "arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/web-lb-prod/1234567890abcdef", "region": "us-east-1", "type": "application", "state": "active"},
    {"name": "api-lb-staging", "arn": "arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/api-lb-staging/abcdef1234567890", "region": "us-west-2", "type": "application", "state": "active"},
]

mock_asgs = [
    {"name": "web-asg-prod", "arn": "arn:aws:autoscaling:us-east-1:123456789012:autoScalingGroup:12345678-1234-1234-1234-123456789012:autoScalingGroupName/web-asg-prod", "region": "us-east-1", "desired": 3, "current": 3},
    {"name": "worker-asg-prod", "arn": "arn:aws:autoscaling:eu-west-1:123456789012:autoScalingGroup:87654321-4321-4321-4321-210987654321:autoScalingGroupName/worker-asg-prod", "region": "eu-west-1", "desired": 2, "current": 2},
]

mock_ebs_volumes = [
    {"volume_id": "vol-0a1b2c3d4e5f6g7h8", "region": "us-east-1", "type": "gp3", "size": 100, "state": "in-use", "attached": "i-0a1b2c3d4e5f6g7h8"},
    {"volume_id": "vol-1b2c3d4e5f6g7h8i9", "region": "us-west-2", "type": "gp2", "size": 50, "state": "available", "attached": None},
]

mock_rds_instances = [
    {"db_id": "prod-mysql-db", "arn": "arn:aws:rds:us-east-1:123456789012:db:prod-mysql-db", "region": "us-east-1", "engine": "mysql", "class": "db.t3.medium", "cpu": 12.5},
    {"db_id": "staging-postgres-db", "arn": "arn:aws:rds:eu-west-1:123456789012:db:staging-postgres-db", "region": "eu-west-1", "engine": "postgres", "class": "db.t3.small", "cpu": 4.2},
]

print("\n" + "="*80)
print("🔄 RESIZE & RECOMMENDATIONS PHASE")
print("="*80)

print("\n" + "="*80)
print("💰 SAVINGS & COST TRACKING PHASE")
print("="*80)

total_monthly_cost = 0.0
region_costs = {}

# Process EC2 instances
print("\nProcessing EC2 Instances...")
for instance in mock_instances:
    instance_id = instance["instance_id"]
    region = instance["region"]
    state = instance["state"]
    instance_type = instance["instance_type"]
    cpu = instance["cpu"]
    
    # Mock pricing
    pricing_map = {
        "t2.large": {"hourly": 0.0928, "monthly": 67.65},
        "t2.medium": {"hourly": 0.0464, "monthly": 33.83},
        "m5.large": {"hourly": 0.096, "monthly": 70.08},
        "t3.small": {"hourly": 0.0208, "monthly": 15.18},
    }
    
    pricing = pricing_map.get(instance_type, {"hourly": 0.05, "monthly": 36.5})
    hourly_cost = pricing["hourly"]
    monthly_cost = pricing["monthly"]
    total_monthly_cost += monthly_cost
    
    print(
        f"Instance: {instance_id} | "
        f"Type: {instance_type} | "
        f"Region: {region} | "
        f"CPU: {cpu:.2f}% | "
        f"State: {state} | "
        f"Cost: ${hourly_cost:.4f}/hr (${monthly_cost:.2f}/mo)"
    )
    
    try:
        requests.post(
            "http://localhost:5000/api/instances",
            json={
                "instance_id": instance_id,
                "state": state,
                "region": region,
                "cpu": round(cpu, 2),
                "instance_type": instance_type,
                "hourly_cost": round(hourly_cost, 4),
                "monthly_cost": round(monthly_cost, 2),
                "annual_cost": round(monthly_cost * 12, 2)
            },
            timeout=5
        )
        print("📦 Instance data saved")
    except Exception as e:
        print("❌ Instance API error:", e)
    
    # Check if instance is waste (low CPU)
    if state == "running" and cpu < 10:
        money_saved = monthly_cost * 0.5  # Estimate 50% savings
        
        try:
            requests.post(
                "http://localhost:5000/api/savings",
                json={
                    "resource_id": instance_id,
                    "cloud": "AWS",
                    "money_saved": money_saved,
                    "region": region,
                    "state": "stopped",
                    "instance_type": instance_type,
                    "pricing_model": "on-demand",
                    "estimated_hours_saved": 1,
                    "date": str(datetime.utcnow())
                },
                timeout=5
            )
            print(f"💰 Savings data saved - Potential savings: ${money_saved:.2f}")
        except Exception as e:
            print("❌ Savings API error:", e)

# Process Load Balancers
print("\n" + "="*80)
print("📊 RESOURCE MANAGEMENT PHASE")
print("="*80)

print("\nProcessing Load Balancers...")
for lb in mock_load_balancers:
    lb_name = lb["name"]
    region = lb["region"]
    lb_type = lb["type"]
    state = lb["state"]
    
    monthly_cost = 16.20  # Mock ALB cost
    total_monthly_cost += monthly_cost
    
    print(
        f"Load Balancer: {lb_name} | "
        f"Type: {lb_type} | "
        f"Region: {region} | "
        f"State: {state} | "
        f"Cost: ${monthly_cost:.2f}/mo"
    )
    
    try:
        requests.post(
            "http://localhost:5000/api/load-balancers",
            json={
                "load_balancer_name": lb_name,
                "load_balancer_arn": lb["arn"],
                "load_balancer_type": lb_type,
                "region": region,
                "state": state,
                "scheme": "internet-facing",
                "vpc_id": "vpc-12345678",
                "metrics": {"RequestCount": 5000},
                "hourly_cost": round(monthly_cost / 730, 4),
                "monthly_cost": round(monthly_cost, 2),
                "annual_cost": round(monthly_cost * 12, 2)
            },
            timeout=5
        )
        print("📦 Load Balancer data saved")
    except Exception as e:
        print("❌ Load Balancer API error:", e)

# Process Auto Scaling Groups
print("\nProcessing Auto Scaling Groups...")
for asg in mock_asgs:
    asg_name = asg["name"]
    region = asg["region"]
    desired = asg["desired"]
    current = asg["current"]
    
    monthly_cost = desired * 67.65  # t2.large pricing
    total_monthly_cost += monthly_cost
    
    print(
        f"ASG: {asg_name} | "
        f"Region: {region} | "
        f"Desired: {desired} | "
        f"Current: {current} | "
        f"Cost: ${monthly_cost:.2f}/mo"
    )
    
    try:
        requests.post(
            "http://localhost:5000/api/auto-scaling-groups",
            json={
                "asg_name": asg_name,
                "asg_arn": asg["arn"],
                "region": region,
                "min_size": 1,
                "max_size": 5,
                "desired_capacity": desired,
                "current_instances": current,
                "instance_ids": [f"i-{i}" for i in range(current)],
                "health_check_type": "ELB",
                "metrics": {"InstanceUtilizationPercent": 45.0},
                "hourly_cost": round(monthly_cost / 730, 4),
                "monthly_cost": round(monthly_cost, 2),
                "annual_cost": round(monthly_cost * 12, 2),
                "instance_costs": []
            },
            timeout=5
        )
        print("📦 Auto Scaling Group data saved")
    except Exception as e:
        print("❌ Auto Scaling Group API error:", e)

# Process EBS Volumes
print("\nProcessing EBS Volumes...")
for volume in mock_ebs_volumes:
    volume_id = volume["volume_id"]
    region = volume["region"]
    vol_type = volume["type"]
    size = volume["size"]
    state = volume["state"]
    
    # Mock pricing: $0.10 per GB-month for gp3, $0.10 for gp2
    monthly_cost = size * 0.10
    total_monthly_cost += monthly_cost
    
    print(
        f"Volume: {volume_id} | "
        f"Type: {vol_type} | "
        f"Size: {size}GB | "
        f"Region: {region} | "
        f"State: {state} | "
        f"Cost: ${monthly_cost:.2f}/mo"
    )
    
    try:
        requests.post(
            "http://localhost:5000/api/ebs-volumes",
            json={
                "volume_id": volume_id,
                "volume_type": vol_type,
                "size_gb": size,
                "region": region,
                "state": state,
                "availability_zone": f"{region}a",
                "encrypted": True,
                "iops": 3000,
                "throughput": 125,
                "attached_instance_id": volume["attached"],
                "attached_device": "/dev/sdf" if volume["attached"] else None,
                "metrics": {"VolumeReadOps": 100, "VolumeWriteOps": 50},
                "hourly_cost": round(monthly_cost / 730, 4),
                "monthly_cost": round(monthly_cost, 2),
                "annual_cost": round(monthly_cost * 12, 2),
                "tags": {}
            },
            timeout=5
        )
        print("📦 EBS Volume data saved")
    except Exception as e:
        print("❌ EBS Volume API error:", e)

# Process RDS Instances
print("\nProcessing RDS Instances...")
for rds in mock_rds_instances:
    db_id = rds["db_id"]
    region = rds["region"]
    engine = rds["engine"]
    db_class = rds["class"]
    cpu = rds["cpu"]
    
    # Mock pricing
    monthly_cost = 50.0  # Mock RDS cost
    total_monthly_cost += monthly_cost
    
    print(
        f"RDS: {db_id} | "
        f"Engine: {engine} | "
        f"Class: {db_class} | "
        f"Region: {region} | "
        f"CPU: {cpu:.1f}% | "
        f"Cost: ${monthly_cost:.2f}/mo"
    )
    
    try:
        requests.post(
            "http://localhost:5000/api/rds-instances",
            json={
                "db_instance_id": db_id,
                "db_instance_arn": rds["arn"],
                "engine": engine,
                "engine_version": "8.0.28" if engine == "mysql" else "14.5",
                "db_instance_class": db_class,
                "region": region,
                "status": "available",
                "allocated_storage_gb": 100,
                "storage_type": "gp3",
                "multi_az": False,
                "backup_retention_days": 7,
                "publicly_accessible": False,
                "read_replicas": [],
                "metrics": {"CPUUtilizationPercent": cpu, "DatabaseConnections": 25},
                "instance_hourly_cost": round(monthly_cost * 0.7 / 730, 4),
                "storage_hourly_cost": round(monthly_cost * 0.3 / 730, 4),
                "hourly_cost": round(monthly_cost / 730, 4),
                "monthly_cost": round(monthly_cost, 2),
                "annual_cost": round(monthly_cost * 12, 2),
                "tags": {}
            },
            timeout=5
        )
        print("📦 RDS Instance data saved")
    except Exception as e:
        print("❌ RDS Instance API error:", e)

# Send costing data
print("\n" + "="*80)
print("📤 SENDING COSTING DATA TO BACKEND")
print("="*80)

total_daily_cost = total_monthly_cost / 30
total_annual_cost = total_monthly_cost * 12

# Send current costing
try:
    requests.post(
        "http://localhost:5000/api/costing/current",
        json={
            "total_monthly_cost": round(total_monthly_cost, 2),
            "total_daily_cost": round(total_daily_cost, 2),
            "total_annual_cost": round(total_annual_cost, 2),
            "timestamp": str(datetime.utcnow()),
            "region_count": 3,
            "service_breakdown": {
                "ec2": round(sum(67.65 for _ in mock_instances), 2),
                "load_balancers": round(len(mock_load_balancers) * 16.20, 2),
                "auto_scaling_groups": round(sum(asg["desired"] * 67.65 for asg in mock_asgs), 2),
                "ebs_volumes": round(sum(vol["size"] * 0.10 for vol in mock_ebs_volumes), 2),
                "rds_instances": round(len(mock_rds_instances) * 50.0, 2)
            }
        },
        timeout=5
    )
    print("✅ Current costing data saved")
except Exception as e:
    print("❌ Costing API error:", e)

# Send costing by service
try:
    service_totals = {
        "ec2": round(sum(67.65 for _ in mock_instances), 2),
        "load_balancers": round(len(mock_load_balancers) * 16.20, 2),
        "auto_scaling_groups": round(sum(asg["desired"] * 67.65 for asg in mock_asgs), 2),
        "ebs_volumes": round(sum(vol["size"] * 0.10 for vol in mock_ebs_volumes), 2),
        "rds_instances": round(len(mock_rds_instances) * 50.0, 2)
    }
    
    requests.post(
        "http://localhost:5000/api/costing/by-service",
        json={
            "services": service_totals,
            "total_monthly": round(total_monthly_cost, 2),
            "timestamp": str(datetime.utcnow()),
            "service_percentages": {
                "ec2": round((service_totals['ec2'] / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 2),
                "load_balancers": round((service_totals['load_balancers'] / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 2),
                "auto_scaling_groups": round((service_totals['auto_scaling_groups'] / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 2),
                "ebs_volumes": round((service_totals['ebs_volumes'] / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 2),
                "rds_instances": round((service_totals['rds_instances'] / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 2)
            }
        },
        timeout=5
    )
    print("✅ Service costing data saved")
except Exception as e:
    print("❌ Service costing API error:", e)

print("\n" + "="*80)
print("💰 COST SUMMARY & REPORTING")
print("="*80)

print(f"\n📊 TOTAL INFRASTRUCTURE COSTS:")
print(f"  💰 Monthly: ${total_monthly_cost:.2f}")
print(f"  💰 Daily:   ${total_daily_cost:.2f}")
print(f"  💰 Annual:  ${total_annual_cost:.2f}")

print("\n" + "="*80)
print("✅ AWS FinOps Bot Execution Complete (Mock Data Mode)")
print("="*80 + "\n")
