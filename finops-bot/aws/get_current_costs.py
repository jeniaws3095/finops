import boto3
from datetime import datetime, timedelta

def get_ec2_instance_cost(instance):
    """Calculate hourly cost for an EC2 instance"""
    instance_type = instance["instance_type"]
    region = instance["region"]
    state = instance["state"]
    
    # Pricing data (simplified - in production, use AWS Pricing API)
    # Prices are on-demand hourly rates in USD
    pricing_map = {
        "us-east-1": {
            "t2.micro": 0.0116,
            "t2.small": 0.0232,
            "t2.medium": 0.0464,
            "t2.large": 0.0928,
            "t3.micro": 0.0104,
            "t3.small": 0.0208,
            "t3.medium": 0.0416,
            "t3.large": 0.0832,
            "m5.large": 0.096,
            "m5.xlarge": 0.192,
            "m5.2xlarge": 0.384,
            "c5.large": 0.085,
            "c5.xlarge": 0.17,
            "c5.2xlarge": 0.34,
        },
        "us-west-2": {
            "t2.micro": 0.0116,
            "t2.small": 0.0232,
            "t2.medium": 0.0464,
            "t2.large": 0.0928,
            "t3.micro": 0.0104,
            "t3.small": 0.0208,
            "t3.medium": 0.0416,
            "t3.large": 0.0832,
            "m5.large": 0.096,
            "m5.xlarge": 0.192,
            "m5.2xlarge": 0.384,
            "c5.large": 0.085,
            "c5.xlarge": 0.17,
            "c5.2xlarge": 0.34,
        },
        "eu-west-1": {
            "t2.micro": 0.0127,
            "t2.small": 0.0254,
            "t2.medium": 0.0508,
            "t2.large": 0.1016,
            "t3.micro": 0.0114,
            "t3.small": 0.0228,
            "t3.medium": 0.0456,
            "t3.large": 0.0912,
            "m5.large": 0.1056,
            "m5.xlarge": 0.2112,
            "m5.2xlarge": 0.4224,
            "c5.large": 0.0935,
            "c5.xlarge": 0.187,
            "c5.2xlarge": 0.374,
        }
    }
    
    # Get region pricing, default to us-east-1 if not found
    region_pricing = pricing_map.get(region, pricing_map["us-east-1"])
    hourly_cost = region_pricing.get(instance_type, 0.096)  # Default to m5.large price
    
    # Only charge for running instances
    if state == "running":
        return {
            "hourly_cost": hourly_cost,
            "daily_cost": hourly_cost * 24,
            "monthly_cost": hourly_cost * 24 * 30,
            "annual_cost": hourly_cost * 24 * 365
        }
    else:
        return {
            "hourly_cost": 0.0,
            "daily_cost": 0.0,
            "monthly_cost": 0.0,
            "annual_cost": 0.0
        }


def get_load_balancer_cost(load_balancer, metrics):
    """Calculate hourly cost for a load balancer"""
    lb_type = load_balancer["load_balancer_type"]
    region = load_balancer["region"]
    state = load_balancer["state"]
    
    # Pricing data (simplified - in production, use AWS Pricing API)
    # Prices are hourly rates in USD
    lb_pricing = {
        "us-east-1": {
            "application": 0.0225,  # ALB hourly charge
            "network": 0.0325,      # NLB hourly charge
            "classic": 0.025        # Classic LB hourly charge
        },
        "us-west-2": {
            "application": 0.0225,
            "network": 0.0325,
            "classic": 0.025
        },
        "eu-west-1": {
            "application": 0.0247,
            "network": 0.0357,
            "classic": 0.0275
        }
    }
    
    # Get region pricing, default to us-east-1 if not found
    region_pricing = lb_pricing.get(region, lb_pricing["us-east-1"])
    hourly_base_cost = region_pricing.get(lb_type, 0.0225)
    
    # Add data processing charges (per GB)
    processed_bytes = metrics.get("ProcessedBytes", 0)
    processed_gb = processed_bytes / (1024 ** 3)
    
    # Data processing rates (per GB)
    data_processing_rates = {
        "us-east-1": 0.006,
        "us-west-2": 0.006,
        "eu-west-1": 0.0066
    }
    
    data_processing_rate = data_processing_rates.get(region, 0.006)
    data_processing_cost = processed_gb * data_processing_rate
    
    # Add new connections charge (per million)
    request_count = metrics.get("RequestCount", 0)
    new_connections = request_count  # Simplified: assume 1 connection per request
    
    # New connections rates (per million)
    new_connections_rates = {
        "us-east-1": 0.006,
        "us-west-2": 0.006,
        "eu-west-1": 0.0066
    }
    
    new_connections_rate = new_connections_rates.get(region, 0.006)
    new_connections_cost = (new_connections / 1_000_000) * new_connections_rate
    
    total_hourly_cost = hourly_base_cost + data_processing_cost + new_connections_cost
    
    if state == "active":
        return {
            "hourly_base_cost": hourly_base_cost,
            "data_processing_cost": data_processing_cost,
            "new_connections_cost": new_connections_cost,
            "hourly_cost": total_hourly_cost,
            "daily_cost": total_hourly_cost * 24,
            "monthly_cost": total_hourly_cost * 24 * 30,
            "annual_cost": total_hourly_cost * 24 * 365
        }
    else:
        return {
            "hourly_base_cost": 0.0,
            "data_processing_cost": 0.0,
            "new_connections_cost": 0.0,
            "hourly_cost": 0.0,
            "daily_cost": 0.0,
            "monthly_cost": 0.0,
            "annual_cost": 0.0
        }


def get_asg_cost(asg, metrics):
    """Calculate hourly cost for an Auto Scaling Group (sum of EC2 instances)"""
    instance_ids = asg["instance_ids"]
    region = asg["region"]
    
    # Get EC2 client to fetch instance details
    ec2 = boto3.client("ec2", region_name=region)
    
    total_hourly_cost = 0.0
    instance_costs = []
    
    try:
        if instance_ids:
            response = ec2.describe_instances(InstanceIds=instance_ids)
            
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    instance_type = instance["InstanceType"]
                    state = instance["State"]["Name"]
                    
                    # Create instance dict for cost calculation
                    instance_dict = {
                        "instance_type": instance_type,
                        "region": region,
                        "state": state
                    }
                    
                    cost = get_ec2_instance_cost(instance_dict)
                    total_hourly_cost += cost["hourly_cost"]
                    instance_costs.append({
                        "instance_id": instance["InstanceId"],
                        "instance_type": instance_type,
                        "state": state,
                        "hourly_cost": cost["hourly_cost"]
                    })
    
    except Exception as e:
        print(f"⚠️ Error calculating ASG costs: {e}")
    
    return {
        "instance_count": len(instance_ids),
        "running_instances": len([ic for ic in instance_costs if ic["state"] == "running"]),
        "instance_costs": instance_costs,
        "hourly_cost": total_hourly_cost,
        "daily_cost": total_hourly_cost * 24,
        "monthly_cost": total_hourly_cost * 24 * 30,
        "annual_cost": total_hourly_cost * 24 * 365
    }


def get_ebs_volume_cost(region):
    """Calculate cost for EBS volumes in a region"""
    ec2 = boto3.client("ec2", region_name=region)
    
    # Pricing data (simplified - in production, use AWS Pricing API)
    # Prices are per GB-month
    ebs_pricing = {
        "us-east-1": {
            "gp2": 0.10,
            "gp3": 0.08,
            "io1": 0.125,
            "io2": 0.125,
            "st1": 0.045,
            "sc1": 0.015
        },
        "us-west-2": {
            "gp2": 0.10,
            "gp3": 0.08,
            "io1": 0.125,
            "io2": 0.125,
            "st1": 0.045,
            "sc1": 0.015
        },
        "eu-west-1": {
            "gp2": 0.11,
            "gp3": 0.088,
            "io1": 0.1375,
            "io2": 0.1375,
            "st1": 0.0495,
            "sc1": 0.0165
        }
    }
    
    region_pricing = ebs_pricing.get(region, ebs_pricing["us-east-1"])
    
    total_monthly_cost = 0.0
    volume_costs = []
    
    try:
        response = ec2.describe_volumes()
        
        for volume in response["Volumes"]:
            volume_type = volume["VolumeType"]
            size_gb = volume["Size"]
            state = volume["State"]
            
            price_per_gb = region_pricing.get(volume_type, 0.10)
            monthly_cost = size_gb * price_per_gb
            
            if state == "available" or state == "in-use":
                total_monthly_cost += monthly_cost
                volume_costs.append({
                    "volume_id": volume["VolumeId"],
                    "volume_type": volume_type,
                    "size_gb": size_gb,
                    "state": state,
                    "monthly_cost": monthly_cost
                })
    
    except Exception as e:
        print(f"⚠️ Error calculating EBS costs: {e}")
    
    return {
        "volume_count": len(volume_costs),
        "volume_costs": volume_costs,
        "monthly_cost": total_monthly_cost,
        "daily_cost": total_monthly_cost / 30,
        "hourly_cost": total_monthly_cost / 30 / 24,
        "annual_cost": total_monthly_cost * 12
    }


def get_total_region_cost(region):
    """Calculate total cost for all resources in a region"""
    ec2 = boto3.client("ec2", region_name=region)
    elbv2 = boto3.client("elbv2", region_name=region)
    autoscaling = boto3.client("autoscaling", region_name=region)
    
    total_cost = {
        "region": region,
        "ec2_cost": 0.0,
        "load_balancer_cost": 0.0,
        "asg_cost": 0.0,
        "ebs_cost": 0.0,
        "total_hourly": 0.0,
        "total_daily": 0.0,
        "total_monthly": 0.0,
        "total_annual": 0.0,
        "breakdown": {}
    }
    
    try:
        # EC2 instances
        response = ec2.describe_instances()
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instance_dict = {
                    "instance_type": instance["InstanceType"],
                    "region": region,
                    "state": instance["State"]["Name"]
                }
                cost = get_ec2_instance_cost(instance_dict)
                total_cost["ec2_cost"] += cost["hourly_cost"]
        
        # Load Balancers (ALB/NLB)
        response = elbv2.describe_load_balancers()
        for lb in response["LoadBalancers"]:
            lb_dict = {
                "load_balancer_type": lb["Type"],
                "region": region,
                "state": lb["State"]["Code"]
            }
            metrics = {"ProcessedBytes": 0, "RequestCount": 0}
            cost = get_load_balancer_cost(lb_dict, metrics)
            total_cost["load_balancer_cost"] += cost["hourly_cost"]
        
        # EBS volumes
        ebs_cost = get_ebs_volume_cost(region)
        total_cost["ebs_cost"] = ebs_cost["hourly_cost"]
        
        # Calculate totals
        total_cost["total_hourly"] = (
            total_cost["ec2_cost"] + 
            total_cost["load_balancer_cost"] + 
            total_cost["ebs_cost"]
        )
        total_cost["total_daily"] = total_cost["total_hourly"] * 24
        total_cost["total_monthly"] = total_cost["total_hourly"] * 24 * 30
        total_cost["total_annual"] = total_cost["total_hourly"] * 24 * 365
        
        total_cost["breakdown"] = {
            "ec2": total_cost["ec2_cost"],
            "load_balancers": total_cost["load_balancer_cost"],
            "ebs": total_cost["ebs_cost"]
        }
    
    except Exception as e:
        print(f"❌ Error calculating region costs for {region}: {e}")
    
    return total_cost
