# Test chatbot service functionality
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from services.chatbot_service import ChatbotService

@pytest.mark.asyncio
class TestChatbotService:
    """Test chatbot service functionality"""
    
    def test_initialization(self):
        """Test chatbot service initialization"""
        service = ChatbotService()
        assert service.conversations == {}
        assert service.memory_duration == timedelta(hours=2)
    
    def test_get_or_create_conversation_new(self):
        """Test creating new conversation"""
        service = ChatbotService()
        
        conversation = service._get_or_create_conversation("new_session")
        
        assert "new_session" in service.conversations
        assert "created_at" in conversation
        assert conversation["messages"] == []
        assert conversation["context"] == {}
        assert conversation["user_preferences"] == {}
    
    def test_get_or_create_conversation_existing(self):
        """Test getting existing conversation"""
        service = ChatbotService()
        
        # Create initial conversation
        conv1 = service._get_or_create_conversation("session1")
        conv1["messages"].append({"role": "user", "content": "Hello"})
        
        # Get same conversation
        conv2 = service._get_or_create_conversation("session1")
        
        assert conv1 is conv2
        assert len(conv2["messages"]) == 1
    
    def test_cleanup_old_conversations(self):
        """Test cleanup of old conversations"""
        service = ChatbotService()
        
        # Create old conversation
        old_time = datetime.utcnow() - timedelta(hours=3)
        service.conversations["old_session"] = {
            "created_at": old_time,
            "messages": [],
            "context": {},
            "user_preferences": {}
        }
        
        # Create recent conversation
        service.conversations["recent_session"] = {
            "created_at": datetime.utcnow(),
            "messages": [],
            "context": {},
            "user_preferences": {}
        }
        
        service._cleanup_old_conversations()
        
        assert "old_session" not in service.conversations
        assert "recent_session" in service.conversations
    
    def test_build_system_prompt_base(self):
        """Test building basic system prompt"""
        service = ChatbotService()
        
        conversation = {
            "context": {},
            "messages": []
        }
        
        prompt = service._build_system_prompt(conversation)
        
        assert "EduForge AI Assistant" in prompt
        assert "Answer Questions" in prompt
        assert "Summarize Topics" in prompt
    
    def test_build_system_prompt_with_context(self):
        """Test building system prompt with learning context"""
        service = ChatbotService()
        
        conversation = {
            "context": {
                "current_topic": "Machine Learning",
                "learning_style": "visual",
                "learner_level": "beginner",
                "recent_objectives": ["Learn ML basics", "Understand algorithms", "Practice coding"]
            },
            "messages": []
        }
        
        prompt = service._build_system_prompt(conversation)
        
        assert "Machine Learning" in prompt
        assert "visual" in prompt
        assert "beginner" in prompt
        assert "Learn ML basics" in prompt
    
    def test_build_system_prompt_long_conversation(self):
        """Test building system prompt for long conversation"""
        service = ChatbotService()
        
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(10)]
        conversation = {
            "context": {},
            "messages": messages
        }
        
        prompt = service._build_system_prompt(conversation)
        
        assert "Conversation Summary" in prompt
        assert "continuity" in prompt
    
    @patch('services.chatbot_service.groq_service')
    async def test_chat_success(self, mock_groq):
        """Test successful chat interaction"""
        mock_groq._make_request.return_value = "This is a helpful response from the AI assistant."
        
        service = ChatbotService()
        
        result = await service.chat("test_session", "What is machine learning?")
        
        assert result["response"] == "This is a helpful response from the AI assistant."
        assert result["session_id"] == "test_session"
        assert "timestamp" in result
        assert result.get("error") != True
        
        # Check conversation was stored
        conversation = service.conversations["test_session"]
        assert len(conversation["messages"]) == 2  # user + assistant
        assert conversation["messages"][0]["role"] == "user"
        assert conversation["messages"][1]["role"] == "assistant"
    
    @patch('services.chatbot_service.groq_service')
    async def test_chat_with_context(self, mock_groq):
        """Test chat with additional context"""
        mock_groq._make_request.return_value = "Contextual response"
        
        service = ChatbotService()
        
        context = {
            "current_topic": "Python Programming",
            "learning_style": "kinesthetic"
        }
        
        result = await service.chat("test_session", "How do I learn Python?", context)
        
        # Check context was stored
        conversation = service.conversations["test_session"]
        assert conversation["context"]["current_topic"] == "Python Programming"
        assert conversation["context"]["learning_style"] == "kinesthetic"
    
    @patch('services.chatbot_service.groq_service')
    async def test_chat_api_failure_fallback(self, mock_groq):
        """Test chat fallback when Groq API fails"""
        mock_groq._make_request.return_value = None
        
        service = ChatbotService()
        
        result = await service.chat("test_session", "Help me understand physics")
        
        assert "fallback" in result["response"] or "technical difficulties" in result["response"]
        assert result["session_id"] == "test_session"
    
    async def test_chat_exception_handling(self):
        """Test chat exception handling"""
        service = ChatbotService()
        
        # Force an exception by not mocking groq_service properly
        result = await service.chat("test_session", "Test message")
        
        assert result.get("error") == True
        assert "technical difficulties" in result["response"]
    
    def test_get_fallback_response_what_is_query(self):
        """Test fallback response for 'what is' queries"""
        service = ChatbotService()
        
        response = service._get_fallback_response("What is machine learning?")
        
        assert "explain" in response.lower()
        assert "technical difficulties" in response
    
    def test_get_fallback_response_how_to_query(self):
        """Test fallback response for 'how to' queries"""
        service = ChatbotService()
        
        response = service._get_fallback_response("How to learn Python programming?")
        
        assert "steps" in response.lower() or "process" in response.lower()
        assert "connectivity issues" in response
    
    def test_get_fallback_response_summary_query(self):
        """Test fallback response for summary requests"""
        service = ChatbotService()
        
        response = service._get_fallback_response("Can you summarize this topic?")
        
        assert "summary" in response.lower()
        assert "main points" in response
    
    def test_get_fallback_response_help_query(self):
        """Test fallback response for help requests"""
        service = ChatbotService()
        
        response = service._get_fallback_response("I'm stuck and need help")
        
        assert "help" in response.lower()
        assert "strategies" in response
    
    def test_get_fallback_response_generic(self):
        """Test fallback response for generic queries"""
        service = ChatbotService()
        
        response = service._get_fallback_response("Random question about something")
        
        assert "technical difficulties" in response
        assert "EduForge AI" in response
    
    @patch('services.chatbot_service.ChatbotService.chat')
    async def test_summarize_topic_brief(self, mock_chat):
        """Test topic summarization with brief detail level"""
        mock_chat.return_value = {
            "response": "Brief summary of the topic",
            "session_id": "test",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        service = ChatbotService()
        
        result = await service.summarize_topic("test_session", "Artificial Intelligence", "brief")
        
        mock_chat.assert_called_once()
        args = mock_chat.call_args[0]
        assert "brief" in args[1].lower()
        assert "2-3 sentence" in args[1]
    
    @patch('services.chatbot_service.ChatbotService.chat')
    async def test_summarize_topic_detailed(self, mock_chat):
        """Test topic summarization with detailed level"""
        mock_chat.return_value = {
            "response": "Detailed summary with examples",
            "session_id": "test",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        service = ChatbotService()
        
        result = await service.summarize_topic("test_session", "Machine Learning", "detailed")
        
        args = mock_chat.call_args[0]
        assert "detailed" in args[1].lower() or "in-depth" in args[1]
        assert "multiple paragraphs" in args[1]
    
    @patch('services.chatbot_service.ChatbotService.chat')
    async def test_get_study_tips_with_style(self, mock_chat):
        """Test getting study tips with learning style"""
        mock_chat.return_value = {
            "response": "Visual learning study tips",
            "session_id": "test",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        service = ChatbotService()
        
        result = await service.get_study_tips("test_session", "Chemistry", "visual")
        
        args = mock_chat.call_args[0]
        assert "Chemistry" in args[1]
        assert "visual learner" in args[1]
        assert "study tips" in args[1]
    
    @patch('services.chatbot_service.ChatbotService.chat')
    async def test_get_study_tips_without_style(self, mock_chat):
        """Test getting study tips without specified learning style"""
        mock_chat.return_value = {
            "response": "General study tips",
            "session_id": "test",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        service = ChatbotService()
        
        result = await service.get_study_tips("test_session", "History", None)
        
        args = mock_chat.call_args[0]
        assert "History" in args[1]
        assert "visual learner" not in args[1]  # Should not include learning style
    
    def test_get_conversation_history_existing(self):
        """Test getting conversation history for existing session"""
        service = ChatbotService()
        
        # Create conversation with messages
        conversation = service._get_or_create_conversation("test_session")
        conversation["messages"] = [
            {"role": "user", "content": "Hello", "timestamp": "2023-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi!", "timestamp": "2023-01-01T00:00:01"}
        ]
        
        history = service.get_conversation_history("test_session")
        
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
    
    def test_get_conversation_history_nonexistent(self):
        """Test getting conversation history for non-existent session"""
        service = ChatbotService()
        
        history = service.get_conversation_history("nonexistent_session")
        
        assert history == []
    
    def test_clear_conversation_existing(self):
        """Test clearing existing conversation"""
        service = ChatbotService()
        
        # Create conversation
        service._get_or_create_conversation("test_session")
        assert "test_session" in service.conversations
        
        result = service.clear_conversation("test_session")
        
        assert result == True
        assert "test_session" not in service.conversations
    
    def test_clear_conversation_nonexistent(self):
        """Test clearing non-existent conversation"""
        service = ChatbotService()
        
        result = service.clear_conversation("nonexistent_session")
        
        assert result == False
    
    def test_update_learning_context(self):
        """Test updating learning context for a session"""
        service = ChatbotService()
        
        objectives = ["Learn basics", "Practice skills", "Apply knowledge"]
        
        service.update_learning_context(
            "test_session",
            "Data Science",
            "auditory", 
            "intermediate",
            objectives
        )
        
        conversation = service.conversations["test_session"]
        context = conversation["context"]
        
        assert context["current_topic"] == "Data Science"
        assert context["learning_style"] == "auditory"
        assert context["learner_level"] == "intermediate"
        assert context["recent_objectives"] == objectives
        assert "updated_at" in context
    
    def test_update_learning_context_without_objectives(self):
        """Test updating learning context without objectives"""
        service = ChatbotService()
        
        service.update_learning_context(
            "test_session",
            "Mathematics",
            "reading",
            "advanced"
        )
        
        context = service.conversations["test_session"]["context"]
        
        assert context["current_topic"] == "Mathematics"
        assert "recent_objectives" not in context
    
    def test_get_active_sessions(self):
        """Test getting active session IDs"""
        service = ChatbotService()
        
        # Create multiple sessions
        service._get_or_create_conversation("session1")
        service._get_or_create_conversation("session2")
        service._get_or_create_conversation("session3")
        
        # Create one old session that should be cleaned up
        old_time = datetime.utcnow() - timedelta(hours=3)
        service.conversations["old_session"] = {
            "created_at": old_time,
            "messages": [],
            "context": {},
            "user_preferences": {}
        }
        
        active_sessions = service.get_active_sessions()
        
        assert len(active_sessions) == 3
        assert "session1" in active_sessions
        assert "session2" in active_sessions
        assert "session3" in active_sessions
        assert "old_session" not in active_sessions
    
    def test_get_session_stats_empty(self):
        """Test getting session statistics when no sessions exist"""
        service = ChatbotService()
        
        stats = service.get_session_stats()
        
        assert stats["active_sessions"] == 0
        assert stats["total_messages"] == 0
        assert stats["average_messages_per_session"] == 0
    
    def test_get_session_stats_with_data(self):
        """Test getting session statistics with active sessions"""
        service = ChatbotService()
        
        # Create sessions with different message counts
        conv1 = service._get_or_create_conversation("session1")
        conv1["messages"] = [{"role": "user", "content": "msg1"}] * 3
        
        conv2 = service._get_or_create_conversation("session2")
        conv2["messages"] = [{"role": "user", "content": "msg2"}] * 7
        
        stats = service.get_session_stats()
        
        assert stats["active_sessions"] == 2
        assert stats["total_messages"] == 10
        assert stats["average_messages_per_session"] == 5.0
    
    def test_conversation_message_limit(self):
        """Test that conversation history is limited in API calls"""
        service = ChatbotService()
        
        # Create conversation with many messages
        conversation = service._get_or_create_conversation("test_session")
        conversation["messages"] = [
            {"role": "user", "content": f"Message {i}", "timestamp": f"2023-01-01T00:00:{i:02d}"}
            for i in range(15)
        ]
        
        # Test that build_system_prompt works with long conversation
        prompt = service._build_system_prompt(conversation)
        
        # Should include conversation summary for long conversations
        assert "Conversation Summary" in prompt
    
    @patch('services.chatbot_service.groq_service')
    async def test_chat_conversation_history_limit(self, mock_groq):
        """Test that only recent messages are sent to Groq API"""
        mock_groq._make_request.return_value = "Response"
        
        service = ChatbotService()
        
        # Pre-populate with many messages
        conversation = service._get_or_create_conversation("test_session")
        conversation["messages"] = [
            {"role": "user", "content": f"Old message {i}", "timestamp": f"2023-01-01T00:00:{i:02d}"}
            for i in range(12)
        ]
        
        await service.chat("test_session", "New message")
        
        # Check that _make_request was called with limited message history
        call_args = mock_groq._make_request.call_args
        messages = call_args[1]["messages"]
        
        # Should have system prompt + last 10 messages + new message
        # (The limit is applied to conversation history, new message gets added)
        assert len(messages) <= 12  # system + 10 old + new user message