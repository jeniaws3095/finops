import boto3
from botocore.exceptions import ClientError
from core.approval_request import create_approval_request, wait_for_approval

def stop_rds_instance(db_instance_id, region, require_approval=True, approval_request_id=None):
    """
    Stop an RDS instance (requires approval before execution).
    
    Args:
        db_instance_id: The RDS instance identifier
        region: AWS region where the instance is located
        require_approval: Whether to require approval before stopping (default: True)
        approval_request_id: ID of pre-approved approval request (if already approved)
    
    Returns:
        dict: Response from AWS API with status information
    """
    # Check approval if required
    if require_approval and not approval_request_id:
        print(f"⚠️ Approval required before stopping RDS instance {db_instance_id}")
        return {
            "status": "approval_required",
            "message": f"Approval request must be created and approved before stopping {db_instance_id}",
            "db_instance_id": db_instance_id
        }
    
    # If approval_request_id provided, verify it was approved
    if approval_request_id:
        from core.approval_request import get_approval_status
        status_response = get_approval_status(approval_request_id)
        
        if status_response.get("status") != "success":
            return {
                "status": "approval_check_failed",
                "message": f"Could not verify approval status",
                "db_instance_id": db_instance_id
            }
        
        if status_response.get("approval_status") != "approved":
            return {
                "status": "not_approved",
                "message": f"Approval request {approval_request_id} is not approved",
                "db_instance_id": db_instance_id
            }
    
    rds = boto3.client("rds", region_name=region)

    try:
        print(f"🚨 Sending STOP request to AWS for RDS instance {db_instance_id}")
        response = rds.stop_db_instance(DBInstanceIdentifier=db_instance_id)
        print(f"✅ Stop request sent for RDS instance {db_instance_id}")
        return {
            "status": "success",
            "message": f"Stop request sent for {db_instance_id}",
            "db_instance_id": db_instance_id,
            "approval_request_id": approval_request_id
        }
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        
        if error_code == "InvalidDBInstanceState":
            print(f"ℹ️ RDS instance already stopped or in invalid state: {db_instance_id}")
            return {
                "status": "already_stopped",
                "message": f"RDS instance {db_instance_id} is already stopped or in invalid state",
                "db_instance_id": db_instance_id
            }
        elif error_code == "DBInstanceNotFound":
            print(f"❌ RDS instance not found: {db_instance_id}")
            return {
                "status": "not_found",
                "message": f"RDS instance {db_instance_id} not found",
                "db_instance_id": db_instance_id
            }
        else:
            print(f"❌ Error stopping RDS instance {db_instance_id}: {e}")
            raise e


def delete_rds_instance(db_instance_id, region, skip_final_snapshot=False, require_approval=True, approval_request_id=None):
    """
    Delete an RDS instance (requires approval before execution).
    
    Args:
        db_instance_id: The RDS instance identifier
        region: AWS region where the instance is located
        skip_final_snapshot: Whether to skip creating a final snapshot before deletion
        require_approval: Whether to require approval before deletion (default: True)
        approval_request_id: ID of pre-approved approval request (if already approved)
    
    Returns:
        dict: Response from AWS API with status information
    """
    # Check approval if required
    if require_approval and not approval_request_id:
        print(f"⚠️ Approval required before deleting RDS instance {db_instance_id}")
        return {
            "status": "approval_required",
            "message": f"Approval request must be created and approved before deleting {db_instance_id}",
            "db_instance_id": db_instance_id
        }
    
    # If approval_request_id provided, verify it was approved
    if approval_request_id:
        from core.approval_request import get_approval_status
        status_response = get_approval_status(approval_request_id)
        
        if status_response.get("status") != "success":
            return {
                "status": "approval_check_failed",
                "message": f"Could not verify approval status",
                "db_instance_id": db_instance_id
            }
        
        if status_response.get("approval_status") != "approved":
            return {
                "status": "not_approved",
                "message": f"Approval request {approval_request_id} is not approved",
                "db_instance_id": db_instance_id
            }
    
    rds = boto3.client("rds", region_name=region)

    try:
        print(f"🚨 Sending DELETE request to AWS for RDS instance {db_instance_id}")
        response = rds.delete_db_instance(
            DBInstanceIdentifier=db_instance_id,
            SkipFinalSnapshot=skip_final_snapshot
        )
        print(f"✅ Delete request sent for RDS instance {db_instance_id}")
        return {
            "status": "success",
            "message": f"Delete request sent for {db_instance_id}",
            "db_instance_id": db_instance_id,
            "approval_request_id": approval_request_id
        }
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        
        if error_code == "InvalidDBInstanceState":
            print(f"ℹ️ RDS instance in invalid state for deletion: {db_instance_id}")
            return {
                "status": "invalid_state",
                "message": f"RDS instance {db_instance_id} is in invalid state for deletion",
                "db_instance_id": db_instance_id
            }
        elif error_code == "DBInstanceNotFound":
            print(f"❌ RDS instance not found: {db_instance_id}")
            return {
                "status": "not_found",
                "message": f"RDS instance {db_instance_id} not found",
                "db_instance_id": db_instance_id
            }
        else:
            print(f"❌ Error deleting RDS instance {db_instance_id}: {e}")
            raise e


def modify_rds_instance(db_instance_id, region, db_instance_class, require_approval=True, approval_request_id=None):
    """
    Downsize an RDS instance to a smaller instance class (requires approval).
    
    Args:
        db_instance_id: The RDS instance identifier
        region: AWS region where the instance is located
        db_instance_class: Target instance class (e.g., 'db.t3.small')
        require_approval: Whether to require approval before modification (default: True)
        approval_request_id: ID of pre-approved approval request (if already approved)
    
    Returns:
        dict: Response from AWS API with status information
    """
    # Check approval if required
    if require_approval and not approval_request_id:
        print(f"⚠️ Approval required before modifying RDS instance {db_instance_id}")
        return {
            "status": "approval_required",
            "message": f"Approval request must be created and approved before modifying {db_instance_id}",
            "db_instance_id": db_instance_id
        }
    
    # If approval_request_id provided, verify it was approved
    if approval_request_id:
        from core.approval_request import get_approval_status
        status_response = get_approval_status(approval_request_id)
        
        if status_response.get("status") != "success":
            return {
                "status": "approval_check_failed",
                "message": f"Could not verify approval status",
                "db_instance_id": db_instance_id
            }
        
        if status_response.get("approval_status") != "approved":
            return {
                "status": "not_approved",
                "message": f"Approval request {approval_request_id} is not approved",
                "db_instance_id": db_instance_id
            }
    
    rds = boto3.client("rds", region_name=region)

    try:
        print(f"🚨 Sending MODIFY request to AWS for RDS instance {db_instance_id}")
        print(f"   Downsizing to {db_instance_class}")
        response = rds.modify_db_instance(
            DBInstanceIdentifier=db_instance_id,
            DBInstanceClass=db_instance_class,
            ApplyImmediately=False  # Apply during maintenance window
        )
        print(f"✅ Modify request sent for RDS instance {db_instance_id}")
        return {
            "status": "success",
            "message": f"Modify request sent for {db_instance_id} to {db_instance_class}",
            "db_instance_id": db_instance_id,
            "new_instance_class": db_instance_class,
            "approval_request_id": approval_request_id
        }
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        
        if error_code == "InvalidDBInstanceState":
            print(f"ℹ️ RDS instance in invalid state for modification: {db_instance_id}")
            return {
                "status": "invalid_state",
                "message": f"RDS instance {db_instance_id} is in invalid state for modification",
                "db_instance_id": db_instance_id
            }
        elif error_code == "DBInstanceNotFound":
            print(f"❌ RDS instance not found: {db_instance_id}")
            return {
                "status": "not_found",
                "message": f"RDS instance {db_instance_id} not found",
                "db_instance_id": db_instance_id
            }
        else:
            print(f"❌ Error modifying RDS instance {db_instance_id}: {e}")
            raise e
