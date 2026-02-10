import boto3

def get_load_balancers():
    """Discover all load balancers (ALB, NLB, Classic LB) across regions"""
    load_balancers = []
    
    # Get all regions
    ec2 = boto3.client("ec2")
    regions = [region["RegionName"] for region in ec2.describe_regions()["Regions"]]
    
    for region in regions:
        try:
            # ALB and NLB (ELBv2)
            elbv2 = boto3.client("elbv2", region_name=region)
            response = elbv2.describe_load_balancers()
            
            for lb in response.get("LoadBalancers", []):
                load_balancers.append({
                    "load_balancer_arn": lb["LoadBalancerArn"],
                    "load_balancer_name": lb["LoadBalancerName"],
                    "load_balancer_type": lb["Type"],  # application, network, gateway
                    "scheme": lb["Scheme"],  # internet-facing, internal
                    "state": lb["State"]["Code"],  # active, provisioning, failed, loading
                    "region": region,
                    "vpc_id": lb.get("VpcId"),
                    "created_time": str(lb["CreatedTime"])
                })
            
            # Classic Load Balancers (ELB)
            elb = boto3.client("elb", region_name=region)
            response = elb.describe_load_balancers()
            
            for lb in response.get("LoadBalancerDescriptions", []):
                load_balancers.append({
                    "load_balancer_arn": f"arn:aws:elasticloadbalancing:{region}:account:loadbalancer/{lb['LoadBalancerName']}",
                    "load_balancer_name": lb["LoadBalancerName"],
                    "load_balancer_type": "classic",
                    "scheme": lb["Scheme"],
                    "state": "active",  # Classic LBs don't have explicit state
                    "region": region,
                    "vpc_id": lb.get("VPCId"),
                    "created_time": str(lb["CreatedTime"])
                })
        
        except Exception as e:
            print(f"❌ Error discovering load balancers in {region}: {e}")
            continue
    
    return load_balancers
