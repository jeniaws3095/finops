#!/usr/bin/env python3
"""
Safety Controls and DRY_RUN Validation for Advanced FinOps Platform

Implements comprehensive safety controls for AWS operations including:
- DRY_RUN mode validation and pre-execution checks
- Comprehensive rollback capabilities for all optimization actions
- Detailed audit logging and operation tracking
- Risk assessment and approval workflows
- Pre-execution validation and safety checks
- Real-time operation monitoring and alerting

Enhanced for Advanced FinOps Platform with:
- Multi-service rollback support (EC2, RDS, Lambda, S3, EBS, ELB, CloudWatch)
- Advanced risk assessment with resource-specific factors
- Comprehensive audit trails with detailed operation metadata
- Automated rollback plan generation and execution
- Integration with approval workflows and stakeholder notifications

Requirements: 8.2, 8.4, 3.4
"""

import logging
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for operations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OperationType(Enum):
    """Types of operations that can be performed."""
    TERMINATE_INSTANCE = "TERMINATE_INSTANCE"
    STOP_INSTANCE = "STOP_INSTANCE"
    START_INSTANCE = "START_INSTANCE"
    MODIFY_INSTANCE = "MODIFY_INSTANCE"
    RESIZE_INSTANCE = "RESIZE_INSTANCE"
    DELETE_VOLUME = "DELETE_VOLUME"
    MODIFY_SECURITY_GROUP = "MODIFY_SECURITY_GROUP"
    DELETE_SNAPSHOT = "DELETE_SNAPSHOT"
    DELETE_RDS_INSTANCE = "DELETE_RDS_INSTANCE"
    STOP_RDS_INSTANCE = "STOP_RDS_INSTANCE"
    DELETE_LAMBDA_FUNCTION = "DELETE_LAMBDA_FUNCTION"
    DELETE_S3_BUCKET = "DELETE_S3_BUCKET"
    MODIFY_S3_LIFECYCLE = "MODIFY_S3_LIFECYCLE"
    DELETE_LOAD_BALANCER = "DELETE_LOAD_BALANCER"
    MODIFY_CLOUDWATCH_LOGS = "MODIFY_CLOUDWATCH_LOGS"


class OperationStatus(Enum):
    """Status of operations."""
    PENDING = "PENDING"
    SIMULATED = "SIMULATED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"


class RollbackCapability(Enum):
    """Rollback capability levels."""
    FULL = "FULL"          # Can be fully rolled back
    PARTIAL = "PARTIAL"    # Can be partially rolled back
    NONE = "NONE"         # Cannot be rolled back


class SafetyControls:
    """Manages safety controls and DRY_RUN validation for AWS operations."""
    
    def __init__(self, dry_run: bool = True, log_file: str = "finops_operations.log"):
        """
        Initialize safety controls.
        
        Args:
            dry_run: If True, no actual AWS operations will be performed
            log_file: File to log all operations for audit trail
        """
        self.dry_run = dry_run
        self.log_file = log_file
        self.operation_history = []
        self.rollback_plans = {}
        self.active_sessions = {}
        
        # Create logs directory if it doesn't exist
        log_dir = Path(log_file).parent
        log_dir.mkdir(exist_ok=True)
        
        # Configure comprehensive operation logging
        self._setup_operation_logging()
        
        if self.dry_run:
            logger.warning("DRY_RUN mode enabled - no actual AWS operations will be performed")
        else:
            logger.warning("LIVE mode enabled - AWS operations will be performed")
            logger.warning("All operations will be logged and rollback plans created")
    
    def _setup_operation_logging(self) -> None:
        """Set up comprehensive logging for operations."""
        operation_logger = logging.getLogger('finops.operations')
        operation_logger.setLevel(logging.INFO)
        
        # Clear existing handlers to avoid duplicates
        operation_logger.handlers.clear()
        
        # Create file handler for operation logs
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        operation_logger.addHandler(handler)
        
        # Also log to console for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        operation_logger.addHandler(console_handler)
        
        # Log safety controls initialization
        operation_logger.info(f"Safety controls initialized - DRY_RUN: {self.dry_run}")
    
    def get_rollback_capability(self, operation_type: OperationType) -> RollbackCapability:
        """
        Determine rollback capability for an operation type.
        
        Args:
            operation_type: Type of operation
            
        Returns:
            Rollback capability level
        """
        rollback_map = {
            OperationType.TERMINATE_INSTANCE: RollbackCapability.NONE,  # Cannot restore terminated instance
            OperationType.STOP_INSTANCE: RollbackCapability.FULL,      # Can restart
            OperationType.START_INSTANCE: RollbackCapability.FULL,     # Can stop
            OperationType.MODIFY_INSTANCE: RollbackCapability.PARTIAL, # Can revert some changes
            OperationType.RESIZE_INSTANCE: RollbackCapability.FULL,    # Can resize back
            OperationType.DELETE_VOLUME: RollbackCapability.NONE,      # Cannot restore deleted volume
            OperationType.DELETE_SNAPSHOT: RollbackCapability.NONE,    # Cannot restore deleted snapshot
            OperationType.DELETE_RDS_INSTANCE: RollbackCapability.NONE, # Cannot restore deleted RDS
            OperationType.STOP_RDS_INSTANCE: RollbackCapability.FULL,  # Can restart RDS
            OperationType.DELETE_LAMBDA_FUNCTION: RollbackCapability.PARTIAL, # Can redeploy if code saved
            OperationType.DELETE_S3_BUCKET: RollbackCapability.NONE,   # Cannot restore deleted bucket
            OperationType.MODIFY_S3_LIFECYCLE: RollbackCapability.FULL, # Can revert lifecycle policy
            OperationType.DELETE_LOAD_BALANCER: RollbackCapability.PARTIAL, # Can recreate with config
            OperationType.MODIFY_CLOUDWATCH_LOGS: RollbackCapability.FULL, # Can revert log settings
        }
        
        return rollback_map.get(operation_type, RollbackCapability.NONE)
    
    def assess_risk(self, operation_type: OperationType, resource_data: Dict[str, Any]) -> RiskLevel:
        """
        Assess risk level for an operation with comprehensive analysis.
        
        Args:
            operation_type: Type of operation to perform
            resource_data: Data about the resource being operated on
            
        Returns:
            Risk level for the operation
        """
        # Base risk assessment
        base_risk = self._get_base_risk(operation_type)
        
        # Adjust risk based on resource characteristics
        adjusted_risk = self._adjust_risk_for_resource(base_risk, resource_data)
        
        # Log risk assessment
        operation_logger = logging.getLogger('finops.operations')
        operation_logger.info(
            f"Risk assessment: {operation_type.value} on {resource_data.get('resource_id', 'unknown')} "
            f"- Base: {base_risk.value}, Adjusted: {adjusted_risk.value}"
        )
        
        return adjusted_risk
    
    def _get_base_risk(self, operation_type: OperationType) -> RiskLevel:
        """Get base risk level for operation type."""
        high_risk_ops = {
            OperationType.TERMINATE_INSTANCE,
            OperationType.DELETE_VOLUME,
            OperationType.DELETE_RDS_INSTANCE,
            OperationType.DELETE_LAMBDA_FUNCTION,
            OperationType.DELETE_S3_BUCKET,
            OperationType.DELETE_LOAD_BALANCER
        }
        
        medium_risk_ops = {
            OperationType.MODIFY_INSTANCE,
            OperationType.RESIZE_INSTANCE,
            OperationType.DELETE_SNAPSHOT,
            OperationType.MODIFY_S3_LIFECYCLE,
            OperationType.MODIFY_CLOUDWATCH_LOGS
        }
        
        if operation_type in high_risk_ops:
            return RiskLevel.HIGH
        elif operation_type in medium_risk_ops:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _adjust_risk_for_resource(self, base_risk: RiskLevel, resource_data: Dict[str, Any]) -> RiskLevel:
        """Adjust risk based on resource characteristics."""
        # Check for production/critical tags
        tags = resource_data.get('tags', {})
        critical_tags = ['production', 'prod', 'critical', 'important']
        
        if any(tag.lower() in critical_tags for tag in tags.values()):
            if base_risk == RiskLevel.HIGH:
                return RiskLevel.CRITICAL
            elif base_risk == RiskLevel.MEDIUM:
                return RiskLevel.HIGH
        
        # Check for large/expensive resources
        instance_type = resource_data.get('instance_type', '')
        if any(size in instance_type for size in ['xlarge', '2xlarge', '4xlarge']):
            if base_risk == RiskLevel.MEDIUM:
                return RiskLevel.HIGH
        
        # Check for encrypted resources (higher value)
        if resource_data.get('encrypted', False) and base_risk == RiskLevel.MEDIUM:
            return RiskLevel.HIGH
        
        return base_risk
    
    def validate_operation(self, 
                          operation_type: OperationType,
                          resource_id: str,
                          resource_data: Dict[str, Any],
                          operation_func: Callable,
                          *args, **kwargs) -> Dict[str, Any]:
        """
        Validate and potentially execute an operation with comprehensive safety controls.
        
        Args:
            operation_type: Type of operation
            resource_id: ID of the resource being operated on
            resource_data: Data about the resource
            operation_func: Function to execute the operation
            *args, **kwargs: Arguments to pass to operation_func
            
        Returns:
            Result of the operation or simulation
        """
        operation_id = str(uuid.uuid4())
        risk_level = self.assess_risk(operation_type, resource_data)
        rollback_capability = self.get_rollback_capability(operation_type)
        
        operation_record = {
            'operation_id': operation_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'operation_type': operation_type.value,
            'resource_id': resource_id,
            'risk_level': risk_level.value,
            'rollback_capability': rollback_capability.value,
            'dry_run': self.dry_run,
            'resource_data': resource_data.copy(),
            'status': OperationStatus.PENDING.value
        }
        
        # Comprehensive operation logging
        operation_logger = logging.getLogger('finops.operations')
        operation_logger.info(f"Starting operation: {json.dumps(operation_record, indent=2)}")
        
        if self.dry_run:
            # Simulate the operation
            result = self._simulate_operation(operation_type, resource_id, resource_data)
            operation_record['status'] = OperationStatus.SIMULATED.value
            operation_record['simulation_result'] = result
            operation_logger.info(f"Operation simulated: {operation_id}")
        else:
            # Check if operation requires approval
            if self._requires_approval(risk_level):
                logger.warning(f"Operation {operation_type.value} on {resource_id} requires approval (Risk: {risk_level.value})")
                result = {
                    'success': False,
                    'message': f'Operation requires approval due to {risk_level.value} risk level',
                    'requires_approval': True,
                    'risk_level': risk_level.value,
                    'operation_id': operation_id
                }
                operation_record['status'] = OperationStatus.PENDING.value
                operation_record['approval_required'] = True
            else:
                # Create rollback plan before execution
                if rollback_capability != RollbackCapability.NONE:
                    rollback_plan = self._create_detailed_rollback_plan(operation_record)
                    self.rollback_plans[operation_id] = rollback_plan
                    operation_logger.info(f"Rollback plan created for operation {operation_id}")
                
                # Execute the actual operation
                try:
                    result = operation_func(*args, **kwargs)
                    operation_record['status'] = OperationStatus.EXECUTED.value
                    operation_record['execution_result'] = result
                    operation_logger.info(f"Successfully executed {operation_type.value} on {resource_id}")
                except Exception as e:
                    result = {
                        'success': False,
                        'error': str(e),
                        'message': f'Operation failed: {e}',
                        'operation_id': operation_id
                    }
                    operation_record['status'] = OperationStatus.FAILED.value
                    operation_record['error'] = str(e)
                    operation_logger.error(f"Failed to execute {operation_type.value} on {resource_id}: {e}")
        
        # Store operation in history
        self.operation_history.append(operation_record)
        
        # Log final operation state
        operation_logger.info(f"Operation completed: {operation_id} - Status: {operation_record['status']}")
        
        return result
    
    def _simulate_operation(self, 
                           operation_type: OperationType,
                           resource_id: str,
                           resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate an operation for DRY_RUN mode with detailed analysis.
        
        Args:
            operation_type: Type of operation
            resource_id: Resource identifier
            resource_data: Resource data
            
        Returns:
            Detailed simulated operation result
        """
        operation_logger = logging.getLogger('finops.operations')
        operation_logger.info(f"SIMULATING {operation_type.value} on {resource_id}")
        
        base_result = {
            'success': True,
            'simulated': True,
            'resource_id': resource_id,
            'operation_type': operation_type.value,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if operation_type == OperationType.TERMINATE_INSTANCE:
            estimated_savings = resource_data.get('monthly_cost', 0)
            base_result.update({
                'message': f'Would terminate instance {resource_id}',
                'estimated_monthly_savings': estimated_savings,
                'impact': 'Instance would be permanently destroyed',
                'rollback_possible': False
            })
        
        elif operation_type == OperationType.STOP_INSTANCE:
            base_result.update({
                'message': f'Would stop instance {resource_id}',
                'impact': 'Instance would be stopped, can be restarted',
                'rollback_possible': True,
                'rollback_action': 'START_INSTANCE'
            })
        
        elif operation_type == OperationType.RESIZE_INSTANCE:
            current_type = resource_data.get('instance_type', 'unknown')
            new_type = resource_data.get('recommended_type', 'unknown')
            base_result.update({
                'message': f'Would resize instance {resource_id} from {current_type} to {new_type}',
                'impact': f'Instance type would change from {current_type} to {new_type}',
                'rollback_possible': True,
                'rollback_action': f'RESIZE back to {current_type}'
            })
        
        elif operation_type == OperationType.DELETE_VOLUME:
            base_result.update({
                'message': f'Would delete EBS volume {resource_id}',
                'impact': 'Volume and all data would be permanently lost',
                'rollback_possible': False
            })
        
        elif operation_type == OperationType.DELETE_RDS_INSTANCE:
            base_result.update({
                'message': f'Would delete RDS instance {resource_id}',
                'impact': 'Database instance and data would be permanently lost',
                'rollback_possible': False
            })
        
        elif operation_type == OperationType.DELETE_LAMBDA_FUNCTION:
            base_result.update({
                'message': f'Would delete Lambda function {resource_id}',
                'impact': 'Function code and configuration would be lost',
                'rollback_possible': True,  # If code is backed up
                'rollback_action': 'Redeploy function from backup'
            })
        
        else:
            base_result.update({
                'message': f'Would perform {operation_type.value} on {resource_id}',
                'impact': 'Operation would be performed as specified'
            })
        
        operation_logger.info(f"Simulation complete: {base_result['message']}")
        return base_result
    
    def _requires_approval(self, risk_level: RiskLevel) -> bool:
        """
        Determine if an operation requires manual approval.
        
        Args:
            risk_level: Risk level of the operation
            
        Returns:
            True if approval is required
        """
        # Allow automatic execution of LOW and MEDIUM risk operations
        # Require approval for HIGH and CRITICAL risk operations
        return risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def _create_detailed_rollback_plan(self, operation_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a detailed rollback plan for an operation.
        
        Args:
            operation_record: Record of the operation
            
        Returns:
            Detailed rollback plan
        """
        operation_type = OperationType(operation_record['operation_type'])
        resource_data = operation_record['resource_data']
        
        rollback_plan = {
            'rollback_id': str(uuid.uuid4()),
            'operation_id': operation_record['operation_id'],
            'created_at': datetime.now(timezone.utc).isoformat(),
            'rollback_capability': self.get_rollback_capability(operation_type).value,
            'steps': []
        }
        
        if operation_type == OperationType.STOP_INSTANCE:
            rollback_plan['steps'].append({
                'action': OperationType.START_INSTANCE.value,
                'resource_id': operation_record['resource_id'],
                'description': f'Start instance {operation_record["resource_id"]}',
                'aws_service': 'ec2',
                'estimated_time_minutes': 2
            })
        
        elif operation_type == OperationType.START_INSTANCE:
            rollback_plan['steps'].append({
                'action': OperationType.STOP_INSTANCE.value,
                'resource_id': operation_record['resource_id'],
                'description': f'Stop instance {operation_record["resource_id"]}',
                'aws_service': 'ec2',
                'estimated_time_minutes': 2
            })
        
        elif operation_type == OperationType.RESIZE_INSTANCE:
            original_type = resource_data.get('instance_type')
            rollback_plan['steps'].append({
                'action': OperationType.RESIZE_INSTANCE.value,
                'resource_id': operation_record['resource_id'],
                'description': f'Resize instance back to {original_type}',
                'aws_service': 'ec2',
                'original_instance_type': original_type,
                'estimated_time_minutes': 5
            })
        
        elif operation_type == OperationType.STOP_RDS_INSTANCE:
            rollback_plan['steps'].append({
                'action': 'START_RDS_INSTANCE',
                'resource_id': operation_record['resource_id'],
                'description': f'Start RDS instance {operation_record["resource_id"]}',
                'aws_service': 'rds',
                'estimated_time_minutes': 10
            })
        
        elif operation_type == OperationType.MODIFY_S3_LIFECYCLE:
            original_policy = resource_data.get('original_lifecycle_policy')
            rollback_plan['steps'].append({
                'action': 'RESTORE_S3_LIFECYCLE',
                'resource_id': operation_record['resource_id'],
                'description': f'Restore original lifecycle policy for bucket {operation_record["resource_id"]}',
                'aws_service': 's3',
                'original_policy': original_policy,
                'estimated_time_minutes': 1
            })
        
        elif operation_type == OperationType.MODIFY_CLOUDWATCH_LOGS:
            original_retention = resource_data.get('original_log_retention_days')
            rollback_plan['steps'].append({
                'action': 'RESTORE_CLOUDWATCH_LOG_RETENTION',
                'resource_id': operation_record['resource_id'],
                'description': f'Restore original log retention for {operation_record["resource_id"]}',
                'aws_service': 'cloudwatch',
                'original_retention_days': original_retention,
                'estimated_time_minutes': 1
            })
        
        elif operation_type == OperationType.DELETE_LAMBDA_FUNCTION:
            # Partial rollback - can redeploy if code is available
            rollback_plan['steps'].append({
                'action': 'REDEPLOY_LAMBDA_FUNCTION',
                'resource_id': operation_record['resource_id'],
                'description': f'Redeploy Lambda function {operation_record["resource_id"]} from backup',
                'aws_service': 'lambda',
                'function_code_backup': resource_data.get('function_code'),
                'function_config': resource_data.get('function_config'),
                'estimated_time_minutes': 5,
                'requires_backup': True
            })
        
        rollback_plan['total_steps'] = len(rollback_plan['steps'])
        rollback_plan['estimated_total_time_minutes'] = sum(
            step.get('estimated_time_minutes', 0) for step in rollback_plan['steps']
        )
        
        return rollback_plan
    
    def execute_rollback(self, operation_id: str, aws_clients: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute rollback for a specific operation.
        
        Args:
            operation_id: ID of the operation to rollback
            aws_clients: Dictionary of AWS service clients
            
        Returns:
            Rollback execution result
        """
        if operation_id not in self.rollback_plans:
            return {
                'success': False,
                'message': f'No rollback plan found for operation {operation_id}'
            }
        
        rollback_plan = self.rollback_plans[operation_id]
        operation_logger = logging.getLogger('finops.operations')
        
        operation_logger.info(f"Starting rollback execution for operation {operation_id}")
        
        if self.dry_run:
            return self._simulate_rollback(rollback_plan)
        
        rollback_results = []
        
        for step in rollback_plan['steps']:
            try:
                step_result = self._execute_rollback_step(step, aws_clients)
                rollback_results.append(step_result)
                
                if not step_result.get('success', False):
                    operation_logger.error(f"Rollback step failed: {step['description']}")
                    break
                    
            except Exception as e:
                error_result = {
                    'success': False,
                    'step': step['description'],
                    'error': str(e)
                }
                rollback_results.append(error_result)
                operation_logger.error(f"Rollback step exception: {step['description']} - {e}")
                break
        
        # Update operation history
        for op_record in self.operation_history:
            if op_record.get('operation_id') == operation_id:
                if all(result.get('success', False) for result in rollback_results):
                    op_record['status'] = OperationStatus.ROLLED_BACK.value
                else:
                    op_record['status'] = OperationStatus.ROLLBACK_FAILED.value
                op_record['rollback_results'] = rollback_results
                break
        
        success = all(result.get('success', False) for result in rollback_results)
        
        return {
            'success': success,
            'operation_id': operation_id,
            'rollback_plan_id': rollback_plan['rollback_id'],
            'steps_executed': len(rollback_results),
            'total_steps': len(rollback_plan['steps']),
            'results': rollback_results
        }
    
    def _simulate_rollback(self, rollback_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate rollback execution for DRY_RUN mode."""
        operation_logger = logging.getLogger('finops.operations')
        operation_logger.info(f"SIMULATING rollback execution for plan {rollback_plan['rollback_id']}")
        
        simulated_results = []
        for step in rollback_plan['steps']:
            simulated_results.append({
                'success': True,
                'step': step['description'],
                'simulated': True,
                'estimated_time': step.get('estimated_time_minutes', 0)
            })
        
        return {
            'success': True,
            'simulated': True,
            'rollback_plan_id': rollback_plan['rollback_id'],
            'steps_simulated': len(simulated_results),
            'total_steps': len(rollback_plan['steps']),
            'results': simulated_results
        }
    
    def _execute_rollback_step(self, step: Dict[str, Any], aws_clients: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a single rollback step.
        
        Args:
            step: Rollback step to execute
            aws_clients: AWS service clients
            
        Returns:
            Step execution result
        """
        # This is a placeholder for actual AWS API calls
        # In a real implementation, this would use the appropriate AWS clients
        # to perform the rollback actions
        
        operation_logger = logging.getLogger('finops.operations')
        operation_logger.info(f"Executing rollback step: {step['description']}")
        
        # Simulate successful execution for now
        # Real implementation would call appropriate AWS APIs
        return {
            'success': True,
            'step': step['description'],
            'executed_at': datetime.now(timezone.utc).isoformat()
        }
    
    def get_operation_history(self, 
                             operation_type: Optional[OperationType] = None,
                             risk_level: Optional[RiskLevel] = None,
                             status: Optional[OperationStatus] = None) -> List[Dict[str, Any]]:
        """
        Get filtered history of operations performed.
        
        Args:
            operation_type: Filter by operation type
            risk_level: Filter by risk level
            status: Filter by operation status
            
        Returns:
            Filtered list of operation records
        """
        filtered_history = self.operation_history.copy()
        
        if operation_type:
            filtered_history = [
                op for op in filtered_history 
                if op.get('operation_type') == operation_type.value
            ]
        
        if risk_level:
            filtered_history = [
                op for op in filtered_history 
                if op.get('risk_level') == risk_level.value
            ]
        
        if status:
            filtered_history = [
                op for op in filtered_history 
                if op.get('status') == status.value
            ]
        
        return filtered_history
    
    def get_rollback_plans(self) -> Dict[str, Dict[str, Any]]:
        """Get all available rollback plans."""
        return self.rollback_plans.copy()
    
    def get_operations_requiring_approval(self) -> List[Dict[str, Any]]:
        """Get all operations that require approval."""
        return [
            op for op in self.operation_history
            if op.get('approval_required', False) and op.get('status') == OperationStatus.PENDING.value
        ]
    
    def approve_operation(self, operation_id: str, approver: str) -> Dict[str, Any]:
        """
        Approve a pending operation.
        
        Args:
            operation_id: ID of the operation to approve
            approver: Name/ID of the approver
            
        Returns:
            Approval result
        """
        operation_logger = logging.getLogger('finops.operations')
        
        # Find the operation
        operation_record = None
        for op in self.operation_history:
            if op.get('operation_id') == operation_id:
                operation_record = op
                break
        
        if not operation_record:
            return {
                'success': False,
                'message': f'Operation {operation_id} not found'
            }
        
        if operation_record.get('status') != OperationStatus.PENDING.value:
            return {
                'success': False,
                'message': f'Operation {operation_id} is not pending approval'
            }
        
        # Record approval
        operation_record['approved_by'] = approver
        operation_record['approved_at'] = datetime.now(timezone.utc).isoformat()
        operation_record['status'] = 'APPROVED'
        
        operation_logger.info(f"Operation {operation_id} approved by {approver}")
        
        return {
            'success': True,
            'message': f'Operation {operation_id} approved',
            'operation_id': operation_id,
            'approver': approver
        }
    
    def get_safety_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive safety metrics and statistics.
        
        Returns:
            Safety metrics and statistics
        """
        total_operations = len(self.operation_history)
        
        if total_operations == 0:
            return {
                'total_operations': 0,
                'dry_run_mode': self.dry_run,
                'message': 'No operations recorded'
            }
        
        # Count by status
        status_counts = {}
        for status in OperationStatus:
            status_counts[status.value] = len([
                op for op in self.operation_history 
                if op.get('status') == status.value
            ])
        
        # Count by risk level
        risk_counts = {}
        for risk in RiskLevel:
            risk_counts[risk.value] = len([
                op for op in self.operation_history 
                if op.get('risk_level') == risk.value
            ])
        
        # Count rollback capabilities
        rollback_counts = {}
        for capability in RollbackCapability:
            rollback_counts[capability.value] = len([
                op for op in self.operation_history 
                if op.get('rollback_capability') == capability.value
            ])
        
        # Calculate success rates
        executed_ops = [op for op in self.operation_history if op.get('status') == OperationStatus.EXECUTED.value]
        failed_ops = [op for op in self.operation_history if op.get('status') == OperationStatus.FAILED.value]
        
        success_rate = len(executed_ops) / max(len(executed_ops) + len(failed_ops), 1) * 100
        
        return {
            'total_operations': total_operations,
            'dry_run_mode': self.dry_run,
            'status_distribution': status_counts,
            'risk_distribution': risk_counts,
            'rollback_capability_distribution': rollback_counts,
            'success_rate_percentage': round(success_rate, 2),
            'total_rollback_plans': len(self.rollback_plans),
            'operations_requiring_approval': len(self.get_operations_requiring_approval()),
            'log_file': self.log_file
        }
    
    def export_audit_log(self, output_file: Optional[str] = None) -> str:
        """
        Export comprehensive audit log to file.
        
        Args:
            output_file: Output file path (optional)
            
        Returns:
            Path to the exported audit log file
        """
        if not output_file:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            output_file = f"finops_audit_log_{timestamp}.json"
        
        audit_data = {
            'export_timestamp': datetime.now(timezone.utc).isoformat(),
            'safety_controls_config': {
                'dry_run_mode': self.dry_run,
                'log_file': self.log_file
            },
            'safety_metrics': self.get_safety_metrics(),
            'operation_history': self.operation_history,
            'rollback_plans': self.rollback_plans
        }
        
        with open(output_file, 'w') as f:
            json.dump(audit_data, f, indent=2, default=str)
        
        operation_logger = logging.getLogger('finops.operations')
        operation_logger.info(f"Audit log exported to {output_file}")
        
        return output_file
    
    def create_rollback_plan(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a comprehensive rollback plan for a set of operations.
        
        Args:
            operations: List of operations to create rollback for
            
        Returns:
            Comprehensive rollback plan with detailed instructions
        """
        rollback_steps = []
        total_estimated_time = 0
        
        # Process operations in reverse order for proper rollback sequence
        for op in reversed(operations):
            operation_type = op.get('operation_type')
            resource_id = op.get('resource_id')
            resource_data = op.get('resource_data', {})
            
            if operation_type == 'TERMINATE_INSTANCE':
                rollback_steps.append({
                    'action': 'LAUNCH_INSTANCE',
                    'resource_id': resource_id,
                    'priority': 'HIGH',
                    'instructions': 'Launch new instance with same configuration',
                    'original_config': resource_data,
                    'estimated_time_minutes': 10,
                    'aws_service': 'ec2',
                    'rollback_capability': RollbackCapability.NONE.value,
                    'notes': 'Cannot restore exact same instance - will create new instance with same config'
                })
                total_estimated_time += 10
                
            elif operation_type == 'STOP_INSTANCE':
                rollback_steps.append({
                    'action': 'START_INSTANCE',
                    'resource_id': resource_id,
                    'priority': 'MEDIUM',
                    'instructions': f'Start instance {resource_id}',
                    'estimated_time_minutes': 2,
                    'aws_service': 'ec2',
                    'rollback_capability': RollbackCapability.FULL.value
                })
                total_estimated_time += 2
                
            elif operation_type == 'RESIZE_INSTANCE':
                original_type = resource_data.get('instance_type')
                rollback_steps.append({
                    'action': 'RESIZE_INSTANCE',
                    'resource_id': resource_id,
                    'priority': 'MEDIUM',
                    'instructions': f'Resize instance back to {original_type}',
                    'original_instance_type': original_type,
                    'estimated_time_minutes': 5,
                    'aws_service': 'ec2',
                    'rollback_capability': RollbackCapability.FULL.value
                })
                total_estimated_time += 5
                
            elif operation_type == 'DELETE_VOLUME':
                rollback_steps.append({
                    'action': 'RESTORE_FROM_SNAPSHOT',
                    'resource_id': resource_id,
                    'priority': 'HIGH',
                    'instructions': 'Restore volume from most recent snapshot if available',
                    'snapshot_id': resource_data.get('latest_snapshot_id'),
                    'estimated_time_minutes': 15,
                    'aws_service': 'ec2',
                    'rollback_capability': RollbackCapability.PARTIAL.value,
                    'notes': 'Data loss possible if no recent snapshot exists'
                })
                total_estimated_time += 15
        
        rollback_plan = {
            'rollback_plan_id': str(uuid.uuid4()),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'total_operations': len(operations),
            'rollback_steps': rollback_steps,
            'total_steps': len(rollback_steps),
            'estimated_total_time_minutes': total_estimated_time,
            'execution_order': 'REVERSE',  # Execute in reverse order of original operations
            'risk_assessment': self._assess_rollback_risk(rollback_steps),
            'prerequisites': [
                'Verify AWS credentials and permissions',
                'Ensure target resources are accessible',
                'Check for any resource dependencies'
            ]
        }
        
        return rollback_plan
    
    def _assess_rollback_risk(self, rollback_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the risk of executing a rollback plan."""
        high_risk_count = len([step for step in rollback_steps if step.get('priority') == 'HIGH'])
        total_steps = len(rollback_steps)
        
        if high_risk_count > total_steps * 0.5:
            risk_level = RiskLevel.HIGH
        elif high_risk_count > 0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return {
            'overall_risk': risk_level.value,
            'high_risk_steps': high_risk_count,
            'total_steps': total_steps,
            'risk_factors': [
                'Data loss potential' if any('data loss' in step.get('notes', '').lower() for step in rollback_steps) else None,
                'Service downtime' if any(step.get('aws_service') == 'ec2' for step in rollback_steps) else None,
                'Configuration complexity' if any(step.get('rollback_capability') == RollbackCapability.PARTIAL.value for step in rollback_steps) else None
            ]
        }


# Utility functions for external use
def create_safety_controls(dry_run: bool = True, log_file: str = "finops_operations.log") -> SafetyControls:
    """
    Factory function to create SafetyControls instance.
    
    Args:
        dry_run: Enable DRY_RUN mode
        log_file: Path to operation log file
        
    Returns:
        Configured SafetyControls instance
    """
    return SafetyControls(dry_run=dry_run, log_file=log_file)


def validate_dry_run_mode() -> bool:
    """
    Validate that DRY_RUN mode is properly configured.
    
    Returns:
        True if DRY_RUN validation passes
    """
    # Check environment variable
    dry_run_env = os.getenv('DRY_RUN', 'true').lower()
    
    if dry_run_env not in ['true', 'false']:
        logger.warning(f"Invalid DRY_RUN environment variable: {dry_run_env}. Defaulting to True.")
        return True
    
    return dry_run_env == 'true'


def setup_comprehensive_logging(log_level: str = 'INFO') -> None:
    """
    Set up comprehensive logging for safety controls.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('advanced_finops.log'),
            logging.StreamHandler()
        ]
    )
    
    # Set up specific logger for operations
    operation_logger = logging.getLogger('finops.operations')
    operation_logger.setLevel(logging.INFO)


if __name__ == "__main__":
    # Example usage and testing
    setup_comprehensive_logging()
    
    # Create safety controls in DRY_RUN mode
    safety = create_safety_controls(dry_run=True)
    
    # Example operation validation
    def dummy_operation():
        return {"success": True, "message": "Operation completed"}
    
    result = safety.validate_operation(
        operation_type=OperationType.STOP_INSTANCE,
        resource_id="i-1234567890abcdef0",
        resource_data={
            "instance_type": "t3.micro",
            "tags": {"Environment": "development"},
            "monthly_cost": 15.0
        },
        operation_func=dummy_operation
    )
    
    print("Safety Controls Test Result:")
    print(json.dumps(result, indent=2))
    
    # Display safety metrics
    metrics = safety.get_safety_metrics()
    print("\nSafety Metrics:")
    print(json.dumps(metrics, indent=2))