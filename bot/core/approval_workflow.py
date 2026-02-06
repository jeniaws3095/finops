#!/usr/bin/env python3
"""
Approval Workflow System for Advanced FinOps Platform

Implements risk-based approval workflows for cost optimization actions:
- Risk categorization logic (LOW, MEDIUM, HIGH, CRITICAL)
- Approval requirement determination based on risk levels
- Workflow state management and tracking
- Integration with safety controls and optimization engines

Requirements: 8.1, 8.3
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for optimization actions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalStatus(Enum):
    """Status of approval workflow."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class WorkflowState(Enum):
    """State of the approval workflow."""
    CREATED = "CREATED"
    UNDER_REVIEW = "UNDER_REVIEW"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class ApprovalAuthority(Enum):
    """Authority levels for approvals."""
    SYSTEM = "SYSTEM"           # Automatic approval for low-risk items
    ENGINEER = "ENGINEER"       # Engineering team approval
    MANAGER = "MANAGER"         # Management approval required
    DIRECTOR = "DIRECTOR"       # Director-level approval required
    EXECUTIVE = "EXECUTIVE"     # Executive approval required


@dataclass
class ApprovalCriteria:
    """Criteria for determining approval requirements."""
    risk_level: RiskLevel
    estimated_savings: float
    resource_type: str
    operation_type: str
    resource_criticality: str
    business_impact: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = asdict(self)
        # Convert enum values to strings
        if hasattr(self.risk_level, 'value'):
            result['risk_level'] = self.risk_level.value
        return result


@dataclass
class ApprovalRequirement:
    """Requirements for approval based on criteria."""
    authority_required: ApprovalAuthority
    approval_timeout_hours: int
    requires_justification: bool
    requires_rollback_plan: bool
    requires_stakeholder_notification: bool
    auto_approval_eligible: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = asdict(self)
        # Convert enum values to strings
        if hasattr(self.authority_required, 'value'):
            result['authority_required'] = self.authority_required.value
        return result


@dataclass
class WorkflowStep:
    """Individual step in the approval workflow."""
    step_id: str
    step_name: str
    required_authority: ApprovalAuthority
    status: ApprovalStatus
    assigned_to: Optional[str]
    completed_by: Optional[str]
    completed_at: Optional[str]
    comments: Optional[str]
    timeout_at: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = asdict(self)
        # Convert enum values to strings
        if hasattr(self.required_authority, 'value'):
            result['required_authority'] = self.required_authority.value
        if hasattr(self.status, 'value'):
            result['status'] = self.status.value
        return result


class ApprovalWorkflow:
    """
    Manages approval workflows for cost optimization actions.
    
    Provides risk-based approval routing, workflow state management,
    and integration with safety controls and optimization engines.
    """
    
    def __init__(self, dry_run: bool = True):
        """
        Initialize approval workflow system.
        
        Args:
            dry_run: If True, no actual approvals will be processed
        """
        self.dry_run = dry_run
        self.active_workflows = {}
        self.completed_workflows = {}
        self.approval_rules = self._initialize_approval_rules()
        self.risk_assessment_rules = self._initialize_risk_assessment_rules()
        
        logger.info(f"Approval Workflow System initialized - DRY_RUN: {dry_run}")
    
    def _initialize_approval_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize approval rules based on risk levels and criteria.
        
        Returns:
            Dictionary of approval rules by risk level and criteria
        """
        return {
            'risk_based_rules': {
                RiskLevel.LOW.value: {
                    'authority_required': ApprovalAuthority.SYSTEM.value,
                    'approval_timeout_hours': 1,
                    'auto_approval_eligible': True,
                    'requires_justification': False,
                    'requires_rollback_plan': False,
                    'requires_stakeholder_notification': False,
                    'max_savings_threshold': 500.0  # Auto-approve up to $500 savings
                },
                RiskLevel.MEDIUM.value: {
                    'authority_required': ApprovalAuthority.ENGINEER.value,
                    'approval_timeout_hours': 24,
                    'auto_approval_eligible': False,
                    'requires_justification': True,
                    'requires_rollback_plan': True,
                    'requires_stakeholder_notification': False,
                    'max_savings_threshold': 2000.0  # Engineer approval up to $2000
                },
                RiskLevel.HIGH.value: {
                    'authority_required': ApprovalAuthority.MANAGER.value,
                    'approval_timeout_hours': 48,
                    'auto_approval_eligible': False,
                    'requires_justification': True,
                    'requires_rollback_plan': True,
                    'requires_stakeholder_notification': True,
                    'max_savings_threshold': 10000.0  # Manager approval up to $10000
                },
                RiskLevel.CRITICAL.value: {
                    'authority_required': ApprovalAuthority.DIRECTOR.value,
                    'approval_timeout_hours': 72,
                    'auto_approval_eligible': False,
                    'requires_justification': True,
                    'requires_rollback_plan': True,
                    'requires_stakeholder_notification': True,
                    'max_savings_threshold': float('inf')  # No limit for director approval
                }
            },
            'savings_escalation_rules': {
                'thresholds': [
                    {'amount': 5000.0, 'authority': ApprovalAuthority.MANAGER.value},
                    {'amount': 25000.0, 'authority': ApprovalAuthority.DIRECTOR.value},
                    {'amount': 100000.0, 'authority': ApprovalAuthority.EXECUTIVE.value}
                ]
            },
            'resource_type_rules': {
                'production_resources': {
                    'minimum_authority': ApprovalAuthority.MANAGER.value,
                    'additional_timeout_hours': 24
                },
                'critical_resources': {
                    'minimum_authority': ApprovalAuthority.DIRECTOR.value,
                    'additional_timeout_hours': 48
                }
            }
        }
    
    def _initialize_risk_assessment_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize risk assessment rules for categorizing optimization actions.
        
        Returns:
            Dictionary of risk assessment rules
        """
        return {
            'operation_risk_mapping': {
                'cleanup': {
                    'base_risk': RiskLevel.HIGH.value,  # Deletion operations are inherently risky
                    'risk_factors': ['data_loss', 'service_interruption']
                },
                'rightsizing': {
                    'base_risk': RiskLevel.MEDIUM.value,
                    'risk_factors': ['performance_impact', 'service_interruption']
                },
                'pricing': {
                    'base_risk': RiskLevel.LOW.value,
                    'risk_factors': ['cost_impact']
                },
                'storage_optimization': {
                    'base_risk': RiskLevel.MEDIUM.value,
                    'risk_factors': ['data_access_delay', 'cost_impact']
                },
                'configuration': {
                    'base_risk': RiskLevel.MEDIUM.value,
                    'risk_factors': ['service_behavior_change']
                }
            },
            'resource_criticality_factors': {
                'production_tags': ['prod', 'production', 'live'],
                'critical_tags': ['critical', 'important', 'essential'],
                'high_cost_threshold': 1000.0,  # Monthly cost threshold for high-value resources
                'large_instance_types': ['xlarge', '2xlarge', '4xlarge', '8xlarge']
            },
            'risk_escalation_factors': {
                'production_environment': 1,  # Increase risk by 1 level
                'critical_resource': 2,       # Increase risk by 2 levels
                'high_cost_resource': 1,      # Increase risk by 1 level
                'large_instance': 1           # Increase risk by 1 level
            }
        }
    
    def assess_risk(self, optimization_data: Dict[str, Any]) -> RiskLevel:
        """
        Assess risk level for an optimization action using comprehensive analysis.
        
        Args:
            optimization_data: Optimization recommendation data
            
        Returns:
            Assessed risk level
        """
        # Get base risk from operation type
        operation_type = optimization_data.get('optimizationType', 'unknown')
        base_risk_str = self.risk_assessment_rules['operation_risk_mapping'].get(
            operation_type, {}
        ).get('base_risk', RiskLevel.MEDIUM.value)
        
        base_risk = RiskLevel(base_risk_str)
        
        # Calculate risk escalation factors
        escalation_level = 0
        resource_data = optimization_data.get('resourceData', {})
        
        # Check for production environment
        tags = resource_data.get('tags', {})
        production_tags = self.risk_assessment_rules['resource_criticality_factors']['production_tags']
        if any(tag.lower() in production_tags for tag in tags.values()):
            escalation_level += self.risk_assessment_rules['risk_escalation_factors']['production_environment']
        
        # Check for critical resource tags
        critical_tags = self.risk_assessment_rules['resource_criticality_factors']['critical_tags']
        if any(tag.lower() in critical_tags for tag in tags.values()):
            escalation_level += self.risk_assessment_rules['risk_escalation_factors']['critical_resource']
        
        # Check for high-cost resources
        current_cost = optimization_data.get('currentCost', 0)
        high_cost_threshold = self.risk_assessment_rules['resource_criticality_factors']['high_cost_threshold']
        if current_cost > high_cost_threshold:
            escalation_level += self.risk_assessment_rules['risk_escalation_factors']['high_cost_resource']
        
        # Check for large instance types
        instance_type = resource_data.get('instanceType', '')
        large_types = self.risk_assessment_rules['resource_criticality_factors']['large_instance_types']
        if any(size in instance_type for size in large_types):
            escalation_level += self.risk_assessment_rules['risk_escalation_factors']['large_instance']
        
        # Apply risk escalation
        risk_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        current_index = risk_levels.index(base_risk)
        escalated_index = min(current_index + escalation_level, len(risk_levels) - 1)
        
        final_risk = risk_levels[escalated_index]
        
        logger.info(
            f"Risk assessment for {optimization_data.get('resourceId', 'unknown')}: "
            f"Base: {base_risk.value}, Escalation: +{escalation_level}, Final: {final_risk.value}"
        )
        
        return final_risk
    
    def determine_approval_requirements(self, 
                                      risk_level: RiskLevel,
                                      optimization_data: Dict[str, Any]) -> ApprovalRequirement:
        """
        Determine approval requirements based on risk level and optimization data.
        
        Args:
            risk_level: Assessed risk level
            optimization_data: Optimization recommendation data
            
        Returns:
            Approval requirements
        """
        base_rules = self.approval_rules['risk_based_rules'][risk_level.value]
        estimated_savings = optimization_data.get('estimatedSavings', 0)
        
        # Check for savings-based escalation
        authority_required = ApprovalAuthority(base_rules['authority_required'])
        for threshold in self.approval_rules['savings_escalation_rules']['thresholds']:
            if estimated_savings >= threshold['amount']:
                escalated_authority = ApprovalAuthority(threshold['authority'])
                if escalated_authority.value > authority_required.value:
                    authority_required = escalated_authority
        
        # Check for resource-type-based escalation
        resource_data = optimization_data.get('resourceData', {})
        tags = resource_data.get('tags', {})
        
        # Production resource check
        production_tags = self.risk_assessment_rules['resource_criticality_factors']['production_tags']
        if any(tag.lower() in production_tags for tag in tags.values()):
            prod_rules = self.approval_rules['resource_type_rules']['production_resources']
            min_authority = ApprovalAuthority(prod_rules['minimum_authority'])
            if min_authority.value > authority_required.value:
                authority_required = min_authority
        
        # Critical resource check
        critical_tags = self.risk_assessment_rules['resource_criticality_factors']['critical_tags']
        if any(tag.lower() in critical_tags for tag in tags.values()):
            crit_rules = self.approval_rules['resource_type_rules']['critical_resources']
            min_authority = ApprovalAuthority(crit_rules['minimum_authority'])
            if min_authority.value > authority_required.value:
                authority_required = min_authority
        
        # Calculate timeout with escalations
        timeout_hours = base_rules['approval_timeout_hours']
        if any(tag.lower() in production_tags for tag in tags.values()):
            timeout_hours += self.approval_rules['resource_type_rules']['production_resources']['additional_timeout_hours']
        if any(tag.lower() in critical_tags for tag in tags.values()):
            timeout_hours += self.approval_rules['resource_type_rules']['critical_resources']['additional_timeout_hours']
        
        return ApprovalRequirement(
            authority_required=authority_required,
            approval_timeout_hours=timeout_hours,
            requires_justification=base_rules['requires_justification'],
            requires_rollback_plan=base_rules['requires_rollback_plan'],
            requires_stakeholder_notification=base_rules['requires_stakeholder_notification'],
            auto_approval_eligible=(
                base_rules['auto_approval_eligible'] and 
                estimated_savings <= base_rules['max_savings_threshold']
            )
        )
    
    def create_workflow(self, 
                       optimization_data: Dict[str, Any],
                       requester: str,
                       justification: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new approval workflow for an optimization action.
        
        Args:
            optimization_data: Optimization recommendation data
            requester: User requesting the optimization
            justification: Justification for the optimization
            
        Returns:
            Created workflow information
        """
        workflow_id = str(uuid.uuid4())
        
        # Assess risk and determine requirements
        risk_level = self.assess_risk(optimization_data)
        approval_requirements = self.determine_approval_requirements(risk_level, optimization_data)
        
        # Create approval criteria
        criteria = ApprovalCriteria(
            risk_level=risk_level,
            estimated_savings=optimization_data.get('estimatedSavings', 0),
            resource_type=optimization_data.get('resourceType', 'unknown'),
            operation_type=optimization_data.get('optimizationType', 'unknown'),
            resource_criticality=self._assess_resource_criticality(optimization_data),
            business_impact=self._assess_business_impact(optimization_data)
        )
        
        # Create workflow steps
        workflow_steps = self._create_workflow_steps(approval_requirements, workflow_id)
        
        # Calculate timeout
        timeout_at = datetime.utcnow() + timedelta(hours=approval_requirements.approval_timeout_hours)
        
        workflow = {
            'workflow_id': workflow_id,
            'created_at': datetime.utcnow().isoformat(),
            'requester': requester,
            'optimization_id': optimization_data.get('optimizationId'),
            'resource_id': optimization_data.get('resourceId'),
            'state': WorkflowState.CREATED.value,
            'risk_level': risk_level.value,
            'approval_criteria': criteria.to_dict(),
            'approval_requirements': approval_requirements.to_dict(),
            'workflow_steps': [step.to_dict() for step in workflow_steps],
            'justification': justification,
            'timeout_at': timeout_at.isoformat(),
            'optimization_data': optimization_data,
            'dry_run': self.dry_run
        }
        
        # Store workflow
        self.active_workflows[workflow_id] = workflow
        
        # Send stakeholder notifications if required
        if approval_requirements.requires_stakeholder_notification:
            notification_result = self.send_stakeholder_notification(
                workflow_id=workflow_id,
                notification_type='created'
            )
            workflow['initial_notification_sent'] = notification_result.get('success', False)
        
        # Handle auto-approval if eligible
        if approval_requirements.auto_approval_eligible and not self.dry_run:
            auto_approval_result = self._process_auto_approval(workflow_id)
            workflow.update(auto_approval_result)
            
            # Send approval notification for auto-approved workflows
            if auto_approval_result.get('auto_approved'):
                self.send_stakeholder_notification(
                    workflow_id=workflow_id,
                    notification_type='approved'
                )
        
        logger.info(
            f"Created approval workflow {workflow_id} for {optimization_data.get('resourceId', 'unknown')} "
            f"- Risk: {risk_level.value}, Authority: {approval_requirements.authority_required.value}"
        )
        
        return workflow
    
    def _assess_resource_criticality(self, optimization_data: Dict[str, Any]) -> str:
        """Assess resource criticality based on tags and characteristics."""
        resource_data = optimization_data.get('resourceData', {})
        tags = resource_data.get('tags', {})
        
        # Check for critical tags
        critical_tags = self.risk_assessment_rules['resource_criticality_factors']['critical_tags']
        if any(tag.lower() in critical_tags for tag in tags.values()):
            return 'CRITICAL'
        
        # Check for production tags
        production_tags = self.risk_assessment_rules['resource_criticality_factors']['production_tags']
        if any(tag.lower() in production_tags for tag in tags.values()):
            return 'HIGH'
        
        # Check for high cost
        current_cost = optimization_data.get('currentCost', 0)
        high_cost_threshold = self.risk_assessment_rules['resource_criticality_factors']['high_cost_threshold']
        if current_cost > high_cost_threshold:
            return 'HIGH'
        
        return 'MEDIUM'
    
    def _assess_business_impact(self, optimization_data: Dict[str, Any]) -> str:
        """Assess business impact of the optimization."""
        estimated_savings = optimization_data.get('estimatedSavings', 0)
        operation_type = optimization_data.get('optimizationType', 'unknown')
        
        # High impact for large savings or risky operations
        if estimated_savings > 5000 or operation_type == 'cleanup':
            return 'HIGH'
        elif estimated_savings > 1000 or operation_type in ['rightsizing', 'storage_optimization']:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _create_workflow_steps(self, 
                              approval_requirements: ApprovalRequirement,
                              workflow_id: str) -> List[WorkflowStep]:
        """Create workflow steps based on approval requirements."""
        steps = []
        
        if approval_requirements.auto_approval_eligible:
            # Single auto-approval step
            steps.append(WorkflowStep(
                step_id=f"{workflow_id}_auto",
                step_name="Automatic Approval",
                required_authority=ApprovalAuthority.SYSTEM,
                status=ApprovalStatus.PENDING,
                assigned_to="system",
                completed_by=None,
                completed_at=None,
                comments="Eligible for automatic approval",
                timeout_at=None
            ))
        else:
            # Manual approval step
            timeout_at = datetime.utcnow() + timedelta(hours=approval_requirements.approval_timeout_hours)
            
            steps.append(WorkflowStep(
                step_id=f"{workflow_id}_approval",
                step_name=f"{approval_requirements.authority_required.value} Approval",
                required_authority=approval_requirements.authority_required,
                status=ApprovalStatus.PENDING,
                assigned_to=None,  # Will be assigned when routed
                completed_by=None,
                completed_at=None,
                comments=None,
                timeout_at=timeout_at.isoformat()
            ))
            
            # Add additional steps if required
            if approval_requirements.requires_rollback_plan:
                steps.append(WorkflowStep(
                    step_id=f"{workflow_id}_rollback",
                    step_name="Rollback Plan Review",
                    required_authority=ApprovalAuthority.ENGINEER,
                    status=ApprovalStatus.PENDING,
                    assigned_to=None,
                    completed_by=None,
                    completed_at=None,
                    comments="Rollback plan validation required",
                    timeout_at=timeout_at.isoformat()
                ))
        
        return steps
    
    def _process_auto_approval(self, workflow_id: str) -> Dict[str, Any]:
        """Process automatic approval for eligible workflows."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return {'error': 'Workflow not found'}
        
        # Update workflow state
        workflow['state'] = WorkflowState.APPROVED.value
        workflow['approved_at'] = datetime.utcnow().isoformat()
        workflow['approved_by'] = 'system'
        
        # Update workflow steps
        for step in workflow['workflow_steps']:
            if step['required_authority'] == ApprovalAuthority.SYSTEM.value:
                step['status'] = ApprovalStatus.APPROVED.value
                step['completed_by'] = 'system'
                step['completed_at'] = datetime.utcnow().isoformat()
                step['comments'] = 'Automatically approved - low risk, low savings'
        
        logger.info(f"Workflow {workflow_id} automatically approved")
        
        return {
            'auto_approved': True,
            'approved_at': workflow['approved_at'],
            'approved_by': 'system'
        }
    
    def submit_approval(self, 
                       workflow_id: str,
                       approver: str,
                       decision: str,
                       comments: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit an approval decision for a workflow.
        
        Args:
            workflow_id: ID of the workflow
            approver: User submitting the approval
            decision: 'approve' or 'reject'
            comments: Optional comments
            
        Returns:
            Approval submission result
        """
        if workflow_id not in self.active_workflows:
            return {
                'success': False,
                'message': f'Workflow {workflow_id} not found'
            }
        
        workflow = self.active_workflows[workflow_id]
        
        # Check if workflow is in correct state
        if workflow['state'] not in [WorkflowState.CREATED.value, WorkflowState.UNDER_REVIEW.value, WorkflowState.AWAITING_APPROVAL.value]:
            return {
                'success': False,
                'message': f'Workflow {workflow_id} is not in a state that accepts approvals'
            }
        
        # Check for timeout
        timeout_at = datetime.fromisoformat(workflow['timeout_at'])
        if datetime.utcnow() > timeout_at:
            workflow['state'] = WorkflowState.EXPIRED.value
            return {
                'success': False,
                'message': f'Workflow {workflow_id} has expired'
            }
        
        # Process approval decision
        if decision.lower() == 'approve':
            return self._process_approval(workflow_id, approver, comments)
        elif decision.lower() == 'reject':
            return self._process_rejection(workflow_id, approver, comments)
        else:
            return {
                'success': False,
                'message': f'Invalid decision: {decision}. Must be "approve" or "reject"'
            }
    
    def _process_approval(self, 
                         workflow_id: str,
                         approver: str,
                         comments: Optional[str]) -> Dict[str, Any]:
        """Process approval decision."""
        workflow = self.active_workflows[workflow_id]
        
        # Update workflow state
        workflow['state'] = WorkflowState.APPROVED.value
        workflow['approved_at'] = datetime.utcnow().isoformat()
        workflow['approved_by'] = approver
        
        # Update workflow steps
        for step in workflow['workflow_steps']:
            if step['status'] == ApprovalStatus.PENDING.value:
                step['status'] = ApprovalStatus.APPROVED.value
                step['completed_by'] = approver
                step['completed_at'] = datetime.utcnow().isoformat()
                step['comments'] = comments or 'Approved'
                break
        
        logger.info(f"Workflow {workflow_id} approved by {approver}")
        
        # Send approval notification
        self.send_stakeholder_notification(
            workflow_id=workflow_id,
            notification_type='approved'
        )
        
        return {
            'success': True,
            'message': f'Workflow {workflow_id} approved',
            'workflow_id': workflow_id,
            'approved_by': approver,
            'approved_at': workflow['approved_at']
        }
    
    def _process_rejection(self, 
                          workflow_id: str,
                          approver: str,
                          comments: Optional[str]) -> Dict[str, Any]:
        """Process rejection decision."""
        workflow = self.active_workflows[workflow_id]
        
        # Update workflow state
        workflow['state'] = WorkflowState.REJECTED.value
        workflow['rejected_at'] = datetime.utcnow().isoformat()
        workflow['rejected_by'] = approver
        workflow['rejection_reason'] = comments or 'No reason provided'
        
        # Update workflow steps
        for step in workflow['workflow_steps']:
            if step['status'] == ApprovalStatus.PENDING.value:
                step['status'] = ApprovalStatus.REJECTED.value
                step['completed_by'] = approver
                step['completed_at'] = datetime.utcnow().isoformat()
                step['comments'] = comments or 'Rejected'
                break
        
        # Move to completed workflows
        self.completed_workflows[workflow_id] = workflow
        del self.active_workflows[workflow_id]
        
        logger.info(f"Workflow {workflow_id} rejected by {approver}")
        
        # Send rejection notification
        self.send_stakeholder_notification(
            workflow_id=workflow_id,
            notification_type='rejected'
        )
        
        return {
            'success': True,
            'message': f'Workflow {workflow_id} rejected',
            'workflow_id': workflow_id,
            'rejected_by': approver,
            'rejected_at': workflow['rejected_at']
        }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get current status of a workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Workflow status information
        """
        # Check active workflows first
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
        elif workflow_id in self.completed_workflows:
            workflow = self.completed_workflows[workflow_id]
        else:
            return {
                'success': False,
                'message': f'Workflow {workflow_id} not found'
            }
        
        # Check for timeout
        if workflow['state'] in [WorkflowState.CREATED.value, WorkflowState.UNDER_REVIEW.value, WorkflowState.AWAITING_APPROVAL.value]:
            timeout_at = datetime.fromisoformat(workflow['timeout_at'])
            if datetime.utcnow() > timeout_at:
                workflow['state'] = WorkflowState.EXPIRED.value
                if workflow_id in self.active_workflows:
                    self.completed_workflows[workflow_id] = workflow
                    del self.active_workflows[workflow_id]
        
        return {
            'success': True,
            'workflow': workflow
        }
    
    def get_pending_approvals(self, 
                             authority_level: Optional[ApprovalAuthority] = None) -> List[Dict[str, Any]]:
        """
        Get list of workflows pending approval.
        
        Args:
            authority_level: Filter by required authority level
            
        Returns:
            List of pending approval workflows
        """
        pending_workflows = []
        
        for workflow_id, workflow in self.active_workflows.items():
            if workflow['state'] in [WorkflowState.CREATED.value, WorkflowState.UNDER_REVIEW.value, WorkflowState.AWAITING_APPROVAL.value]:
                # Check for timeout
                timeout_at = datetime.fromisoformat(workflow['timeout_at'])
                if datetime.utcnow() > timeout_at:
                    workflow['state'] = WorkflowState.EXPIRED.value
                    continue
                
                # Filter by authority level if specified
                if authority_level:
                    required_authority = workflow['approval_requirements']['authority_required']
                    if required_authority != authority_level.value:
                        continue
                
                pending_workflows.append(workflow)
        
        return pending_workflows
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive workflow metrics and statistics.
        
        Returns:
            Workflow metrics and statistics
        """
        total_workflows = len(self.active_workflows) + len(self.completed_workflows)
        
        if total_workflows == 0:
            return {
                'total_workflows': 0,
                'dry_run_mode': self.dry_run,
                'message': 'No workflows recorded'
            }
        
        # Count by state
        state_counts = {}
        for state in WorkflowState:
            state_counts[state.value] = 0
        
        for workflow in self.active_workflows.values():
            state = workflow.get('state', WorkflowState.CREATED.value)
            state_counts[state] = state_counts.get(state, 0) + 1
        
        for workflow in self.completed_workflows.values():
            state = workflow.get('state', WorkflowState.COMPLETED.value)
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # Count by risk level
        risk_counts = {}
        for risk in RiskLevel:
            risk_counts[risk.value] = 0
        
        all_workflows = list(self.active_workflows.values()) + list(self.completed_workflows.values())
        for workflow in all_workflows:
            risk = workflow.get('risk_level', RiskLevel.MEDIUM.value)
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        # Count by authority level
        authority_counts = {}
        for authority in ApprovalAuthority:
            authority_counts[authority.value] = 0
        
        for workflow in all_workflows:
            authority = workflow.get('approval_requirements', {}).get('authority_required', ApprovalAuthority.ENGINEER.value)
            authority_counts[authority] = authority_counts.get(authority, 0) + 1
        
        # Calculate approval rates
        approved_count = state_counts.get(WorkflowState.APPROVED.value, 0)
        rejected_count = state_counts.get(WorkflowState.REJECTED.value, 0)
        completed_count = approved_count + rejected_count
        
        approval_rate = (approved_count / max(completed_count, 1)) * 100
        
        # Calculate average processing time
        processing_times = []
        for workflow in self.completed_workflows.values():
            created_at = datetime.fromisoformat(workflow['created_at'])
            if 'approved_at' in workflow:
                completed_at = datetime.fromisoformat(workflow['approved_at'])
            elif 'rejected_at' in workflow:
                completed_at = datetime.fromisoformat(workflow['rejected_at'])
            else:
                continue
            
            processing_time = (completed_at - created_at).total_seconds() / 3600  # hours
            processing_times.append(processing_time)
        
        avg_processing_time = sum(processing_times) / max(len(processing_times), 1)
        
        return {
            'total_workflows': total_workflows,
            'active_workflows': len(self.active_workflows),
            'completed_workflows': len(self.completed_workflows),
            'dry_run_mode': self.dry_run,
            'state_distribution': state_counts,
            'risk_distribution': risk_counts,
            'authority_distribution': authority_counts,
            'approval_rate_percentage': round(approval_rate, 2),
            'average_processing_time_hours': round(avg_processing_time, 2),
            'pending_approvals': len(self.get_pending_approvals())
        }
    
    def cleanup_expired_workflows(self) -> Dict[str, Any]:
        """
        Clean up expired workflows and move them to completed.
        
        Returns:
            Cleanup results
        """
        expired_count = 0
        current_time = datetime.utcnow()
        
        expired_workflows = []
        for workflow_id, workflow in list(self.active_workflows.items()):
            timeout_at = datetime.fromisoformat(workflow['timeout_at'])
            if current_time > timeout_at:
                workflow['state'] = WorkflowState.EXPIRED.value
                workflow['expired_at'] = current_time.isoformat()
                
                self.completed_workflows[workflow_id] = workflow
                del self.active_workflows[workflow_id]
                
                expired_workflows.append(workflow_id)
                expired_count += 1
        
        logger.info(f"Cleaned up {expired_count} expired workflows")
        
        return {
            'expired_count': expired_count,
            'expired_workflows': expired_workflows,
            'cleanup_timestamp': current_time.isoformat()
        }
    
    def send_stakeholder_notification(self, 
                                    workflow_id: str,
                                    notification_type: str,
                                    recipients: List[str] = None) -> Dict[str, Any]:
        """
        Send stakeholder notifications for workflow events.
        
        Args:
            workflow_id: ID of the workflow
            notification_type: Type of notification ('created', 'approved', 'rejected', 'expired', 'escalated')
            recipients: List of email addresses to notify
            
        Returns:
            Notification result
        """
        if workflow_id not in self.active_workflows and workflow_id not in self.completed_workflows:
            return {
                'success': False,
                'message': f'Workflow {workflow_id} not found'
            }
        
        # Get workflow data
        workflow = self.active_workflows.get(workflow_id) or self.completed_workflows.get(workflow_id)
        
        # Determine recipients if not provided
        if not recipients:
            recipients = self._get_notification_recipients(workflow, notification_type)
        
        if self.dry_run:
            logger.info(
                f"DRY_RUN: Would send {notification_type} notification for workflow {workflow_id} "
                f"to {len(recipients)} recipients: {recipients}"
            )
            return {
                'success': True,
                'dry_run': True,
                'notification_type': notification_type,
                'recipients': recipients,
                'message': f'DRY_RUN: Notification would be sent to {len(recipients)} recipients'
            }
        
        # Generate notification content
        notification_content = self._generate_notification_content(workflow, notification_type)
        
        # Send notifications (in real implementation, this would use actual email service)
        sent_count = 0
        failed_recipients = []
        
        for recipient in recipients:
            try:
                # In a real implementation, this would send actual emails
                # For demo purposes, we'll just log the notification
                logger.info(
                    f"Sending {notification_type} notification to {recipient} "
                    f"for workflow {workflow_id}: {notification_content['subject']}"
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send notification to {recipient}: {str(e)}")
                failed_recipients.append(recipient)
        
        # Record notification in workflow
        if 'notifications' not in workflow:
            workflow['notifications'] = []
        
        workflow['notifications'].append({
            'notification_id': str(uuid.uuid4()),
            'type': notification_type,
            'sent_at': datetime.utcnow().isoformat(),
            'recipients': recipients,
            'sent_count': sent_count,
            'failed_recipients': failed_recipients,
            'subject': notification_content['subject']
        })
        
        return {
            'success': True,
            'notification_type': notification_type,
            'recipients_count': len(recipients),
            'sent_count': sent_count,
            'failed_count': len(failed_recipients),
            'failed_recipients': failed_recipients
        }
    
    def _get_notification_recipients(self, 
                                   workflow: Dict[str, Any],
                                   notification_type: str) -> List[str]:
        """
        Determine notification recipients based on workflow and notification type.
        
        Args:
            workflow: Workflow data
            notification_type: Type of notification
            
        Returns:
            List of recipient email addresses
        """
        recipients = []
        
        # Always include the requester
        if workflow.get('requester'):
            recipients.append(workflow['requester'])
        
        # Add authority-specific recipients based on approval requirements
        authority_required = workflow.get('approval_requirements', {}).get('authority_required')
        
        # In a real implementation, these would be configured email lists
        authority_email_mapping = {
            'SYSTEM': [],  # No additional notifications for system approvals
            'ENGINEER': ['engineering-team@company.com'],
            'MANAGER': ['engineering-managers@company.com', 'finops-team@company.com'],
            'DIRECTOR': ['engineering-directors@company.com', 'finops-directors@company.com'],
            'EXECUTIVE': ['executives@company.com', 'cfo@company.com']
        }
        
        if authority_required in authority_email_mapping:
            recipients.extend(authority_email_mapping[authority_required])
        
        # Add escalation recipients for high-value or critical workflows
        estimated_savings = workflow.get('optimization_data', {}).get('estimatedSavings', 0)
        risk_level = workflow.get('risk_level', 'MEDIUM')
        
        if estimated_savings > 10000 or risk_level == 'CRITICAL':
            recipients.extend(['finops-directors@company.com', 'cost-optimization@company.com'])
        
        # Add resource-specific stakeholders based on tags
        resource_data = workflow.get('optimization_data', {}).get('resourceData', {})
        tags = resource_data.get('tags', {})
        
        # Add team-specific notifications
        if 'Team' in tags:
            team = tags['Team'].lower()
            recipients.append(f'{team}-team@company.com')
        
        # Add environment-specific notifications for production resources
        if any(env in tags.get('Environment', '').lower() for env in ['prod', 'production']):
            recipients.extend(['production-team@company.com', 'sre-team@company.com'])
        
        # Remove duplicates and return
        return list(set(recipients))
    
    def _generate_notification_content(self, 
                                     workflow: Dict[str, Any],
                                     notification_type: str) -> Dict[str, str]:
        """
        Generate notification content based on workflow and notification type.
        
        Args:
            workflow: Workflow data
            notification_type: Type of notification
            
        Returns:
            Dictionary with 'subject' and 'body' keys
        """
        workflow_id = workflow['workflow_id']
        resource_id = workflow.get('resource_id', 'Unknown')
        optimization_type = workflow.get('optimization_data', {}).get('optimizationType', 'unknown')
        estimated_savings = workflow.get('optimization_data', {}).get('estimatedSavings', 0)
        risk_level = workflow.get('risk_level', 'MEDIUM')
        
        content_templates = {
            'created': {
                'subject': f'FinOps Approval Required: {optimization_type.title()} for {resource_id}',
                'body': f"""
A new cost optimization workflow requires approval:

Workflow ID: {workflow_id}
Resource: {resource_id}
Optimization Type: {optimization_type.title()}
Estimated Savings: ${estimated_savings:.2f}
Risk Level: {risk_level}
Requester: {workflow.get('requester', 'Unknown')}

Justification: {workflow.get('justification', 'No justification provided')}

Please review and approve/reject this optimization request.
                """
            },
            'approved': {
                'subject': f'FinOps Workflow Approved: {optimization_type.title()} for {resource_id}',
                'body': f"""
Cost optimization workflow has been approved:

Workflow ID: {workflow_id}
Resource: {resource_id}
Optimization Type: {optimization_type.title()}
Estimated Savings: ${estimated_savings:.2f}
Approved By: {workflow.get('approved_by', 'Unknown')}
Approved At: {workflow.get('approved_at', 'Unknown')}

The optimization will be executed according to the approved plan.
                """
            },
            'rejected': {
                'subject': f'FinOps Workflow Rejected: {optimization_type.title()} for {resource_id}',
                'body': f"""
Cost optimization workflow has been rejected:

Workflow ID: {workflow_id}
Resource: {resource_id}
Optimization Type: {optimization_type.title()}
Estimated Savings: ${estimated_savings:.2f}
Rejected By: {workflow.get('rejected_by', 'Unknown')}
Rejected At: {workflow.get('rejected_at', 'Unknown')}

Reason: {workflow.get('rejection_reason', 'No reason provided')}
                """
            },
            'expired': {
                'subject': f'FinOps Workflow Expired: {optimization_type.title()} for {resource_id}',
                'body': f"""
Cost optimization workflow has expired without approval:

Workflow ID: {workflow_id}
Resource: {resource_id}
Optimization Type: {optimization_type.title()}
Estimated Savings: ${estimated_savings:.2f}
Expired At: {workflow.get('expired_at', 'Unknown')}

The optimization opportunity may no longer be valid. Please review if re-submission is needed.
                """
            },
            'escalated': {
                'subject': f'FinOps Workflow Escalated: {optimization_type.title()} for {resource_id}',
                'body': f"""
Cost optimization workflow has been escalated for higher-level approval:

Workflow ID: {workflow_id}
Resource: {resource_id}
Optimization Type: {optimization_type.title()}
Estimated Savings: ${estimated_savings:.2f}
Risk Level: {risk_level}
Escalation Reason: High-value or high-risk optimization requires additional approval

Please review and provide executive-level approval for this optimization.
                """
            }
        }
        
        return content_templates.get(notification_type, {
            'subject': f'FinOps Workflow Notification: {workflow_id}',
            'body': f'Workflow {workflow_id} status update: {notification_type}'
        })
    
    def escalate_workflow(self, 
                         workflow_id: str,
                         escalation_reason: str,
                         escalated_by: str) -> Dict[str, Any]:
        """
        Escalate workflow to higher authority level.
        
        Args:
            workflow_id: ID of the workflow to escalate
            escalation_reason: Reason for escalation
            escalated_by: User initiating the escalation
            
        Returns:
            Escalation result
        """
        if workflow_id not in self.active_workflows:
            return {
                'success': False,
                'message': f'Workflow {workflow_id} not found or not active'
            }
        
        workflow = self.active_workflows[workflow_id]
        
        # Check if workflow is in a state that allows escalation
        if workflow['state'] not in [WorkflowState.CREATED.value, WorkflowState.UNDER_REVIEW.value, WorkflowState.AWAITING_APPROVAL.value]:
            return {
                'success': False,
                'message': f'Workflow {workflow_id} cannot be escalated in current state: {workflow["state"]}'
            }
        
        # Determine current and next authority levels
        current_authority = ApprovalAuthority(workflow['approval_requirements']['authority_required'])
        
        # Define escalation hierarchy
        escalation_hierarchy = [
            ApprovalAuthority.SYSTEM,
            ApprovalAuthority.ENGINEER,
            ApprovalAuthority.MANAGER,
            ApprovalAuthority.DIRECTOR,
            ApprovalAuthority.EXECUTIVE
        ]
        
        try:
            current_index = escalation_hierarchy.index(current_authority)
            if current_index >= len(escalation_hierarchy) - 1:
                return {
                    'success': False,
                    'message': f'Workflow {workflow_id} is already at the highest authority level'
                }
            
            next_authority = escalation_hierarchy[current_index + 1]
        except ValueError:
            return {
                'success': False,
                'message': f'Invalid current authority level: {current_authority.value}'
            }
        
        # Update workflow with escalation
        workflow['approval_requirements']['authority_required'] = next_authority.value
        workflow['state'] = WorkflowState.AWAITING_APPROVAL.value
        
        # Extend timeout for escalated approval
        current_timeout = datetime.fromisoformat(workflow['timeout_at'])
        extended_timeout = current_timeout + timedelta(hours=24)  # Add 24 hours for escalation
        workflow['timeout_at'] = extended_timeout.isoformat()
        
        # Record escalation history
        if 'escalation_history' not in workflow:
            workflow['escalation_history'] = []
        
        escalation_record = {
            'escalation_id': str(uuid.uuid4()),
            'escalated_at': datetime.utcnow().isoformat(),
            'escalated_by': escalated_by,
            'escalation_reason': escalation_reason,
            'from_authority': current_authority.value,
            'to_authority': next_authority.value,
            'timeout_extended_to': extended_timeout.isoformat()
        }
        
        workflow['escalation_history'].append(escalation_record)
        
        # Update workflow steps
        for step in workflow['workflow_steps']:
            if step['status'] == ApprovalStatus.PENDING.value:
                step['required_authority'] = next_authority.value
                step['step_name'] = f"{next_authority.value} Approval (Escalated)"
                step['timeout_at'] = extended_timeout.isoformat()
                step['comments'] = f"Escalated: {escalation_reason}"
                break
        
        # Send escalation notifications
        notification_result = self.send_stakeholder_notification(
            workflow_id=workflow_id,
            notification_type='escalated'
        )
        
        logger.info(
            f"Workflow {workflow_id} escalated from {current_authority.value} to {next_authority.value} "
            f"by {escalated_by}. Reason: {escalation_reason}"
        )
        
        return {
            'success': True,
            'workflow_id': workflow_id,
            'escalated_from': current_authority.value,
            'escalated_to': next_authority.value,
            'escalated_by': escalated_by,
            'escalation_reason': escalation_reason,
            'new_timeout': extended_timeout.isoformat(),
            'notification_sent': notification_result.get('success', False)
        }
    
    def check_workflow_timeouts(self) -> Dict[str, Any]:
        """
        Check for workflow timeouts and handle them appropriately.
        
        Returns:
            Timeout check results with actions taken
        """
        current_time = datetime.utcnow()
        timeout_actions = {
            'expired_workflows': [],
            'escalated_workflows': [],
            'notification_sent': []
        }
        
        for workflow_id, workflow in list(self.active_workflows.items()):
            if workflow['state'] not in [WorkflowState.CREATED.value, WorkflowState.UNDER_REVIEW.value, WorkflowState.AWAITING_APPROVAL.value]:
                continue
            
            timeout_at = datetime.fromisoformat(workflow['timeout_at'])
            
            # Check if workflow has timed out
            if current_time > timeout_at:
                # Determine if escalation is possible
                current_authority = ApprovalAuthority(workflow['approval_requirements']['authority_required'])
                escalation_hierarchy = [ApprovalAuthority.SYSTEM, ApprovalAuthority.ENGINEER, ApprovalAuthority.MANAGER, ApprovalAuthority.DIRECTOR, ApprovalAuthority.EXECUTIVE]
                
                try:
                    current_index = escalation_hierarchy.index(current_authority)
                    can_escalate = current_index < len(escalation_hierarchy) - 1
                except ValueError:
                    can_escalate = False
                
                # Check if this is a high-value workflow that should be escalated instead of expired
                estimated_savings = workflow.get('optimization_data', {}).get('estimatedSavings', 0)
                risk_level = workflow.get('risk_level', 'MEDIUM')
                should_escalate = (
                    can_escalate and 
                    (estimated_savings > 5000 or risk_level in ['HIGH', 'CRITICAL']) and
                    len(workflow.get('escalation_history', [])) < 2  # Limit escalations
                )
                
                if should_escalate:
                    # Auto-escalate high-value workflows
                    escalation_result = self.escalate_workflow(
                        workflow_id=workflow_id,
                        escalation_reason=f"Automatic escalation due to timeout - High value (${estimated_savings:.2f}) or high risk ({risk_level})",
                        escalated_by='system'
                    )
                    
                    if escalation_result['success']:
                        timeout_actions['escalated_workflows'].append({
                            'workflow_id': workflow_id,
                            'escalated_to': escalation_result['escalated_to'],
                            'reason': 'timeout_auto_escalation'
                        })
                        
                        logger.info(f"Auto-escalated workflow {workflow_id} due to timeout")
                else:
                    # Expire the workflow
                    workflow['state'] = WorkflowState.EXPIRED.value
                    workflow['expired_at'] = current_time.isoformat()
                    
                    # Move to completed workflows
                    self.completed_workflows[workflow_id] = workflow
                    del self.active_workflows[workflow_id]
                    
                    timeout_actions['expired_workflows'].append({
                        'workflow_id': workflow_id,
                        'expired_at': current_time.isoformat()
                    })
                    
                    # Send expiration notification
                    notification_result = self.send_stakeholder_notification(
                        workflow_id=workflow_id,
                        notification_type='expired'
                    )
                    
                    if notification_result.get('success'):
                        timeout_actions['notification_sent'].append({
                            'workflow_id': workflow_id,
                            'notification_type': 'expired'
                        })
                    
                    logger.info(f"Workflow {workflow_id} expired due to timeout")
        
        return {
            'check_timestamp': current_time.isoformat(),
            'expired_count': len(timeout_actions['expired_workflows']),
            'escalated_count': len(timeout_actions['escalated_workflows']),
            'notifications_sent': len(timeout_actions['notification_sent']),
            'actions_taken': timeout_actions
        }


# Utility functions for external use
def create_approval_workflow(dry_run: bool = True) -> ApprovalWorkflow:
    """
    Factory function to create ApprovalWorkflow instance.
    
    Args:
        dry_run: Enable DRY_RUN mode
        
    Returns:
        Configured ApprovalWorkflow instance
    """
    return ApprovalWorkflow(dry_run=dry_run)


def assess_optimization_risk(optimization_data: Dict[str, Any]) -> RiskLevel:
    """
    Utility function to assess risk level for optimization data.
    
    Args:
        optimization_data: Optimization recommendation data
        
    Returns:
        Assessed risk level
    """
    workflow = create_approval_workflow()
    return workflow.assess_risk(optimization_data)


def escalate_workflow_by_id(workflow_system: ApprovalWorkflow, 
                           workflow_id: str,
                           escalation_reason: str,
                           escalated_by: str) -> Dict[str, Any]:
    """
    Utility function to escalate a workflow by ID.
    
    Args:
        workflow_system: ApprovalWorkflow instance
        workflow_id: ID of the workflow to escalate
        escalation_reason: Reason for escalation
        escalated_by: User initiating the escalation
        
    Returns:
        Escalation result
    """
    return workflow_system.escalate_workflow(workflow_id, escalation_reason, escalated_by)


def send_workflow_notification(workflow_system: ApprovalWorkflow,
                             workflow_id: str,
                             notification_type: str,
                             recipients: List[str] = None) -> Dict[str, Any]:
    """
    Utility function to send workflow notifications.
    
    Args:
        workflow_system: ApprovalWorkflow instance
        workflow_id: ID of the workflow
        notification_type: Type of notification
        recipients: Optional list of recipients
        
    Returns:
        Notification result
    """
    return workflow_system.send_stakeholder_notification(workflow_id, notification_type, recipients)


if __name__ == "__main__":
    # Example usage and testing
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create approval workflow system
    workflow_system = create_approval_workflow(dry_run=True)
    
    # Example optimization data
    optimization_data = {
        'optimizationId': 'opt_123',
        'resourceId': 'i-1234567890abcdef0',
        'resourceType': 'ec2',
        'optimizationType': 'cleanup',
        'currentCost': 150.0,
        'estimatedSavings': 150.0,
        'riskLevel': 'HIGH',
        'resourceData': {
            'instanceType': 't3.micro',
            'tags': {'Environment': 'production', 'Team': 'backend'}
        }
    }
    
    # Create workflow
    workflow = workflow_system.create_workflow(
        optimization_data=optimization_data,
        requester='john.doe@company.com',
        justification='Instance has been unused for 30 days with 0% CPU utilization'
    )
    
    print("Approval Workflow Test Result:")
    print(json.dumps(workflow, indent=2, default=str))
    
    # Test escalation
    workflow_id = workflow['workflow_id']
    escalation_result = workflow_system.escalate_workflow(
        workflow_id=workflow_id,
        escalation_reason='High-value optimization requires executive approval',
        escalated_by='manager@company.com'
    )
    
    print("\nEscalation Result:")
    print(json.dumps(escalation_result, indent=2, default=str))
    
    # Test timeout checking
    timeout_result = workflow_system.check_workflow_timeouts()
    print("\nTimeout Check Result:")
    print(json.dumps(timeout_result, indent=2, default=str))
    
    # Display workflow metrics
    metrics = workflow_system.get_workflow_metrics()
    print("\nWorkflow Metrics:")
    print(json.dumps(metrics, indent=2))