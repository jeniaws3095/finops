#!/usr/bin/env python3
"""
Property-based tests for safety_controls.py

**Property 23: Automated Low-Risk Execution**
**Validates: Requirements 8.2, 8.4**

Tests that low-risk optimizations are executed automatically while maintaining 
rollback capabilities, and that DRY_RUN mode prevents actual resource modifications.
"""

import pytest
import tempfile
import os
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime
from unittest.mock import patch, MagicMock

from utils.safety_controls import (
    SafetyControls, 
    OperationType, 
    RiskLevel, 
    OperationStatus,
    RollbackCapability,
    validate_dry_run_mode
)


# Hypothesis strategies for generating test data
@st.composite
def resource_data_strategy(draw):
    """Generate realistic resource data for testing."""
    instance_types = ['t3.micro', 't3.small', 't3.medium', 'm5.large', 'c5.xlarge']
    environments = ['development', 'staging', 'production', 'test']
    
    return {
        'resource_id': draw(st.text(min_size=10, max_size=20, alphabet='abcdef0123456789')),
        'instance_type': draw(st.sampled_from(instance_types)),
        'tags': {
            'Environment': draw(st.sampled_from(environments)),
            'Project': draw(st.text(min_size=3, max_size=10))
        },
        'monthly_cost': draw(st.floats(min_value=1.0, max_value=1000.0)),
        'encrypted': draw(st.booleans()),
        'region': draw(st.sampled_from(['us-east-1', 'us-west-2', 'eu-west-1']))
    }


@st.composite
def low_risk_operation_strategy(draw):
    """Generate low-risk operations for testing automated execution."""
    low_risk_ops = [
        OperationType.STOP_INSTANCE,
        OperationType.START_INSTANCE,
        OperationType.MODIFY_S3_LIFECYCLE,
        OperationType.MODIFY_CLOUDWATCH_LOGS
    ]
    
    return draw(st.sampled_from(low_risk_ops))


@st.composite
def high_risk_operation_strategy(draw):
    """Generate high-risk operations that should require approval."""
    high_risk_ops = [
        OperationType.TERMINATE_INSTANCE,
        OperationType.DELETE_VOLUME,
        OperationType.DELETE_RDS_INSTANCE,
        OperationType.DELETE_S3_BUCKET
    ]
    
    return draw(st.sampled_from(high_risk_ops))


class TestSafetyControlsProperties:
    """Property-based tests for SafetyControls."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_log = tempfile.NamedTemporaryFile(delete=False, suffix='.log')
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_log.name):
            os.unlink(self.temp_log.name)
    
    @given(resource_data=resource_data_strategy())
    @settings(max_examples=50)
    def test_property_dry_run_never_modifies_resources(self, resource_data):
        """
        **Property 23a: DRY_RUN Validation**
        **Feature: advanced-finops-platform, Property 23: Automated Low-Risk Execution**
        **Validates: Requirements 8.2, 8.4**
        
        For any operation in DRY_RUN mode, the system should never modify actual AWS resources
        and should always return simulation results.
        """
        safety_controls = SafetyControls(dry_run=True, log_file=self.temp_log.name)
        
        # Mock operation function that would modify resources
        mock_operation = MagicMock(return_value={'success': True, 'modified': True})
        
        # Test with any operation type
        for operation_type in OperationType:
            result = safety_controls.validate_operation(
                operation_type=operation_type,
                resource_id=resource_data['resource_id'],
                resource_data=resource_data,
                operation_func=mock_operation
            )
            
            # In DRY_RUN mode, the actual operation function should never be called
            assert not mock_operation.called, f"Operation function was called in DRY_RUN mode for {operation_type}"
            
            # Result should always indicate simulation
            assert result.get('simulated') is True, f"Result should be simulated for {operation_type}"
            assert result.get('success') is True, f"Simulation should succeed for {operation_type}"
            
            # Operation should be recorded as simulated
            op_record = safety_controls.operation_history[-1]
            assert op_record['status'] == OperationStatus.SIMULATED.value
            assert op_record['dry_run'] is True
            
            # Reset mock for next iteration
            mock_operation.reset_mock()
    
    @given(
        resource_data=resource_data_strategy(),
        operation_type=low_risk_operation_strategy()
    )
    @settings(max_examples=30)
    def test_property_low_risk_automatic_execution(self, resource_data, operation_type):
        """
        **Property 23b: Low-Risk Automatic Execution**
        **Feature: advanced-finops-platform, Property 23: Automated Low-Risk Execution**
        **Validates: Requirements 8.2, 8.4**
        
        For any low-risk operation, the system should execute automatically without requiring approval,
        while maintaining rollback capabilities.
        """
        # Ensure we're testing with a resource that will be assessed as low risk
        # Modify resource data to ensure low risk assessment
        safe_resource_data = resource_data.copy()
        safe_resource_data['tags'] = {'Environment': 'development', 'Project': 'test'}
        
        safety_controls = SafetyControls(dry_run=False, log_file=self.temp_log.name)
        
        # Mock successful operation
        mock_operation = MagicMock(return_value={'success': True, 'executed': True})
        
        # Assess risk to ensure it's actually low risk for this test
        risk_level = safety_controls.assess_risk(operation_type, safe_resource_data)
        
        # Only test if the operation is actually assessed as low or medium risk
        # (since we allow automatic execution for both LOW and MEDIUM risk)
        assume(risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM])
        
        result = safety_controls.validate_operation(
            operation_type=operation_type,
            resource_id=safe_resource_data['resource_id'],
            resource_data=safe_resource_data,
            operation_func=mock_operation
        )
        
        # Low-risk operations should not require approval
        assert not result.get('requires_approval', False), f"Low-risk {operation_type} should not require approval"
        
        # Operation should be executed (not just simulated)
        if not safety_controls.dry_run:
            assert mock_operation.called, f"Low-risk {operation_type} should be executed automatically"
        
        # Operation should be recorded
        op_record = safety_controls.operation_history[-1]
        assert op_record['operation_type'] == operation_type.value
        assert op_record['risk_level'] in [RiskLevel.LOW.value, RiskLevel.MEDIUM.value]
    
    @given(
        resource_data=resource_data_strategy(),
        operation_type=high_risk_operation_strategy()
    )
    @settings(max_examples=30)
    def test_property_high_risk_requires_approval(self, resource_data, operation_type):
        """
        **Property 23c: High-Risk Approval Requirement**
        **Feature: advanced-finops-platform, Property 23: Automated Low-Risk Execution**
        **Validates: Requirements 8.2, 8.4**
        
        For any high-risk operation, the system should require approval and not execute automatically.
        """
        # Ensure we're testing with a resource that will be assessed as high risk
        # Add production tags to increase risk
        high_risk_resource_data = resource_data.copy()
        high_risk_resource_data['tags'] = {'Environment': 'production', 'Critical': 'true'}
        high_risk_resource_data['instance_type'] = 'm5.2xlarge'  # Large instance type
        
        safety_controls = SafetyControls(dry_run=False, log_file=self.temp_log.name)
        
        # Mock operation that should not be called
        mock_operation = MagicMock(return_value={'success': True, 'executed': True})
        
        # Assess risk to ensure it's actually high risk for this test
        risk_level = safety_controls.assess_risk(operation_type, high_risk_resource_data)
        
        # Only test if the operation is actually assessed as high or critical risk
        assume(risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL])
        
        result = safety_controls.validate_operation(
            operation_type=operation_type,
            resource_id=high_risk_resource_data['resource_id'],
            resource_data=high_risk_resource_data,
            operation_func=mock_operation
        )
        
        # High-risk operations should require approval
        assert result.get('requires_approval', False) is True, f"High-risk {operation_type} should require approval"
        assert result.get('success', True) is False, f"High-risk {operation_type} should not succeed without approval"
        
        # Operation function should not be called without approval
        assert not mock_operation.called, f"High-risk {operation_type} should not be executed without approval"
        
        # Operation should be recorded as pending
        op_record = safety_controls.operation_history[-1]
        assert op_record['operation_type'] == operation_type.value
        assert op_record['risk_level'] in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]
        assert op_record.get('approval_required', False) is True
    
    @given(resource_data=resource_data_strategy())
    @settings(max_examples=30)
    def test_property_rollback_capability_consistency(self, resource_data):
        """
        **Property 23d: Rollback Capability Consistency**
        **Feature: advanced-finops-platform, Property 23: Automated Low-Risk Execution**
        **Validates: Requirements 8.2, 8.4**
        
        For any operation, the rollback capability assessment should be consistent
        and rollback plans should be created when capabilities exist.
        """
        safety_controls = SafetyControls(dry_run=True, log_file=self.temp_log.name)
        
        for operation_type in OperationType:
            # Get rollback capability
            rollback_capability = safety_controls.get_rollback_capability(operation_type)
            
            # Rollback capability should be one of the defined values
            assert rollback_capability in [RollbackCapability.FULL, RollbackCapability.PARTIAL, RollbackCapability.NONE]
            
            # Test rollback plan creation for operations with rollback capability
            if rollback_capability != RollbackCapability.NONE:
                operation_record = {
                    'operation_id': f'test-{operation_type.value}',
                    'operation_type': operation_type.value,
                    'resource_id': resource_data['resource_id'],
                    'resource_data': resource_data
                }
                
                rollback_plan = safety_controls._create_detailed_rollback_plan(operation_record)
                
                # Rollback plan should be created
                assert rollback_plan is not None
                assert 'rollback_id' in rollback_plan
                assert 'steps' in rollback_plan
                assert rollback_plan['rollback_capability'] == rollback_capability.value
                
                # If capability is FULL, there should be rollback steps
                if rollback_capability == RollbackCapability.FULL:
                    assert len(rollback_plan['steps']) > 0, f"FULL rollback capability should have steps for {operation_type}"
    
    @given(
        operations_count=st.integers(min_value=1, max_value=10),
        resource_data=resource_data_strategy()
    )
    @settings(max_examples=20)
    def test_property_operation_history_integrity(self, operations_count, resource_data):
        """
        **Property 23e: Operation History Integrity**
        **Feature: advanced-finops-platform, Property 23: Automated Low-Risk Execution**
        **Validates: Requirements 8.2, 8.4**
        
        For any sequence of operations, the operation history should maintain integrity
        and provide accurate tracking of all operations performed.
        """
        safety_controls = SafetyControls(dry_run=True, log_file=self.temp_log.name)
        
        # Mock operation function
        mock_operation = MagicMock(return_value={'success': True})
        
        # Perform multiple operations
        operation_types = list(OperationType)
        for i in range(operations_count):
            operation_type = operation_types[i % len(operation_types)]
            
            safety_controls.validate_operation(
                operation_type=operation_type,
                resource_id=f"{resource_data['resource_id']}-{i}",
                resource_data=resource_data,
                operation_func=mock_operation
            )
        
        # Verify operation history integrity
        history = safety_controls.get_operation_history()
        
        # Should have recorded all operations
        assert len(history) == operations_count, "All operations should be recorded in history"
        
        # Each operation should have required fields
        for i, op_record in enumerate(history):
            assert 'operation_id' in op_record, f"Operation {i} should have operation_id"
            assert 'timestamp' in op_record, f"Operation {i} should have timestamp"
            assert 'operation_type' in op_record, f"Operation {i} should have operation_type"
            assert 'resource_id' in op_record, f"Operation {i} should have resource_id"
            assert 'risk_level' in op_record, f"Operation {i} should have risk_level"
            assert 'status' in op_record, f"Operation {i} should have status"
            assert 'dry_run' in op_record, f"Operation {i} should have dry_run flag"
            
            # In DRY_RUN mode, all should be simulated
            assert op_record['status'] == OperationStatus.SIMULATED.value
            assert op_record['dry_run'] is True
    
    @given(st.booleans())
    @settings(max_examples=10)
    def test_property_dry_run_environment_validation(self, env_dry_run_value):
        """
        **Property 23f: DRY_RUN Environment Validation**
        **Feature: advanced-finops-platform, Property 23: Automated Low-Risk Execution**
        **Validates: Requirements 8.2, 8.4**
        
        For any DRY_RUN environment configuration, the validation should work correctly
        and default to safe mode when invalid.
        """
        env_value = 'true' if env_dry_run_value else 'false'
        
        with patch.dict(os.environ, {'DRY_RUN': env_value}):
            result = validate_dry_run_mode()
            
            # Should return the correct boolean value
            assert result == env_dry_run_value, f"DRY_RUN validation should return {env_dry_run_value} for '{env_value}'"
        
        # Test with invalid value - should default to True (safe mode)
        with patch.dict(os.environ, {'DRY_RUN': 'invalid_value'}):
            result = validate_dry_run_mode()
            assert result is True, "Invalid DRY_RUN value should default to True (safe mode)"
    
    @given(resource_data=resource_data_strategy())
    @settings(max_examples=20)
    def test_property_comprehensive_logging(self, resource_data):
        """
        **Property 23g: Comprehensive Logging**
        **Feature: advanced-finops-platform, Property 23: Automated Low-Risk Execution**
        **Validates: Requirements 8.2, 8.4**
        
        For any operation, comprehensive logging should be maintained with all required details.
        """
        safety_controls = SafetyControls(dry_run=True, log_file=self.temp_log.name)
        
        # Mock operation function
        mock_operation = MagicMock(return_value={'success': True})
        
        # Perform operation
        operation_type = OperationType.STOP_INSTANCE
        safety_controls.validate_operation(
            operation_type=operation_type,
            resource_id=resource_data['resource_id'],
            resource_data=resource_data,
            operation_func=mock_operation
        )
        
        # Verify log file exists and has content
        assert os.path.exists(self.temp_log.name), "Log file should exist"
        
        # Verify operation was logged
        with open(self.temp_log.name, 'r') as f:
            log_content = f.read()
        
        # Log should contain operation details
        assert resource_data['resource_id'] in log_content, "Log should contain resource ID"
        assert operation_type.value in log_content, "Log should contain operation type"
        assert 'Safety controls initialized' in log_content, "Log should contain initialization message"
        
        # Verify safety metrics are available
        metrics = safety_controls.get_safety_metrics()
        assert metrics['total_operations'] > 0, "Safety metrics should track operations"
        assert metrics['dry_run_mode'] is True, "Safety metrics should reflect DRY_RUN mode"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])