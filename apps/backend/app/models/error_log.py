"""
Error Log Model for comprehensive error tracking and analysis
"""

from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from ..core.database import Base


class ErrorLog(Base):
    """
    Model for storing comprehensive error information for analysis and recovery
    """
    __tablename__ = "error_logs"
    
    # Primary key and identification
    id = Column(Integer, primary_key=True, index=True)
    error_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Request information
    endpoint = Column(String(500), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    query_params = Column(Text)
    
    # Error details
    error_type = Column(String(50), nullable=False, index=True)
    error_message = Column(Text, nullable=False)
    error_traceback = Column(Text)
    
    # Client information
    user_agent = Column(Text)
    ip_address = Column(String(45))  # IPv6 compatible
    
    # Performance metrics
    processing_time = Column(Float)  # In seconds
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_error_logs_endpoint_timestamp', 'endpoint', 'timestamp'),
        Index('idx_error_logs_error_type_timestamp', 'error_type', 'timestamp'),
        Index('idx_error_logs_ip_timestamp', 'ip_address', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<ErrorLog(error_id='{self.error_id}', endpoint='{self.endpoint}', error_type='{self.error_type}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'error_id': self.error_id,
            'endpoint': self.endpoint,
            'method': self.method,
            'query_params': self.query_params,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'error_traceback': self.error_traceback,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'processing_time': self.processing_time,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class ErrorPattern(Base):
    """
    Model for tracking error patterns and recovery strategies
    """
    __tablename__ = "error_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Pattern identification
    endpoint_pattern = Column(String(500), index=True)
    error_type_pattern = Column(String(50), index=True)
    frequency_threshold = Column(Integer, default=5)
    
    # Pattern statistics
    occurrence_count = Column(Integer, default=0)
    first_occurrence = Column(DateTime, default=datetime.utcnow)
    last_occurrence = Column(DateTime, default=datetime.utcnow)
    
    # Recovery information
    recovery_strategy = Column(String(100))
    recovery_success_rate = Column(Float, default=0.0)
    auto_recovery_enabled = Column(String(10), default='true')  # 'true', 'false', 'conditional'
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ErrorPattern(pattern_id='{self.pattern_id}', endpoint='{self.endpoint_pattern}')>"


class SystemHealth(Base):
    """
    Model for tracking system health metrics
    """
    __tablename__ = "system_health"
    
    id = Column(Integer, primary_key=True, index=True)
    health_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Health metrics
    service_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # 'healthy', 'degraded', 'unhealthy'
    response_time_avg = Column(Float)  # Average response time in ms
    error_rate = Column(Float, default=0.0)  # Error rate percentage
    uptime_percentage = Column(Float, default=100.0)
    
    # Detailed metrics
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    active_connections = Column(Integer)
    
    # Circuit breaker status
    circuit_breaker_state = Column(String(20), default='closed')  # 'closed', 'open', 'half_open'
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<SystemHealth(service='{self.service_name}', status='{self.status}')>"


class RecoveryAction(Base):
    """
    Model for tracking recovery actions and their effectiveness
    """
    __tablename__ = "recovery_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Action details
    action_type = Column(String(50), nullable=False, index=True)  # 'cache_invalidation', 'circuit_breaker', 'service_restart'
    target_service = Column(String(100), nullable=False)
    trigger_error_type = Column(String(50))
    
    # Action parameters
    action_parameters = Column(Text)  # JSON string of action parameters
    
    # Execution details
    execution_status = Column(String(20), default='pending')  # 'pending', 'executing', 'completed', 'failed'
    execution_start = Column(DateTime)
    execution_end = Column(DateTime)
    execution_duration = Column(Float)  # In seconds
    
    # Results
    success = Column(String(10), default='unknown')  # 'true', 'false', 'unknown'
    result_message = Column(Text)
    
    # Impact assessment
    error_rate_before = Column(Float)
    error_rate_after = Column(Float)
    recovery_effectiveness = Column(Float)  # Percentage improvement
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<RecoveryAction(action_type='{self.action_type}', target='{self.target_service}')>"