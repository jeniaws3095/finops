#!/usr/bin/env python3
"""
Workflow State Management for Advanced FinOps Platform

This module provides workflow state persistence and resume capabilities,
allowing long-running optimization workflows to be interrupted and resumed
without losing progress.

Features:
- Workflow state persistence to disk
- Resume capability from saved state
- Progress tracking and checkpoints
- Error recovery and rollback
- State validation and integrity checks
"""

import json
import os
import pickle
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import logging
from pathlib import Path


class WorkflowPhase(Enum):
    """Workflow execution phases."""
    INITIALIZATION = "initialization"
    DISCOVERY = "discovery"
    OPTIMIZATION_ANALYSIS = "optimization_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    BUDGET_MANAGEMENT = "budget_management"
    EXECUTION = "execution"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(Enum):
    """Workflow execution status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStateManager:
    """
    Manages workflow state persistence and resume capabilities.
    
    This class handles:
    - Saving workflow state at checkpoints
    - Loading and resuming from saved state
    - Progress tracking and reporting
    - Error recovery and rollback
    """
    
    def __init__(self, workflow_id: str, state_dir: str = "workflow_states"):
        """
        Initialize workflow state manager.
        
        Args:
            workflow_id: Unique identifier for this workflow execution
            state_dir: Directory to store workflow state files
        """
        self.workflow_id = workflow_id
        self.state_dir = Path(state_dir)
        self.state_file = self.state_dir / f"{workflow_id}.json"
        self.checkpoint_dir = self.state_dir / workflow_id / "checkpoints"
        self.logger = logging.getLogger(__name__)
        
        # Create directories if they don't exist
        self.state_dir.mkdir(exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize workflow state
        self.state = {
            'workflow_id': workflow_id,
            'status': WorkflowStatus.NOT_STARTED.value,
            'current_phase': None,
            'phases_completed': [],
            'phases_failed': [],
            'start_time': None,
            'end_time': None,
            'last_checkpoint': None,
            'configuration': {},
            'results': {},
            'errors': [],
            'metrics': {
                'total_resources_discovered': 0,
                'total_optimizations_found': 0,
                'total_savings_potential': 0.0,
                'execution_time_seconds': 0.0
            }
        }
        
        # Load existing state if available
        self._load_state()
        
        self.logger.info(f"Workflow state manager initialized for workflow {workflow_id}")
    
    def _load_state(self) -> None:
        """Load workflow state from disk if it exists."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    saved_state = json.load(f)
                    self.state.update(saved_state)
                self.logger.info(f"Loaded existing workflow state from {self.state_file}")
            else:
                self.logger.info("No existing workflow state found, starting fresh")
        except Exception as e:
            self.logger.error(f"Failed to load workflow state: {e}")
            # Continue with fresh state
    
    def _save_state(self) -> None:
        """Save current workflow state to disk."""
        try:
            # Update timestamp
            self.state['last_updated'] = datetime.now(timezone.utc).isoformat()
            
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
            
            self.logger.debug(f"Saved workflow state to {self.state_file}")
        except Exception as e:
            self.logger.error(f"Failed to save workflow state: {e}")
    
    def start_workflow(self, configuration: Dict[str, Any]) -> None:
        """
        Start a new workflow execution.
        
        Args:
            configuration: Workflow configuration parameters
        """
        self.state['status'] = WorkflowStatus.IN_PROGRESS.value
        self.state['start_time'] = datetime.now(timezone.utc).isoformat()
        self.state['configuration'] = configuration
        self.state['phases_completed'] = []
        self.state['phases_failed'] = []
        self.state['errors'] = []
        
        self._save_state()
        self.logger.info(f"Started workflow {self.workflow_id}")
    
    def start_phase(self, phase: WorkflowPhase) -> None:
        """
        Start a workflow phase.
        
        Args:
            phase: The workflow phase being started
        """
        self.state['current_phase'] = phase.value
        self.state['phase_start_time'] = datetime.now(timezone.utc).isoformat()
        
        self._save_state()
        self.logger.info(f"Started phase: {phase.value}")
    
    def complete_phase(self, phase: WorkflowPhase, results: Dict[str, Any]) -> None:
        """
        Complete a workflow phase.
        
        Args:
            phase: The workflow phase being completed
            results: Results from the phase execution
        """
        if phase.value not in self.state['phases_completed']:
            self.state['phases_completed'].append(phase.value)
        
        # Remove from failed phases if it was there
        if phase.value in self.state['phases_failed']:
            self.state['phases_failed'].remove(phase.value)
        
        # Store phase results
        self.state['results'][phase.value] = results
        
        # Update metrics
        if phase == WorkflowPhase.DISCOVERY:
            self.state['metrics']['total_resources_discovered'] = results.get('resources_discovered', 0)
        elif phase == WorkflowPhase.OPTIMIZATION_ANALYSIS:
            self.state['metrics']['total_optimizations_found'] = results.get('optimizations_found', 0)
            self.state['metrics']['total_savings_potential'] = results.get('potential_monthly_savings', 0.0)
        
        self.state['current_phase'] = None
        self._save_state()
        self.logger.info(f"Completed phase: {phase.value}")
    
    def fail_phase(self, phase: WorkflowPhase, error: str) -> None:
        """
        Mark a workflow phase as failed.
        
        Args:
            phase: The workflow phase that failed
            error: Error message describing the failure
        """
        if phase.value not in self.state['phases_failed']:
            self.state['phases_failed'].append(phase.value)
        
        # Remove from completed phases if it was there
        if phase.value in self.state['phases_completed']:
            self.state['phases_completed'].remove(phase.value)
        
        # Store error
        error_entry = {
            'phase': phase.value,
            'error': error,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self.state['errors'].append(error_entry)
        
        self.state['current_phase'] = None
        self._save_state()
        self.logger.error(f"Failed phase {phase.value}: {error}")
    
    def create_checkpoint(self, checkpoint_name: str, data: Dict[str, Any]) -> None:
        """
        Create a checkpoint with intermediate data.
        
        Args:
            checkpoint_name: Name of the checkpoint
            data: Data to save at this checkpoint
        """
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.pkl"
        
        try:
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(data, f)
            
            self.state['last_checkpoint'] = checkpoint_name
            self.state['checkpoint_time'] = datetime.now(timezone.utc).isoformat()
            
            self._save_state()
            self.logger.info(f"Created checkpoint: {checkpoint_name}")
        except Exception as e:
            self.logger.error(f"Failed to create checkpoint {checkpoint_name}: {e}")
    
    def load_checkpoint(self, checkpoint_name: str) -> Optional[Dict[str, Any]]:
        """
        Load data from a checkpoint.
        
        Args:
            checkpoint_name: Name of the checkpoint to load
            
        Returns:
            Checkpoint data or None if not found
        """
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.pkl"
        
        try:
            if checkpoint_file.exists():
                with open(checkpoint_file, 'rb') as f:
                    data = pickle.load(f)
                self.logger.info(f"Loaded checkpoint: {checkpoint_name}")
                return data
            else:
                self.logger.warning(f"Checkpoint {checkpoint_name} not found")
                return None
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint {checkpoint_name}: {e}")
            return None
    
    def complete_workflow(self, success: bool = True) -> None:
        """
        Complete the workflow execution.
        
        Args:
            success: Whether the workflow completed successfully
        """
        self.state['status'] = WorkflowStatus.COMPLETED.value if success else WorkflowStatus.FAILED.value
        self.state['end_time'] = datetime.now(timezone.utc).isoformat()
        self.state['current_phase'] = None
        
        # Calculate total execution time
        if self.state['start_time']:
            start_time = datetime.fromisoformat(self.state['start_time'].replace('Z', '+00:00'))
            end_time = datetime.now(timezone.utc)
            self.state['metrics']['execution_time_seconds'] = (end_time - start_time).total_seconds()
        
        self._save_state()
        status_text = "successfully" if success else "with failures"
        self.logger.info(f"Workflow {self.workflow_id} completed {status_text}")
    
    def pause_workflow(self) -> None:
        """Pause the workflow execution."""
        self.state['status'] = WorkflowStatus.PAUSED.value
        self.state['pause_time'] = datetime.now(timezone.utc).isoformat()
        
        self._save_state()
        self.logger.info(f"Workflow {self.workflow_id} paused")
    
    def resume_workflow(self) -> None:
        """Resume the workflow execution."""
        self.state['status'] = WorkflowStatus.IN_PROGRESS.value
        self.state['resume_time'] = datetime.now(timezone.utc).isoformat()
        
        self._save_state()
        self.logger.info(f"Workflow {self.workflow_id} resumed")
    
    def cancel_workflow(self) -> None:
        """Cancel the workflow execution."""
        self.state['status'] = WorkflowStatus.CANCELLED.value
        self.state['cancel_time'] = datetime.now(timezone.utc).isoformat()
        self.state['current_phase'] = None
        
        self._save_state()
        self.logger.info(f"Workflow {self.workflow_id} cancelled")
    
    def get_status(self) -> WorkflowStatus:
        """Get current workflow status."""
        return WorkflowStatus(self.state['status'])
    
    def get_current_phase(self) -> Optional[WorkflowPhase]:
        """Get current workflow phase."""
        if self.state['current_phase']:
            return WorkflowPhase(self.state['current_phase'])
        return None
    
    def get_completed_phases(self) -> List[WorkflowPhase]:
        """Get list of completed phases."""
        return [WorkflowPhase(phase) for phase in self.state['phases_completed']]
    
    def get_failed_phases(self) -> List[WorkflowPhase]:
        """Get list of failed phases."""
        return [WorkflowPhase(phase) for phase in self.state['phases_failed']]
    
    def can_resume(self) -> bool:
        """Check if workflow can be resumed."""
        return self.state['status'] in [WorkflowStatus.PAUSED.value, WorkflowStatus.FAILED.value]
    
    def get_next_phase(self) -> Optional[WorkflowPhase]:
        """
        Get the next phase to execute based on completed phases.
        
        Returns:
            Next phase to execute or None if workflow is complete
        """
        all_phases = [
            WorkflowPhase.INITIALIZATION,
            WorkflowPhase.DISCOVERY,
            WorkflowPhase.OPTIMIZATION_ANALYSIS,
            WorkflowPhase.ANOMALY_DETECTION,
            WorkflowPhase.BUDGET_MANAGEMENT,
            WorkflowPhase.EXECUTION,
            WorkflowPhase.REPORTING
        ]
        
        completed = set(self.state['phases_completed'])
        
        for phase in all_phases:
            if phase.value not in completed:
                return phase
        
        return None  # All phases completed
    
    def get_progress_percentage(self) -> float:
        """
        Get workflow progress as a percentage.
        
        Returns:
            Progress percentage (0.0 to 100.0)
        """
        total_phases = 7  # Total number of phases
        completed_phases = len(self.state['phases_completed'])
        return (completed_phases / total_phases) * 100.0
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the workflow state.
        
        Returns:
            Dictionary containing workflow summary
        """
        return {
            'workflow_id': self.workflow_id,
            'status': self.state['status'],
            'current_phase': self.state['current_phase'],
            'progress_percentage': self.get_progress_percentage(),
            'phases_completed': len(self.state['phases_completed']),
            'phases_failed': len(self.state['phases_failed']),
            'total_errors': len(self.state['errors']),
            'start_time': self.state['start_time'],
            'end_time': self.state['end_time'],
            'execution_time_seconds': self.state['metrics']['execution_time_seconds'],
            'metrics': self.state['metrics']
        }
    
    def cleanup_old_states(self, days_to_keep: int = 30) -> None:
        """
        Clean up old workflow state files.
        
        Args:
            days_to_keep: Number of days to keep workflow states
        """
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            for state_file in self.state_dir.glob("*.json"):
                if state_file.stat().st_mtime < cutoff_time.timestamp():
                    state_file.unlink()
                    self.logger.info(f"Cleaned up old state file: {state_file}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup old states: {e}")
    
    def export_state(self, export_path: str) -> None:
        """
        Export workflow state to a file.
        
        Args:
            export_path: Path to export the state to
        """
        try:
            with open(export_path, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
            self.logger.info(f"Exported workflow state to {export_path}")
        except Exception as e:
            self.logger.error(f"Failed to export state: {e}")
            raise