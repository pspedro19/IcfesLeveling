# Complete Diagnostic API Endpoints Documentation

## Overview

This document describes the complete diagnostic API endpoints that provide comprehensive adaptive testing functionality with real-time question selection, theta score calculation, and detailed performance analysis.

## Base URL

```
http://localhost:8000/api/diagnostic
```

## Authentication

All endpoints require Bearer Token authentication:

```http
Authorization: Bearer <jwt_token>
```

## API Endpoints

### 1. Start Diagnostic Test

**Endpoint:** `GET /diagnostic/start/{subject_id}`

**Description:** Starts a new adaptive diagnostic test for the specified subject.

**Parameters:**
- `subject_id` (path): The ID of the subject to test

**Response:**
```json
{
  "test_id": "uuid-string",
  "subject": {
    "id": "subject-uuid",
    "name": "Subject Name",
    "description": "Subject description"
  },
  "initial_theta": 0.0,
  "status": "started",
  "message": "Diagnostic test started for Subject Name",
  "started_at": "2024-01-01T10:00:00Z"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/diagnostic/start/math-subject-id" \
  -H "Authorization: Bearer your-jwt-token"
```

### 2. Get Next Question

**Endpoint:** `GET /diagnostic/next-question`

**Description:** Retrieves the next adaptive question based on current performance.

**Query Parameters:**
- `test_id` (required): The test session identifier

**Response:**
```json
{
  "question": {
    "id": "question-uuid",
    "question_text": "What is 2 + 2?",
    "options": ["A) 1", "B) 2", "C) 3", "D) 4", "E) 5"],
    "subject": "Mathematics",
    "topic": "Basic Arithmetic",
    "difficulty": 3,
    "hint": "Think about basic addition"
  },
  "question_number": 1,
  "total_questions_answered": 0,
  "current_theta": 0.0,
  "difficulty_level": "Easy",
  "test_complete": false
}
```

**Test Complete Response:**
```json
{
  "question": null,
  "test_complete": true,
  "message": "Test completed. Call /results to get final results.",
  "questions_answered": 20,
  "current_theta": 1.25
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/diagnostic/next-question?test_id=your-test-id" \
  -H "Authorization: Bearer your-jwt-token"
```

### 3. Submit Answer

**Endpoint:** `POST /diagnostic/answer`

**Description:** Submits an answer and receives real-time adaptive feedback.

**Query Parameters:**
- `test_id` (required): The test session identifier

**Request Body:**
```json
{
  "question_id": "question-uuid",
  "user_answer": "D",
  "response_time_ms": 15000
}
```

**Response:**
```json
{
  "correct": true,
  "feedback": {
    "message": "Excellent! Your ability level has increased significantly.",
    "encouragement": "Keep up the great work!",
    "explanation": "This demonstrates good understanding of basic arithmetic."
  },
  "theta_change": 0.150,
  "new_theta": 0.150,
  "performance_trend": "improving",
  "next_difficulty_recommendation": 4,
  "questions_answered": 1,
  "current_accuracy": 100.0,
  "confidence_interval": [-0.35, 0.65]
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/diagnostic/answer?test_id=your-test-id" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": "question-uuid",
    "user_answer": "D",
    "response_time_ms": 15000
  }'
```

### 4. Get Final Results

**Endpoint:** `GET /diagnostic/results`

**Description:** Retrieves comprehensive final results with theta score and detailed analysis.

**Query Parameters:**
- `test_id` (required): The test session identifier

**Response:**
```json
{
  "score": 15,
  "percentage": 75,
  "theta_score": 1.250,
  "rank": "B",
  "strengths": ["Basic Arithmetic", "Algebra"],
  "weaknesses": ["Geometry", "Statistics"],
  "recommendations": [
    "Work on intermediate topics in Mathematics",
    "Review incorrect answers to identify knowledge gaps",
    "Prioritize studying: Geometry, Statistics"
  ],
  "detailed_analysis": {
    "total_questions": 20,
    "time_spent_minutes": 25.5,
    "average_response_time": 76.5,
    "difficulty_distribution": {
      "Easy": 5,
      "Medium": 10,
      "Hard": 4,
      "Very Hard": 1
    },
    "performance_progression": "improving",
    "mastery_level": "Advanced",
    "percentile_rank": 84,
    "topic_breakdown": {
      "Basic Arithmetic": {
        "correct": 4,
        "total": 5
      },
      "Algebra": {
        "correct": 3,
        "total": 4
      },
      "Geometry": {
        "correct": 1,
        "total": 3
      }
    },
    "next_steps": [
      "Take practice tests regularly",
      "Focus on consistency in performance",
      "Create a study plan focusing on Geometry"
    ]
  }
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/diagnostic/results?test_id=your-test-id" \
  -H "Authorization: Bearer your-jwt-token"
```

## Complete Test Flow Example

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api"
headers = {"Authorization": "Bearer your-jwt-token"}

# 1. Start test
response = requests.get(f"{BASE_URL}/diagnostic/start/subject-id", headers=headers)
test_data = response.json()
test_id = test_data["test_id"]

# 2. Answer questions
while True:
    # Get next question
    question_response = requests.get(
        f"{BASE_URL}/diagnostic/next-question", 
        params={"test_id": test_id},
        headers=headers
    )
    
    question_data = question_response.json()
    
    if question_data.get("test_complete"):
        break
    
    # Submit answer
    answer_payload = {
        "question_id": question_data["question"]["id"],
        "user_answer": "A",  # Your selected answer
        "response_time_ms": 10000
    }
    
    answer_response = requests.post(
        f"{BASE_URL}/diagnostic/answer",
        params={"test_id": test_id},
        headers=headers,
        json=answer_payload
    )
    
    result = answer_response.json()
    print(f"Correct: {result['correct']}, New Theta: {result['new_theta']}")

# 3. Get final results
results_response = requests.get(
    f"{BASE_URL}/diagnostic/results",
    params={"test_id": test_id},
    headers=headers
)

results = results_response.json()
print(f"Final Score: {results['percentage']}%, Rank: {results['rank']}")
```

### JavaScript Example

```javascript
const BASE_URL = 'http://localhost:8000/api';
const headers = {
  'Authorization': 'Bearer your-jwt-token',
  'Content-Type': 'application/json'
};

async function runDiagnosticTest(subjectId) {
  try {
    // 1. Start test
    const startResponse = await fetch(`${BASE_URL}/diagnostic/start/${subjectId}`, {
      method: 'GET',
      headers: headers
    });
    const testData = await startResponse.json();
    const testId = testData.test_id;
    
    console.log('Test started:', testId);
    
    // 2. Answer questions
    while (true) {
      // Get next question
      const questionResponse = await fetch(
        `${BASE_URL}/diagnostic/next-question?test_id=${testId}`,
        { method: 'GET', headers: headers }
      );
      const questionData = await questionResponse.json();
      
      if (questionData.test_complete) {
        break;
      }
      
      console.log('Question:', questionData.question.question_text);
      
      // Submit answer (example with 'A')
      const answerPayload = {
        question_id: questionData.question.id,
        user_answer: 'A',
        response_time_ms: 10000
      };
      
      const answerResponse = await fetch(
        `${BASE_URL}/diagnostic/answer?test_id=${testId}`,
        {
          method: 'POST',
          headers: headers,
          body: JSON.stringify(answerPayload)
        }
      );
      
      const answerResult = await answerResponse.json();
      console.log(`Answer result: ${answerResult.correct ? 'Correct' : 'Incorrect'}`);
    }
    
    // 3. Get final results
    const resultsResponse = await fetch(
      `${BASE_URL}/diagnostic/results?test_id=${testId}`,
      { method: 'GET', headers: headers }
    );
    const results = await resultsResponse.json();
    
    console.log('Final Results:', {
      score: results.percentage,
      rank: results.rank,
      thetaScore: results.theta_score
    });
    
    return results;
    
  } catch (error) {
    console.error('Test failed:', error);
  }
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied to this test session"
}
```

### 404 Not Found
```json
{
  "detail": "Subject not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to start diagnostic test: <error_message>"
}
```

## Key Features

### Adaptive Question Selection
- Questions are selected based on current theta (ability estimate)
- Difficulty adjusts in real-time based on performance
- Uses Item Response Theory (IRT) for precise ability estimation

### Real-time Feedback
- Immediate feedback after each answer
- Theta score updates with confidence intervals
- Performance trend analysis

### Comprehensive Results
- ICFES rank calculation (S, A, B, C, D, E)
- Topic-level strength/weakness analysis
- Personalized study recommendations
- Detailed performance metrics

### Session Management
- Secure session handling with user verification
- Automatic session cleanup after results retrieval
- Support for concurrent sessions

## Best Practices

1. **Always check authentication** before making requests
2. **Handle test completion** by checking the `test_complete` flag
3. **Store test_id securely** for the session duration
4. **Implement proper error handling** for all endpoints
5. **Respect rate limits** and add appropriate delays between requests
6. **Validate user input** before submitting answers
7. **Clean up resources** by retrieving results when test is complete

## Testing

Use the provided test script to validate the API:

```bash
python test_diagnostic_api.py
```

This will run through the complete flow and test error conditions.