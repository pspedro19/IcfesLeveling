"""
Media Background Service
Handles cache invalidation, prefetching, cleanup, and maintenance tasks
"""

import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import logging
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

from sqlalchemy.orm import Session
from celery import Celery

from ..core.config import settings
from ..core.database import get_db
from ..services.media_cache_service import media_cache_service
from ..services.media_metrics_service import media_metrics_service
from ..services.image_mapping_service import image_mapping_service

logger = logging.getLogger(__name__)

class TaskType(Enum):
    CACHE_INVALIDATION = "cache_invalidation"
    PREFETCH = "prefetch"
    CLEANUP = "cleanup"
    METRICS_FLUSH = "metrics_flush"
    ALERT_CHECK = "alert_check"
    HEALTH_CHECK = "health_check"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class BackgroundTask:
    """Background task definition"""
    id: str
    task_type: TaskType
    priority: TaskPriority
    scheduled_at: datetime
    parameters: Dict[str, Any]
    retries: int = 0
    max_retries: int = 3
    status: str = "pending"
    error: Optional[str] = None

class MediaBackgroundService:
    """Service for managing background tasks related to media cache"""
    
    def __init__(self):
        self.running_tasks: Dict[str, BackgroundTask] = {}
        self.task_queue: List[BackgroundTask] = []
        self.is_running = False
        
        # File change tracking
        self.file_checksums: Dict[str, str] = {}
        self.last_scan: Optional[datetime] = None
        
        # Performance tracking
        self.task_performance: Dict[TaskType, List[float]] = {}
        
        # Initialize Celery for production background tasks
        self.celery_app = self._init_celery()
    
    def _init_celery(self) -> Optional[Celery]:
        """Initialize Celery for production background tasks"""
        try:
            if settings.ENVIRONMENT == "production":
                celery_app = Celery(
                    'media_tasks',
                    broker=settings.REDIS_URL,
                    backend=settings.REDIS_URL
                )
                
                celery_app.conf.update(
                    task_serializer='json',
                    accept_content=['json'],
                    result_serializer='json',
                    timezone='UTC',
                    enable_utc=True,
                    task_routes={
                        'media.cache_invalidation': {'queue': 'cache'},
                        'media.prefetch': {'queue': 'prefetch'},
                        'media.cleanup': {'queue': 'maintenance'},
                    }
                )
                
                return celery_app
        except Exception as e:
            logger.warning(f"Failed to initialize Celery: {e}")
        
        return None
    
    async def start_background_service(self):
        """Start the background service"""
        if self.is_running:
            logger.warning("Background service is already running")
            return
        
        self.is_running = True
        logger.info("Starting media background service")
        
        # Start main task loop
        asyncio.create_task(self._main_task_loop())
        
        # Schedule periodic tasks
        await self._schedule_periodic_tasks()
        
        logger.info("Media background service started")
    
    async def stop_background_service(self):
        """Stop the background service"""
        self.is_running = False
        
        # Wait for running tasks to complete (with timeout)
        timeout = 30  # seconds
        start_time = datetime.utcnow()
        
        while self.running_tasks and (datetime.utcnow() - start_time).seconds < timeout:
            await asyncio.sleep(1)
        
        if self.running_tasks:
            logger.warning(f"Force stopping service with {len(self.running_tasks)} running tasks")
        
        logger.info("Media background service stopped")
    
    async def _main_task_loop(self):
        """Main task processing loop"""
        while self.is_running:
            try:
                # Process pending tasks
                await self._process_task_queue()
                
                # Sleep for a short interval
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in main task loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _process_task_queue(self):
        """Process tasks in the queue"""
        if not self.task_queue:
            return
        
        # Sort by priority and scheduled time
        self.task_queue.sort(
            key=lambda t: (t.priority.value, t.scheduled_at),
            reverse=True
        )
        
        # Process tasks that are due
        now = datetime.utcnow()
        due_tasks = [t for t in self.task_queue if t.scheduled_at <= now]
        
        for task in due_tasks[:5]:  # Process up to 5 tasks at once
            if task.id not in self.running_tasks:
                self.task_queue.remove(task)
                self.running_tasks[task.id] = task
                
                # Execute task
                asyncio.create_task(self._execute_task(task))
    
    async def _execute_task(self, task: BackgroundTask):
        """Execute a background task"""
        start_time = datetime.utcnow()
        
        try:
            logger.debug(f"Executing task: {task.id} ({task.task_type.value})")
            
            task.status = "running"
            
            # Execute based on task type
            if task.task_type == TaskType.CACHE_INVALIDATION:
                await self._handle_cache_invalidation(task)
            elif task.task_type == TaskType.PREFETCH:
                await self._handle_prefetch(task)
            elif task.task_type == TaskType.CLEANUP:
                await self._handle_cleanup(task)
            elif task.task_type == TaskType.METRICS_FLUSH:
                await self._handle_metrics_flush(task)
            elif task.task_type == TaskType.ALERT_CHECK:
                await self._handle_alert_check(task)
            elif task.task_type == TaskType.HEALTH_CHECK:
                await self._handle_health_check(task)
            
            task.status = "completed"
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Track performance
            if task.task_type not in self.task_performance:
                self.task_performance[task.task_type] = []
            self.task_performance[task.task_type].append(execution_time)
            
            logger.debug(f"Task {task.id} completed in {execution_time:.2f}s")
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.retries += 1
            
            logger.error(f"Task {task.id} failed: {e}")
            
            # Retry if within limit
            if task.retries < task.max_retries:
                task.status = "pending"
                task.scheduled_at = datetime.utcnow() + timedelta(minutes=task.retries * 2)
                self.task_queue.append(task)
                logger.info(f"Rescheduling task {task.id} for retry {task.retries}")
        
        finally:
            # Remove from running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
    
    async def _handle_cache_invalidation(self, task: BackgroundTask):
        """Handle cache invalidation tasks"""
        pattern = task.parameters.get('pattern')
        if not pattern:
            raise ValueError("Pattern required for cache invalidation")
        
        count = await media_cache_service.invalidate_cache(pattern)
        logger.info(f"Invalidated {count} cache entries matching pattern: {pattern}")
    
    async def _handle_prefetch(self, task: BackgroundTask):
        """Handle prefetch tasks"""
        image_type = task.parameters.get('image_type')
        image_paths = task.parameters.get('image_paths', [])
        
        if not image_type or not image_paths:
            raise ValueError("Image type and paths required for prefetch")
        
        prefetch_count = 0
        for image_path in image_paths:
            try:
                # Check if already cached
                cached = await media_cache_service.get_cached_media(image_type, image_path)
                if not cached:
                    # Load and cache the image
                    await self._prefetch_single_image(image_type, image_path)
                    prefetch_count += 1
                    
                    # Limit prefetch rate
                    if prefetch_count >= 10:
                        await asyncio.sleep(0.1)
                        prefetch_count = 0
                        
            except Exception as e:
                logger.warning(f"Failed to prefetch {image_type}/{image_path}: {e}")
        
        logger.info(f"Prefetch task completed for {len(image_paths)} images")
    
    async def _prefetch_single_image(self, image_type: str, image_path: str):
        """Prefetch a single image"""
        try:
            # This would typically:
            # 1. Resolve the image path using image_mapping_service
            # 2. Load the image data
            # 3. Cache it using media_cache_service
            
            # For now, we'll just log the prefetch attempt
            logger.debug(f"Prefetching: {image_type}/{image_path}")
            
        except Exception as e:
            logger.error(f"Error prefetching {image_type}/{image_path}: {e}")
    
    async def _handle_cleanup(self, task: BackgroundTask):
        """Handle cleanup tasks"""
        cleanup_type = task.parameters.get('type', 'expired')
        
        if cleanup_type == 'expired':
            await self._cleanup_expired_cache()
        elif cleanup_type == 'unused':
            await self._cleanup_unused_cache()
        elif cleanup_type == 'oversized':
            await self._cleanup_oversized_cache()
        elif cleanup_type == 'metrics':
            await self._cleanup_old_metrics()
    
    async def _cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        try:
            # This would typically involve scanning Redis keys
            # and removing expired entries
            logger.debug("Cleaning up expired cache entries")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")
    
    async def _cleanup_unused_cache(self):
        """Clean up unused cache entries based on access patterns"""
        try:
            # Get cache statistics
            stats = await media_cache_service.get_cache_statistics()
            
            # Identify least accessed entries
            # This would involve more complex logic to determine unused entries
            logger.debug("Cleaning up unused cache entries")
            
        except Exception as e:
            logger.error(f"Error cleaning up unused cache: {e}")
    
    async def _cleanup_oversized_cache(self):
        """Clean up oversized cache to maintain size limits"""
        try:
            # Monitor Redis memory usage
            # Remove large or least important entries if needed
            logger.debug("Cleaning up oversized cache entries")
            
        except Exception as e:
            logger.error(f"Error cleaning up oversized cache: {e}")
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics data"""
        try:
            # Remove metrics older than retention period
            cutoff_date = datetime.utcnow() - timedelta(days=settings.MEDIA_METRICS_RETENTION_DAYS)
            logger.info(f"Cleaning up metrics older than {cutoff_date}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
    
    async def _handle_metrics_flush(self, task: BackgroundTask):
        """Handle metrics flush tasks"""
        try:
            await media_cache_service._flush_metrics()
            logger.debug("Metrics flushed successfully")
            
        except Exception as e:
            logger.error(f"Error flushing metrics: {e}")
    
    async def _handle_alert_check(self, task: BackgroundTask):
        """Handle alert checking tasks"""
        try:
            # Get recent metrics
            metrics = await media_metrics_service.get_comprehensive_metrics(1)
            
            # This would involve analyzing metrics and creating alerts
            logger.debug("Alert check completed")
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    async def _handle_health_check(self, task: BackgroundTask):
        """Handle health check tasks"""
        try:
            health = await media_cache_service.health_check()
            
            if not health.get('healthy', False):
                logger.warning(f"Cache health check failed: {health}")
                
                # Schedule recovery tasks if needed
                await self.schedule_task(
                    TaskType.CLEANUP,
                    TaskPriority.HIGH,
                    {'type': 'expired'},
                    delay_seconds=60
                )
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
    
    async def _schedule_periodic_tasks(self):
        """Schedule periodic background tasks"""
        now = datetime.utcnow()
        
        # Cache invalidation check (every minute)
        await self.schedule_task(
            TaskType.CACHE_INVALIDATION,
            TaskPriority.NORMAL,
            {'pattern': 'expired:*'},
            delay_seconds=60
        )
        
        # Metrics flush (every 5 minutes)
        await self.schedule_task(
            TaskType.METRICS_FLUSH,
            TaskPriority.NORMAL,
            {},
            delay_seconds=300
        )
        
        # Health check (every 10 minutes)
        await self.schedule_task(
            TaskType.HEALTH_CHECK,
            TaskPriority.NORMAL,
            {},
            delay_seconds=600
        )
        
        # Cleanup tasks (every hour)
        await self.schedule_task(
            TaskType.CLEANUP,
            TaskPriority.LOW,
            {'type': 'expired'},
            delay_seconds=3600
        )
        
        # Alert check (every 15 minutes)
        await self.schedule_task(
            TaskType.ALERT_CHECK,
            TaskPriority.NORMAL,
            {},
            delay_seconds=900
        )
    
    async def schedule_task(self, task_type: TaskType, priority: TaskPriority,
                          parameters: Dict[str, Any], delay_seconds: int = 0) -> str:
        """Schedule a background task"""
        task_id = f"{task_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(parameters)) % 10000}"
        
        scheduled_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        
        task = BackgroundTask(
            id=task_id,
            task_type=task_type,
            priority=priority,
            scheduled_at=scheduled_at,
            parameters=parameters
        )
        
        self.task_queue.append(task)
        logger.debug(f"Scheduled task: {task_id} for {scheduled_at}")
        
        return task_id
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        # Remove from queue
        for i, task in enumerate(self.task_queue):
            if task.id == task_id:
                del self.task_queue[i]
                logger.info(f"Cancelled task: {task_id}")
                return True
        
        # Check if running
        if task_id in self.running_tasks:
            logger.warning(f"Cannot cancel running task: {task_id}")
            return False
        
        return False
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task"""
        # Check running tasks
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            return {
                'id': task.id,
                'type': task.task_type.value,
                'status': task.status,
                'scheduled_at': task.scheduled_at.isoformat(),
                'retries': task.retries,
                'error': task.error
            }
        
        # Check queued tasks
        for task in self.task_queue:
            if task.id == task_id:
                return {
                    'id': task.id,
                    'type': task.task_type.value,
                    'status': task.status,
                    'scheduled_at': task.scheduled_at.isoformat(),
                    'retries': task.retries,
                    'error': task.error
                }
        
        return None
    
    async def get_service_statistics(self) -> Dict[str, Any]:
        """Get background service statistics"""
        return {
            'is_running': self.is_running,
            'queued_tasks': len(self.task_queue),
            'running_tasks': len(self.running_tasks),
            'task_performance': {
                task_type.value: {
                    'count': len(times),
                    'avg_time': sum(times) / len(times) if times else 0,
                    'min_time': min(times) if times else 0,
                    'max_time': max(times) if times else 0
                }
                for task_type, times in self.task_performance.items()
            },
            'queue_by_type': {
                task_type.value: len([t for t in self.task_queue if t.task_type == task_type])
                for task_type in TaskType
            },
            'queue_by_priority': {
                priority.name: len([t for t in self.task_queue if t.priority == priority])
                for priority in TaskPriority
            }
        }
    
    def setup_celery_tasks(self):
        """Setup Celery tasks for production use"""
        if not self.celery_app:
            return
        
        @self.celery_app.task(name='media.cache_invalidation')
        def cache_invalidation_task(pattern: str):
            """Celery task for cache invalidation"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(media_cache_service.invalidate_cache(pattern))
            finally:
                loop.close()
        
        @self.celery_app.task(name='media.cleanup')
        def cleanup_task(cleanup_type: str = 'expired'):
            """Celery task for cleanup"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Run cleanup based on type
                if cleanup_type == 'expired':
                    loop.run_until_complete(self._cleanup_expired_cache())
                elif cleanup_type == 'metrics':
                    loop.run_until_complete(self._cleanup_old_metrics())
            finally:
                loop.close()
        
        @self.celery_app.task(name='media.health_check')
        def health_check_task():
            """Celery task for health checks"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                health = loop.run_until_complete(media_cache_service.health_check())
                return health
            finally:
                loop.close()

# Global instance
media_background_service = MediaBackgroundService()