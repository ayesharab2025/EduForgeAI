# EduForge AI - Enhanced FastAPI Server with Groq Integration
from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from contextlib import asynccontextmanager

# Local imports
from config import settings
from models import *
from services.groq_service import groq_service
from services.video_service import video_service
from services.chatbot_service import chatbot_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
client: AsyncIOMotorClient = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global client, db
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    # Test database connection
    try:
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
    
    # Create video output directory
    Path(settings.VIDEO_OUTPUT_DIR).mkdir(exist_ok=True)
    
    yield
    
    # Shutdown
    if client:
        client.close()

# Create FastAPI app
app = FastAPI(
    title="EduForge AI API",
    description="AI-powered educational content generation platform",
    version="2.0.0",
    lifespan=lifespan
)

# Create API router
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ORIGINS.split(',') if settings.CORS_ORIGINS != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database
async def get_database():
    return db

# Helper function to clean up video files
async def cleanup_video_file(file_path: str, delay: int):
    """Clean up video file after delay"""
    await asyncio.sleep(delay)
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up video file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to cleanup video file {file_path}: {e}")

# API Routes

@api_router.get("/")
async def root():
    """API root endpoint"""
    return {"message": "EduForge AI API v2.0 - Advanced Educational Content Generation"}

@api_router.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    
    # Check OpenSora availability
    opensora_available = await video_service._is_opensora_available()
    
    # Get API key status
    api_key_status = ApiKeyStatus(
        current_key_index=groq_service.current_key_index,
        request_count=groq_service.request_count,
        total_keys=len(groq_service.api_keys),
        max_requests_per_key=groq_service.max_requests_per_key
    )
    
    # Get chatbot stats
    chat_stats = chatbot_service.get_session_stats()
    
    return HealthResponse(
        status="healthy",
        groq_configured=len(groq_service.api_keys) > 0,
        api_key_status=api_key_status,
        opensora_available=opensora_available,
        active_chat_sessions=chat_stats['active_sessions']
    )

@api_router.post("/generate_content", response_model=EducationalContent)
async def generate_content(
    request: ContentRequest,
    db=Depends(get_database)
):
    """Generate comprehensive educational content with learning style adaptation"""
    
    try:
        logger.info(f"Generating content for topic: {request.topic}, level: {request.learner_level}, style: {request.learning_style}")
        
        # Validate learning style and level
        valid_styles = ["visual", "auditory", "reading", "kinesthetic", "comprehensive"]
        valid_levels = ["beginner", "intermediate", "advanced"]
        
        if request.learning_style.lower() not in valid_styles:
            raise HTTPException(status_code=400, detail=f"Invalid learning style. Must be one of: {valid_styles}")
        
        if request.learner_level.lower() not in valid_levels:
            raise HTTPException(status_code=400, detail=f"Invalid learner level. Must be one of: {valid_levels}")
        
        # Generate content using Groq service
        content_data = await groq_service.generate_educational_content(
            topic=request.topic,
            learner_level=request.learner_level.lower(),
            learning_style=request.learning_style.lower()
        )
        
        # Create quiz questions
        quiz_questions = []
        for q_data in content_data.get('quiz', []):
            quiz_questions.append(QuizQuestion(
                question=q_data['question'],
                options=q_data['options'],
                correct_answer=q_data['correct_answer'],
                explanation=q_data['explanation'],
                hint=q_data.get('hint', 'Think about the key concepts we discussed.')
            ))
        
        # Create flashcards
        flashcards = []
        for f_data in content_data.get('flashcards', []):
            flashcards.append(Flashcard(
                front=f_data['front'],
                back=f_data['back']
            ))
        
        # Create UI suggestions
        ui_suggestions = UIsuggestions(
            color_scheme=content_data.get('ui_suggestions', {}).get('color_scheme', 'Blue and purple gradients for focus and creativity'),
            layout_emphasis=content_data.get('ui_suggestions', {}).get('layout_emphasis', f'Optimized for {request.learning_style} learning'),
            interaction_type=content_data.get('ui_suggestions', {}).get('interaction_type', f'Interactive elements for {request.learning_style} learners')
        )
        
        # Create educational content object
        content = EducationalContent(
            topic=request.topic,
            learner_level=request.learner_level.lower(),
            learning_style=request.learning_style.lower(),
            learning_objectives=content_data.get('learning_objectives', []),
            video_script=content_data.get('video_script', ''),
            quiz=quiz_questions,
            flashcards=flashcards,
            ui_suggestions=ui_suggestions
        )
        
        # Save to database
        content_dict = content.model_dump()
        await db.educational_content.insert_one(content_dict)
        
        # Update chatbot context for this session
        # Using content ID as session ID for context continuity
        chatbot_service.update_learning_context(
            session_id=content.id,
            topic=request.topic,
            learning_style=request.learning_style.lower(),
            learner_level=request.learner_level.lower(),
            learning_objectives=content.learning_objectives
        )
        
        logger.info(f"Successfully generated content with ID: {content.id}")
        return content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")

@api_router.post("/generate_video")
async def generate_video(
    request: VideoRequest, 
    background_tasks: BackgroundTasks,
    db=Depends(get_database)
):
    """Generate AI-enhanced educational video"""
    
    try:
        logger.info(f"Starting video generation for content ID: {request.content_id}")
        
        # Get content from database
        content = await db.educational_content.find_one({"id": request.content_id})
        if not content:
            raise HTTPException(status_code=404, detail="Educational content not found")
        
        script = content.get('video_script', '')
        topic = content.get('topic', 'Educational Content')
        learning_style = content.get('learning_style', 'visual')
        
        if not script:
            raise HTTPException(status_code=400, detail="No video script found in content")
        
        # Generate video using enhanced video service
        video_path = await video_service.generate_video(
            script=script,
            topic=topic,
            learning_style=learning_style,
            content_id=request.content_id
        )
        
        # Update database with video path
        await db.educational_content.update_one(
            {"id": request.content_id},
            {"$set": {"video_path": video_path}}
        )
        
        # Schedule cleanup after 2 hours
        background_tasks.add_task(cleanup_video_file, video_path, 7200)
        
        logger.info(f"Successfully generated video: {video_path}")
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=f"eduforge_video_{request.content_id}.mp4",
            headers={"Content-Disposition": f"attachment; filename=eduforge_video_{request.content_id}.mp4"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")

@api_router.get("/content/{content_id}", response_model=EducationalContent)
async def get_content(content_id: str, db=Depends(get_database)):
    """Retrieve educational content by ID"""
    
    content = await db.educational_content.find_one({"id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Educational content not found")
    
    return EducationalContent(**content)

@api_router.get("/video_status/{content_id}")
async def get_video_status(content_id: str, db=Depends(get_database)):
    """Get video generation status"""
    
    content = await db.educational_content.find_one({"id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Educational content not found")
    
    video_path = content.get('video_path')
    
    if video_path and os.path.exists(video_path):
        return VideoGenerationStatus(
            status="completed",
            message="Video generation completed successfully",
            progress_percentage=100
        )
    else:
        return VideoGenerationStatus(
            status="processing", 
            message="Video generation in progress...",
            estimated_time="1-3 minutes",
            progress_percentage=50
        )

# Chatbot endpoints
@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """Chat with the educational AI assistant"""
    
    try:
        response = await chatbot_service.chat(
            session_id=request.session_id,
            message=request.message,
            context=request.context
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return ChatResponse(
            response="I apologize, but I'm experiencing technical difficulties. Please try again.",
            session_id=request.session_id,
            timestamp=datetime.utcnow().isoformat(),
            error=True
        )

@api_router.post("/chat/summarize", response_model=ChatResponse)
async def summarize_topic(request: SummarizeRequest):
    """Get topic summary from the AI assistant"""
    
    try:
        response = await chatbot_service.summarize_topic(
            session_id=request.session_id,
            topic=request.topic,
            detail_level=request.detail_level
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in summarize: {str(e)}")
        return ChatResponse(
            response=f"I'm having trouble generating a summary for {request.topic}. Please try again or ask me specific questions about the topic.",
            session_id=request.session_id,
            timestamp=datetime.utcnow().isoformat(),
            error=True
        )

@api_router.post("/chat/study_tips", response_model=ChatResponse)
async def get_study_tips(request: StudyTipsRequest):
    """Get personalized study tips from the AI assistant"""
    
    try:
        response = await chatbot_service.get_study_tips(
            session_id=request.session_id,
            topic=request.topic,
            learning_style=request.learning_style
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in study_tips: {str(e)}")
        return ChatResponse(
            response=f"I'm having trouble generating study tips for {request.topic}. Here's a general tip: break the topic into smaller, manageable parts and practice regularly.",
            session_id=request.session_id,
            timestamp=datetime.utcnow().isoformat(),
            error=True
        )

@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get conversation history for a session"""
    
    try:
        history = chatbot_service.get_conversation_history(session_id)
        return {"session_id": session_id, "messages": history}
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

@api_router.delete("/chat/{session_id}")
async def clear_chat_session(session_id: str):
    """Clear conversation history for a session"""
    
    try:
        success = chatbot_service.clear_conversation(session_id)
        if success:
            return {"message": f"Chat session {session_id} cleared successfully"}
        else:
            return {"message": f"Chat session {session_id} not found"}
            
    except Exception as e:
        logger.error(f"Error clearing chat session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear chat session")

# Admin endpoints
@api_router.get("/admin/chat_stats")
async def get_chat_statistics():
    """Get chatbot usage statistics"""
    
    try:
        stats = chatbot_service.get_session_stats()
        active_sessions = chatbot_service.get_active_sessions()
        
        return {
            "statistics": stats,
            "active_sessions": len(active_sessions),
            "session_ids": active_sessions[:10]  # Return first 10 for privacy
        }
        
    except Exception as e:
        logger.error(f"Error getting chat stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat statistics")

# Legacy endpoints for compatibility
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input_data: StatusCheckCreate, db=Depends(get_database)):
    """Legacy endpoint for status checks"""
    
    status_dict = input_data.model_dump()
    status_obj = StatusCheck(**status_dict)
    await db.status_checks.insert_one(status_obj.model_dump())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks(db=Depends(get_database)):
    """Legacy endpoint for status retrieval"""
    
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include router
app.include_router(api_router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {str(exc)}")
    return {"error": "Internal server error", "detail": str(exc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)