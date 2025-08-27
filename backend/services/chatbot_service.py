# Chatbot service with stateful memory and topic assistance
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from services.groq_service import groq_service

logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self):
        # In-memory conversation storage
        # In production, this would be stored in Redis or database
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.memory_duration = timedelta(hours=2)  # Keep conversation for 2 hours
        
    def _cleanup_old_conversations(self):
        """Remove conversations older than memory_duration"""
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_id, data in self.conversations.items():
            if current_time - data['created_at'] > self.memory_duration:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.conversations[session_id]
            
    def _get_or_create_conversation(self, session_id: str) -> Dict[str, Any]:
        """Get existing conversation or create new one"""
        self._cleanup_old_conversations()
        
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                'created_at': datetime.utcnow(),
                'messages': [],
                'context': {},
                'user_preferences': {}
            }
        
        return self.conversations[session_id]
    
    async def chat(
        self, 
        session_id: str, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Handle chat interaction with memory and context"""
        
        try:
            # Get conversation history
            conversation = self._get_or_create_conversation(session_id)
            
            # Update context if provided
            if context:
                conversation['context'].update(context)
            
            # Add user message to history
            conversation['messages'].append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Prepare system prompt with context and memory
            system_prompt = self._build_system_prompt(conversation)
            
            # Prepare messages for Groq API
            groq_messages = [{'role': 'system', 'content': system_prompt}]
            
            # Add conversation history (last 10 messages to stay within token limits)
            recent_messages = conversation['messages'][-10:]
            for msg in recent_messages:
                groq_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            # Get response from Groq
            response = await groq_service._make_request(
                messages=groq_messages,
                model="llama3-8b-8192",
                temperature=0.7,
                max_tokens=1500
            )
            
            if response:
                # Add assistant response to history
                conversation['messages'].append({
                    'role': 'assistant', 
                    'content': response,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                return {
                    'response': response,
                    'session_id': session_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                # Fallback response if Groq fails
                fallback_response = self._get_fallback_response(message)
                conversation['messages'].append({
                    'role': 'assistant',
                    'content': fallback_response,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                return {
                    'response': fallback_response,
                    'session_id': session_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Chat service error: {str(e)}")
            error_response = "I apologize, but I'm having technical difficulties. Please try asking your question again."
            
            return {
                'response': error_response,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'error': True
            }
    
    def _build_system_prompt(self, conversation: Dict[str, Any]) -> str:
        """Build contextualized system prompt"""
        
        base_prompt = """You are EduForge AI Assistant, an expert educational chatbot designed to help students learn effectively. You have the following capabilities:

1. **Answer Questions**: Provide clear, accurate answers on any educational topic
2. **Summarize Topics**: Create concise, comprehensive summaries of complex subjects
3. **Clarify Concepts**: Break down difficult ideas into understandable parts
4. **Learning Support**: Offer study tips, learning strategies, and educational guidance
5. **Context Awareness**: Remember our conversation and build upon previous topics

Your communication style should be:
- Clear and educational
- Encouraging and supportive  
- Appropriate for learners of all levels
- Concise but comprehensive
- Engaging and interactive

Guidelines:
- Always provide accurate, helpful information
- If you don't know something, admit it and suggest how to find the answer
- Use examples and analogies to explain complex concepts
- Encourage critical thinking and curiosity
- Maintain conversation context and refer back to previous topics when relevant"""

        # Add context from current learning session if available
        context = conversation.get('context', {})
        if context:
            context_info = "\n\nCurrent Learning Context:\n"
            
            if 'current_topic' in context:
                context_info += f"- Current Topic: {context['current_topic']}\n"
            if 'learning_style' in context:
                context_info += f"- Learner Style: {context['learning_style']}\n"
            if 'learner_level' in context:
                context_info += f"- Learner Level: {context['learner_level']}\n"
            if 'recent_objectives' in context:
                context_info += f"- Recent Learning Objectives: {', '.join(context['recent_objectives'][:3])}\n"
                
            base_prompt += context_info
        
        # Add conversation summary for long conversations
        messages = conversation.get('messages', [])
        if len(messages) > 6:
            base_prompt += "\n\nConversation Summary: We have been discussing educational topics. Please maintain continuity with our previous conversation while helping with new questions."
        
        return base_prompt
    
    def _get_fallback_response(self, message: str) -> str:
        """Provide fallback response when Groq API fails"""
        
        message_lower = message.lower()
        
        # Common educational queries
        if any(word in message_lower for word in ['what is', 'define', 'explain']):
            return "I'd be happy to help explain that concept! However, I'm experiencing some technical difficulties right now. Could you try rephrasing your question, or I can help you find reliable educational resources to look up the information you need."
        
        elif any(word in message_lower for word in ['how to', 'how do', 'steps']):
            return "Great question about the process! While I'm having some connectivity issues, I can suggest breaking down your learning into smaller steps and checking reputable educational sources for step-by-step guides."
        
        elif any(word in message_lower for word in ['summary', 'summarize', 'overview']):
            return "I'd love to help create a summary for you! Unfortunately, I'm experiencing technical issues. In the meantime, try creating your own summary by identifying the main points, key concepts, and important details of the topic you're studying."
        
        elif any(word in message_lower for word in ['help', 'stuck', 'confused']):
            return "I understand you need help! Even though I'm having technical difficulties, here are some general study strategies: break the problem into smaller parts, review the basics, try explaining it to someone else, and don't hesitate to seek additional resources or ask teachers/peers for clarification."
        
        else:
            return "Thank you for your question! I'm currently experiencing technical difficulties, but I'm here to help with your learning. Please try asking your question again, or feel free to explore the educational content and resources available in EduForge AI."
    
    async def summarize_topic(
        self, 
        session_id: str, 
        topic: str, 
        detail_level: str = "medium"
    ) -> Dict[str, str]:
        """Generate topic summary with specified detail level"""
        
        detail_instructions = {
            "brief": "Provide a concise 2-3 sentence summary covering only the most essential points.",
            "medium": "Create a comprehensive paragraph summary (4-6 sentences) covering key concepts and main ideas.",
            "detailed": "Generate an in-depth summary with multiple paragraphs covering concepts, applications, examples, and significance."
        }
        
        instruction = detail_instructions.get(detail_level, detail_instructions["medium"])
        
        prompt = f"""Please provide a {detail_level} summary of the topic: {topic}

{instruction}

The summary should be educational, accurate, and appropriate for learners. Include:
- Main concepts and definitions
- Key points and important details
- Practical applications or examples (if applicable)
- Why this topic is important or relevant

Format the response in a clear, organized manner that's easy to understand."""

        return await self.chat(session_id, prompt)
    
    async def get_study_tips(
        self, 
        session_id: str, 
        topic: str, 
        learning_style: Optional[str] = None
    ) -> Dict[str, str]:
        """Provide personalized study tips"""
        
        style_note = ""
        if learning_style:
            style_note = f" Keep in mind that I'm a {learning_style} learner."
        
        prompt = f"""Can you provide effective study tips and strategies for learning about {topic}?{style_note}

Please include:
- Specific study techniques that work well for this subject
- How to organize and structure learning
- Common challenges and how to overcome them
- Ways to test understanding and retention
- Additional resources or tools that might help

Make the advice practical and actionable."""

        return await self.chat(session_id, prompt)
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        conversation = self.conversations.get(session_id, {})
        return conversation.get('messages', [])
    
    def clear_conversation(self, session_id: str) -> bool:
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            return True
        return False
    
    def update_learning_context(
        self, 
        session_id: str, 
        topic: str, 
        learning_style: str, 
        learner_level: str,
        learning_objectives: Optional[List[str]] = None
    ):
        """Update the learning context for better personalized responses"""
        conversation = self._get_or_create_conversation(session_id)
        
        conversation['context'].update({
            'current_topic': topic,
            'learning_style': learning_style,
            'learner_level': learner_level,
            'updated_at': datetime.utcnow().isoformat()
        })
        
        if learning_objectives:
            conversation['context']['recent_objectives'] = learning_objectives
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        self._cleanup_old_conversations()
        return list(self.conversations.keys())
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions"""
        self._cleanup_old_conversations()
        
        total_sessions = len(self.conversations)
        total_messages = sum(len(conv['messages']) for conv in self.conversations.values())
        
        return {
            'active_sessions': total_sessions,
            'total_messages': total_messages,
            'average_messages_per_session': total_messages / total_sessions if total_sessions > 0 else 0
        }

# Global instance
chatbot_service = ChatbotService()