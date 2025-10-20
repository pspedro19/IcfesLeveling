#!/usr/bin/env python3
"""
Test script for the new diagnostic API endpoints
Tests the complete flow: start -> get questions -> submit answers -> get results
"""

import requests
import json
import time
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000/api"

# Test credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword"

def login() -> str:
    """Login and get JWT token"""
    login_data = {
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/v1/auth/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def get_headers(token: str) -> Dict[str, str]:
    """Get authorization headers"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def test_diagnostic_flow():
    """Test the complete diagnostic API flow"""
    print("🧪 Testing Diagnostic API Endpoints")
    print("=" * 50)
    
    # Step 1: Login
    print("1. Logging in...")
    token = login()
    if not token:
        print("❌ Login failed, cannot proceed with tests")
        return
    
    headers = get_headers(token)
    print("✅ Login successful")
    
    # Step 2: Get available subjects (we'll use the first one)
    print("\n2. Getting available subjects...")
    subjects_response = requests.get(f"{BASE_URL}/v1/subjects", headers=headers)
    if subjects_response.status_code != 200:
        print(f"❌ Failed to get subjects: {subjects_response.status_code}")
        return
    
    subjects = subjects_response.json()
    if not subjects:
        print("❌ No subjects available for testing")
        return
    
    test_subject = subjects[0]
    subject_id = test_subject["id"]
    print(f"✅ Using subject: {test_subject['name']} (ID: {subject_id})")
    
    # Step 3: Start diagnostic test
    print(f"\n3. Starting diagnostic test for subject {subject_id}...")
    start_response = requests.get(
        f"{BASE_URL}/diagnostic/start/{subject_id}", 
        headers=headers
    )
    
    if start_response.status_code != 200:
        print(f"❌ Failed to start test: {start_response.status_code} - {start_response.text}")
        return
    
    start_data = start_response.json()
    test_id = start_data["test_id"]
    print(f"✅ Test started successfully!")
    print(f"   Test ID: {test_id}")
    print(f"   Subject: {start_data['subject']['name']}")
    print(f"   Initial Theta: {start_data['initial_theta']}")
    
    # Step 4: Answer a few questions
    print(f"\n4. Getting and answering questions...")
    questions_answered = 0
    max_questions = 5  # Test with 5 questions
    
    while questions_answered < max_questions:
        # Get next question
        question_response = requests.get(
            f"{BASE_URL}/diagnostic/next-question",
            params={"test_id": test_id},
            headers=headers
        )
        
        if question_response.status_code != 200:
            print(f"❌ Failed to get question: {question_response.status_code}")
            break
        
        question_data = question_response.json()
        
        if question_data.get("test_complete"):
            print("✅ Test completed (no more questions)")
            break
        
        question = question_data["question"]
        print(f"\n   Question {question_data['question_number']}:")
        print(f"   {question['question_text'][:100]}...")
        print(f"   Difficulty: {question['difficulty']} ({question_data['difficulty_level']})")
        print(f"   Current Theta: {question_data['current_theta']}")
        
        # Submit a random answer (A, B, C, D, or E)
        import random
        answers = ['A', 'B', 'C', 'D', 'E']
        selected_answer = random.choice(answers)
        response_time = random.randint(5000, 30000)  # 5-30 seconds
        
        answer_payload = {
            "question_id": question["id"],
            "user_answer": selected_answer,
            "response_time_ms": response_time
        }
        
        answer_response = requests.post(
            f"{BASE_URL}/diagnostic/answer",
            params={"test_id": test_id},
            headers=headers,
            json=answer_payload
        )
        
        if answer_response.status_code != 200:
            print(f"❌ Failed to submit answer: {answer_response.status_code}")
            break
        
        answer_result = answer_response.json()
        print(f"   Answer: {selected_answer} ({'✅ Correct' if answer_result['correct'] else '❌ Incorrect'})")
        print(f"   Theta Change: {answer_result['theta_change']:+.3f} (New: {answer_result['new_theta']:.3f})")
        print(f"   Accuracy: {answer_result['current_accuracy']:.1f}%")
        print(f"   Feedback: {answer_result['feedback']['message']}")
        
        questions_answered += 1
        time.sleep(0.5)  # Small delay between questions
    
    # Step 5: Get final results
    print(f"\n5. Getting final results...")
    results_response = requests.get(
        f"{BASE_URL}/diagnostic/results",
        params={"test_id": test_id},
        headers=headers
    )
    
    if results_response.status_code != 200:
        print(f"❌ Failed to get results: {results_response.status_code}")
        return
    
    results = results_response.json()
    print(f"✅ Final Results:")
    print(f"   Score: {results['score']}/{questions_answered} ({results['percentage']}%)")
    print(f"   Final Theta: {results['theta_score']}")
    print(f"   ICFES Rank: {results['rank']}")
    print(f"   Mastery Level: {results['detailed_analysis']['mastery_level']}")
    print(f"   Percentile Rank: {results['detailed_analysis']['percentile_rank']}")
    
    if results['strengths']:
        print(f"   Strengths: {', '.join(results['strengths'])}")
    
    if results['weaknesses']:
        print(f"   Weaknesses: {', '.join(results['weaknesses'])}")
    
    print(f"   Recommendations: {len(results['recommendations'])} provided")
    
    print(f"\n🎉 Diagnostic API test completed successfully!")

def test_error_cases():
    """Test error cases and edge conditions"""
    print("\n🔍 Testing Error Cases")
    print("=" * 30)
    
    # Test without authentication
    print("1. Testing without authentication...")
    response = requests.get(f"{BASE_URL}/diagnostic/start/invalid-subject")
    print(f"   Expected 401/403, got: {response.status_code} ✅" if response.status_code in [401, 403] else f"   ❌ Expected 401/403, got: {response.status_code}")
    
    # Test with invalid subject (need auth first)
    token = login()
    if token:
        headers = get_headers(token)
        
        print("2. Testing with invalid subject...")
        response = requests.get(f"{BASE_URL}/diagnostic/start/invalid-subject-id", headers=headers)
        print(f"   Expected 404, got: {response.status_code} ✅" if response.status_code == 404 else f"   ❌ Expected 404, got: {response.status_code}")
        
        print("3. Testing get question without valid test_id...")
        response = requests.get(f"{BASE_URL}/diagnostic/next-question", params={"test_id": "invalid"}, headers=headers)
        print(f"   Expected 404, got: {response.status_code} ✅" if response.status_code == 404 else f"   ❌ Expected 404, got: {response.status_code}")

if __name__ == "__main__":
    try:
        test_diagnostic_flow()
        test_error_cases()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")