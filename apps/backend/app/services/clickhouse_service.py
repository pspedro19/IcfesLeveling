from clickhouse_driver import Client
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from ..core.config import settings
import json
import time

logger = logging.getLogger(__name__)

class ClickHouseService:
    def __init__(self):
        self.client = None
        self.connected = False
        self.connect()
    
    def connect(self, max_retries=3):
        """Connect to ClickHouse with retry logic"""
        for attempt in range(max_retries):
            try:
                self.client = Client(
                    host='clickhouse',
                    port=9000,
                    user='default',
                    password='clickhouse123',
                    database='gameplay_analytics',
                    connect_timeout=5,
                    send_receive_timeout=10
                )
                # Test connection
                self.client.execute('SELECT 1')
                self.connected = True
                logger.info("Successfully connected to ClickHouse")
                return
            except Exception as e:
                logger.warning(f"ClickHouse connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("Failed to connect to ClickHouse after all retries")
                    self.connected = False
    
    def _ensure_connection(self):
        """Ensure ClickHouse connection is active"""
        if not self.connected or not self.client:
            self.connect()
    
    def insert_event(self, event_type: str, user_id: str, event_data: Dict[str, Any], 
                    session_id: str = None, platform: str = 'web'):
        """Insert a single event into ClickHouse"""
        try:
            self._ensure_connection()
            if not self.connected:
                logger.warning("ClickHouse not connected, skipping event insertion")
                return
            
            query = """
            INSERT INTO game_events 
            (event_time, user_id, event_type, event_data, session_id, platform)
            VALUES
            """
            
            self.client.execute(
                query,
                [(
                    datetime.now(),
                    user_id,
                    event_type,
                    json.dumps(event_data),
                    session_id or '',
                    platform
                )]
            )
            logger.info(f"Event inserted: {event_type} for user {user_id}")
        except Exception as e:
            logger.error(f"Error inserting event: {e}")
            # Don't raise the exception to prevent 500 errors
            # Just log and continue
    
    def insert_batch_events(self, events: List[Dict[str, Any]]):
        """Insert multiple events in batch"""
        try:
            self._ensure_connection()
            if not self.connected:
                logger.warning("ClickHouse not connected, skipping batch event insertion")
                return
            
            query = """
            INSERT INTO game_events 
            (event_time, user_id, event_type, event_data, session_id, platform)
            VALUES
            """
            
            data = [
                (
                    event.get('event_time', datetime.now()),
                    event['user_id'],
                    event['event_type'],
                    json.dumps(event.get('event_data', {})),
                    event.get('session_id', ''),
                    event.get('platform', 'web')
                )
                for event in events
            ]
            
            self.client.execute(query, data)
            logger.info(f"Batch inserted {len(events)} events")
        except Exception as e:
            logger.error(f"Error inserting batch events: {e}")
            # Don't raise the exception to prevent 500 errors
            # Just log and continue
    
    def track_battle_analytics(self, battle_data: Dict[str, Any]):
        """Track battle analytics data"""
        try:
            query = """
            INSERT INTO battle_analytics
            (battle_id, user_id, battle_type, enemy_name, enemy_level,
             questions_answered, correct_answers, total_damage_dealt,
             total_damage_received, experience_gained, orbs_gained,
             duration_seconds, status, created_at, completed_at)
            VALUES
            """
            
            self.client.execute(
                query,
                [(
                    battle_data['battle_id'],
                    battle_data['user_id'],
                    battle_data['battle_type'],
                    battle_data['enemy_name'],
                    battle_data['enemy_level'],
                    battle_data['questions_answered'],
                    battle_data['correct_answers'],
                    battle_data['total_damage_dealt'],
                    battle_data['total_damage_received'],
                    battle_data['experience_gained'],
                    battle_data['orbs_gained'],
                    battle_data['duration_seconds'],
                    battle_data['status'],
                    battle_data.get('created_at', datetime.now()),
                    battle_data.get('completed_at', datetime.now())
                )]
            )
            logger.info(f"Battle analytics tracked for battle {battle_data['battle_id']}")
        except Exception as e:
            logger.error(f"Error tracking battle analytics: {e}")
            raise
    
    def track_question_performance(self, performance_data: Dict[str, Any]):
        """Track question performance data"""
        try:
            query = """
            INSERT INTO question_performance
            (question_id, user_id, subject_id, topic_id, difficulty,
             user_answer, correct_answer, is_correct, response_time_ms,
             damage_dealt, damage_received, critical_hit, battle_id, created_at)
            VALUES
            """
            
            self.client.execute(
                query,
                [(
                    performance_data['question_id'],
                    performance_data['user_id'],
                    performance_data['subject_id'],
                    performance_data['topic_id'],
                    performance_data['difficulty'],
                    performance_data['user_answer'],
                    performance_data['correct_answer'],
                    1 if performance_data['is_correct'] else 0,
                    performance_data['response_time_ms'],
                    performance_data.get('damage_dealt', 0),
                    performance_data.get('damage_received', 0),
                    1 if performance_data.get('critical_hit', False) else 0,
                    performance_data.get('battle_id', ''),
                    datetime.now()
                )]
            )
        except Exception as e:
            logger.error(f"Error tracking question performance: {e}")
            raise
    
    def update_user_progression(self, user_data: Dict[str, Any]):
        """Update user progression snapshot"""
        try:
            query = """
            INSERT INTO user_progression
            (user_id, level, experience, rank, hp, mp, power, wisdom, speed,
             orbs, crystals, streak_days, recorded_at)
            VALUES
            """
            
            self.client.execute(
                query,
                [(
                    user_data['user_id'],
                    user_data['level'],
                    user_data['experience'],
                    user_data['rank'],
                    user_data['hp'],
                    user_data['mp'],
                    user_data['power'],
                    user_data['wisdom'],
                    user_data['speed'],
                    user_data['orbs'],
                    user_data['crystals'],
                    user_data['streak_days'],
                    datetime.now()
                )]
            )
        except Exception as e:
            logger.error(f"Error updating user progression: {e}")
            raise
    
    def get_user_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user analytics for the specified period"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get battle statistics
            battle_stats = self.client.execute(f"""
                SELECT 
                    count() as total_battles,
                    sum(questions_answered) as total_questions,
                    sum(correct_answers) as total_correct,
                    avg(duration_seconds) as avg_duration,
                    sum(experience_gained) as total_experience,
                    sum(orbs_gained) as total_orbs
                FROM battle_analytics
                WHERE user_id = '{user_id}' 
                AND created_at >= '{start_date.isoformat()}'
            """)[0]
            
            # Get question performance by topic
            topic_performance = self.client.execute(f"""
                SELECT 
                    topic_id,
                    count() as questions_count,
                    sum(is_correct) as correct_count,
                    avg(response_time_ms) as avg_response_time
                FROM question_performance
                WHERE user_id = '{user_id}'
                AND created_at >= '{start_date.isoformat()}'
                GROUP BY topic_id
            """)
            
            # Get daily activity
            daily_activity = self.client.execute(f"""
                SELECT 
                    toDate(created_at) as date,
                    count() as battles_count,
                    sum(correct_answers) / sum(questions_answered) as accuracy
                FROM battle_analytics
                WHERE user_id = '{user_id}'
                AND created_at >= '{start_date.isoformat()}'
                GROUP BY date
                ORDER BY date
            """)
            
            # Get progression history
            progression = self.client.execute(f"""
                SELECT 
                    recorded_at,
                    level,
                    experience,
                    rank,
                    streak_days
                FROM user_progression
                WHERE user_id = '{user_id}'
                AND recorded_at >= '{start_date.isoformat()}'
                ORDER BY recorded_at
                LIMIT 100
            """)
            
            return {
                'battle_stats': {
                    'total_battles': battle_stats[0],
                    'total_questions': battle_stats[1],
                    'total_correct': battle_stats[2],
                    'accuracy': (battle_stats[2] / battle_stats[1] * 100) if battle_stats[1] > 0 else 0,
                    'avg_duration': battle_stats[3],
                    'total_experience': battle_stats[4],
                    'total_orbs': battle_stats[5]
                },
                'topic_performance': [
                    {
                        'topic_id': row[0],
                        'questions_count': row[1],
                        'correct_count': row[2],
                        'accuracy': (row[2] / row[1] * 100) if row[1] > 0 else 0,
                        'avg_response_time': row[3]
                    }
                    for row in topic_performance
                ],
                'daily_activity': [
                    {
                        'date': row[0].isoformat(),
                        'battles_count': row[1],
                        'accuracy': row[2] * 100 if row[2] else 0
                    }
                    for row in daily_activity
                ],
                'progression': [
                    {
                        'recorded_at': row[0].isoformat(),
                        'level': row[1],
                        'experience': row[2],
                        'rank': row[3],
                        'streak_days': row[4]
                    }
                    for row in progression
                ]
            }
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            raise
    
    def get_global_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get global analytics for the platform"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get overall statistics
            overall_stats = self.client.execute(f"""
                SELECT 
                    count(DISTINCT user_id) as unique_users,
                    count() as total_events,
                    count(DISTINCT session_id) as total_sessions
                FROM game_events
                WHERE event_time >= '{start_date.isoformat()}'
            """)[0]
            
            # Get event type distribution
            event_distribution = self.client.execute(f"""
                SELECT 
                    event_type,
                    count() as event_count
                FROM game_events
                WHERE event_time >= '{start_date.isoformat()}'
                GROUP BY event_type
                ORDER BY event_count DESC
                LIMIT 20
            """)
            
            # Get top players
            top_players = self.client.execute(f"""
                SELECT 
                    user_id,
                    sum(experience_gained) as total_experience,
                    count() as battles_count,
                    sum(correct_answers) / sum(questions_answered) as accuracy
                FROM battle_analytics
                WHERE created_at >= '{start_date.isoformat()}'
                GROUP BY user_id
                ORDER BY total_experience DESC
                LIMIT 10
            """)
            
            # Get popular battle types
            popular_battles = self.client.execute(f"""
                SELECT 
                    battle_type,
                    count() as battle_count,
                    avg(questions_answered) as avg_questions,
                    avg(correct_answers / questions_answered) as avg_accuracy
                FROM battle_analytics
                WHERE created_at >= '{start_date.isoformat()}'
                GROUP BY battle_type
                ORDER BY battle_count DESC
            """)
            
            # Get daily metrics
            daily_metrics = self.client.execute(f"""
                SELECT 
                    toDate(created_at) as date,
                    count(DISTINCT user_id) as active_users,
                    count() as total_battles,
                    sum(questions_answered) as total_questions,
                    sum(correct_answers) as correct_answers,
                    sum(experience_gained) as total_experience
                FROM battle_analytics
                WHERE created_at >= '{start_date.isoformat()}'
                GROUP BY date
                ORDER BY date
            """)
            
            return {
                'overall_stats': {
                    'unique_users': overall_stats[0],
                    'total_events': overall_stats[1],
                    'total_sessions': overall_stats[2]
                },
                'event_distribution': [
                    {
                        'event_type': row[0],
                        'count': row[1]
                    }
                    for row in event_distribution
                ],
                'top_players': [
                    {
                        'user_id': row[0],
                        'total_experience': row[1],
                        'battles_count': row[2],
                        'accuracy': row[3] * 100 if row[3] else 0
                    }
                    for row in top_players
                ],
                'popular_battles': [
                    {
                        'battle_type': row[0],
                        'count': row[1],
                        'avg_questions': row[2],
                        'avg_accuracy': row[3] * 100 if row[3] else 0
                    }
                    for row in popular_battles
                ],
                'daily_metrics': [
                    {
                        'date': row[0].isoformat(),
                        'active_users': row[1],
                        'total_battles': row[2],
                        'total_questions': row[3],
                        'correct_answers': row[4],
                        'total_experience': row[5],
                        'accuracy': (row[4] / row[3] * 100) if row[3] > 0 else 0
                    }
                    for row in daily_metrics
                ]
            }
        except Exception as e:
            logger.error(f"Error getting global analytics: {e}")
            raise
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Generate daily analytics report"""
        try:
            # This would be called by a scheduled task
            yesterday = datetime.now() - timedelta(days=1)
            
            daily_stats = self.client.execute(f"""
                SELECT 
                    count(DISTINCT user_id) as active_users,
                    count() as total_battles,
                    sum(questions_answered) as total_questions,
                    sum(correct_answers) as correct_answers,
                    sum(experience_gained) as total_experience,
                    sum(orbs_gained) as total_orbs,
                    avg(duration_seconds) as avg_session_duration
                FROM battle_analytics
                WHERE toDate(created_at) = toDate('{yesterday.isoformat()}')
            """)[0]
            
            # Insert into daily metrics table
            self.client.execute("""
                INSERT INTO daily_metrics
                (date, total_users, active_users, total_battles, 
                 total_questions_answered, correct_answers, 
                 total_experience_gained, total_orbs_gained, 
                 avg_session_duration, retention_rate)
                VALUES
            """, [(
                yesterday.date(),
                daily_stats[0],  # total_users (same as active for now)
                daily_stats[0],  # active_users
                daily_stats[1],  # total_battles
                daily_stats[2],  # total_questions
                daily_stats[3],  # correct_answers
                daily_stats[4],  # total_experience
                daily_stats[5],  # total_orbs
                int(daily_stats[6]),  # avg_session_duration
                0.0  # retention_rate (calculated separately)
            )])
            
            return {
                'date': yesterday.date().isoformat(),
                'active_users': daily_stats[0],
                'total_battles': daily_stats[1],
                'accuracy': (daily_stats[3] / daily_stats[2] * 100) if daily_stats[2] > 0 else 0,
                'total_experience': daily_stats[4],
                'avg_session_duration': daily_stats[6]
            }
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            raise

# Singleton instance
clickhouse_service = ClickHouseService()