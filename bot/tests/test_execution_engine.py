#!/usr/bin/env python3
"""
Unit Tests for Optimization Execution Engine

Tests the comprehensive optimization execution engine including:
- Automatic execution for low-risk optimizations
- Rollback capabilities and safety validation
- Result validation and savings calculation
- Performance monitoring and batch processing
- Execution scheduling capabilities
"""

import unittest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import the execution engine
from core.execution_engine import (
    OptimizationExecutionEngine,
    ExecutionStatus,
    ExecutionPriority,
    BatchProcessingMode,
    ExecutionResult,
    create_execution_engine,
    execute_single_optimization
)


class TestOptimizationExecutionEngine(unittest.TestCase):
    """Test cases for OptimizationExecutionEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = OptimizationExecutionEngine(dry_run=True)
        
        self.sample_optimization = {
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
        
        self.low_risk_optimization = {
            'optimizationId': 'opt-low-risk',
            'resourceId': 'i-lowrisk123',
            'resourceType': 'ec2',
            'optimizationType': 'pricing',
            'currentCost': 50.0,
            'estimatedSavings': 10.0,  # Low savings for auto-approval
            'resourceData': {
                'instanceType': 't3.micro',
                'region': 'us-east-1',
                'tags': {'Environment': 'development'},
                'state': 'running'
            }
        }
    
    def test_engine_initialization(self):
        """Test execution engine initialization."""
        self.assertTrue(self.engine.dry_run)
        self.assertEqual(self.engine.max_concurrent_executions, 5)
        self.assertEqual(self.engine.execution_timeout_minutes, 30)
        self.assertIsNotNone(self.engine.approval_workflow)
        self.assertIsNotNone(self.engine.safety_controls)
        self.assertEqual(len(self.engine.active_executions), 0)
        self.assertEqual(len(self.engine.completed_executions), 0)
    
    def test_execute_optimization_dry_run(self):
        """Test optimization execution in DRY_RUN mode."""
        result = self.engine.execute_optimization(self.sample_optimization)
        
        # Verify execution completed
        self.assertIsInstance(result, dict)
        self.assertIn('execution_id', result)
        self.assertIn('status', result)
        self.assertEqual(result['resource_id'], 'i-1234567890abcdef0')
        
        # Verify execution was recorded
        self.assertEqual(len(self.engine.completed_executions), 1)
        self.assertEqual(len(self.engine.execution_history), 1)
    
    def test_low_risk_auto_approval(self):
        """Test automatic approval for low-risk optimizations."""
        result = self.engine.execute_optimization(self.low_risk_optimization)
        
        # Should complete successfully due to auto-approval
        self.assertEqual(result['status'], ExecutionStatus.COMPLETED.value)
        self.assertIn('actual_savings', result)
        self.assertIsNotNone(result['actual_savings'])
    
    def test_pre_execution_validation(self):
        """Test pre-execution validation checks."""
        validation_result = self.engine._validate_pre_execution(self.sample_optimization)
        
        self.assertIsInstance(validation_result, dict)
        self.assertIn('valid', validation_result)
        self.assertIn('checks', validation_result)
        self.assertIn('warnings', validation_result)
        self.assertIn('errors', validation_result)
        
        # Should pass validation for valid optimization
        self.assertTrue(validation_result['valid'])
    
    def test_conflicting_operations_check(self):
        """Test detection of conflicting operations."""
        # Start first execution
        self.engine.execute_optimization(self.sample_optimization)
        
        # Try to execute same resource again (should detect conflict)
        conflict_check = self.engine._check_conflicting_operations('i-1234567890abcdef0')
        
        # Should detect no conflict since first execution completed
        self.assertTrue(conflict_check['passed'])
    
    def test_rollback_plan_creation(self):
        """Test rollback plan creation for different optimization types."""
        # Test rightsizing rollback plan
        rollback_plan = self.engine._create_execution_rollback_plan(self.sample_optimization)
        
        self.assertIsInstance(rollback_plan, dict)
        self.assertIn('rollback_plan_id', rollback_plan)
        self.assertIn('rollback_steps', rollback_plan)
        self.assertIn('estimated_rollback_time_minutes', rollback_plan)
        
        # Verify rollback plan was stored
        plan_id = rollback_plan['rollback_plan_id']
        self.assertIn(plan_id, self.engine.safety_controls.rollback_plans)
    
    def test_savings_accuracy_calculation(self):
        """Test savings accuracy calculation."""
        # Test exact match
        accuracy = self.engine._calculate_savings_accuracy(100.0, 100.0)
        self.assertEqual(accuracy, 100.0)
        
        # Test 90% accuracy
        accuracy = self.engine._calculate_savings_accuracy(100.0, 90.0)
        self.assertEqual(accuracy, 90.0)
        
        # Test over-estimate
        accuracy = self.engine._calculate_savings_accuracy(100.0, 110.0)
        self.assertEqual(accuracy, 110.0)
        
        # Test None handling
        accuracy = self.engine._calculate_savings_accuracy(100.0, None)
        self.assertIsNone(accuracy)
    
    def test_batch_execution_sequential(self):
        """Test sequential batch execution."""
        optimizations = [
            self.sample_optimization.copy(),
            self.low_risk_optimization.copy()
        ]
        
        # Modify IDs to avoid conflicts
        optimizations[0]['resourceId'] = 'i-batch1'
        optimizations[1]['resourceId'] = 'i-batch2'
        
        batch_result = self.engine.execute_batch_optimizations(
            optimizations, 
            BatchProcessingMode.SEQUENTIAL
        )
        
        self.assertIsInstance(batch_result, dict)
        self.assertIn('batch_id', batch_result)
        self.assertEqual(batch_result['total_optimizations'], 2)
        self.assertEqual(len(batch_result['execution_results']), 2)
        self.assertIn('summary', batch_result)
    
    def test_batch_execution_parallel(self):
        """Test parallel batch execution."""
        optimizations = [
            self.sample_optimization.copy(),
            self.low_risk_optimization.copy()
        ]
        
        # Modify IDs to avoid conflicts
        optimizations[0]['resourceId'] = 'i-parallel1'
        optimizations[1]['resourceId'] = 'i-parallel2'
        
        batch_result = self.engine.execute_batch_optimizations(
            optimizations, 
            BatchProcessingMode.PARALLEL,
            max_parallel=2
        )
        
        self.assertIsInstance(batch_result, dict)
        self.assertEqual(batch_result['total_optimizations'], 2)
        self.assertEqual(len(batch_result['execution_results']), 2)
    
    def test_optimization_scheduling(self):
        """Test optimization scheduling functionality."""
        future_time = datetime.utcnow() + timedelta(hours=1)
        
        schedule_result = self.engine.schedule_optimization(
            self.sample_optimization,
            future_time,
            ExecutionPriority.HIGH
        )
        
        self.assertTrue(schedule_result['success'])
        self.assertIn('schedule_id', schedule_result)
        self.assertEqual(len(self.engine.execution_queue), 1)
        
        # Verify scheduled item
        scheduled_item = self.engine.execution_queue[0]
        self.assertEqual(scheduled_item['priority'], ExecutionPriority.HIGH.value)
        self.assertEqual(scheduled_item['resource_id'], 'i-1234567890abcdef0')
    
    def test_scheduled_optimization_processing(self):
        """Test processing of scheduled optimizations."""
        # Schedule optimization for immediate execution
        past_time = datetime.utcnow() - timedelta(minutes=1)
        
        self.engine.schedule_optimization(
            self.sample_optimization,
            past_time,
            ExecutionPriority.MEDIUM
        )
        
        # Process scheduled optimizations
        process_result = self.engine.process_scheduled_optimizations()
        
        self.assertEqual(process_result['processed_count'], 1)
        self.assertEqual(process_result['successful_executions'], 1)
        self.assertEqual(len(self.engine.execution_queue), 0)  # Should be empty after processing
    
    def test_schedule_cancellation(self):
        """Test cancellation of scheduled optimizations."""
        future_time = datetime.utcnow() + timedelta(hours=2)
        
        schedule_result = self.engine.schedule_optimization(
            self.sample_optimization,
            future_time
        )
        
        schedule_id = schedule_result['schedule_id']
        
        # Cancel the scheduled optimization
        cancel_result = self.engine.cancel_scheduled_optimization(schedule_id)
        
        self.assertTrue(cancel_result['success'])
        self.assertEqual(cancel_result['schedule_id'], schedule_id)
        self.assertEqual(len(self.engine.execution_queue), 0)
    
    def test_execution_status_retrieval(self):
        """Test retrieval of execution status."""
        result = self.engine.execute_optimization(self.sample_optimization)
        execution_id = result['execution_id']
        
        # Get execution status
        status_result = self.engine.get_execution_status(execution_id)
        
        self.assertTrue(status_result['success'])
        self.assertIn('execution', status_result)
        self.assertFalse(status_result['is_active'])  # Should be completed
        
        # Test non-existent execution
        invalid_status = self.engine.get_execution_status('invalid-id')
        self.assertFalse(invalid_status['success'])
    
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        # Execute some optimizations
        self.engine.execute_optimization(self.sample_optimization)
        self.engine.execute_optimization(self.low_risk_optimization)
        
        metrics = self.engine.get_performance_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('execution_metrics', metrics)
        self.assertIn('success_rate_percentage', metrics)
        self.assertIn('average_savings_per_execution', metrics)
        self.assertIn('queue_status', metrics)
        
        # Verify metrics values
        exec_metrics = metrics['execution_metrics']
        self.assertEqual(exec_metrics['total_executions'], 2)
        self.assertEqual(exec_metrics['successful_executions'], 2)
        self.assertEqual(exec_metrics['failed_executions'], 0)
    
    def test_execution_history_filtering(self):
        """Test execution history filtering."""
        # Execute optimizations with different outcomes
        self.engine.execute_optimization(self.sample_optimization)
        self.engine.execute_optimization(self.low_risk_optimization)
        
        # Get all history
        all_history = self.engine.get_execution_history()
        self.assertEqual(len(all_history), 2)
        
        # Filter by status
        completed_history = self.engine.get_execution_history(
            status_filter=ExecutionStatus.COMPLETED
        )
        self.assertEqual(len(completed_history), 2)
        
        # Filter by resource
        resource_history = self.engine.get_execution_history(
            resource_filter='i-1234567890abcdef0'
        )
        self.assertEqual(len(resource_history), 1)
    
    def test_cleanup_completed_executions(self):
        """Test cleanup of old completed executions."""
        # Execute some optimizations
        self.engine.execute_optimization(self.sample_optimization)
        self.engine.execute_optimization(self.low_risk_optimization)
        
        # Verify executions exist
        self.assertEqual(len(self.engine.completed_executions), 2)
        self.assertEqual(len(self.engine.execution_history), 2)
        
        # Cleanup with very short retention (should clean up everything)
        cleanup_result = self.engine.cleanup_completed_executions(retention_days=0)
        
        self.assertEqual(cleanup_result['cleaned_up_count'], 2)
        self.assertEqual(len(self.engine.completed_executions), 0)
        self.assertEqual(len(self.engine.execution_history), 0)
    
    def test_resource_grouping(self):
        """Test grouping optimizations by resource type."""
        optimizations = [
            {'resourceType': 'ec2', 'resourceId': 'i-1'},
            {'resourceType': 'rds', 'resourceId': 'db-1'},
            {'resourceType': 'ec2', 'resourceId': 'i-2'},
            {'resourceType': 's3', 'resourceId': 'bucket-1'}
        ]
        
        grouped = self.engine._group_optimizations_by_resource_type(optimizations)
        
        self.assertEqual(len(grouped), 3)  # ec2, rds, s3
        self.assertEqual(len(grouped['ec2']), 2)
        self.assertEqual(len(grouped['rds']), 1)
        self.assertEqual(len(grouped['s3']), 1)
    
    def test_region_grouping(self):
        """Test grouping optimizations by AWS region."""
        optimizations = [
            {'resourceData': {'region': 'us-east-1'}, 'resourceId': 'r-1'},
            {'resourceData': {'region': 'us-west-2'}, 'resourceId': 'r-2'},
            {'resourceData': {'region': 'us-east-1'}, 'resourceId': 'r-3'},
        ]
        
        grouped = self.engine._group_optimizations_by_region(optimizations)
        
        self.assertEqual(len(grouped), 2)  # us-east-1, us-west-2
        self.assertEqual(len(grouped['us-east-1']), 2)
        self.assertEqual(len(grouped['us-west-2']), 1)
    
    def test_factory_function(self):
        """Test factory function for creating execution engine."""
        engine = create_execution_engine(
            dry_run=False,
            max_concurrent=10,
            timeout_minutes=60
        )
        
        self.assertFalse(engine.dry_run)
        self.assertEqual(engine.max_concurrent_executions, 10)
        self.assertEqual(engine.execution_timeout_minutes, 60)
    
    def test_utility_function(self):
        """Test utility function for single optimization execution."""
        result = execute_single_optimization(self.sample_optimization, dry_run=True)
        
        self.assertIsInstance(result, dict)
        self.assertIn('execution_id', result)
        self.assertIn('status', result)


class TestExecutionResult(unittest.TestCase):
    """Test cases for ExecutionResult dataclass."""
    
    def test_execution_result_creation(self):
        """Test ExecutionResult creation and serialization."""
        result = ExecutionResult(
            execution_id='exec-123',
            optimization_id='opt-123',
            resource_id='i-123',
            status=ExecutionStatus.COMPLETED,
            started_at='2024-01-01T00:00:00Z',
            completed_at='2024-01-01T00:05:00Z',
            execution_time_seconds=300.0,
            actual_savings=25.0,
            estimated_savings=30.0,
            savings_accuracy=83.33,
            performance_impact={'cpu': 'minimal'},
            rollback_plan_id='rb-123',
            error_message=None,
            validation_results={'valid': True}
        )
        
        # Test to_dict conversion
        result_dict = result.to_dict()
        
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['execution_id'], 'exec-123')
        self.assertEqual(result_dict['status'], ExecutionStatus.COMPLETED.value)
        self.assertEqual(result_dict['actual_savings'], 25.0)
        self.assertEqual(result_dict['savings_accuracy'], 83.33)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)