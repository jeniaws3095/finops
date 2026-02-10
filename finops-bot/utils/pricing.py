# AWS on-demand hourly pricing by region and instance type
INSTANCE_PRICING = {
    "us-east-1": {
        # T2 family (burstable)
        "t2.micro": 0.0116,
        "t2.small": 0.0232,
        "t2.medium": 0.0464,
        "t2.large": 0.0928,
        
        # T3 family (burstable)
        "t3.micro": 0.0104,
        "t3.small": 0.0208,
        "t3.medium": 0.0416,
        "t3.large": 0.0832,
        
        # T4g family (burstable - Graviton2)
        "t4g.micro": 0.0084,
        "t4g.small": 0.0168,
        "t4g.medium": 0.0336,
        "t4g.large": 0.0672,
        "t4g.xlarge": 0.1344,
        "t4g.2xlarge": 0.2688,
        
        # M5 family (general purpose)
        "m5.large": 0.096,
        "m5.xlarge": 0.192,
        "m5.2xlarge": 0.384,
        
        # M6g family (general purpose - Graviton2)
        "m6g.large": 0.0816,
        "m6g.xlarge": 0.1632,
        "m6g.2xlarge": 0.3264,
        "m6g.4xlarge": 0.6528,
        "m6g.8xlarge": 1.3056,
        "m6g.12xlarge": 1.9584,
        "m6g.16xlarge": 2.6112,
        
        # M7g family (general purpose - Graviton3)
        "m7g.large": 0.0896,
        "m7g.xlarge": 0.1792,
        "m7g.2xlarge": 0.3584,
        "m7g.4xlarge": 0.7168,
        "m7g.8xlarge": 1.4336,
        "m7g.12xlarge": 2.1504,
        "m7g.16xlarge": 2.8672,
        
        # C5 family (compute optimized)
        "c5.large": 0.085,
        "c5.xlarge": 0.17,
        "c5.2xlarge": 0.34,
        
        # C6g family (compute optimized - Graviton2)
        "c6g.large": 0.0765,
        "c6g.xlarge": 0.153,
        "c6g.2xlarge": 0.306,
        "c6g.4xlarge": 0.612,
        "c6g.8xlarge": 1.224,
        "c6g.12xlarge": 1.836,
        "c6g.16xlarge": 2.448,
        
        # C7g family (compute optimized - Graviton3)
        "c7g.large": 0.0845,
        "c7g.xlarge": 0.169,
        "c7g.2xlarge": 0.338,
        "c7g.4xlarge": 0.676,
        "c7g.8xlarge": 1.352,
        "c7g.12xlarge": 2.028,
        "c7g.16xlarge": 2.704,
        
        # R6g family (memory optimized - Graviton2)
        "r6g.large": 0.126,
        "r6g.xlarge": 0.252,
        "r6g.2xlarge": 0.504,
        "r6g.4xlarge": 1.008,
        "r6g.8xlarge": 2.016,
        "r6g.12xlarge": 3.024,
        "r6g.16xlarge": 4.032,
        
        # R7g family (memory optimized - Graviton3)
        "r7g.large": 0.1386,
        "r7g.xlarge": 0.2772,
        "r7g.2xlarge": 0.5544,
        "r7g.4xlarge": 1.1088,
        "r7g.8xlarge": 2.2176,
        "r7g.12xlarge": 3.3264,
        "r7g.16xlarge": 4.4352,
        
        # G4 family (GPU - NVIDIA T4)
        "g4dn.xlarge": 0.526,
        "g4dn.2xlarge": 0.752,
        "g4dn.4xlarge": 1.204,
        "g4dn.8xlarge": 2.408,
        "g4dn.12xlarge": 3.612,
        "g4dn.16xlarge": 4.816,
        
        # G5 family (GPU - NVIDIA A10G)
        "g5.xlarge": 1.006,
        "g5.2xlarge": 1.212,
        "g5.4xlarge": 1.624,
        "g5.8xlarge": 2.448,
        "g5.12xlarge": 3.672,
        "g5.16xlarge": 4.896,
        "g5.24xlarge": 7.344,
        
        # G6 family (GPU - NVIDIA L4)
        "g6.xlarge": 0.7,
        "g6.2xlarge": 0.9,
        "g6.4xlarge": 1.3,
        "g6.8xlarge": 2.1,
        "g6.12xlarge": 3.1,
        "g6.16xlarge": 4.1,
        "g6.24xlarge": 6.1,
    },
    "us-west-2": {
        # T2 family (burstable)
        "t2.micro": 0.0116,
        "t2.small": 0.0232,
        "t2.medium": 0.0464,
        "t2.large": 0.0928,
        
        # T3 family (burstable)
        "t3.micro": 0.0104,
        "t3.small": 0.0208,
        "t3.medium": 0.0416,
        "t3.large": 0.0832,
        
        # T4g family (burstable - Graviton2)
        "t4g.micro": 0.0084,
        "t4g.small": 0.0168,
        "t4g.medium": 0.0336,
        "t4g.large": 0.0672,
        "t4g.xlarge": 0.1344,
        "t4g.2xlarge": 0.2688,
        
        # M5 family (general purpose)
        "m5.large": 0.096,
        "m5.xlarge": 0.192,
        "m5.2xlarge": 0.384,
        
        # M6g family (general purpose - Graviton2)
        "m6g.large": 0.0816,
        "m6g.xlarge": 0.1632,
        "m6g.2xlarge": 0.3264,
        "m6g.4xlarge": 0.6528,
        "m6g.8xlarge": 1.3056,
        "m6g.12xlarge": 1.9584,
        "m6g.16xlarge": 2.6112,
        
        # M7g family (general purpose - Graviton3)
        "m7g.large": 0.0896,
        "m7g.xlarge": 0.1792,
        "m7g.2xlarge": 0.3584,
        "m7g.4xlarge": 0.7168,
        "m7g.8xlarge": 1.4336,
        "m7g.12xlarge": 2.1504,
        "m7g.16xlarge": 2.8672,
        
        # C5 family (compute optimized)
        "c5.large": 0.085,
        "c5.xlarge": 0.17,
        "c5.2xlarge": 0.34,
        
        # C6g family (compute optimized - Graviton2)
        "c6g.large": 0.0765,
        "c6g.xlarge": 0.153,
        "c6g.2xlarge": 0.306,
        "c6g.4xlarge": 0.612,
        "c6g.8xlarge": 1.224,
        "c6g.12xlarge": 1.836,
        "c6g.16xlarge": 2.448,
        
        # C7g family (compute optimized - Graviton3)
        "c7g.large": 0.0845,
        "c7g.xlarge": 0.169,
        "c7g.2xlarge": 0.338,
        "c7g.4xlarge": 0.676,
        "c7g.8xlarge": 1.352,
        "c7g.12xlarge": 2.028,
        "c7g.16xlarge": 2.704,
        
        # R6g family (memory optimized - Graviton2)
        "r6g.large": 0.126,
        "r6g.xlarge": 0.252,
        "r6g.2xlarge": 0.504,
        "r6g.4xlarge": 1.008,
        "r6g.8xlarge": 2.016,
        "r6g.12xlarge": 3.024,
        "r6g.16xlarge": 4.032,
        
        # R7g family (memory optimized - Graviton3)
        "r7g.large": 0.1386,
        "r7g.xlarge": 0.2772,
        "r7g.2xlarge": 0.5544,
        "r7g.4xlarge": 1.1088,
        "r7g.8xlarge": 2.2176,
        "r7g.12xlarge": 3.3264,
        "r7g.16xlarge": 4.4352,
        
        # G4 family (GPU - NVIDIA T4)
        "g4dn.xlarge": 0.526,
        "g4dn.2xlarge": 0.752,
        "g4dn.4xlarge": 1.204,
        "g4dn.8xlarge": 2.408,
        "g4dn.12xlarge": 3.612,
        "g4dn.16xlarge": 4.816,
        
        # G5 family (GPU - NVIDIA A10G)
        "g5.xlarge": 1.006,
        "g5.2xlarge": 1.212,
        "g5.4xlarge": 1.624,
        "g5.8xlarge": 2.448,
        "g5.12xlarge": 3.672,
        "g5.16xlarge": 4.896,
        "g5.24xlarge": 7.344,
        
        # G6 family (GPU - NVIDIA L4)
        "g6.xlarge": 0.7,
        "g6.2xlarge": 0.9,
        "g6.4xlarge": 1.3,
        "g6.8xlarge": 2.1,
        "g6.12xlarge": 3.1,
        "g6.16xlarge": 4.1,
        "g6.24xlarge": 6.1,
    },
    "eu-west-1": {
        # T2 family (burstable)
        "t2.micro": 0.0127,
        "t2.small": 0.0254,
        "t2.medium": 0.0508,
        "t2.large": 0.1016,
        
        # T3 family (burstable)
        "t3.micro": 0.0114,
        "t3.small": 0.0228,
        "t3.medium": 0.0456,
        "t3.large": 0.0912,
        
        # T4g family (burstable - Graviton2)
        "t4g.micro": 0.00924,
        "t4g.small": 0.01848,
        "t4g.medium": 0.03696,
        "t4g.large": 0.07392,
        "t4g.xlarge": 0.14784,
        "t4g.2xlarge": 0.29568,
        
        # M5 family (general purpose)
        "m5.large": 0.1056,
        "m5.xlarge": 0.2112,
        "m5.2xlarge": 0.4224,
        
        # M6g family (general purpose - Graviton2)
        "m6g.large": 0.08976,
        "m6g.xlarge": 0.17952,
        "m6g.2xlarge": 0.35904,
        "m6g.4xlarge": 0.71808,
        "m6g.8xlarge": 1.43616,
        "m6g.12xlarge": 2.15424,
        "m6g.16xlarge": 2.87232,
        
        # M7g family (general purpose - Graviton3)
        "m7g.large": 0.09856,
        "m7g.xlarge": 0.19712,
        "m7g.2xlarge": 0.39424,
        "m7g.4xlarge": 0.78848,
        "m7g.8xlarge": 1.57696,
        "m7g.12xlarge": 2.36544,
        "m7g.16xlarge": 3.15392,
        
        # C5 family (compute optimized)
        "c5.large": 0.0935,
        "c5.xlarge": 0.187,
        "c5.2xlarge": 0.374,
        
        # C6g family (compute optimized - Graviton2)
        "c6g.large": 0.08415,
        "c6g.xlarge": 0.1683,
        "c6g.2xlarge": 0.3366,
        "c6g.4xlarge": 0.6732,
        "c6g.8xlarge": 1.3464,
        "c6g.12xlarge": 2.0196,
        "c6g.16xlarge": 2.6928,
        
        # C7g family (compute optimized - Graviton3)
        "c7g.large": 0.09295,
        "c7g.xlarge": 0.1859,
        "c7g.2xlarge": 0.3718,
        "c7g.4xlarge": 0.7436,
        "c7g.8xlarge": 1.4872,
        "c7g.12xlarge": 2.2308,
        "c7g.16xlarge": 2.9744,
        
        # R6g family (memory optimized - Graviton2)
        "r6g.large": 0.1386,
        "r6g.xlarge": 0.2772,
        "r6g.2xlarge": 0.5544,
        "r6g.4xlarge": 1.1088,
        "r6g.8xlarge": 2.2176,
        "r6g.12xlarge": 3.3264,
        "r6g.16xlarge": 4.4352,
        
        # R7g family (memory optimized - Graviton3)
        "r7g.large": 0.15246,
        "r7g.xlarge": 0.30492,
        "r7g.2xlarge": 0.60984,
        "r7g.4xlarge": 1.21968,
        "r7g.8xlarge": 2.43936,
        "r7g.12xlarge": 3.65904,
        "r7g.16xlarge": 4.87872,
        
        # G4 family (GPU - NVIDIA T4)
        "g4dn.xlarge": 0.5786,
        "g4dn.2xlarge": 0.8272,
        "g4dn.4xlarge": 1.3244,
        "g4dn.8xlarge": 2.6488,
        "g4dn.12xlarge": 3.9732,
        "g4dn.16xlarge": 5.2976,
        
        # G5 family (GPU - NVIDIA A10G)
        "g5.xlarge": 1.1066,
        "g5.2xlarge": 1.3332,
        "g5.4xlarge": 1.7864,
        "g5.8xlarge": 2.6928,
        "g5.12xlarge": 4.0392,
        "g5.16xlarge": 5.3856,
        "g5.24xlarge": 8.0784,
        
        # G6 family (GPU - NVIDIA L4)
        "g6.xlarge": 0.77,
        "g6.2xlarge": 0.99,
        "g6.4xlarge": 1.43,
        "g6.8xlarge": 2.31,
        "g6.12xlarge": 3.41,
        "g6.16xlarge": 4.51,
        "g6.24xlarge": 6.71,
    }
}

# Load Balancer pricing by region and type
LOAD_BALANCER_PRICING = {
    "us-east-1": {
        "application": 0.0225,
        "network": 0.0325,
        "classic": 0.025
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

# EBS volume pricing by region and type (per GB-month)
EBS_PRICING = {
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

# Data processing rates (per GB)
DATA_PROCESSING_RATES = {
    "us-east-1": 0.006,
    "us-west-2": 0.006,
    "eu-west-1": 0.0066
}

# New connections rates (per million)
NEW_CONNECTIONS_RATES = {
    "us-east-1": 0.006,
    "us-west-2": 0.006,
    "eu-west-1": 0.0066
}

# RDS instance pricing by region and instance class (hourly on-demand)
RDS_PRICING = {
    "us-east-1": {
        "db.t2.micro": 0.017,
        "db.t2.small": 0.034,
        "db.t2.medium": 0.068,
        "db.t2.large": 0.136,
        "db.t3.micro": 0.015,
        "db.t3.small": 0.030,
        "db.t3.medium": 0.060,
        "db.t3.large": 0.120,
        "db.m5.large": 0.192,
        "db.m5.xlarge": 0.384,
        "db.m5.2xlarge": 0.768,
        "db.r5.large": 0.252,
        "db.r5.xlarge": 0.504,
        "db.r5.2xlarge": 1.008,
    },
    "us-west-2": {
        "db.t2.micro": 0.017,
        "db.t2.small": 0.034,
        "db.t2.medium": 0.068,
        "db.t2.large": 0.136,
        "db.t3.micro": 0.015,
        "db.t3.small": 0.030,
        "db.t3.medium": 0.060,
        "db.t3.large": 0.120,
        "db.m5.large": 0.192,
        "db.m5.xlarge": 0.384,
        "db.m5.2xlarge": 0.768,
        "db.r5.large": 0.252,
        "db.r5.xlarge": 0.504,
        "db.r5.2xlarge": 1.008,
    },
    "eu-west-1": {
        "db.t2.micro": 0.0187,
        "db.t2.small": 0.0374,
        "db.t2.medium": 0.0748,
        "db.t2.large": 0.1496,
        "db.t3.micro": 0.0165,
        "db.t3.small": 0.033,
        "db.t3.medium": 0.066,
        "db.t3.large": 0.132,
        "db.m5.large": 0.2112,
        "db.m5.xlarge": 0.4224,
        "db.m5.2xlarge": 0.8448,
        "db.r5.large": 0.2772,
        "db.r5.xlarge": 0.5544,
        "db.r5.2xlarge": 1.1088,
    }
}

# RDS storage pricing by region and type (per GB-month)
RDS_STORAGE_PRICING = {
    "us-east-1": {
        "gp2": 0.23,
        "gp3": 0.115,
        "io1": 0.23,
        "io2": 0.23,
    },
    "us-west-2": {
        "gp2": 0.23,
        "gp3": 0.115,
        "io1": 0.23,
        "io2": 0.23,
    },
    "eu-west-1": {
        "gp2": 0.253,
        "gp3": 0.1265,
        "io1": 0.253,
        "io2": 0.253,
    }
}


def calculate_savings(instance_type, hours_saved=1, region="us-east-1"):
    """Calculate savings from stopping an EC2 instance"""
    region_pricing = INSTANCE_PRICING.get(region, INSTANCE_PRICING["us-east-1"])
    hourly_cost = region_pricing.get(instance_type, 0.096)
    return round(hourly_cost * hours_saved, 4)


def get_instance_hourly_cost(instance_type, region="us-east-1"):
    """Get hourly cost for an EC2 instance"""
    region_pricing = INSTANCE_PRICING.get(region, INSTANCE_PRICING["us-east-1"])
    return region_pricing.get(instance_type, 0.096)


def get_load_balancer_hourly_cost(lb_type, region="us-east-1"):
    """Get hourly base cost for a load balancer"""
    region_pricing = LOAD_BALANCER_PRICING.get(region, LOAD_BALANCER_PRICING["us-east-1"])
    return region_pricing.get(lb_type, 0.0225)


def get_ebs_volume_monthly_cost(volume_type, size_gb, region="us-east-1"):
    """Get monthly cost for an EBS volume"""
    region_pricing = EBS_PRICING.get(region, EBS_PRICING["us-east-1"])
    price_per_gb = region_pricing.get(volume_type, 0.10)
    return price_per_gb * size_gb


def get_data_processing_rate(region="us-east-1"):
    """Get data processing rate per GB"""
    return DATA_PROCESSING_RATES.get(region, 0.006)


def get_new_connections_rate(region="us-east-1"):
    """Get new connections rate per million"""
    return NEW_CONNECTIONS_RATES.get(region, 0.006)


def calculate_monthly_cost(hourly_cost):
    """Convert hourly cost to monthly"""
    return hourly_cost * 24 * 30


def calculate_annual_cost(hourly_cost):
    """Convert hourly cost to annual"""
    return hourly_cost * 24 * 365


def get_rds_instance_hourly_cost(db_instance_class, region="us-east-1"):
    """Get hourly cost for an RDS instance"""
    region_pricing = RDS_PRICING.get(region, RDS_PRICING["us-east-1"])
    return region_pricing.get(db_instance_class, 0.192)


def get_rds_storage_monthly_cost(storage_type, allocated_storage_gb, region="us-east-1"):
    """Get monthly storage cost for an RDS instance"""
    region_pricing = RDS_STORAGE_PRICING.get(region, RDS_STORAGE_PRICING["us-east-1"])
    price_per_gb = region_pricing.get(storage_type, 0.23)
    return price_per_gb * allocated_storage_gb


def get_rds_total_cost(db_instance_class, storage_type, allocated_storage_gb, region="us-east-1", multi_az=False):
    """Get total hourly cost for an RDS instance (instance + storage)"""
    instance_hourly = get_rds_instance_hourly_cost(db_instance_class, region)
    
    # Multi-AZ doubles the instance cost
    if multi_az:
        instance_hourly *= 2
    
    # Storage cost (convert monthly to hourly)
    storage_monthly = get_rds_storage_monthly_cost(storage_type, allocated_storage_gb, region)
    storage_hourly = storage_monthly / 30 / 24
    
    total_hourly = instance_hourly + storage_hourly
    
    return {
        "instance_hourly": instance_hourly,
        "storage_hourly": storage_hourly,
        "total_hourly": total_hourly,
        "total_daily": total_hourly * 24,
        "total_monthly": total_hourly * 24 * 30,
        "total_annual": total_hourly * 24 * 365
    }


def get_ec2_instance_cost(instance):
    """Calculate hourly cost for an EC2 instance"""
    instance_type = instance["instance_type"]
    region = instance["region"]
    state = instance["state"]
    
    # Get hourly cost from pricing data
    hourly_cost = get_instance_hourly_cost(instance_type, region)
    
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
    
    # Get base hourly cost from pricing data
    hourly_base_cost = get_load_balancer_hourly_cost(lb_type, region)
    
    # Add data processing charges (per GB)
    processed_bytes = metrics.get("ProcessedBytes", 0)
    processed_gb = processed_bytes / (1024 ** 3)
    data_processing_rate = get_data_processing_rate(region)
    data_processing_cost = processed_gb * data_processing_rate
    
    # Add new connections charge (per million)
    request_count = metrics.get("RequestCount", 0)
    new_connections = request_count  # Simplified: assume 1 connection per request
    new_connections_rate = get_new_connections_rate(region)
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


def get_ebs_volume_cost(volume):
    """Calculate cost for a single EBS volume"""
    volume_type = volume["volume_type"]
    size_gb = volume["size_gb"]
    region = volume["region"]
    
    # Get monthly cost from pricing data
    monthly_cost = get_ebs_volume_monthly_cost(volume_type, size_gb, region)
    
    return {
        "hourly_cost": monthly_cost / 30 / 24,
        "daily_cost": monthly_cost / 30,
        "monthly_cost": monthly_cost,
        "annual_cost": monthly_cost * 12
    }


def get_rds_instance_cost(rds):
    """Calculate hourly cost for an RDS instance"""
    db_instance_class = rds["db_instance_class"]
    region = rds["region"]
    multi_az = rds.get("multi_az", False)
    
    # Get hourly cost from pricing data
    hourly_cost = get_rds_instance_hourly_cost(db_instance_class, region)
    
    # Multi-AZ doubles the cost
    if multi_az:
        hourly_cost *= 2
    
    return {
        "hourly_cost": hourly_cost,
        "daily_cost": hourly_cost * 24,
        "monthly_cost": hourly_cost * 24 * 30,
        "annual_cost": hourly_cost * 24 * 365
    }


def get_asg_cost(asg, metrics):
    """Calculate hourly cost for an Auto Scaling Group (sum of EC2 instances)"""
    import boto3
    
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


def get_ebs_volumes_region_cost(region):
    """Calculate cost for all EBS volumes in a region"""
    import boto3
    
    ec2 = boto3.client("ec2", region_name=region)
    
    total_monthly_cost = 0.0
    volume_costs = []
    
    try:
        response = ec2.describe_volumes()
        
        for volume in response["Volumes"]:
            volume_type = volume["VolumeType"]
            size_gb = volume["Size"]
            state = volume["State"]
            
            # Get monthly cost from pricing data
            monthly_cost = get_ebs_volume_monthly_cost(volume_type, size_gb, region)
            
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
    import boto3
    
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
        ebs_cost = get_ebs_volumes_region_cost(region)
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
