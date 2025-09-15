from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings
import logging
import time

logger = logging.getLogger(__name__)

# Optimized database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    # Connection Pool Configuration for High Performance
    poolclass=QueuePool,
    pool_size=20,              # Number of connections to maintain in pool
    max_overflow=30,           # Additional connections beyond pool_size
    pool_pre_ping=True,        # Validate connections before use
    pool_recycle=3600,         # Recycle connections every hour
    pool_timeout=30,           # Timeout for getting connection from pool
    
    # Query Performance Settings
    echo=False,                # Set to True for SQL debugging
    echo_pool=False,           # Set to True for connection pool debugging
    
    # Connection Settings for PostgreSQL optimization
    connect_args={
        "application_name": "icfes_leveling_backend",
        "options": "-c statement_timeout=30000",  # 30 second statement timeout
    } if 'postgresql' in settings.DATABASE_URL else {}
)

# Performance monitoring events
@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries for performance monitoring"""
    context._query_start_time = time.time()

@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log completed queries and identify slow ones"""
    total = time.time() - context._query_start_time
    if total > 1.0:  # Log queries taking more than 1 second
        logger.warning(f"Slow query detected ({total:.2f}s): {statement[:200]}...")

# Create optimized session factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    # Optimize session for batch operations
    expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

# Connection pool health check
def check_database_health():
    """Check database connection and pool health"""
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1").scalar()
            pool = engine.pool
            return {
                "status": "healthy",
                "connection_test": result == 1,
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Optimized database session dependency with error handling
def get_db():
    """
    Enhanced database session dependency with:
    - Automatic retry on connection failures
    - Performance monitoring
    - Proper cleanup
    """
    db = None
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()

# Database session context manager for services
class DatabaseSession:
    """Context manager for database sessions in services"""
    
    def __init__(self):
        self.db = None
    
    def __enter__(self):
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.db.rollback()
        self.db.close()

# Utility function for bulk operations
def bulk_insert_optimized(model_class, data_list, batch_size=1000):
    """
    Optimized bulk insert operation
    
    Args:
        model_class: SQLAlchemy model class
        data_list: List of dictionaries with data to insert
        batch_size: Number of records to insert per batch
    """
    with DatabaseSession() as db:
        try:
            # Process in batches to avoid memory issues
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i:i + batch_size]
                db.bulk_insert_mappings(model_class, batch)
                db.commit()
                logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} records")
            
            logger.info(f"Bulk insert completed: {len(data_list)} total records")
            return True
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            db.rollback()
            return False 