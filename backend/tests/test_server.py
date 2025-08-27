# Test server endpoints
import pytest
import json
from unittest.mock import patch, MagicMock
from httpx import AsyncClient

@pytest.mark.asyncio
class TestServerEndpoints:
    """Test all server endpoints"""
    
    async def test_root_endpoint(self, test_client):
        """Test root API endpoint"""
        response = await test_client.get("/api/")
        assert response.status_code == 200
        data = response.json()
        assert "EduForge AI API v2.0" in data["message"]
    
    async def test_health_check(self, test_client):
        """Test health check endpoint"""
        with patch('server.video_service') as mock_video, \
             patch('server.groq_service') as mock_groq, \
             patch('server.chatbot_service') as mock_chat:
            
            mock_video._is_opensora_available.return_value = True
            mock_groq.current_key_index = 0
            mock_groq.request_count = 5
            mock_groq.api_keys = ["key1", "key2"]
            mock_groq.max_requests_per_key = 20
            mock_chat.get_session_stats.return_value = {"active_sessions": 2}
            
            response = await test_client.get("/api/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["groq_configured"] == True
            assert "api_key_status" in data
            assert data["active_chat_sessions"] == 2
    
    @patch('server.db')
    @patch('server.groq_service')
    async def test_generate_content_success(self, mock_groq, mock_db, test_client, sample_content_request):
        """Test successful content generation"""
        # Mock Groq service response
        mock_groq.generate_educational_content.return_value = {
            "learning_objectives": ["Objective 1", "Objective 2"],
            "video_script": "Test script content",
            "quiz": [{
                "question": "Test question?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": 0,
                "explanation": "Test explanation",
                "hint": "Test hint"
            }],
            "flashcards": [{
                "front": "Front text",
                "back": "Back text"
            }],
            "ui_suggestions": {
                "color_scheme": "Blue theme",
                "layout_emphasis": "Visual focus",
                "interaction_type": "Interactive"
            }
        }
        
        # Mock database insert
        mock_db.educational_content.insert_one = MagicMock()
        
        response = await test_client.post("/api/generate_content", json=sample_content_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["topic"] == sample_content_request["topic"]
        assert data["learner_level"] == sample_content_request["learner_level"]
        assert data["learning_style"] == sample_content_request["learning_style"]
        assert len(data["learning_objectives"]) >= 1
        assert len(data["quiz"]) >= 1
        assert len(data["flashcards"]) >= 1
    
    async def test_generate_content_invalid_style(self, test_client):
        """Test content generation with invalid learning style"""
        invalid_request = {
            "topic": "Test Topic",
            "learner_level": "beginner",
            "learning_style": "invalid_style"
        }
        
        response = await test_client.post("/api/generate_content", json=invalid_request)
        assert response.status_code == 400
        assert "Invalid learning style" in response.json()["detail"]
    
    async def test_generate_content_invalid_level(self, test_client):
        """Test content generation with invalid learner level"""
        invalid_request = {
            "topic": "Test Topic",
            "learner_level": "invalid_level",
            "learning_style": "visual"
        }
        
        response = await test_client.post("/api/generate_content", json=invalid_request)
        assert response.status_code == 400
        assert "Invalid learner level" in response.json()["detail"]
    
    @patch('server.db')
    @patch('server.video_service')
    async def test_generate_video_success(self, mock_video, mock_db, test_client):
        """Test successful video generation"""
        # Mock database content retrieval
        mock_db.educational_content.find_one.return_value = {
            "id": "test_id",
            "video_script": "Test script",
            "topic": "Test Topic",
            "learning_style": "visual"
        }
        
        # Mock video service
        mock_video.generate_video.return_value = "/tmp/test_video.mp4"
        mock_db.educational_content.update_one = MagicMock()
        
        # Create a temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b"fake video content")
            video_path = tmp.name
        
        mock_video.generate_video.return_value = video_path
        
        request_data = {"content_id": "test_id"}
        response = await test_client.post("/api/generate_video", json=request_data)
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/mp4"
    
    @patch('server.db')
    async def test_generate_video_content_not_found(self, mock_db, test_client):
        """Test video generation with non-existent content"""
        mock_db.educational_content.find_one.return_value = None
        
        request_data = {"content_id": "nonexistent_id"}
        response = await test_client.post("/api/generate_video", json=request_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch('server.db')
    async def test_get_content_success(self, mock_db, test_client, sample_educational_content):
        """Test successful content retrieval"""
        mock_db.educational_content.find_one.return_value = sample_educational_content
        
        response = await test_client.get("/api/content/test_id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == "test_content_id"
        assert data["topic"] == "Machine Learning Basics"
    
    @patch('server.db')
    async def test_get_content_not_found(self, mock_db, test_client):
        """Test content retrieval for non-existent content"""
        mock_db.educational_content.find_one.return_value = None
        
        response = await test_client.get("/api/content/nonexistent_id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch('server.db')
    async def test_video_status_completed(self, mock_db, test_client):
        """Test video status when video is completed"""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b"video content")
            video_path = tmp.name
        
        mock_db.educational_content.find_one.return_value = {
            "id": "test_id",
            "video_path": video_path
        }
        
        response = await test_client.get("/api/video_status/test_id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress_percentage"] == 100
    
    @patch('server.db')
    async def test_video_status_processing(self, mock_db, test_client):
        """Test video status when video is still processing"""
        mock_db.educational_content.find_one.return_value = {
            "id": "test_id",
            "video_path": None
        }
        
        response = await test_client.get("/api/video_status/test_id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "processing"
        assert data["progress_percentage"] == 50
    
    @patch('server.chatbot_service')
    async def test_chat_success(self, mock_chatbot, test_client):
        """Test successful chat interaction"""
        mock_chatbot.chat.return_value = {
            "response": "This is a test response",
            "session_id": "test_session",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        request_data = {
            "session_id": "test_session",
            "message": "Hello, can you help me?"
        }
        
        response = await test_client.post("/api/chat", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["response"] == "This is a test response"
        assert data["session_id"] == "test_session"
    
    @patch('server.chatbot_service')
    async def test_chat_error_handling(self, mock_chatbot, test_client):
        """Test chat error handling"""
        mock_chatbot.chat.side_effect = Exception("API Error")
        
        request_data = {
            "session_id": "test_session",
            "message": "Hello"
        }
        
        response = await test_client.post("/api/chat", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["error"] == True
        assert "technical difficulties" in data["response"]
    
    @patch('server.chatbot_service')
    async def test_summarize_topic(self, mock_chatbot, test_client):
        """Test topic summarization"""
        mock_chatbot.summarize_topic.return_value = {
            "response": "This is a comprehensive summary",
            "session_id": "test_session",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        request_data = {
            "session_id": "test_session",
            "topic": "Machine Learning",
            "detail_level": "medium"
        }
        
        response = await test_client.post("/api/chat/summarize", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "comprehensive summary" in data["response"]
    
    @patch('server.chatbot_service')
    async def test_get_study_tips(self, mock_chatbot, test_client):
        """Test study tips generation"""
        mock_chatbot.get_study_tips.return_value = {
            "response": "Here are effective study strategies",
            "session_id": "test_session",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        request_data = {
            "session_id": "test_session",
            "topic": "Python Programming",
            "learning_style": "visual"
        }
        
        response = await test_client.post("/api/chat/study_tips", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "study strategies" in data["response"]
    
    @patch('server.chatbot_service')
    async def test_get_chat_history(self, mock_chatbot, test_client):
        """Test chat history retrieval"""
        mock_chatbot.get_conversation_history.return_value = [
            {"role": "user", "content": "Hello", "timestamp": "2023-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2023-01-01T00:00:01"}
        ]
        
        response = await test_client.get("/api/chat/history/test_session")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == "test_session"
        assert len(data["messages"]) == 2
    
    @patch('server.chatbot_service')
    async def test_clear_chat_session(self, mock_chatbot, test_client):
        """Test chat session clearing"""
        mock_chatbot.clear_conversation.return_value = True
        
        response = await test_client.delete("/api/chat/test_session")
        assert response.status_code == 200
        
        data = response.json()
        assert "cleared successfully" in data["message"]
    
    @patch('server.chatbot_service')
    async def test_chat_statistics(self, mock_chatbot, test_client):
        """Test chat statistics endpoint"""
        mock_chatbot.get_session_stats.return_value = {
            "active_sessions": 5,
            "total_messages": 50,
            "average_messages_per_session": 10.0
        }
        mock_chatbot.get_active_sessions.return_value = ["session1", "session2", "session3"]
        
        response = await test_client.get("/api/admin/chat_stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["statistics"]["active_sessions"] == 5
        assert data["active_sessions"] == 3
    
    @patch('server.db')
    async def test_legacy_status_endpoints(self, mock_db, test_client):
        """Test legacy status check endpoints"""
        mock_db.status_checks.insert_one = MagicMock()
        mock_db.status_checks.find.return_value.to_list.return_value = [
            {"id": "test_id", "client_name": "test_client", "timestamp": "2023-01-01T00:00:00"}
        ]
        
        # Test create status
        request_data = {"client_name": "test_client"}
        response = await test_client.post("/api/status", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["client_name"] == "test_client"
        
        # Test get status
        response = await test_client.get("/api/status")
        assert response.status_code == 200
        assert isinstance(response.json(), list)