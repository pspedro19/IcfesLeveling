#!/usr/bin/env python3
"""
Advanced Performance Monitoring Service for ICFES Leveling System
Real-time performance metrics, alerts, and optimization recommendations
"""

import psutil
import time
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import statistics
from collections import defaultdict, deque

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import DatabaseSession, engine, check_database_health
from app.core.cache_manager import cache_manager

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    memory_available: float
    disk_io_read: float
    disk_io_write: float
    network_sent: float
    network_received: float
    database_connections: int
    cache_hit_rate: float
    response_time_avg: float
    active_sessions: int

@dataclass
class AlertThresholds:
    """Alert threshold configuration"""
    cpu_warning: float = 70.0
    cpu_critical: float = 90.0
    memory_warning: float = 80.0
    memory_critical: float = 95.0
    response_time_warning: float = 1.0
    response_time_critical: float = 3.0
    cache_hit_rate_warning: float = 60.0
    cache_hit_rate_critical: float = 40.0
    db_connections_warning: float = 40
    db_connections_critical: float = 45

class AdvancedPerformanceMonitor:
    """Advanced performance monitoring service with real-time alerts"""
    
    def __init__(self, max_history_points: int = 1000):
        self.max_history_points = max_history_points
        self.metrics_history = deque(maxlen=max_history_points)
        self.alert_thresholds = AlertThresholds()
        self.active_alerts = set()
        self.response_times = deque(maxlen=100)  # Last 100 response times
        self.query_performance_stats = defaultdict(list)
        self.is_monitoring = False
        
        # System resource tracking
        self.last_disk_io = psutil.disk_io_counters()
        self.last_network_io = psutil.net_io_counters()
        self.last_check_time = time.time()
        
    async def start_monitoring(self, interval: float = 30.0):
        """Start continuous performance monitoring"""
        self.is_monitoring = True
        logger.info(f"Starting performance monitoring with {interval}s interval")
        
        while self.is_monitoring:
            try:
                metrics = await self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check for alerts
                await self.check_alerts(metrics)
                
                # Log performance summary every 10 minutes
                if len(self.metrics_history) % 20 == 0:  # Every 20 intervals (10min if 30s interval)
                    summary = self.generate_performance_summary()
                    logger.info(f"Performance Summary: CPU: {summary['avg_cpu']:.1f}%, "
                              f"Memory: {summary['avg_memory']:.1f}%, "
                              f"Response Time: {summary['avg_response_time']:.2f}s, "
                              f"Cache Hit Rate: {summary['avg_cache_hit_rate']:.1f}%")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(interval)
    
    async def collect_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics"""
        current_time = time.time()
        
        # System metrics
        cpu_usage = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        memory_available = memory.available / (1024**3)  # GB
        
        # Disk I/O metrics
        current_disk_io = psutil.disk_io_counters()
        if self.last_disk_io:
            time_delta = current_time - self.last_check_time
            disk_io_read = (current_disk_io.read_bytes - self.last_disk_io.read_bytes) / time_delta / 1024  # KB/s
            disk_io_write = (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / time_delta / 1024  # KB/s
        else:
            disk_io_read = disk_io_write = 0.0
        
        # Network I/O metrics
        current_network_io = psutil.net_io_counters()
        if self.last_network_io:
            network_sent = (current_network_io.bytes_sent - self.last_network_io.bytes_sent) / time_delta / 1024  # KB/s
            network_received = (current_network_io.bytes_recv - self.last_network_io.bytes_recv) / time_delta / 1024  # KB/s
        else:
            network_sent = network_received = 0.0
        
        # Database metrics
        db_health = check_database_health()
        database_connections = db_health.get('checked_out', 0) if db_health.get('status') == 'healthy' else -1
        
        # Cache metrics
        cache_stats = cache_manager.get_cache_stats()
        cache_hit_rate = cache_stats.get('hit_rate', 0.0)
        
        # Response time metrics
        response_time_avg = statistics.mean(self.response_times) if self.response_times else 0.0
        
        # Active sessions (placeholder - would need session tracking)
        active_sessions = len(self.response_times)  # Approximate based on recent activity
        
        # Update state
        self.last_disk_io = current_disk_io
        self.last_network_io = current_network_io
        self.last_check_time = current_time
        
        return PerformanceMetrics(
            timestamp=current_time,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            memory_available=memory_available,
            disk_io_read=disk_io_read,
            disk_io_write=disk_io_write,
            network_sent=network_sent,
            network_received=network_received,
            database_connections=database_connections,
            cache_hit_rate=cache_hit_rate,
            response_time_avg=response_time_avg,
            active_sessions=active_sessions
        )
    
    async def check_alerts(self, metrics: PerformanceMetrics):
        """Check metrics against thresholds and generate alerts"""
        alerts_to_add = set()
        alerts_to_remove = set()
        
        # CPU alerts
        if metrics.cpu_usage >= self.alert_thresholds.cpu_critical:
            alerts_to_add.add(('cpu', 'CRITICAL', f'CPU usage at {metrics.cpu_usage:.1f}%'))
        elif metrics.cpu_usage >= self.alert_thresholds.cpu_warning:
            alerts_to_add.add(('cpu', 'WARNING', f'CPU usage at {metrics.cpu_usage:.1f}%'))
        else:
            alerts_to_remove.add('cpu')
        
        # Memory alerts
        if metrics.memory_usage >= self.alert_thresholds.memory_critical:
            alerts_to_add.add(('memory', 'CRITICAL', f'Memory usage at {metrics.memory_usage:.1f}%'))
        elif metrics.memory_usage >= self.alert_thresholds.memory_warning:
            alerts_to_add.add(('memory', 'WARNING', f'Memory usage at {metrics.memory_usage:.1f}%'))
        else:
            alerts_to_remove.add('memory')
        
        # Response time alerts
        if metrics.response_time_avg >= self.alert_thresholds.response_time_critical:
            alerts_to_add.add(('response_time', 'CRITICAL', f'Avg response time: {metrics.response_time_avg:.2f}s'))
        elif metrics.response_time_avg >= self.alert_thresholds.response_time_warning:
            alerts_to_add.add(('response_time', 'WARNING', f'Avg response time: {metrics.response_time_avg:.2f}s'))
        else:
            alerts_to_remove.add('response_time')
        
        # Cache hit rate alerts
        if metrics.cache_hit_rate <= self.alert_thresholds.cache_hit_rate_critical:
            alerts_to_add.add(('cache', 'CRITICAL', f'Cache hit rate: {metrics.cache_hit_rate:.1f}%'))
        elif metrics.cache_hit_rate <= self.alert_thresholds.cache_hit_rate_warning:
            alerts_to_add.add(('cache', 'WARNING', f'Cache hit rate: {metrics.cache_hit_rate:.1f}%'))
        else:
            alerts_to_remove.add('cache')
        
        # Database connections alerts
        if metrics.database_connections >= self.alert_thresholds.db_connections_critical:
            alerts_to_add.add(('database', 'CRITICAL', f'DB connections: {metrics.database_connections}'))
        elif metrics.database_connections >= self.alert_thresholds.db_connections_warning:
            alerts_to_add.add(('database', 'WARNING', f'DB connections: {metrics.database_connections}'))
        else:
            alerts_to_remove.add('database')
        
        # Update active alerts
        for alert_key in alerts_to_remove:
            self.active_alerts = {alert for alert in self.active_alerts if not alert[0] == alert_key}
        
        for alert in alerts_to_add:
            if alert not in self.active_alerts:
                self.active_alerts.add(alert)
                await self.send_alert(alert)
    
    async def send_alert(self, alert: tuple):
        """Send alert notification (placeholder for actual notification system)"""
        alert_type, severity, message = alert
        timestamp = datetime.now().isoformat()
        
        alert_data = {
            'timestamp': timestamp,
            'type': alert_type,
            'severity': severity,
            'message': message,
            'system': 'icfes_leveling'
        }
        
        # Log alert (in production, this would send to notification system)
        logger.warning(f"PERFORMANCE ALERT [{severity}] {alert_type}: {message}")
        
        # Store alert in cache for dashboard
        cache_key = f"performance_alert:{alert_type}:{timestamp}"
        cache_manager.set(cache_key, alert_data, ttl=86400)  # Store for 24 hours
    
    def record_response_time(self, response_time: float):
        """Record an API response time"""
        self.response_times.append(response_time)
    
    def record_query_performance(self, query_hash: str, execution_time: float):
        """Record database query performance"""
        self.query_performance_stats[query_hash].append(execution_time)
        
        # Keep only last 100 executions per query
        if len(self.query_performance_stats[query_hash]) > 100:
            self.query_performance_stats[query_hash] = self.query_performance_stats[query_hash][-100:]
    
    def generate_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary from recent metrics"""
        if not self.metrics_history:
            return {}
        
        # Get recent metrics (last hour or last 120 points)
        recent_metrics = list(self.metrics_history)[-120:]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'period_minutes': len(recent_metrics) * 0.5,  # Assuming 30s intervals
            'avg_cpu': statistics.mean(m.cpu_usage for m in recent_metrics),
            'max_cpu': max(m.cpu_usage for m in recent_metrics),
            'avg_memory': statistics.mean(m.memory_usage for m in recent_metrics),
            'max_memory': max(m.memory_usage for m in recent_metrics),
            'avg_response_time': statistics.mean(m.response_time_avg for m in recent_metrics),
            'max_response_time': max(m.response_time_avg for m in recent_metrics),
            'avg_cache_hit_rate': statistics.mean(m.cache_hit_rate for m in recent_metrics),
            'min_cache_hit_rate': min(m.cache_hit_rate for m in recent_metrics),
            'avg_db_connections': statistics.mean(m.database_connections for m in recent_metrics if m.database_connections >= 0),
            'max_db_connections': max(m.database_connections for m in recent_metrics if m.database_connections >= 0),
            'active_alerts': len(self.active_alerts),
            'total_data_points': len(recent_metrics)
        }
    
    def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive data for performance dashboard"""
        current_metrics = None
        if self.metrics_history:
            current_metrics = asdict(self.metrics_history[-1])
        
        # Get recent alerts
        recent_alerts = []
        for alert in self.active_alerts:
            recent_alerts.append({
                'type': alert[0],
                'severity': alert[1],
                'message': alert[2],
                'timestamp': datetime.now().isoformat()
            })
        
        # Get query performance stats
        slow_queries = []
        for query_hash, times in self.query_performance_stats.items():
            if times:
                avg_time = statistics.mean(times)
                if avg_time > 1.0:  # Queries taking more than 1 second
                    slow_queries.append({
                        'query_hash': query_hash,
                        'avg_execution_time': avg_time,
                        'executions': len(times),
                        'max_time': max(times)
                    })
        
        slow_queries.sort(key=lambda x: x['avg_execution_time'], reverse=True)
        
        return {
            'current_metrics': current_metrics,
            'summary': self.generate_performance_summary(),
            'active_alerts': recent_alerts,
            'slow_queries': slow_queries[:10],  # Top 10 slow queries
            'system_health': {
                'monitoring_active': self.is_monitoring,
                'metrics_collected': len(self.metrics_history),
                'uptime_hours': (time.time() - self.last_check_time) / 3600 if self.metrics_history else 0
            },
            'recommendations': self.generate_recommendations()
        }
    
    def generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        if not self.metrics_history:
            return recommendations
        
        recent_metrics = list(self.metrics_history)[-20:]  # Last 10 minutes
        
        # CPU recommendations
        avg_cpu = statistics.mean(m.cpu_usage for m in recent_metrics)
        if avg_cpu > 80:
            recommendations.append({
                'type': 'cpu',
                'priority': 'HIGH',
                'title': 'High CPU Usage',
                'description': f'Average CPU usage is {avg_cpu:.1f}%. Consider scaling or optimizing CPU-intensive operations.',
                'action': 'Review slow queries and consider adding more worker processes'
            })
        
        # Memory recommendations
        avg_memory = statistics.mean(m.memory_usage for m in recent_metrics)
        if avg_memory > 85:
            recommendations.append({
                'type': 'memory',
                'priority': 'HIGH',
                'title': 'High Memory Usage',
                'description': f'Average memory usage is {avg_memory:.1f}%. Memory optimization required.',
                'action': 'Review cache sizes and implement memory cleanup procedures'
            })
        
        # Response time recommendations
        avg_response = statistics.mean(m.response_time_avg for m in recent_metrics)
        if avg_response > 1.5:
            recommendations.append({
                'type': 'performance',
                'priority': 'MEDIUM',
                'title': 'Slow Response Times',
                'description': f'Average response time is {avg_response:.2f}s. API optimization needed.',
                'action': 'Review database queries and implement additional caching'
            })
        
        # Cache recommendations
        avg_cache_hit = statistics.mean(m.cache_hit_rate for m in recent_metrics)
        if avg_cache_hit < 70:
            recommendations.append({
                'type': 'cache',
                'priority': 'MEDIUM',
                'title': 'Low Cache Hit Rate',
                'description': f'Cache hit rate is {avg_cache_hit:.1f}%. Cache optimization needed.',
                'action': 'Review cache keys and TTL settings, warm up frequently accessed data'
            })
        
        # Database recommendations
        db_connections = [m.database_connections for m in recent_metrics if m.database_connections >= 0]
        if db_connections:
            avg_db_conn = statistics.mean(db_connections)
            if avg_db_conn > 35:
                recommendations.append({
                    'type': 'database',
                    'priority': 'MEDIUM',
                    'title': 'High Database Connection Usage',
                    'description': f'Average DB connections: {avg_db_conn:.1f}. Connection pool optimization needed.',
                    'action': 'Review connection pool settings and implement connection reuse'
                })
        
        return recommendations
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
        logger.info("Performance monitoring stopped")
    
    def get_metrics_for_timerange(self, start_time: float, end_time: float) -> List[PerformanceMetrics]:
        """Get metrics for a specific time range"""
        return [
            metrics for metrics in self.metrics_history
            if start_time <= metrics.timestamp <= end_time
        ]
    
    def export_metrics_to_json(self, filepath: str):
        """Export metrics history to JSON file"""
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_metrics': len(self.metrics_history),
            'metrics': [asdict(m) for m in self.metrics_history]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(self.metrics_history)} metrics to {filepath}")

# Global performance monitor instance
performance_monitor = AdvancedPerformanceMonitor()

# Performance monitoring middleware
async def performance_monitoring_middleware(request, call_next):
    """Middleware to track API response times"""
    start_time = time.time()
    
    response = await call_next(request)
    
    end_time = time.time()
    response_time = end_time - start_time
    
    # Record response time
    performance_monitor.record_response_time(response_time)
    
    # Log slow requests
    if response_time > 2.0:
        logger.warning(f"Slow request: {request.url} took {response_time:.2f}s")
    
    # Add performance headers
    response.headers["X-Response-Time"] = f"{response_time:.3f}"
    
    return response

# Database query monitoring hook
def monitor_database_query(query_hash: str, execution_time: float):
    """Hook to monitor database query performance"""
    performance_monitor.record_query_performance(query_hash, execution_time)
    
    # Log very slow queries
    if execution_time > 5.0:
        logger.error(f"Very slow query detected: {query_hash} took {execution_time:.2f}s")

# Utility function to start monitoring in background
def start_background_monitoring(interval: float = 30.0):
    """Start performance monitoring in background"""
    async def monitor():
        await performance_monitor.start_monitoring(interval)
    
    # In production, this would be started as a background task
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(monitor())
    
    logger.info("Background performance monitoring started")