import boto3

def get_auto_scaling_groups():
    """Discover all Auto Scaling Groups across regions"""
    asgs = []
    
    # Get all regions
    ec2 = boto3.client("ec2")
    regions = [region["RegionName"] for region in ec2.describe_regions()["Regions"]]
    
    for region in regions:
        try:
            autoscaling = boto3.client("autoscaling", region_name=region)
            paginator = autoscaling.get_paginator("describe_auto_scaling_groups")
            
            for page in paginator.paginate():
                for asg in page.get("AutoScalingGroups", []):
                    asgs.append({
                        "asg_name": asg["AutoScalingGroupName"],
                        "asg_arn": asg["AutoScalingGroupARN"],
                        "region": region,
                        "min_size": asg["MinSize"],
                        "max_size": asg["MaxSize"],
                        "desired_capacity": asg["DesiredCapacity"],
                        "current_instances": len(asg["Instances"]),
                        "instance_ids": [inst["InstanceId"] for inst in asg["Instances"]],
                        "instance_type": asg.get("LaunchConfigurationName") or asg.get("LaunchTemplate", {}).get("LaunchTemplateName"),
                        "vpc_zone_identifier": asg.get("VPCZoneIdentifier", ""),
                        "health_check_type": asg.get("HealthCheckType", "ELB"),
                        "health_check_grace_period": asg.get("HealthCheckGracePeriod", 0),
                        "created_time": str(asg["CreatedTime"]),
                        "suspended_processes": [proc["ProcessName"] for proc in asg.get("SuspendedProcesses", [])],
                        "load_balancer_names": asg.get("LoadBalancerNames", []),
                        "target_group_arns": asg.get("TargetGroupARNs", [])
                    })
        
        except Exception as e:
            print(f"❌ Error discovering Auto Scaling Groups in {region}: {e}")
            continue
    
    return asgs
