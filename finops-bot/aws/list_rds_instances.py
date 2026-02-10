import boto3

def get_rds_instances():
    """Discover all RDS instances across regions"""
    instances = []
    
    # Get all regions
    ec2 = boto3.client("ec2")
    regions = [region["RegionName"] for region in ec2.describe_regions()["Regions"]]
    
    for region in regions:
        try:
            rds = boto3.client("rds", region_name=region)
            paginator = rds.get_paginator("describe_db_instances")
            
            for page in paginator.paginate():
                for db in page.get("DBInstances", []):
                    instances.append({
                        "db_instance_id": db["DBInstanceIdentifier"],
                        "db_instance_arn": db["DBInstanceArn"],
                        "engine": db["Engine"],
                        "engine_version": db["EngineVersion"],
                        "db_instance_class": db["DBInstanceClass"],
                        "region": region,
                        "availability_zone": db["AvailabilityZone"],
                        "db_name": db.get("DBName", ""),
                        "status": db["DBInstanceStatus"],
                        "allocated_storage_gb": db.get("AllocatedStorage", 0),
                        "storage_type": db.get("StorageType", "gp2"),
                        "iops": db.get("Iops"),
                        "multi_az": db.get("MultiAZ", False),
                        "backup_retention_days": db.get("BackupRetentionPeriod", 0),
                        "publicly_accessible": db.get("PubliclyAccessible", False),
                        "create_time": str(db["InstanceCreateTime"]),
                        "preferred_backup_window": db.get("PreferredBackupWindow", ""),
                        "preferred_maintenance_window": db.get("PreferredMaintenanceWindow", ""),
                        "read_replicas": db.get("ReadReplicaDBInstanceIdentifiers", []),
                        "tags": {tag["Key"]: tag["Value"] for tag in db.get("TagList", [])}
                    })
        
        except Exception as e:
            print(f"❌ Error discovering RDS instances in {region}: {e}")
            continue
    
    return instances
