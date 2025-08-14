# YouTube Integration for ICFES Leveling

## Overview

This document describes the comprehensive YouTube video integration system implemented for ICFES Leveling. The system provides personalized educational video recommendations, real-time video metadata fetching, and seamless integration with the YML study plan system.

## Features

### 🎯 Core Features
- **Personalized Video Recommendations**: AI-driven video suggestions based on user performance and learning style
- **Real-time Metadata Fetching**: Live video information from YouTube Data API v3
- **Quota Management**: Intelligent API quota management with caching
- **Educational Metrics**: Quality scoring and relevance assessment for educational content
- **Seamless YML Integration**: Videos integrated directly into personalized study plans

### 🔧 Technical Features
- **Multi-layer Caching**: Redis-based caching for API responses
- **Error Handling**: Robust error handling and fallback mechanisms
- **Rate Limiting**: Built-in quota management and rate limiting
- **Responsive Design**: Mobile-optimized video player interface
- **Accessibility**: WCAG-compliant video player controls

## Architecture

### Backend Components

#### 1. YouTube API Service (`apps/backend/app/services/youtube_api_service.py`)
```python
class YouTubeAPIService:
    - get_video_info(video_id)           # Get detailed video metadata
    - search_videos(query, filters)      # Search educational videos
    - get_playlist_videos(playlist_id)   # Get playlist contents
    - get_channel_info(channel_id)       # Get channel information
    - update_youtube_links_metadata()    # Batch update video metadata
```

#### 2. Enhanced Video Service (`apps/backend/app/services/video_service.py`)
```python
class VideoService:
    - get_personalized_video_recommendations()  # AI-driven recommendations
    - search_educational_videos()              # Educational content search
    - get_video_quota_status()                 # API quota monitoring
```

#### 3. Database Models
- **YouTubeLinks**: Comprehensive video metadata storage
- **VideoTracking**: User video progress tracking
- **UserYMLPlan**: YML plan integration

### Frontend Components

#### 1. YouTube Video Renderer (`apps/frontend/app/components/StudyPlan/YouTubeVideoRenderer.tsx`)
- Personalized video recommendations display
- Interactive video player with progress tracking
- Responsive grid layout for video thumbnails
- Integration with design system

#### 2. Enhanced YML Renderer (`apps/frontend/app/components/StudyPlan/PersonalizedYMLRenderer.tsx`)
- YouTube video section integration
- Seamless video recommendation display
- Progress tracking and completion marking

## Setup Instructions

### 1. YouTube API Configuration

#### Get YouTube Data API v3 Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Restrict the API key:
   - HTTP referrers: Your domain
   - API restrictions: YouTube Data API v3 only

#### Environment Configuration
```bash
# Add to your .env file
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### 2. Database Setup

#### Run Migrations
```bash
# The YouTube links table should already exist
# If not, run the migration:
psql -d gameplay_db -f database/init/05-youtube-links.sql
```

#### Verify Table Structure
```sql
-- Check if youtube_links table exists
\d youtube_links

-- Verify columns
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'youtube_links';
```

### 3. Redis Configuration

#### Ensure Redis is Running
```bash
# Check Redis status
redis-cli ping

# Should return: PONG
```

#### Verify Redis Connection
```bash
# Test Redis connection from backend
python -c "
import redis
r = redis.from_url('redis://localhost:6379')
print('Redis connected:', r.ping())
"
```

## API Endpoints

### YouTube API Routes (`/api/v1/youtube`)

#### 1. Personalized Recommendations
```http
GET /api/v1/youtube/recommendations/personalized
?subject=Matemáticas
&weak_topics=álgebra,geometría
&difficulty_level=3
&limit=10
```

#### 2. Educational Video Search
```http
GET /api/v1/youtube/search
?query=ecuaciones lineales
&subject=Matemáticas
&max_results=15
```

#### 3. Video Information
```http
GET /api/v1/youtube/video/{video_id}/info
```

#### 4. Playlist Videos
```http
GET /api/v1/youtube/playlist/{playlist_id}/videos
?max_results=50
```

#### 5. Channel Information
```http
GET /api/v1/youtube/channel/{channel_id}/info
```

#### 6. YML Plan Videos
```http
GET /api/v1/youtube/recommendations/for-yml-plan
?subject=Matemáticas
&weak_topics=álgebra,geometría
&strong_topics=aritmética
&learning_style=visual
&limit_per_topic=3
```

#### 7. Quota Status
```http
GET /api/v1/youtube/quota/status
```

#### 8. Metadata Update (Admin Only)
```http
POST /api/v1/youtube/metadata/update
```

## Usage Examples

### 1. Frontend Integration

#### Basic Video Renderer Usage
```tsx
import YouTubeVideoRenderer from './components/StudyPlan/YouTubeVideoRenderer';

const MyComponent = () => {
  const videos = [
    {
      youtube_url: "https://www.youtube.com/watch?v=example",
      video_title: "Álgebra Básica",
      duration_seconds: 600,
      relevance_score: 0.9,
      difficulty_level: 2
    }
  ];

  return (
    <YouTubeVideoRenderer
      videos={videos}
      subject="Matemáticas"
      weakTopics={["álgebra", "geometría"]}
      strongTopics={["aritmética"]}
      learningStyle="visual"
      onVideoSelect={(video) => console.log('Selected:', video)}
      onVideoComplete={(video, progress) => console.log('Completed:', progress)}
    />
  );
};
```

#### YML Plan Integration
```tsx
// In PersonalizedYMLRenderer.tsx
<YouTubeVideoRenderer
  videos={[]} // Loaded from API
  subject={subject}
  weakTopics={ymlData.user_profile.weak_topics}
  strongTopics={ymlData.user_profile.strong_topics}
  learningStyle={ymlData.user_profile.learning_style}
  onVideoSelect={handleVideoSelect}
  onVideoComplete={handleVideoComplete}
  showRecommendations={true}
  maxVideos={15}
/>
```

### 2. Backend Service Usage

#### Get Personalized Recommendations
```python
from app.services.video_service import VideoService

video_service = VideoService(db)
recommendations = video_service.get_personalized_video_recommendations(
    user_id="user123",
    subject="Matemáticas",
    weak_topics=["álgebra", "geometría"],
    difficulty_level=3,
    limit=10
)
```

#### Search Educational Videos
```python
videos = video_service.search_educational_videos(
    query="ecuaciones lineales",
    subject="Matemáticas",
    max_results=15
)
```

#### Update Video Metadata
```python
from app.services.youtube_api_service import YouTubeAPIService

youtube_api = YouTubeAPIService(db)
result = youtube_api.update_youtube_links_metadata()
print(f"Updated {result['updated_count']} videos")
```

## Quota Management

### YouTube API Quota Limits
- **Daily Limit**: 10,000 units
- **Search**: 100 units per request
- **Video Info**: 1 unit per request
- **Playlist**: 1 unit per request
- **Channel Info**: 1 unit per request

### Caching Strategy
- **Video Info**: 1 hour TTL
- **Search Results**: 1 hour TTL
- **Playlist Data**: 2 hours TTL
- **Channel Info**: 24 hours TTL

### Quota Monitoring
```python
# Check quota status
quota_status = video_service.get_video_quota_status()
print(f"Usage: {quota_status['current_usage']}/{quota_status['daily_limit']}")
```

## Best Practices

### 1. API Key Security
- ✅ Store API key in environment variables
- ✅ Restrict API key to specific domains
- ✅ Use API restrictions in Google Console
- ❌ Never commit API keys to version control

### 2. Caching Strategy
- ✅ Cache frequently accessed data
- ✅ Use appropriate TTL values
- ✅ Implement cache warming for popular content
- ❌ Don't cache user-specific data

### 3. Error Handling
- ✅ Implement graceful fallbacks
- ✅ Log errors for debugging
- ✅ Provide user-friendly error messages
- ❌ Don't expose API errors to users

### 4. Performance Optimization
- ✅ Use pagination for large result sets
- ✅ Implement lazy loading for video thumbnails
- ✅ Optimize database queries
- ✅ Use CDN for video thumbnails

## Troubleshooting

### Common Issues

#### 1. API Key Not Working
```bash
# Check environment variable
echo $YOUTUBE_API_KEY

# Test API connection
curl "https://www.googleapis.com/youtube/v3/videos?id=dQw4w9WgXcQ&key=$YOUTUBE_API_KEY&part=snippet"
```

#### 2. Redis Connection Issues
```bash
# Check Redis status
redis-cli ping

# Check Redis logs
docker logs redis-container
```

#### 3. Database Connection Issues
```bash
# Test database connection
psql -h localhost -p 5433 -U gameplay -d gameplay_db -c "SELECT 1;"
```

#### 4. CORS Issues
```bash
# Check if API is accessible
curl -H "Origin: http://localhost:4001" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://localhost:4000/api/v1/youtube/quota/status
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Check logs
docker logs backend-container
```

## Monitoring and Analytics

### Key Metrics to Monitor
- API quota usage
- Cache hit rates
- Video completion rates
- User engagement with videos
- Error rates and types

### Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Video recommendation generated", extra={
    "user_id": user_id,
    "subject": subject,
    "videos_count": len(recommendations)
})
```

## Future Enhancements

### Planned Features
1. **Advanced AI Recommendations**: Machine learning-based video suggestions
2. **Video Quality Assessment**: Automated quality scoring
3. **Multi-language Support**: International video content
4. **Offline Support**: Download videos for offline viewing
5. **Social Features**: Video sharing and comments

### Performance Improvements
1. **Edge Caching**: CDN integration for global performance
2. **Database Optimization**: Advanced indexing strategies
3. **Background Processing**: Async video metadata updates
4. **Predictive Caching**: ML-based cache warming

## Support

For technical support or questions about the YouTube integration:

1. **Documentation**: Check this document and inline code comments
2. **Logs**: Review application logs for error details
3. **API Status**: Check [YouTube Data API Status](https://status.youtube.com/)
4. **Issues**: Create an issue in the project repository

## Contributing

When contributing to the YouTube integration:

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Test with different quota scenarios
5. Ensure backward compatibility

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Maintainer**: ICFES Leveling Team
