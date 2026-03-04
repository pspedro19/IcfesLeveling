#!/usr/bin/env python3
"""
Script to execute the batch video-question mapping process.
Ref: apps/backend/app/services/question_video_mapping_service.py
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal
from app.services.question_video_mapping_service import QuestionVideoMappingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Starting Video-Question Mapping Process")
    
    db = SessionLocal()
    try:
        service = QuestionVideoMappingService()
        
        # Calculate stats for all questions
        stats = await service.batch_generate_recommendations(
            db=db,
            batch_size=20
        )
        
        logger.info(f"✅ Mapping Completed!")
        logger.info(f"📊 Stats: {stats}")
        
    except Exception as e:
        logger.error(f"❌ Error during mapping: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
