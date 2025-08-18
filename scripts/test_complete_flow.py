#!/usr/bin/env python3
"""
ICFES Leveling - Complete Flow Integration Test
Tests the entire user journey from registration to study plan with videos
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys
import os

# Configuration
BASE_URL = os.getenv("API_URL", "http://localhost:4000/api/v1")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Colors for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(message: str):
    """Print step message"""
    print(f"{Colors.OKBLUE}➜ {message}{Colors.ENDC}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def print_info(key: str, value: str):
    """Print info message"""
    print(f"  {Colors.BOLD}{key}:{Colors.ENDC} {value}")

class ICFESIntegrationTest:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_data = None
        self.test_id = None
        self.plan_id = None
        self.yml_id = None
        
    def test_1_register_user(self) -> bool:
        """Test user registration"""
        print_step("Testing user registration...")
        
        timestamp = int(datetime.now().timestamp())
        self.user_data = {
            "username": f"test_user_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User",
            "grade": "11"
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/register",
                json=self.user_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("User registered successfully")
                print_info("User ID", data.get("id", "N/A"))
                print_info("Username", self.user_data["username"])
                return True
            else:
                print_error(f"Registration failed: {response.status_code}")
                print_error(response.text)
                return False
                
        except Exception as e:
            print_error(f"Registration error: {str(e)}")
            return False
    
    def test_2_login(self) -> bool:
        """Test user login"""
        print_step("Testing user login...")
        
        login_data = {
            "username": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                data=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                print_success("Login successful")
                print_info("Token Type", data["token_type"])
                print_info("Token Length", str(len(self.token)))
                return True
            else:
                print_error(f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Login error: {str(e)}")
            return False
    
    def test_3_create_diagnostic_test(self) -> bool:
        """Test diagnostic test creation"""
        print_step("Creating diagnostic test...")
        
        # First get available subjects
        try:
            response = self.session.get(f"{BASE_URL}/subjects/dynamic")
            if response.status_code == 200:
                subjects = response.json()
                if subjects:
                    subject_id = subjects[0]["id"]
                    subject_name = subjects[0]["name"]
                else:
                    print_error("No subjects available")
                    return False
            else:
                # Use a default subject ID if endpoint fails
                subject_id = "mathematics"
                subject_name = "Mathematics"
                
        except:
            subject_id = "mathematics"
            subject_name = "Mathematics"
        
        test_data = {
            "subject_id": subject_id,
            "test_type": "diagnostic",
            "difficulty": "medium"
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/diagnostic/tests",
                json=test_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_id = data["id"]
                print_success("Diagnostic test created")
                print_info("Test ID", self.test_id)
                print_info("Subject", subject_name)
                return True
            else:
                print_error(f"Test creation failed: {response.status_code}")
                print_error(response.text)
                return False
                
        except Exception as e:
            print_error(f"Test creation error: {str(e)}")
            return False
    
    def test_4_answer_questions(self) -> bool:
        """Test answering diagnostic questions"""
        print_step("Answering diagnostic questions...")
        
        try:
            # Get questions for the test
            response = self.session.get(
                f"{BASE_URL}/diagnostic/questions",
                params={"test_id": self.test_id}
            )
            
            if response.status_code != 200:
                print_error(f"Failed to get questions: {response.status_code}")
                return False
            
            questions = response.json()
            
            if not questions:
                print_error("No questions available")
                return False
            
            print_info("Total Questions", str(len(questions)))
            
            # Answer first 10 questions
            questions_to_answer = questions[:10]
            correct_count = 0
            
            for i, question in enumerate(questions_to_answer, 1):
                # Simulate answering with varying correctness
                is_correct = i % 3 != 0  # 2/3 correct answers
                selected_option = "A" if is_correct else "B"
                
                answer_data = {
                    "question_id": question["id"],
                    "selected_option": selected_option,
                    "time_spent": 30 + (i * 5),  # Varying time spent
                    "is_marked": False
                }
                
                response = self.session.post(
                    f"{BASE_URL}/diagnostic/tests/{self.test_id}/answers",
                    json=answer_data
                )
                
                if response.status_code == 200:
                    if is_correct:
                        correct_count += 1
                    print(f"  Question {i}/10 answered {'✓' if is_correct else '✗'}")
                else:
                    print_error(f"Failed to answer question {i}")
            
            print_success(f"Answered {len(questions_to_answer)} questions")
            print_info("Expected Correct", f"{correct_count}/{len(questions_to_answer)}")
            return True
            
        except Exception as e:
            print_error(f"Answer questions error: {str(e)}")
            return False
    
    def test_5_submit_test(self) -> bool:
        """Test submitting diagnostic test"""
        print_step("Submitting diagnostic test...")
        
        try:
            response = self.session.post(
                f"{BASE_URL}/diagnostic/tests/{self.test_id}/submit"
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Test submitted successfully")
                print_info("Status", data.get("status", "completed"))
                print_info("Score", f"{data.get('score_percentage', 0)}%")
                return True
            else:
                print_error(f"Test submission failed: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Test submission error: {str(e)}")
            return False
    
    def test_6_get_results(self) -> bool:
        """Test getting diagnostic results"""
        print_step("Getting diagnostic results...")
        
        try:
            response = self.session.get(
                f"{BASE_URL}/diagnostic/tests/{self.test_id}/results"
            )
            
            if response.status_code == 200:
                results = response.json()
                print_success("Results retrieved successfully")
                print_info("Score", f"{results.get('score_percentage', 0)}%")
                print_info("Total Questions", str(results.get('total_questions', 0)))
                print_info("Correct Answers", str(results.get('correct_answers', 0)))
                
                # Print strengths and weaknesses
                if "strengths" in results:
                    print_info("Strengths", ", ".join(results["strengths"][:3]))
                if "weaknesses" in results:
                    print_info("Weaknesses", ", ".join(results["weaknesses"][:3]))
                    
                return True
            else:
                print_error(f"Failed to get results: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Get results error: {str(e)}")
            return False
    
    def test_7_generate_study_plan(self) -> bool:
        """Test generating adaptive study plan"""
        print_step("Generating adaptive study plan...")
        
        plan_data = {
            "diagnostic_test_id": self.test_id,
            "target_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "study_hours_per_day": 2,
            "difficulty_preference": "balanced"
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/study-plans/generate-adaptive",
                json=plan_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.plan_id = data["id"]
                print_success("Study plan generated")
                print_info("Plan ID", self.plan_id)
                print_info("Duration", f"{data.get('duration_days', 30)} days")
                print_info("Topics", str(len(data.get('topics', []))))
                return True
            else:
                print_error(f"Plan generation failed: {response.status_code}")
                print_error(response.text)
                return False
                
        except Exception as e:
            print_error(f"Plan generation error: {str(e)}")
            return False
    
    def test_8_generate_yml(self) -> bool:
        """Test generating personalized YML"""
        print_step("Generating personalized YML content...")
        
        yml_data = {
            "study_plan_id": self.plan_id,
            "include_videos": True,
            "include_exercises": True,
            "language": "es"
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/yml/generate",
                json=yml_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.yml_id = data["yml_id"]
                print_success("YML generated successfully")
                print_info("YML ID", self.yml_id)
                print_info("Status", data.get("status", "ready"))
                
                # Wait for generation if async
                if data.get("status") == "generating":
                    print("  Waiting for YML generation...")
                    time.sleep(3)
                    
                return True
            else:
                print_error(f"YML generation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"YML generation error: {str(e)}")
            return False
    
    def test_9_get_youtube_videos(self) -> bool:
        """Test getting YouTube video recommendations"""
        print_step("Getting YouTube video recommendations...")
        
        try:
            response = self.session.get(
                f"{BASE_URL}/youtube/recommendations/for-yml-plan/{self.yml_id}"
            )
            
            if response.status_code == 200:
                videos = response.json()
                print_success("YouTube videos retrieved")
                print_info("Total Videos", str(len(videos)))
                
                # Show first 3 videos
                for i, video in enumerate(videos[:3], 1):
                    print(f"  Video {i}: {video.get('title', 'N/A')[:50]}...")
                    
                return True
            else:
                print_error(f"Failed to get videos: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Get videos error: {str(e)}")
            return False
    
    def test_10_check_freemium_limits(self) -> bool:
        """Test freemium limits enforcement"""
        print_step("Checking freemium limits...")
        
        try:
            response = self.session.get(f"{BASE_URL}/users/limits")
            
            if response.status_code == 200:
                limits = response.json()
                print_success("Freemium limits checked")
                print_info("Questions Today", f"{limits.get('questions_used', 0)}/{limits.get('questions_limit', 10)}")
                print_info("Tests This Month", f"{limits.get('tests_used', 1)}/{limits.get('tests_limit', 1)}")
                print_info("AI Explanations", f"{limits.get('ai_used', 0)}/{limits.get('ai_limit', 5)}")
                return True
            else:
                print_error(f"Failed to check limits: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Check limits error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("ICFES LEVELING - COMPLETE FLOW INTEGRATION TEST")
        print(f"{'='*60}{Colors.ENDC}\n")
        
        print_info("API URL", BASE_URL)
        print_info("Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print()
        
        tests = [
            self.test_1_register_user,
            self.test_2_login,
            self.test_3_create_diagnostic_test,
            self.test_4_answer_questions,
            self.test_5_submit_test,
            self.test_6_get_results,
            self.test_7_generate_study_plan,
            self.test_8_generate_yml,
            self.test_9_get_youtube_videos,
            self.test_10_check_freemium_limits
        ]
        
        passed = 0
        failed = 0
        
        for i, test in enumerate(tests, 1):
            print(f"\n{Colors.BOLD}Test {i}/10{Colors.ENDC}")
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
                    print(f"{Colors.WARNING}⚠ Continuing with remaining tests...{Colors.ENDC}")
            except Exception as e:
                failed += 1
                print_error(f"Unexpected error: {str(e)}")
                print(f"{Colors.WARNING}⚠ Continuing with remaining tests...{Colors.ENDC}")
            
            time.sleep(1)  # Small delay between tests
        
        # Print summary
        print(f"\n{Colors.HEADER}{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}{Colors.ENDC}\n")
        
        total = passed + failed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        if passed == total:
            print(f"{Colors.OKGREEN}🎉 ALL TESTS PASSED! ({passed}/{total}){Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ SOME TESTS FAILED{Colors.ENDC}")
            
        print_info("Passed", f"{passed}")
        print_info("Failed", f"{failed}")
        print_info("Success Rate", f"{success_rate:.1f}%")
        
        if self.user_data:
            print(f"\n{Colors.BOLD}Test User Credentials:{Colors.ENDC}")
            print_info("Email", self.user_data["email"])
            print_info("Password", self.user_data["password"])
            
        print(f"\n{Colors.BOLD}Test Artifacts:{Colors.ENDC}")
        if self.test_id:
            print_info("Test ID", self.test_id)
        if self.plan_id:
            print_info("Plan ID", self.plan_id)
        if self.yml_id:
            print_info("YML ID", self.yml_id)
        
        return passed == total

if __name__ == "__main__":
    tester = ICFESIntegrationTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)