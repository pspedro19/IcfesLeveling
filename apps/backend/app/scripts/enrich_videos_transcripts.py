#!/usr/bin/env python3
"""
Script to enrich youtube_videos with transcripts from YouTube
Uses youtube-transcript-api v1.2.3+ with new API syntax
"""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from youtube_transcript_api import YouTubeTranscriptApi
from sqlalchemy import text
from app.core.database import SessionLocal


def extract_keywords(text_content, min_length=4, top_n=20):
    """Extract keywords from text"""
    words = re.findall(r'\b[a-záéíóúñü]+\b', text_content.lower())

    stopwords = {
        'para', 'como', 'este', 'esta', 'estos', 'estas', 'pero', 'porque',
        'cuando', 'donde', 'cual', 'entre', 'sobre', 'desde', 'hasta',
        'entonces', 'ahora', 'esto', 'eso', 'todo', 'toda', 'todos', 'todas',
        'algo', 'cada', 'otro', 'otra', 'otros', 'otras', 'mismo', 'mucho',
        'poco', 'muy', 'más', 'menos', 'bien', 'que', 'del', 'los', 'las',
        'una', 'unos', 'unas', 'ella', 'ellos', 'ellas', 'con', 'sin', 'por',
        'tiene', 'hacer', 'dice', 'decir', 'puede', 'vamos', 'tenemos', 'tiene',
        'están', 'están', 'siendo', 'sido', 'será', 'sería', 'hecho', 'hacer'
    }

    filtered = [w for w in words if len(w) >= min_length and w not in stopwords]

    freq = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]


def main():
    db = SessionLocal()
    api = YouTubeTranscriptApi()  # Create instance (new API v1.2.3+)

    try:
        videos = db.execute(text(
            'SELECT id, youtube_id, title FROM youtube_videos WHERE transcript IS NULL'
        )).fetchall()

        print(f"🎬 Processing {len(videos)} videos without transcripts...")

        stats = {'success': 0, 'no_transcript': 0, 'error': 0}

        for i, (vid, youtube_id, title) in enumerate(videos):
            try:
                transcript = None
                full_text = None

                # Try Spanish first, then English (new API syntax)
                for langs in [['es'], ['es-419'], ['es-ES'], ['en']]:
                    try:
                        transcript = api.fetch(youtube_id, languages=langs)
                        if transcript:
                            data = transcript.to_raw_data()
                            full_text = ' '.join([s.get('text', '') for s in data])
                            break
                    except Exception:
                        continue

                if full_text and len(full_text) > 50:
                    keywords = extract_keywords(full_text)
                    desc = full_text[:500] + '...' if len(full_text) > 500 else full_text

                    db.execute(text("""
                        UPDATE youtube_videos
                        SET transcript = :transcript,
                            keywords = :keywords,
                            description = COALESCE(description, :desc),
                            updated_at = NOW()
                        WHERE id = :id
                    """), {
                        'id': str(vid),
                        'transcript': full_text[:50000],
                        'keywords': keywords,
                        'desc': desc
                    })

                    stats['success'] += 1
                    if (i + 1) % 10 == 0:
                        db.commit()
                        print(f"  ✓ Processed {i+1}/{len(videos)} - Last: {title[:40]}...")
                else:
                    stats['no_transcript'] += 1

            except Exception as e:
                stats['error'] += 1
                error_msg = str(e)
                if 'Too Many Requests' in error_msg or '429' in error_msg:
                    print(f"  ⚠️ Rate limited at video {i+1}. Waiting 10s...")
                    time.sleep(10)
                elif i < 5:  # Only print first few errors
                    print(f"  ⚠️ Error on {youtube_id}: {error_msg[:80]}")

        db.commit()
        print(f"\n✅ Transcript enrichment complete!")
        print(f"📊 Stats: {stats}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
