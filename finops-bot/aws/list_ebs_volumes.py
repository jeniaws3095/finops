import boto3

def get_ebs_volumes():
    """Discover all EBS volumes across regions"""
    volumes = []
    
    # Get all regions
    ec2 = boto3.client("ec2")
    regions = [region["RegionName"] for region in ec2.describe_regions()["Regions"]]
    
    for region in regions:
        try:
            ec2_region = boto3.client("ec2", region_name=region)
            paginator = ec2_region.get_paginator("describe_volumes")
            
            for page in paginator.paginate():
                for volume in page.get("Volumes", []):
                    # Get attachment info
                    attachments = volume.get("Attachments", [])
                    attached_instance_id = None
                    attached_device = None
                    
                    if attachments:
                        attached_instance_id = attachments[0].get("InstanceId")
                        attached_device = attachments[0].get("Device")
                    
                    volumes.append({
                        "volume_id": volume["VolumeId"],
                        "volume_type": volume["VolumeType"],
                        "size_gb": volume["Size"],
                        "state": volume["State"],
                        "region": region,
                        "availability_zone": volume["AvailabilityZone"],
                        "create_time": str(volume["CreateTime"]),
                        "encrypted": volume.get("Encrypted", False),
                        "iops": volume.get("Iops"),
                        "throughput": volume.get("Throughput"),
                        "attached_instance_id": attached_instance_id,
                        "attached_device": attached_device,
                        "snapshot_id": volume.get("SnapshotId"),
                        "tags": {tag["Key"]: tag["Value"] for tag in volume.get("Tags", [])}
                    })
        
        except Exception as e:
            print(f"❌ Error discovering EBS volumes in {region}: {e}")
            continue
    
    return volumes
