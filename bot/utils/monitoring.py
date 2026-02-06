#!/usr/bin/env python3
"""
Comprehensive Monitoring and Error Handling for Advanced FinOps Platform

This module provides:
- Structured logging with correlation IDs
- System health monitoring and alerting
- Performance metrics collection and analysis
- Error recovery mechanisms with exponential backoff
- Operational dashboards data collection
- Real-time monitoring and alerting capabilities

Requirements: 4.4 - System health monitoring, alerting, and performance metrics
"""

import logging
import json
import time
import uuid
import threading
import psutil
import socket
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

# Create monitoring-specific logger
monitor_logger = logging.getLogger('finops.monitoring')


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    CRITICAL = "CRITICAL"


@dataclass
class CorrelationContext:
    """Context for request correlation tracking."""
    correlation_id: str
    operation_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    parent_correlation_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = "count"


@dataclass
class HealthCheck:
    """Health check result."""
    name: str
    status: HealthStatus
    message: str
    timestamp: float
    response_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """System alert."""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: float
    source: str
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[float] = None


class SafeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles non-serializable objects by converting them to strings."""
    def default(self, obj: Any) -> Any:
        try:
            return super().default(obj)
        except TypeError:
            if isinstance(obj, datetime):
                return obj.isoformat()
            if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
                return obj.to_dict()
            return str(obj)


class StructuredLogger:
    """Enhanced structured logger with correlation ID support."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._context_storage = threading.local()
    
    def set_correlation_context(self, context: CorrelationContext):
        """Set correlation context for current thread."""
        self._context_storage.context = context
    
    def get_correlation_context(self) -> Optional[CorrelationContext]:
        """Get correlation context for current thread."""
        return getattr(self._context_storage, 'context', None)
    
    def clear_correlation_context(self):
        """Clear correlation context for current thread."""
        if hasattr(self._context_storage, 'context'):
            delattr(self._context_storage, 'context')
    
    def _format_message(self, message: str, extra_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format message with correlation context and structured data."""
        context = self.get_correlation_context()
        
        structured_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': message,
            'level': 'INFO'  # Will be overridden by specific log methods
        }
        
        if context:
            structured_data.update({
                'correlation_id': context.correlation_id,
                'operation_id': context.operation_id,
                'session_id': context.session_id,
                'user_id': context.user_id,
                'parent_correlation_id': context.parent_correlation_id,
                'operation_duration_ms': (time.time() - context.start_time) * 1000
            })
            
            if context.metadata:
                structured_data['context_metadata'] = context.metadata
        
        if extra_data:
            structured_data['extra_data'] = extra_data
        
        return structured_data
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log info message with correlation context."""
        structured_data = self._format_message(message, extra_data)
        structured_data['level'] = 'INFO'
        self.logger.info(json.dumps(structured_data, cls=SafeJSONEncoder))
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log warning message with correlation context."""
        structured_data = self._format_message(message, extra_data)
        structured_data['level'] = 'WARNING'
        self.logger.warning(json.dumps(structured_data, cls=SafeJSONEncoder))
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message with correlation context."""
        structured_data = self._format_message(message, extra_data)
        structured_data['level'] = 'ERROR'
        
        if exc_info:
            import traceback
            structured_data['exception'] = traceback.format_exc()
        
        self.logger.error(json.dumps(structured_data, cls=SafeJSONEncoder), exc_info=exc_info)
    
    def critical(self, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log critical message with correlation context."""
        structured_data = self._format_message(message, extra_data)
        structured_data['level'] = 'CRITICAL'
        
        if exc_info:
            import traceback
            structured_data['exception'] = traceback.format_exc()
        
        self.logger.critical(json.dumps(structured_data, cls=SafeJSONEncoder), exc_info=exc_info)
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log debug message with correlation context."""
        structured_data = self._format_message(message, extra_data)
        structured_data['level'] = 'DEBUG'
        self.logger.debug(json.dumps(structured_data, cls=SafeJSONEncoder))


class ExponentialBackoff:
    """Exponential backoff implementation with jitter."""
    
    def __init__(self, 
                 initial_delay: float = 1.0,
                 max_delay: float = 60.0,
                 multiplier: float = 2.0,
                 jitter: bool = True):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
        self.attempt = 0
    
    def get_delay(self) -> float:
        """Get delay for current attempt."""
        delay = min(self.initial_delay * (self.multiplier ** self.attempt), self.max_delay)
        
        if self.jitter:
            # Add jitter to prevent thundering herd
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    def wait(self):
        """Wait for the calculated delay."""
        delay = self.get_delay()
        time.sleep(delay)
        self.attempt += 1
    
    def reset(self):
        """Reset attempt counter."""
        self.attempt = 0


class MetricsCollector:
    """Collects and aggregates performance metrics."""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics = deque(maxlen=max_metrics)
        self.aggregated_metrics = defaultdict(list)
        self.lock = threading.Lock()
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric."""
        with self.lock:
            self.metrics.append(metric)
            self.aggregated_metrics[metric.name].append(metric)
            
            # Keep only recent metrics per name
            if len(self.aggregated_metrics[metric.name]) > 1000:
                self.aggregated_metrics[metric.name] = self.aggregated_metrics[metric.name][-1000:]
    
    def get_metric_stats(self, metric_name: str, time_window_seconds: Optional[float] = None) -> Dict[str, Any]:
        """Get statistics for a specific metric."""
        with self.lock:
            if metric_name not in self.aggregated_metrics:
                return {}
            
            metrics = self.aggregated_metrics[metric_name]
            
            if time_window_seconds:
                cutoff_time = time.time() - time_window_seconds
                metrics = [m for m in metrics if m.timestamp >= cutoff_time]
            
            if not metrics:
                return {}
            
            values = [m.value for m in metrics]
            
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                'p95': statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
                'p99': statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values),
                'latest': values[-1],
                'time_window_seconds': time_window_seconds
            }
    
    def get_all_metrics_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all metrics."""
        summary = {}
        for metric_name in self.aggregated_metrics.keys():
            summary[metric_name] = self.get_metric_stats(metric_name, time_window_seconds=300)  # Last 5 minutes
        return summary


class HealthMonitor:
    """System health monitoring with configurable checks."""
    
    def __init__(self):
        self.health_checks = {}
        self.health_history = deque(maxlen=1000)
        self.lock = threading.Lock()
        self.logger = StructuredLogger('finops.health')
    
    def register_health_check(self, name: str, check_func: Callable[[], HealthCheck]):
        """Register a health check function."""
        self.health_checks[name] = check_func
        self.logger.info(f"Registered health check: {name}")
    
    def run_health_check(self, name: str) -> HealthCheck:
        """Run a specific health check."""
        if name not in self.health_checks:
            return HealthCheck(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Health check '{name}' not found",
                timestamp=time.time(),
                response_time_ms=0
            )
        
        start_time = time.time()
        try:
            result = self.health_checks[name]()
            result.response_time_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            return HealthCheck(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                timestamp=time.time(),
                response_time_ms=(time.time() - start_time) * 1000,
                metadata={'exception': str(e)}
            )
    
    def run_all_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks."""
        results = {}
        for name in self.health_checks.keys():
            results[name] = self.run_health_check(name)
        
        with self.lock:
            self.health_history.append({
                'timestamp': time.time(),
                'results': results
            })
        
        return results
    
    def get_overall_health_status(self) -> HealthStatus:
        """Get overall system health status."""
        results = self.run_all_health_checks()
        
        if not results:
            return HealthStatus.CRITICAL
        
        statuses = [check.status for check in results.values()]
        
        if any(status == HealthStatus.CRITICAL for status in statuses):
            return HealthStatus.CRITICAL
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY


class AlertManager:
    """Manages system alerts and notifications."""
    
    def __init__(self, max_alerts: int = 1000):
        self.max_alerts = max_alerts
        self.alerts = deque(maxlen=max_alerts)
        self.alert_handlers = defaultdict(list)
        self.lock = threading.Lock()
        self.logger = StructuredLogger('finops.alerts')
    
    def register_alert_handler(self, severity: AlertSeverity, handler: Callable[[Alert], None]):
        """Register an alert handler for specific severity."""
        self.alert_handlers[severity].append(handler)
        self.logger.info(f"Registered alert handler for {severity.value}")
    
    def create_alert(self, 
                    severity: AlertSeverity,
                    title: str,
                    message: str,
                    source: str,
                    correlation_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Alert:
        """Create and process a new alert."""
        alert = Alert(
            id=str(uuid.uuid4()),
            severity=severity,
            title=title,
            message=message,
            timestamp=time.time(),
            source=source,
            correlation_id=correlation_id,
            metadata=metadata or {}
        )
        
        with self.lock:
            self.alerts.append(alert)
        
        # Log the alert
        self.logger.warning(f"Alert created: {title}", {
            'alert_id': alert.id,
            'severity': severity.value,
            'source': source,
            'message': message
        })
        
        # Notify handlers
        for handler in self.alert_handlers[severity]:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {str(e)}", exc_info=True)
        
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert by ID."""
        with self.lock:
            for alert in self.alerts:
                if alert.id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = time.time()
                    self.logger.info(f"Alert resolved: {alert.title}", {'alert_id': alert_id})
                    return True
        return False
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active (unresolved) alerts."""
        with self.lock:
            active_alerts = [alert for alert in self.alerts if not alert.resolved]
            
            if severity:
                active_alerts = [alert for alert in active_alerts if alert.severity == severity]
            
            return active_alerts
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alerts."""
        with self.lock:
            active_alerts = [alert for alert in self.alerts if not alert.resolved]
            
            summary = {
                'total_alerts': len(self.alerts),
                'active_alerts': len(active_alerts),
                'resolved_alerts': len(self.alerts) - len(active_alerts),
                'by_severity': {
                    'CRITICAL': len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                    'ERROR': len([a for a in active_alerts if a.severity == AlertSeverity.ERROR]),
                    'WARNING': len([a for a in active_alerts if a.severity == AlertSeverity.WARNING]),
                    'INFO': len([a for a in active_alerts if a.severity == AlertSeverity.INFO])
                }
            }
            
            return summary


class SystemMonitor:
    """Comprehensive system monitoring and health management."""
    
    def __init__(self):
        self.logger = StructuredLogger('finops.system')
        self.metrics_collector = MetricsCollector()
        self.health_monitor = HealthMonitor()
        self.alert_manager = AlertManager()
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # Register default health checks
        self._register_default_health_checks()
        
        # Register default alert handlers
        self._register_default_alert_handlers()
    
    def _register_default_health_checks(self):
        """Register default system health checks."""
        
        def check_system_resources() -> HealthCheck:
            """Check system CPU, memory, and disk usage."""
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                status = HealthStatus.HEALTHY
                messages = []
                
                if cpu_percent > 90:
                    status = HealthStatus.CRITICAL
                    messages.append(f"CPU usage critical: {cpu_percent}%")
                elif cpu_percent > 80:
                    status = HealthStatus.UNHEALTHY
                    messages.append(f"CPU usage high: {cpu_percent}%")
                elif cpu_percent > 70:
                    status = HealthStatus.DEGRADED
                    messages.append(f"CPU usage elevated: {cpu_percent}%")
                
                if memory.percent > 90:
                    status = max(status, HealthStatus.CRITICAL, key=lambda x: x.value)
                    messages.append(f"Memory usage critical: {memory.percent}%")
                elif memory.percent > 80:
                    status = max(status, HealthStatus.UNHEALTHY, key=lambda x: x.value)
                    messages.append(f"Memory usage high: {memory.percent}%")
                
                if disk.percent > 95:
                    status = max(status, HealthStatus.CRITICAL, key=lambda x: x.value)
                    messages.append(f"Disk usage critical: {disk.percent}%")
                elif disk.percent > 85:
                    status = max(status, HealthStatus.UNHEALTHY, key=lambda x: x.value)
                    messages.append(f"Disk usage high: {disk.percent}%")
                
                message = "; ".join(messages) if messages else f"System resources normal (CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%)"
                
                return HealthCheck(
                    name="system_resources",
                    status=status,
                    message=message,
                    timestamp=time.time(),
                    response_time_ms=0,
                    metadata={
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'disk_percent': disk.percent,
                        'memory_available_gb': memory.available / (1024**3),
                        'disk_free_gb': disk.free / (1024**3)
                    }
                )
            except Exception as e:
                return HealthCheck(
                    name="system_resources",
                    status=HealthStatus.CRITICAL,
                    message=f"Failed to check system resources: {str(e)}",
                    timestamp=time.time(),
                    response_time_ms=0
                )
        
        def check_network_connectivity() -> HealthCheck:
            """Check network connectivity."""
            try:
                # Test DNS resolution and connectivity
                socket.create_connection(("8.8.8.8", 53), timeout=5)
                
                return HealthCheck(
                    name="network_connectivity",
                    status=HealthStatus.HEALTHY,
                    message="Network connectivity normal",
                    timestamp=time.time(),
                    response_time_ms=0
                )
            except Exception as e:
                return HealthCheck(
                    name="network_connectivity",
                    status=HealthStatus.CRITICAL,
                    message=f"Network connectivity failed: {str(e)}",
                    timestamp=time.time(),
                    response_time_ms=0
                )
        
        self.health_monitor.register_health_check("system_resources", check_system_resources)
        self.health_monitor.register_health_check("network_connectivity", check_network_connectivity)
    
    def _register_default_alert_handlers(self):
        """Register default alert handlers."""
        
        def log_alert(alert: Alert):
            """Log alert to structured logger."""
            self.logger.error(f"ALERT: {alert.title}", {
                'alert_id': alert.id,
                'severity': alert.severity.value,
                'source': alert.source,
                'message': alert.message,
                'metadata': alert.metadata
            })
        
        # Register log handler for all severities
        for severity in AlertSeverity:
            self.alert_manager.register_alert_handler(severity, log_alert)
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start background monitoring thread."""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        
        def monitoring_loop():
            self.logger.info("System monitoring started", {'interval_seconds': interval_seconds})
            
            while self.monitoring_active:
                try:
                    # Run health checks
                    health_results = self.health_monitor.run_all_health_checks()
                    
                    # Record system metrics
                    self._record_system_metrics()
                    
                    # Check for alerts based on health status
                    self._check_health_alerts(health_results)
                    
                    time.sleep(interval_seconds)
                    
                except Exception as e:
                    self.logger.error("Monitoring loop error", {'error': str(e)}, exc_info=True)
                    time.sleep(interval_seconds)
            
            self.logger.info("System monitoring stopped")
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        if self.monitoring_active:
            self.monitoring_active = False
            self.logger.info("Stopping system monitoring")
            
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
    
    def _record_system_metrics(self):
        """Record system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent()
            self.metrics_collector.record_metric(PerformanceMetric(
                name="system.cpu.usage_percent",
                value=cpu_percent,
                timestamp=time.time(),
                unit="percent"
            ))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics_collector.record_metric(PerformanceMetric(
                name="system.memory.usage_percent",
                value=memory.percent,
                timestamp=time.time(),
                unit="percent"
            ))
            
            self.metrics_collector.record_metric(PerformanceMetric(
                name="system.memory.available_gb",
                value=memory.available / (1024**3),
                timestamp=time.time(),
                unit="gigabytes"
            ))
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.metrics_collector.record_metric(PerformanceMetric(
                name="system.disk.usage_percent",
                value=disk.percent,
                timestamp=time.time(),
                unit="percent"
            ))
            
            self.metrics_collector.record_metric(PerformanceMetric(
                name="system.disk.free_gb",
                value=disk.free / (1024**3),
                timestamp=time.time(),
                unit="gigabytes"
            ))
            
        except Exception as e:
            self.logger.error("Failed to record system metrics", {'error': str(e)})
    
    def _check_health_alerts(self, health_results: Dict[str, HealthCheck]):
        """Check health results and create alerts if needed."""
        for name, health_check in health_results.items():
            if health_check.status == HealthStatus.CRITICAL:
                self.alert_manager.create_alert(
                    severity=AlertSeverity.CRITICAL,
                    title=f"Critical Health Check Failure: {name}",
                    message=health_check.message,
                    source="system_monitor",
                    metadata={
                        'health_check_name': name,
                        'response_time_ms': health_check.response_time_ms,
                        'health_metadata': health_check.metadata
                    }
                )
            elif health_check.status == HealthStatus.UNHEALTHY:
                self.alert_manager.create_alert(
                    severity=AlertSeverity.ERROR,
                    title=f"Health Check Unhealthy: {name}",
                    message=health_check.message,
                    source="system_monitor",
                    metadata={
                        'health_check_name': name,
                        'response_time_ms': health_check.response_time_ms,
                        'health_metadata': health_check.metadata
                    }
                )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        health_results = self.health_monitor.run_all_health_checks()
        overall_health = self.health_monitor.get_overall_health_status()
        alert_summary = self.alert_manager.get_alert_summary()
        metrics_summary = self.metrics_collector.get_all_metrics_summary()
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_health': overall_health.value,
            'health_checks': {
                name: {
                    'status': check.status.value,
                    'message': check.message,
                    'response_time_ms': check.response_time_ms,
                    'metadata': check.metadata
                }
                for name, check in health_results.items()
            },
            'alerts': alert_summary,
            'metrics': metrics_summary,
            'monitoring_active': self.monitoring_active
        }
    
    def record_operation_metric(self, operation_name: str, duration_ms: float, success: bool):
        """Record operation performance metric."""
        self.metrics_collector.record_metric(PerformanceMetric(
            name=f"operation.{operation_name}.duration_ms",
            value=duration_ms,
            timestamp=time.time(),
            tags={'success': str(success)},
            unit="milliseconds"
        ))
        
        self.metrics_collector.record_metric(PerformanceMetric(
            name=f"operation.{operation_name}.count",
            value=1,
            timestamp=time.time(),
            tags={'success': str(success)},
            unit="count"
        ))


# Global system monitor instance
system_monitor = SystemMonitor()

# Convenience functions for easy access
def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)

def create_correlation_context(operation_id: str, **kwargs) -> CorrelationContext:
    """Create a new correlation context."""
    return CorrelationContext(
        correlation_id=str(uuid.uuid4()),
        operation_id=operation_id,
        **kwargs
    )

def with_correlation_context(context: CorrelationContext):
    """Decorator to set correlation context for a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_structured_logger(func.__module__)
            logger.set_correlation_context(context)
            try:
                return func(*args, **kwargs)
            finally:
                logger.clear_correlation_context()
        return wrapper
    return decorator