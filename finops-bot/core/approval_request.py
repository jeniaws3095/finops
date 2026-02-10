import requests
from datetime import datetime
from typing import Dict, Any

def create_approval_request(resource_data: Dict[str, Any], action: str, reason: str) -> Dict[str, Any]:
    """
    Create an approval request before executing optimization actions.
    
    Args:
        resource_data: Dictionary containing resource details (id, type, metrics, etc.)
        action: The action to be taken ('stop', 'delete', 'resize', etc.)
        reason: Reason why this resource is flagged for optimization
    
    Returns:
        dict: Response from backend API with approval request details
    """
    try:
        approval_payload = {
            "resource_id": resource_data.get("id"),
            "resource_name": resource_data.get("name"),
            "resource_type": resource_data.get("type"),
            "service_type": resource_data.get("service_type"),
            "action": action,
            "reason": reason,
            "metrics": resource_data.get("metrics", {}),
            "estimated_savings": resource_data.get("estimated_savings", 0),
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = requests.post(
            "http://localhost:5000/api/approval-requests",
            json=approval_payload,
            timeout=5
        )
        
        if response.status_code == 201:
            print(f"✅ Approval request created for {resource_data.get('name')}")
            return {
                "status": "success",
                "approval_request_id": response.json().get("id"),
                "message": f"Approval request created. Awaiting manager review."
            }
        else:
            print(f"⚠️ Failed to create approval request: {response.status_code}")
            return {
                "status": "failed",
                "message": f"Failed to create approval request: {response.text}"
            }
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating approval request: {e}")
        return {
            "status": "error",
            "message": f"Error communicating with backend: {str(e)}"
        }


def get_approval_status(approval_request_id: str) -> Dict[str, Any]:
    """
    Check the status of an approval request.
    
    Args:
        approval_request_id: The ID of the approval request
    
    Returns:
        dict: Approval request status and decision
    """
    try:
        response = requests.get(
            f"http://localhost:5000/api/approval-requests/{approval_request_id}",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "approval_status": data.get("status"),
                "decision": data.get("decision"),
                "decided_by": data.get("decided_by"),
                "reasoning": data.get("reasoning")
            }
        else:
            return {
                "status": "not_found",
                "message": f"Approval request not found: {approval_request_id}"
            }
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking approval status: {e}")
        return {
            "status": "error",
            "message": f"Error communicating with backend: {str(e)}"
        }


def wait_for_approval(approval_request_id: str, max_wait_seconds: int = 300) -> bool:
    """
    Wait for an approval request to be reviewed (with timeout).
    
    Args:
        approval_request_id: The ID of the approval request
        max_wait_seconds: Maximum time to wait for approval (default: 5 minutes)
    
    Returns:
        bool: True if approved, False if rejected or timeout
    """
    import time
    
    start_time = time.time()
    check_interval = 10  # Check every 10 seconds
    
    while time.time() - start_time < max_wait_seconds:
        status_response = get_approval_status(approval_request_id)
        
        if status_response.get("status") == "success":
            approval_status = status_response.get("approval_status")
            
            if approval_status == "approved":
                print(f"✅ Approval request {approval_request_id} was APPROVED")
                print(f"   Reasoning: {status_response.get('reasoning', 'N/A')}")
                return True
            
            elif approval_status == "rejected":
                print(f"❌ Approval request {approval_request_id} was REJECTED")
                print(f"   Reasoning: {status_response.get('reasoning', 'N/A')}")
                return False
        
        # Still pending, wait and check again
        print(f"⏳ Approval pending... checking again in {check_interval}s")
        time.sleep(check_interval)
    
    print(f"⏱️ Approval request {approval_request_id} timed out after {max_wait_seconds}s")
    return False
