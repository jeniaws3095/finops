import boto3
from botocore.exceptions import ClientError
from core.approval_request import create_approval_request, get_approval_status

def stop_instance(instance_id, region, require_approval=True, approval_request_id=None):
    """
    Stop an EC2 instance (requires approval before execution).
    
    Args:
        instance_id: The EC2 instance identifier
        region: AWS region where the instance is located
        require_approval: Whether to require approval before stopping (default: True)
        approval_request_id: ID of pre-approved approval request (if already approved)
    
    Returns:
        dict: Response from AWS API with status information
    """
    # Check approval if required
    if require_approval and not approval_request_id:
        print(f"⚠️ Approval required before stopping EC2 instance {instance_id}")
        return {
            "status": "approval_required",
            "message": f"Approval request must be created and approved before stopping {instance_id}",
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

    try:
        print(f"🚨 Sending STOP request to AWS for {instance_id}")
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f"✅ Stop request sent for {instance_id}")
        return {
            "status": "success",
            "message": f"Stop request sent for {instance_id}",
            "instance_id": instance_id,
            "approval_request_id": approval_request_id
        }
    except ClientError as e:
        if e.response["Error"]["Code"] == "IncorrectInstanceState":
            print(f"ℹ️ Instance already stopped: {instance_id}")
            return {
                "status": "already_stopped",
                "message": f"Instance {instance_id} is already stopped",
                "instance_id": instance_id
            }
        else:
            print(f"❌ Error stopping instance {instance_id}: {e}")
            raise e


def resize_instance(instance_id, region, new_instance_type, require_approval=True, approval_request_id=None):
    """
    Resize an EC2 instance to a different instance type (requires approval).
    
    Args:
        instance_id: The EC2 instance identifier
        region: AWS region where the instance is located
        new_instance_type: Target instance type (e.g., 't2.medium')
        require_approval: Whether to require approval before resizing (default: True)
        approval_request_id: ID of pre-approved approval request (if already approved)
    
    Returns:
        dict: Response from AWS API with status information
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
        print(f"\n� Fetching current instance details for {instance_id}...")
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        current_instance_type = instance['InstanceType']
        current_state = instance['State']['Name']
        
        print(f"   Current Type: {current_instance_type}")
        print(f"   Current State: {current_state}")
        print(f"   Target Type: {new_instance_type}")
        
        resize_steps.append({
            "step": "fetch_details",
            "status": "completed",
            "current_type": current_instance_type,
            "current_state": current_state
        })
        
        # Step 1: Stop the instance (required for resize)
        print(f"\n🚨 [STEP 1/4] Stopping EC2 instance {instance_id}...")
        if current_state != "stopped":
            ec2.stop_instances(InstanceIds=[instance_id])
            print(f"   ⏳ Waiting for instance to stop...")
            
            # Wait for instance to stop (with timeout)
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
        
        # Wait for instance to start
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
        
        return {
            "status": "success",
            "message": f"Resize completed successfully for {instance_id}",
            "instance_id": instance_id,
            "old_instance_type": current_instance_type,
            "new_instance_type": new_instance_type,
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


def change_instance_type(instance_id, region, new_instance_type, require_approval=True, approval_request_id=None):
    """
    Alias for resize_instance for backward compatibility.
    
    Args:
        instance_id: The EC2 instance identifier
        region: AWS region where the instance is located
        new_instance_type: Target instance type (e.g., 't2.medium')
        require_approval: Whether to require approval before changing (default: True)
        approval_request_id: ID of pre-approved approval request (if already approved)
    
    Returns:
        dict: Response from AWS API with status information
    """
    return resize_instance(instance_id, region, new_instance_type, require_approval, approval_request_id)
