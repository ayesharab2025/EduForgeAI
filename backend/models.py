# Pydantic models for EduForge AI
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Request models
class ContentRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200, description="Learning topic")
    learner_level: str = Field(..., description="Learning level: beginner, intermediate, advanced")
    learning_style: str = Field(..., description="Learning style: visual, auditory, reading, kinesthetic")

class VideoRequest(BaseModel):
    content_id: str = Field(..., description="Educational content ID")

class ChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str = Field(..., min_length=1, max_length=1000)
    context: Optional[Dict[str, Any]] = None

class SummarizeRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = Field(..., min_length=1, max_length=200)
    detail_level: str = Field(default="medium", description="brief, medium, or detailed")

class StudyTipsRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = Field(..., min_length=1, max_length=200)
    learning_style: Optional[str] = None

# Response models
class QuizQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    options: List[str]
    correct_answer: int
    explanation: str
    hint: str

class Flashcard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    front: str
    back: str

class UIsuggestions(BaseModel):
    color_scheme: str
    layout_emphasis: str
    interaction_type: str

class EducationalContent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    learner_level: str
    learning_style: str
    learning_objectives: List[str]
    video_script: str
    quiz: List[QuizQuestion]
    flashcards: List[Flashcard]
    ui_suggestions: UIsuggestions
    created_at: datetime = Field(default_factory=datetime.utcnow)
    video_path: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    error: Optional[bool] = False

class ApiKeyStatus(BaseModel):
    current_key_index: int
    request_count: int
    total_keys: int
    max_requests_per_key: int

class HealthResponse(BaseModel):
    status: str
    groq_configured: bool
    api_key_status: ApiKeyStatus
    opensora_available: bool
    active_chat_sessions: int

class VideoGenerationStatus(BaseModel):
    status: str
    message: str
    estimated_time: Optional[str] = None
    progress_percentage: Optional[int] = None

# Legacy models for compatibility
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str