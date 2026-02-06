#!/usr/bin/env python3
"""
Operational Dashboard for Advanced FinOps Platform

This script provides a simple command-line operational dashboard that displays:
- System health status
- Performance metrics
- Active alerts
- Error recovery statistics
- Real-time monitoring data

Usage:
    python operational_dashboard.py --refresh 30    # Refresh every 30 seconds
    python operational_dashboard.py --once          # Run once and exit
    python operational_dashboard.py --export        # Export metrics to file
"""

import argparse
import time
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

from utils.monitoring import system_monitor, AlertSeverity, HealthStatus
from utils.error_recovery import global_recovery_manager


class OperationalDashboard:
    """Simple operational dashboard for system monitoring."""
    
    def __init__(self):
        self.start_time = time.time()
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_uptime(self, uptime_seconds: float) -> str:
        """Format uptime in human-readable format."""
        seconds = int(uptime_seconds)
        minutes = seconds // 60
        hours = minutes // 60
        days = hours // 24
        
        if days > 0:
            return f"{days}d {hours % 24}h {minutes % 60}m"
        elif hours > 0:
            return f"{hours}h {minutes % 60}m"
        elif minutes > 0:
            return f"{minutes}m {seconds % 60}s"
        else:
            return f"{seconds}s"
    
    def get_status_color(self, status: str) -> str:
        """Get ANSI color code for status."""
        colors = {
            'HEALTHY': '\033[92m',    # Green
            'DEGRADED': '\033[93m',   # Yellow
            'UNHEALTHY': '\033[91m',  # Red
            'CRITICAL': '\033[95m',   # Magenta
        }
        return colors.get(status, '\033[0m')  # Default
    
    def get_severity_color(self, severity: str) -> str:
        """Get ANSI color code for alert severity."""
        colors = {
            'INFO': '\033[94m',       # Blue
            'WARNING': '\033[93m',    # Yellow
            'ERROR': '\033[91m',      # Red
            'CRITICAL': '\033[95m',   # Magenta
        }
        return colors.get(severity, '\033[0m')  # Default
    
    def display_header(self):
        """Display dashboard header."""
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        uptime = self.format_uptime(time.time() - self.start_time)
        
        print("=" * 80)
        print("🚀 ADVANCED FINOPS PLATFORM - OPERATIONAL DASHBOARD")
        print("=" * 80)
        print(f"Current Time: {current_time}")
        print(f"Dashboard Uptime: {uptime}")
        print()
    
    def display_system_status(self):
        """Display system health status."""
        print("📊 SYSTEM STATUS")
        print("-" * 40)
        
        try:
            status = system_monitor.get_system_status()
            overall_health = status.get('overall_health', 'UNKNOWN')
            
            color = self.get_status_color(overall_health)
            print(f"Overall Health: {color}{overall_health}\033[0m")
            
            # Display individual health checks
            health_checks = status.get('health_checks', {})
            for name, check in health_checks.items():
                check_status = check.get('status', 'UNKNOWN')
                check_color = self.get_status_color(check_status)
                response_time = check.get('response_time_ms', 0)
                print(f"  {name}: {check_color}{check_status}\033[0m ({response_time:.1f}ms)")
                
                # Show message if not healthy
                if check_status != 'HEALTHY':
                    message = check.get('message', 'No details available')
                    print(f"    └─ {message}")
            
        except Exception as e:
            print(f"❌ Error getting system status: {e}")
        
        print()
    
    def display_performance_metrics(self):
        """Display performance metrics."""
        print("📈 PERFORMANCE METRICS")
        print("-" * 40)
        
        try:
            status = system_monitor.get_system_status()
            metrics = status.get('metrics', {})
            
            if not metrics:
                print("No metrics available")
            else:
                # Display key metrics
                for metric_name, metric_data in list(metrics.items())[:10]:  # Show top 10
                    if isinstance(metric_data, dict) and 'count' in metric_data:
                        count = metric_data.get('count', 0)
                        mean = metric_data.get('mean', 0)
                        p95 = metric_data.get('p95', 0)
                        print(f"  {metric_name}:")
                        print(f"    Count: {count}, Mean: {mean:.2f}, P95: {p95:.2f}")
            
        except Exception as e:
            print(f"❌ Error getting performance metrics: {e}")
        
        print()
    
    def display_alerts(self):
        """Display active alerts."""
        print("🚨 ACTIVE ALERTS")
        print("-" * 40)
        
        try:
            status = system_monitor.get_system_status()
            alerts_info = status.get('alerts', {})
            
            active_count = alerts_info.get('active', 0)
            by_severity = alerts_info.get('bySeverity', {})
            
            print(f"Active Alerts: {active_count}")
            
            if active_count > 0:
                for severity, count in by_severity.items():
                    if count > 0:
                        color = self.get_severity_color(severity)
                        print(f"  {color}{severity}\033[0m: {count}")
                
                # Get recent alerts
                active_alerts = system_monitor.alert_manager.get_active_alerts()
                
                print("\nRecent Active Alerts:")
                for alert in active_alerts[-5:]:  # Show last 5
                    severity_color = self.get_severity_color(alert.severity.value)
                    timestamp = datetime.fromtimestamp(alert.timestamp).strftime('%H:%M:%S')
                    print(f"  [{timestamp}] {severity_color}{alert.severity.value}\033[0m: {alert.title}")
                    print(f"    └─ {alert.message}")
            else:
                print("✅ No active alerts")
            
        except Exception as e:
            print(f"❌ Error getting alerts: {e}")
        
        print()
    
    def display_error_recovery_stats(self):
        """Display error recovery statistics."""
        print("🔄 ERROR RECOVERY STATISTICS")
        print("-" * 40)
        
        try:
            stats = global_recovery_manager.get_recovery_stats()
            
            if not stats:
                print("No recovery statistics available")
            else:
                total_attempts = stats.get('total_attempts', 0)
                total_successes = stats.get('total_successes', 0)
                total_failures = stats.get('total_failures', 0)
                success_rate = stats.get('overall_success_rate', 0) * 100
                
                print(f"Total Attempts: {total_attempts}")
                print(f"Total Successes: {total_successes}")
                print(f"Total Failures: {total_failures}")
                print(f"Success Rate: {success_rate:.1f}%")
                
                # Show operations with circuit breaker open
                cb_open = stats.get('operations_with_circuit_breaker_open', 0)
                if cb_open > 0:
                    print(f"⚠️  Operations with Circuit Breaker Open: {cb_open}")
                
                # Show top operations by activity
                operations = stats.get('operations', {})
                if operations:
                    print("\nTop Operations:")
                    sorted_ops = sorted(
                        operations.items(), 
                        key=lambda x: x[1].get('success_rate', 0), 
                        reverse=True
                    )
                    
                    for op_name, op_stats in sorted_ops[:5]:  # Top 5
                        op_success_rate = op_stats.get('success_rate', 0) * 100
                        consecutive_failures = op_stats.get('consecutive_failures', 0)
                        cb_open = op_stats.get('circuit_breaker_open', False)
                        
                        status_indicator = "🔴" if cb_open else "🟡" if consecutive_failures > 0 else "🟢"
                        print(f"  {status_indicator} {op_name}: {op_success_rate:.1f}% success")
            
        except Exception as e:
            print(f"❌ Error getting recovery statistics: {e}")
        
        print()
    
    def display_footer(self):
        """Display dashboard footer."""
        print("=" * 80)
        print("Press Ctrl+C to exit | Use --help for options")
        print("=" * 80)
    
    def display_dashboard(self):
        """Display complete dashboard."""
        self.clear_screen()
        self.display_header()
        self.display_system_status()
        self.display_performance_metrics()
        self.display_alerts()
        self.display_error_recovery_stats()
        self.display_footer()
    
    def export_metrics(self, filename: str = None):
        """Export metrics to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"finops_metrics_{timestamp}.json"
        
        try:
            # Collect all metrics
            system_status = system_monitor.get_system_status()
            recovery_stats = global_recovery_manager.get_recovery_stats()
            
            export_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_status': system_status,
                'recovery_statistics': recovery_stats,
                'dashboard_uptime': time.time() - self.start_time
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"✅ Metrics exported to {filename}")
            
        except Exception as e:
            print(f"❌ Error exporting metrics: {e}")
    
    def run_continuous(self, refresh_interval: int = 30):
        """Run dashboard in continuous mode."""
        print(f"Starting operational dashboard (refresh every {refresh_interval}s)")
        
        try:
            while True:
                self.display_dashboard()
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\n\n👋 Dashboard stopped by user")
    
    def run_once(self):
        """Run dashboard once and exit."""
        self.display_dashboard()


def main():
    """Main entry point for operational dashboard."""
    parser = argparse.ArgumentParser(
        description='Advanced FinOps Platform Operational Dashboard',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--refresh', type=int, default=30,
                       help='Refresh interval in seconds (default: 30)')
    
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit')
    
    parser.add_argument('--export', type=str, nargs='?', const='auto',
                       help='Export metrics to JSON file')
    
    args = parser.parse_args()
    
    # Initialize dashboard
    dashboard = OperationalDashboard()
    
    # Start system monitoring if not already started
    if not system_monitor.monitoring_active:
        system_monitor.start_monitoring()
        print("Started system monitoring...")
        time.sleep(2)  # Give it a moment to collect initial data
    
    try:
        if args.export:
            filename = None if args.export == 'auto' else args.export
            dashboard.export_metrics(filename)
        elif args.once:
            dashboard.run_once()
        else:
            dashboard.run_continuous(args.refresh)
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
    finally:
        # Stop monitoring if we started it
        if system_monitor.monitoring_active:
            system_monitor.stop_monitoring()


if __name__ == "__main__":
    main()