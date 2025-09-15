import asyncio
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from ..core.database import get_db
from .student_file_storage_service import StudentFileStorageService

logger = logging.getLogger(__name__)

class StorageScheduler:
    """
    Automated Storage Management Scheduler
    
    Handles:
    - Automatic file archiving
    - Cache cleanup
    - Backup creation
    - Storage optimization
    - Monitoring and alerts
    """
    
    def __init__(self):
        self.is_running = False
        self.scheduler_stats = {
            'last_archive': None,
            'last_cache_cleanup': None,
            'last_backup_check': None,
            'archived_files_today': 0,
            'errors_today': 0
        }
    
    def setup_schedules(self):
        """Setup all scheduled tasks"""
        # Daily tasks
        schedule.every().day.at("02:00").do(self.daily_archive_task)
        schedule.every().day.at("03:00").do(self.daily_cache_cleanup)
        schedule.every().day.at("04:00").do(self.daily_backup_check)
        
        # Weekly tasks
        schedule.every().sunday.at("01:00").do(self.weekly_deep_cleanup)
        schedule.every().monday.at("05:00").do(self.weekly_stats_report)
        
        # Hourly tasks
        schedule.every().hour.do(self.hourly_health_check)
        
        logger.info("✅ Storage scheduler setup completed")
    
    async def daily_archive_task(self):
        """Archive files older than 90 days"""
        try:
            logger.info("🗄️ Starting daily archive task")
            
            db_session = next(get_db())
            storage_service = StudentFileStorageService(db_session)
            
            # Archive files older than 90 days
            result = storage_service.archive_old_files(days_old=90)
            
            self.scheduler_stats['last_archive'] = datetime.now().isoformat()
            self.scheduler_stats['archived_files_today'] += result['archived_count']
            
            logger.info(f"✅ Daily archive completed: {result['archived_count']} files archived")
            
            db_session.close()
            
        except Exception as e:
            logger.error(f"❌ Daily archive task failed: {e}")
            self.scheduler_stats['errors_today'] += 1
    
    async def daily_cache_cleanup(self):
        """Clean up expired cache entries"""
        try:
            logger.info("🧹 Starting daily cache cleanup")
            
            db_session = next(get_db())
            storage_service = StudentFileStorageService(db_session)
            
            result = storage_service.cleanup_expired_cache()
            
            self.scheduler_stats['last_cache_cleanup'] = datetime.now().isoformat()
            
            logger.info(f"✅ Cache cleanup completed: {result}")
            
            db_session.close()
            
        except Exception as e:
            logger.error(f"❌ Cache cleanup failed: {e}")
            self.scheduler_stats['errors_today'] += 1
    
    async def daily_backup_check(self):
        """Check and create backups for users without recent backups"""
        try:
            logger.info("💾 Starting daily backup check")
            
            db_session = next(get_db())
            storage_service = StudentFileStorageService(db_session)
            
            # Get users who haven't had a backup in 7 days
            cutoff_date = datetime.now() - timedelta(days=7)
            
            # This is a simplified version - in practice, you'd query for users
            # who need backups based on their last backup date
            users_needing_backup = []  # Would come from database query
            
            backup_count = 0
            for user_id in users_needing_backup:
                try:
                    backup_info = storage_service.create_backup(user_id)
                    backup_count += 1
                    logger.info(f"✅ Backup created for user {user_id}")
                except Exception as e:
                    logger.error(f"❌ Backup failed for user {user_id}: {e}")
            
            self.scheduler_stats['last_backup_check'] = datetime.now().isoformat()
            
            logger.info(f"✅ Backup check completed: {backup_count} backups created")
            
            db_session.close()
            
        except Exception as e:
            logger.error(f"❌ Backup check failed: {e}")
            self.scheduler_stats['errors_today'] += 1
    
    async def weekly_deep_cleanup(self):
        """Perform deep cleanup and optimization"""
        try:
            logger.info("🔧 Starting weekly deep cleanup")
            
            db_session = next(get_db())
            storage_service = StudentFileStorageService(db_session)
            
            # Remove archived files older than 1 year
            very_old_cutoff = datetime.now() - timedelta(days=365)
            
            # Archive very old files (older than 1 year)
            result = storage_service.archive_old_files(days_old=365)
            
            # Additional cleanup tasks
            stats = storage_service.get_storage_statistics()
            
            logger.info(f"✅ Weekly deep cleanup completed")
            logger.info(f"   - Storage stats: {stats['total_files']} files, {stats['total_size_mb']} MB")
            
            db_session.close()
            
        except Exception as e:
            logger.error(f"❌ Weekly deep cleanup failed: {e}")
    
    async def weekly_stats_report(self):
        """Generate weekly storage statistics report"""
        try:
            logger.info("📊 Generating weekly stats report")
            
            db_session = next(get_db())
            storage_service = StudentFileStorageService(db_session)
            
            stats = storage_service.get_storage_statistics()
            
            # Log comprehensive stats
            logger.info("📊 Weekly Storage Report:")
            logger.info(f"   - Total files: {stats['total_files']}")
            logger.info(f"   - Total size: {stats['total_size_mb']} MB")
            logger.info(f"   - Recent files: {stats.get('recent_files_7_days', 0)}")
            logger.info(f"   - Files by type: {len(stats['files_by_type'])} categories")
            
            # Reset daily counters
            self.scheduler_stats['archived_files_today'] = 0
            self.scheduler_stats['errors_today'] = 0
            
            db_session.close()
            
        except Exception as e:
            logger.error(f"❌ Weekly stats report failed: {e}")
    
    async def hourly_health_check(self):
        """Perform hourly health checks"""
        try:
            db_session = next(get_db())
            storage_service = StudentFileStorageService(db_session)
            
            # Basic health checks
            # 1. Check database connectivity
            db_session.execute("SELECT 1")
            
            # 2. Check storage backend
            if storage_service.minio_client:
                try:
                    list(storage_service.minio_client.list_buckets())
                except Exception as e:
                    logger.warning(f"MinIO health check failed: {e}")
            
            # 3. Check Redis
            if storage_service.redis_client:
                try:
                    storage_service.redis_client.ping()
                except Exception as e:
                    logger.warning(f"Redis health check failed: {e}")
            
            db_session.close()
            
        except Exception as e:
            logger.error(f"❌ Hourly health check failed: {e}")
    
    def start_scheduler(self):
        """Start the background scheduler"""
        self.is_running = True
        self.setup_schedules()
        
        async def run_scheduler():
            logger.info("🚀 Storage scheduler started")
            while self.is_running:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
        
        # Start the scheduler in a separate task
        asyncio.create_task(run_scheduler())
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("⏹️ Storage scheduler stopped")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status and statistics"""
        return {
            'is_running': self.is_running,
            'scheduled_jobs': len(schedule.jobs),
            'stats': self.scheduler_stats,
            'next_jobs': [
                {
                    'job': str(job.job_func.__name__),
                    'next_run': job.next_run.isoformat() if job.next_run else None
                }
                for job in schedule.jobs[:5]  # Show next 5 jobs
            ]
        }

# Storage policy configurations
STORAGE_POLICIES = {
    'archival': {
        'study_plans': 180,      # Archive after 6 months
        'progress_data': 90,     # Archive after 3 months
        'assessments': 365,      # Archive after 1 year
        'certificates': None,    # Never archive
        'multimedia': 90,        # Archive after 3 months
    },
    'backup': {
        'frequency_days': 7,     # Create backup every 7 days
        'retention_days': 90,    # Keep backups for 90 days
    },
    'cache': {
        'max_file_size_mb': 1,   # Don't cache files larger than 1MB
        'default_ttl_seconds': 3600,  # 1 hour default TTL
    },
    'cleanup': {
        'temp_files_hours': 24,  # Remove temp files after 24 hours
        'failed_uploads_hours': 2, # Remove failed uploads after 2 hours
    }
}

class StoragePolicyManager:
    """
    Manages and enforces storage policies
    """
    
    def __init__(self, policies: Dict[str, Any] = None):
        self.policies = policies or STORAGE_POLICIES
    
    def should_archive_file(self, file_metadata: Dict[str, Any]) -> bool:
        """Check if a file should be archived based on policy"""
        content_type = file_metadata.get('content_type', 'study_plans')
        created_at = datetime.fromisoformat(file_metadata['created_at'].replace('Z', '+00:00'))
        
        archive_days = self.policies['archival'].get(content_type)
        if archive_days is None:
            return False
        
        age_days = (datetime.now() - created_at).days
        return age_days >= archive_days
    
    def should_backup_user(self, last_backup_date: datetime) -> bool:
        """Check if a user needs a new backup"""
        if not last_backup_date:
            return True
        
        days_since_backup = (datetime.now() - last_backup_date).days
        return days_since_backup >= self.policies['backup']['frequency_days']
    
    def should_cache_file(self, file_size_bytes: int) -> bool:
        """Check if a file should be cached"""
        max_size_bytes = self.policies['cache']['max_file_size_mb'] * 1024 * 1024
        return file_size_bytes <= max_size_bytes
    
    def get_cache_ttl(self, content_type: str) -> int:
        """Get cache TTL for content type"""
        # Could be customized per content type
        return self.policies['cache']['default_ttl_seconds']

# Initialize global scheduler instance
storage_scheduler = StorageScheduler()
policy_manager = StoragePolicyManager()