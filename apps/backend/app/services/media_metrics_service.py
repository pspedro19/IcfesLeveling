"""
Media Metrics Service for Advanced Analytics and Monitoring
Provides comprehensive metrics collection, analysis, and alerting for media cache system
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, Counter
import statistics

import redis.asyncio as aioredis
from fastapi import BackgroundTasks

from ..core.config import settings
from .media_cache_service import CacheMetrics, CacheStatus

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class MetricType(Enum):
    HIT_RATIO = "hit_ratio"
    RESPONSE_TIME = "response_time"
    BANDWIDTH = "bandwidth"
    ERROR_RATE = "error_rate"
    TOP_REQUESTED = "top_requested"
    CACHE_SIZE = "cache_size"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    metric_type: MetricType
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class BandwidthMetrics:
    """Bandwidth usage metrics"""
    total_bytes_served: int
    total_bytes_cached: int
    compression_savings: int
    bandwidth_efficiency: float
    peak_usage_per_hour: Dict[int, int]

@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    avg_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    cache_hit_ratio: float
    error_rate: float

class MediaMetricsService:
    """Advanced metrics service for media cache system"""
    
    def __init__(self):
        self.redis_pool = None
        self.alert_thresholds = {
            MetricType.HIT_RATIO: 0.7,  # Alert if hit ratio < 70%
            MetricType.ERROR_RATE: 0.05,  # Alert if error rate > 5%
            MetricType.RESPONSE_TIME: 1000,  # Alert if avg response time > 1000ms
        }
        self.active_alerts: Dict[str, Alert] = {}
        
        # Metrics keys
        self.metrics_key_pattern = f"{settings.MEDIA_CACHE_PREFIX}_metrics:{{date}}"
        self.alerts_key = f"{settings.MEDIA_CACHE_PREFIX}_alerts"
        self.hourly_stats_key = f"{settings.MEDIA_CACHE_PREFIX}_hourly_stats"
        
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_pool = aioredis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=False
            )
            logger.info("Metrics service Redis connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize metrics Redis: {e}")
    
    async def get_redis(self) -> aioredis.Redis:
        """Get Redis connection"""
        if not self.redis_pool:
            raise Exception("Redis pool not initialized")
        return aioredis.Redis(connection_pool=self.redis_pool)
    
    async def get_comprehensive_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive metrics for the specified number of days"""
        try:
            redis_conn = await self.get_redis()
            
            # Get metrics for the specified period
            metrics_data = []
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
                metrics_key = self.metrics_key_pattern.format(date=date)
                
                daily_data = await redis_conn.get(metrics_key)
                if daily_data:
                    daily_metrics = json.loads(daily_data)
                    metrics_data.extend(daily_metrics)
            
            if not metrics_data:
                return self._empty_metrics_response()
            
            # Calculate comprehensive metrics
            result = {
                "period": f"{days} days",
                "total_requests": len(metrics_data),
                "date_range": {
                    "start": (datetime.utcnow() - timedelta(days=days-1)).strftime("%Y-%m-%d"),
                    "end": datetime.utcnow().strftime("%Y-%m-%d")
                },
                "cache_performance": await self._calculate_cache_performance(metrics_data),
                "bandwidth_analysis": await self._calculate_bandwidth_metrics(metrics_data),
                "response_time_analysis": await self._calculate_response_time_metrics(metrics_data),
                "top_requested_images": await self._get_detailed_top_requested(metrics_data),
                "image_type_breakdown": await self._get_image_type_breakdown(metrics_data),
                "hourly_patterns": await self._get_hourly_patterns(metrics_data),
                "error_analysis": await self._get_error_analysis(metrics_data),
                "cache_efficiency": await self._calculate_cache_efficiency(metrics_data),
                "alerts": await self._get_active_alerts()
            }
            
            await redis_conn.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting comprehensive metrics: {e}")
            return {"error": str(e)}
    
    def _empty_metrics_response(self) -> Dict[str, Any]:
        """Return empty metrics response when no data available"""
        return {
            "period": "No data",
            "total_requests": 0,
            "cache_performance": {"hit_ratio": 0.0, "miss_ratio": 0.0},
            "bandwidth_analysis": {"total_bytes": 0, "savings": 0},
            "response_time_analysis": {"avg_ms": 0, "p95_ms": 0},
            "top_requested_images": [],
            "image_type_breakdown": {},
            "hourly_patterns": {},
            "error_analysis": {"total_errors": 0, "error_rate": 0.0},
            "cache_efficiency": {"compression_ratio": 1.0, "storage_efficiency": 0.0},
            "alerts": []
        }
    
    async def _calculate_cache_performance(self, metrics_data: List[Dict]) -> Dict[str, Any]:
        """Calculate detailed cache performance metrics"""
        total_requests = len(metrics_data)
        if total_requests == 0:
            return {"hit_ratio": 0.0, "miss_ratio": 0.0, "error_ratio": 0.0}
        
        hits = sum(1 for m in metrics_data if m.get('status') == CacheStatus.HIT.value)
        misses = sum(1 for m in metrics_data if m.get('status') == CacheStatus.MISS.value)
        errors = sum(1 for m in metrics_data if m.get('status') == CacheStatus.ERROR.value)
        expired = sum(1 for m in metrics_data if m.get('status') == CacheStatus.EXPIRED.value)
        
        # Calculate hit ratio trend (last 24 hours vs previous 24 hours)
        now = datetime.utcnow()
        last_24h = [m for m in metrics_data 
                   if datetime.fromisoformat(m.get('timestamp', now.isoformat())) > now - timedelta(hours=24)]
        prev_24h = [m for m in metrics_data 
                   if now - timedelta(hours=48) < datetime.fromisoformat(m.get('timestamp', now.isoformat())) <= now - timedelta(hours=24)]
        
        current_hit_ratio = 0.0
        previous_hit_ratio = 0.0
        
        if last_24h:
            current_hits = sum(1 for m in last_24h if m.get('status') == CacheStatus.HIT.value)
            current_hit_ratio = current_hits / len(last_24h)
        
        if prev_24h:
            previous_hits = sum(1 for m in prev_24h if m.get('status') == CacheStatus.HIT.value)
            previous_hit_ratio = previous_hits / len(prev_24h)
        
        trend = current_hit_ratio - previous_hit_ratio
        
        return {
            "total_requests": total_requests,
            "cache_hits": hits,
            "cache_misses": misses,
            "cache_errors": errors,
            "cache_expired": expired,
            "hit_ratio": round(hits / total_requests, 4),
            "miss_ratio": round(misses / total_requests, 4),
            "error_ratio": round(errors / total_requests, 4),
            "expired_ratio": round(expired / total_requests, 4),
            "hit_ratio_trend": {
                "current_24h": round(current_hit_ratio, 4),
                "previous_24h": round(previous_hit_ratio, 4),
                "change": round(trend, 4),
                "trend_direction": "improving" if trend > 0 else "declining" if trend < 0 else "stable"
            }
        }
    
    async def _calculate_bandwidth_metrics(self, metrics_data: List[Dict]) -> BandwidthMetrics:
        """Calculate bandwidth usage and savings metrics"""
        total_bytes_served = sum(m.get('file_size', 0) for m in metrics_data)
        total_bytes_cached = sum(m.get('cache_size', 0) for m in metrics_data if m.get('cache_size'))
        
        compression_savings = 0
        compressed_items = 0
        
        for metric in metrics_data:
            if metric.get('cache_size') and metric.get('file_size'):
                compression_savings += metric['file_size'] - metric['cache_size']
                compressed_items += 1
        
        # Calculate peak usage per hour
        hourly_usage = defaultdict(int)
        for metric in metrics_data:
            timestamp = datetime.fromisoformat(metric.get('timestamp', datetime.utcnow().isoformat()))
            hour = timestamp.hour
            hourly_usage[hour] += metric.get('file_size', 0)
        
        bandwidth_efficiency = 0.0
        if total_bytes_served > 0:
            bandwidth_efficiency = compression_savings / total_bytes_served
        
        return BandwidthMetrics(
            total_bytes_served=total_bytes_served,
            total_bytes_cached=total_bytes_cached,
            compression_savings=compression_savings,
            bandwidth_efficiency=bandwidth_efficiency,
            peak_usage_per_hour=dict(hourly_usage)
        )
    
    async def _calculate_response_time_metrics(self, metrics_data: List[Dict]) -> PerformanceMetrics:
        """Calculate detailed response time metrics"""
        response_times = [m.get('response_time_ms', 0) for m in metrics_data if m.get('response_time_ms')]
        
        if not response_times:
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0)
        
        # Calculate percentiles
        response_times.sort()
        p50 = statistics.median(response_times)
        p95 = response_times[int(len(response_times) * 0.95)] if len(response_times) > 1 else response_times[0]
        p99 = response_times[int(len(response_times) * 0.99)] if len(response_times) > 1 else response_times[0]
        
        # Calculate requests per second (based on time range)
        if metrics_data:
            timestamps = [datetime.fromisoformat(m.get('timestamp', datetime.utcnow().isoformat())) for m in metrics_data]
            time_range = (max(timestamps) - min(timestamps)).total_seconds()
            requests_per_second = len(metrics_data) / max(time_range, 1)
        else:
            requests_per_second = 0
        
        # Calculate cache hit ratio and error rate
        total_requests = len(metrics_data)
        hits = sum(1 for m in metrics_data if m.get('status') == CacheStatus.HIT.value)
        errors = sum(1 for m in metrics_data if m.get('status') == CacheStatus.ERROR.value)
        
        cache_hit_ratio = hits / total_requests if total_requests > 0 else 0
        error_rate = errors / total_requests if total_requests > 0 else 0
        
        return PerformanceMetrics(
            avg_response_time=statistics.mean(response_times),
            p50_response_time=p50,
            p95_response_time=p95,
            p99_response_time=p99,
            requests_per_second=requests_per_second,
            cache_hit_ratio=cache_hit_ratio,
            error_rate=error_rate
        )
    
    async def _get_detailed_top_requested(self, metrics_data: List[Dict]) -> List[Dict[str, Any]]:
        """Get detailed analysis of top requested images"""
        # Group by cache key
        key_stats = defaultdict(lambda: {
            'requests': 0,
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'total_response_time': 0,
            'total_file_size': 0,
            'image_type': 'unknown',
            'last_requested': None
        })
        
        for metric in metrics_data:
            key = metric.get('key', 'unknown')
            stats = key_stats[key]
            
            stats['requests'] += 1
            stats['total_response_time'] += metric.get('response_time_ms', 0)
            stats['total_file_size'] += metric.get('file_size', 0)
            stats['image_type'] = metric.get('image_type', 'unknown')
            
            timestamp = datetime.fromisoformat(metric.get('timestamp', datetime.utcnow().isoformat()))
            if not stats['last_requested'] or timestamp > stats['last_requested']:
                stats['last_requested'] = timestamp
            
            status = metric.get('status')
            if status == CacheStatus.HIT.value:
                stats['hits'] += 1
            elif status == CacheStatus.MISS.value:
                stats['misses'] += 1
            elif status == CacheStatus.ERROR.value:
                stats['errors'] += 1
        
        # Sort by request count and get top N
        sorted_stats = sorted(
            key_stats.items(),
            key=lambda x: x[1]['requests'],
            reverse=True
        )[:settings.MEDIA_METRICS_TOP_LIMIT]
        
        result = []
        for key, stats in sorted_stats:
            avg_response_time = stats['total_response_time'] / stats['requests'] if stats['requests'] > 0 else 0
            avg_file_size = stats['total_file_size'] / stats['requests'] if stats['requests'] > 0 else 0
            hit_ratio = stats['hits'] / stats['requests'] if stats['requests'] > 0 else 0
            
            result.append({
                'cache_key': key,
                'image_type': stats['image_type'],
                'total_requests': stats['requests'],
                'cache_hits': stats['hits'],
                'cache_misses': stats['misses'],
                'errors': stats['errors'],
                'hit_ratio': round(hit_ratio, 4),
                'avg_response_time_ms': round(avg_response_time, 2),
                'avg_file_size_bytes': int(avg_file_size),
                'last_requested': stats['last_requested'].isoformat() if stats['last_requested'] else None,
                'performance_score': self._calculate_performance_score(hit_ratio, avg_response_time, stats['errors'] / stats['requests'] if stats['requests'] > 0 else 0)
            })
        
        return result
    
    def _calculate_performance_score(self, hit_ratio: float, avg_response_time: float, error_rate: float) -> float:
        """Calculate a performance score for an image (0-100)"""
        # Higher hit ratio = better score
        hit_score = hit_ratio * 40
        
        # Lower response time = better score (normalize to 0-30)
        response_score = max(0, 30 - (avg_response_time / 100))
        
        # Lower error rate = better score
        error_score = max(0, 30 - (error_rate * 300))
        
        return round(hit_score + response_score + error_score, 2)
    
    async def _get_image_type_breakdown(self, metrics_data: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Get breakdown of metrics by image type"""
        type_stats = defaultdict(lambda: {
            'requests': 0,
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'total_response_time': 0,
            'total_file_size': 0,
            'total_cache_size': 0
        })
        
        for metric in metrics_data:
            img_type = metric.get('image_type', 'unknown')
            stats = type_stats[img_type]
            
            stats['requests'] += 1
            stats['total_response_time'] += metric.get('response_time_ms', 0)
            stats['total_file_size'] += metric.get('file_size', 0)
            stats['total_cache_size'] += metric.get('cache_size', 0)
            
            status = metric.get('status')
            if status == CacheStatus.HIT.value:
                stats['hits'] += 1
            elif status == CacheStatus.MISS.value:
                stats['misses'] += 1
            elif status == CacheStatus.ERROR.value:
                stats['errors'] += 1
        
        # Calculate ratios and averages
        result = {}
        for img_type, stats in type_stats.items():
            requests = stats['requests']
            if requests > 0:
                result[img_type] = {
                    'total_requests': requests,
                    'cache_hits': stats['hits'],
                    'cache_misses': stats['misses'],
                    'errors': stats['errors'],
                    'hit_ratio': round(stats['hits'] / requests, 4),
                    'error_ratio': round(stats['errors'] / requests, 4),
                    'avg_response_time_ms': round(stats['total_response_time'] / requests, 2),
                    'avg_file_size_bytes': int(stats['total_file_size'] / requests),
                    'total_bandwidth_bytes': stats['total_file_size'],
                    'compression_savings_bytes': stats['total_file_size'] - stats['total_cache_size']
                }
        
        return result
    
    async def _get_hourly_patterns(self, metrics_data: List[Dict]) -> Dict[str, Any]:
        """Get hourly usage patterns"""
        hourly_requests = defaultdict(int)
        hourly_bandwidth = defaultdict(int)
        hourly_response_times = defaultdict(list)
        
        for metric in metrics_data:
            timestamp = datetime.fromisoformat(metric.get('timestamp', datetime.utcnow().isoformat()))
            hour = timestamp.hour
            
            hourly_requests[hour] += 1
            hourly_bandwidth[hour] += metric.get('file_size', 0)
            hourly_response_times[hour].append(metric.get('response_time_ms', 0))
        
        # Calculate hourly averages
        hourly_avg_response = {}
        for hour, times in hourly_response_times.items():
            if times:
                hourly_avg_response[hour] = statistics.mean(times)
        
        # Find peak hours
        peak_request_hour = max(hourly_requests.items(), key=lambda x: x[1])[0] if hourly_requests else 0
        peak_bandwidth_hour = max(hourly_bandwidth.items(), key=lambda x: x[1])[0] if hourly_bandwidth else 0
        
        return {
            'requests_by_hour': dict(hourly_requests),
            'bandwidth_by_hour': dict(hourly_bandwidth),
            'avg_response_time_by_hour': hourly_avg_response,
            'peak_request_hour': peak_request_hour,
            'peak_bandwidth_hour': peak_bandwidth_hour,
            'total_peak_requests': hourly_requests[peak_request_hour] if hourly_requests else 0,
            'total_peak_bandwidth': hourly_bandwidth[peak_bandwidth_hour] if hourly_bandwidth else 0
        }
    
    async def _get_error_analysis(self, metrics_data: List[Dict]) -> Dict[str, Any]:
        """Get detailed error analysis"""
        total_errors = sum(1 for m in metrics_data if m.get('status') == CacheStatus.ERROR.value)
        total_requests = len(metrics_data)
        error_rate = total_errors / total_requests if total_requests > 0 else 0
        
        # Group errors by image type
        error_by_type = defaultdict(int)
        for metric in metrics_data:
            if metric.get('status') == CacheStatus.ERROR.value:
                error_by_type[metric.get('image_type', 'unknown')] += 1
        
        # Recent error trend (last 4 hours vs previous 4 hours)
        now = datetime.utcnow()
        recent_errors = sum(1 for m in metrics_data 
                          if m.get('status') == CacheStatus.ERROR.value 
                          and datetime.fromisoformat(m.get('timestamp', now.isoformat())) > now - timedelta(hours=4))
        
        prev_errors = sum(1 for m in metrics_data 
                        if m.get('status') == CacheStatus.ERROR.value 
                        and now - timedelta(hours=8) < datetime.fromisoformat(m.get('timestamp', now.isoformat())) <= now - timedelta(hours=4))
        
        error_trend = recent_errors - prev_errors
        
        return {
            'total_errors': total_errors,
            'error_rate': round(error_rate, 4),
            'errors_by_image_type': dict(error_by_type),
            'recent_error_trend': {
                'last_4h_errors': recent_errors,
                'prev_4h_errors': prev_errors,
                'trend': 'increasing' if error_trend > 0 else 'decreasing' if error_trend < 0 else 'stable',
                'change': error_trend
            }
        }
    
    async def _calculate_cache_efficiency(self, metrics_data: List[Dict]) -> Dict[str, Any]:
        """Calculate cache efficiency metrics"""
        compressed_items = [m for m in metrics_data if m.get('compression_ratio') and m.get('compression_ratio') < 1.0]
        
        if not compressed_items:
            return {
                'compression_enabled': False,
                'avg_compression_ratio': 1.0,
                'storage_efficiency': 0.0,
                'space_saved_bytes': 0
            }
        
        compression_ratios = [m['compression_ratio'] for m in compressed_items]
        total_original_size = sum(m.get('file_size', 0) for m in compressed_items)
        total_compressed_size = sum(m.get('cache_size', 0) for m in compressed_items)
        
        space_saved = total_original_size - total_compressed_size
        storage_efficiency = space_saved / total_original_size if total_original_size > 0 else 0
        
        return {
            'compression_enabled': True,
            'total_compressed_items': len(compressed_items),
            'avg_compression_ratio': round(statistics.mean(compression_ratios), 4),
            'best_compression_ratio': round(min(compression_ratios), 4),
            'worst_compression_ratio': round(max(compression_ratios), 4),
            'storage_efficiency': round(storage_efficiency, 4),
            'space_saved_bytes': space_saved,
            'space_saved_percentage': round(storage_efficiency * 100, 2)
        }
    
    async def check_and_create_alerts(self, metrics_data: List[Dict]):
        """Check metrics and create alerts if thresholds are exceeded"""
        try:
            redis_conn = await self.get_redis()
            
            # Calculate current metrics for alerting
            if not metrics_data:
                return
            
            total_requests = len(metrics_data)
            hits = sum(1 for m in metrics_data if m.get('status') == CacheStatus.HIT.value)
            errors = sum(1 for m in metrics_data if m.get('status') == CacheStatus.ERROR.value)
            response_times = [m.get('response_time_ms', 0) for m in metrics_data]
            
            hit_ratio = hits / total_requests if total_requests > 0 else 0
            error_rate = errors / total_requests if total_requests > 0 else 0
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            # Check hit ratio threshold
            if hit_ratio < self.alert_thresholds[MetricType.HIT_RATIO]:
                await self._create_alert(
                    MetricType.HIT_RATIO,
                    AlertSeverity.WARNING,
                    f"Cache hit ratio is below threshold: {hit_ratio:.2%} < {self.alert_thresholds[MetricType.HIT_RATIO]:.2%}",
                    hit_ratio,
                    self.alert_thresholds[MetricType.HIT_RATIO]
                )
            
            # Check error rate threshold
            if error_rate > self.alert_thresholds[MetricType.ERROR_RATE]:
                await self._create_alert(
                    MetricType.ERROR_RATE,
                    AlertSeverity.CRITICAL if error_rate > 0.1 else AlertSeverity.WARNING,
                    f"Error rate is above threshold: {error_rate:.2%} > {self.alert_thresholds[MetricType.ERROR_RATE]:.2%}",
                    error_rate,
                    self.alert_thresholds[MetricType.ERROR_RATE]
                )
            
            # Check response time threshold
            if avg_response_time > self.alert_thresholds[MetricType.RESPONSE_TIME]:
                await self._create_alert(
                    MetricType.RESPONSE_TIME,
                    AlertSeverity.WARNING,
                    f"Average response time is above threshold: {avg_response_time:.1f}ms > {self.alert_thresholds[MetricType.RESPONSE_TIME]}ms",
                    avg_response_time,
                    self.alert_thresholds[MetricType.RESPONSE_TIME]
                )
            
            await redis_conn.close()
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    async def _create_alert(self, metric_type: MetricType, severity: AlertSeverity, 
                          message: str, value: float, threshold: float):
        """Create a new alert"""
        try:
            alert_id = f"{metric_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            alert = Alert(
                id=alert_id,
                metric_type=metric_type,
                severity=severity,
                message=message,
                value=value,
                threshold=threshold,
                timestamp=datetime.utcnow()
            )
            
            # Store in memory
            self.active_alerts[alert_id] = alert
            
            # Store in Redis
            redis_conn = await self.get_redis()
            alerts_data = await redis_conn.get(self.alerts_key)
            
            if alerts_data:
                stored_alerts = json.loads(alerts_data)
            else:
                stored_alerts = []
            
            stored_alerts.append(asdict(alert))
            
            # Keep only recent alerts (last 7 days)
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            stored_alerts = [
                a for a in stored_alerts 
                if datetime.fromisoformat(a['timestamp']) > cutoff_date
            ]
            
            await redis_conn.setex(
                self.alerts_key,
                86400 * 7,  # 7 days
                json.dumps(stored_alerts, default=str)
            )
            
            await redis_conn.close()
            
            logger.warning(f"Alert created: {alert.message}")
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts"""
        try:
            redis_conn = await self.get_redis()
            alerts_data = await redis_conn.get(self.alerts_key)
            await redis_conn.close()
            
            if not alerts_data:
                return []
            
            stored_alerts = json.loads(alerts_data)
            
            # Filter active alerts (not resolved and recent)
            active_alerts = [
                alert for alert in stored_alerts
                if not alert.get('resolved', False)
                and datetime.fromisoformat(alert['timestamp']) > datetime.utcnow() - timedelta(hours=24)
            ]
            
            return active_alerts
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        try:
            redis_conn = await self.get_redis()
            alerts_data = await redis_conn.get(self.alerts_key)
            
            if not alerts_data:
                return False
            
            stored_alerts = json.loads(alerts_data)
            
            # Find and resolve alert
            for alert in stored_alerts:
                if alert['id'] == alert_id:
                    alert['resolved'] = True
                    alert['resolved_at'] = datetime.utcnow().isoformat()
                    break
            else:
                return False
            
            # Update stored alerts
            await redis_conn.setex(
                self.alerts_key,
                86400 * 7,
                json.dumps(stored_alerts, default=str)
            )
            
            # Remove from active alerts
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
            
            await redis_conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False

# Global instance
media_metrics_service = MediaMetricsService()