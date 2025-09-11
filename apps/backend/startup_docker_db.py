#!/usr/bin/env python3
"""
ICFES LEVELING BACKEND - Docker DB Connection
Connects to PostgreSQL running in Docker container with real ICFES questions
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for Docker PostgreSQL connection
os.environ["DATABASE_URL"] = "postgresql://gameplay:gameplay123@localhost:5433/gameplay_db"
os.environ["ENVIRONMENT"] = "development"

import uvicorn
from app.main import app
from app.core.database import engine, Base, get_db
from app.models import user, subject, question, topic, battle, quest, leaderboard, user_event, ai_explanation, notification, subscription
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and show question count"""
    try:
        from sqlalchemy.orm import Session
        from app.models.question import Question
        from app.models.subject import Subject
        
        with Session(engine) as db:
            # Test basic connection
            result = db.execute("SELECT 1").scalar()
            logger.info("✅ Database connection successful")
            
            # Count questions
            question_count = db.query(Question).count()
            logger.info(f"📊 Total questions in database: {question_count}")
            
            # Count by subject
            subjects = db.query(Subject).all()
            for subject in subjects:
                count = db.query(Question).filter(Question.subject_id == subject.id).count()
                logger.info(f"  - {subject.name}: {count} questions")
            
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🚀 ICFES LEVELING BACKEND - DOCKER DB")
    print("=" * 60)
    print("Starting server on http://0.0.0.0:8000")
    print("Database: PostgreSQL Docker on port 5433")
    print("API docs: http://localhost:8000/docs")
    print("=" * 60)
    
    # Test database connection
    if not test_database_connection():
        logger.error("Database connection failed, serving with mock data fallback")
    else:
        logger.info("✅ Connected to PostgreSQL with ICFES questions")
    
    print("\nAvailable endpoints:")
    print("  - GET /api/v1/diagnostic-public/diagnostic-questions/{subject_id}")
    print("  - GET /api/v1/subjects/dynamic")
    print("  - POST /api/v1/auth-simple/login")
    print("=" * 60)
    
    # Start server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()