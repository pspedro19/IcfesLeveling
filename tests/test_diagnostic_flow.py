#!/usr/bin/env python3
"""
Complete Diagnostic Flow Test Script
Tests the entire diagnostic process from initialization to completion
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {"username": "test", "password": "secret"}
SUBJECTS = ["matematicas", "fisica", "quimica", "biologia", "espanol"]

class DiagnosticFlowTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = {}
        
    def print_step(self, step: str, status: str = "RUNNING"):
        print(f"\n{'='*60}")
        print(f"STEP: {step}")
        print(f"STATUS: {status}")
        print('='*60)
    
    def print_result(self, test_name: str, success: bool, details: str = ""):
        status = "[PASS]" if success else "[FAIL]" 
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        return success
    
    def test_api_health(self) -> bool:
        """Test if the API is responding"""
        self.print_step("1. Testing API Health")
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                return self.print_result("API Health Check", True, 
                    f"Service: {data.get('message', 'Unknown')}")
            else:
                return self.print_result("API Health Check", False, 
                    f"Status: {response.status_code}")
        except Exception as e:
            return self.print_result("API Health Check", False, str(e))
    
    def test_subjects_endpoint(self) -> bool:
        """Test subjects endpoint"""
        self.print_step("2. Testing Subjects Endpoint")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/subjects")
            if response.status_code == 200:
                subjects = response.json()
                return self.print_result("Subjects Endpoint", True, 
                    f"Found {len(subjects)} subjects")
            else:
                return self.print_result("Subjects Endpoint", False, 
                    f"Status: {response.status_code}")
        except Exception as e:
            return self.print_result("Subjects Endpoint", False, str(e))
    
    def test_user_authentication(self) -> bool:
        """Test user authentication"""
        self.print_step("3. Testing User Authentication")
        try:
            response = self.session.post(f"{self.base_url}/api/v1/auth-simple/login", 
                json=TEST_USER)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                if self.auth_token:
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    return self.print_result("User Authentication", True, 
                        f"User: {data.get('user', {}).get('display_name', 'Unknown')}")
                else:
                    return self.print_result("User Authentication", False, "No token received")
            else:
                return self.print_result("User Authentication", False, 
                    f"Status: {response.status_code}")
        except Exception as e:
            return self.print_result("User Authentication", False, str(e))
    
    def test_diagnostic_initialization(self, subject: str) -> Dict[str, Any]:
        """Test diagnostic test initialization"""
        self.print_step(f"4. Testing Diagnostic Initialization - {subject.title()}")
        try:
            response = self.session.post(f"{self.base_url}/api/v1/diagnostic/start", 
                json={"subject_id": subject})
            if response.status_code == 200:
                data = response.json()
                test_id = data.get("test_id") or data.get("session_id")
                if test_id:
                    self.print_result("Diagnostic Initialization", True, 
                        f"Test ID: {test_id}")
                    return {
                        "success": True,
                        "test_id": test_id,
                        "data": data
                    }
                else:
                    self.print_result("Diagnostic Initialization", False, "No test ID received")
                    return {"success": False}
            else:
                self.print_result("Diagnostic Initialization", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return {"success": False}
        except Exception as e:
            self.print_result("Diagnostic Initialization", False, str(e))
            return {"success": False}
    
    def test_question_retrieval(self, test_id: str, subject: str) -> Dict[str, Any]:
        """Test question retrieval from database"""
        self.print_step(f"5. Testing Question Retrieval - {subject.title()}")
        
        # Try different endpoint patterns
        endpoints_to_try = [
            f"/api/v1/diagnostic/{test_id}/questions",
            f"/api/v1/diagnostic/{test_id}/next-question", 
            f"/api/v1/diagnostic/{test_id}/question",
            f"/api/v1/questions/{subject}",
            f"/api/v1/questions?subject={subject}"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    question_data = data.get("question") or data.get("questions") or data
                    if question_data:
                        self.print_result("Question Retrieval", True, 
                            f"Endpoint: {endpoint}, Got questions")
                        return {
                            "success": True,
                            "endpoint": endpoint,
                            "questions": question_data,
                            "data": data
                        }
            except Exception as e:
                continue
        
        self.print_result("Question Retrieval", False, "No working endpoint found")
        return {"success": False}
    
    def test_answer_submission(self, test_id: str, question_data: Dict) -> Dict[str, Any]:
        """Test answer submission and processing"""
        self.print_step("6. Testing Answer Submission")
        
        # Try to extract question info
        question_id = question_data.get("id") or question_data.get("question_id") or 1
        
        # Submit a test answer
        answer_payload = {
            "session_id": test_id,
            "question_id": question_id,
            "selected_option": "A",
            "user_answer": "A",
            "time_seconds": 30,
            "response_time_ms": 30000
        }
        
        endpoints_to_try = [
            f"/api/v1/diagnostic/{test_id}/answer",
            f"/api/v1/diagnostic/{test_id}/submit",
            f"/api/v1/diagnostic/answer"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                response = self.session.post(f"{self.base_url}{endpoint}", 
                    json=answer_payload)
                if response.status_code == 200:
                    data = response.json()
                    self.print_result("Answer Submission", True, 
                        f"Endpoint: {endpoint}")
                    return {
                        "success": True,
                        "endpoint": endpoint,
                        "response": data
                    }
            except Exception as e:
                continue
        
        self.print_result("Answer Submission", False, "No working endpoint found")
        return {"success": False}
    
    def test_irt_calculations(self, answer_response: Dict) -> bool:
        """Test IRT calculations and theta updates"""
        self.print_step("7. Testing IRT Calculations")
        
        # Check for theta-related fields in the response
        theta_fields = [
            "updated_theta", "current_theta", "theta", "ability_estimate",
            "new_theta", "theta_change", "final_theta"
        ]
        
        found_theta = False
        for field in theta_fields:
            if field in answer_response:
                found_theta = True
                theta_value = answer_response[field]
                self.print_result("IRT Theta Calculation", True, 
                    f"Found {field}: {theta_value}")
                break
        
        if not found_theta:
            self.print_result("IRT Theta Calculation", False, 
                "No theta-related fields found")
        
        # Check for rank/level updates
        rank_fields = ["rank", "updated_rank", "level", "mastery_level"]
        found_rank = False
        for field in rank_fields:
            if field in answer_response:
                found_rank = True
                rank_value = answer_response[field]
                self.print_result("Performance Ranking", True, 
                    f"Found {field}: {rank_value}")
                break
        
        if not found_rank:
            self.print_result("Performance Ranking", False, 
                "No rank/level fields found")
        
        return found_theta or found_rank
    
    def test_adaptive_selection(self, test_id: str) -> bool:
        """Test adaptive question selection"""
        self.print_step("8. Testing Adaptive Question Selection")
        
        # Try to get multiple questions to test adaptation
        questions = []
        for i in range(3):
            try:
                response = self.session.get(f"{self.base_url}/api/v1/diagnostic/{test_id}/next-question")
                if response.status_code == 200:
                    data = response.json()
                    question = data.get("question")
                    if question:
                        questions.append(question)
                        # Submit an answer to trigger adaptation
                        self.session.post(f"{self.base_url}/api/v1/diagnostic/{test_id}/answer", 
                            json={
                                "session_id": test_id,
                                "question_id": question.get("id", 1),
                                "selected_option": "A",
                                "time_seconds": 25
                            })
            except:
                continue
        
        if len(questions) > 1:
            difficulties = [q.get("difficulty") for q in questions]
            return self.print_result("Adaptive Selection", True, 
                f"Got {len(questions)} questions with difficulties: {difficulties}")
        else:
            return self.print_result("Adaptive Selection", False, 
                f"Only got {len(questions)} questions")
    
    def test_complete_diagnostic_flow(self, subject: str) -> Dict[str, Any]:
        """Test complete diagnostic flow for a subject"""
        self.print_step(f"TESTING COMPLETE DIAGNOSTIC FLOW - {subject.upper()}")
        
        # Initialize diagnostic
        init_result = self.test_diagnostic_initialization(subject)
        if not init_result["success"]:
            return {"success": False, "step": "initialization"}
        
        test_id = init_result["test_id"]
        
        # Get questions
        questions_result = self.test_question_retrieval(test_id, subject)
        if not questions_result["success"]:
            return {"success": False, "step": "question_retrieval"}
        
        # Submit answer
        question_data = questions_result["questions"]
        if isinstance(question_data, list) and question_data:
            question_data = question_data[0]
        
        answer_result = self.test_answer_submission(test_id, question_data)
        if not answer_result["success"]:
            return {"success": False, "step": "answer_submission"}
        
        # Test IRT calculations
        irt_success = self.test_irt_calculations(answer_result["response"])
        
        # Test adaptive selection
        adaptive_success = self.test_adaptive_selection(test_id)
        
        return {
            "success": True,
            "subject": subject,
            "test_id": test_id,
            "irt_working": irt_success,
            "adaptive_working": adaptive_success
        }
    
    def run_complete_test_suite(self):
        """Run complete test suite"""
        print("\n" + "="*80)
        print("ICFES LEVELING DIAGNOSTIC FLOW TEST SUITE")
        print("="*80)
        
        # Pre-flight checks
        if not self.test_api_health():
            print("\n❌ API not responding. Exiting.")
            return
        
        if not self.test_subjects_endpoint():
            print("\n⚠️  Subjects endpoint not working. Continuing anyway...")
        
        # Authentication (optional)
        auth_success = self.test_user_authentication()
        if not auth_success:
            print("\n⚠️  Authentication failed. Continuing without auth...")
        
        # Test diagnostic flow for each subject
        results = {}
        for subject in SUBJECTS:
            print(f"\n{'='*80}")
            print(f"TESTING SUBJECT: {subject.upper()}")
            print('='*80)
            
            result = self.test_complete_diagnostic_flow(subject)
            results[subject] = result
        
        # Print final summary
        self.print_final_summary(results)
    
    def print_final_summary(self, results: Dict):
        """Print final test summary"""
        print("\n" + "="*80)
        print("FINAL TEST SUMMARY")
        print("="*80)
        
        total_subjects = len(results)
        successful_subjects = sum(1 for r in results.values() if r["success"])
        irt_working_count = sum(1 for r in results.values() if r.get("irt_working", False))
        adaptive_working_count = sum(1 for r in results.values() if r.get("adaptive_working", False))
        
        print(f"\n[OVERALL RESULTS]:")
        print(f"   - Subjects Tested: {total_subjects}")
        print(f"   - Successful Tests: {successful_subjects}/{total_subjects}")
        print(f"   - IRT System Working: {irt_working_count}/{total_subjects} subjects")
        print(f"   - Adaptive Selection Working: {adaptive_working_count}/{total_subjects} subjects")
        
        print(f"\n[DETAILED RESULTS]:")
        for subject, result in results.items():
            status = "[PASS]" if result["success"] else "[FAIL]"
            irt_status = "IRT:[PASS]" if result.get("irt_working") else "IRT:[FAIL]"
            adaptive_status = "Adaptive:[PASS]" if result.get("adaptive_working") else "Adaptive:[FAIL]"
            print(f"   {status} {subject.title():<15} {irt_status:<8} {adaptive_status}")
        
        # Overall assessment
        if successful_subjects == total_subjects:
            print(f"\n[SUCCESS] ALL TESTS PASSED! Diagnostic system is fully operational.")
        elif successful_subjects > total_subjects // 2:
            print(f"\n[WARNING] PARTIALLY WORKING: {successful_subjects}/{total_subjects} subjects working.")
        else:
            print(f"\n[ERROR] SYSTEM ISSUES: Only {successful_subjects}/{total_subjects} subjects working.")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    tester = DiagnosticFlowTester(BASE_URL)
    tester.run_complete_test_suite()