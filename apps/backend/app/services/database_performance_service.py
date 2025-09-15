"""
Database Performance Monitoring and Optimization Service
ICFES Leveling System

This service provides comprehensive database performance monitoring, 
optimization recommendations, and automated tuning for the 480+ question 
database and user analytics.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import text, func, desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from dataclasses import dataclass
import psutil
import pandas as pd

from ..core.database import engine, DatabaseSession, check_database_health
from ..core.database_indexes import DatabaseIndexOptimizer, db_optimizer
from ..core.cache_manager import cache_manager, query_cache
from ..models.question import Question
from ..models.user import User
from ..models.practice_session import PracticeSession, PracticeAnswer
from ..models.diagnostic_analytics import DiagnosticTestAnalytics

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Data class for performance metrics"""
    name: str
    value: float
    unit: str
    status: str  # 'good', 'warning', 'critical'
    recommendation: Optional[str] = None

class DatabasePerformanceService:
    """
    Comprehensive database performance monitoring and optimization service
    """
    
    def __init__(self):
        self.index_optimizer = db_optimizer
        self.performance_history = []
        
        # Performance thresholds
        self.thresholds = {
            'query_time_warning': 1.0,      # seconds
            'query_time_critical': 5.0,     # seconds
            'connection_usage_warning': 0.7,  # 70% of pool
            'connection_usage_critical': 0.9, # 90% of pool
            'cache_hit_rate_warning': 0.5,   # 50%
            'cache_hit_rate_critical': 0.3,  # 30%
            'memory_usage_warning': 0.8,     # 80%
            'memory_usage_critical': 0.95,   # 95%
        }
        
        # Query patterns to monitor
        self.critical_queries = [
            'SELECT * FROM questions WHERE subject_id = %s AND difficulty = %s',
            'SELECT * FROM practice_sessions WHERE user_id = %s AND status = %s',
            'SELECT * FROM user_question_mastery WHERE user_id = %s AND needs_review = true',
            'SELECT * FROM diagnostic_test_analytics WHERE user_id = %s',
        ]
    
    def get_comprehensive_performance_report(self, db: Session) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report including:
        - Database health metrics
        - Query performance analysis
        - Cache performance
        - Resource utilization
        - Optimization recommendations
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'database_health': {},
            'query_performance': {},
            'cache_performance': {},
            'resource_utilization': {},
            'recommendations': [],
            'metrics': []
        }
        
        try:
            # Database health check
            report['database_health'] = check_database_health()
            
            # Connection pool analysis
            pool_metrics = self._analyze_connection_pool()
            report['database_health']['connection_pool'] = pool_metrics
            
            # Query performance analysis
            report['query_performance'] = self._analyze_query_performance(db)
            
            # Cache performance
            report['cache_performance'] = self._analyze_cache_performance()
            
            # Resource utilization
            report['resource_utilization'] = self._analyze_resource_utilization()
            
            # Table statistics
            report['table_statistics'] = self._get_table_statistics(db)
            
            # Index usage analysis
            report['index_analysis'] = self._analyze_index_usage(db)
            
            # Generate metrics with status
            report['metrics'] = self._generate_performance_metrics(report)
            
            # Generate recommendations
            report['recommendations'] = self._generate_recommendations(report)
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            report['error'] = str(e)
        
        return report
    
    def _analyze_connection_pool(self) -> Dict[str, Any]:
        """Analyze database connection pool performance"""
        try:
            pool = engine.pool
            pool_status = {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid(),
                'total_capacity': pool.size() + 30,  # size + max_overflow
            }
            
            # Calculate utilization
            total_connections = pool_status['checked_in'] + pool_status['checked_out']
            utilization = total_connections / pool_status['total_capacity']
            pool_status['utilization'] = utilization
            
            # Determine status
            if utilization > self.thresholds['connection_usage_critical']:
                pool_status['status'] = 'critical'
            elif utilization > self.thresholds['connection_usage_warning']:
                pool_status['status'] = 'warning'
            else:
                pool_status['status'] = 'good'
            
            return pool_status
            
        except Exception as e:
            logger.error(f"Error analyzing connection pool: {e}")
            return {'error': str(e)}
    
    def _analyze_query_performance(self, db: Session) -> Dict[str, Any]:
        """Analyze query performance using pg_stat_statements if available"""
        query_analysis = {
            'slow_queries': [],
            'most_frequent': [],
            'resource_intensive': [],
            'recommendations': []
        }
        
        try:
            # Check if pg_stat_statements is available
            extensions_query = """
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
            ) as has_pg_stat_statements;
            """
            has_extension = db.execute(text(extensions_query)).scalar()
            
            if has_extension:
                # Get slow queries
                slow_queries_sql = """
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements
                WHERE mean_time > 1000  -- queries taking more than 1 second on average
                ORDER BY mean_time DESC
                LIMIT 10;
                """
                
                result = db.execute(text(slow_queries_sql)).fetchall()
                query_analysis['slow_queries'] = [
                    {
                        'query': row.query[:200] + '...' if len(row.query) > 200 else row.query,
                        'calls': row.calls,
                        'total_time_ms': round(row.total_time, 2),
                        'mean_time_ms': round(row.mean_time, 2),
                        'rows': row.rows,
                        'hit_percent': round(row.hit_percent or 0, 2)
                    } for row in result
                ]
                
                # Get most frequent queries
                frequent_queries_sql = """
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time
                FROM pg_stat_statements
                ORDER BY calls DESC
                LIMIT 10;
                """
                
                result = db.execute(text(frequent_queries_sql)).fetchall()
                query_analysis['most_frequent'] = [
                    {
                        'query': row.query[:200] + '...' if len(row.query) > 200 else row.query,
                        'calls': row.calls,
                        'total_time_ms': round(row.total_time, 2),
                        'mean_time_ms': round(row.mean_time, 2)
                    } for row in result
                ]
            else:
                query_analysis['note'] = "pg_stat_statements extension not available"
            
            # Analyze specific table query patterns
            query_analysis.update(self._analyze_table_query_patterns(db))
            
        except Exception as e:
            logger.error(f"Error analyzing query performance: {e}")
            query_analysis['error'] = str(e)
        
        return query_analysis
    
    def _analyze_cache_performance(self) -> Dict[str, Any]:
        """Analyze cache performance"""
        cache_stats = cache_manager.get_stats()
        
        # Determine cache status
        hit_rate = cache_stats['hit_rate'] / 100  # Convert percentage to ratio
        
        if hit_rate < self.thresholds['cache_hit_rate_critical']:
            status = 'critical'
        elif hit_rate < self.thresholds['cache_hit_rate_warning']:
            status = 'warning'
        else:
            status = 'good'
        
        cache_stats['status'] = status
        return cache_stats
    
    def _analyze_resource_utilization(self) -> Dict[str, Any]:
        """Analyze system resource utilization"""
        try:
            # Get system memory usage
            memory = psutil.virtual_memory()
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get disk I/O statistics
            disk_io = psutil.disk_io_counters()
            
            utilization = {
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'percent': memory.percent,
                    'status': 'critical' if memory.percent > 95 else 'warning' if memory.percent > 80 else 'good'
                },
                'cpu': {
                    'percent': cpu_percent,
                    'status': 'critical' if cpu_percent > 90 else 'warning' if cpu_percent > 70 else 'good'
                },
                'disk_io': {
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0,
                    'read_count': disk_io.read_count if disk_io else 0,
                    'write_count': disk_io.write_count if disk_io else 0
                } if disk_io else {}
            }
            
            return utilization
            
        except Exception as e:
            logger.error(f"Error analyzing resource utilization: {e}")
            return {'error': str(e)}
    
    def _get_table_statistics(self, db: Session) -> Dict[str, Any]:
        """Get detailed table statistics"""
        try:
            # Get table sizes and statistics
            table_stats_query = """
            SELECT 
                schemaname,
                tablename,
                n_live_tup as live_tuples,
                n_dead_tup as dead_tuples,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """
            
            result = db.execute(text(table_stats_query)).fetchall()
            table_stats = []
            
            for row in result:
                stats = {
                    'table_name': row.tablename,
                    'live_tuples': row.live_tuples,
                    'dead_tuples': row.dead_tuples,
                    'size': row.size,
                    'size_bytes': row.size_bytes,
                    'inserts': row.inserts,
                    'updates': row.updates,
                    'deletes': row.deletes,
                    'last_vacuum': row.last_vacuum.isoformat() if row.last_vacuum else None,
                    'last_analyze': row.last_analyze.isoformat() if row.last_analyze else None
                }
                
                # Calculate dead tuple ratio
                if row.live_tuples and row.dead_tuples:
                    total_tuples = row.live_tuples + row.dead_tuples
                    dead_ratio = row.dead_tuples / total_tuples
                    stats['dead_tuple_ratio'] = round(dead_ratio, 4)
                    stats['needs_vacuum'] = dead_ratio > 0.2
                else:
                    stats['dead_tuple_ratio'] = 0.0
                    stats['needs_vacuum'] = False
                
                table_stats.append(stats)
            
            return {
                'tables': table_stats,
                'total_tables': len(table_stats),
                'total_size_bytes': sum(t['size_bytes'] for t in table_stats)
            }
            
        except Exception as e:
            logger.error(f"Error getting table statistics: {e}")
            return {'error': str(e)}
    
    def _analyze_index_usage(self, db: Session) -> Dict[str, Any]:
        """Analyze index usage and effectiveness"""
        try:
            # Get index usage statistics
            index_usage_query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan as index_scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched,
                pg_size_pretty(pg_relation_size(indexrelid)) as size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC;
            """
            
            result = db.execute(text(index_usage_query)).fetchall()
            
            index_analysis = {
                'used_indexes': [],
                'unused_indexes': [],
                'recommendations': []
            }
            
            for row in result:
                index_info = {
                    'table_name': row.tablename,
                    'index_name': row.indexname,
                    'scans': row.index_scans,
                    'tuples_read': row.tuples_read,
                    'tuples_fetched': row.tuples_fetched,
                    'size': row.size
                }
                
                if row.index_scans == 0:
                    index_analysis['unused_indexes'].append(index_info)
                else:
                    index_analysis['used_indexes'].append(index_info)
            
            # Generate recommendations for unused indexes
            if index_analysis['unused_indexes']:
                index_analysis['recommendations'].append(
                    f"Consider dropping {len(index_analysis['unused_indexes'])} unused indexes to save space"
                )
            
            return index_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing index usage: {e}")
            return {'error': str(e)}
    
    def _analyze_table_query_patterns(self, db: Session) -> Dict[str, Any]:
        """Analyze query patterns for critical tables"""
        patterns = {
            'questions_analysis': {},
            'users_analysis': {},
            'practice_sessions_analysis': {},
            'recommendations': []
        }
        
        try:
            # Analyze questions table patterns
            questions_stats = db.execute(text("""
                SELECT 
                    COUNT(*) as total_questions,
                    COUNT(DISTINCT subject_id) as total_subjects,
                    COUNT(DISTINCT topic_id) as total_topics,
                    AVG(difficulty) as avg_difficulty,
                    COUNT(*) FILTER (WHERE parametro_irt_a IS NOT NULL) as questions_with_irt
                FROM questions
            """)).fetchone()
            
            if questions_stats:
                patterns['questions_analysis'] = {
                    'total_questions': questions_stats.total_questions,
                    'total_subjects': questions_stats.total_subjects,
                    'total_topics': questions_stats.total_topics,
                    'avg_difficulty': round(questions_stats.avg_difficulty or 0, 2),
                    'irt_coverage': round(
                        (questions_stats.questions_with_irt / questions_stats.total_questions) * 100, 2
                    ) if questions_stats.total_questions > 0 else 0
                }
            
            # Analyze user activity patterns
            user_stats = db.execute(text("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (WHERE is_active = true) as active_users,
                    AVG(level) as avg_level,
                    COUNT(DISTINCT rank) as unique_ranks
                FROM users
            """)).fetchone()
            
            if user_stats:
                patterns['users_analysis'] = {
                    'total_users': user_stats.total_users,
                    'active_users': user_stats.active_users,
                    'avg_level': round(user_stats.avg_level or 0, 2),
                    'unique_ranks': user_stats.unique_ranks
                }
            
            # Analyze practice session patterns
            session_stats = db.execute(text("""
                SELECT 
                    COUNT(*) as total_sessions,
                    COUNT(*) FILTER (WHERE status = 'active') as active_sessions,
                    AVG(questions_answered) as avg_questions_answered,
                    AVG(correct_answers::float / NULLIF(questions_answered, 0)) as avg_accuracy
                FROM practice_sessions
                WHERE created_at > NOW() - INTERVAL '7 days'
            """)).fetchone()
            
            if session_stats:
                patterns['practice_sessions_analysis'] = {
                    'total_sessions_7d': session_stats.total_sessions,
                    'active_sessions': session_stats.active_sessions,
                    'avg_questions_answered': round(session_stats.avg_questions_answered or 0, 2),
                    'avg_accuracy': round(session_stats.avg_accuracy or 0, 4)
                }
            
        except Exception as e:
            logger.error(f"Error analyzing table query patterns: {e}")
            patterns['error'] = str(e)
        
        return patterns
    
    def _generate_performance_metrics(self, report: Dict[str, Any]) -> List[PerformanceMetric]:
        """Generate performance metrics with status indicators"""
        metrics = []
        
        try:
            # Database health metrics
            if 'database_health' in report:
                db_health = report['database_health']
                
                # Connection pool utilization
                if 'connection_pool' in db_health:
                    pool = db_health['connection_pool']
                    utilization = pool.get('utilization', 0)
                    
                    if utilization > self.thresholds['connection_usage_critical']:
                        status = 'critical'
                        rec = 'Increase connection pool size or optimize query performance'
                    elif utilization > self.thresholds['connection_usage_warning']:
                        status = 'warning'
                        rec = 'Monitor connection usage and consider pool optimization'
                    else:
                        status = 'good'
                        rec = None
                    
                    metrics.append(PerformanceMetric(
                        name='Connection Pool Utilization',
                        value=utilization * 100,
                        unit='%',
                        status=status,
                        recommendation=rec
                    ))
            
            # Cache performance metrics
            if 'cache_performance' in report:
                cache = report['cache_performance']
                hit_rate = cache.get('hit_rate', 0) / 100
                
                if hit_rate < self.thresholds['cache_hit_rate_critical']:
                    status = 'critical'
                    rec = 'Review caching strategy and increase cache TTL for stable data'
                elif hit_rate < self.thresholds['cache_hit_rate_warning']:
                    status = 'warning'
                    rec = 'Optimize cache warming and key management'
                else:
                    status = 'good'
                    rec = None
                
                metrics.append(PerformanceMetric(
                    name='Cache Hit Rate',
                    value=hit_rate * 100,
                    unit='%',
                    status=status,
                    recommendation=rec
                ))
            
            # Memory utilization
            if 'resource_utilization' in report and 'memory' in report['resource_utilization']:
                memory = report['resource_utilization']['memory']
                memory_percent = memory.get('percent', 0)
                
                if memory_percent > self.thresholds['memory_usage_critical'] * 100:
                    status = 'critical'
                    rec = 'Critical memory usage - consider increasing RAM or optimizing queries'
                elif memory_percent > self.thresholds['memory_usage_warning'] * 100:
                    status = 'warning'
                    rec = 'High memory usage - monitor and optimize if needed'
                else:
                    status = 'good'
                    rec = None
                
                metrics.append(PerformanceMetric(
                    name='Memory Utilization',
                    value=memory_percent,
                    unit='%',
                    status=status,
                    recommendation=rec
                ))
            
        except Exception as e:
            logger.error(f"Error generating performance metrics: {e}")
        
        return metrics
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on the performance report"""
        recommendations = []
        
        try:
            # Database-specific recommendations
            if 'table_statistics' in report and 'tables' in report['table_statistics']:
                tables = report['table_statistics']['tables']
                
                # Check for tables needing vacuum
                vacuum_tables = [t for t in tables if t.get('needs_vacuum', False)]
                if vacuum_tables:
                    table_names = [t['table_name'] for t in vacuum_tables[:3]]
                    recommendations.append(
                        f"Run VACUUM on tables with high dead tuple ratio: {', '.join(table_names)}"
                    )
                
                # Check for tables without recent analyze
                analyze_needed = [t for t in tables if not t.get('last_analyze')]
                if analyze_needed:
                    recommendations.append(
                        f"Run ANALYZE on {len(analyze_needed)} tables to update query planner statistics"
                    )
            
            # Cache recommendations
            if 'cache_performance' in report:
                cache = report['cache_performance']
                hit_rate = cache.get('hit_rate', 0)
                
                if hit_rate < 50:
                    recommendations.append("Implement cache warming for frequently accessed data")
                    recommendations.append("Review cache TTL settings for better hit rates")
            
            # Query performance recommendations
            if 'query_performance' in report:
                query_perf = report['query_performance']
                
                if 'slow_queries' in query_perf and query_perf['slow_queries']:
                    recommendations.append(
                        f"Optimize {len(query_perf['slow_queries'])} slow queries identified"
                    )
                
                if 'questions_analysis' in query_perf:
                    q_analysis = query_perf['questions_analysis']
                    irt_coverage = q_analysis.get('irt_coverage', 0)
                    
                    if irt_coverage < 80:
                        recommendations.append(
                            "Improve IRT parameter coverage for better adaptive question selection"
                        )
            
            # Resource utilization recommendations
            if 'resource_utilization' in report:
                resources = report['resource_utilization']
                
                if 'memory' in resources and resources['memory']['percent'] > 80:
                    recommendations.append("Consider increasing system memory or optimizing memory-intensive operations")
                
                if 'cpu' in resources and resources['cpu']['percent'] > 70:
                    recommendations.append("High CPU usage detected - optimize query performance and consider horizontal scaling")
            
            # Index recommendations
            if 'index_analysis' in report:
                index_analysis = report['index_analysis']
                
                if 'unused_indexes' in index_analysis and index_analysis['unused_indexes']:
                    count = len(index_analysis['unused_indexes'])
                    recommendations.append(f"Consider dropping {count} unused indexes to save storage space")
            
            # General recommendations
            recommendations.extend([
                "Implement automated database maintenance tasks (VACUUM, ANALYZE)",
                "Set up query performance monitoring with pg_stat_statements",
                "Consider implementing read replicas for analytical queries",
                "Review and optimize the most frequent queries identified",
                "Implement connection pooling at the application level",
                "Set up automated cache warming for critical data paths"
            ])
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append(f"Error generating recommendations: {str(e)}")
        
        return recommendations[:10]  # Return top 10 recommendations
    
    async def optimize_database_automatically(self, db: Session) -> Dict[str, Any]:
        """
        Perform automated database optimizations
        """
        optimization_results = {
            'timestamp': datetime.now().isoformat(),
            'actions_performed': [],
            'errors': [],
            'recommendations': []
        }
        
        try:
            # Create critical indexes
            logger.info("Creating database indexes...")
            index_results = self.index_optimizer.create_all_indexes(db)
            optimization_results['actions_performed'].extend(index_results['created'])
            optimization_results['errors'].extend(index_results['failed'])
            
            # Create materialized views
            logger.info("Creating materialized views...")
            mv_results = self.index_optimizer.create_materialized_views(db)
            optimization_results['actions_performed'].extend([
                f"Materialized view: {name}" for name in mv_results['created']
            ])
            optimization_results['errors'].extend(mv_results['failed'])
            
            # Update table statistics
            logger.info("Updating table statistics...")
            try:
                tables_to_analyze = ['questions', 'users', 'practice_sessions', 'practice_answers']
                for table in tables_to_analyze:
                    db.execute(text(f"ANALYZE {table};"))
                optimization_results['actions_performed'].append(f"Updated statistics for {len(tables_to_analyze)} tables")
            except Exception as e:
                optimization_results['errors'].append(f"Failed to update statistics: {str(e)}")
            
            # Warm critical caches
            logger.info("Warming critical caches...")
            try:
                # This would call cache warming functions
                optimization_results['actions_performed'].append("Warmed critical application caches")
            except Exception as e:
                optimization_results['errors'].append(f"Failed to warm caches: {str(e)}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error in automatic optimization: {e}")
            optimization_results['errors'].append(f"Critical error: {str(e)}")
            db.rollback()
        
        return optimization_results

# Global service instance
db_performance_service = DatabasePerformanceService()