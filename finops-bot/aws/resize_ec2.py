import boto3
from botocore.exceptions import ClientError
from core.approval_request import get_approval_status
from utils.pricing import get_instance_hourly_cost, calculate_monthly_cost

def get_resize_options(instance_type: str, region: str) -> dict:
    """
    Get available resize options for an EC2 instance.
    
    Args:
        instance_type: Current instance type (e.g., 't2.large')
        region: AWS region
    
    Returns:
        dict: Available resize options with cost comparisons
    """
    # Downsizing hierarchy for common instance families
    downsizing_map = {
        # t2 family
        "t2.2xlarge": ["t2.xlarge", "t2.large", "t2.medium"],
        "t2.xlarge": ["t2.large", "t2.medium", "t2.small"],
        "t2.large": ["t2.medium", "t2.small", "t2.micro"],
        "t2.medium": ["t2.small", "t2.micro"],
        "t2.small": ["t2.micro"],
        
        # t3 family
        "t3.2xlarge": ["t3.xlarge", "t3.large", "t3.medium"],
        "t3.xlarge": ["t3.large", "t3.medium", "t3.small"],
        "t3.large": ["t3.medium", "t3.small", "t3.micro"],
        "t3.medium": ["t3.small", "t3.micro"],
        "t3.small": ["t3.micro"],
        
        # t4g family (burstable - Graviton2)
        "t4g.2xlarge": ["t4g.xlarge", "t4g.large", "t4g.medium"],
        "t4g.xlarge": ["t4g.large", "t4g.medium", "t4g.small"],
        "t4g.large": ["t4g.medium", "t4g.small", "t4g.micro"],
        "t4g.medium": ["t4g.small", "t4g.micro"],
        "t4g.small": ["t4g.micro"],
        
        # m5 family
        "m5.2xlarge": ["m5.xlarge", "m5.large"],
        "m5.xlarge": ["m5.large"],
        
        # m6g family (general purpose - Graviton2)
        "m6g.16xlarge": ["m6g.12xlarge", "m6g.8xlarge"],
        "m6g.12xlarge": ["m6g.8xlarge", "m6g.4xlarge"],
        "m6g.8xlarge": ["m6g.4xlarge", "m6g.2xlarge"],
        "m6g.4xlarge": ["m6g.2xlarge", "m6g.xlarge"],
        "m6g.2xlarge": ["m6g.xlarge", "m6g.large"],
        "m6g.xlarge": ["m6g.large"],
        
        # m7g family (general purpose - Graviton3)
        "m7g.16xlarge": ["m7g.12xlarge", "m7g.8xlarge"],
        "m7g.12xlarge": ["m7g.8xlarge", "m7g.4xlarge"],
        "m7g.8xlarge": ["m7g.4xlarge", "m7g.2xlarge"],
        "m7g.4xlarge": ["m7g.2xlarge", "m7g.xlarge"],
        "m7g.2xlarge": ["m7g.xlarge", "m7g.large"],
        "m7g.xlarge": ["m7g.large"],
        
        # c5 family
        "c5.2xlarge": ["c5.xlarge", "c5.large"],
        "c5.xlarge": ["c5.large"],
        
        # c6g family (compute optimized - Graviton2)
        "c6g.16xlarge": ["c6g.12xlarge", "c6g.8xlarge"],
        "c6g.12xlarge": ["c6g.8xlarge", "c6g.4xlarge"],
        "c6g.8xlarge": ["c6g.4xlarge", "c6g.2xlarge"],
        "c6g.4xlarge": ["c6g.2xlarge", "c6g.xlarge"],
        "c6g.2xlarge": ["c6g.xlarge", "c6g.large"],
        "c6g.xlarge": ["c6g.large"],
        
        # c7g family (compute optimized - Graviton3)
        "c7g.16xlarge": ["c7g.12xlarge", "c7g.8xlarge"],
        "c7g.12xlarge": ["c7g.8xlarge", "c7g.4xlarge"],
        "c7g.8xlarge": ["c7g.4xlarge", "c7g.2xlarge"],
        "c7g.4xlarge": ["c7g.2xlarge", "c7g.xlarge"],
        "c7g.2xlarge": ["c7g.xlarge", "c7g.large"],
        "c7g.xlarge": ["c7g.large"],
        
        # r6g family (memory optimized - Graviton2)
        "r6g.16xlarge": ["r6g.12xlarge", "r6g.8xlarge"],
        "r6g.12xlarge": ["r6g.8xlarge", "r6g.4xlarge"],
        "r6g.8xlarge": ["r6g.4xlarge", "r6g.2xlarge"],
        "r6g.4xlarge": ["r6g.2xlarge", "r6g.xlarge"],
        "r6g.2xlarge": ["r6g.xlarge", "r6g.large"],
        "r6g.xlarge": ["r6g.large"],
        
        # r7g family (memory optimized - Graviton3)
        "r7g.16xlarge": ["r7g.12xlarge", "r7g.8xlarge"],
        "r7g.12xlarge": ["r7g.8xlarge", "r7g.4xlarge"],
        "r7g.8xlarge": ["r7g.4xlarge", "r7g.2xlarge"],
        "r7g.4xlarge": ["r7g.2xlarge", "r7g.xlarge"],
        "r7g.2xlarge": ["r7g.xlarge", "r7g.large"],
        "r7g.xlarge": ["r7g.large"],
        
        # g4dn family (GPU - NVIDIA T4)
        "g4dn.16xlarge": ["g4dn.12xlarge", "g4dn.8xlarge"],
        "g4dn.12xlarge": ["g4dn.8xlarge", "g4dn.4xlarge"],
        "g4dn.8xlarge": ["g4dn.4xlarge", "g4dn.2xlarge"],
        "g4dn.4xlarge": ["g4dn.2xlarge", "g4dn.xlarge"],
        "g4dn.2xlarge": ["g4dn.xlarge"],
        
        # g5 family (GPU - NVIDIA A10G)
        "g5.24xlarge": ["g5.16xlarge", "g5.12xlarge"],
        "g5.16xlarge": ["g5.12xlarge", "g5.8xlarge"],
        "g5.12xlarge": ["g5.8xlarge", "g5.4xlarge"],
        "g5.8xlarge": ["g5.4xlarge", "g5.2xlarge"],
        "g5.4xlarge": ["g5.2xlarge", "g5.xlarge"],
        "g5.2xlarge": ["g5.xlarge"],
        
        # g6 family (GPU - NVIDIA L4)
        "g6.24xlarge": ["g6.16xlarge", "g6.12xlarge"],
        "g6.16xlarge": ["g6.12xlarge", "g6.8xlarge"],
        "g6.12xlarge": ["g6.8xlarge", "g6.4xlarge"],
        "g6.8xlarge": ["g6.4xlarge", "g6.2xlarge"],
        "g6.4xlarge": ["g6.2xlarge", "g6.xlarge"],
        "g6.2xlarge": ["g6.xlarge"],
    }
    
    current_hourly = get_instance_hourly_cost(instance_type, region)
    current_monthly = calculate_monthly_cost(current_hourly)
    
    resize_options = []
    available_types = downsizing_map.get(instance_type, [])
    
    for target_type in available_types:
        target_hourly = get_instance_hourly_cost(target_type, region)
        target_monthly = calculate_monthly_cost(target_hourly)
        savings = current_monthly - target_monthly
        savings_percent = (savings / current_monthly * 100) if current_monthly > 0 else 0
        
        resize_options.append({
            "target_instance_type": target_type,
            "current_monthly_cost": current_monthly,
            "target_monthly_cost": target_monthly,
            "estimated_monthly_savings": savings,
            "estimated_annual_savings": savings * 12,
            "savings_percentage": round(savings_percent, 2),
            "downtime_estimate": "2-5 minutes"
        })
    
    return {
        "current_instance_type": instance_type,
        "current_monthly_cost": current_monthly,
        "current_annual_cost": current_monthly * 12,
        "resize_options": resize_options,
        "total_options": len(resize_options)
    }


def resize_instance_with_recommendation(instance_id: str, region: str, 
                                       new_instance_type: str, 
                                       require_approval: bool = True, 
                                       approval_request_id: str = None) -> dict:
    """
    Resize an EC2 instance with detailed logging and recommendations.
    
    Args:
        instance_id: The EC2 instance identifier
        region: AWS region where the instance is located
        new_instance_type: Target instance type (e.g., 't2.medium')
        require_approval: Whether to require approval before resizing (default: True)
        approval_request_id: ID of pre-approved approval request (if already approved)
    
    Returns:
        dict: Response with resize status and details
    """
    # Check approval if required
    if require_approval and not approval_request_id:
        print(f"⚠️ Approval required before resizing EC2 instance {instance_id}")
        return {
            "status": "approval_required",
            "message": f"Approval request must be created and approved before resizing {instance_id}",
            "instance_id": instance_id
        }
    
    # If approval_request_id provided, verify it was approved
    if approval_request_id:
        status_response = get_approval_status(approval_request_id)
        
        if status_response.get("status") != "success":
            return {
                "status": "approval_check_failed",
                "message": f"Could not verify approval status",
                "instance_id": instance_id
            }
        
        if status_response.get("approval_status") != "approved":
            return {
                "status": "not_approved",
                "message": f"Approval request {approval_request_id} is not approved",
                "instance_id": instance_id
            }
    
    ec2 = boto3.client("ec2", region_name=region)
    resize_steps = []

    try:
        # Get current instance details
        print(f"\n📋 Fetching current instance details for {instance_id}...")
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        current_instance_type = instance['InstanceType']
        current_state = instance['State']['Name']
        
        print(f"   Current Type: {current_instance_type}")
        print(f"   Current State: {current_state}")
        print(f"   Target Type: {new_instance_type}")
        
        # Get cost comparison
        current_hourly = get_instance_hourly_cost(current_instance_type, region)
        current_monthly = calculate_monthly_cost(current_hourly)
        target_hourly = get_instance_hourly_cost(new_instance_type, region)
        target_monthly = calculate_monthly_cost(target_hourly)
        monthly_savings = current_monthly - target_monthly
        
        print(f"   Current Cost: ${current_monthly:.2f}/month")
        print(f"   Target Cost: ${target_monthly:.2f}/month")
        print(f"   Monthly Savings: ${monthly_savings:.2f}")
        
        resize_steps.append({
            "step": "fetch_details",
            "status": "completed",
            "current_type": current_instance_type,
            "current_state": current_state,
            "current_monthly_cost": current_monthly,
            "target_monthly_cost": target_monthly,
            "monthly_savings": monthly_savings
        })
        
        # Step 1: Stop the instance (required for resize)
        print(f"\n🚨 [STEP 1/4] Stopping EC2 instance {instance_id}...")
        if current_state != "stopped":
            ec2.stop_instances(InstanceIds=[instance_id])
            print(f"   ⏳ Waiting for instance to stop...")
            
            waiter = ec2.get_waiter('instance_stopped')
            waiter.wait(InstanceIds=[instance_id])
            print(f"   ✅ Instance stopped successfully")
        else:
            print(f"   ℹ️ Instance already stopped")
        
        resize_steps.append({
            "step": "stop_instance",
            "status": "completed"
        })
        
        # Step 2: Change instance type
        print(f"\n🚨 [STEP 2/4] Changing instance type from {current_instance_type} to {new_instance_type}...")
        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            InstanceType={'Value': new_instance_type}
        )
        print(f"   ✅ Instance type changed successfully")
        
        resize_steps.append({
            "step": "change_type",
            "status": "completed",
            "old_type": current_instance_type,
            "new_type": new_instance_type
        })
        
        # Step 3: Restart the instance
        print(f"\n🚨 [STEP 3/4] Restarting EC2 instance {instance_id}...")
        ec2.start_instances(InstanceIds=[instance_id])
        print(f"   ⏳ Waiting for instance to start...")
        
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        print(f"   ✅ Instance started successfully")
        
        resize_steps.append({
            "step": "start_instance",
            "status": "completed"
        })
        
        # Step 4: Verify new instance type
        print(f"\n🚨 [STEP 4/4] Verifying instance type...")
        response = ec2.describe_instances(InstanceIds=[instance_id])
        updated_instance = response['Reservations'][0]['Instances'][0]
        updated_type = updated_instance['InstanceType']
        updated_state = updated_instance['State']['Name']
        
        print(f"   New Type: {updated_type}")
        print(f"   New State: {updated_state}")
        
        if updated_type == new_instance_type:
            print(f"   ✅ Verification successful")
        else:
            print(f"   ⚠️ Type mismatch - expected {new_instance_type}, got {updated_type}")
        
        resize_steps.append({
            "step": "verify_type",
            "status": "completed",
            "verified_type": updated_type,
            "verified_state": updated_state
        })
        
        print(f"\n✅ RESIZE COMPLETED SUCCESSFULLY")
        print(f"   Instance: {instance_id}")
        print(f"   Old Type: {current_instance_type}")
        print(f"   New Type: {new_instance_type}")
        print(f"   Monthly Savings: ${monthly_savings:.2f}")
        print(f"   Annual Savings: ${monthly_savings * 12:.2f}")
        
        return {
            "status": "success",
            "message": f"Resize completed successfully for {instance_id}",
            "instance_id": instance_id,
            "old_instance_type": current_instance_type,
            "new_instance_type": new_instance_type,
            "current_monthly_cost": current_monthly,
            "target_monthly_cost": target_monthly,
            "estimated_monthly_savings": monthly_savings,
            "estimated_annual_savings": monthly_savings * 12,
            "approval_request_id": approval_request_id,
            "steps": resize_steps
        }
    
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        
        if error_code == "IncorrectInstanceState":
            print(f"\n❌ Instance in invalid state for resize: {instance_id}")
            return {
                "status": "invalid_state",
                "message": f"Instance {instance_id} is in invalid state for resize",
                "instance_id": instance_id,
                "steps": resize_steps
            }
        elif error_code == "InvalidInstanceID.NotFound":
            print(f"\n❌ Instance not found: {instance_id}")
            return {
                "status": "not_found",
                "message": f"Instance {instance_id} not found",
                "instance_id": instance_id,
                "steps": resize_steps
            }
        else:
            print(f"\n❌ Error resizing instance {instance_id}: {e}")
            raise e


def get_resize_recommendation(instance_id: str, region: str, current_instance_type: str) -> dict:
    """
    Get resize recommendations for an EC2 instance.
    
    Args:
        instance_id: The EC2 instance identifier
        region: AWS region
        current_instance_type: Current instance type
    
    Returns:
        dict: Resize recommendations with cost analysis
    """
    print(f"\n📊 Analyzing resize options for {instance_id} ({current_instance_type})...")
    
    options = get_resize_options(current_instance_type, region)
    
    if options['total_options'] == 0:
        print(f"   ℹ️ No resize options available - already at smallest instance type")
        return {
            "instance_id": instance_id,
            "current_instance_type": current_instance_type,
            "resize_available": False,
            "message": "Instance is already at the smallest available type"
        }
    
    # Find best option (most savings)
    best_option = max(options['resize_options'], key=lambda x: x['estimated_monthly_savings'])
    
    print(f"\n💡 RESIZE RECOMMENDATIONS:")
    print(f"   Current Type: {current_instance_type}")
    print(f"   Current Cost: ${options['current_monthly_cost']:.2f}/month")
    print(f"\n   Available Options:")
    
    for i, option in enumerate(options['resize_options'], 1):
        print(f"   {i}. {option['target_instance_type']}")
        print(f"      Cost: ${option['target_monthly_cost']:.2f}/month")
        print(f"      Savings: ${option['estimated_monthly_savings']:.2f}/month ({option['savings_percentage']}%)")
        print(f"      Annual Savings: ${option['estimated_annual_savings']:.2f}")
    
    print(f"\n   ⭐ BEST OPTION: {best_option['target_instance_type']}")
    print(f"      Monthly Savings: ${best_option['estimated_monthly_savings']:.2f}")
    print(f"      Annual Savings: ${best_option['estimated_annual_savings']:.2f}")
    
    return {
        "instance_id": instance_id,
        "current_instance_type": current_instance_type,
        "resize_available": True,
        "resize_options": options['resize_options'],
        "best_option": {
            "target_instance_type": best_option['target_instance_type'],
            "estimated_monthly_savings": best_option['estimated_monthly_savings'],
            "estimated_annual_savings": best_option['estimated_annual_savings'],
            "savings_percentage": best_option['savings_percentage']
        }
    }
