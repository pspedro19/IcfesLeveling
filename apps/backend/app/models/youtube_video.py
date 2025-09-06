from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from ..core.database import Base

class YoutubeVideo(Base):
    __tablename__ = "youtube_videos"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    channel_name = Column(String(255), nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    thumbnail_url = Column(String(500), nullable=True)
    
    # Educational metadata
    subject = Column(String(100), nullable=True, index=True)
    topic = Column(String(255), nullable=True, index=True)
    difficulty_level = Column(String(50), nullable=True)
    codigo_tema = Column(String(50), nullable=True, index=True)
    
    # Stats
    views_count = Column(Integer, default=0)
    quality_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<YoutubeVideo(id={self.id}, title='{self.title}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "channel_name": self.channel_name,
            "duration": self.duration,
            "thumbnail_url": self.thumbnail_url,
            "subject": self.subject,
            "topic": self.topic,
            "difficulty_level": self.difficulty_level,
            "codigo_tema": self.codigo_tema,
            "views_count": self.views_count,
            "quality_score": self.quality_score,
            "url": f"https://www.youtube.com/watch?v={self.video_id}"
        }