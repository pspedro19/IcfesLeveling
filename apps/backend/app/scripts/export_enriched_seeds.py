#!/usr/bin/env python3
"""
Script to export enriched video data and mapping links to JSON/CSV for seeding.
This ensures that expensive computations (transcripts, embeddings, matching) can be reused.
"""

import logging
import sys
import os
import json
import csv
from pathlib import Path
from datetime import datetime

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal
from app.models.youtube_catalog import YoutubeCatalog
from app.models.question_video_recommendations import QuestionVideoRecommendations
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXPORT_DIR = Path("/app/database/seed_data/enriched")

def export_youtube_catalog(db: Session, export_dir: Path):
    """Export enriched YoutubeCatalog to JSON"""
    logger.info("📦 Exporting YoutubeCatalog...")
    
    videos = db.query(YoutubeCatalog).order_by(YoutubeCatalog.id).all()
    data = [video.to_dict() for video in videos]
    
    # Clean up dates for JSON serialization (handled in to_dict but verifying)
    output_file = export_dir / "youtube_catalog_enriched.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    logger.info(f"✅ Exported {len(data)} videos to {output_file}")

def export_video_recommendations(db: Session, export_dir: Path):
    """Export QuestionVideoRecommendations to CSV for fast loading"""
    logger.info("📦 Exporting QuestionVideoRecommendations...")
    
    recommendations = db.query(QuestionVideoRecommendations).all()
    
    if not recommendations:
        logger.warning("⚠️ No recommendations found to export.")
        return

    output_file = export_dir / "question_video_links_seeded.csv"
    
    # Define CSV fields
    fields = [
        'question_id', 'video_id', 'total_score', 
        'recommendation_type', 'error_pattern_addressed',
        'is_active', 'created_at'
    ]
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        
        count = 0
        for rec in recommendations:
            writer.writerow({
                'question_id': str(rec.question_id),
                'video_id': rec.video_id,
                'total_score': float(rec.total_score),
                'recommendation_type': rec.recommendation_type,
                'error_pattern_addressed': rec.error_pattern_addressed,
                'is_active': rec.is_active,
                'created_at': rec.created_at.isoformat() if rec.created_at else datetime.utcnow().isoformat()
            })
            count += 1
            
    logger.info(f"✅ Exported {count} recommendations to {output_file}")

def main():
    if not EXPORT_DIR.exists():
        os.makedirs(EXPORT_DIR, exist_ok=True)
        
    db = SessionLocal()
    try:
        export_youtube_catalog(db, EXPORT_DIR)
        export_video_recommendations(db, EXPORT_DIR)
        logger.info("🎉 All exports completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during export: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
