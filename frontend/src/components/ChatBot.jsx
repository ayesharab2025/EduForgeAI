import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { 
  MessageCircle, 
  Send, 
  Minimize2, 
  Maximize2, 
  X, 
  Bot, 
  User, 
  BookOpen, 
  HelpCircle,
  Lightbulb,
  RotateCw
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ChatBot = ({ currentTopic, learningStyle, learnerLevel }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  useEffect(() => {
    // Send welcome message when chatbot opens for the first time
    if (isOpen && messages.length === 0) {
      const welcomeMessage = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: `👋 Hello! I'm your EduForge AI Assistant. I'm here to help you learn more effectively!

I can help you with:
• 📚 Answering questions about any topic
• 📝 Summarizing complex subjects  
• 💡 Providing study tips and strategies
• 🎯 Clarifying difficult concepts

${currentTopic ? `I see you're currently learning about "${currentTopic}". Feel free to ask me anything related to this topic or any other subject you'd like to explore!` : 'What would you like to learn about today?'}`,
        timestamp: new Date().toISOString()
      };
      setMessages([welcomeMessage]);
    }
  }, [isOpen, currentTopic]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const context = currentTopic ? {
        current_topic: currentTopic,
        learning_style: learningStyle,
        learner_level: learnerLevel
      } : null;

      const response = await axios.post(`${API}/chat`, {
        session_id: sessionId,
        message: inputMessage.trim(),
        context
      });

      const assistantMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: response.data.response,
        timestamp: response.data.timestamp,
        error: response.data.error
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('Chat error:', error);
      
      const errorMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: "I apologize, but I'm experiencing technical difficulties. Please try asking your question again, or check your internet connection.",
        timestamp: new Date().toISOString(),
        error: true
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickActions = [
    {
      label: "Summarize Topic",
      icon: <BookOpen className="h-4 w-4" />,
      action: () => {
        if (currentTopic) {
          setInputMessage(`Can you provide a comprehensive summary of ${currentTopic}?`);
        } else {
          setInputMessage("Can you summarize a topic for me?");
        }
      }
    },
    {
      label: "Study Tips", 
      icon: <Lightbulb className="h-4 w-4" />,
      action: () => {
        if (currentTopic) {
          setInputMessage(`What are the best study strategies for learning ${currentTopic}?`);
        } else {
          setInputMessage("What are some effective study strategies?");
        }
      }
    },
    {
      label: "Ask Question",
      icon: <HelpCircle className="h-4 w-4" />,
      action: () => {
        if (currentTopic) {
          setInputMessage(`I have a question about ${currentTopic}: `);
        } else {
          setInputMessage("I have a question about: ");
        }
      }
    }
  ];

  const clearChat = () => {
    setMessages([]);
    // Send new welcome message
    const welcomeMessage = {
      id: `msg_${Date.now()}`,
      role: 'assistant',
      content: "Chat cleared! I'm ready to help you with any new questions or topics you'd like to explore. What would you like to learn about?",
      timestamp: new Date().toISOString()
    };
    setMessages([welcomeMessage]);
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <Button
          onClick={() => setIsOpen(true)}
          className="h-14 w-14 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
        >
          <MessageCircle className="h-6 w-6" />
        </Button>
        <div className="absolute -top-12 right-0 bg-slate-800 text-white text-sm px-3 py-1 rounded-lg opacity-0 hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
          Chat with AI Assistant
        </div>
      </div>
    );
  }

  return (
    <div className={`fixed bottom-6 right-6 z-50 transition-all duration-300 ${
      isMinimized ? 'h-14' : 'h-96 w-96'
    }`}>
      <Card className="h-full w-full shadow-2xl border-0 bg-white/95 backdrop-blur-sm">
        {/* Header */}
        <CardHeader className="pb-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-t-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              <CardTitle className="text-sm font-semibold">
                EduForge AI Assistant
              </CardTitle>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsMinimized(!isMinimized)}
                className="h-6 w-6 p-0 text-white hover:bg-white/20"
              >
                {isMinimized ? <Maximize2 className="h-3 w-3" /> : <Minimize2 className="h-3 w-3" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(false)}
                className="h-6 w-6 p-0 text-white hover:bg-white/20"
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          </div>
          {currentTopic && !isMinimized && (
            <div className="mt-2">
              <Badge variant="secondary" className="bg-white/20 text-white border-white/30">
                Learning: {currentTopic}
              </Badge>
            </div>
          )}
        </CardHeader>

        {!isMinimized && (
          <CardContent className="p-0 flex flex-col h-80">
            {/* Quick Actions */}
            <div className="p-3 border-b bg-slate-50">
              <div className="flex flex-wrap gap-1">
                {quickActions.map((action, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={action.action}
                    className="h-7 text-xs px-2 hover:bg-blue-50"
                  >
                    {action.icon}
                    <span className="ml-1">{action.label}</span>
                  </Button>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearChat}
                  className="h-7 text-xs px-2 hover:bg-red-50 text-red-600"
                >
                  <RotateCw className="h-3 w-3" />
                  <span className="ml-1">Clear</span>
                </Button>
              </div>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 px-3 py-2">
              <div className="space-y-3">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white ml-2'
                          : message.error
                          ? 'bg-red-50 text-red-700 border border-red-200 mr-2'
                          : 'bg-gray-100 text-gray-800 mr-2'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {message.role === 'assistant' && (
                          <Bot className={`h-4 w-4 flex-shrink-0 mt-0.5 ${
                            message.error ? 'text-red-500' : 'text-blue-600'
                          }`} />
                        )}
                        {message.role === 'user' && (
                          <User className="h-4 w-4 flex-shrink-0 mt-0.5 text-white" />
                        )}
                        <div className="whitespace-pre-wrap leading-relaxed">
                          {message.content}
                        </div>
                      </div>
                      <div className={`text-xs mt-1 opacity-70 ${
                        message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                      }`}>
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 text-gray-800 rounded-lg px-3 py-2 text-sm mr-2">
                      <div className="flex items-center gap-2">
                        <Bot className="h-4 w-4 text-blue-600" />
                        <div className="flex space-x-1">
                          <div className="w-1 h-1 bg-blue-600 rounded-full animate-bounce"></div>
                          <div className="w-1 h-1 bg-blue-600 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-1 h-1 bg-blue-600 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input */}
            <div className="p-3 border-t bg-white">
              <div className="flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about learning..."
                  className="flex-1 text-sm"
                  disabled={isLoading}
                />
                <Button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isLoading}
                  className="px-3 bg-blue-600 hover:bg-blue-700"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
};

export default ChatBot;