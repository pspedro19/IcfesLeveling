#!/usr/bin/env python3
"""
Script to enrich video metadata (transcripts, concepts) using YouTube Transcript API and Content Analysis.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import List, Optional

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal
from app.models.youtube_catalog import YoutubeCatalog
from app.services.video_content_analysis_service import VideoContentAnalysisService

# Try importing youtube_transcript_api
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    print("⚠️ youtube_transcript_api not found. Transcript fetching will be simulated or skipped.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoEnricher:
    def __init__(self, db_session):
        self.db = db_session
        self.analysis_service = VideoContentAnalysisService(db_session)
        
    def fetch_transcript(self, video_id: str) -> Optional[str]:
        """Fetch transcript using unofficial API"""
        if not YOUTUBE_API_AVAILABLE:
            return None
            
        try:
            # Prefer Spanish, fallback to English
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
            
            # Combine text
            full_text = " ".join([item['text'] for item in transcript_list])
            return full_text
            
        except Exception as e:
            logger.warning(f"Could not fetch transcript for {video_id}: {e}")
            return None

    async def process_videos(self, limit: int = 50):
        """Process a batch of videos"""
        videos = self.db.query(YoutubeCatalog).order_by(YoutubeCatalog.updated_at.asc()).limit(limit).all()
        
        stats = {"processed": 0, "transcripts_found": 0, "analyzed": 0}
        
        for video in videos:
            logger.info(f"Processing video: {video.title[:50]}... ({video.youtube_id})")
            
            # 1. Fetch Transcript if missing
            if not video.transcript:
                transcript = self.fetch_transcript(video.youtube_id)
                if transcript:
                    video.transcript = transcript
                    stats["transcripts_found"] += 1
                    logger.info(f"  ✓ Transcript fetched ({len(transcript)} chars)")
                else:
                    logger.info("  - No transcript available")
            
            # 2. Analyze Content (using available text)
            try:
                features = await self.analysis_service.analyze_video_content(video.id)
                stats["analyzed"] += 1
                logger.info(f"  ✓ Content analyzed: {len(features.keywords)} keywords, {len(features.concepts)} concepts")
            except Exception as e:
                logger.error(f"  ❌ Analysis failed: {e}")
            
            stats["processed"] += 1
            
        self.db.commit()
        return stats

async def main():
    logger.info("🚀 Starting Video Enrichment Process")
    
    db = SessionLocal()
    try:
        enricher = VideoEnricher(db)
        
        # Process all videos in batches
        total_stats = {"processed": 0, "transcripts_found": 0, "analyzed": 0}
        
        while True:
            stats = await enricher.process_videos(limit=20)
            if stats["processed"] == 0:
                break
                
            total_stats["processed"] += stats["processed"]
            total_stats["transcripts_found"] += stats["transcripts_found"]
            total_stats["analyzed"] += stats["analyzed"]
            
            logger.info(f"--- Batch Stats: {stats} ---")
            # Break after one batch for testing/demo purposes unless specified otherwise
            # User asked to "proceed", assuming full run might be slow without async concurrency control in fetching
            # For this context, running one pass or until completion?
            # Let's run until completion but careful with rate limits if fetching real data.
            # Since we likely don't have the lib, it will skip quickly.
            if stats["processed"] < 20: 
                break
        
        logger.info(f"✅ Enrichment Completed!")
        logger.info(f"📊 Total Stats: {total_stats}")
        
    except Exception as e:
        logger.error(f"❌ Error during enrichment: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
