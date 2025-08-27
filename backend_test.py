#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class EduForgeAPITester:
    def __init__(self, base_url="https://learnforge-16.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.content_ids = []
        self.critical_failures = []
        self.minor_issues = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - {name}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:500]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    self.critical_failures.append(f"{name}: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                    self.critical_failures.append(f"{name}: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after {timeout} seconds")
            self.critical_failures.append(f"{name}: Request timeout after {timeout}s")
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.critical_failures.append(f"{name}: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        
        if success:
            groq_configured = response.get('groq_configured', False)
            if groq_configured:
                print(f"   ✅ Groq API is properly configured")
            else:
                print(f"   ⚠️  Groq API configuration issue")
                
        return success

    def test_generate_content(self):
        """Test content generation endpoint"""
        test_data = {
            "topic": "Machine Learning Basics",
            "learner_level": "beginner",
            "learning_style": "visual"
        }
        
        success, response = self.run_test(
            "Generate Content",
            "POST",
            "generate_content",
            200,
            data=test_data,
            timeout=60  # Content generation may take longer
        )
        
        if success:
            # Validate response structure
            required_fields = ['id', 'topic', 'learner_level', 'learning_style', 
                             'learning_objectives', 'video_script', 'quiz', 'flashcards']
            
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
            else:
                print(f"   ✅ All required fields present")
                
            # Store content ID for video generation test
            self.content_id = response.get('id')
            
            # Validate content quality
            objectives_count = len(response.get('learning_objectives', []))
            quiz_count = len(response.get('quiz', []))
            flashcards_count = len(response.get('flashcards', []))
            
            print(f"   📊 Content Stats:")
            print(f"      - Learning Objectives: {objectives_count}")
            print(f"      - Quiz Questions: {quiz_count}")
            print(f"      - Flashcards: {flashcards_count}")
            print(f"      - Video Script Length: {len(response.get('video_script', ''))}")
            
        return success

    def test_generate_video(self):
        """Test video generation endpoint"""
        if not self.content_id:
            print("❌ SKIPPED - No content ID available for video generation")
            return False
            
        test_data = {
            "content_id": self.content_id
        }
        
        print(f"   Using content ID: {self.content_id}")
        
        success, response = self.run_test(
            "Generate Video",
            "POST",
            "generate_video",
            200,
            data=test_data,
            timeout=120  # Video generation takes longer
        )
        
        return success

    def test_get_content(self):
        """Test get content by ID endpoint"""
        if not self.content_id:
            print("❌ SKIPPED - No content ID available")
            return False
            
        success, response = self.run_test(
            "Get Content by ID",
            "GET",
            f"content/{self.content_id}",
            200
        )
        
        return success

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

def main():
    print("🚀 Starting EduForge AI Backend API Tests")
    print("=" * 60)
    
    tester = EduForgeAPITester()
    
    # Run all tests
    tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Health Check", tester.test_health_check),
        ("Content Generation", tester.test_generate_content),
        ("Get Content", tester.test_get_content),
        ("Video Generation", tester.test_generate_video),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ FAILED - Unexpected error in {test_name}: {str(e)}")
        
        time.sleep(1)  # Brief pause between tests
    
    # Print final results
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())