from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import json
import tempfile
import asyncio
from groq import Groq
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import io
import base64


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Groq client
groq_client = Groq(api_key=os.environ['GROQ_API_KEY'])

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class ContentRequest(BaseModel):
    topic: str
    learner_level: str  # beginner, intermediate, advanced
    learning_style: str  # visual, auditory, kinesthetic, reading

class QuizQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    options: List[str]
    correct_answer: int
    explanation: str

class Flashcard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    front: str
    back: str

class EducationalContent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    learner_level: str
    learning_style: str
    learning_objectives: List[str]
    video_script: str
    quiz: List[QuizQuestion]
    flashcards: List[Flashcard]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VideoRequest(BaseModel):
    content_id: str

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str


def create_slide_image(text: str, slide_number: int, total_slides: int, width: int = 1280, height: int = 720) -> str:
    """Create a slide image with text"""
    # Create image with gradient background
    img = Image.new('RGB', (width, height), color=(45, 55, 72))
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect
    for i in range(height):
        r = int(45 + (70 - 45) * i / height)
        g = int(55 + (90 - 55) * i / height) 
        b = int(72 + (120 - 72) * i / height)
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    
    # Add text
    try:
        font_size = 48
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Word wrap text
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] < width - 100:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw text lines
    y_offset = height // 2 - (len(lines) * 60) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y_offset), line, fill=(255, 255, 255), font=font)
        y_offset += 60
    
    # Add slide number
    slide_text = f"{slide_number}/{total_slides}"
    draw.text((width - 150, height - 50), slide_text, fill=(200, 200, 200), font=font)
    
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp_file.name)
    return temp_file.name


async def generate_content_with_groq(topic: str, learner_level: str, learning_style: str) -> dict:
    """Generate educational content using Groq"""
    
    system_prompt = f"""You are an expert educational content creator. Generate comprehensive learning content based on the given parameters.

Topic: {topic}
Learner Level: {learner_level}
Learning Style: {learning_style}

Generate a JSON response with the following structure:
{{
  "learning_objectives": [list of 3-5 clear learning objectives],
  "video_script": "A detailed script for a 2-3 minute educational video. Include narration that explains the topic clearly with examples. Make it engaging and appropriate for {learner_level} level.",
  "quiz": [
    {{
      "question": "Multiple choice question text",
      "options": ["option1", "option2", "option3", "option4"],
      "correct_answer": 0,
      "explanation": "Explanation of why this is correct"
    }}
  ],
  "flashcards": [
    {{
      "front": "Question or term",
      "back": "Answer or definition"
    }}
  ]
}}

Generate 5 quiz questions and 8 flashcards. Ensure content is appropriate for {learner_level} learners and optimized for {learning_style} learning style."""

    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate educational content for: {topic}"}
            ],
            model="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=4000
        )
        
        content_text = response.choices[0].message.content
        
        # Parse JSON from response
        start_idx = content_text.find('{')
        end_idx = content_text.rfind('}') + 1
        json_str = content_text[start_idx:end_idx]
        
        return json.loads(json_str)
    
    except Exception as e:
        logging.error(f"Error generating content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")


async def create_video_from_script(script: str, content_id: str) -> str:
    """Create video from script using TTS and simple slides"""
    try:
        # Create TTS audio
        tts = gTTS(text=script, lang='en', slow=False)
        audio_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tts.save(audio_file.name)
        
        # Split script into segments for slides
        sentences = script.split('. ')
        slides = []
        
        # Create slide images
        for i, sentence in enumerate(sentences[:6]):  # Limit to 6 slides
            if sentence.strip():
                slide_path = create_slide_image(sentence.strip() + '.', i + 1, len(sentences[:6]))
                slides.append(slide_path)
        
        if not slides:
            # Create a single slide with the full script
            slide_path = create_slide_image(script[:200] + "...", 1, 1)
            slides.append(slide_path)
        
        # Load audio clip
        audio_clip = AudioFileClip(audio_file.name)
        duration_per_slide = audio_clip.duration / len(slides)
        
        # Create video clips from slides
        video_clips = []
        for slide_path in slides:
            img_clip = ImageClip(slide_path, duration=duration_per_slide)
            video_clips.append(img_clip)
        
        # Concatenate video clips
        final_video = concatenate_videoclips(video_clips)
        final_video = final_video.set_audio(audio_clip)
        
        # Save video
        video_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        final_video.write_videofile(
            video_file.name,
            fps=24,
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        
        # Cleanup
        os.unlink(audio_file.name)
        for slide_path in slides:
            try:
                os.unlink(slide_path)
            except:
                pass
        
        return video_file.name
        
    except Exception as e:
        logging.error(f"Error creating video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create video: {str(e)}")


# Routes
@api_router.get("/")
async def root():
    return {"message": "Educational Content Generator API"}

@api_router.post("/generate_content", response_model=EducationalContent)
async def generate_content(request: ContentRequest):
    """Generate educational content based on topic, level, and learning style"""
    try:
        # Generate content using Groq
        content_data = await generate_content_with_groq(
            request.topic, 
            request.learner_level, 
            request.learning_style
        )
        
        # Create quiz questions
        quiz_questions = []
        for q_data in content_data.get('quiz', []):
            quiz_questions.append(QuizQuestion(
                question=q_data['question'],
                options=q_data['options'],
                correct_answer=q_data['correct_answer'],
                explanation=q_data['explanation']
            ))
        
        # Create flashcards
        flashcards = []
        for f_data in content_data.get('flashcards', []):
            flashcards.append(Flashcard(
                front=f_data['front'],
                back=f_data['back']
            ))
        
        # Create educational content object
        content = EducationalContent(
            topic=request.topic,
            learner_level=request.learner_level,
            learning_style=request.learning_style,
            learning_objectives=content_data.get('learning_objectives', []),
            video_script=content_data.get('video_script', ''),
            quiz=quiz_questions,
            flashcards=flashcards
        )
        
        # Save to database
        content_dict = content.dict()
        await db.educational_content.insert_one(content_dict)
        
        return content
        
    except Exception as e:
        logging.error(f"Error in generate_content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/generate_video")
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Generate video for the given content"""
    try:
        # Get content from database
        content = await db.educational_content.find_one({"id": request.content_id})
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        script = content.get('video_script', '')
        if not script:
            raise HTTPException(status_code=400, detail="No video script found")
        
        # Create video
        video_path = await create_video_from_script(script, request.content_id)
        
        # Store video path in database
        await db.educational_content.update_one(
            {"id": request.content_id},
            {"$set": {"video_path": video_path}}
        )
        
        # Schedule cleanup after 1 hour
        background_tasks.add_task(cleanup_video_file, video_path, 3600)
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=f"educational_video_{request.content_id}.mp4"
        )
        
    except Exception as e:
        logging.error(f"Error in generate_video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/content/{content_id}", response_model=EducationalContent)
async def get_content(content_id: str):
    """Get educational content by ID"""
    content = await db.educational_content.find_one({"id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return EducationalContent(**content)

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "groq_configured": bool(os.environ.get('GROQ_API_KEY'))}

async def cleanup_video_file(file_path: str, delay: int):
    """Clean up video file after delay"""
    await asyncio.sleep(delay)
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logging.error(f"Failed to cleanup video file {file_path}: {e}")

# Legacy routes
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()