# Groq API service with key rotation and retry logic
import asyncio
import logging
from typing import Dict, Any, Optional
from groq import Groq
from ..config import settings, LEARNING_STYLES

logger = logging.getLogger(__name__)

class GroqAPIService:
    def __init__(self):
        self.api_keys = settings.GROQ_API_KEYS
        self.current_key_index = 0
        self.request_count = 0
        self.max_requests_per_key = settings.MAX_REQUESTS_PER_KEY
        self.client = Groq(api_key=self.api_keys[0])
        
    def _rotate_api_key(self):
        """Rotate to the next API key"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.request_count = 0
        new_key = self.api_keys[self.current_key_index]
        self.client = Groq(api_key=new_key)
        logger.info(f"Rotated to API key {self.current_key_index + 1}")
        
    async def _make_request(self, messages: list, model: str = "llama3-8b-8192", **kwargs) -> Optional[str]:
        """Make request with automatic key rotation and retry logic"""
        max_retries = len(self.api_keys)
        
        for attempt in range(max_retries):
            try:
                # Check if we need to rotate the key
                if self.request_count >= self.max_requests_per_key:
                    self._rotate_api_key()
                
                response = self.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    **kwargs
                )
                
                self.request_count += 1
                return response.choices[0].message.content
                
            except Exception as e:
                logger.warning(f"Request failed with key {self.current_key_index + 1}: {str(e)}")
                if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                    self._rotate_api_key()
                else:
                    # For other errors, wait a bit and retry with same key
                    await asyncio.sleep(1)
                
                if attempt == max_retries - 1:
                    logger.error(f"All API keys exhausted for request")
                    raise e
                    
        return None
    
    async def generate_educational_content(
        self, 
        topic: str, 
        learner_level: str, 
        learning_style: str
    ) -> Dict[str, Any]:
        """Generate complete educational content tailored to learning style"""
        
        style_config = LEARNING_STYLES.get(learning_style.lower(), LEARNING_STYLES["visual"])
        
        system_prompt = f"""You are an expert educational content creator specializing in {learning_style} learning.

Create comprehensive educational content for {learner_level} level learners about: {topic}

Learning Style Focus: {style_config['content_emphasis']}
{style_config['prompt_suffix']}

Generate ONLY valid JSON with this exact structure:
{{
  "learning_objectives": [
    "Detailed objective 1 (specific and measurable)",
    "Detailed objective 2 (with action verbs)",
    "Detailed objective 3 (tailored to {learner_level} level)",
    "Detailed objective 4 (aligned with {learning_style} learning)",
    "Detailed objective 5 (practical application)"
  ],
  "video_script": "Comprehensive 3-4 minute script with [SCENE: description] markers for visual cues. Include engaging narration tailored for {learning_style} learners. Format with proper paragraphs and scene breaks.",
  "quiz": [
    {{
      "question": "Thought-provoking question 1",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0,
      "explanation": "Detailed explanation with learning reinforcement",
      "hint": "Helpful hint for learners"
    }},
    {{
      "question": "Application-based question 2",
      "options": ["Option A", "Option B", "Option C", "Option D"], 
      "correct_answer": 1,
      "explanation": "Clear explanation connecting to learning objectives",
      "hint": "Guiding hint"
    }},
    {{
      "question": "Analysis question 3",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 2,
      "explanation": "Comprehensive explanation",
      "hint": "Strategic hint"
    }},
    {{
      "question": "Synthesis question 4", 
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 1,
      "explanation": "In-depth explanation",
      "hint": "Learning-focused hint"
    }},
    {{
      "question": "Evaluation question 5",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 3,
      "explanation": "Detailed explanation with examples",
      "hint": "Supportive hint"
    }}
  ],
  "flashcards": [
    {{
      "front": "Key concept 1",
      "back": "Comprehensive explanation with examples"
    }},
    {{
      "front": "Important term 2",
      "back": "Clear definition with context"
    }},
    {{
      "front": "Process/Method 3",
      "back": "Step-by-step explanation"
    }},
    {{
      "front": "Application 4",
      "back": "Real-world example and usage"
    }},
    {{
      "front": "Connection 5",
      "back": "How this relates to broader concepts"
    }},
    {{
      "front": "Practice 6",
      "back": "Example problem or scenario"
    }},
    {{
      "front": "Summary 7",
      "back": "Key takeaway and importance"
    }},
    {{
      "front": "Next Steps 8",
      "back": "What to learn next or how to apply"
    }}
  ],
  "ui_suggestions": {{
    "color_scheme": "Recommended colors based on topic and learning style",
    "layout_emphasis": "Visual focus areas for {learning_style} learners",
    "interaction_type": "Recommended interaction patterns"
  }}
}}

Ensure the content is engaging, age-appropriate for {learner_level} level, and optimized for {learning_style} learning style."""

        try:
            content = await self._make_request(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create educational content for: {topic}"}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            return self._parse_educational_content(content)
            
        except Exception as e:
            logger.error(f"Error generating educational content: {str(e)}")
            return self._get_fallback_content(topic, learner_level, learning_style)
    
    def _parse_educational_content(self, content: str) -> Dict[str, Any]:
        """Parse and clean the educational content from Groq response"""
        import json
        import re
        
        # Clean the content
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        content = re.sub(r'Here is.*?:', '', content, flags=re.IGNORECASE)
        content = content.strip()
        
        # Find JSON object
        start_idx = content.find('{')
        if start_idx == -1:
            raise ValueError("No JSON object found in response")
        
        # Find matching closing brace
        brace_count = 0
        end_idx = start_idx
        for i, char in enumerate(content[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        json_str = content[start_idx:end_idx]
        return json.loads(json_str)
    
    def _get_fallback_content(self, topic: str, learner_level: str, learning_style: str) -> Dict[str, Any]:
        """Provide fallback content if API fails"""
        style_config = LEARNING_STYLES.get(learning_style.lower(), LEARNING_STYLES["visual"])
        
        return {
            "learning_objectives": [
                f"Understand the fundamental concepts of {topic}",
                f"Analyze key components and their relationships in {topic}",
                f"Apply {topic} principles to real-world scenarios",
                f"Evaluate different approaches and methods in {topic}",
                f"Create solutions using {topic} knowledge and skills"
            ],
            "video_script": f"""[SCENE: Introduction with {topic} overview]
Welcome to this comprehensive lesson on {topic}! Today we'll explore this fascinating subject through a {learning_style} learning approach.

[SCENE: Core concepts explanation] 
Let's start by understanding what {topic} really means and why it's important in today's world. {style_config['content_emphasis']} will help us grasp these concepts effectively.

[SCENE: Detailed breakdown]
Now, let's dive deeper into the key components and examine how they work together to form the complete picture of {topic}.

[SCENE: Practical applications]
Finally, we'll see how {topic} applies to real-world situations and how you can use this knowledge in practical scenarios.

[SCENE: Summary and next steps]
To summarize, we've covered the essential aspects of {topic} using {learning_style} learning techniques. Remember to practice these concepts and explore further!""",
            "quiz": [
                {
                    "question": f"What is the primary focus of {topic}?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": 0,
                    "explanation": f"The primary focus helps establish the foundation for understanding {topic}.",
                    "hint": "Think about the core purpose and main objectives."
                },
                {
                    "question": f"How does {topic} apply to real-world scenarios?",
                    "options": ["Limited applications", "Broad practical uses", "Theoretical only", "Outdated concepts"],
                    "correct_answer": 1,
                    "explanation": f"{topic} has extensive real-world applications across many fields.",
                    "hint": "Consider the practical benefits and widespread usage."
                },
                {
                    "question": f"What makes {topic} particularly suitable for {learning_style} learners?",
                    "options": ["Text-heavy content", style_config['content_emphasis'], "Audio-only format", "Abstract concepts"],
                    "correct_answer": 1,
                    "explanation": f"The emphasis on {style_config['content_emphasis']} aligns perfectly with {learning_style} learning preferences.",
                    "hint": "Think about how the content is presented and structured."
                }
            ],
            "flashcards": [
                {
                    "front": f"What is {topic}?",
                    "back": f"A comprehensive subject area with practical applications and theoretical foundations."
                },
                {
                    "front": f"Key benefits of {topic}",
                    "back": "Provides practical skills, theoretical understanding, and real-world applications."
                },
                {
                    "front": f"{learning_style} learning approach",
                    "back": f"Emphasizes {style_config['content_emphasis']} for optimal learning experience."
                }
            ],
            "ui_suggestions": {
                "color_scheme": "Blue and green gradients for trust and growth",
                "layout_emphasis": f"Focus on {style_config['video_style']}",
                "interaction_type": f"Interactive elements suited for {learning_style} learners"
            }
        }

# Global instance
groq_service = GroqAPIService()