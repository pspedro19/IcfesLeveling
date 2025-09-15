"""
Automatic Recovery Service
Implements automatic recovery mechanisms for system components and services
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.database import get_db, engine
from ..core.cache_manager import cache_manager
from ..models.error_log import RecoveryAction, SystemHealth
from .graceful_degradation_service import graceful_degradation_service

logger = logging.getLogger(__name__)


class RecoveryActionType(Enum):
    """Types of recovery actions that can be performed"""
    CACHE_INVALIDATION = "cache_invalidation"
    SERVICE_RESTART = "service_restart"
    CIRCUIT_BREAKER_RESET = "circuit_breaker_reset"
    DATABASE_RECONNECT = "database_reconnect"
    MEMORY_CLEANUP = "memory_cleanup"
    LOG_ROTATION = "log_rotation"
    HEALTH_CHECK = "health_check"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"


@dataclass
class RecoveryRule:
    """Rule definition for automatic recovery"""
    trigger_condition: str  # Error pattern or condition
    recovery_action: RecoveryActionType
    cooldown_seconds: int = 300  # 5 minutes default cooldown
    max_attempts: int = 3
    priority: int = 1  # 1 = highest priority
    enabled: bool = True
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class RecoveryResult:
    """Result of a recovery action"""
    success: bool
    action_type: RecoveryActionType
    duration_seconds: float
    message: str
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class AutomaticRecoveryService:
    """
    Service that automatically detects system issues and applies recovery actions
    """
    
    def __init__(self):
        self.recovery_rules: List[RecoveryRule] = []
        self.recovery_history: Dict[str, List[datetime]] = {}
        self.active_recoveries: Dict[str, datetime] = {}
        self.recovery_handlers: Dict[RecoveryActionType, Callable] = {}
        self.monitoring_active = False
        self.monitoring_task = None
        
        self._initialize_recovery_rules()
        self._register_recovery_handlers()
    
    def _initialize_recovery_rules(self):
        """Initialize default recovery rules"""
        self.recovery_rules = [
            # High priority rules
            RecoveryRule(
                trigger_condition="database_connection_failed",
                recovery_action=RecoveryActionType.DATABASE_RECONNECT,
                cooldown_seconds=60,
                max_attempts=5,
                priority=1,
                parameters={"timeout": 30, "retry_count": 3}
            ),
            
            RecoveryRule(
                trigger_condition="memory_usage_high",
                recovery_action=RecoveryActionType.MEMORY_CLEANUP,
                cooldown_seconds=300,
                max_attempts=3,
                priority=1,
                parameters={"threshold_mb": 1000}
            ),
            
            # Medium priority rules
            RecoveryRule(
                trigger_condition="cache_errors_high",
                recovery_action=RecoveryActionType.CACHE_INVALIDATION,
                cooldown_seconds=120,
                max_attempts=3,
                priority=2,
                parameters={"pattern": "*", "force": True}
            ),
            
            RecoveryRule(
                trigger_condition="circuit_breaker_open",
                recovery_action=RecoveryActionType.CIRCUIT_BREAKER_RESET,
                cooldown_seconds=300,
                max_attempts=2,
                priority=2
            ),
            
            # Lower priority rules
            RecoveryRule(
                trigger_condition="error_rate_high",
                recovery_action=RecoveryActionType.GRACEFUL_DEGRADATION,
                cooldown_seconds=180,
                max_attempts=1,
                priority=3,
                parameters={"services": ["ai_service", "external_apis"]}
            ),
            
            RecoveryRule(
                trigger_condition="log_files_large",
                recovery_action=RecoveryActionType.LOG_ROTATION,
                cooldown_seconds=3600,  # 1 hour
                max_attempts=1,
                priority=4,
                parameters={"max_size_mb": 100}
            )
        ]
    
    def _register_recovery_handlers(self):
        """Register handlers for different recovery action types"""
        self.recovery_handlers = {
            RecoveryActionType.CACHE_INVALIDATION: self._handle_cache_invalidation,
            RecoveryActionType.SERVICE_RESTART: self._handle_service_restart,
            RecoveryActionType.CIRCUIT_BREAKER_RESET: self._handle_circuit_breaker_reset,
            RecoveryActionType.DATABASE_RECONNECT: self._handle_database_reconnect,
            RecoveryActionType.MEMORY_CLEANUP: self._handle_memory_cleanup,
            RecoveryActionType.LOG_ROTATION: self._handle_log_rotation,
            RecoveryActionType.HEALTH_CHECK: self._handle_health_check,
            RecoveryActionType.GRACEFUL_DEGRADATION: self._handle_graceful_degradation,
            RecoveryActionType.SCALE_UP: self._handle_scale_up,
            RecoveryActionType.SCALE_DOWN: self._handle_scale_down
        }
    
    async def start_monitoring(self):
        """Start the automatic monitoring and recovery system"""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Automatic recovery monitoring started")
    
    async def stop_monitoring(self):
        """Stop the automatic monitoring and recovery system"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Automatic recovery monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop that checks system health and triggers recovery"""
        while self.monitoring_active:
            try:
                await self._check_system_health()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as error:
                logger.error(f"Error in monitoring loop: {error}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_system_health(self):
        """Check system health and trigger recovery if needed"""
        try:
            # Check database health
            if not await self._check_database_health():
                await self._trigger_recovery("database_connection_failed")
            
            # Check memory usage
            memory_usage = await self._get_memory_usage()
            if memory_usage > 80:  # 80% memory usage threshold
                await self._trigger_recovery("memory_usage_high")
            
            # Check cache health
            if not await graceful_degradation_service.check_service_health("cache"):
                await self._trigger_recovery("cache_errors_high")
            
            # Check error rates
            error_rate = await self._get_recent_error_rate()
            if error_rate > 0.1:  # 10% error rate threshold
                await self._trigger_recovery("error_rate_high")
            
            # Check log file sizes
            if await self._check_log_sizes():
                await self._trigger_recovery("log_files_large")
                
        except Exception as error:
            logger.error(f"Error checking system health: {error}")
    
    async def _trigger_recovery(self, condition: str):
        """Trigger recovery actions for a given condition"""
        # Find applicable recovery rules
        applicable_rules = [
            rule for rule in self.recovery_rules 
            if rule.trigger_condition == condition and rule.enabled
        ]
        
        # Sort by priority
        applicable_rules.sort(key=lambda r: r.priority)
        
        for rule in applicable_rules:
            if await self._can_execute_recovery(rule):
                await self._execute_recovery(rule)
    
    async def _can_execute_recovery(self, rule: RecoveryRule) -> bool:
        """Check if a recovery rule can be executed"""
        rule_key = f"{rule.trigger_condition}:{rule.recovery_action.value}"
        
        # Check if currently active
        if rule_key in self.active_recoveries:
            return False
        
        # Check cooldown
        if rule_key in self.recovery_history:
            last_executions = self.recovery_history[rule_key]
            recent_executions = [
                exec_time for exec_time in last_executions
                if (datetime.now() - exec_time).seconds < rule.cooldown_seconds
            ]
            
            if len(recent_executions) >= rule.max_attempts:
                logger.warning(f"Recovery rule {rule_key} exceeded max attempts")
                return False
        
        return True
    
    async def _execute_recovery(self, rule: RecoveryRule) -> RecoveryResult:
        """Execute a recovery action"""
        rule_key = f"{rule.trigger_condition}:{rule.recovery_action.value}"
        start_time = time.time()
        
        logger.info(f"Executing recovery action: {rule.recovery_action.value} for {rule.trigger_condition}")
        
        # Mark as active
        self.active_recoveries[rule_key] = datetime.now()
        
        try:
            # Get recovery handler
            handler = self.recovery_handlers.get(rule.recovery_action)
            if not handler:
                raise Exception(f"No handler found for recovery action: {rule.recovery_action}")
            
            # Execute recovery
            success = await handler(rule.parameters)
            duration = time.time() - start_time
            
            # Create result
            result = RecoveryResult(
                success=success,
                action_type=rule.recovery_action,
                duration_seconds=duration,
                message=f"Recovery action completed: {success}",
                details={
                    "trigger_condition": rule.trigger_condition,
                    "parameters": rule.parameters,
                    "rule_key": rule_key
                }
            )
            
            # Record execution
            if rule_key not in self.recovery_history:
                self.recovery_history[rule_key] = []
            self.recovery_history[rule_key].append(datetime.now())
            
            # Store in database
            await self._store_recovery_action(rule, result)
            
            if success:
                logger.info(f"Recovery action successful: {rule.recovery_action.value}")
            else:
                logger.error(f"Recovery action failed: {rule.recovery_action.value}")
            
            return result
            
        except Exception as error:
            duration = time.time() - start_time
            result = RecoveryResult(
                success=False,
                action_type=rule.recovery_action,
                duration_seconds=duration,
                message=f"Recovery action failed: {error}",
                details={"error": str(error)}
            )
            
            logger.error(f"Recovery action failed: {rule.recovery_action.value} - {error}")
            return result
            
        finally:
            # Remove from active recoveries
            self.active_recoveries.pop(rule_key, None)
    
    # Recovery action handlers
    async def _handle_cache_invalidation(self, parameters: Dict) -> bool:
        """Handle cache invalidation recovery"""
        try:
            pattern = parameters.get('pattern', '*')
            force = parameters.get('force', False)
            
            if force:
                # Clear all cache
                await cache_manager.clear_all()
                logger.info("All cache cleared due to recovery action")
            else:
                # Clear specific pattern
                keys = await cache_manager.get_keys_by_pattern(pattern)
                for key in keys:
                    await cache_manager.delete(key)
                logger.info(f"Cache cleared for pattern: {pattern}")
            
            return True
            
        except Exception as error:
            logger.error(f"Cache invalidation recovery failed: {error}")
            return False
    
    async def _handle_service_restart(self, parameters: Dict) -> bool:
        """Handle service restart recovery"""
        try:
            service_name = parameters.get('service_name', 'backend')
            
            # This would depend on your deployment setup
            # For Docker, you might use docker restart commands
            # For systemd, you might use systemctl restart
            # This is a placeholder implementation
            
            logger.info(f"Service restart requested for: {service_name}")
            
            # In a real implementation, you would:
            # 1. Send signal to gracefully shutdown
            # 2. Wait for shutdown
            # 3. Restart service
            # 4. Wait for health check
            
            return True
            
        except Exception as error:
            logger.error(f"Service restart recovery failed: {error}")
            return False
    
    async def _handle_circuit_breaker_reset(self, parameters: Dict) -> bool:
        """Handle circuit breaker reset recovery"""
        try:
            # This would integrate with your circuit breaker implementation
            # from the error recovery middleware
            
            logger.info("Circuit breaker reset requested")
            
            # Reset circuit breakers in error recovery middleware
            # This would be implemented in the middleware
            
            return True
            
        except Exception as error:
            logger.error(f"Circuit breaker reset recovery failed: {error}")
            return False
    
    async def _handle_database_reconnect(self, parameters: Dict) -> bool:
        """Handle database reconnection recovery"""
        try:
            timeout = parameters.get('timeout', 30)
            retry_count = parameters.get('retry_count', 3)
            
            for attempt in range(retry_count):
                try:
                    # Test database connection
                    db = next(get_db())
                    result = db.execute("SELECT 1").fetchone()
                    
                    if result:
                        logger.info(f"Database connection restored on attempt {attempt + 1}")
                        return True
                        
                except Exception as db_error:
                    logger.warning(f"Database reconnect attempt {attempt + 1} failed: {db_error}")
                    if attempt < retry_count - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            return False
            
        except Exception as error:
            logger.error(f"Database reconnect recovery failed: {error}")
            return False
    
    async def _handle_memory_cleanup(self, parameters: Dict) -> bool:
        """Handle memory cleanup recovery"""
        try:
            import gc
            
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"Garbage collection freed {collected} objects")
            
            # Clear caches if memory usage is still high
            current_memory = await self._get_memory_usage()
            threshold = parameters.get('threshold_mb', 1000)
            
            if current_memory > threshold:
                await cache_manager.clear_all()
                logger.info("Cache cleared due to high memory usage")
            
            return True
            
        except Exception as error:
            logger.error(f"Memory cleanup recovery failed: {error}")
            return False
    
    async def _handle_log_rotation(self, parameters: Dict) -> bool:
        """Handle log rotation recovery"""
        try:
            max_size_mb = parameters.get('max_size_mb', 100)
            log_dir = "/root/IcfesLeveling/logs"
            
            if not os.path.exists(log_dir):
                return True  # No logs to rotate
            
            for log_file in os.listdir(log_dir):
                log_path = os.path.join(log_dir, log_file)
                
                if os.path.isfile(log_path):
                    size_mb = os.path.getsize(log_path) / (1024 * 1024)
                    
                    if size_mb > max_size_mb:
                        # Rotate log file
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        rotated_path = f"{log_path}.{timestamp}"
                        os.rename(log_path, rotated_path)
                        
                        logger.info(f"Rotated log file: {log_file} ({size_mb:.1f}MB)")
            
            return True
            
        except Exception as error:
            logger.error(f"Log rotation recovery failed: {error}")
            return False
    
    async def _handle_health_check(self, parameters: Dict) -> bool:
        """Handle health check recovery"""
        try:
            services = parameters.get('services', ['database', 'cache', 'ai_service'])
            
            all_healthy = True
            for service in services:
                healthy = await graceful_degradation_service.check_service_health(service)
                if not healthy:
                    all_healthy = False
                    logger.warning(f"Service {service} is unhealthy")
            
            return all_healthy
            
        except Exception as error:
            logger.error(f"Health check recovery failed: {error}")
            return False
    
    async def _handle_graceful_degradation(self, parameters: Dict) -> bool:
        """Handle graceful degradation recovery"""
        try:
            services = parameters.get('services', [])
            
            for service in services:
                await graceful_degradation_service.update_service_status(service, False)
                logger.info(f"Activated graceful degradation for service: {service}")
            
            return True
            
        except Exception as error:
            logger.error(f"Graceful degradation recovery failed: {error}")
            return False
    
    async def _handle_scale_up(self, parameters: Dict) -> bool:
        """Handle scale up recovery"""
        try:
            # This would integrate with your container orchestration system
            # (Docker Swarm, Kubernetes, etc.)
            logger.info("Scale up requested")
            return True
            
        except Exception as error:
            logger.error(f"Scale up recovery failed: {error}")
            return False
    
    async def _handle_scale_down(self, parameters: Dict) -> bool:
        """Handle scale down recovery"""
        try:
            # This would integrate with your container orchestration system
            logger.info("Scale down requested")
            return True
            
        except Exception as error:
            logger.error(f"Scale down recovery failed: {error}")
            return False
    
    # Health check methods
    async def _check_database_health(self) -> bool:
        """Check database health"""
        try:
            db = next(get_db())
            result = db.execute("SELECT 1").fetchone()
            return result is not None
        except Exception:
            return False
    
    async def _get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            # Fallback if psutil is not available
            try:
                with open('/proc/meminfo', 'r') as f:
                    lines = f.readlines()
                    total = int([line for line in lines if 'MemTotal' in line][0].split()[1])
                    available = int([line for line in lines if 'MemAvailable' in line][0].split()[1])
                    return ((total - available) / total) * 100
            except:
                return 0.0
    
    async def _get_recent_error_rate(self) -> float:
        """Get recent error rate from error logs"""
        try:
            db = next(get_db())
            
            # Get errors from last 5 minutes
            five_minutes_ago = datetime.now() - timedelta(minutes=5)
            
            from ..models.error_log import ErrorLog
            error_count = db.query(ErrorLog).filter(
                ErrorLog.timestamp >= five_minutes_ago
            ).count()
            
            # Estimate total requests (this would be better with actual metrics)
            estimated_total_requests = max(error_count * 10, 100)  # Rough estimate
            
            return error_count / estimated_total_requests
            
        except Exception:
            return 0.0
    
    async def _check_log_sizes(self) -> bool:
        """Check if log files are too large"""
        try:
            log_dir = "/root/IcfesLeveling/logs"
            max_size_mb = 100
            
            if not os.path.exists(log_dir):
                return False
            
            for log_file in os.listdir(log_dir):
                log_path = os.path.join(log_dir, log_file)
                if os.path.isfile(log_path):
                    size_mb = os.path.getsize(log_path) / (1024 * 1024)
                    if size_mb > max_size_mb:
                        return True
            
            return False
            
        except Exception:
            return False
    
    async def _store_recovery_action(self, rule: RecoveryRule, result: RecoveryResult):
        """Store recovery action in database for analysis"""
        try:
            db = next(get_db())
            
            recovery_action = RecoveryAction(
                action_type=result.action_type.value,
                target_service="system",
                trigger_error_type=rule.trigger_condition,
                action_parameters=json.dumps(rule.parameters),
                execution_status="completed" if result.success else "failed",
                execution_start=datetime.now() - timedelta(seconds=result.duration_seconds),
                execution_end=datetime.now(),
                execution_duration=result.duration_seconds,
                success="true" if result.success else "false",
                result_message=result.message
            )
            
            db.add(recovery_action)
            db.commit()
            
        except Exception as error:
            logger.error(f"Failed to store recovery action: {error}")
    
    # Public API methods
    def add_recovery_rule(self, rule: RecoveryRule):
        """Add a custom recovery rule"""
        self.recovery_rules.append(rule)
        self.recovery_rules.sort(key=lambda r: r.priority)
    
    def remove_recovery_rule(self, condition: str, action_type: RecoveryActionType):
        """Remove a recovery rule"""
        self.recovery_rules = [
            rule for rule in self.recovery_rules
            if not (rule.trigger_condition == condition and rule.recovery_action == action_type)
        ]
    
    def get_recovery_status(self) -> Dict:
        """Get current recovery system status"""
        return {
            "monitoring_active": self.monitoring_active,
            "active_recoveries": len(self.active_recoveries),
            "total_rules": len(self.recovery_rules),
            "enabled_rules": len([r for r in self.recovery_rules if r.enabled]),
            "recovery_history_keys": len(self.recovery_history)
        }
    
    async def manual_recovery(self, action_type: RecoveryActionType, parameters: Dict = None) -> RecoveryResult:
        """Manually trigger a recovery action"""
        rule = RecoveryRule(
            trigger_condition="manual_trigger",
            recovery_action=action_type,
            parameters=parameters or {}
        )
        
        return await self._execute_recovery(rule)


# Global instance
automatic_recovery_service = AutomaticRecoveryService()