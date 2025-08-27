# Test video generation service
import pytest
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from services.video_service import VideoGenerationService

@pytest.mark.asyncio
class TestVideoGenerationService:
    """Test video generation service functionality"""
    
    def test_initialization(self):
        """Test service initialization"""
        service = VideoGenerationService()
        assert isinstance(service.opensora_path, Path)
        assert isinstance(service.video_output_dir, Path)
    
    @patch('services.video_service.Path.exists')
    async def test_is_opensora_available_not_installed(self, mock_exists):
        """Test OpenSora availability when not installed"""
        mock_exists.return_value = False
        
        service = VideoGenerationService()
        
        with patch.object(service, '_setup_opensora', return_value=True) as mock_setup:
            result = await service._is_opensora_available()
            mock_setup.assert_called_once()
    
    @patch('services.video_service.Path.exists')
    async def test_is_opensora_available_installed(self, mock_exists):
        """Test OpenSora availability when properly installed"""
        mock_exists.return_value = True
        
        service = VideoGenerationService()
        result = await service._is_opensora_available()
        assert result == True
    
    @patch('asyncio.create_subprocess_exec')
    async def test_setup_opensora_success(self, mock_subprocess):
        """Test successful OpenSora setup"""
        # Mock successful git clone
        mock_process = Mock()
        mock_process.communicate.return_value = (b"success", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        service = VideoGenerationService()
        result = await service._setup_opensora()
        
        assert result == True
        assert mock_subprocess.call_count == 2  # git clone + pip install
    
    @patch('asyncio.create_subprocess_exec')
    async def test_setup_opensora_failure(self, mock_subprocess):
        """Test OpenSora setup failure"""
        # Mock failed git clone
        mock_process = Mock()
        mock_process.communicate.return_value = (b"", b"error")
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process
        
        service = VideoGenerationService()
        result = await service._setup_opensora()
        
        assert result == False
    
    async def test_generate_tts_audio(self):
        """Test TTS audio generation"""
        service = VideoGenerationService()
        
        script = "[SCENE: Intro] Welcome to the lesson! This is important content. [SCENE: Main] Key concepts here."
        
        with patch('services.video_service.gTTS') as mock_gtts:
            mock_tts_instance = Mock()
            mock_gtts.return_value = mock_tts_instance
            
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp_file = Mock()
                mock_temp_file.name = "/tmp/test_audio.mp3"
                mock_temp.return_value = mock_temp_file
                
                result = await service._generate_tts_audio(script)
                
                # Verify TTS was called with cleaned script (no scene markers)
                mock_gtts.assert_called_once()
                args = mock_gtts.call_args[1]
                assert "[SCENE:" not in args['text']
                assert "Welcome to the lesson!" in args['text']
                
                assert result == "/tmp/test_audio.mp3"
    
    def test_extract_scenes_from_script_with_markers(self):
        """Test scene extraction with scene markers"""
        service = VideoGenerationService()
        
        script = "[SCENE: Introduction] Welcome! [SCENE: Main Content] Key points here. [SCENE: Conclusion] Summary."
        
        scenes = service._extract_scenes_from_script(script, "Test Topic")
        
        assert len(scenes) >= 3
        assert "Introduction" in scenes[0]
        assert "Main Content" in scenes[1]
        assert "Conclusion" in scenes[2]
    
    def test_extract_scenes_from_script_without_markers(self):
        """Test scene extraction without scene markers"""
        service = VideoGenerationService()
        
        script = "This is paragraph one.\n\nThis is paragraph two.\n\nThis is paragraph three."
        
        scenes = service._extract_scenes_from_script(script, "Test Topic")
        
        assert len(scenes) >= 3
        assert "Section 1" in scenes[0]
        assert "paragraph one" in scenes[0]
    
    def test_extract_scenes_minimal_content(self):
        """Test scene extraction with minimal content"""
        service = VideoGenerationService()
        
        script = "Short script."
        
        scenes = service._extract_scenes_from_script(script, "Test Topic")
        
        # Should ensure at least 3 scenes
        assert len(scenes) >= 3
        assert "Test Topic" in scenes[1]  # Fallback scenes mention the topic
    
    def test_create_opensora_prompt_visual_style(self):
        """Test OpenSora prompt creation for visual learning style"""
        service = VideoGenerationService()
        
        script = "[SCENE: Intro] Welcome [SCENE: Content] Main ideas [SCENE: Summary] Conclusion"
        
        prompt = service._create_opensora_prompt(script, "Machine Learning", "visual")
        
        assert "Machine Learning" in prompt
        assert "educational animation" in prompt
        assert "diagrams" in prompt
        assert "Intro" in prompt or "Content" in prompt
    
    def test_create_opensora_prompt_auditory_style(self):
        """Test OpenSora prompt creation for auditory learning style"""
        service = VideoGenerationService()
        
        script = "Educational content about AI"
        
        prompt = service._create_opensora_prompt(script, "AI", "auditory")
        
        assert "AI" in prompt
        assert "talking head" in prompt
        assert "narration" in prompt
    
    @patch('services.video_service.VideoGenerationService._generate_tts_audio')
    @patch('services.video_service.VideoGenerationService._create_enhanced_slide')
    @patch('services.video_service.ImageClip')
    @patch('services.video_service.AudioFileClip')
    async def test_generate_enhanced_slideshow_video(self, mock_audio_clip, mock_image_clip, mock_create_slide, mock_tts):
        """Test enhanced slideshow video generation"""
        # Mock TTS audio
        mock_tts.return_value = "/tmp/audio.mp3"
        
        # Mock audio clip
        mock_audio_instance = Mock()
        mock_audio_instance.duration = 10.0
        mock_audio_clip.return_value = mock_audio_instance
        
        # Mock slide creation
        mock_create_slide.return_value = "/tmp/slide.png"
        
        # Mock image clips
        mock_img_instance = Mock()
        mock_img_instance.fadein.return_value = mock_img_instance
        mock_img_instance.fadeout.return_value = mock_img_instance
        mock_image_clip.return_value = mock_img_instance
        
        # Mock video composition
        mock_final_video = Mock()
        mock_final_video.with_audio.return_value = mock_final_video
        
        with patch('services.video_service.concatenate_videoclips', return_value=mock_final_video):
            service = VideoGenerationService()
            
            script = "[SCENE: Test] This is a test script for video generation."
            
            with patch('tempfile.mkdtemp', return_value="/tmp"):
                result = await service._generate_enhanced_slideshow_video(script, "Test Topic", "visual", "test_id")
                
                # Verify the process
                mock_tts.assert_called_once()
                mock_create_slide.assert_called()
                mock_final_video.write_videofile.assert_called_once()
    
    @patch('services.video_service.VideoGenerationService._generate_tts_audio')
    @patch('services.video_service.VideoGenerationService._create_simple_slide')
    @patch('services.video_service.ImageClip')
    @patch('services.video_service.AudioFileClip')
    async def test_generate_simple_slideshow_video(self, mock_audio_clip, mock_image_clip, mock_create_slide, mock_tts):
        """Test simple slideshow video generation (fallback)"""
        # Mock TTS and slide creation
        mock_tts.return_value = "/tmp/audio.mp3"
        mock_create_slide.return_value = "/tmp/slide.png"
        
        # Mock clips
        mock_audio_instance = Mock()
        mock_audio_instance.duration = 5.0
        mock_audio_clip.return_value = mock_audio_instance
        
        mock_img_instance = Mock()
        mock_img_instance.with_audio.return_value = mock_img_instance
        mock_image_clip.return_value = mock_img_instance
        
        service = VideoGenerationService()
        
        result = await service._generate_simple_slideshow_video("Test script", "Test Topic", "test_id")
        
        mock_tts.assert_called_once()
        mock_create_slide.assert_called_once()
        mock_img_instance.write_videofile.assert_called_once()
    
    async def test_create_enhanced_slide_visual_style(self):
        """Test enhanced slide creation for visual learning style"""
        service = VideoGenerationService()
        
        with patch('services.video_service.Image') as mock_image, \
             patch('services.video_service.ImageDraw') as mock_draw, \
             patch('services.video_service.ImageFont') as mock_font:
            
            # Mock PIL objects
            mock_img_instance = Mock()
            mock_image.new.return_value = mock_img_instance
            
            mock_draw_instance = Mock()
            mock_draw.Draw.return_value = mock_draw_instance
            
            # Mock text dimensions
            mock_draw_instance.textbbox.return_value = (0, 0, 100, 20)
            
            # Mock font loading
            mock_font.truetype.return_value = Mock()
            
            # Mock temporary file
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp_file = Mock()
                mock_temp_file.name = "/tmp/slide.png"
                mock_temp.return_value = mock_temp_file
                
                result = await service._create_enhanced_slide(
                    "Test scene description", "AI Topic", "visual", 1, 3
                )
                
                # Verify slide creation process
                mock_image.new.assert_called_once()
                mock_draw.Draw.assert_called_once()
                mock_img_instance.save.assert_called_once()
                
                assert result == "/tmp/slide.png"
    
    async def test_create_simple_slide(self):
        """Test simple slide creation (fallback)"""
        service = VideoGenerationService()
        
        with patch('services.video_service.Image') as mock_image, \
             patch('services.video_service.ImageDraw') as mock_draw:
            
            mock_img_instance = Mock()
            mock_image.new.return_value = mock_img_instance
            
            mock_draw_instance = Mock()
            mock_draw_instance.textbbox.return_value = (0, 0, 100, 20)
            mock_draw.Draw.return_value = mock_draw_instance
            
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp_file = Mock()
                mock_temp_file.name = "/tmp/simple_slide.png"
                mock_temp.return_value = mock_temp_file
                
                result = await service._create_simple_slide("Test Topic", "Test content for the slide")
                
                mock_img_instance.save.assert_called_once()
                assert result == "/tmp/simple_slide.png"
    
    @patch('services.video_service.VideoGenerationService._is_opensora_available')
    @patch('services.video_service.VideoGenerationService._generate_opensora_video')
    async def test_generate_video_with_opensora(self, mock_opensora_gen, mock_available):
        """Test video generation when OpenSora is available"""
        mock_available.return_value = True
        mock_opensora_gen.return_value = "/tmp/opensora_video.mp4"
        
        service = VideoGenerationService()
        
        result = await service.generate_video("Test script", "AI", "visual", "test_id")
        
        assert result == "/tmp/opensora_video.mp4"
        mock_opensora_gen.assert_called_once_with("Test script", "AI", "visual", "test_id")
    
    @patch('services.video_service.VideoGenerationService._is_opensora_available')
    @patch('services.video_service.VideoGenerationService._generate_enhanced_slideshow_video')
    async def test_generate_video_without_opensora(self, mock_slideshow_gen, mock_available):
        """Test video generation when OpenSora is not available"""
        mock_available.return_value = False
        mock_slideshow_gen.return_value = "/tmp/slideshow_video.mp4"
        
        service = VideoGenerationService()
        
        result = await service.generate_video("Test script", "AI", "visual", "test_id")
        
        assert result == "/tmp/slideshow_video.mp4"
        mock_slideshow_gen.assert_called_once_with("Test script", "AI", "visual", "test_id")
    
    @patch('services.video_service.VideoGenerationService._is_opensora_available')
    @patch('services.video_service.VideoGenerationService._generate_simple_slideshow_video')
    async def test_generate_video_fallback_on_error(self, mock_simple_gen, mock_available):
        """Test video generation falls back to simple slideshow on errors"""
        mock_available.return_value = True
        
        service = VideoGenerationService()
        
        # Mock the enhanced methods to fail
        with patch.object(service, '_generate_opensora_video', side_effect=Exception("OpenSora failed")):
            with patch.object(service, '_generate_enhanced_slideshow_video', side_effect=Exception("Enhanced failed")):
                mock_simple_gen.return_value = "/tmp/simple_video.mp4"
                
                result = await service.generate_video("Test script", "AI", "visual", "test_id")
                
                assert result == "/tmp/simple_video.mp4"
                mock_simple_gen.assert_called_once()