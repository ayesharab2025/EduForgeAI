# Enhanced video generation service with OpenSora integration
import os
import tempfile
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, List
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import json
from config import settings

logger = logging.getLogger(__name__)

class VideoGenerationService:
    def __init__(self):
        self.opensora_path = Path(settings.OPENSORA_MODEL_PATH)
        self.video_output_dir = Path(settings.VIDEO_OUTPUT_DIR)
        self.video_output_dir.mkdir(exist_ok=True)
        
    async def generate_video(
        self, 
        script: str, 
        topic: str, 
        learning_style: str,
        content_id: str
    ) -> str:
        """Generate AI-powered educational video"""
        try:
            # Check if OpenSora is available
            if await self._is_opensora_available():
                return await self._generate_opensora_video(script, topic, learning_style, content_id)
            else:
                return await self._generate_enhanced_slideshow_video(script, topic, learning_style, content_id)
                
        except Exception as e:
            logger.error(f"Video generation failed: {str(e)}")
            # Fallback to simple slideshow
            return await self._generate_simple_slideshow_video(script, topic, content_id)
    
    async def _is_opensora_available(self) -> bool:
        """Check if OpenSora is properly installed and configured"""
        try:
            if not self.opensora_path.exists():
                logger.info("OpenSora not found, cloning repository...")
                await self._setup_opensora()
            
            # Check if required files exist
            config_path = self.opensora_path / "configs" / "opensora-v1-2" / "inference" / "sample.py"
            return config_path.exists()
            
        except Exception as e:
            logger.warning(f"OpenSora availability check failed: {str(e)}")
            return False
    
    async def _setup_opensora(self):
        """Clone and setup OpenSora repository"""
        try:
            # Clone OpenSora repository
            clone_cmd = [
                "git", "clone", 
                "https://github.com/hpcaitech/Open-Sora.git",
                str(self.opensora_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to clone OpenSora: {stderr.decode()}")
                return False
            
            # Install dependencies
            install_cmd = [
                "pip", "install", "-e", ".",
            ]
            
            process = await asyncio.create_subprocess_exec(
                *install_cmd,
                cwd=str(self.opensora_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            logger.info("OpenSora setup completed")
            return True
            
        except Exception as e:
            logger.error(f"OpenSora setup failed: {str(e)}")
            return False
    
    async def _generate_opensora_video(
        self, 
        script: str, 
        topic: str, 
        learning_style: str,
        content_id: str
    ) -> str:
        """Generate video using OpenSora AI"""
        try:
            # Create video prompt based on script and learning style
            video_prompt = self._create_opensora_prompt(script, topic, learning_style)
            
            # Generate TTS audio first
            audio_path = await self._generate_tts_audio(script)
            
            # Generate AI video using OpenSora
            video_path = await self._run_opensora_inference(video_prompt, content_id)
            
            if video_path and os.path.exists(video_path):
                # Combine AI video with TTS audio
                final_video_path = await self._combine_video_audio(video_path, audio_path, content_id)
                return final_video_path
            else:
                # Fallback to slideshow if OpenSora fails
                return await self._generate_enhanced_slideshow_video(script, topic, learning_style, content_id)
                
        except Exception as e:
            logger.error(f"OpenSora video generation failed: {str(e)}")
            return await self._generate_enhanced_slideshow_video(script, topic, learning_style, content_id)
    
    def _create_opensora_prompt(self, script: str, topic: str, learning_style: str) -> str:
        """Create optimized prompt for OpenSora video generation"""
        
        # Extract key scenes from script
        scenes = []
        if "[SCENE:" in script:
            import re
            scene_matches = re.findall(r'\[SCENE: ([^\]]+)\]', script)
            scenes = scene_matches[:4]  # Limit to 4 scenes
        
        if not scenes:
            scenes = [f"Introduction to {topic}", f"Key concepts of {topic}", f"Applications of {topic}", f"Summary of {topic}"]
        
        # Create style-specific video prompt
        style_prompts = {
            "visual": "educational animation with clear diagrams, charts, and visual explanations",
            "auditory": "talking head style with emphasis on clear narration and minimal distractions", 
            "reading": "text-heavy slides with bullet points and structured information",
            "kinesthetic": "demonstration-style with hands-on examples and interactive elements"
        }
        
        style_instruction = style_prompts.get(learning_style, style_prompts["visual"])
        
        prompt = f"""Create an educational video about {topic} in {style_instruction} format. 
        
        The video should include these scenes:
        {' -> '.join(scenes)}
        
        Style: Professional educational content, clean design, appropriate for learning environment.
        Duration: 2-3 minutes with smooth transitions between concepts.
        Quality: High definition, stable camera, good lighting."""
        
        return prompt
    
    async def _run_opensora_inference(self, prompt: str, content_id: str) -> Optional[str]:
        """Run OpenSora inference to generate video"""
        try:
            output_path = self.video_output_dir / f"opensora_{content_id}.mp4"
            
            # Prepare OpenSora command
            inference_cmd = [
                "python", "scripts/inference.py",
                "configs/opensora-v1-2/inference/sample.py",
                "--prompt", prompt,
                "--save-dir", str(output_path.parent),
                "--num-frames", "49",  # ~2 second video at 24fps
                "--resolution", "480p",
                "--aspect-ratio", "16:9"
            ]
            
            # Run OpenSora inference
            process = await asyncio.create_subprocess_exec(
                *inference_cmd,
                cwd=str(self.opensora_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # OpenSora usually saves with a different name, find the generated file
                generated_files = list(output_path.parent.glob("*.mp4"))
                if generated_files:
                    latest_file = max(generated_files, key=os.path.getctime)
                    # Rename to our expected name
                    latest_file.rename(output_path)
                    return str(output_path)
            else:
                logger.error(f"OpenSora inference failed: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"OpenSora inference error: {str(e)}")
            return None
    
    async def _generate_tts_audio(self, script: str) -> str:
        """Generate high-quality TTS audio"""
        # Clean script - remove any remaining scene markers and format for speech
        import re
        clean_script = re.sub(r'\[SCENE: [^\]]+\]', '', script)
        clean_script = re.sub(r'\n+', ' ', clean_script).strip()
        
        # Additional formatting for better TTS
        clean_script = clean_script.replace('. ', '. ')  # Ensure proper pauses
        clean_script = re.sub(r'\s+', ' ', clean_script)  # Clean up extra spaces
        
        # Generate TTS with better pronunciation
        tts = gTTS(text=clean_script, lang='en', slow=False, tld='com')
        audio_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tts.save(audio_file.name)
        
        return audio_file.name
    
    async def _combine_video_audio(self, video_path: str, audio_path: str, content_id: str) -> str:
        """Combine AI-generated video with TTS audio using ffmpeg"""
        try:
            output_path = self.video_output_dir / f"final_{content_id}.mp4"
            
            # Use ffmpeg to combine video and audio
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-strict", "experimental",
                "-shortest",
                str(output_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            # Cleanup temporary files
            try:
                os.unlink(video_path)
                os.unlink(audio_path)
            except:
                pass
                
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Video-audio combination failed: {str(e)}")
            # Return original video if audio combination fails
            return video_path
    
    async def _generate_enhanced_slideshow_video(
        self, 
        script: str, 
        topic: str, 
        learning_style: str,
        content_id: str
    ) -> str:
        """Generate enhanced slideshow video with better visuals"""
        from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
        
        try:
            # Generate TTS audio
            audio_path = await self._generate_tts_audio(script)
            audio_clip = AudioFileClip(audio_path)
            
            # Extract scenes from script
            scenes = self._extract_scenes_from_script(script, topic)
            
            # Create enhanced slide images
            slide_paths = []
            for i, scene in enumerate(scenes[:6]):  # Limit to 6 slides
                slide_path = await self._create_enhanced_slide(
                    scene, topic, learning_style, i + 1, len(scenes[:6])
                )
                slide_paths.append(slide_path)
            
            # Calculate duration per slide
            duration_per_slide = audio_clip.duration / len(slide_paths)
            
            # Create video clips
            video_clips = []
            for i, slide_path in enumerate(slide_paths):
                img_clip = ImageClip(slide_path, duration=duration_per_slide)
                
                # Add fade transitions
                if i > 0:
                    img_clip = img_clip.fadein(0.5)
                if i < len(slide_paths) - 1:
                    img_clip = img_clip.fadeout(0.5)
                    
                video_clips.append(img_clip)
            
            # Concatenate clips
            if len(video_clips) > 1:
                final_video = concatenate_videoclips(video_clips, method="compose")
            else:
                final_video = video_clips[0]
            
            # Add audio
            final_video = final_video.with_audio(audio_clip)
            
            # Save video
            output_path = self.video_output_dir / f"enhanced_{content_id}.mp4"
            final_video.write_videofile(
                str(output_path),
                fps=30,
                audio_codec='aac',
                video_codec='libx264',
                temp_audiofile_path=tempfile.mkdtemp(),
                remove_temp=True,
                logger=None
            )
            
            # Cleanup
            os.unlink(audio_path)
            for slide_path in slide_paths:
                try:
                    os.unlink(slide_path)
                except:
                    pass
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Enhanced slideshow generation failed: {str(e)}")
            return await self._generate_simple_slideshow_video(script, topic, content_id)
    
    def _extract_scenes_from_script(self, script: str, topic: str) -> List[str]:
        """Extract scene descriptions from script"""
        import re
        
        scenes = []
        
        # Look for [SCENE: ...] markers
        scene_matches = re.findall(r'\[SCENE: ([^\]]+)\]([^[]*)', script)
        
        if scene_matches:
            for scene_title, scene_content in scene_matches:
                # Combine title and first part of content
                content_preview = scene_content.strip()[:200] + "..." if len(scene_content.strip()) > 200 else scene_content.strip()
                scenes.append(f"{scene_title}: {content_preview}")
        else:
            # Fallback: split by paragraphs
            paragraphs = [p.strip() for p in script.split('\n\n') if p.strip()]
            for i, para in enumerate(paragraphs[:6]):
                preview = para[:200] + "..." if len(para) > 200 else para
                scenes.append(f"Section {i+1}: {preview}")
        
        # Ensure we have at least 3 scenes
        while len(scenes) < 3:
            scenes.append(f"Learning about {topic} - Key concept {len(scenes) + 1}")
            
        return scenes
    
    async def _create_enhanced_slide(
        self, 
        scene_description: str, 
        topic: str, 
        learning_style: str,
        slide_number: int, 
        total_slides: int,
        width: int = 1920, 
        height: int = 1080
    ) -> str:
        """Create visually enhanced slide image"""
        
        # Create base image
        img = Image.new('RGB', (width, height), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)
        
        # Learning style specific color schemes
        color_schemes = {
            "visual": {"primary": (59, 130, 246), "secondary": (147, 51, 234), "accent": (34, 197, 94)},
            "auditory": {"primary": (239, 68, 68), "secondary": (245, 158, 11), "accent": (168, 85, 247)}, 
            "reading": {"primary": (75, 85, 99), "secondary": (55, 65, 81), "accent": (99, 102, 241)},
            "kinesthetic": {"primary": (34, 197, 94), "secondary": (6, 182, 212), "accent": (251, 146, 60)}
        }
        
        colors = color_schemes.get(learning_style, color_schemes["visual"])
        
        # Create gradient background
        for i in range(height):
            r = int(15 + (colors["primary"][0] - 15) * i / height * 0.3)
            g = int(23 + (colors["primary"][1] - 23) * i / height * 0.3) 
            b = int(42 + (colors["primary"][2] - 42) * i / height * 0.3)
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        # Add decorative elements
        draw.rectangle([(0, 0), (width, 12)], fill=colors["accent"])
        draw.rectangle([(0, 0), (16, height)], fill=colors["accent"])
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw topic title
        topic_text = topic.upper()
        topic_bbox = draw.textbbox((0, 0), topic_text, font=title_font)
        topic_width = topic_bbox[2] - topic_bbox[0]
        topic_x = (width - topic_width) // 2
        
        # Add shadow and main text
        draw.text((topic_x + 3, 53), topic_text, fill=(0, 0, 0, 120), font=title_font)
        draw.text((topic_x, 50), topic_text, fill=(255, 255, 255), font=title_font)
        
        # Process scene description
        if ":" in scene_description:
            scene_title, scene_content = scene_description.split(":", 1)
            scene_title = scene_title.strip()
            scene_content = scene_content.strip()
        else:
            scene_title = f"Scene {slide_number}"
            scene_content = scene_description
        
        # Draw scene title
        scene_bbox = draw.textbbox((0, 0), scene_title, font=text_font)
        scene_width = scene_bbox[2] - scene_bbox[0]
        scene_x = (width - scene_width) // 2
        
        draw.text((scene_x + 2, 182), scene_title, fill=(0, 0, 0, 100), font=text_font)
        draw.text((scene_x, 180), scene_title, fill=colors["accent"], font=text_font)
        
        # Format and draw main content
        words = scene_content.split()
        lines = []
        current_line = []
        max_width = width - 200
        
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
        
        # Draw content lines
        start_y = 280
        line_height = 45
        
        for i, line in enumerate(lines[:12]):  # Limit to 12 lines
            line_bbox = draw.textbbox((0, 0), line, font=text_font)
            line_width = line_bbox[2] - line_bbox[0]
            x = (width - line_width) // 2
            y = start_y + i * line_height
            
            # Add shadow
            draw.text((x + 1, y + 1), line, fill=(0, 0, 0, 80), font=text_font)
            draw.text((x, y), line, fill=(255, 255, 255), font=text_font)
        
        # Add slide counter
        counter_text = f"{slide_number} / {total_slides}"
        counter_bbox = draw.textbbox((0, 0), counter_text, font=small_font)
        counter_width = counter_bbox[2] - counter_bbox[0]
        
        # Counter background
        counter_bg = (width - counter_width - 80, height - 100, width - 20, height - 20)
        draw.rounded_rectangle(counter_bg, radius=20, fill=(*colors["primary"], 180))
        
        counter_x = width - counter_width - 50
        counter_y = height - 70
        draw.text((counter_x, counter_y), counter_text, fill=(255, 255, 255), font=small_font)
        
        # Add branding
        brand_text = "EduForge AI"
        draw.text((50, height - 70), brand_text, fill=(200, 200, 200), font=small_font)
        
        # Add learning style indicator
        style_text = f"{learning_style.capitalize()} Learning"
        style_bbox = draw.textbbox((0, 0), style_text, font=small_font)
        style_width = style_bbox[2] - style_bbox[0]
        
        # Style background
        style_bg = (50, 140, 50 + style_width + 40, 180)
        draw.rounded_rectangle(style_bg, radius=15, fill=(*colors["secondary"], 160))
        draw.text((70, 150), style_text, fill=(255, 255, 255), font=small_font)
        
        # Save image
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_file.name, optimize=True, quality=95)
        return temp_file.name
    
    async def _generate_simple_slideshow_video(self, script: str, topic: str, content_id: str) -> str:
        """Fallback: Generate simple slideshow video"""
        from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
        
        try:
            # Generate audio
            audio_path = await self._generate_tts_audio(script)
            audio_clip = AudioFileClip(audio_path)
            
            # Create simple slide
            slide_path = await self._create_simple_slide(topic, script[:300])
            
            # Create video
            img_clip = ImageClip(slide_path, duration=audio_clip.duration)
            final_video = img_clip.with_audio(audio_clip)
            
            # Save
            output_path = self.video_output_dir / f"simple_{content_id}.mp4"
            final_video.write_videofile(str(output_path), fps=24, logger=None)
            
            # Cleanup
            os.unlink(audio_path)
            os.unlink(slide_path)
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Simple slideshow generation failed: {str(e)}")
            raise e
    
    async def _create_simple_slide(self, topic: str, content: str) -> str:
        """Create a simple slide as fallback"""
        img = Image.new('RGB', (1280, 720), color=(30, 41, 59))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        # Draw title
        title_bbox = draw.textbbox((0, 0), topic, font=font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (1280 - title_width) // 2
        
        draw.text((title_x, 100), topic, fill=(255, 255, 255), font=font)
        
        # Draw content preview
        try:
            content_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            content_font = ImageFont.load_default()
        
        words = content.split()[:30]  # First 30 words
        content_text = ' '.join(words) + "..."
        
        # Word wrap
        lines = []
        current_line = []
        max_width = 1000
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=content_font)
            if bbox[2] - bbox[0] < max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw lines
        start_y = 250
        for i, line in enumerate(lines[:8]):
            line_bbox = draw.textbbox((0, 0), line, font=content_font)
            line_width = line_bbox[2] - line_bbox[0]
            x = (1280 - line_width) // 2
            y = start_y + i * 35
            
            draw.text((x, y), line, fill=(200, 200, 200), font=content_font)
        
        # Save
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_file.name)
        return temp_file.name

# Global instance
video_service = VideoGenerationService()