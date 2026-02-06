#!/usr/bin/env python3
"""
Scheduler for Advanced FinOps Platform

This module provides scheduling capabilities for continuous monitoring,
daily optimizations, and periodic reporting.
"""

import time
import threading
import logging
import signal
import sys
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ScheduleType(Enum):
    """Types of scheduled operations."""
    CONTINUOUS = "continuous"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    task_id: str
    name: str
    schedule_type: ScheduleType
    interval_minutes: Optional[int] = None  # For continuous tasks
    time_of_day: Optional[str] = None  # For daily tasks (HH:MM format)
    day_of_week: Optional[str] = None  # For weekly tasks
    day_of_month: Optional[int] = None  # For monthly tasks
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    callback: Optional[Callable] = None
    callback_args: tuple = ()
    callback_kwargs: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.callback_kwargs is None:
            self.callback_kwargs = {}


class FinOpsScheduler:
    """
    Scheduler for FinOps platform operations.
    
    Supports:
    - Continuous monitoring at configurable intervals
    - Daily optimization runs at specific times
    - Weekly reporting
    - Custom scheduling patterns
    """
    
    def __init__(self):
        """Initialize the scheduler."""
        self.logger = logging.getLogger(__name__)
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down scheduler...")
        self.stop()
        sys.exit(0)
    
    def add_continuous_task(self, 
                           task_id: str,
                           name: str,
                           interval_minutes: int,
                           callback: Callable,
                           callback_args: tuple = (),
                           callback_kwargs: Dict[str, Any] = None,
                           enabled: bool = True) -> None:
        """
        Add a continuous monitoring task.
        
        Args:
            task_id: Unique identifier for the task
            name: Human-readable name
            interval_minutes: Interval between runs in minutes
            callback: Function to call
            callback_args: Arguments for callback
            callback_kwargs: Keyword arguments for callback
            enabled: Whether task is enabled
        """
        if callback_kwargs is None:
            callback_kwargs = {}
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=ScheduleType.CONTINUOUS,
            interval_minutes=interval_minutes,
            enabled=enabled,
            callback=callback,
            callback_args=callback_args,
            callback_kwargs=callback_kwargs
        )
        
        # Calculate next run time
        task.next_run = datetime.now(timezone.utc) + timedelta(minutes=interval_minutes)
        
        self.tasks[task_id] = task
        self.logger.info(f"Added continuous task: {name} (every {interval_minutes} minutes)")
    
    def add_daily_task(self,
                      task_id: str,
                      name: str,
                      time_of_day: str,
                      callback: Callable,
                      callback_args: tuple = (),
                      callback_kwargs: Dict[str, Any] = None,
                      enabled: bool = True) -> None:
        """
        Add a daily scheduled task.
        
        Args:
            task_id: Unique identifier for the task
            name: Human-readable name
            time_of_day: Time to run in HH:MM format (24-hour, UTC)
            callback: Function to call
            callback_args: Arguments for callback
            callback_kwargs: Keyword arguments for callback
            enabled: Whether task is enabled
        """
        if callback_kwargs is None:
            callback_kwargs = {}
        
        # Validate time format
        try:
            hour, minute = map(int, time_of_day.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time format")
        except ValueError:
            raise ValueError(f"Invalid time format: {time_of_day}. Use HH:MM format.")
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=ScheduleType.DAILY,
            time_of_day=time_of_day,
            enabled=enabled,
            callback=callback,
            callback_args=callback_args,
            callback_kwargs=callback_kwargs
        )
        
        # Calculate next run time
        task.next_run = self._calculate_next_daily_run(time_of_day)
        
        self.tasks[task_id] = task
        self.logger.info(f"Added daily task: {name} (at {time_of_day} UTC)")
    
    def add_weekly_task(self,
                       task_id: str,
                       name: str,
                       day_of_week: str,
                       time_of_day: str,
                       callback: Callable,
                       callback_args: tuple = (),
                       callback_kwargs: Dict[str, Any] = None,
                       enabled: bool = True) -> None:
        """
        Add a weekly scheduled task.
        
        Args:
            task_id: Unique identifier for the task
            name: Human-readable name
            day_of_week: Day of week (monday, tuesday, etc.)
            time_of_day: Time to run in HH:MM format (24-hour, UTC)
            callback: Function to call
            callback_args: Arguments for callback
            callback_kwargs: Keyword arguments for callback
            enabled: Whether task is enabled
        """
        if callback_kwargs is None:
            callback_kwargs = {}
        
        # Validate day of week
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if day_of_week.lower() not in valid_days:
            raise ValueError(f"Invalid day of week: {day_of_week}. Use: {', '.join(valid_days)}")
        
        # Validate time format
        try:
            hour, minute = map(int, time_of_day.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time format")
        except ValueError:
            raise ValueError(f"Invalid time format: {time_of_day}. Use HH:MM format.")
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=ScheduleType.WEEKLY,
            day_of_week=day_of_week.lower(),
            time_of_day=time_of_day,
            enabled=enabled,
            callback=callback,
            callback_args=callback_args,
            callback_kwargs=callback_kwargs
        )
        
        # Calculate next run time
        task.next_run = self._calculate_next_weekly_run(day_of_week.lower(), time_of_day)
        
        self.tasks[task_id] = task
        self.logger.info(f"Added weekly task: {name} (every {day_of_week} at {time_of_day} UTC)")
    
    def _calculate_next_daily_run(self, time_of_day: str) -> datetime:
        """Calculate the next run time for a daily task."""
        now = datetime.now(timezone.utc)
        hour, minute = map(int, time_of_day.split(':'))
        
        # Create today's run time
        today_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If today's time has passed, schedule for tomorrow
        if today_run <= now:
            today_run += timedelta(days=1)
        
        return today_run
    
    def _calculate_next_weekly_run(self, day_of_week: str, time_of_day: str) -> datetime:
        """Calculate the next run time for a weekly task."""
        now = datetime.now(timezone.utc)
        hour, minute = map(int, time_of_day.split(':'))
        
        # Map day names to weekday numbers (Monday = 0)
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday = day_mapping[day_of_week]
        current_weekday = now.weekday()
        
        # Calculate days until target day
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        # Create the target datetime
        target_date = now + timedelta(days=days_ahead)
        target_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If it's the same day but time has passed, schedule for next week
        if days_ahead == 0 and target_datetime <= now:
            target_datetime += timedelta(days=7)
        
        return target_datetime
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a scheduled task.
        
        Args:
            task_id: ID of task to remove
            
        Returns:
            True if task was removed, False if not found
        """
        if task_id in self.tasks:
            task = self.tasks.pop(task_id)
            self.logger.info(f"Removed task: {task.name}")
            return True
        return False
    
    def enable_task(self, task_id: str) -> bool:
        """Enable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self.logger.info(f"Enabled task: {self.tasks[task_id].name}")
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """Disable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self.logger.info(f"Disabled task: {self.tasks[task_id].name}")
            return True
        return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status information for a task."""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            'task_id': task.task_id,
            'name': task.name,
            'schedule_type': task.schedule_type.value,
            'enabled': task.enabled,
            'last_run': task.last_run.isoformat() if task.last_run else None,
            'next_run': task.next_run.isoformat() if task.next_run else None,
            'interval_minutes': task.interval_minutes,
            'time_of_day': task.time_of_day,
            'day_of_week': task.day_of_week
        }
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks and their status."""
        return [self.get_task_status(task_id) for task_id in self.tasks.keys()]
    
    def start(self) -> None:
        """Start the scheduler."""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.stop_event.clear()
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info(f"Scheduler started with {len(self.tasks)} tasks")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.running:
            return
        
        self.logger.info("Stopping scheduler...")
        self.running = False
        self.stop_event.set()
        
        # Wait for scheduler thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5.0)
        
        self.logger.info("Scheduler stopped")
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        self.logger.info("Scheduler loop started")
        
        while self.running and not self.stop_event.is_set():
            try:
                now = datetime.now(timezone.utc)
                
                # Check each task
                for task in self.tasks.values():
                    if not task.enabled or not task.next_run:
                        continue
                    
                    # Check if it's time to run the task
                    if now >= task.next_run:
                        self._execute_task(task)
                        self._schedule_next_run(task)
                
                # Sleep for 30 seconds before next check
                if not self.stop_event.wait(30):
                    continue
                else:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                # Continue running even if there's an error
                time.sleep(60)  # Wait a minute before retrying
        
        self.logger.info("Scheduler loop ended")
    
    def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a scheduled task."""
        self.logger.info(f"Executing task: {task.name}")
        
        try:
            # Update last run time
            task.last_run = datetime.now(timezone.utc)
            
            # Execute the callback
            if task.callback:
                if task.callback_args or task.callback_kwargs:
                    result = task.callback(*task.callback_args, **task.callback_kwargs)
                else:
                    result = task.callback()
                
                self.logger.info(f"Task {task.name} completed successfully")
                
                # Log result if it's a dictionary with useful info
                if isinstance(result, dict) and 'success' in result:
                    self.logger.info(f"Task result: success={result.get('success')}")
            
        except Exception as e:
            self.logger.error(f"Task {task.name} failed: {e}")
    
    def _schedule_next_run(self, task: ScheduledTask) -> None:
        """Schedule the next run for a task."""
        if task.schedule_type == ScheduleType.CONTINUOUS:
            # Add interval to current time
            task.next_run = datetime.now(timezone.utc) + timedelta(minutes=task.interval_minutes)
            
        elif task.schedule_type == ScheduleType.DAILY:
            # Schedule for next day at same time
            task.next_run = self._calculate_next_daily_run(task.time_of_day)
            
        elif task.schedule_type == ScheduleType.WEEKLY:
            # Schedule for next week at same day/time
            task.next_run = self._calculate_next_weekly_run(task.day_of_week, task.time_of_day)
        
        self.logger.debug(f"Next run for {task.name}: {task.next_run}")
    
    def run_task_now(self, task_id: str) -> bool:
        """
        Run a task immediately (outside of its schedule).
        
        Args:
            task_id: ID of task to run
            
        Returns:
            True if task was executed, False if not found or disabled
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if not task.enabled:
            return False
        
        self.logger.info(f"Running task immediately: {task.name}")
        self._execute_task(task)
        return True
    
    def get_next_run_times(self) -> Dict[str, datetime]:
        """Get next run times for all enabled tasks."""
        return {
            task_id: task.next_run
            for task_id, task in self.tasks.items()
            if task.enabled and task.next_run
        }
    
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.running
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()