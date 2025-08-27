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
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
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
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=4000
        )
        
        content_text = response.choices[0].message.content
        
        # Clean the content text to remove control characters
        import re
        content_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content_text)
        
        # Find JSON in the response - look for the first complete JSON object
        try:
            # Try to find JSON block
            start_idx = content_text.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found in response")
            
            # Find the matching closing brace
            brace_count = 0
            end_idx = start_idx
            for i, char in enumerate(content_text[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            json_str = content_text[start_idx:end_idx]
            return json.loads(json_str)
            
        except (json.JSONDecodeError, ValueError) as e:
            # If JSON parsing fails, log the content and try a fallback
            logging.error(f"JSON parsing failed: {e}")
            logging.error(f"Content received: {content_text[:1000]}...")
            
            # Fallback: create a basic structure
            return {
                "learning_objectives": ["Understand the basics of the topic", "Apply key concepts", "Practice problem-solving"],
                "video_script": "This is an educational video about the requested topic. The content will cover the fundamental concepts and provide practical examples.",
                "quiz": [
                    {
                        "question": "What is the main concept discussed?",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": 0,
                        "explanation": "This is the correct answer because..."
                    }
                ],
                "flashcards": [
                    {
                        "front": "Key Term",
                        "back": "Definition of the key term"
                    }
                ]
            }
    
    except Exception as e:
        logging.error(f"Error generating content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")


async def create_enhanced_video_from_script(script: str, topic: str, content_id: str) -> str:
    """Create enhanced AI-powered video from script using TTS and AI-generated visuals"""
    try:
        # Create TTS audio with better quality
        tts = gTTS(text=script, lang='en', slow=False, tld='com')
        audio_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tts.save(audio_file.name)
        
        # Generate AI-enhanced content for visuals using Groq
        visual_prompt = f"""Generate detailed visual descriptions for an educational video about {topic}. 
        Create 4-6 scene descriptions that would make engaging slides. Each description should be visual, specific, and educational.
        
        Script: {script[:500]}...
        
        Return only a JSON array of visual descriptions:
        ["Scene 1 description", "Scene 2 description", ...]
        """
        
        try:
            visual_response = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a visual content creator for educational videos. Generate engaging scene descriptions."},
                    {"role": "user", "content": visual_prompt}
                ],
                model="llama3-8b-8192",
                temperature=0.8,
                max_tokens=1000
            )
            
            visual_content = visual_response.choices[0].message.content
            # Extract JSON array
            start_idx = visual_content.find('[')
            end_idx = visual_content.rfind(']') + 1
            if start_idx != -1 and end_idx != -1:
                visual_descriptions = json.loads(visual_content[start_idx:end_idx])
            else:
                # Fallback to script-based slides
                visual_descriptions = [f"Educational content about {topic}" for _ in range(4)]
                
        except Exception as e:
            logging.warning(f"Failed to generate visual descriptions: {e}")
            visual_descriptions = [f"Educational content about {topic}" for _ in range(4)]
        
        # Create enhanced slide images with animations
        slides = []
        for i, description in enumerate(visual_descriptions[:6]):
            slide_path = create_enhanced_slide_image(
                description, 
                topic,
                i + 1, 
                len(visual_descriptions[:6])
            )
            slides.append(slide_path)
        
        if not slides:
            # Fallback slide
            slide_path = create_enhanced_slide_image(f"Learning about {topic}", topic, 1, 1)
            slides.append(slide_path)
        
        # Load audio clip
        audio_clip = AudioFileClip(audio_file.name)
        duration_per_slide = audio_clip.duration / len(slides)
        
        # Create video clips with transitions and effects
        video_clips = []
        for i, slide_path in enumerate(slides):
            # Create image clip with Ken Burns effect (zoom + pan)
            img_clip = ImageClip(slide_path, duration=duration_per_slide)
            
            # Add Ken Burns effect (slight zoom and pan)
            if i % 2 == 0:
                # Zoom in effect
                img_clip = img_clip.resize(lambda t: 1 + 0.02 * t)  # Gradual zoom
            else:
                # Zoom out effect  
                img_clip = img_clip.resize(lambda t: 1.02 - 0.02 * t)  # Gradual zoom out
            
            # Add fade transitions
            if i > 0:
                img_clip = img_clip.fadein(0.5)
            if i < len(slides) - 1:
                img_clip = img_clip.fadeout(0.5)
                
            video_clips.append(img_clip)
        
        # Concatenate video clips with crossfade transitions
        if len(video_clips) > 1:
            final_video = video_clips[0]
            for clip in video_clips[1:]:
                final_video = final_video.crossfadeout(0.5).crossfadein(0.5, clip)
        else:
            final_video = video_clips[0]
            
        # Add audio
        final_video = final_video.with_audio(audio_clip)
        
        # Save video with better quality settings
        video_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        final_video.write_videofile(
            video_file.name,
            fps=30,  # Higher FPS for smoother video
            audio_codec='aac',
            video_codec='libx264',
            logger=None,
            temp_audiofile_path=tempfile.mkdtemp(),
            remove_temp=True
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
        logging.error(f"Error creating enhanced video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create video: {str(e)}")


def create_enhanced_slide_image(description: str, topic: str, slide_number: int, total_slides: int, width: int = 1920, height: int = 1080) -> str:
    """Create enhanced slide image with better design and AI-generated content"""
    # Create image with sophisticated gradient background
    img = Image.new('RGB', (width, height), color=(15, 23, 42))  # Dark slate background
    draw = ImageDraw.Draw(img)
    
    # Create multi-layer gradient background
    for i in range(height):
        # Base gradient
        r = int(15 + (45 - 15) * i / height)
        g = int(23 + (55 - 23) * i / height) 
        b = int(42 + (82 - 42) * i / height)
        
        # Add some color variation based on topic
        topic_lower = topic.lower()
        if 'science' in topic_lower or 'physics' in topic_lower:
            g = min(255, g + 20)  # More green for science
        elif 'math' in topic_lower or 'programming' in topic_lower:
            b = min(255, b + 30)  # More blue for tech
        elif 'history' in topic_lower or 'literature' in topic_lower:
            r = min(255, r + 25)  # More red for humanities
            
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    
    # Add decorative elements
    # Top accent bar
    accent_color = (99, 102, 241)  # Indigo accent
    draw.rectangle([(0, 0), (width, 8)], fill=accent_color)
    
    # Side accent
    draw.rectangle([(0, 0), (12, height)], fill=accent_color)
    
    # Load fonts with fallbacks
    title_font_size = 72
    text_font_size = 36
    small_font_size = 28
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", title_font_size)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", text_font_size)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", small_font_size)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw topic title at top
    topic_text = topic.upper()
    topic_bbox = draw.textbbox((0, 0), topic_text, font=title_font)
    topic_width = topic_bbox[2] - topic_bbox[0]
    topic_x = (width - topic_width) // 2
    
    # Add shadow effect for title
    draw.text((topic_x + 2, 82), topic_text, fill=(0, 0, 0, 100), font=title_font)  # Shadow
    draw.text((topic_x, 80), topic_text, fill=(255, 255, 255), font=title_font)  # Main text
    
    # Draw main description with better formatting
    words = description.split()
    lines = []
    current_line = []
    max_width = width - 200  # Margins
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=text_font)
        if bbox[2] - bbox[0] < max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Position main text in center
    total_text_height = len(lines) * 50
    start_y = (height - total_text_height) // 2 + 50
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=text_font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        y = start_y + i * 50
        
        # Add subtle shadow
        draw.text((x + 1, y + 1), line, fill=(0, 0, 0, 80), font=text_font)
        draw.text((x, y), line, fill=(255, 255, 255), font=text_font)
    
    # Add slide counter with better styling
    counter_text = f"{slide_number} / {total_slides}"
    counter_bbox = draw.textbbox((0, 0), counter_text, font=small_font)
    counter_width = counter_bbox[2] - counter_bbox[0]
    
    # Counter background
    counter_bg_x1 = width - counter_width - 60
    counter_bg_y1 = height - 80
    counter_bg_x2 = width - 20
    counter_bg_y2 = height - 20
    draw.rounded_rectangle(
        [(counter_bg_x1, counter_bg_y1), (counter_bg_x2, counter_bg_y2)], 
        radius=15, 
        fill=(0, 0, 0, 100)
    )
    
    counter_x = width - counter_width - 40
    counter_y = height - 60
    draw.text((counter_x, counter_y), counter_text, fill=(200, 200, 200), font=small_font)
    
    # Add subtle branding
    brand_text = "EduForge AI"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=small_font)
    brand_x = 40
    brand_y = height - 60
    draw.text((brand_x, brand_y), brand_text, fill=(150, 150, 150), font=small_font)
    
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp_file.name, optimize=True, quality=95)
    return temp_file.name


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
        
        topic = content.get('topic', 'Educational Content')
        
        # Create video
        video_path = await create_enhanced_video_from_script(script, topic, request.content_id)
        
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