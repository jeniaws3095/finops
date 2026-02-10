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
