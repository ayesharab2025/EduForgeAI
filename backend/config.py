# Configuration settings for EduForge AI
import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "eduforge_db")
    
    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    
    # Groq API Keys with rotation
    GROQ_API_KEYS: List[str] = [
        "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",
        "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", 
        "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",
        "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"
    ]
    
    # API Key rotation settings
    MAX_REQUESTS_PER_KEY: int = 20
    
    # Video generation
    VIDEO_OUTPUT_DIR: str = "/tmp/eduforge_videos"
    OPENSORA_MODEL_PATH: str = "/app/Open-Sora"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env

settings = Settings()

# Learning style configurations
LEARNING_STYLES = {
    "visual": {
        "content_emphasis": "diagrams, infographics, visual scenes, charts, mind maps",
        "video_style": "rich visual content with diagrams and animations",
        "quiz_style": "visual-based questions with image descriptions",
        "prompt_suffix": "Focus on visual elements, diagrams, and scene descriptions. Use visual metaphors and spatial relationships."
    },
    "auditory": {
        "content_emphasis": "narration, dialogues, discussions, audio explanations",
        "video_style": "podcast-style with detailed audio explanations and dialogues",
        "quiz_style": "listening-based and discussion questions", 
        "prompt_suffix": "Emphasize audio content, conversations, and verbal explanations. Use dialogue format and discussion-based learning."
    },
    "reading": {
        "content_emphasis": "detailed text notes, structured outlines, written summaries",
        "video_style": "text-heavy slides with detailed written content",
        "quiz_style": "reading comprehension and written analysis questions",
        "prompt_suffix": "Focus on detailed written content, structured text, and comprehensive reading materials. Use bullet points and organized text."
    },
    "kinesthetic": {
        "content_emphasis": "hands-on activities, simulations, interactive experiments",
        "video_style": "demonstration-focused with step-by-step practical examples",
        "quiz_style": "interactive and simulation-based questions with practical scenarios",
        "prompt_suffix": "Emphasize hands-on learning, practical examples, and interactive elements. Include 'try-it-yourself' activities and real-world applications."
    },
    "comprehensive": {
        "content_emphasis": "multi-modal content combining visual, auditory, and practical elements",
        "video_style": "balanced approach with visuals, clear narration, and practical examples",
        "quiz_style": "diverse question types covering multiple learning approaches",
        "prompt_suffix": "Create comprehensive content that appeals to all learning styles. Include visual elements, clear explanations, practical examples, and interactive components."
    }
}