# ICFES Leveling Platform - Complete API Documentation

## Table of Contents

1. [Authentication](#authentication)
2. [User Management](#user-management)
3. [Diagnostic System](#diagnostic-system)
4. [Study Plans](#study-plans)
5. [Questions & Content](#questions--content)
6. [Gamification](#gamification)
7. [Analytics & Reporting](#analytics--reporting)
8. [Real-time Features](#real-time-features)
9. [Admin Endpoints](#admin-endpoints)
10. [Error Handling](#error-handling)
11. [Rate Limiting](#rate-limiting)
12. [WebSocket Events](#websocket-events)

## Base URL

- **Development**: `http://localhost:4000`
- **Production**: `https://api.icfes-leveling.com`

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Auth Endpoints

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "string (3-50 chars, alphanumeric)",
  "email": "string (valid email)",
  "password": "string (min 8 chars)",
  "display_name": "string (max 100 chars)"
}
```

**Response (201):**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1440,
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "display_name": "string",
    "rank": "E",
    "level": 1,
    "xp": 0,
    "created_at": "timestamp"
  }
}
```

**Errors:**
- `400` - Username or email already exists
- `422` - Validation errors

#### POST /auth/login
Authenticate user and get access token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1440,
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "display_name": "string",
    "rank": "string",
    "level": "integer",
    "xp": "integer",
    "hp": "integer",
    "mp": "integer",
    "credits": "integer",
    "gems": "integer"
  }
}
```

**Errors:**
- `401` - Invalid credentials
- `403` - Account deactivated

#### POST /auth/refresh
Refresh access token.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1440
}
```

#### GET /auth/me
Get current user information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "display_name": "string",
  "rank": "string",
  "level": "integer",
  "xp": "integer",
  "hp": "integer",
  "mp": "integer",
  "power": "integer",
  "wisdom": "integer",
  "speed": "integer",
  "resistance": "integer",
  "credits": "integer",
  "gems": "integer",
  "is_premium": "boolean",
  "created_at": "timestamp",
  "last_login": "timestamp"
}
```

#### POST /auth/logout
Logout and invalidate token.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

## User Management

#### GET /api/v1/users/profile
Get detailed user profile.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "user": {
    "id": "uuid",
    "username": "string",
    "display_name": "string",
    "rank": "string",
    "level": "integer",
    "xp": "integer",
    "stats": {
      "hp": "integer",
      "mp": "integer", 
      "power": "integer",
      "wisdom": "integer",
      "speed": "integer",
      "resistance": "integer"
    },
    "currency": {
      "credits": "integer",
      "gems": "integer"
    },
    "hero_class": {
      "id": "uuid",
      "name": "string",
      "element": "string",
      "color_theme": "string"
    },
    "achievements": ["array of achievement objects"],
    "study_streak": "integer",
    "total_study_time": "integer"
  }
}
```

#### PUT /api/v1/users/profile
Update user profile.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "display_name": "string (optional)",
  "email": "string (optional)"
}
```

**Response (200):**
```json
{
  "message": "Profile updated successfully",
  "user": { /* updated user object */ }
}
```

#### POST /auth/change-password
Change user password.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "current_password": "string",
  "new_password": "string (min 8 chars)"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

## Diagnostic System

#### GET /api/v1/diagnostic/test-questions/{subject_id}
Get diagnostic test questions for a subject.

**Parameters:**
- `subject_id` (path): Subject ID (1=Math, 2=Reading, 3=Science, 4=Social, 5=English)
- `count` (query): Number of questions (default: 10, max: 50)
- `difficulty` (query): Filter by difficulty (1-3, optional)

**Response (200):**
```json
{
  "subject": {
    "id": "integer",
    "name": "string",
    "description": "string"
  },
  "questions": [
    {
      "id": "integer",
      "question_text": "string",
      "options": {
        "A": "string",
        "B": "string", 
        "C": "string",
        "D": "string"
      },
      "difficulty": "integer (1-3)",
      "competency": "string",
      "topic": {
        "id": "integer",
        "name": "string"
      },
      "image_url": "string (optional)",
      "time_limit": "integer (seconds)"
    }
  ],
  "total_time_limit": "integer (seconds)",
  "instructions": "string"
}
```

#### POST /api/v1/diagnostic/submit
Submit diagnostic test answers.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "user_id": "uuid",
  "subject_id": "integer",
  "answers": [
    {
      "question_id": "integer",
      "selected_answer": "string (A-D)",
      "time_taken": "integer (seconds)"
    }
  ],
  "total_time": "integer (seconds)"
}
```

**Response (200):**
```json
{
  "test_id": "integer",
  "score_percentage": "float",
  "correct_answers": "integer",
  "total_questions": "integer",
  "rank_assigned": "string (E-S)",
  "time_taken": "integer",
  "detailed_results": [
    {
      "question_id": "integer",
      "correct": "boolean",
      "selected_answer": "string",
      "correct_answer": "string",
      "topic": "string",
      "explanation": "string"
    }
  ],
  "weak_areas": ["array of topic names"],
  "strong_areas": ["array of topic names"],
  "recommendations": ["array of recommendation strings"],
  "next_steps": {
    "study_plan_generated": "boolean",
    "suggested_topics": ["array of topic names"]
  }
}
```

#### GET /api/v1/diagnostic/results/{test_id}
Get detailed diagnostic test results.

**Headers:** `Authorization: Bearer <token>`

**Parameters:**
- `test_id` (path): Diagnostic test ID

**Response (200):**
```json
{
  "id": "integer",
  "subject": {
    "id": "integer",
    "name": "string"
  },
  "score_percentage": "float",
  "correct_answers": "integer",
  "total_questions": "integer",
  "rank_assigned": "string",
  "time_taken": "integer",
  "created_at": "timestamp",
  "detailed_analysis": {
    "topic_breakdown": [
      {
        "topic": "string",
        "correct": "integer",
        "total": "integer",
        "percentage": "float"
      }
    ],
    "difficulty_analysis": {
      "easy": {"correct": "integer", "total": "integer"},
      "medium": {"correct": "integer", "total": "integer"},
      "hard": {"correct": "integer", "total": "integer"}
    },
    "competency_breakdown": [
      {
        "competency": "string",
        "score": "float",
        "questions": "integer"
      }
    ]
  },
  "recommendations": {
    "immediate_focus": ["array of topics"],
    "study_plan_suggestions": ["array of suggestions"],
    "estimated_study_time": "integer (hours)"
  }
}
```

#### GET /api/v1/diagnostic/user/{user_id}/history
Get user's diagnostic test history.

**Headers:** `Authorization: Bearer <token>`

**Parameters:**
- `user_id` (path): User ID
- `subject_id` (query): Filter by subject (optional)
- `limit` (query): Number of results (default: 10, max: 100)
- `offset` (query): Pagination offset (default: 0)

**Response (200):**
```json
{
  "tests": [
    {
      "id": "integer",
      "subject": {
        "id": "integer", 
        "name": "string"
      },
      "score_percentage": "float",
      "rank_assigned": "string",
      "created_at": "timestamp",
      "improvement_from_previous": "float (optional)"
    }
  ],
  "total_count": "integer",
  "performance_trend": {
    "trend": "string (improving/declining/stable)",
    "average_score": "float",
    "best_score": "float",
    "most_recent_score": "float"
  }
}
```

## Study Plans

#### POST /api/v1/study-plans/generate/{subject_id}
Generate personalized study plan based on diagnostic results.

**Headers:** `Authorization: Bearer <token>`

**Parameters:**
- `subject_id` (path): Subject ID
- `ai_enhanced` (query): Use AI for enhanced planning (default: false)

**Response (200):**
```json
{
  "id": "integer",
  "title": "string",
  "description": "string", 
  "subject": {
    "id": "integer",
    "name": "string"
  },
  "difficulty_level": "integer (1-3)",
  "estimated_weeks": "integer",
  "total_hours": "integer",
  "topics": [
    {
      "id": "integer",
      "name": "string",
      "description": "string",
      "order_index": "integer",
      "estimated_hours": "integer",
      "difficulty_level": "integer",
      "status": "string (pending/in_progress/completed)",
      "prerequisites": ["array of topic IDs"],
      "learning_objectives": ["array of objectives"],
      "resources": {
        "videos": "integer",
        "exercises": "integer",
        "practice_tests": "integer"
      }
    }
  ],
  "milestones": [
    {
      "week": "integer",
      "title": "string",
      "description": "string",
      "topics_to_complete": ["array of topic names"]
    }
  ],
  "personalization": {
    "based_on_diagnostic": "boolean",
    "learning_style": "string",
    "weak_areas_focus": ["array of topics"],
    "custom_recommendations": ["array of recommendations"]
  }
}
```

#### GET /api/v1/study-plans/user/{user_id}
Get user's study plans.

**Headers:** `Authorization: Bearer <token>`

**Parameters:**
- `user_id` (path): User ID
- `status` (query): Filter by status (active/completed/paused)

**Response (200):**
```json
[
  {
    "id": "integer",
    "title": "string",
    "subject": {
      "id": "integer",
      "name": "string"
    },
    "status": "string",
    "progress": {
      "completion_percentage": "float",
      "completed_topics": "integer",
      "total_topics": "integer",
      "estimated_completion_date": "timestamp"
    },
    "created_at": "timestamp",
    "updated_at": "timestamp"
  }
]
```

#### GET /api/v1/study-plans/{plan_id}
Get detailed study plan information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "integer",
  "title": "string",
  "description": "string",
  "subject": {
    "id": "integer",
    "name": "string"
  },
  "difficulty_level": "integer",
  "status": "string",
  "progress": {
    "completion_percentage": "float",
    "completed_topics": "integer",
    "total_topics": "integer",
    "current_topic": {
      "id": "integer",
      "name": "string"
    },
    "time_spent": "integer (minutes)",
    "estimated_time_remaining": "integer (minutes)"
  },
  "topics": [
    {
      "id": "integer",
      "name": "string",
      "description": "string",
      "status": "string",
      "progress_percentage": "float",
      "estimated_hours": "integer",
      "actual_time_spent": "integer (minutes)",
      "resources": {
        "videos": [
          {
            "id": "string",
            "title": "string",
            "url": "string",
            "duration": "integer (seconds)",
            "watched": "boolean"
          }
        ],
        "exercises": [
          {
            "id": "integer",
            "title": "string",
            "type": "string",
            "completed": "boolean"
          }
        ]
      }
    }
  ]
}
```

#### POST /api/v1/study-plans/{plan_id}/topics/{topic_id}/complete
Mark a topic as completed.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "time_spent": "integer (minutes, optional)",
  "difficulty_rating": "integer (1-5, optional)",
  "notes": "string (optional)"
}
```

**Response (200):**
```json
{
  "message": "Topic completed successfully",
  "xp_gained": "integer",
  "level_up": "boolean",
  "new_level": "integer (if level_up)",
  "achievements_unlocked": ["array of achievement objects"],
  "next_topic": {
    "id": "integer",
    "name": "string"
  },
  "plan_progress": {
    "completion_percentage": "float",
    "estimated_completion_date": "timestamp"
  }
}
```

#### GET /api/v1/study-plans/{plan_id}/progress
Get detailed progress information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "completion_percentage": "float",
  "completed_topics": "integer",
  "total_topics": "integer",
  "time_spent": "integer (minutes)",
  "estimated_time_remaining": "integer (minutes)",
  "current_streak": "integer (days)",
  "study_sessions": "integer",
  "average_session_time": "integer (minutes)",
  "weekly_progress": [
    {
      "week": "string (YYYY-WW)",
      "topics_completed": "integer",
      "time_spent": "integer (minutes)",
      "progress_percentage": "float"
    }
  ],
  "upcoming_milestones": [
    {
      "date": "timestamp",
      "title": "string",
      "description": "string"
    }
  ]
}
```

## Questions & Content

#### GET /api/v1/questions/search
Search and filter questions.

**Parameters:**
- `subject_id` (query): Filter by subject
- `topic_id` (query): Filter by topic
- `difficulty` (query): Filter by difficulty (1-3)
- `competency` (query): Filter by competency
- `question_type` (query): Filter by type (multiple_choice, true_false, etc.)
- `has_image` (query): Filter questions with images (boolean)
- `limit` (query): Number of results (default: 20, max: 100)
- `offset` (query): Pagination offset

**Response (200):**
```json
{
  "questions": [
    {
      "id": "integer",
      "question_text": "string",
      "options": {
        "A": "string",
        "B": "string",
        "C": "string", 
        "D": "string"
      },
      "difficulty": "integer",
      "competency": "string",
      "question_type": "string",
      "topic": {
        "id": "integer",
        "name": "string"
      },
      "subject": {
        "id": "integer", 
        "name": "string"
      },
      "image_url": "string (optional)",
      "created_at": "timestamp"
    }
  ],
  "total_count": "integer",
  "filters_applied": {
    "subject_id": "integer",
    "topic_id": "integer",
    "difficulty": "integer"
  }
}
```

#### GET /api/v1/questions/{question_id}
Get detailed question information.

**Response (200):**
```json
{
  "id": "integer",
  "question_text": "string", 
  "options": {
    "A": "string",
    "B": "string",
    "C": "string",
    "D": "string"
  },
  "correct_answer": "string (only for authenticated users)",
  "explanation": "string",
  "difficulty": "integer",
  "competency": "string",
  "question_type": "string",
  "topic": {
    "id": "integer",
    "name": "string",
    "description": "string"
  },
  "subject": {
    "id": "integer",
    "name": "string"
  },
  "image_url": "string (optional)",
  "related_questions": ["array of question IDs"],
  "tags": ["array of tags"],
  "statistics": {
    "total_attempts": "integer",
    "correct_percentage": "float",
    "average_time": "float (seconds)"
  }
}
```

#### GET /api/v1/subjects
Get list of all subjects.

**Response (200):**
```json
[
  {
    "id": "integer",
    "name": "string",
    "code": "string",
    "description": "string",
    "icon_url": "string",
    "difficulty_level": "integer",
    "estimated_hours": "integer",
    "total_topics": "integer",
    "total_questions": "integer",
    "is_active": "boolean"
  }
]
```

#### GET /api/v1/subjects/{subject_id}/topics
Get topics for a subject.

**Parameters:**
- `subject_id` (path): Subject ID

**Response (200):**
```json
[
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "difficulty_level": "integer",
    "estimated_time": "integer (minutes)",
    "prerequisites": ["array of topic IDs"],
    "learning_objectives": ["array of objectives"],
    "question_count": "integer",
    "video_count": "integer",
    "is_active": "boolean"
  }
]
```

## Gamification

#### GET /api/v1/achievements
Get list of available achievements.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
[
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "icon_url": "string",
    "category": "string",
    "difficulty": "string (bronze/silver/gold/platinum)",
    "xp_reward": "integer",
    "gem_reward": "integer",
    "requirements": {
      "type": "string",
      "target": "integer",
      "description": "string"
    },
    "unlocked": "boolean",
    "unlocked_at": "timestamp (optional)",
    "progress": {
      "current": "integer",
      "required": "integer",
      "percentage": "float"
    }
  }
]
```

#### GET /api/v1/achievements/user/{user_id}
Get user's achievement progress.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "total_achievements": "integer",
  "unlocked_achievements": "integer",
  "total_xp_from_achievements": "integer",
  "total_gems_from_achievements": "integer",
  "recent_unlocks": [
    {
      "achievement": {
        "id": "integer",
        "name": "string",
        "description": "string",
        "icon_url": "string"
      },
      "unlocked_at": "timestamp",
      "xp_gained": "integer",
      "gems_gained": "integer"
    }
  ],
  "in_progress": [
    {
      "achievement": {
        "id": "integer",
        "name": "string",
        "description": "string"
      },
      "progress": {
        "current": "integer",
        "required": "integer",
        "percentage": "float"
      }
    }
  ]
}
```

#### GET /api/v1/leaderboard
Get global leaderboard.

**Parameters:**
- `type` (query): Leaderboard type (xp/level/streak/monthly)
- `timeframe` (query): Time period (daily/weekly/monthly/all_time)
- `limit` (query): Number of results (default: 50, max: 100)

**Response (200):**
```json
{
  "leaderboard": [
    {
      "rank": "integer",
      "user": {
        "id": "uuid",
        "username": "string",
        "display_name": "string",
        "rank": "string",
        "level": "integer",
        "hero_class": {
          "name": "string",
          "element": "string"
        }
      },
      "score": "integer",
      "change_from_previous": "integer"
    }
  ],
  "user_position": {
    "rank": "integer",
    "score": "integer"
  },
  "total_participants": "integer",
  "last_updated": "timestamp"
}
```

#### GET /api/v1/battle/available
Get available boss battles.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
[
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "difficulty": "integer",
    "required_level": "integer",
    "hp": "integer",
    "image_url": "string",
    "rewards": {
      "xp": "integer",
      "gems": "integer",
      "items": ["array of item objects"]
    },
    "available": "boolean",
    "cooldown_until": "timestamp (optional)"
  }
]
```

## Analytics & Reporting

#### GET /api/v1/analytics/user/{user_id}/dashboard
Get user analytics dashboard data.

**Headers:** `Authorization: Bearer <token>`

**Parameters:**
- `timeframe` (query): Time period (7d/30d/90d/1y)

**Response (200):**
```json
{
  "overview": {
    "total_study_time": "integer (minutes)",
    "questions_answered": "integer", 
    "accuracy_rate": "float",
    "current_streak": "integer (days)",
    "level_ups": "integer",
    "achievements_unlocked": "integer"
  },
  "performance_trends": {
    "accuracy_over_time": [
      {
        "date": "string (YYYY-MM-DD)",
        "accuracy": "float"
      }
    ],
    "study_time_per_day": [
      {
        "date": "string (YYYY-MM-DD)",
        "minutes": "integer"
      }
    ]
  },
  "subject_breakdown": [
    {
      "subject": {
        "id": "integer",
        "name": "string"
      },
      "time_spent": "integer (minutes)",
      "questions_answered": "integer",
      "accuracy": "float",
      "progress_percentage": "float"
    }
  ],
  "learning_insights": {
    "best_study_time": "string",
    "most_productive_day": "string",
    "average_session_length": "integer (minutes)",
    "improvement_areas": ["array of topics"]
  }
}
```

#### GET /api/v1/analytics/performance-report/{user_id}
Generate comprehensive performance report.

**Headers:** `Authorization: Bearer <token>`

**Parameters:**
- `start_date` (query): Start date (YYYY-MM-DD)
- `end_date` (query): End date (YYYY-MM-DD)
- `include_predictions` (query): Include AI predictions (boolean)

**Response (200):**
```json
{
  "report_period": {
    "start_date": "string",
    "end_date": "string",
    "total_days": "integer"
  },
  "overall_performance": {
    "total_study_sessions": "integer",
    "total_study_time": "integer (minutes)",
    "questions_answered": "integer",
    "overall_accuracy": "float",
    "improvement_rate": "float"
  },
  "subject_performance": [
    {
      "subject": "string",
      "accuracy": "float",
      "time_spent": "integer",
      "questions_answered": "integer",
      "difficulty_progression": {
        "easy": "float",
        "medium": "float", 
        "hard": "float"
      },
      "weak_topics": ["array of topics"],
      "strong_topics": ["array of topics"]
    }
  ],
  "learning_patterns": {
    "peak_performance_hours": ["array of hours"],
    "study_consistency": "float",
    "session_length_optimization": {
      "current_average": "integer",
      "recommended": "integer"
    }
  },
  "predictions": {
    "icfes_score_estimate": {
      "mathematics": "float",
      "reading": "float",
      "science": "float",
      "social": "float",
      "english": "float",
      "overall": "float"
    },
    "study_plan_recommendations": ["array of recommendations"],
    "estimated_preparation_time": "integer (weeks)"
  }
}
```

## Real-time Features

#### GET /api/v1/notifications/user/{user_id}
Get user notifications.

**Headers:** `Authorization: Bearer <token>`

**Parameters:**
- `unread_only` (query): Show only unread notifications (boolean)
- `type` (query): Filter by type (achievement/reminder/system/social)
- `limit` (query): Number of results (default: 20)

**Response (200):**
```json
{
  "notifications": [
    {
      "id": "integer",
      "type": "string",
      "title": "string",
      "message": "string",
      "data": "object (optional)",
      "is_read": "boolean",
      "created_at": "timestamp"
    }
  ],
  "unread_count": "integer"
}
```

#### POST /api/v1/notifications/{notification_id}/read
Mark notification as read.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Notification marked as read"
}
```

## Admin Endpoints

### User Management

#### GET /api/v1/admin/users
Get list of users with admin capabilities.

**Headers:** `Authorization: Bearer <admin_token>`

**Parameters:**
- `search` (query): Search by username or email
- `rank` (query): Filter by rank
- `is_active` (query): Filter by active status
- `limit` (query): Results per page (max 100)
- `offset` (query): Pagination offset

**Response (200):**
```json
{
  "users": [
    {
      "id": "uuid",
      "username": "string",
      "email": "string",
      "display_name": "string",
      "rank": "string",
      "level": "integer",
      "xp": "integer",
      "is_active": "boolean",
      "is_premium": "boolean",
      "last_login": "timestamp",
      "created_at": "timestamp",
      "diagnostic_tests_taken": "integer",
      "study_plans_active": "integer"
    }
  ],
  "total_count": "integer"
}
```

#### PUT /api/v1/admin/users/{user_id}
Update user as admin.

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "is_active": "boolean (optional)",
  "is_premium": "boolean (optional)",
  "rank": "string (optional)",
  "level": "integer (optional)",
  "xp": "integer (optional)",
  "credits": "integer (optional)",
  "gems": "integer (optional)"
}
```

### Content Management

#### POST /api/v1/admin/questions
Create new question.

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "question_text": "string",
  "options": {
    "A": "string",
    "B": "string",
    "C": "string",
    "D": "string"
  },
  "correct_answer": "string (A-D)",
  "explanation": "string",
  "difficulty": "integer (1-3)",
  "competency": "string",
  "question_type": "string",
  "topic_id": "integer",
  "subject_id": "integer",
  "image_url": "string (optional)",
  "tags": ["array of strings"]
}
```

#### PUT /api/v1/admin/questions/{question_id}
Update existing question.

**Headers:** `Authorization: Bearer <admin_token>`

### System Analytics

#### GET /api/v1/admin/analytics/system
Get system-wide analytics.

**Headers:** `Authorization: Bearer <admin_token>`

**Response (200):**
```json
{
  "users": {
    "total": "integer",
    "active_today": "integer",
    "active_this_week": "integer",
    "new_registrations_today": "integer",
    "premium_users": "integer"
  },
  "content": {
    "total_questions": "integer",
    "questions_by_subject": "object",
    "total_diagnostic_tests": "integer",
    "total_study_plans": "integer"
  },
  "performance": {
    "average_response_time": "float",
    "uptime_percentage": "float",
    "error_rate": "float",
    "cache_hit_rate": "float"
  },
  "engagement": {
    "daily_active_users": "integer",
    "average_session_duration": "integer",
    "questions_answered_today": "integer",
    "study_plans_completed_today": "integer"
  }
}
```

## Error Handling

All API endpoints use consistent error response format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object (optional)",
    "timestamp": "timestamp"
  }
}
```

### Common Error Codes

- `400` - Bad Request: Invalid request parameters
- `401` - Unauthorized: Authentication required or invalid token
- `403` - Forbidden: Insufficient permissions
- `404` - Not Found: Resource not found
- `422` - Unprocessable Entity: Validation errors
- `429` - Too Many Requests: Rate limit exceeded
- `500` - Internal Server Error: Unexpected server error
- `503` - Service Unavailable: Server maintenance or overloaded

### Validation Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "field_errors": {
        "username": ["Username must be at least 3 characters"],
        "email": ["Invalid email format"]
      }
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **General endpoints**: 100 requests per minute per IP
- **Authentication endpoints**: 5 requests per minute per IP
- **Admin endpoints**: 1000 requests per minute per authenticated user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```

## WebSocket Events

Connect to WebSocket endpoint: `ws://localhost:8003/ws/{user_id}`

### Client Events

#### authenticate
Authenticate WebSocket connection.

```json
{
  "type": "authenticate",
  "token": "jwt_token"
}
```

#### join_room
Join a specific room.

```json
{
  "type": "join_room", 
  "room": "study_session_123"
}
```

### Server Events

#### notification
Real-time notification.

```json
{
  "type": "notification",
  "data": {
    "title": "Achievement Unlocked!",
    "message": "You've completed your first study session",
    "category": "achievement"
  }
}
```

#### study_progress
Study progress update.

```json
{
  "type": "study_progress",
  "data": {
    "topic_id": 123,
    "progress_percentage": 75.5,
    "xp_gained": 10
  }
}
```

#### leaderboard_update
Real-time leaderboard changes.

```json
{
  "type": "leaderboard_update",
  "data": {
    "user_rank": 15,
    "rank_change": -2,
    "new_score": 1250
  }
}
```

This comprehensive API documentation covers all major endpoints and functionality of the ICFES Leveling Platform. For additional technical details, refer to the OpenAPI/Swagger documentation available at `/docs` when running the application.