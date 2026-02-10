from aws.list_ec2 import get_instances
from aws.check_cpu import get_cpu
from aws.stop_ec2 import stop_instance
from aws.list_load_balancers import get_load_balancers
from aws.check_load_balancer_metrics import get_load_balancer_metrics
from aws.list_auto_scaling_groups import get_auto_scaling_groups
from aws.check_asg_metrics import get_asg_metrics
from aws.list_ebs_volumes import get_ebs_volumes
from aws.check_ebs_metrics import get_ebs_volume_metrics, is_volume_unused
from aws.list_rds_instances import get_rds_instances
from aws.check_rds_metrics import get_rds_instance_metrics, is_rds_underutilized
from aws.stop_rds import stop_rds_instance, delete_rds_instance, modify_rds_instance
from aws.get_current_costs import (
    get_ec2_instance_cost,
    get_load_balancer_cost,
    get_asg_cost,
    get_ebs_volume_cost,
    get_total_region_cost
)
from core.rules_engine import is_waste, is_rds_waste
from utils.pricing import calculate_savings 

import requests
from datetime import datetime, timezone
import boto3

DRY_RUN = False 

print("Starting AWS FinOps Bot...")
print("\n" + "="*80)
print("🔄 RESIZE & RECOMMENDATIONS PHASE")
print("="*80)

# Get all regions for cost summary
ec2 = boto3.client("ec2")
all_regions = [region["RegionName"] for region in ec2.describe_regions()["Regions"]]

total_monthly_cost = 0.0
region_costs = {}

print("\n" + "="*80)
print("💰 SAVINGS & COST TRACKING PHASE")
print("="*80)

for instance in get_instances():
    instance_id = instance["instance_id"]
    region = instance["region"]
    state = instance["state"]
    instance_type = instance["instance_type"] 

    cpu = get_cpu(instance)
    
    # Calculate instance cost
    instance_cost = get_ec2_instance_cost(instance)
    hourly_cost = instance_cost["hourly_cost"]
    monthly_cost = instance_cost["monthly_cost"]
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
                "annual_cost": round(instance_cost["annual_cost"], 2)
            },
            timeout=5
        )
        print("📦 Instance data saved")
    except Exception as e:
        print("❌ Instance API error:", e)

    # ✅ FINOPS RULE (FIXED INDENTATION + REALISTIC SAVINGS)
    if state == "running" and is_waste(cpu):

        money_saved = calculate_savings(
            instance_type,
            hours_saved=1
        )

        if DRY_RUN:
            print(
                f"[DRY RUN] WOULD STOP EC2: {instance_id} | "
                f"Estimated savings: ${money_saved}"
            )
        else:
            stop_instance(instance_id, region)
            print(
                f"[STOPPED] EC2: {instance_id} | "
                f"Estimated savings: ${money_saved}"
            )

        # ✅ SEND SAVINGS DATA (NO HARDCODED 40)
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
                    "date": str(datetime.now(timezone.utc))
                },
                timeout=5
            )
            print(
            f"💵 Calculated Savings → "
            f"Instance: {instance_id} | "
            f"Type: {instance_type} | "
            f"Hours Saved: 1 | "
            f"Savings: ${money_saved}"
            )
            print("💰 Savings data saved")
        except Exception as e:
            print("❌ Savings API error:", e)

    elif state == "stopped":
        print(f"ℹ️ Instance already stopped, skipping: {instance_id}")

print("AWS FinOps Bot finished.")

# ============================================================================
# 📊 RESOURCE MANAGEMENT PHASE
# ============================================================================

print("\n" + "="*80)
print("📊 RESOURCE MANAGEMENT PHASE")
print("="*80)

# ============================================================================
# LOAD BALANCER DISCOVERY AND OPTIMIZATION
# ============================================================================

print("\n" + "="*80)
print("Discovering Load Balancers...")
print("="*80)

for lb in get_load_balancers():
    lb_name = lb["load_balancer_name"]
    lb_type = lb["load_balancer_type"]
    region = lb["region"]
    state = lb["state"]
    
    metrics = get_load_balancer_metrics(lb)
    
    # Calculate load balancer cost
    lb_cost = get_load_balancer_cost(lb, metrics)
    hourly_cost = lb_cost["hourly_cost"]
    monthly_cost = lb_cost["monthly_cost"]
    total_monthly_cost += monthly_cost
    
    print(
        f"Load Balancer: {lb_name} | "
        f"Type: {lb_type} | "
        f"Region: {region} | "
        f"State: {state} | "
        f"Requests: {metrics.get('RequestCount', 0):.0f} | "
        f"Cost: ${hourly_cost:.4f}/hr (${monthly_cost:.2f}/mo)"
    )
    
    try:
        requests.post(
            "http://localhost:5000/api/load-balancers",
            json={
                "load_balancer_name": lb_name,
                "load_balancer_arn": lb["load_balancer_arn"],
                "load_balancer_type": lb_type,
                "region": region,
                "state": state,
                "scheme": lb["scheme"],
                "vpc_id": lb.get("vpc_id"),
                "metrics": metrics,
                "hourly_cost": round(hourly_cost, 4),
                "monthly_cost": round(monthly_cost, 2),
                "annual_cost": round(lb_cost["annual_cost"], 2)
            },
            timeout=5
        )
        print("📦 Load Balancer data saved")
    except Exception as e:
        print("❌ Load Balancer API error:", e)
    
    # Check if load balancer is underutilized
    request_count = metrics.get("RequestCount", 0)
    healthy_hosts = metrics.get("HealthyHostCount", 0)
    
    if state == "active" and request_count < 100 and healthy_hosts > 0:
        print(f"⚠️ Load Balancer {lb_name} may be underutilized (low request count)")
        print(f"   Potential savings: ${monthly_cost:.2f}/month if removed")

print("\n" + "="*80)
print("Discovering Auto Scaling Groups...")
print("="*80)

for asg in get_auto_scaling_groups():
    asg_name = asg["asg_name"]
    region = asg["region"]
    desired = asg["desired_capacity"]
    current = asg["current_instances"]
    
    metrics = get_asg_metrics(asg)
    
    # Calculate ASG cost (sum of all instances)
    asg_cost = get_asg_cost(asg, metrics)
    hourly_cost = asg_cost["hourly_cost"]
    monthly_cost = asg_cost["monthly_cost"]
    total_monthly_cost += monthly_cost
    
    print(
        f"ASG: {asg_name} | "
        f"Region: {region} | "
        f"Desired: {desired} | "
        f"Current: {current} | "
        f"Utilization: {metrics.get('InstanceUtilizationPercent', 0):.1f}% | "
        f"Cost: ${hourly_cost:.4f}/hr (${monthly_cost:.2f}/mo)"
    )
    
    try:
        requests.post(
            "http://localhost:5000/api/auto-scaling-groups",
            json={
                "asg_name": asg_name,
                "asg_arn": asg["asg_arn"],
                "region": region,
                "min_size": asg["min_size"],
                "max_size": asg["max_size"],
                "desired_capacity": desired,
                "current_instances": current,
                "instance_ids": asg["instance_ids"],
                "health_check_type": asg["health_check_type"],
                "metrics": metrics,
                "hourly_cost": round(hourly_cost, 4),
                "monthly_cost": round(monthly_cost, 2),
                "annual_cost": round(asg_cost["annual_cost"], 2),
                "instance_costs": asg_cost["instance_costs"]
            },
            timeout=5
        )
        print("📦 Auto Scaling Group data saved")
    except Exception as e:
        print("❌ Auto Scaling Group API error:", e)
    
    # Check if ASG is underutilized
    utilization = metrics.get("InstanceUtilizationPercent", 0)
    
    if utilization < 20 and current > asg["min_size"]:
        potential_savings = monthly_cost * (current - asg["min_size"]) / current
        print(f"⚠️ ASG {asg_name} is underutilized ({utilization:.1f}%)")
        print(f"   Consider reducing desired capacity from {desired} to {asg['min_size']}")
        print(f"   Potential savings: ${potential_savings:.2f}/month")

print("\nAWS FinOps Bot finished.")

# ============================================================================
# EBS VOLUME DISCOVERY AND OPTIMIZATION
# ============================================================================

print("\n" + "="*80)
print("Processing EBS Volumes...")
print("="*80)

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
                "encrypted": False,
                "iops": None,
                "throughput": None,
                "attached_instance_id": volume.get("attached"),
                "attached_device": None,
                "metrics": {},
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
    
    # Check if EBS volume is unused and calculate savings
    if state == "available":
        money_saved = monthly_cost * 1.0  # 100% savings if deleted
        
        try:
            requests.post(
                "http://localhost:5000/api/savings",
                json={
                    "resource_id": volume_id,
                    "cloud": "AWS",
                    "money_saved": money_saved,
                    "region": region,
                    "state": "deleted",
                    "instance_type": vol_type,
                    "pricing_model": "on-demand",
                    "estimated_hours_saved": 730,
                    "date": str(datetime.now(timezone.utc))
                },
                timeout=5
            )
            print(
                f"💵 Calculated Savings → "
                f"Volume: {volume_id} | "
                f"Type: {vol_type} | "
                f"Size: {size}GB | "
                f"Savings: ${money_saved:.2f}"
            )
            print("💰 Savings data saved")
        except Exception as e:
            print("❌ Savings API error:", e)

# ============================================================================
# RDS INSTANCE DISCOVERY AND OPTIMIZATION
# ============================================================================

print("\n" + "="*80)
print("Processing RDS Instances...")
print("="*80)

for rds in mock_rds_instances:
    db_instance_id = rds["db_id"]
    engine = rds["engine"]
    db_instance_class = rds["class"]
    region = rds["region"]
    cpu = rds["cpu"]
    
    # Mock pricing for RDS
    pricing_map = {
        "db.t3.medium": {"hourly": 0.168, "monthly": 122.64},
        "db.t3.small": {"hourly": 0.084, "monthly": 61.32},
    }
    
    pricing = pricing_map.get(db_instance_class, {"hourly": 0.1, "monthly": 73})
    hourly_cost = pricing["hourly"]
    monthly_cost = pricing["monthly"]
    total_monthly_cost += monthly_cost
    
    print(
        f"RDS: {db_instance_id} | "
        f"Engine: {engine} | "
        f"Class: {db_instance_class} | "
        f"Region: {region} | "
        f"CPU: {cpu:.1f}% | "
        f"Cost: ${hourly_cost:.4f}/hr (${monthly_cost:.2f}/mo)"
    )
    
    try:
        requests.post(
            "http://localhost:5000/api/rds-instances",
            json={
                "db_instance_id": db_instance_id,
                "db_instance_arn": rds["arn"],
                "engine": engine,
                "engine_version": "8.0.28",
                "db_instance_class": db_instance_class,
                "region": region,
                "status": "available",
                "allocated_storage_gb": 100,
                "storage_type": "gp2",
                "multi_az": False,
                "backup_retention_days": 7,
                "publicly_accessible": False,
                "read_replicas": [],
                "metrics": {"CPUUtilizationPercent": cpu, "DatabaseConnections": 5},
                "instance_hourly_cost": round(hourly_cost * 0.8, 4),
                "storage_hourly_cost": round(hourly_cost * 0.2, 4),
                "hourly_cost": round(hourly_cost, 4),
                "monthly_cost": round(monthly_cost, 2),
                "annual_cost": round(monthly_cost * 12, 2),
                "tags": {}
            },
            timeout=5
        )
        print("📦 RDS Instance data saved")
    except Exception as e:
        print("❌ RDS Instance API error:", e)
    
    # Check if RDS is underutilized and calculate savings
    if cpu < 10:
        money_saved = monthly_cost * 0.4  # Estimate 40% savings if downsized
        
        try:
            requests.post(
                "http://localhost:5000/api/savings",
                json={
                    "resource_id": db_instance_id,
                    "cloud": "AWS",
                    "money_saved": money_saved,
                    "region": region,
                    "state": "downsized",
                    "instance_type": db_instance_class,
                    "pricing_model": "on-demand",
                    "estimated_hours_saved": 730,
                    "date": str(datetime.now(timezone.utc))
                },
                timeout=5
            )
            print(
                f"💵 Calculated Savings → "
                f"RDS: {db_instance_id} | "
                f"Engine: {engine} | "
                f"CPU: {cpu:.1f}% | "
                f"Savings: ${money_saved:.2f}"
            )
            print("💰 Savings data saved")
        except Exception as e:
            print("❌ Savings API error:", e)

print("\nAWS FinOps Bot finished.")

# ============================================================================
# COST SUMMARY
# ============================================================================

print("\n" + "="*80)
print("💰 COST SUMMARY & REPORTING")
print("="*80)

print(f"\n💰 TOTAL INFRASTRUCTURE COSTS:")
print(f"  💰 Monthly: ${total_monthly_cost:.2f}")
print(f"  💰 Daily:   ${total_monthly_cost/30:.2f}")
print(f"  💰 Annual:  ${total_monthly_cost*12:.2f}")

print("\n" + "="*80)
print("📍 COST BREAKDOWN BY REGION")
print("="*80)

region_summary = []
for region in all_regions:
    try:
        region_cost = get_total_region_cost(region)
        if region_cost["total_monthly"] > 0:
            region_summary.append({
                "region": region,
                "monthly": region_cost["total_monthly"],
                "ec2": region_cost['ec2_cost']*24*30,
                "lb": region_cost['load_balancer_cost']*24*30,
                "ebs": region_cost['ebs_cost']*24*30
            })
    except Exception as e:
        print(f"⚠️ Error calculating costs for {region}: {e}")

# Sort by cost (highest first)
region_summary.sort(key=lambda x: x["monthly"], reverse=True)

for item in region_summary:
    print(f"\n🌍 {item['region']}:")
    print(f"   EC2 Instances:  ${item['ec2']:.2f}/month")
    print(f"   Load Balancers: ${item['lb']:.2f}/month")
    print(f"   EBS Volumes:    ${item['ebs']:.2f}/month")
    print(f"   ─────────────────────────────")
    print(f"   Total:          ${item['monthly']:.2f}/month")

print("\n" + "="*80)
print("📤 SENDING COSTING DATA TO BACKEND")
print("="*80)

# Send current costing summary
try:
    requests.post(
        "http://localhost:5000/api/costing/current",
        json={
            "total_monthly_cost": round(total_monthly_cost, 2),
            "total_daily_cost": round(total_monthly_cost/30, 2),
            "total_annual_cost": round(total_monthly_cost*12, 2),
            "timestamp": str(datetime.now(timezone.utc)),
            "region_count": len(region_summary),
            "service_breakdown": {
                "ec2": round(sum(item['ec2'] for item in region_summary), 2),
                "load_balancers": round(sum(item['lb'] for item in region_summary), 2),
                "ebs_volumes": round(sum(item['ebs'] for item in region_summary), 2)
            }
        },
        timeout=5
    )
    print("✅ Current costing data saved")
except Exception as e:
    print("❌ Costing API error:", e)

# Send costing by region
try:
    requests.post(
        "http://localhost:5000/api/costing/by-region",
        json={
            "regions": region_summary,
            "total_monthly": round(total_monthly_cost, 2),
            "timestamp": str(datetime.now(timezone.utc))
        },
        timeout=5
    )
    print("✅ Regional costing data saved")
except Exception as e:
    print("❌ Regional costing API error:", e)

# Send costing by service
try:
    service_totals = {
        "ec2": round(sum(item['ec2'] for item in region_summary), 2),
        "load_balancers": round(sum(item['lb'] for item in region_summary), 2),
        "ebs_volumes": round(sum(item['ebs'] for item in region_summary), 2)
    }
    
    requests.post(
        "http://localhost:5000/api/costing/by-service",
        json={
            "services": service_totals,
            "total_monthly": round(total_monthly_cost, 2),
            "timestamp": str(datetime.now(timezone.utc)),
            "service_percentages": {
                "ec2": round((service_totals['ec2'] / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 2),
                "load_balancers": round((service_totals['load_balancers'] / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 2),
                "ebs_volumes": round((service_totals['ebs_volumes'] / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 2)
            }
        },
        timeout=5
    )
    print("✅ Service costing data saved")
except Exception as e:
    print("❌ Service costing API error:", e)

print("\n" + "="*80)
print("✅ AWS FinOps Bot Execution Complete")
print("="*80 + "\n")
