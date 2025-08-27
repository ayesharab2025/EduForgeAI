# Test Groq API service
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.groq_service import GroqAPIService

@pytest.mark.asyncio
class TestGroqAPIService:
    """Test Groq API service functionality"""
    
    def test_initialization(self):
        """Test service initialization"""
        service = GroqAPIService()
        assert len(service.api_keys) == 4
        assert service.current_key_index == 0
        assert service.request_count == 0
        assert service.max_requests_per_key == 20
    
    def test_rotate_api_key(self):
        """Test API key rotation"""
        service = GroqAPIService()
        original_key_index = service.current_key_index
        
        service._rotate_api_key()
        
        assert service.current_key_index == (original_key_index + 1) % len(service.api_keys)
        assert service.request_count == 0
    
    def test_rotate_api_key_wraparound(self):
        """Test API key rotation wrap around"""
        service = GroqAPIService()
        service.current_key_index = len(service.api_keys) - 1
        
        service._rotate_api_key()
        
        assert service.current_key_index == 0
    
    @patch('services.groq_service.Groq')
    async def test_make_request_success(self, mock_groq_class):
        """Test successful API request"""
        # Mock Groq client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client
        
        service = GroqAPIService()
        
        messages = [{"role": "user", "content": "Test message"}]
        response = await service._make_request(messages)
        
        assert response == "Test response"
        assert service.request_count == 1
    
    @patch('services.groq_service.Groq')
    async def test_make_request_quota_error_rotation(self, mock_groq_class):
        """Test API key rotation on quota error"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = [
            Exception("quota exceeded"),
            Mock(choices=[Mock(message=Mock(content="Success after rotation"))])
        ]
        mock_groq_class.return_value = mock_client
        
        service = GroqAPIService()
        original_key_index = service.current_key_index
        
        messages = [{"role": "user", "content": "Test message"}]
        response = await service._make_request(messages)
        
        assert response == "Success after rotation"
        assert service.current_key_index != original_key_index
    
    @patch('services.groq_service.Groq')
    async def test_make_request_max_rotation(self, mock_groq_class):
        """Test API request fails after all keys exhausted"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("persistent error")
        mock_groq_class.return_value = mock_client
        
        service = GroqAPIService()
        
        messages = [{"role": "user", "content": "Test message"}]
        
        with pytest.raises(Exception):
            await service._make_request(messages)
    
    @patch('services.groq_service.GroqAPIService._make_request')
    async def test_generate_educational_content_success(self, mock_request):
        """Test successful educational content generation"""
        mock_request.return_value = '''
        {
            "learning_objectives": ["Objective 1", "Objective 2"],
            "video_script": "Test video script",
            "quiz": [{"question": "Test?", "options": ["A", "B"], "correct_answer": 0, "explanation": "Test", "hint": "Hint"}],
            "flashcards": [{"front": "Front", "back": "Back"}],
            "ui_suggestions": {"color_scheme": "Blue", "layout_emphasis": "Visual", "interaction_type": "Interactive"}
        }
        '''
        
        service = GroqAPIService()
        
        result = await service.generate_educational_content("Python", "beginner", "visual")
        
        assert "learning_objectives" in result
        assert "video_script" in result
        assert "quiz" in result
        assert "flashcards" in result
        assert "ui_suggestions" in result
        assert len(result["learning_objectives"]) == 2
    
    @patch('services.groq_service.GroqAPIService._make_request')
    async def test_generate_educational_content_json_with_markdown(self, mock_request):
        """Test content generation with markdown-wrapped JSON"""
        mock_request.return_value = '''
        Here is the educational content:
        ```json
        {
            "learning_objectives": ["Clean objective"],
            "video_script": "Clean script",
            "quiz": [],
            "flashcards": [],
            "ui_suggestions": {"color_scheme": "Test", "layout_emphasis": "Test", "interaction_type": "Test"}
        }
        ```
        '''
        
        service = GroqAPIService()
        
        result = await service.generate_educational_content("Test", "beginner", "visual")
        
        assert result["learning_objectives"] == ["Clean objective"]
        assert result["video_script"] == "Clean script"
    
    @patch('services.groq_service.GroqAPIService._make_request')
    async def test_generate_educational_content_invalid_json(self, mock_request):
        """Test content generation with invalid JSON - should return fallback"""
        mock_request.return_value = "Invalid JSON response"
        
        service = GroqAPIService()
        
        result = await service.generate_educational_content("Test", "beginner", "visual")
        
        # Should return fallback content
        assert "learning_objectives" in result
        assert "Test" in result["learning_objectives"][0]
    
    async def test_parse_educational_content_clean_json(self):
        """Test parsing clean JSON content"""
        service = GroqAPIService()
        
        content = '{"test": "value", "number": 123}'
        result = service._parse_educational_content(content)
        
        assert result["test"] == "value"
        assert result["number"] == 123
    
    async def test_parse_educational_content_with_prefix(self):
        """Test parsing JSON with text prefix"""
        service = GroqAPIService()
        
        content = 'Here is the content: {"test": "value"}'
        result = service._parse_educational_content(content)
        
        assert result["test"] == "value"
    
    async def test_parse_educational_content_no_json(self):
        """Test parsing content with no JSON - should raise error"""
        service = GroqAPIService()
        
        content = 'No JSON here at all'
        
        with pytest.raises(ValueError):
            service._parse_educational_content(content)
    
    def test_get_fallback_content(self):
        """Test fallback content generation"""
        service = GroqAPIService()
        
        result = service._get_fallback_content("Test Topic", "intermediate", "kinesthetic")
        
        assert "learning_objectives" in result
        assert "video_script" in result
        assert "quiz" in result
        assert "flashcards" in result
        assert "ui_suggestions" in result
        
        # Check that topic is included in content
        assert "Test Topic" in result["learning_objectives"][0]
        assert "kinesthetic" in result["video_script"]
        assert "intermediate" in result["quiz"][0]["explanation"] or "Test Topic" in result["quiz"][0]["question"]
    
    def test_learning_style_configuration(self):
        """Test that different learning styles produce different fallback content"""
        service = GroqAPIService()
        
        visual_content = service._get_fallback_content("Test", "beginner", "visual")
        auditory_content = service._get_fallback_content("Test", "beginner", "auditory") 
        
        # The video scripts should be different based on learning style
        assert visual_content["video_script"] != auditory_content["video_script"]
    
    @patch('services.groq_service.GroqAPIService._make_request')
    async def test_generate_educational_content_exception_handling(self, mock_request):
        """Test exception handling in content generation"""
        mock_request.side_effect = Exception("API Error")
        
        service = GroqAPIService()
        
        # Should return fallback content instead of raising
        result = await service.generate_educational_content("Test", "beginner", "visual")
        
        assert "learning_objectives" in result
        assert isinstance(result["learning_objectives"], list)