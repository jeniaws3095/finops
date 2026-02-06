#!/usr/bin/env python3
"""
Unit tests for safety_controls.py

Tests comprehensive safety controls including:
- DRY_RUN validation
- Rollback capabilities
- Risk assessment
- Operation logging
- Approval workflows
"""

import pytest
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

from utils.safety_controls import (
    SafetyControls, 
    OperationType, 
    RiskLevel, 
    OperationStatus,
    RollbackCapability,
    create_safety_controls,
    validate_dry_run_mode,
    setup_comprehensive_logging
)


class TestSafetyControls:
    """Test suite for SafetyControls class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_log = tempfile.NamedTemporaryFile(delete=False, suffix='.log')
        self.safety_controls = SafetyControls(dry_run=True, log_file=self.temp_log.name)
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_log.name):
            os.unlink(self.temp_log.name)
    
    def test_initialization_dry_run_mode(self):
        """Test SafetyControls initialization in DRY_RUN mode."""
        assert self.safety_controls.dry_run is True
        assert self.safety_controls.log_file == self.temp_log.name
        assert len(self.safety_controls.operation_history) == 0
        assert len(self.safety_controls.rollback_plans) == 0
    
    def test_initialization_live_mode(self):
        """Test SafetyControls initialization in LIVE mode."""
        live_safety = SafetyControls(dry_run=False, log_file=self.temp_log.name)
        assert live_safety.dry_run is False
    
    def test_risk_assessment_terminate_instance(self):
        """Test risk assessment for instance termination."""
        # Test production instance (should be CRITICAL)
        prod_resource = {
            'resource_id': 'i-prod123',
            'instance_type': 'm5.large',
            'tags': {'Environment': 'production'}
        }
        risk = self.safety_controls.assess_risk(OperationType.TERMINATE_INSTANCE, prod_resource)
        assert risk == RiskLevel.CRITICAL
        
        # Test development instance (should be HIGH)
        dev_resource = {
            'resource_id': 'i-dev123',
            'instance_type': 't3.micro',
            'tags': {'Environment': 'development'}
        }
        risk = self.safety_controls.assess_risk(OperationType.TERMINATE_INSTANCE, dev_resource)
        assert risk == RiskLevel.HIGH
    
    def test_risk_assessment_stop_instance(self):
        """Test risk assessment for instance stop."""
        resource = {
            'resource_id': 'i-test123',
            'instance_type': 't3.micro'
        }
        risk = self.safety_controls.assess_risk(OperationType.STOP_INSTANCE, resource)
        assert risk == RiskLevel.LOW
    
    def test_rollback_capability_assessment(self):
        """Test rollback capability assessment."""
        assert self.safety_controls.get_rollback_capability(OperationType.TERMINATE_INSTANCE) == RollbackCapability.NONE
        assert self.safety_controls.get_rollback_capability(OperationType.STOP_INSTANCE) == RollbackCapability.FULL
        assert self.safety_controls.get_rollback_capability(OperationType.RESIZE_INSTANCE) == RollbackCapability.FULL
        assert self.safety_controls.get_rollback_capability(OperationType.DELETE_VOLUME) == RollbackCapability.NONE
    
    def test_dry_run_operation_simulation(self):
        """Test operation simulation in DRY_RUN mode."""
        def dummy_operation():
            return {"success": True, "message": "Real operation"}
        
        resource_data = {
            'resource_id': 'i-test123',
            'instance_type': 't3.micro',
            'monthly_cost': 15.0
        }
        
        result = self.safety_controls.validate_operation(
            operation_type=OperationType.STOP_INSTANCE,
            resource_id='i-test123',
            resource_data=resource_data,
            operation_func=dummy_operation
        )
        
        assert result['success'] is True
        assert result['simulated'] is True
        assert 'Would stop instance' in result['message']
        assert len(self.safety_controls.operation_history) == 1
        
        # Check operation record
        op_record = self.safety_controls.operation_history[0]
        assert op_record['operation_type'] == OperationType.STOP_INSTANCE.value
        assert op_record['resource_id'] == 'i-test123'
        assert op_record['status'] == OperationStatus.SIMULATED.value
        assert op_record['dry_run'] is True
    
    def test_approval_requirement_logic(self):
        """Test approval requirement logic."""
        # LOW and MEDIUM risk should not require approval
        assert not self.safety_controls._requires_approval(RiskLevel.LOW)
        assert not self.safety_controls._requires_approval(RiskLevel.MEDIUM)
        
        # HIGH and CRITICAL risk should require approval
        assert self.safety_controls._requires_approval(RiskLevel.HIGH)
        assert self.safety_controls._requires_approval(RiskLevel.CRITICAL)
    
    def test_rollback_plan_creation(self):
        """Test rollback plan creation."""
        operations = [
            {
                'operation_id': 'op-123',
                'operation_type': 'STOP_INSTANCE',
                'resource_id': 'i-test123',
                'resource_data': {'instance_type': 't3.micro'}
            }
        ]
        
        rollback_plan = self.safety_controls.create_rollback_plan(operations)
        
        assert 'rollback_plan_id' in rollback_plan
        assert rollback_plan['total_operations'] == 1
        assert rollback_plan['total_steps'] == 1
        assert rollback_plan['rollback_steps'][0]['action'] == 'START_INSTANCE'
        assert rollback_plan['rollback_steps'][0]['resource_id'] == 'i-test123'
    
    def test_detailed_rollback_plan_creation(self):
        """Test detailed rollback plan creation for specific operation."""
        operation_record = {
            'operation_id': 'op-456',
            'operation_type': OperationType.STOP_INSTANCE.value,
            'resource_id': 'i-test456',
            'resource_data': {'instance_type': 't3.small'}
        }
        
        rollback_plan = self.safety_controls._create_detailed_rollback_plan(operation_record)
        
        assert rollback_plan['operation_id'] == 'op-456'
        assert rollback_plan['rollback_capability'] == RollbackCapability.FULL.value
        assert len(rollback_plan['steps']) == 1
        assert rollback_plan['steps'][0]['action'] == OperationType.START_INSTANCE.value
        assert rollback_plan['estimated_total_time_minutes'] == 2
    
    def test_rollback_execution_dry_run(self):
        """Test rollback execution in DRY_RUN mode."""
        # First create an operation with rollback plan
        operation_record = {
            'operation_id': 'op-rollback-test',
            'operation_type': OperationType.STOP_INSTANCE.value,
            'resource_id': 'i-rollback-test',
            'resource_data': {'instance_type': 't3.micro'}
        }
        
        rollback_plan = self.safety_controls._create_detailed_rollback_plan(operation_record)
        self.safety_controls.rollback_plans['op-rollback-test'] = rollback_plan
        
        # Execute rollback
        result = self.safety_controls.execute_rollback('op-rollback-test')
        
        assert result['success'] is True
        assert result['simulated'] is True
        assert result['steps_simulated'] == 1
        assert result['total_steps'] == 1
    
    def test_operation_history_filtering(self):
        """Test operation history filtering capabilities."""
        # Add some test operations
        self.safety_controls.operation_history = [
            {
                'operation_id': 'op-1',
                'operation_type': OperationType.STOP_INSTANCE.value,
                'risk_level': RiskLevel.LOW.value,
                'status': OperationStatus.SIMULATED.value
            },
            {
                'operation_id': 'op-2',
                'operation_type': OperationType.TERMINATE_INSTANCE.value,
                'risk_level': RiskLevel.HIGH.value,
                'status': OperationStatus.PENDING.value
            }
        ]
        
        # Test filtering by operation type
        stop_ops = self.safety_controls.get_operation_history(operation_type=OperationType.STOP_INSTANCE)
        assert len(stop_ops) == 1
        assert stop_ops[0]['operation_id'] == 'op-1'
        
        # Test filtering by risk level
        high_risk_ops = self.safety_controls.get_operation_history(risk_level=RiskLevel.HIGH)
        assert len(high_risk_ops) == 1
        assert high_risk_ops[0]['operation_id'] == 'op-2'
        
        # Test filtering by status
        pending_ops = self.safety_controls.get_operation_history(status=OperationStatus.PENDING)
        assert len(pending_ops) == 1
        assert pending_ops[0]['operation_id'] == 'op-2'
    
    def test_safety_metrics_calculation(self):
        """Test safety metrics calculation."""
        # Add some test operations
        self.safety_controls.operation_history = [
            {
                'operation_type': OperationType.STOP_INSTANCE.value,
                'risk_level': RiskLevel.LOW.value,
                'status': OperationStatus.SIMULATED.value,
                'rollback_capability': RollbackCapability.FULL.value
            },
            {
                'operation_type': OperationType.TERMINATE_INSTANCE.value,
                'risk_level': RiskLevel.HIGH.value,
                'status': OperationStatus.EXECUTED.value,
                'rollback_capability': RollbackCapability.NONE.value
            }
        ]
        
        metrics = self.safety_controls.get_safety_metrics()
        
        assert metrics['total_operations'] == 2
        assert metrics['dry_run_mode'] is True
        assert metrics['status_distribution'][OperationStatus.SIMULATED.value] == 1
        assert metrics['status_distribution'][OperationStatus.EXECUTED.value] == 1
        assert metrics['risk_distribution'][RiskLevel.LOW.value] == 1
        assert metrics['risk_distribution'][RiskLevel.HIGH.value] == 1
        assert metrics['rollback_capability_distribution'][RollbackCapability.FULL.value] == 1
        assert metrics['rollback_capability_distribution'][RollbackCapability.NONE.value] == 1
    
    def test_audit_log_export(self):
        """Test audit log export functionality."""
        # Add a test operation
        self.safety_controls.operation_history = [
            {
                'operation_id': 'op-audit-test',
                'operation_type': OperationType.STOP_INSTANCE.value,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # Export audit log
        output_file = self.safety_controls.export_audit_log()
        
        assert os.path.exists(output_file)
        
        # Verify content
        with open(output_file, 'r') as f:
            audit_data = json.load(f)
        
        assert 'export_timestamp' in audit_data
        assert 'safety_controls_config' in audit_data
        assert 'operation_history' in audit_data
        assert len(audit_data['operation_history']) == 1
        
        # Clean up
        os.unlink(output_file)
    
    def test_approval_workflow(self):
        """Test operation approval workflow."""
        # Add a pending operation
        self.safety_controls.operation_history = [
            {
                'operation_id': 'op-approval-test',
                'status': OperationStatus.PENDING.value,
                'approval_required': True
            }
        ]
        
        # Test getting operations requiring approval
        pending_ops = self.safety_controls.get_operations_requiring_approval()
        assert len(pending_ops) == 1
        assert pending_ops[0]['operation_id'] == 'op-approval-test'
        
        # Test approving operation
        result = self.safety_controls.approve_operation('op-approval-test', 'test-approver')
        assert result['success'] is True
        assert result['approver'] == 'test-approver'
        
        # Verify operation was updated
        updated_op = self.safety_controls.operation_history[0]
        assert updated_op['approved_by'] == 'test-approver'
        assert updated_op['status'] == 'APPROVED'


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_safety_controls_factory(self):
        """Test safety controls factory function."""
        safety = create_safety_controls(dry_run=True, log_file='test.log')
        assert isinstance(safety, SafetyControls)
        assert safety.dry_run is True
        assert safety.log_file == 'test.log'
    
    @patch.dict(os.environ, {'DRY_RUN': 'true'})
    def test_validate_dry_run_mode_true(self):
        """Test DRY_RUN validation when set to true."""
        assert validate_dry_run_mode() is True
    
    @patch.dict(os.environ, {'DRY_RUN': 'false'})
    def test_validate_dry_run_mode_false(self):
        """Test DRY_RUN validation when set to false."""
        assert validate_dry_run_mode() is False
    
    @patch.dict(os.environ, {'DRY_RUN': 'invalid'})
    def test_validate_dry_run_mode_invalid(self):
        """Test DRY_RUN validation with invalid value."""
        assert validate_dry_run_mode() is True  # Should default to True
    
    def test_setup_comprehensive_logging(self):
        """Test comprehensive logging setup."""
        # This test mainly ensures the function runs without error
        setup_comprehensive_logging('DEBUG')
        # Could add more specific logging tests if needed


if __name__ == '__main__':
    pytest.main([__file__, '-v'])