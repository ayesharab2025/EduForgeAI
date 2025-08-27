#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class ChatbotAPITester:
    def __init__(self, base_url="https://learnforge-16.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = f"test_session_{int(time.time())}"

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - {name}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    def test_chat_basic(self):
        """Test basic chat functionality"""
        test_data = {
            "session_id": self.session_id,
            "message": "What is machine learning?",
            "context": {}
        }
        
        success, response = self.run_test(
            "Basic Chat",
            "POST",
            "chat",
            200,
            data=test_data,
            timeout=45
        )
        
        if success:
            if 'response' in response and response['response']:
                print(f"   ✅ Bot responded with: {response['response'][:100]}...")
            else:
                print(f"   ⚠️  Empty or missing response")
                
        return success

    def test_summarize_topic(self):
        """Test topic summarization"""
        test_data = {
            "session_id": self.session_id,
            "topic": "Machine Learning Basics",
            "detail_level": "beginner"
        }
        
        success, response = self.run_test(
            "Summarize Topic",
            "POST",
            "chat/summarize",
            200,
            data=test_data,
            timeout=45
        )
        
        return success

    def test_study_tips(self):
        """Test study tips generation"""
        test_data = {
            "session_id": self.session_id,
            "topic": "Machine Learning Basics",
            "learning_style": "visual"
        }
        
        success, response = self.run_test(
            "Study Tips",
            "POST",
            "chat/study_tips",
            200,
            data=test_data,
            timeout=45
        )
        
        return success

    def test_chat_history(self):
        """Test chat history retrieval"""
        success, response = self.run_test(
            "Chat History",
            "GET",
            f"chat/history/{self.session_id}",
            200
        )
        
        return success

    def test_clear_chat(self):
        """Test clearing chat session"""
        success, response = self.run_test(
            "Clear Chat Session",
            "DELETE",
            f"chat/{self.session_id}",
            200
        )
        
        return success

def main():
    print("🤖 Starting EduForge AI Chatbot API Tests")
    print("=" * 60)
    
    tester = ChatbotAPITester()
    
    # Run all tests
    tests = [
        ("Basic Chat", tester.test_chat_basic),
        ("Summarize Topic", tester.test_summarize_topic),
        ("Study Tips", tester.test_study_tips),
        ("Chat History", tester.test_chat_history),
        ("Clear Chat Session", tester.test_clear_chat),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ FAILED - Unexpected error in {test_name}: {str(e)}")
        
        time.sleep(2)  # Brief pause between tests
    
    # Print final results
    print(f"\n{'='*60}")
    print(f"📊 CHATBOT TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL CHATBOT TESTS PASSED!")
        return 0
    else:
        print("⚠️  SOME CHATBOT TESTS FAILED - Check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())