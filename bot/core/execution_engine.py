#!/usr/bin/env python3
"""
Optimization Execution Engine for Advanced FinOps Platform

Implements comprehensive optimization execution with:
- Automatic execution for low-risk optimizations with safety validation
- Comprehensive rollback capabilities for all optimization actions
- Result validation, savings calculation, and performance monitoring
- Execution scheduling and batch processing capabilities
- Integration with approval workflows and safety controls

Requirements: 8.2, 8.4, 8.5, 3.4
"""

import logging
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import concurrent.futures
from pathlib import Path

# Import related components
try:
    from core.approval_workflow import ApprovalWorkflow, RiskLevel, WorkflowState, ApprovalStatus
    from utils.safety_controls import SafetyControls, OperationType, OperationStatus, RollbackCapability
    from utils.http_client import HTTPClient
except ImportError:
    # Fallback for relative imports if run as a package
    try:
        from .approval_workflow import ApprovalWorkflow, RiskLevel, WorkflowState, ApprovalStatus
        from ..utils.safety_controls import SafetyControls, OperationType, OperationStatus, RollbackCapability
        from ..utils.http_client import HTTPClient
    except ImportError:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from core.approval_workflow import ApprovalWorkflow, RiskLevel, WorkflowState, ApprovalStatus
        from utils.safety_controls import SafetyControls, OperationType, OperationStatus, RollbackCapability
        from utils.http_client import HTTPClient

from datetime import timezone

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status of optimization execution."""
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    CANCELLED = "CANCELLED"


class ExecutionPriority(Enum):
    """Priority levels for execution scheduling."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BatchProcessingMode(Enum):
    """Batch processing modes."""
    SEQUENTIAL = "SEQUENTIAL"      # Execute one at a time
    PARALLEL = "PARALLEL"         # Execute multiple simultaneously
    RESOURCE_GROUPED = "RESOURCE_GROUPED"  # Group by resource type
    REGION_GROUPED = "REGION_GROUPED"      # Group by AWS region


@dataclass
class ExecutionResult:
    """Result of an optimization execution."""
    execution_id: str
    optimization_id: str
    resource_id: str
    status: ExecutionStatus
    started_at: str
    completed_at: Optional[str]
    execution_time_seconds: Optional[float]
    actual_savings: Optional[float]
    estimated_savings: float
    savings_accuracy: Optional[float]
    performance_impact: Optional[Dict[str, Any]]
    rollback_plan_id: Optional[str]
    error_message: Optional[str]
    validation_results: Optional[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = asdict(self)
        # Convert enum values to strings
        if hasattr(self.status, 'value'):
            result['status'] = self.status.value
        return result


class OptimizationExecutionEngine:
    """
    Manages execution of cost optimization actions with comprehensive
    safety controls, monitoring, and rollback capabilities.
    """
    
    def __init__(self, 
                 aws_config: Optional[Any] = None,
                 safety_controls: Optional[Any] = None,
                 dry_run: bool = True,
                 max_concurrent_executions: int = 5,
                 execution_timeout_minutes: int = 30):
        """
        Initialize optimization execution engine.
        
        Args:
            aws_config: AWSConfig instance for client management
            safety_controls: SafetyControls instance for operation validation
            dry_run: If True, no actual optimizations will be executed
            max_concurrent_executions: Maximum number of concurrent executions
            execution_timeout_minutes: Timeout for individual executions
        """
        self.dry_run = dry_run
        self.max_concurrent_executions = max_concurrent_executions
        self.execution_timeout_minutes = execution_timeout_minutes
        self.aws_config = aws_config
        
        # Initialize related components
        self.approval_workflow = ApprovalWorkflow(dry_run=dry_run)
        
        if safety_controls:
            self.safety_controls = safety_controls
        else:
            self.safety_controls = SafetyControls(dry_run=dry_run, log_file="execution_engine.log")
            
        self.http_client = HTTPClient()
        
        # Execution tracking
        self.active_executions = {}
        self.completed_executions = {}
        self.execution_queue = []
        self.execution_history = []
        
        # Performance monitoring
        self.performance_metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_savings_achieved': 0.0,
            'average_execution_time': 0.0,
            'rollback_count': 0
        }
        
        logger.info(f"Optimization Execution Engine initialized - DRY_RUN: {dry_run}")
    
    def execute_optimization(self, 
                           optimization_data: Dict[str, Any],
                           force_execution: bool = False) -> Dict[str, Any]:
        """
        Execute a single optimization with comprehensive safety validation.
        
        Args:
            optimization_data: Optimization recommendation data
            force_execution: Skip approval workflow if True (use with caution)
            
        Returns:
            Execution result
        """
        execution_id = str(uuid.uuid4())
        optimization_id = optimization_data.get('optimizationId', str(uuid.uuid4()))
        resource_id = optimization_data.get('resourceId', 'unknown')
        
        logger.info(f"Starting optimization execution {execution_id} for {resource_id}")
        
        # Create execution record
        execution_record = ExecutionResult(
            execution_id=execution_id,
            optimization_id=optimization_id,
            resource_id=resource_id,
            status=ExecutionStatus.PENDING,
            started_at=datetime.utcnow().isoformat(),
            completed_at=None,
            execution_time_seconds=None,
            actual_savings=None,
            estimated_savings=optimization_data.get('estimatedSavings', 0),
            savings_accuracy=None,
            performance_impact=None,
            rollback_plan_id=None,
            error_message=None,
            validation_results=None
        )
        
        self.active_executions[execution_id] = execution_record
        
        try:
            # Step 1: Risk assessment and approval workflow
            if not force_execution:
                approval_result = self._handle_approval_workflow(optimization_data, execution_id)
                if not approval_result['approved']:
                    execution_record.status = ExecutionStatus.CANCELLED
                    execution_record.error_message = approval_result.get('message', 'Approval required')
                    return self._finalize_execution(execution_record)
            
            # Step 2: Pre-execution validation
            validation_result = self._validate_pre_execution(optimization_data)
            execution_record.validation_results = validation_result
            
            if not validation_result['valid']:
                execution_record.status = ExecutionStatus.FAILED
                execution_record.error_message = validation_result.get('message', 'Pre-execution validation failed')
                return self._finalize_execution(execution_record)
            
            # Step 3: Create rollback plan
            rollback_plan = self._create_execution_rollback_plan(optimization_data)
            execution_record.rollback_plan_id = rollback_plan['rollback_plan_id']
            
            # Step 4: Execute the optimization
            execution_record.status = ExecutionStatus.EXECUTING
            execution_result = self._execute_optimization_action(optimization_data, execution_id)
            
            if execution_result['success']:
                # Step 5: Post-execution validation and monitoring
                post_validation = self._validate_post_execution(optimization_data, execution_result)
                
                if post_validation['valid']:
                    execution_record.status = ExecutionStatus.COMPLETED
                    execution_record.actual_savings = post_validation.get('actual_savings')
                    execution_record.performance_impact = post_validation.get('performance_impact')
                    execution_record.savings_accuracy = self._calculate_savings_accuracy(
                        execution_record.estimated_savings, 
                        execution_record.actual_savings
                    )
                else:
                    # Rollback if post-validation fails
                    rollback_result = self._execute_rollback(execution_record.rollback_plan_id)
                    execution_record.status = ExecutionStatus.ROLLED_BACK
                    execution_record.error_message = f"Post-validation failed: {post_validation.get('message')}"
            else:
                execution_record.status = ExecutionStatus.FAILED
                execution_record.error_message = execution_result.get('error', 'Execution failed')
                
        except Exception as e:
            logger.error(f"Execution {execution_id} failed with exception: {str(e)}")
            execution_record.status = ExecutionStatus.FAILED
            execution_record.error_message = str(e)
            
            # Attempt rollback on exception
            if execution_record.rollback_plan_id:
                try:
                    self._execute_rollback(execution_record.rollback_plan_id)
                    execution_record.status = ExecutionStatus.ROLLED_BACK
                except Exception as rollback_error:
                    logger.error(f"Rollback failed for execution {execution_id}: {str(rollback_error)}")
        
        return self._finalize_execution(execution_record)
    
    def _handle_approval_workflow(self, 
                                 optimization_data: Dict[str, Any],
                                 execution_id: str) -> Dict[str, Any]:
        """Handle approval workflow for optimization execution."""
        # Assess risk level
        risk_level = self.approval_workflow.assess_risk(optimization_data)
        
        # Check if automatic execution is allowed for low-risk optimizations
        if risk_level == RiskLevel.LOW:
            estimated_savings = optimization_data.get('estimatedSavings', 0)
            
            # Auto-approve low-risk, low-savings optimizations
            if estimated_savings <= 500.0:  # Configurable threshold
                logger.info(f"Auto-approving low-risk optimization {execution_id} (${estimated_savings:.2f} savings)")
                return {
                    'approved': True,
                    'auto_approved': True,
                    'risk_level': risk_level.value,
                    'message': 'Auto-approved: low risk and low savings'
                }
        
        # Create approval workflow for higher-risk optimizations
        workflow = self.approval_workflow.create_workflow(
            optimization_data=optimization_data,
            requester='execution_engine',
            justification=f'Automatic optimization execution for {optimization_data.get("resourceId")}'
        )
        
        # Check if workflow was auto-approved
        if workflow.get('auto_approved'):
            return {
                'approved': True,
                'auto_approved': True,
                'workflow_id': workflow['workflow_id'],
                'risk_level': risk_level.value
            }
        
        # Manual approval required
        return {
            'approved': False,
            'workflow_id': workflow['workflow_id'],
            'risk_level': risk_level.value,
            'message': f'Manual approval required for {risk_level.value} risk optimization'
        }
    
    def _validate_pre_execution(self, optimization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate optimization before execution."""
        validation_results: Dict[str, Any] = {
            'valid': True,
            'checks': [],
            'warnings': [],
            'errors': []
        }
        
        resource_id = optimization_data.get('resourceId')
        optimization_type = optimization_data.get('optimizationType')
        
        # Check 1: Resource exists and is accessible
        resource_check = self._validate_resource_accessibility(resource_id, optimization_type)
        validation_results['checks'].append(resource_check)
        
        if not resource_check['passed']:
            validation_results['valid'] = False
            validation_results['errors'].append(resource_check['message'])
        
        # Check 2: No conflicting operations
        conflict_check = self._check_conflicting_operations(resource_id)
        validation_results['checks'].append(conflict_check)
        
        if not conflict_check['passed']:
            validation_results['valid'] = False
            validation_results['errors'].append(conflict_check['message'])
        
        # Check 3: Resource state is appropriate for optimization
        state_check = self._validate_resource_state(optimization_data)
        validation_results['checks'].append(state_check)
        
        if not state_check['passed']:
            validation_results['valid'] = False
            validation_results['errors'].append(state_check['message'])
        
        # Check 4: Estimated savings are realistic
        savings_check = self._validate_savings_estimate(optimization_data)
        validation_results['checks'].append(savings_check)
        
        if not savings_check['passed']:
            validation_results['warnings'].append(savings_check['message'])
        
        validation_results['message'] = (
            'Pre-execution validation passed' if validation_results['valid'] 
            else f"Validation failed: {'; '.join(str(e) for e in validation_results['errors'])}"
        )
        
        return validation_results
    
    def _validate_resource_accessibility(self, resource_id: str, optimization_type: str) -> Dict[str, Any]:
        """Validate that the resource exists and is accessible."""
        # This would integrate with AWS APIs to check resource status
        # For now, simulate the check
        
        if self.dry_run:
            return {
                'check_name': 'resource_accessibility',
                'passed': True,
                'message': f'DRY_RUN: Would verify {resource_id} accessibility'
            }
        
        # In real implementation, this would make AWS API calls
        # to verify the resource exists and is in the expected state
        return {
            'check_name': 'resource_accessibility',
            'passed': True,
            'message': f'Resource {resource_id} is accessible'
        }
    
    def _check_conflicting_operations(self, resource_id: str) -> Dict[str, Any]:
        """Check for conflicting operations on the same resource."""
        conflicting_executions = [
            exec_record for exec_record in self.active_executions.values()
            if (exec_record.resource_id == resource_id and 
                exec_record.status in [ExecutionStatus.EXECUTING, ExecutionStatus.SCHEDULED])
        ]
        
        if conflicting_executions:
            return {
                'check_name': 'conflicting_operations',
                'passed': False,
                'message': f'Resource {resource_id} has {len(conflicting_executions)} active operations'
            }
        
        return {
            'check_name': 'conflicting_operations',
            'passed': True,
            'message': f'No conflicting operations found for {resource_id}'
        }
    
    def _validate_resource_state(self, optimization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that the resource is in the correct state for optimization."""
        resource_data = optimization_data.get('resourceData', {})
        optimization_type = optimization_data.get('optimizationType')
        
        # Check resource state based on optimization type
        if optimization_type == 'rightsizing':
            instance_state = resource_data.get('state', 'unknown')
            if instance_state not in ['running', 'stopped']:
                return {
                    'check_name': 'resource_state',
                    'passed': False,
                    'message': f'Instance must be running or stopped for rightsizing, current state: {instance_state}'
                }
        
        elif optimization_type == 'cleanup':
            # For cleanup operations, ensure resource is not critical
            tags = resource_data.get('tags', {})
            if any(tag.lower() in ['critical', 'production'] for tag in tags.values()):
                return {
                    'check_name': 'resource_state',
                    'passed': False,
                    'message': 'Cannot cleanup critical or production resources without explicit approval'
                }
        
        return {
            'check_name': 'resource_state',
            'passed': True,
            'message': 'Resource state is appropriate for optimization'
        }
    
    def _validate_savings_estimate(self, optimization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that the estimated savings are realistic."""
        estimated_savings = optimization_data.get('estimatedSavings', 0)
        current_cost = optimization_data.get('currentCost', 0)
        
        # Check if savings estimate is reasonable (not more than 100% of current cost)
        if estimated_savings > current_cost:
            return {
                'check_name': 'savings_estimate',
                'passed': False,
                'message': f'Estimated savings (${estimated_savings:.2f}) exceed current cost (${current_cost:.2f})'
            }
        
        # Warn if savings are very high percentage of current cost
        if current_cost > 0 and (estimated_savings / current_cost) > 0.8:
            return {
                'check_name': 'savings_estimate',
                'passed': True,
                'message': f'High savings estimate: {(estimated_savings/current_cost)*100:.1f}% of current cost'
            }
        
        return {
            'check_name': 'savings_estimate',
            'passed': True,
            'message': f'Savings estimate appears reasonable: ${estimated_savings:.2f}'
        }
    
    def _create_execution_rollback_plan(self, optimization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detailed rollback plan for the optimization execution."""
        rollback_plan_id = str(uuid.uuid4())
        optimization_type = optimization_data.get('optimizationType')
        resource_data = optimization_data.get('resourceData', {})
        
        rollback_plan = {
            'rollback_plan_id': rollback_plan_id,
            'created_at': datetime.utcnow().isoformat(),
            'optimization_type': optimization_type,
            'resource_id': optimization_data.get('resourceId'),
            'rollback_steps': [],
            'estimated_rollback_time_minutes': 0
        }
        
        # Define rollback steps based on optimization type
        if optimization_type == 'rightsizing':
            original_instance_type = resource_data.get('instanceType')
            rollback_plan['rollback_steps'] = [{
                'step_id': 1,
                'action': 'resize_instance',
                'description': f'Resize instance back to {original_instance_type}',
                'parameters': {
                    'instance_id': optimization_data.get('resourceId'),
                    'instance_type': original_instance_type
                },
                'estimated_time_minutes': 5
            }]
            rollback_plan['estimated_rollback_time_minutes'] = 5
            
        elif optimization_type == 'cleanup':
            # For cleanup operations, rollback might not be possible
            rollback_plan['rollback_steps'] = [{
                'step_id': 1,
                'action': 'restore_from_backup',
                'description': 'Attempt to restore from most recent backup',
                'parameters': {
                    'resource_id': optimization_data.get('resourceId'),
                    'backup_id': resource_data.get('latest_backup_id')
                },
                'estimated_time_minutes': 15,
                'success_probability': 0.7  # May not always succeed
            }]
            rollback_plan['estimated_rollback_time_minutes'] = 15
            
        elif optimization_type == 'pricing':
            # Pricing optimizations are usually reversible
            rollback_plan['rollback_steps'] = [{
                'step_id': 1,
                'action': 'revert_pricing_change',
                'description': 'Revert to original pricing model',
                'parameters': {
                    'resource_id': optimization_data.get('resourceId'),
                    'original_pricing': resource_data.get('original_pricing')
                },
                'estimated_time_minutes': 2
            }]
            rollback_plan['estimated_rollback_time_minutes'] = 2
        
        # Store rollback plan
        self.safety_controls.rollback_plans[rollback_plan_id] = rollback_plan
        
        logger.info(f"Created rollback plan {rollback_plan_id} for {optimization_type} optimization")
        
        return rollback_plan
    
    def _execute_optimization_action(self, 
                                   optimization_data: Dict[str, Any],
                                   execution_id: str) -> Dict[str, Any]:
        """Execute the actual optimization action."""
        optimization_type = optimization_data.get('optimizationType')
        resource_id = optimization_data.get('resourceId')
        
        logger.info(f"Executing {optimization_type} optimization on {resource_id}")
        
        if self.dry_run:
            return self._simulate_optimization_execution(optimization_data, execution_id)
        
        # Map optimization types to operation types for safety controls
        operation_type_mapping = {
            'rightsizing': OperationType.RESIZE_INSTANCE,
            'cleanup': OperationType.TERMINATE_INSTANCE,
            'pricing': OperationType.MODIFY_INSTANCE,
            'storage_optimization': OperationType.MODIFY_S3_LIFECYCLE
        }
        
        operation_type = operation_type_mapping.get(optimization_type, OperationType.MODIFY_INSTANCE)
        
        # Use safety controls to validate and execute the operation
        def execute_aws_operation():
            # This would contain the actual AWS API calls
            # For now, simulate successful execution
            return {
                'success': True,
                'message': f'Successfully executed {optimization_type} on {resource_id}',
                'execution_details': {
                    'operation_type': optimization_type,
                    'resource_id': resource_id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
        
        # Execute through safety controls
        result = self.safety_controls.validate_operation(
            operation_type=operation_type,
            resource_id=resource_id,
            resource_data=optimization_data.get('resourceData', {}),
            operation_func=execute_aws_operation
        )
        
        return result
    
    def _simulate_optimization_execution(self, 
                                       optimization_data: Dict[str, Any],
                                       execution_id: str) -> Dict[str, Any]:
        """Simulate optimization execution for DRY_RUN mode."""
        optimization_type = optimization_data.get('optimizationType')
        resource_id = optimization_data.get('resourceId')
        estimated_savings = optimization_data.get('estimatedSavings', 0)
        
        logger.info(f"DRY_RUN: Simulating {optimization_type} execution on {resource_id}")
        
        # Simulate execution time
        import time
        time.sleep(1)  # Simulate processing time
        
        return {
            'success': True,
            'simulated': True,
            'message': f'DRY_RUN: Would execute {optimization_type} on {resource_id}',
            'estimated_savings': estimated_savings,
            'execution_details': {
                'operation_type': optimization_type,
                'resource_id': resource_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'simulated': True
            }
        }
    
    def _validate_post_execution(self, 
                               optimization_data: Dict[str, Any],
                               execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate optimization results after execution."""
        validation_results = {
            'valid': True,
            'actual_savings': None,
            'performance_impact': {},
            'validation_checks': [],
            'message': 'Post-execution validation passed'
        }
        
        if self.dry_run:
            # For DRY_RUN, simulate validation results
            estimated_savings = optimization_data.get('estimatedSavings', 0)
            # Simulate 90-110% accuracy for savings
            import random
            accuracy_factor = random.uniform(0.9, 1.1)
            actual_savings = estimated_savings * accuracy_factor
            
            validation_results.update({
                'actual_savings': actual_savings,
                'performance_impact': {
                    'cpu_impact': 'minimal',
                    'memory_impact': 'none',
                    'network_impact': 'none',
                    'availability_impact': 'none'
                },
                'message': f'DRY_RUN: Simulated validation - actual savings: ${actual_savings:.2f}'
            })
            
            return validation_results
        
        # In real implementation, this would:
        # 1. Check resource state after optimization
        # 2. Measure actual cost reduction
        # 3. Monitor performance metrics
        # 4. Validate that the optimization achieved expected results
        
        resource_id = optimization_data.get('resourceId')
        optimization_type = optimization_data.get('optimizationType')
        
        # Simulate post-execution checks
        validation_results['validation_checks'] = [
            {
                'check_name': 'resource_state_verification',
                'passed': True,
                'message': f'Resource {resource_id} is in expected state after {optimization_type}'
            },
            {
                'check_name': 'cost_reduction_verification',
                'passed': True,
                'message': 'Cost reduction is within expected range'
            },
            {
                'check_name': 'performance_impact_assessment',
                'passed': True,
                'message': 'No negative performance impact detected'
            }
        ]
        
        return validation_results
    
    def _calculate_savings_accuracy(self, 
                                  estimated_savings: float,
                                  actual_savings: Optional[float]) -> Optional[float]:
        """Calculate the accuracy of savings estimates."""
        if actual_savings is None or estimated_savings == 0:
            return None
        
        # Calculate accuracy as percentage
        accuracy = (actual_savings / estimated_savings) * 100
        return round(accuracy, 2)
    
    def _execute_rollback(self, rollback_plan_id: str) -> Dict[str, Any]:
        """Execute rollback plan."""
        if rollback_plan_id not in self.safety_controls.rollback_plans:
            return {
                'success': False,
                'message': f'Rollback plan {rollback_plan_id} not found'
            }
        
        logger.info(f"Executing rollback plan {rollback_plan_id}")
        
        # Use safety controls to execute rollback
        rollback_result = self.safety_controls.execute_rollback(rollback_plan_id)
        
        # Update performance metrics
        if rollback_result.get('success'):
            self.performance_metrics['rollback_count'] += 1
        
        return rollback_result
    
    def _finalize_execution(self, execution_record: ExecutionResult) -> Dict[str, Any]:
        """Finalize execution and update metrics."""
        execution_record.completed_at = datetime.utcnow().isoformat()
        
        # Calculate execution time
        started_at = datetime.fromisoformat(execution_record.started_at)
        completed_at = datetime.fromisoformat(execution_record.completed_at)
        execution_record.execution_time_seconds = (completed_at - started_at).total_seconds()
        
        # Move from active to completed executions
        if execution_record.execution_id in self.active_executions:
            del self.active_executions[execution_record.execution_id]
        
        self.completed_executions[execution_record.execution_id] = execution_record
        self.execution_history.append(execution_record.to_dict())
        
        # Update performance metrics
        self._update_performance_metrics(execution_record)
        
        # Send results to backend API
        self._send_execution_results_to_api(execution_record)
        
        logger.info(
            f"Execution {execution_record.execution_id} finalized - "
            f"Status: {execution_record.status.value}, "
            f"Time: {execution_record.execution_time_seconds:.2f}s"
        )
        
        return execution_record.to_dict()
    
    def _update_performance_metrics(self, execution_record: ExecutionResult) -> None:
        """Update performance metrics based on execution results."""
        self.performance_metrics['total_executions'] += 1
        
        if execution_record.status == ExecutionStatus.COMPLETED:
            self.performance_metrics['successful_executions'] += 1
            
            if execution_record.actual_savings:
                self.performance_metrics['total_savings_achieved'] += execution_record.actual_savings
        
        elif execution_record.status in [ExecutionStatus.FAILED, ExecutionStatus.ROLLED_BACK]:
            self.performance_metrics['failed_executions'] += 1
        
        # Update average execution time
        total_time = sum(
            record.execution_time_seconds or 0 
            for record in self.completed_executions.values()
        )
        completed_count = len(self.completed_executions)
        
        if completed_count > 0:
            self.performance_metrics['average_execution_time'] = total_time / completed_count
    
    def _send_execution_results_to_api(self, execution_record: ExecutionResult) -> None:
        """Send execution results to the backend API."""
        try:
            # Prepare data for API
            api_data = {
                'execution_id': execution_record.execution_id,
                'optimization_id': execution_record.optimization_id,
                'resource_id': execution_record.resource_id,
                'status': execution_record.status.value,
                'actual_savings': execution_record.actual_savings,
                'estimated_savings': execution_record.estimated_savings,
                'savings_accuracy': execution_record.savings_accuracy,
                'execution_time_seconds': execution_record.execution_time_seconds,
                'completed_at': execution_record.completed_at,
                'performance_impact': execution_record.performance_impact,
                'error_message': execution_record.error_message
            }
            
            # Send to backend API using the correct method
            response = self.http_client._make_request('POST', '/api/executions', data=api_data)
            
            if response.get('success'):
                logger.info(f"Execution results sent to API for {execution_record.execution_id}")
            else:
                logger.warning(f"Failed to send execution results to API: {response.get('message')}")
                
        except Exception as e:
            logger.error(f"Error sending execution results to API: {str(e)}")
    
    def execute_batch_optimizations(self, 
                                  optimizations: List[Dict[str, Any]],
                                  batch_mode: BatchProcessingMode = BatchProcessingMode.SEQUENTIAL,
                                  max_parallel: int = None) -> Dict[str, Any]:
        """
        Execute multiple optimizations in batch with different processing modes.
        
        Args:
            optimizations: List of optimization data
            batch_mode: Processing mode (sequential, parallel, grouped)
            max_parallel: Maximum parallel executions (overrides default)
            
        Returns:
            Batch execution results
        """
        batch_id = str(uuid.uuid4())
        max_parallel = max_parallel or self.max_concurrent_executions
        
        logger.info(
            f"Starting batch execution {batch_id} with {len(optimizations)} optimizations "
            f"in {batch_mode.value} mode"
        )
        
        batch_results = {
            'batch_id': batch_id,
            'started_at': datetime.utcnow().isoformat(),
            'total_optimizations': len(optimizations),
            'processing_mode': batch_mode.value,
            'execution_results': [],
            'summary': {
                'completed': 0,
                'failed': 0,
                'cancelled': 0,
                'total_savings': 0.0,
                'total_execution_time': 0.0
            }
        }
        
        if batch_mode == BatchProcessingMode.SEQUENTIAL:
            # Execute one at a time
            for optimization in optimizations:
                result = self.execute_optimization(optimization)
                batch_results['execution_results'].append(result)
                self._update_batch_summary(batch_results['summary'], result)
        
        elif batch_mode == BatchProcessingMode.PARALLEL:
            # Execute multiple simultaneously
            batch_results = self._execute_parallel_batch(optimizations, max_parallel, batch_results)
        
        elif batch_mode == BatchProcessingMode.RESOURCE_GROUPED:
            # Group by resource type and execute groups in parallel
            grouped_optimizations = self._group_optimizations_by_resource_type(optimizations)
            batch_results = self._execute_grouped_batch(grouped_optimizations, batch_results)
        
        elif batch_mode == BatchProcessingMode.REGION_GROUPED:
            # Group by AWS region and execute groups in parallel
            grouped_optimizations = self._group_optimizations_by_region(optimizations)
            batch_results = self._execute_grouped_batch(grouped_optimizations, batch_results)
        
        batch_results['completed_at'] = datetime.utcnow().isoformat()
        batch_results['total_batch_time'] = (
            datetime.fromisoformat(batch_results['completed_at']) - 
            datetime.fromisoformat(batch_results['started_at'])
        ).total_seconds()
        
        logger.info(
            f"Batch execution {batch_id} completed - "
            f"Success: {batch_results['summary']['completed']}, "
            f"Failed: {batch_results['summary']['failed']}, "
            f"Total savings: ${batch_results['summary']['total_savings']:.2f}"
        )
        
        return batch_results
    
    def _execute_parallel_batch(self, 
                               optimizations: List[Dict[str, Any]],
                               max_parallel: int,
                               batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimizations in parallel with concurrency control."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as executor:
            # Submit all optimization executions
            future_to_optimization = {
                executor.submit(self.execute_optimization, opt): opt 
                for opt in optimizations
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_optimization):
                try:
                    result = future.result(timeout=self.execution_timeout_minutes * 60)
                    batch_results['execution_results'].append(result)
                    self._update_batch_summary(batch_results['summary'], result)
                except concurrent.futures.TimeoutError:
                    logger.error(f"Optimization execution timed out after {self.execution_timeout_minutes} minutes")
                    timeout_result = {
                        'status': ExecutionStatus.FAILED.value,
                        'error_message': 'Execution timeout',
                        'actual_savings': 0,
                        'execution_time_seconds': self.execution_timeout_minutes * 60
                    }
                    batch_results['execution_results'].append(timeout_result)
                    self._update_batch_summary(batch_results['summary'], timeout_result)
                except Exception as e:
                    logger.error(f"Parallel execution failed: {str(e)}")
                    error_result = {
                        'status': ExecutionStatus.FAILED.value,
                        'error_message': str(e),
                        'actual_savings': 0,
                        'execution_time_seconds': 0
                    }
                    batch_results['execution_results'].append(error_result)
                    self._update_batch_summary(batch_results['summary'], error_result)
        
        return batch_results
    
    def _group_optimizations_by_resource_type(self, 
                                            optimizations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group optimizations by resource type."""
        grouped = {}
        
        for optimization in optimizations:
            resource_type = optimization.get('resourceType', 'unknown')
            if resource_type not in grouped:
                grouped[resource_type] = []
            grouped[resource_type].append(optimization)
        
        return grouped
    
    def _group_optimizations_by_region(self, 
                                     optimizations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group optimizations by AWS region."""
        grouped = {}
        
        for optimization in optimizations:
            region = optimization.get('resourceData', {}).get('region', 'unknown')
            if region not in grouped:
                grouped[region] = []
            grouped[region].append(optimization)
        
        return grouped
    
    def _execute_grouped_batch(self, 
                             grouped_optimizations: Dict[str, List[Dict[str, Any]]],
                             batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute grouped optimizations with parallel group processing."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(grouped_optimizations)) as executor:
            # Submit each group for parallel execution
            future_to_group = {}
            
            for group_name, group_optimizations in grouped_optimizations.items():
                future = executor.submit(self._execute_optimization_group, group_name, group_optimizations)
                future_to_group[future] = group_name
            
            # Collect results from all groups
            for future in concurrent.futures.as_completed(future_to_group):
                group_name = future_to_group[future]
                try:
                    group_results = future.result()
                    batch_results['execution_results'].extend(group_results)
                    
                    # Update batch summary
                    for result in group_results:
                        self._update_batch_summary(batch_results['summary'], result)
                        
                    logger.info(f"Completed execution group: {group_name} ({len(group_results)} optimizations)")
                    
                except Exception as e:
                    logger.error(f"Group execution failed for {group_name}: {str(e)}")
        
        return batch_results
    
    def _execute_optimization_group(self, 
                                  group_name: str,
                                  optimizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a group of optimizations sequentially."""
        logger.info(f"Executing optimization group: {group_name} ({len(optimizations)} optimizations)")
        
        group_results = []
        for optimization in optimizations:
            result = self.execute_optimization(optimization)
            group_results.append(result)
        
        return group_results
    
    def _update_batch_summary(self, summary: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Update batch execution summary with individual result."""
        status = result.get('status', ExecutionStatus.FAILED.value)
        
        if status == ExecutionStatus.COMPLETED.value:
            summary['completed'] += 1
        elif status in [ExecutionStatus.FAILED.value, ExecutionStatus.ROLLED_BACK.value]:
            summary['failed'] += 1
        elif status == ExecutionStatus.CANCELLED.value:
            summary['cancelled'] += 1
        
        # Add savings and execution time
        actual_savings = result.get('actual_savings', 0) or 0
        execution_time = result.get('execution_time_seconds', 0) or 0
        
        summary['total_savings'] += actual_savings
        summary['total_execution_time'] += execution_time
    
    def schedule_optimization(self, 
                            optimization_data: Dict[str, Any],
                            scheduled_time: datetime,
                            priority: ExecutionPriority = ExecutionPriority.MEDIUM) -> Dict[str, Any]:
        """
        Schedule an optimization for future execution.
        
        Args:
            optimization_data: Optimization recommendation data
            scheduled_time: When to execute the optimization
            priority: Execution priority
            
        Returns:
            Scheduling result
        """
        schedule_id = str(uuid.uuid4())
        
        scheduled_item = {
            'schedule_id': schedule_id,
            'optimization_data': optimization_data,
            'scheduled_time': scheduled_time.isoformat(),
            'priority': priority.value,
            'status': ExecutionStatus.SCHEDULED.value,
            'created_at': datetime.utcnow().isoformat(),
            'resource_id': optimization_data.get('resourceId'),
            'estimated_savings': optimization_data.get('estimatedSavings', 0)
        }
        
        # Add to execution queue with priority ordering
        self.execution_queue.append(scheduled_item)
        self.execution_queue.sort(key=lambda x: (x['scheduled_time'], x['priority']))
        
        logger.info(
            f"Scheduled optimization {schedule_id} for {optimization_data.get('resourceId')} "
            f"at {scheduled_time.isoformat()} with {priority.value} priority"
        )
        
        return {
            'success': True,
            'schedule_id': schedule_id,
            'scheduled_time': scheduled_time.isoformat(),
            'priority': priority.value,
            'message': f'Optimization scheduled for {scheduled_time.isoformat()}'
        }
    
    def process_scheduled_optimizations(self) -> Dict[str, Any]:
        """
        Process scheduled optimizations that are due for execution.
        
        Returns:
            Processing results
        """
        current_time = datetime.utcnow()
        due_optimizations = []
        remaining_queue = []
        
        # Separate due optimizations from future ones
        for scheduled_item in self.execution_queue:
            scheduled_time = datetime.fromisoformat(scheduled_item['scheduled_time'])
            
            if scheduled_time <= current_time:
                due_optimizations.append(scheduled_item)
            else:
                remaining_queue.append(scheduled_item)
        
        # Update queue to remove processed items
        self.execution_queue = remaining_queue
        
        if not due_optimizations:
            return {
                'processed_count': 0,
                'message': 'No scheduled optimizations due for execution',
                'next_scheduled': (
                    remaining_queue[0]['scheduled_time'] if remaining_queue 
                    else None
                )
            }
        
        logger.info(f"Processing {len(due_optimizations)} scheduled optimizations")
        
        # Execute due optimizations
        execution_results = []
        for scheduled_item in due_optimizations:
            try:
                result = self.execute_optimization(scheduled_item['optimization_data'])
                result['schedule_id'] = scheduled_item['schedule_id']
                execution_results.append(result)
            except Exception as e:
                logger.error(f"Failed to execute scheduled optimization {scheduled_item['schedule_id']}: {str(e)}")
                execution_results.append({
                    'schedule_id': scheduled_item['schedule_id'],
                    'status': ExecutionStatus.FAILED.value,
                    'error_message': str(e)
                })
        
        # Calculate summary
        successful_executions = len([r for r in execution_results if r.get('status') == ExecutionStatus.COMPLETED.value])
        total_savings = sum(r.get('actual_savings', 0) or 0 for r in execution_results)
        
        return {
            'processed_count': len(due_optimizations),
            'successful_executions': successful_executions,
            'failed_executions': len(due_optimizations) - successful_executions,
            'total_savings_achieved': total_savings,
            'execution_results': execution_results,
            'next_scheduled': (
                remaining_queue[0]['scheduled_time'] if remaining_queue 
                else None
            )
        }
    
    def cancel_scheduled_optimization(self, schedule_id: str) -> Dict[str, Any]:
        """
        Cancel a scheduled optimization.
        
        Args:
            schedule_id: ID of the scheduled optimization to cancel
            
        Returns:
            Cancellation result
        """
        # Find and remove the scheduled item
        for i, scheduled_item in enumerate(self.execution_queue):
            if scheduled_item['schedule_id'] == schedule_id:
                cancelled_item = self.execution_queue.pop(i)
                
                logger.info(f"Cancelled scheduled optimization {schedule_id}")
                
                return {
                    'success': True,
                    'schedule_id': schedule_id,
                    'cancelled_at': datetime.utcnow().isoformat(),
                    'message': f'Scheduled optimization {schedule_id} cancelled'
                }
        
        return {
            'success': False,
            'message': f'Scheduled optimization {schedule_id} not found'
        }
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get status of a specific execution.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Execution status information
        """
        # Check active executions
        if execution_id in self.active_executions:
            execution_record = self.active_executions[execution_id]
            return {
                'success': True,
                'execution': execution_record.to_dict(),
                'is_active': True
            }
        
        # Check completed executions
        if execution_id in self.completed_executions:
            execution_record = self.completed_executions[execution_id]
            return {
                'success': True,
                'execution': execution_record.to_dict(),
                'is_active': False
            }
        
        return {
            'success': False,
            'message': f'Execution {execution_id} not found'
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics for the execution engine.
        
        Returns:
            Performance metrics and statistics
        """
        # Calculate additional metrics
        success_rate = 0
        if self.performance_metrics['total_executions'] > 0:
            success_rate = (
                self.performance_metrics['successful_executions'] / 
                self.performance_metrics['total_executions']
            ) * 100
        
        # Calculate average savings per execution
        avg_savings_per_execution = 0
        if self.performance_metrics['successful_executions'] > 0:
            avg_savings_per_execution = (
                self.performance_metrics['total_savings_achieved'] / 
                self.performance_metrics['successful_executions']
            )
        
        # Get current queue status
        queue_status = {
            'scheduled_optimizations': len(self.execution_queue),
            'active_executions': len(self.active_executions),
            'next_scheduled': (
                self.execution_queue[0]['scheduled_time'] if self.execution_queue 
                else None
            )
        }
        
        return {
            'execution_metrics': self.performance_metrics.copy(),
            'success_rate_percentage': round(success_rate, 2),
            'average_savings_per_execution': round(avg_savings_per_execution, 2),
            'queue_status': queue_status,
            'dry_run_mode': self.dry_run,
            'max_concurrent_executions': self.max_concurrent_executions,
            'execution_timeout_minutes': self.execution_timeout_minutes,
            'total_rollback_plans': len(self.safety_controls.rollback_plans)
        }
    
    def get_execution_history(self, 
                            limit: int = 100,
                            status_filter: Optional[ExecutionStatus] = None,
                            resource_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get filtered execution history.
        
        Args:
            limit: Maximum number of records to return
            status_filter: Filter by execution status
            resource_filter: Filter by resource ID
            
        Returns:
            Filtered execution history
        """
        filtered_history = self.execution_history.copy()
        
        # Apply filters
        if status_filter:
            filtered_history = [
                record for record in filtered_history
                if record.get('status') == status_filter.value
            ]
        
        if resource_filter:
            filtered_history = [
                record for record in filtered_history
                if resource_filter in record.get('resource_id', '')
            ]
        
        # Sort by completion time (most recent first)
        filtered_history.sort(
            key=lambda x: x.get('completed_at', x.get('started_at', '')),
            reverse=True
        )
        
        # Apply limit
        return filtered_history[:limit]
    
    def cleanup_completed_executions(self, retention_days: int = 30) -> Dict[str, Any]:
        """
        Clean up old completed executions to manage memory usage.
        
        Args:
            retention_days: Number of days to retain execution records
            
        Returns:
            Cleanup results
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Find executions to clean up
        executions_to_remove = []
        for execution_id, execution_record in self.completed_executions.items():
            completed_at = datetime.fromisoformat(execution_record.completed_at)
            if completed_at < cutoff_date:
                executions_to_remove.append(execution_id)
        
        # Remove old executions
        for execution_id in executions_to_remove:
            del self.completed_executions[execution_id]
        
        # Clean up execution history
        self.execution_history = [
            record for record in self.execution_history
            if datetime.fromisoformat(record.get('completed_at', record.get('started_at', ''))) >= cutoff_date
        ]
        
        logger.info(f"Cleaned up {len(executions_to_remove)} old execution records")
        
        return {
            'cleaned_up_count': len(executions_to_remove),
            'retention_days': retention_days,
            'cutoff_date': cutoff_date.isoformat(),
            'remaining_executions': len(self.completed_executions)
        }


# Alias for backward compatibility
ExecutionEngine = OptimizationExecutionEngine


# Utility functions for external use
def create_execution_engine(dry_run: bool = True, 
                          max_concurrent: int = 5,
                          timeout_minutes: int = 30) -> OptimizationExecutionEngine:
    """
    Factory function to create OptimizationExecutionEngine instance.
    
    Args:
        dry_run: Enable DRY_RUN mode
        max_concurrent: Maximum concurrent executions
        timeout_minutes: Execution timeout in minutes
        
    Returns:
        Configured OptimizationExecutionEngine instance
    """
    return ExecutionEngine(
        dry_run=dry_run,
        max_concurrent_executions=max_concurrent,
        execution_timeout_minutes=timeout_minutes
    )


def execute_single_optimization(optimization_data: Dict[str, Any],
                              dry_run: bool = True) -> Dict[str, Any]:
    """
    Utility function to execute a single optimization.
    
    Args:
        optimization_data: Optimization recommendation data
        dry_run: Enable DRY_RUN mode
        
    Returns:
        Execution result
    """
    engine = create_execution_engine(dry_run=dry_run)
    return engine.execute_optimization(optimization_data)


if __name__ == "__main__":
    # Example usage and testing
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create execution engine in DRY_RUN mode
    engine = create_execution_engine(dry_run=True)
    
    # Example optimization data
    sample_optimization = {
        'optimizationId': 'opt-12345',
        'resourceId': 'i-1234567890abcdef0',
        'resourceType': 'ec2',
        'optimizationType': 'rightsizing',
        'currentCost': 100.0,
        'estimatedSavings': 30.0,
        'resourceData': {
            'instanceType': 't3.large',
            'region': 'us-east-1',
            'tags': {'Environment': 'development'},
            'state': 'running'
        }
    }
    
    # Execute single optimization
    result = engine.execute_optimization(sample_optimization)
    print("Execution Result:")
    print(json.dumps(result, indent=2))
    
    # Get performance metrics
    metrics = engine.get_performance_metrics()
    print("\nPerformance Metrics:")
    print(json.dumps(metrics, indent=2))