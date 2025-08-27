# Pytest configuration and fixtures
import pytest
import asyncio
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from unittest.mock import AsyncMock, MagicMock
import tempfile
import os

# Import the app
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from server import app
from config import settings
from services.groq_service import GroqAPIService
from services.video_service import VideoGenerationService
from services.chatbot_service import ChatbotService

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def test_db():
    """Create test database connection"""
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client["test_eduforge_db"]
    yield db
    # Cleanup
    await client.drop_database("test_eduforge_db")
    client.close()

@pytest.fixture
def mock_groq_service():
    """Mock Groq API service"""
    service = MagicMock(spec=GroqAPIService)
    service.api_keys = ["test_key_1", "test_key_2"]
    service.current_key_index = 0
    service.request_count = 0
    service.max_requests_per_key = 20
    
    # Mock the generate_educational_content method
    service.generate_educational_content = AsyncMock(return_value={
        "learning_objectives": [
            "Understand the fundamental concepts",
            "Apply key principles",
            "Analyze real-world applications",
            "Evaluate different approaches",
            "Create innovative solutions"
        ],
        "video_script": "[SCENE: Introduction] Welcome to this lesson! [SCENE: Main content] Let's explore the key concepts. [SCENE: Conclusion] Summary and next steps.",
        "quiz": [
            {
                "question": "What is the main concept?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": 0,
                "explanation": "This is the correct explanation",
                "hint": "Think about the main idea"
            }
        ],
        "flashcards": [
            {
                "front": "Key term",
                "back": "Definition and explanation"
            }
        ],
        "ui_suggestions": {
            "color_scheme": "Blue and green for learning",
            "layout_emphasis": "Visual focus areas",
            "interaction_type": "Interactive elements"
        }
    })
    
    service._make_request = AsyncMock(return_value="Test response from Groq")
    
    return service

@pytest.fixture
def mock_video_service():
    """Mock video generation service"""
    service = MagicMock(spec=VideoGenerationService)
    
    # Create a temporary video file for testing
    temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    temp_video.write(b"fake video content")
    temp_video.close()
    
    service.generate_video = AsyncMock(return_value=temp_video.name)
    service._is_opensora_available = AsyncMock(return_value=False)
    
    return service

@pytest.fixture
def mock_chatbot_service():
    """Mock chatbot service"""
    service = MagicMock(spec=ChatbotService)
    
    service.chat = AsyncMock(return_value={
        "response": "This is a test response from the chatbot",
        "session_id": "test_session",
        "timestamp": "2023-01-01T00:00:00"
    })
    
    service.summarize_topic = AsyncMock(return_value={
        "response": "This is a test summary of the topic",
        "session_id": "test_session", 
        "timestamp": "2023-01-01T00:00:00"
    })
    
    service.get_study_tips = AsyncMock(return_value={
        "response": "Here are some effective study tips for this topic",
        "session_id": "test_session",
        "timestamp": "2023-01-01T00:00:00"
    })
    
    service.get_conversation_history = MagicMock(return_value=[
        {"role": "user", "content": "Hello", "timestamp": "2023-01-01T00:00:00"},
        {"role": "assistant", "content": "Hi there!", "timestamp": "2023-01-01T00:00:01"}
    ])
    
    service.clear_conversation = MagicMock(return_value=True)
    service.get_session_stats = MagicMock(return_value={
        "active_sessions": 1,
        "total_messages": 5,
        "average_messages_per_session": 5.0
    })
    
    service.get_active_sessions = MagicMock(return_value=["session1", "session2"])
    
    return service

@pytest.fixture
def sample_content_request():
    """Sample content request for testing"""
    return {
        "topic": "Machine Learning Basics",
        "learner_level": "beginner",
        "learning_style": "visual"
    }

@pytest.fixture
def sample_educational_content():
    """Sample educational content for testing"""
    return {
        "id": "test_content_id",
        "topic": "Machine Learning Basics",
        "learner_level": "beginner", 
        "learning_style": "visual",
        "learning_objectives": [
            "Understand ML fundamentals",
            "Identify different ML types",
            "Apply basic ML concepts"
        ],
        "video_script": "Welcome to Machine Learning! This is a comprehensive introduction...",
        "quiz": [
            {
                "id": "q1",
                "question": "What is machine learning?",
                "options": ["AI subset", "Programming language", "Database", "Operating system"],
                "correct_answer": 0,
                "explanation": "Machine learning is a subset of AI",
                "hint": "Think about artificial intelligence"
            }
        ],
        "flashcards": [
            {
                "id": "f1",
                "front": "Machine Learning",
                "back": "A method of data analysis that automates analytical model building"
            }
        ],
        "ui_suggestions": {
            "color_scheme": "Blue and green gradients",
            "layout_emphasis": "Visual learning focus",
            "interaction_type": "Interactive visual elements"
        },
        "created_at": "2023-01-01T00:00:00",
        "video_path": None
    }