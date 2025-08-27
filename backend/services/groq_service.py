# Groq API service with key rotation and retry logic
import asyncio
import logging
from typing import Dict, Any, Optional
from groq import Groq
from config import settings, LEARNING_STYLES

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
        learning_style: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generate complete educational content tailored to learning style"""
        
        system_prompt = f"""You are an expert educational content creator. Create comprehensive, high-quality educational content about {topic} for {learner_level} level learners.

Generate ONLY valid JSON with this exact structure:
{{
  "learning_objectives": [
    "Specific, measurable learning objective 1 about {topic}",
    "Practical learning objective 2 about {topic}",
    "Applied learning objective 3 about {topic}",
    "Advanced understanding objective 4 about {topic}",
    "Real-world application objective 5 about {topic}"
  ],
  "video_script": "Create a comprehensive, engaging 3-4 minute educational video script about {topic}. Write it as a complete narrative that teaches the viewer about {topic}. Do NOT include any scene markers, developer instructions, or technical notes. Write it as if you are directly teaching a student about {topic}. Start with an engaging introduction, explain key concepts clearly, provide examples, and conclude with practical applications. Make it conversational and educational.",
  "quiz": [
    {{
      "question": "Thoughtful question about core concept of {topic}",
      "options": ["Correct detailed answer about {topic}", "Plausible but incorrect option", "Another incorrect but reasonable option", "Obviously incorrect option"],
      "correct_answer": 0,
      "explanation": "Detailed explanation of why this answer is correct and how it relates to {topic}",
      "hint": "Helpful hint that guides thinking about {topic}"
    }},
    {{
      "question": "Application-based question about {topic}",
      "options": ["Incorrect application", "Correct practical application of {topic}", "Misunderstanding of concept", "Unrelated option"],
      "correct_answer": 1,
      "explanation": "Clear explanation connecting theory to practice in {topic}",
      "hint": "Think about how {topic} is used in real-world scenarios"
    }},
    {{
      "question": "Analysis question requiring deeper understanding of {topic}",
      "options": ["Surface-level answer", "Partially correct but incomplete", "Fully correct analytical answer about {topic}", "Incorrect analysis"],
      "correct_answer": 2,
      "explanation": "Comprehensive explanation of the analytical aspects of {topic}",
      "hint": "Consider the underlying principles of {topic}"
    }},
    {{
      "question": "Problem-solving question related to {topic}",
      "options": ["Wrong approach", "Correct problem-solving approach for {topic}", "Incomplete solution", "Irrelevant method"],
      "correct_answer": 1,
      "explanation": "Step-by-step explanation of the correct problem-solving approach in {topic}",
      "hint": "Break down the problem systematically using {topic} principles"
    }},
    {{
      "question": "Evaluation question about {topic} applications",
      "options": ["Incorrect evaluation", "Partially correct assessment", "Incomplete analysis", "Correct comprehensive evaluation of {topic}"],
      "correct_answer": 3,
      "explanation": "Detailed explanation of evaluation criteria and correct assessment of {topic}",
      "hint": "Consider multiple factors when evaluating {topic} applications"
    }}
  ],
  "flashcards": [
    {{
      "front": "What is {topic}?",
      "back": "Comprehensive definition and explanation of {topic} with key characteristics"
    }},
    {{
      "front": "Key principles of {topic}",
      "back": "List and explain the fundamental principles that govern {topic}"
    }},
    {{
      "front": "How does {topic} work?",
      "back": "Step-by-step explanation of the process/mechanism behind {topic}"
    }},
    {{
      "front": "Main applications of {topic}",
      "back": "Real-world applications and use cases where {topic} is implemented"
    }},
    {{
      "front": "Benefits of {topic}",
      "back": "Key advantages and positive impacts of using/understanding {topic}"
    }},
    {{
      "front": "Common challenges in {topic}",
      "back": "Typical difficulties and how they are addressed in {topic}"
    }},
    {{
      "front": "Future of {topic}",
      "back": "Emerging trends and future developments in {topic}"
    }},
    {{
      "front": "Getting started with {topic}",
      "back": "Practical steps for beginners to start learning/implementing {topic}"
    }}
  ],
  "ui_suggestions": {{
    "color_scheme": "Professional color scheme suitable for {topic}",
    "layout_emphasis": "Focus on clear content presentation for {topic}",
    "interaction_type": "Educational interactions optimized for learning {topic}"
  }}
}}

Make sure all content is specifically about {topic}, educational, accurate, and appropriate for {learner_level} level learners. Avoid generic or placeholder content."""

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
            "video_script": f"""Welcome to this comprehensive lesson on {topic}! Today we'll explore this fascinating subject through a {learning_style} learning approach.

Let's start by understanding what {topic} really means and why it's important in today's world. {style_config['content_emphasis']} will help us grasp these concepts effectively.

Now, let's dive deeper into the key components and examine how they work together to form the complete picture of {topic}.

Finally, we'll see how {topic} applies to real-world situations and how you can use this knowledge in practical scenarios.

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