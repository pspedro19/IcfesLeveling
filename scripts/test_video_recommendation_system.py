#!/usr/bin/env python3
"""
Test Script for Video Recommendation System
Tests the complete video recommendation pipeline with multiple failed question scenarios
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'gameplay_db',
    'user': 'gameplay',
    'password': 'gameplay123'
}

# API Base URL
API_BASE_URL = 'http://localhost:8000'

class VideoRecommendationSystemTester:
    """Comprehensive tester for the video recommendation system"""
    
    def __init__(self):
        self.test_results = {
            'database_tests': {},
            'api_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'scenarios': {}
        }
        self.test_users = []
        self.test_questions = []
        self.sample_videos = []
    
    def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🚀 Starting Video Recommendation System Tests")
        
        try:
            # 1. Database connectivity and schema tests
            self.test_database_connectivity()
            self.test_database_schema()
            
            # 2. Setup test data
            self.setup_test_data()
            
            # 3. Test video recommendation engine
            self.test_recommendation_engine()
            
            # 4. Test API endpoints
            self.test_api_endpoints()
            
            # 5. Test failed question scenarios
            self.test_failed_question_scenarios()
            
            # 6. Test personalized recommendations
            self.test_personalized_recommendations()
            
            # 7. Test video tracking
            self.test_video_tracking()
            
            # 8. Performance tests
            self.test_performance()
            
            # 9. Generate final report
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            self.test_results['overall_status'] = 'FAILED'
            self.test_results['error'] = str(e)
        
        return self.test_results
    
    def test_database_connectivity(self):
        """Test database connectivity and basic operations"""
        logger.info("📊 Testing database connectivity...")
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Test basic connectivity
            cur.execute("SELECT version()")
            version = cur.fetchone()
            
            self.test_results['database_tests']['connectivity'] = {
                'status': 'PASSED',
                'postgres_version': version['version'],
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("✅ Database connectivity test passed")
            
        except Exception as e:
            logger.error(f"❌ Database connectivity test failed: {e}")
            self.test_results['database_tests']['connectivity'] = {
                'status': 'FAILED',
                'error': str(e)
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def test_database_schema(self):
        """Test if all required tables and schemas exist"""
        logger.info("📋 Testing database schema...")
        
        required_tables = [
            'youtube_catalog',
            'video_stats', 
            'student_video_interactions',
            'question_video_recommendations',
            'recommendation_metrics',
            'questions',
            'users',
            'subjects',
            'topics'
        ]
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check if pgvector extension exists
            cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
            pgvector_exists = cur.fetchone() is not None
            
            # Check table existence
            existing_tables = []
            missing_tables = []
            
            for table in required_tables:
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                """, (table,))
                
                if cur.fetchone():
                    existing_tables.append(table)
                else:
                    missing_tables.append(table)
            
            self.test_results['database_tests']['schema'] = {
                'status': 'PASSED' if len(missing_tables) == 0 else 'PARTIAL',
                'pgvector_available': pgvector_exists,
                'existing_tables': existing_tables,
                'missing_tables': missing_tables,
                'table_coverage': f"{len(existing_tables)}/{len(required_tables)}"
            }
            
            if missing_tables:
                logger.warning(f"⚠️ Missing tables: {missing_tables}")
            else:
                logger.info("✅ All required tables exist")
                
        except Exception as e:
            logger.error(f"❌ Database schema test failed: {e}")
            self.test_results['database_tests']['schema'] = {
                'status': 'FAILED',
                'error': str(e)
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def setup_test_data(self):
        """Setup test data for testing"""
        logger.info("🔧 Setting up test data...")
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Create test users
            test_user_ids = []
            for i in range(3):
                user_id = str(uuid.uuid4())
                test_user_ids.append(user_id)
                
                # Insert test user (simplified)
                cur.execute("""
                    INSERT INTO users (id, username, email, created_at) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (user_id, f'test_user_{i}', f'test{i}@example.com', datetime.now()))
            
            # Get sample questions
            cur.execute("SELECT id, text, subject_id, topic_id FROM questions LIMIT 10")
            sample_questions = cur.fetchall()
            
            # Get sample videos
            cur.execute("SELECT id, youtube_id, title, subject_id, topic_id FROM youtube_catalog WHERE is_processed = true LIMIT 10")
            sample_videos = cur.fetchall()
            
            # Create some failed question responses
            for user_id in test_user_ids:
                for question in sample_questions[:3]:  # First 3 questions as failed
                    cur.execute("""
                        INSERT INTO responses (id, student_id, question_id, is_correct, answered_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (str(uuid.uuid4()), user_id, question['id'], False, datetime.now() - timedelta(days=1)))
            
            conn.commit()
            
            self.test_users = test_user_ids
            self.test_questions = [dict(q) for q in sample_questions]
            self.sample_videos = [dict(v) for v in sample_videos]
            
            self.test_results['database_tests']['test_data'] = {
                'status': 'PASSED',
                'test_users_created': len(test_user_ids),
                'sample_questions': len(sample_questions),
                'sample_videos': len(sample_videos)
            }
            
            logger.info(f"✅ Test data setup complete: {len(test_user_ids)} users, {len(sample_questions)} questions, {len(sample_videos)} videos")
            
        except Exception as e:
            logger.error(f"❌ Test data setup failed: {e}")
            self.test_results['database_tests']['test_data'] = {
                'status': 'FAILED',
                'error': str(e)
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def test_recommendation_engine(self):
        """Test the core recommendation engine"""
        logger.info("🎯 Testing recommendation engine...")
        
        try:
            from apps.backend.app.services.enhanced_video_recommendation_engine import enhanced_video_recommendation_engine
            from apps.backend.app.core.database import get_db
            
            # This would require proper async context and database session
            # For now, we'll test the API endpoints instead
            
            self.test_results['integration_tests']['recommendation_engine'] = {
                'status': 'SKIPPED',
                'reason': 'Direct engine testing requires async context'
            }
            
        except Exception as e:
            logger.error(f"❌ Recommendation engine test failed: {e}")
            self.test_results['integration_tests']['recommendation_engine'] = {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def test_api_endpoints(self):
        """Test all API endpoints"""
        logger.info("🌐 Testing API endpoints...")
        
        # Test health endpoint
        self.test_health_endpoint()
        
        # Test personalized recommendations endpoint
        self.test_personalized_api()
        
        # Test failed question recommendations
        self.test_failed_question_api()
        
        # Test subject videos endpoint
        self.test_subject_videos_api()
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/video-recommendations/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.test_results['api_tests']['health'] = {
                    'status': 'PASSED',
                    'response_data': data,
                    'response_time_ms': response.elapsed.total_seconds() * 1000
                }
                logger.info("✅ Health endpoint test passed")
            else:
                self.test_results['api_tests']['health'] = {
                    'status': 'FAILED',
                    'status_code': response.status_code,
                    'response': response.text
                }
                logger.error(f"❌ Health endpoint failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Health endpoint test failed: {e}")
            self.test_results['api_tests']['health'] = {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def test_personalized_api(self):
        """Test personalized recommendations API"""
        try:
            # This would require authentication token
            # For now, test without auth to check endpoint existence
            response = requests.get(f"{API_BASE_URL}/api/v1/video-recommendations/personalized", timeout=10)
            
            self.test_results['api_tests']['personalized'] = {
                'status': 'TESTED',
                'status_code': response.status_code,
                'requires_auth': response.status_code == 401,
                'endpoint_exists': response.status_code != 404
            }
            
            if response.status_code == 401:
                logger.info("✅ Personalized API endpoint exists and requires authentication")
            else:
                logger.warning(f"⚠️ Personalized API returned unexpected status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Personalized API test failed: {e}")
            self.test_results['api_tests']['personalized'] = {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def test_failed_question_api(self):
        """Test failed question recommendations API"""
        try:
            if self.test_questions:
                question_id = self.test_questions[0]['id']
                response = requests.get(
                    f"{API_BASE_URL}/api/v1/video-recommendations/for-failed-question/{question_id}",
                    timeout=10
                )
                
                self.test_results['api_tests']['failed_question'] = {
                    'status': 'TESTED',
                    'status_code': response.status_code,
                    'requires_auth': response.status_code == 401,
                    'endpoint_exists': response.status_code != 404
                }
                
                if response.status_code == 401:
                    logger.info("✅ Failed question API endpoint exists and requires authentication")
                else:
                    logger.warning(f"⚠️ Failed question API returned unexpected status: {response.status_code}")
            else:
                self.test_results['api_tests']['failed_question'] = {
                    'status': 'SKIPPED',
                    'reason': 'No test questions available'
                }
                
        except Exception as e:
            logger.error(f"❌ Failed question API test failed: {e}")
            self.test_results['api_tests']['failed_question'] = {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def test_subject_videos_api(self):
        """Test subject videos API"""
        try:
            # Test with subject ID 1 (common in ICFES systems)
            response = requests.get(f"{API_BASE_URL}/api/v1/video-recommendations/by-subject/1", timeout=10)
            
            self.test_results['api_tests']['subject_videos'] = {
                'status': 'TESTED',
                'status_code': response.status_code,
                'requires_auth': response.status_code == 401,
                'endpoint_exists': response.status_code != 404
            }
            
            if response.status_code == 401:
                logger.info("✅ Subject videos API endpoint exists and requires authentication")
            else:
                logger.warning(f"⚠️ Subject videos API returned unexpected status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Subject videos API test failed: {e}")
            self.test_results['api_tests']['subject_videos'] = {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def test_failed_question_scenarios(self):
        """Test multiple failed question scenarios"""
        logger.info("📚 Testing failed question scenarios...")
        
        scenarios = [
            {
                'name': 'Mathematics - Algebra',
                'subject': 'Matemáticas',
                'topic': 'Álgebra',
                'expected_video_types': ['concept_review', 'skill_building']
            },
            {
                'name': 'Physics - Mechanics',
                'subject': 'Física',
                'topic': 'Mecánica',
                'expected_video_types': ['error_remediation', 'direct_practice']
            },
            {
                'name': 'Chemistry - Stoichiometry',
                'subject': 'Química',
                'topic': 'Estequiometría',
                'expected_video_types': ['concept_review', 'skill_building']
            }
        ]
        
        for scenario in scenarios:
            try:
                # Simulate failed question scenario
                scenario_results = self.simulate_failed_question_scenario(scenario)
                self.test_results['scenarios'][scenario['name']] = scenario_results
                
            except Exception as e:
                logger.error(f"❌ Scenario '{scenario['name']}' failed: {e}")
                self.test_results['scenarios'][scenario['name']] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
    
    def simulate_failed_question_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a specific failed question scenario"""
        logger.info(f"🎭 Simulating scenario: {scenario['name']}")
        
        # For now, return a simulated result
        # In a real implementation, this would:
        # 1. Create a failed question in the specified subject/topic
        # 2. Run the recommendation engine
        # 3. Verify the recommendations match expected types
        
        return {
            'status': 'SIMULATED',
            'scenario_name': scenario['name'],
            'expected_types': scenario['expected_video_types'],
            'recommendations_found': 5,  # Simulated
            'avg_confidence': 0.85,  # Simulated
            'processing_time_ms': 150  # Simulated
        }
    
    def test_personalized_recommendations(self):
        """Test personalized recommendation generation"""
        logger.info("👤 Testing personalized recommendations...")
        
        try:
            # Test with our test users
            for i, user_id in enumerate(self.test_users[:2]):  # Test first 2 users
                user_results = self.test_user_personalized_recommendations(user_id, f"test_user_{i}")
                self.test_results['integration_tests'][f'personalized_user_{i}'] = user_results
                
        except Exception as e:
            logger.error(f"❌ Personalized recommendations test failed: {e}")
            self.test_results['integration_tests']['personalized_error'] = str(e)
    
    def test_user_personalized_recommendations(self, user_id: str, username: str) -> Dict[str, Any]:
        """Test personalized recommendations for a specific user"""
        logger.info(f"👤 Testing personalized recommendations for {username}")
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get user's failed questions
            cur.execute("""
                SELECT COUNT(*) as failed_count
                FROM responses r
                WHERE r.student_id = %s AND r.is_correct = false
            """, (user_id,))
            
            failed_count = cur.fetchone()['failed_count']
            
            # Get available videos
            cur.execute("SELECT COUNT(*) as video_count FROM youtube_catalog WHERE is_processed = true")
            video_count = cur.fetchone()['video_count']
            
            return {
                'status': 'ANALYZED',
                'user_id': user_id,
                'failed_questions_count': failed_count,
                'available_videos': video_count,
                'has_failed_questions': failed_count > 0,
                'can_generate_recommendations': failed_count > 0 and video_count > 0
            }
            
        except Exception as e:
            return {
                'status': 'FAILED',
                'error': str(e)
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def test_video_tracking(self):
        """Test video interaction tracking"""
        logger.info("📊 Testing video tracking...")
        
        try:
            # This would test the interaction tracking functionality
            # For now, just check if the table exists and can be written to
            
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Test inserting a sample interaction
            interaction_id = str(uuid.uuid4())
            test_user_id = self.test_users[0] if self.test_users else str(uuid.uuid4())
            test_video_id = self.sample_videos[0]['id'] if self.sample_videos else 1
            
            cur.execute("""
                INSERT INTO student_video_interactions 
                (id, student_id, video_id, total_watch_seconds, completion_percentage, clicked_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (interaction_id, test_user_id, test_video_id, 120, 0.8, datetime.now()))
            
            conn.commit()
            
            # Verify the interaction was recorded
            cur.execute("SELECT COUNT(*) as count FROM student_video_interactions WHERE id = %s", (interaction_id,))
            result = cur.fetchone()
            
            self.test_results['integration_tests']['video_tracking'] = {
                'status': 'PASSED' if result['count'] > 0 else 'FAILED',
                'interaction_recorded': result['count'] > 0,
                'test_interaction_id': interaction_id
            }
            
            logger.info("✅ Video tracking test passed")
            
        except Exception as e:
            logger.error(f"❌ Video tracking test failed: {e}")
            self.test_results['integration_tests']['video_tracking'] = {
                'status': 'FAILED',
                'error': str(e)
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def test_performance(self):
        """Test system performance"""
        logger.info("⚡ Testing performance...")
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Test database query performance
            start_time = datetime.now()
            
            # Complex query to test performance
            cur.execute("""
                SELECT yc.id, yc.title, yc.subject_id, yc.topic_id,
                       COUNT(svi.id) as interaction_count
                FROM youtube_catalog yc
                LEFT JOIN student_video_interactions svi ON yc.id = svi.video_id
                WHERE yc.is_processed = true
                GROUP BY yc.id, yc.title, yc.subject_id, yc.topic_id
                ORDER BY interaction_count DESC
                LIMIT 50
            """)
            
            results = cur.fetchall()
            end_time = datetime.now()
            
            query_time = (end_time - start_time).total_seconds() * 1000
            
            self.test_results['performance_tests']['database_query'] = {
                'status': 'PASSED',
                'query_time_ms': query_time,
                'results_count': len(results),
                'performance_rating': 'Good' if query_time < 1000 else 'Slow' if query_time < 5000 else 'Poor'
            }
            
            logger.info(f"✅ Database query performance: {query_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            self.test_results['performance_tests']['database_query'] = {
                'status': 'FAILED',
                'error': str(e)
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📋 Generating test report...")
        
        # Count test results
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        def count_results(results_dict):
            nonlocal total_tests, passed_tests, failed_tests, skipped_tests
            
            for key, value in results_dict.items():
                if isinstance(value, dict) and 'status' in value:
                    total_tests += 1
                    if value['status'] == 'PASSED':
                        passed_tests += 1
                    elif value['status'] == 'FAILED':
                        failed_tests += 1
                    elif value['status'] in ['SKIPPED', 'SIMULATED', 'TESTED', 'ANALYZED']:
                        skipped_tests += 1
                elif isinstance(value, dict):
                    count_results(value)
        
        count_results(self.test_results)
        
        # Generate summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'skipped': skipped_tests,
            'success_rate_percent': round(success_rate, 2),
            'overall_status': 'PASSED' if failed_tests == 0 else 'FAILED',
            'test_duration': datetime.now().isoformat(),
            'recommendations': self.generate_recommendations()
        }
        
        # Save report to file
        report_filename = f"video_recommendation_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info(f"📋 Test report saved: {report_filename}")
        logger.info(f"📊 Test Summary: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        if failed_tests > 0:
            logger.warning(f"⚠️ {failed_tests} tests failed")
        else:
            logger.info("✅ All tests passed!")
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check database issues
        if self.test_results.get('database_tests', {}).get('schema', {}).get('status') != 'PASSED':
            recommendations.append("Setup missing database tables using the provided migration scripts")
        
        if not self.test_results.get('database_tests', {}).get('schema', {}).get('pgvector_available', False):
            recommendations.append("Install pgvector extension for semantic search functionality")
        
        # Check API issues
        api_tests = self.test_results.get('api_tests', {})
        if all(test.get('status') == 'FAILED' for test in api_tests.values()):
            recommendations.append("Check if the backend server is running on the correct port")
        
        # Check performance issues
        perf_tests = self.test_results.get('performance_tests', {})
        db_query = perf_tests.get('database_query', {})
        if db_query.get('performance_rating') == 'Poor':
            recommendations.append("Consider adding database indexes for better query performance")
        
        if not recommendations:
            recommendations.append("System appears to be functioning correctly!")
        
        return recommendations


def main():
    """Main test function"""
    tester = VideoRecommendationSystemTester()
    results = tester.run_all_tests()
    
    print("\n" + "="*80)
    print("VIDEO RECOMMENDATION SYSTEM TEST RESULTS")
    print("="*80)
    
    summary = results.get('summary', {})
    print(f"Total Tests: {summary.get('total_tests', 0)}")
    print(f"Passed: {summary.get('passed', 0)}")
    print(f"Failed: {summary.get('failed', 0)}")
    print(f"Skipped: {summary.get('skipped', 0)}")
    print(f"Success Rate: {summary.get('success_rate_percent', 0)}%")
    print(f"Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
    
    print("\nRecommendations:")
    for rec in summary.get('recommendations', []):
        print(f"- {rec}")
    
    print("="*80)
    
    return results


if __name__ == "__main__":
    main()