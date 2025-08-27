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
        """Test health check endpoint with detailed validation"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        
        if success:
            # Validate required fields
            required_fields = ['status', 'groq_configured', 'api_key_status', 'opensora_available', 'active_chat_sessions']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
                self.minor_issues.append(f"Health check missing fields: {missing_fields}")
            else:
                print(f"   ✅ All required fields present")
            
            # Check Groq configuration
            groq_configured = response.get('groq_configured', False)
            if groq_configured:
                print(f"   ✅ Groq API is properly configured")
            else:
                print(f"   ❌ Groq API configuration issue")
                self.critical_failures.append("Groq API not configured")
                
            # Check API key rotation status
            api_key_status = response.get('api_key_status', {})
            if api_key_status:
                print(f"   📊 API Key Status:")
                print(f"      - Current Key Index: {api_key_status.get('current_key_index', 'N/A')}")
                print(f"      - Request Count: {api_key_status.get('request_count', 'N/A')}")
                print(f"      - Total Keys: {api_key_status.get('total_keys', 'N/A')}")
                print(f"      - Max Requests Per Key: {api_key_status.get('max_requests_per_key', 'N/A')}")
            
            # Check OpenSora availability
            opensora_available = response.get('opensora_available', False)
            print(f"   📹 OpenSora Available: {opensora_available}")
            
            # Check active chat sessions
            active_sessions = response.get('active_chat_sessions', 0)
            print(f"   💬 Active Chat Sessions: {active_sessions}")
                
        return success

    def test_generate_content_without_learning_style(self):
        """Test content generation without learning_style parameter (should default to 'comprehensive')"""
        test_data = {
            "topic": "Machine Learning Fundamentals",
            "learner_level": "beginner"
            # Intentionally omitting learning_style to test default behavior
        }
        
        success, response = self.run_test(
            "Generate Content (No Learning Style)",
            "POST",
            "generate_content",
            200,
            data=test_data,
            timeout=60
        )
        
        if success:
            self._validate_content_response(response, "Machine Learning Fundamentals")
            self.content_ids.append(response.get('id'))
            
            # Check if learning_style was set to default
            learning_style = response.get('learning_style')
            if learning_style == 'comprehensive':
                print(f"   ✅ Learning style correctly defaulted to 'comprehensive'")
            else:
                print(f"   ⚠️  Learning style is '{learning_style}', expected 'comprehensive'")
                self.minor_issues.append(f"Learning style not defaulting correctly: {learning_style}")
                
        return success

    def test_generate_content_with_learning_style(self):
        """Test content generation with explicit learning_style parameter"""
        test_data = {
            "topic": "Quantum Physics Basics",
            "learner_level": "intermediate",
            "learning_style": "visual"
        }
        
        success, response = self.run_test(
            "Generate Content (With Learning Style)",
            "POST",
            "generate_content",
            200,
            data=test_data,
            timeout=60
        )
        
        if success:
            self._validate_content_response(response, "Quantum Physics Basics")
            self.content_ids.append(response.get('id'))
                
        return success

    def test_generate_content_spanish_grammar(self):
        """Test content generation with Spanish Grammar topic"""
        test_data = {
            "topic": "Spanish Grammar - Present Tense",
            "learner_level": "beginner"
        }
        
        success, response = self.run_test(
            "Generate Content (Spanish Grammar)",
            "POST",
            "generate_content",
            200,
            data=test_data,
            timeout=60
        )
        
        if success:
            self._validate_content_response(response, "Spanish Grammar")
            self.content_ids.append(response.get('id'))
                
        return success

    def _validate_content_response(self, response, topic_keyword):
        """Validate the structure and quality of content generation response"""
        # Validate response structure
        required_fields = ['id', 'topic', 'learner_level', 'learning_style', 
                         'learning_objectives', 'video_script', 'quiz', 'flashcards']
        
        missing_fields = [field for field in required_fields if field not in response]
        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
            self.critical_failures.append(f"Content generation missing fields: {missing_fields}")
        else:
            print(f"   ✅ All required fields present")
        
        # Validate learning objectives (should be 5-7)
        objectives = response.get('learning_objectives', [])
        objectives_count = len(objectives)
        print(f"   📚 Learning Objectives: {objectives_count}")
        
        if 5 <= objectives_count <= 7:
            print(f"   ✅ Learning objectives count is appropriate (5-7)")
        else:
            print(f"   ⚠️  Learning objectives count should be 5-7, got {objectives_count}")
            self.minor_issues.append(f"Learning objectives count: {objectives_count} (expected 5-7)")
        
        # Check if objectives are topic-specific
        topic_specific_objectives = [obj for obj in objectives if topic_keyword.lower() in obj.lower()]
        if len(topic_specific_objectives) >= 3:
            print(f"   ✅ Learning objectives are topic-specific")
        else:
            print(f"   ⚠️  Learning objectives may be too generic")
            self.minor_issues.append("Learning objectives appear generic")
        
        # Validate video script quality
        video_script = response.get('video_script', '')
        script_length = len(video_script)
        print(f"   🎬 Video Script Length: {script_length} characters")
        
        if script_length > 500:
            print(f"   ✅ Video script has substantial content")
        else:
            print(f"   ⚠️  Video script seems too short")
            self.minor_issues.append(f"Video script too short: {script_length} chars")
        
        # Check for developer instructions in video script
        dev_markers = ['[SCENE:', '[CUT TO:', '[FADE IN:', '[FADE OUT:', 'DEVELOPER NOTE:', '[INSTRUCTION:']
        has_dev_markers = any(marker in video_script.upper() for marker in dev_markers)
        
        if not has_dev_markers:
            print(f"   ✅ Video script is user-friendly without developer instructions")
        else:
            print(f"   ❌ Video script contains developer instructions/scene markers")
            self.critical_failures.append("Video script contains developer instructions")
        
        # Validate quiz questions (should be 5)
        quiz = response.get('quiz', [])
        quiz_count = len(quiz)
        print(f"   ❓ Quiz Questions: {quiz_count}")
        
        if quiz_count == 5:
            print(f"   ✅ Quiz has correct number of questions (5)")
        else:
            print(f"   ⚠️  Quiz should have 5 questions, got {quiz_count}")
            self.minor_issues.append(f"Quiz question count: {quiz_count} (expected 5)")
        
        # Validate quiz quality
        if quiz:
            first_question = quiz[0]
            required_quiz_fields = ['question', 'options', 'correct_answer', 'explanation', 'hint']
            missing_quiz_fields = [field for field in required_quiz_fields if field not in first_question]
            
            if not missing_quiz_fields:
                print(f"   ✅ Quiz questions have proper structure")
            else:
                print(f"   ❌ Quiz questions missing fields: {missing_quiz_fields}")
                self.critical_failures.append(f"Quiz structure incomplete: {missing_quiz_fields}")
            
            # Check if quiz is topic-specific
            topic_specific_questions = [q for q in quiz if topic_keyword.lower() in q.get('question', '').lower()]
            if len(topic_specific_questions) >= 2:
                print(f"   ✅ Quiz questions are topic-specific")
            else:
                print(f"   ⚠️  Quiz questions may be too generic")
                self.minor_issues.append("Quiz questions appear generic")
        
        # Validate flashcards (should be 8)
        flashcards = response.get('flashcards', [])
        flashcards_count = len(flashcards)
        print(f"   🗂️  Flashcards: {flashcards_count}")
        
        if flashcards_count == 8:
            print(f"   ✅ Flashcards have correct count (8)")
        else:
            print(f"   ⚠️  Flashcards should be 8, got {flashcards_count}")
            self.minor_issues.append(f"Flashcard count: {flashcards_count} (expected 8)")
        
        # Check flashcard quality
        if flashcards:
            topic_specific_flashcards = [fc for fc in flashcards if topic_keyword.lower() in fc.get('front', '').lower() or topic_keyword.lower() in fc.get('back', '').lower()]
            if len(topic_specific_flashcards) >= 4:
                print(f"   ✅ Flashcards are topic-specific")
            else:
                print(f"   ⚠️  Flashcards may be too generic")
                self.minor_issues.append("Flashcards appear generic")

    def test_generate_video(self):
        """Test video generation endpoint"""
        if not self.content_ids:
            print("❌ SKIPPED - No content IDs available for video generation")
            return False
            
        # Use the first content ID for video generation
        content_id = self.content_ids[0]
        test_data = {
            "content_id": content_id
        }
        
        print(f"   Using content ID: {content_id}")
        
        success, response = self.run_test(
            "Generate Video",
            "POST",
            "generate_video",
            200,
            data=test_data,
            timeout=120  # Video generation takes longer
        )
        
        if success:
            print(f"   ✅ Video generation initiated successfully")
            # Note: Video generation is async, so we just check if the request was accepted
        
        return success

    def test_get_content(self):
        """Test get content by ID endpoint"""
        if not self.content_ids:
            print("❌ SKIPPED - No content IDs available")
            return False
            
        # Test retrieving the first content
        content_id = self.content_ids[0]
        success, response = self.run_test(
            "Get Content by ID",
            "GET",
            f"content/{content_id}",
            200
        )
        
        if success:
            print(f"   ✅ Successfully retrieved content by ID")
            # Validate that the retrieved content matches what we expect
            if response.get('id') == content_id:
                print(f"   ✅ Content ID matches request")
            else:
                print(f"   ❌ Content ID mismatch")
                self.critical_failures.append("Content ID mismatch in retrieval")
        
        return success

    def test_chat_functionality(self):
        """Test basic chat functionality"""
        test_data = {
            "session_id": "test_session_123",
            "message": "What is machine learning?",
            "context": {"topic": "Machine Learning"}
        }
        
        success, response = self.run_test(
            "Chat Functionality",
            "POST",
            "chat",
            200,
            data=test_data,
            timeout=30
        )
        
        if success:
            # Validate chat response structure
            required_fields = ['response', 'session_id', 'timestamp']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                print(f"   ✅ Chat response has proper structure")
            else:
                print(f"   ❌ Chat response missing fields: {missing_fields}")
                self.critical_failures.append(f"Chat response incomplete: {missing_fields}")
            
            # Check if response is meaningful
            chat_response = response.get('response', '')
            if len(chat_response) > 20:
                print(f"   ✅ Chat response has substantial content")
            else:
                print(f"   ⚠️  Chat response seems too short")
                self.minor_issues.append("Chat response too short")
            
            # Check session management
            returned_session_id = response.get('session_id')
            if returned_session_id == test_data['session_id']:
                print(f"   ✅ Session ID properly managed")
            else:
                print(f"   ⚠️  Session ID mismatch")
                self.minor_issues.append("Session ID management issue")
        
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
    
    # Run all tests in priority order
    tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Health Check", tester.test_health_check),
        ("Content Generation (No Learning Style)", tester.test_generate_content_without_learning_style),
        ("Content Generation (With Learning Style)", tester.test_generate_content_with_learning_style),
        ("Content Generation (Spanish Grammar)", tester.test_generate_content_spanish_grammar),
        ("Get Content", tester.test_get_content),
        ("Chat Functionality", tester.test_chat_functionality),
        ("Video Generation", tester.test_generate_video),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ FAILED - Unexpected error in {test_name}: {str(e)}")
            tester.critical_failures.append(f"{test_name}: Unexpected error - {str(e)}")
        
        time.sleep(1)  # Brief pause between tests
    
    # Print final results
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    # Report critical failures
    if tester.critical_failures:
        print(f"\n❌ CRITICAL FAILURES ({len(tester.critical_failures)}):")
        for i, failure in enumerate(tester.critical_failures, 1):
            print(f"   {i}. {failure}")
    
    # Report minor issues
    if tester.minor_issues:
        print(f"\n⚠️  MINOR ISSUES ({len(tester.minor_issues)}):")
        for i, issue in enumerate(tester.minor_issues, 1):
            print(f"   {i}. {issue}")
    
    # Overall assessment
    if tester.tests_passed == tester.tests_run and not tester.critical_failures:
        print("\n🎉 ALL TESTS PASSED WITH NO CRITICAL ISSUES!")
        return 0
    elif tester.critical_failures:
        print(f"\n⚠️  CRITICAL ISSUES FOUND - Backend needs attention")
        return 1
    else:
        print(f"\n⚠️  SOME TESTS FAILED - Check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())