#!/usr/bin/env python3
"""
Advanced Query Optimization Service
Smart query caching, optimization, and performance monitoring
"""

import time
import hashlib
import logging
import json
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from functools import wraps
from collections import defaultdict
import asyncio
from datetime import datetime, timedelta

from sqlalchemy import text, event
from sqlalchemy.orm import Session
from sqlalchemy.sql import ClauseElement

from app.core.database import DatabaseSession, engine
from app.core.cache_manager import cache_manager

logger = logging.getLogger(__name__)

@dataclass
class QueryStats:
    """Query performance statistics"""
    query_hash: str
    query_text: str
    execution_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    last_executed: datetime
    is_slow: bool

@dataclass
class CacheStats:
    """Query cache statistics"""
    total_queries: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    total_saved_time: float

class QueryOptimizer:
    """Advanced query optimization and caching service"""
    
    def __init__(self):
        self.query_stats: Dict[str, QueryStats] = {}
        self.cache_stats = CacheStats(0, 0, 0, 0.0, 0.0)
        self.slow_query_threshold = 1.0  # seconds
        self.cache_ttl_map = {
            'questions': 3600,      # 1 hour
            'users': 1800,          # 30 minutes
            'practice': 900,        # 15 minutes
            'leaderboard': 300,     # 5 minutes
            'analytics': 1800,      # 30 minutes
            'default': 600          # 10 minutes
        }
        self.setup_query_monitoring()
    
    def setup_query_monitoring(self):
        """Setup database query monitoring events"""
        
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query start time"""
            context._query_start_time = time.time()
            context._query_text = str(statement)[:1000]  # First 1000 chars
        
        @event.listens_for(engine, "after_cursor_execute") 
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query completion and update stats"""
            if hasattr(context, '_query_start_time'):
                execution_time = time.time() - context._query_start_time
                query_text = getattr(context, '_query_text', str(statement)[:1000])
                self.update_query_stats(query_text, execution_time)
    
    def generate_cache_key(self, query: str, params: Optional[Dict] = None) -> str:
        """Generate a cache key for a query and its parameters"""
        key_data = {
            'query': query,
            'params': params or {}
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cache_ttl(self, query: str) -> int:
        """Determine cache TTL based on query type"""
        query_lower = query.lower()
        
        for table_type, ttl in self.cache_ttl_map.items():
            if table_type in query_lower:
                return ttl
        
        # Dynamic TTL based on query complexity
        if 'join' in query_lower and 'group by' in query_lower:
            return 1800  # 30 minutes for complex queries
        elif 'count' in query_lower or 'sum' in query_lower:
            return 900   # 15 minutes for aggregations
        
        return self.cache_ttl_map['default']
    
    def cached_query(self, ttl: Optional[int] = None, cache_key_prefix: str = "query"):
        """Decorator for caching database queries"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                cache_key_data = {
                    'func': func.__name__,
                    'args': args[1:] if args else [],  # Skip 'db' parameter
                    'kwargs': kwargs
                }
                cache_key = f"{cache_key_prefix}:{self.generate_cache_key(str(cache_key_data))}"
                
                # Try to get from cache
                start_time = time.time()
                cached_result = cache_manager.get(cache_key)
                
                if cached_result is not None:
                    # Cache hit
                    self.cache_stats.cache_hits += 1
                    self.cache_stats.total_queries += 1
                    saved_time = time.time() - start_time
                    self.cache_stats.total_saved_time += saved_time
                    logger.debug(f"Cache HIT for {func.__name__}: {cache_key[:50]}...")
                    return cached_result
                
                # Cache miss - execute query
                self.cache_stats.cache_misses += 1
                self.cache_stats.total_queries += 1
                
                result = func(*args, **kwargs)
                
                # Cache the result
                query_ttl = ttl or self.get_cache_ttl(func.__name__)
                cache_manager.set(cache_key, result, ttl=query_ttl)
                
                execution_time = time.time() - start_time
                logger.debug(f"Cache MISS for {func.__name__}: {execution_time:.3f}s, cached for {query_ttl}s")
                
                return result
            
            return wrapper
        return decorator
    
    def update_query_stats(self, query_text: str, execution_time: float):
        """Update statistics for a query execution"""
        query_hash = hashlib.md5(query_text.encode()).hexdigest()
        
        if query_hash in self.query_stats:
            stats = self.query_stats[query_hash]
            stats.execution_count += 1
            stats.total_time += execution_time
            stats.avg_time = stats.total_time / stats.execution_count
            stats.min_time = min(stats.min_time, execution_time)
            stats.max_time = max(stats.max_time, execution_time)
            stats.last_executed = datetime.now()
            stats.is_slow = stats.avg_time > self.slow_query_threshold
        else:
            self.query_stats[query_hash] = QueryStats(
                query_hash=query_hash,
                query_text=query_text,
                execution_count=1,
                total_time=execution_time,
                avg_time=execution_time,
                min_time=execution_time,
                max_time=execution_time,
                last_executed=datetime.now(),
                is_slow=execution_time > self.slow_query_threshold
            )
        
        # Log slow queries
        if execution_time > self.slow_query_threshold:
            logger.warning(f"Slow query detected ({execution_time:.3f}s): {query_text[:200]}...")
    
    def get_slow_queries(self, limit: int = 20) -> List[QueryStats]:
        """Get the slowest queries"""
        slow_queries = [stats for stats in self.query_stats.values() if stats.is_slow]
        return sorted(slow_queries, key=lambda x: x.avg_time, reverse=True)[:limit]
    
    def get_most_frequent_queries(self, limit: int = 20) -> List[QueryStats]:
        """Get the most frequently executed queries"""
        return sorted(
            self.query_stats.values(), 
            key=lambda x: x.execution_count, 
            reverse=True
        )[:limit]
    
    def get_cache_performance(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        if self.cache_stats.total_queries > 0:
            hit_rate = (self.cache_stats.cache_hits / self.cache_stats.total_queries) * 100
        else:
            hit_rate = 0.0
        
        return {
            'total_queries': self.cache_stats.total_queries,
            'cache_hits': self.cache_stats.cache_hits,
            'cache_misses': self.cache_stats.cache_misses,
            'hit_rate_percentage': hit_rate,
            'total_saved_time_seconds': self.cache_stats.total_saved_time,
            'avg_cache_lookup_time_ms': (self.cache_stats.total_saved_time / max(self.cache_stats.total_queries, 1)) * 1000
        }
    
    def optimize_query_plan(self, query: str) -> Dict[str, Any]:
        """Analyze and suggest optimizations for a query"""
        suggestions = []
        query_lower = query.lower()
        
        # Check for missing indexes
        if 'where' in query_lower and 'index' not in query_lower:
            suggestions.append({
                'type': 'INDEX',
                'priority': 'HIGH',
                'description': 'Consider adding indexes for WHERE clause columns',
                'impact': 'Can significantly improve query performance'
            })
        
        # Check for SELECT *
        if 'select *' in query_lower:
            suggestions.append({
                'type': 'SELECT',
                'priority': 'MEDIUM',
                'description': 'Avoid SELECT * - specify only needed columns',
                'impact': 'Reduces network traffic and memory usage'
            })
        
        # Check for N+1 queries pattern
        if self.detect_n_plus_one_pattern(query):
            suggestions.append({
                'type': 'N_PLUS_ONE',
                'priority': 'HIGH',
                'description': 'Possible N+1 query pattern detected',
                'impact': 'Consider using JOIN or eager loading to reduce database calls'
            })
        
        # Check for lack of LIMIT
        if 'select' in query_lower and 'limit' not in query_lower and 'count' not in query_lower:
            suggestions.append({
                'type': 'PAGINATION',
                'priority': 'MEDIUM',
                'description': 'Consider adding LIMIT clause for large result sets',
                'impact': 'Prevents memory issues and improves response times'
            })
        
        # Check for inefficient JOINs
        if query_lower.count('join') > 3:
            suggestions.append({
                'type': 'JOIN',
                'priority': 'HIGH',
                'description': 'Multiple JOINs detected - consider query refactoring',
                'impact': 'Complex JOINs can be expensive, consider breaking into smaller queries'
            })
        
        return {
            'query_hash': hashlib.md5(query.encode()).hexdigest(),
            'suggestions': suggestions,
            'complexity_score': self.calculate_query_complexity(query),
            'estimated_cache_benefit': self.estimate_cache_benefit(query)
        }
    
    def detect_n_plus_one_pattern(self, query: str) -> bool:
        """Detect potential N+1 query patterns"""
        # This is a simplified detection - in practice, you'd analyze query patterns over time
        return 'select' in query.lower() and 'where' in query.lower() and '= ?' in query
    
    def calculate_query_complexity(self, query: str) -> int:
        """Calculate a complexity score for a query"""
        query_lower = query.lower()
        complexity = 0
        
        # Count different operations
        complexity += query_lower.count('join') * 2
        complexity += query_lower.count('union') * 3
        complexity += query_lower.count('subquery') * 4
        complexity += query_lower.count('group by') * 2
        complexity += query_lower.count('order by') * 1
        complexity += query_lower.count('having') * 3
        
        # Count functions
        complexity += query_lower.count('sum(') * 1
        complexity += query_lower.count('count(') * 1
        complexity += query_lower.count('avg(') * 1
        complexity += query_lower.count('max(') * 1
        complexity += query_lower.count('min(') * 1
        
        return min(complexity, 100)  # Cap at 100
    
    def estimate_cache_benefit(self, query: str) -> str:
        """Estimate how much caching would benefit this query"""
        complexity = self.calculate_query_complexity(query)
        query_lower = query.lower()
        
        if complexity > 10 and ('group by' in query_lower or 'join' in query_lower):
            return "HIGH"
        elif complexity > 5:
            return "MEDIUM"
        elif 'select' in query_lower and 'where' in query_lower:
            return "LOW"
        else:
            return "MINIMAL"
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        slow_queries = self.get_slow_queries(10)
        frequent_queries = self.get_most_frequent_queries(10)
        cache_perf = self.get_cache_performance()
        
        # Calculate recommendations
        recommendations = []
        
        if len(slow_queries) > 0:
            recommendations.append({
                'type': 'SLOW_QUERIES',
                'priority': 'HIGH',
                'description': f'{len(slow_queries)} slow queries detected',
                'action': 'Review and optimize queries taking >1s to execute'
            })
        
        if cache_perf['hit_rate_percentage'] < 60:
            recommendations.append({
                'type': 'CACHE_OPTIMIZATION',
                'priority': 'HIGH',
                'description': f'Cache hit rate is {cache_perf["hit_rate_percentage"]:.1f}%',
                'action': 'Optimize caching strategy and TTL values'
            })
        
        # Identify most cacheable queries
        cacheable_queries = []
        for stats in frequent_queries:
            if stats.execution_count > 10 and stats.avg_time > 0.1:
                cacheable_queries.append({
                    'query_hash': stats.query_hash,
                    'execution_count': stats.execution_count,
                    'avg_time': stats.avg_time,
                    'potential_savings': stats.execution_count * stats.avg_time
                })
        
        cacheable_queries.sort(key=lambda x: x['potential_savings'], reverse=True)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_unique_queries': len(self.query_stats),
                'slow_queries_count': len(slow_queries),
                'most_executed_query_count': max([s.execution_count for s in self.query_stats.values()], default=0),
                'avg_query_time': sum(s.avg_time for s in self.query_stats.values()) / max(len(self.query_stats), 1)
            },
            'cache_performance': cache_perf,
            'slow_queries': [asdict(sq) for sq in slow_queries[:5]],
            'most_cacheable_queries': cacheable_queries[:5],
            'recommendations': recommendations,
            'query_distribution': self.get_query_distribution()
        }
    
    def get_query_distribution(self) -> Dict[str, int]:
        """Get distribution of query types"""
        distribution = defaultdict(int)
        
        for stats in self.query_stats.values():
            query_lower = stats.query_text.lower()
            if query_lower.startswith('select'):
                distribution['SELECT'] += stats.execution_count
            elif query_lower.startswith('insert'):
                distribution['INSERT'] += stats.execution_count
            elif query_lower.startswith('update'):
                distribution['UPDATE'] += stats.execution_count
            elif query_lower.startswith('delete'):
                distribution['DELETE'] += stats.execution_count
            else:
                distribution['OTHER'] += stats.execution_count
        
        return dict(distribution)
    
    def invalidate_cache_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern"""
        invalidated_count = cache_manager.invalidate_pattern(pattern)
        logger.info(f"Invalidated {invalidated_count} cache entries matching pattern: {pattern}")
        return invalidated_count
    
    def warm_cache(self, warmup_queries: List[Dict[str, Any]]):
        """Pre-populate cache with frequently used queries"""
        warmed_count = 0
        
        for query_config in warmup_queries:
            try:
                query_func = query_config['function']
                params = query_config.get('params', {})
                ttl = query_config.get('ttl', 3600)
                
                # Execute query and cache result
                result = query_func(**params)
                cache_key = f"warmup:{self.generate_cache_key(str(query_config))}"
                cache_manager.set(cache_key, result, ttl=ttl)
                warmed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to warm cache for query: {e}")
        
        logger.info(f"Warmed cache with {warmed_count} queries")
        return warmed_count

# Global query optimizer instance
query_optimizer = QueryOptimizer()

# Convenience decorators for common caching patterns
def cache_query_result(ttl: int = 600, key_prefix: str = "query"):
    """Decorator for caching query results"""
    return query_optimizer.cached_query(ttl=ttl, cache_key_prefix=key_prefix)

def cache_user_data(ttl: int = 1800):
    """Decorator for caching user-related queries"""
    return query_optimizer.cached_query(ttl=ttl, cache_key_prefix="user")

def cache_questions_data(ttl: int = 3600):
    """Decorator for caching questions-related queries"""
    return query_optimizer.cached_query(ttl=ttl, cache_key_prefix="questions")

def cache_analytics_data(ttl: int = 1800):
    """Decorator for caching analytics queries"""
    return query_optimizer.cached_query(ttl=ttl, cache_key_prefix="analytics")

# Utility functions for common optimization patterns
def bulk_query_optimizer(queries: List[str], batch_size: int = 100) -> List[Any]:
    """Optimize multiple queries by batching them"""
    results = []
    
    for i in range(0, len(queries), batch_size):
        batch = queries[i:i + batch_size]
        
        with DatabaseSession() as db:
            batch_results = []
            for query in batch:
                result = db.execute(text(query))
                batch_results.append(result.fetchall())
            
            results.extend(batch_results)
    
    return results

def analyze_query_performance(query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Analyze a single query's performance and optimization opportunities"""
    start_time = time.time()
    
    with DatabaseSession() as db:
        # Execute query and measure time
        result = db.execute(text(query), params or {})
        rows = result.fetchall()
        execution_time = time.time() - start_time
    
    # Update stats
    query_optimizer.update_query_stats(query, execution_time)
    
    # Generate optimization suggestions
    optimization = query_optimizer.optimize_query_plan(query)
    
    return {
        'execution_time': execution_time,
        'row_count': len(rows),
        'optimization_suggestions': optimization,
        'performance_rating': 'GOOD' if execution_time < 0.1 else 'SLOW' if execution_time > 1.0 else 'FAIR'
    }