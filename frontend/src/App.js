import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Progress } from "./components/ui/progress";
import { Alert, AlertDescription } from "./components/ui/alert";
import { 
  CheckCircle2, 
  Brain, 
  BookOpen, 
  Video, 
  HelpCircle, 
  RotateCw, 
  Play, 
  Sparkles,
  Target,
  Clock,
  Users,
  TrendingUp,
  Award,
  Zap,
  Lightbulb
} from "lucide-react";
import { toast, Toaster } from "sonner";
import ChatBot from "./components/ChatBot";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [formData, setFormData] = useState({
    topic: "",
    learner_level: "",
    learning_style: ""
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [showQuizResults, setShowQuizResults] = useState(false);
  const [flippedCards, setFlippedCards] = useState(new Set());
  const [videoUrl, setVideoUrl] = useState(null);
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [videoProgress, setVideoProgress] = useState(0);

  const steps = ["Content Generation", "Video Creation", "Ready to Learn"];

  const learningStyleInfo = {
    visual: {
      icon: "👁️",
      title: "Visual Learner",
      description: "Learn best through images, diagrams, and visual aids",
      features: ["Rich visual content", "Infographics & charts", "Color-coded materials", "Visual scene markers"]
    },
    auditory: {
      icon: "👂",
      title: "Auditory Learner", 
      description: "Learn best through listening and discussion",
      features: ["Detailed narration", "Dialogue-based content", "Audio explanations", "Discussion questions"]
    },
    reading: {
      icon: "📚",
      title: "Reading/Writing Learner",
      description: "Learn best through text and written materials",
      features: ["Comprehensive text", "Structured outlines", "Written summaries", "Reading materials"]
    },
    kinesthetic: {
      icon: "✋",
      title: "Kinesthetic Learner",
      description: "Learn best through hands-on activities",
      features: ["Interactive elements", "Practical examples", "Try-it-yourself tasks", "Real-world applications"]
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const generateContent = async () => {
    if (!formData.topic || !formData.learner_level || !formData.learning_style) {
      toast.error("Please fill in all fields to create your personalized learning experience");
      return;
    }

    setIsGenerating(true);
    setCurrentStep(0);
    setVideoProgress(0);
    
    try {
      toast.info("🚀 Generating your personalized learning content...");
      
      const response = await axios.post(`${API}/generate_content`, formData);
      setGeneratedContent(response.data);
      setCurrentStep(1);
      
      toast.success("✨ Content generated successfully! Now creating your video...");
      
      // Generate video
      await generateVideo(response.data.id);
      
    } catch (error) {
      console.error("Error generating content:", error);
      
      let errorMessage = "Failed to generate content. Please try again.";
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      toast.error(errorMessage);
      setIsGenerating(false);
      setCurrentStep(0);
    }
  };

  const generateVideo = async (contentId) => {
    setIsGeneratingVideo(true);
    setVideoProgress(20);
    
    try {
      // Start video generation
      const response = await axios.post(`${API}/generate_video`, 
        { content_id: contentId },
        { responseType: 'blob', timeout: 180000 } // 3 minute timeout
      );
      
      setVideoProgress(90);
      
      // Create video URL from blob
      const videoBlob = new Blob([response.data], { type: 'video/mp4' });
      const videoUrl = URL.createObjectURL(videoBlob);
      setVideoUrl(videoUrl);
      
      setVideoProgress(100);
      setCurrentStep(2);
      setIsGenerating(false);
      
      toast.success("🎬 Your AI-powered educational video is ready!");
      
    } catch (error) {
      console.error("Error generating video:", error);
      
      let errorMessage = "Video generation failed. You can still access the learning materials below.";
      if (error.response?.status === 404) {
        errorMessage = "Content not found. Please try generating content again.";
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = "Video generation is taking longer than expected. You can still access other learning materials.";
      }
      
      toast.warning(errorMessage);
      
      // Still mark as complete so user can access other content
      setCurrentStep(2);
      setIsGenerating(false);
    } finally {
      setIsGeneratingVideo(false);
    }
  };

  const handleQuizAnswer = (questionId, answerIndex) => {
    setQuizAnswers(prev => ({ ...prev, [questionId]: answerIndex }));
  };

  const submitQuiz = () => {
    setShowQuizResults(true);
    const correctAnswers = generatedContent.quiz.filter(
      (q) => quizAnswers[q.id] === q.correct_answer
    ).length;
    
    const percentage = Math.round((correctAnswers / generatedContent.quiz.length) * 100);
    
    if (percentage >= 80) {
      toast.success(`🎉 Excellent work! You scored ${correctAnswers}/${generatedContent.quiz.length} (${percentage}%)`);
    } else if (percentage >= 60) {
      toast.success(`👏 Good job! You scored ${correctAnswers}/${generatedContent.quiz.length} (${percentage}%)`);
    } else {
      toast.info(`📚 You scored ${correctAnswers}/${generatedContent.quiz.length} (${percentage}%). Review the explanations and try again!`);
    }
  };

  const toggleFlashcard = (cardId) => {
    const newFlipped = new Set(flippedCards);
    if (newFlipped.has(cardId)) {
      newFlipped.delete(cardId);
    } else {
      newFlipped.add(cardId);
    }
    setFlippedCards(newFlipped);
  };

  const resetApp = () => {
    setFormData({ topic: "", learner_level: "", learning_style: "" });
    setGeneratedContent(null);
    setCurrentStep(0);
    setQuizAnswers({});
    setShowQuizResults(false);
    setFlippedCards(new Set());
    setVideoUrl(null);
    setIsGeneratingVideo(false);
    setVideoProgress(0);
    
    if (videoUrl) {
      URL.revokeObjectURL(videoUrl);
    }
  };

  // Update video progress simulation during generation
  useEffect(() => {
    if (isGeneratingVideo && videoProgress < 80) {
      const interval = setInterval(() => {
        setVideoProgress(prev => Math.min(prev + Math.random() * 10, 80));
      }, 2000);
      
      return () => clearInterval(interval);
    }
  }, [isGeneratingVideo, videoProgress]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      <Toaster position="top-center" expand={true} richColors />
      
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="relative">
              <Brain className="h-12 w-12 text-blue-600" />
              <Sparkles className="h-5 w-5 text-purple-500 absolute -top-1 -right-1" />
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
              EduForge AI
            </h1>
          </div>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed mb-6">
            Transform any topic into a complete learning experience with AI-powered content generation, 
            interactive quizzes, personalized videos, and intelligent tutoring.
          </p>
          
          {/* Feature highlights */}
          <div className="flex flex-wrap justify-center gap-4 mt-8">
            <Badge variant="outline" className="px-4 py-2 text-sm">
              <Zap className="h-4 w-4 mr-2 text-yellow-500" />
              AI-Powered Content
            </Badge>
            <Badge variant="outline" className="px-4 py-2 text-sm">
              <Target className="h-4 w-4 mr-2 text-green-500" />
              Personalized Learning
            </Badge>
            <Badge variant="outline" className="px-4 py-2 text-sm">
              <Award className="h-4 w-4 mr-2 text-purple-500" />
              Interactive Quizzes
            </Badge>
            <Badge variant="outline" className="px-4 py-2 text-sm">
              <Video className="h-4 w-4 mr-2 text-blue-500" />
              HD Video Generation
            </Badge>
          </div>
        </div>

        {!generatedContent ? (
          // Content Generation Form
          <Card className="max-w-4xl mx-auto shadow-2xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader className="text-center pb-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-t-lg">
              <CardTitle className="text-3xl font-semibold text-slate-800">Create Your Learning Experience</CardTitle>
              <CardDescription className="text-lg text-slate-600 mt-2">
                Tell us what you want to learn and how you learn best. Our AI will create personalized content just for you.
              </CardDescription>
            </CardHeader>
            
            <CardContent className="p-8 space-y-8">
              {/* Topic Input */}
              <div className="space-y-3">
                <Label htmlFor="topic" className="text-base font-semibold text-slate-700">
                  What would you like to learn about? 🎯
                </Label>
                <Input
                  id="topic"
                  placeholder="e.g., Machine Learning, Quantum Physics, Spanish Grammar, Photography..."
                  value={formData.topic}
                  onChange={(e) => handleInputChange("topic", e.target.value)}
                  className="text-base py-4 px-4 border-slate-200 focus:border-blue-500 focus:ring-blue-500/20 bg-white"
                />
                <p className="text-sm text-slate-500">
                  Be specific! The more detailed your topic, the better your personalized content will be.
                </p>
              </div>

              {/* Learning Level */}
              <div className="space-y-3">
                <Label className="text-base font-semibold text-slate-700">
                  What's your current level? 📊
                </Label>
                <Select onValueChange={(value) => handleInputChange("learner_level", value)}>
                  <SelectTrigger className="text-base py-4 border-slate-200 focus:border-blue-500 bg-white">
                    <SelectValue placeholder="Choose your experience level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="beginner">
                      <div className="flex items-center gap-2">
                        <span className="text-green-500">🌱</span>
                        <div>
                          <div className="font-medium">Beginner</div>
                          <div className="text-sm text-slate-500">New to this topic</div>
                        </div>
                      </div>
                    </SelectItem>
                    <SelectItem value="intermediate">
                      <div className="flex items-center gap-2">
                        <span className="text-blue-500">🌿</span>
                        <div>
                          <div className="font-medium">Intermediate</div>
                          <div className="text-sm text-slate-500">Some background knowledge</div>
                        </div>
                      </div>
                    </SelectItem>
                    <SelectItem value="advanced">
                      <div className="flex items-center gap-2">
                        <span className="text-purple-500">🌳</span>
                        <div>
                          <div className="font-medium">Advanced</div>
                          <div className="text-sm text-slate-500">Strong foundation, seeking depth</div>
                        </div>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Learning Style */}
              <div className="space-y-4">
                <Label className="text-base font-semibold text-slate-700">
                  How do you learn best? 🧠
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(learningStyleInfo).map(([key, info]) => (
                    <Card 
                      key={key}
                      className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
                        formData.learning_style === key 
                          ? 'ring-2 ring-blue-500 bg-blue-50' 
                          : 'hover:bg-slate-50'
                      }`}
                      onClick={() => handleInputChange("learning_style", key)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <div className="text-2xl">{info.icon}</div>
                          <div className="flex-1">
                            <div className="font-semibold text-slate-800">{info.title}</div>
                            <p className="text-sm text-slate-600 mb-2">{info.description}</p>
                            <div className="flex flex-wrap gap-1">
                              {info.features.slice(0, 2).map((feature, idx) => (
                                <Badge key={idx} variant="secondary" className="text-xs">
                                  {feature}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>

              {/* Generate Button */}
              <div className="pt-4">
                <Button 
                  onClick={generateContent} 
                  disabled={isGenerating || !formData.topic || !formData.learner_level || !formData.learning_style}
                  className="w-full py-6 text-lg font-semibold bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg transition-all duration-200 transform hover:scale-[1.02] disabled:transform-none"
                >
                  {isGenerating ? (
                    <div className="flex items-center gap-3">
                      <RotateCw className="h-5 w-5 animate-spin" />
                      Creating Your Learning Experience...
                    </div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <Sparkles className="h-5 w-5" />
                      Generate My Learning Experience
                    </div>
                  )}
                </Button>
                
                {!formData.topic && (
                  <p className="text-center text-sm text-slate-500 mt-3">
                    Enter a topic to get started with AI-powered learning
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          // Generated Content Display
          <div className="space-y-8">
            {/* Progress Indicator */}
            <Card className="max-w-5xl mx-auto shadow-lg border-0 bg-white/95 backdrop-blur-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold text-slate-800">Learning Experience Progress</h3>
                  <Button 
                    onClick={resetApp} 
                    variant="outline" 
                    size="sm"
                    className="text-slate-600 hover:text-slate-800"
                  >
                    <RotateCw className="h-4 w-4 mr-2" />
                    Create New Experience
                  </Button>
                </div>
                
                {/* Steps Progress */}
                <div className="flex items-center justify-between mb-4">
                  {steps.map((step, index) => (
                    <div key={index} className="flex items-center">
                      <div className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-colors ${
                        currentStep > index 
                          ? 'bg-green-500 border-green-500 text-white shadow-lg' 
                          : currentStep === index 
                          ? 'bg-blue-500 border-blue-500 text-white animate-pulse shadow-lg' 
                          : 'border-slate-300 text-slate-400 bg-white'
                      }`}>
                        {currentStep > index ? <CheckCircle2 className="h-6 w-6" /> : index + 1}
                      </div>
                      <div className="ml-3">
                        <span className={`text-sm font-medium ${
                          currentStep >= index ? 'text-slate-800' : 'text-slate-400'
                        }`}>
                          {step}
                        </span>
                      </div>
                      {index < steps.length - 1 && (
                        <div className={`w-24 h-1 mx-6 rounded-full ${
                          currentStep > index ? 'bg-green-500' : 'bg-slate-200'
                        }`} />
                      )}
                    </div>
                  ))}
                </div>
                
                {/* Progress Details */}
                {(isGenerating || isGeneratingVideo) && (
                  <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                        <RotateCw className="h-4 w-4 text-white animate-spin" />
                      </div>
                      <div>
                        <p className="font-semibold text-slate-800">
                          {isGeneratingVideo ? "🎬 Creating AI-Powered Video" : "🤖 Generating Content"}
                        </p>
                        <p className="text-sm text-slate-600">
                          {isGeneratingVideo 
                            ? "Using AI to create personalized educational video with narration..." 
                            : "Analyzing your preferences and creating personalized learning materials..."
                          }
                        </p>
                      </div>
                    </div>
                    
                    <Progress 
                      value={isGeneratingVideo ? videoProgress : 75} 
                      className="h-2 mb-2" 
                    />
                    
                    {isGeneratingVideo && (
                      <div className="text-xs text-slate-600 space-y-1">
                        <p>✅ Content generated with learning objectives, quiz, and flashcards</p>
                        <p className={videoProgress > 30 ? "text-green-600" : ""}>
                          {videoProgress > 30 ? "✅" : "⏳"} AI visual scenes created using advanced algorithms
                        </p>
                        <p className={videoProgress > 60 ? "text-green-600" : ""}>
                          {videoProgress > 60 ? "✅" : "⏳"} Professional narration with high-quality TTS
                        </p>
                        <p className={videoProgress > 80 ? "text-green-600" : ""}>
                          {videoProgress > 80 ? "✅" : "⏳"} HD video compilation with animations
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Learning Content */}
            <Card className="max-w-7xl mx-auto shadow-2xl border-0 bg-white/95 backdrop-blur-sm">
              <CardHeader className="text-center pb-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-t-lg">
                <CardTitle className="text-3xl font-bold text-slate-800">
                  📚 {generatedContent.topic}
                </CardTitle>
                <CardDescription className="text-lg text-slate-600 mt-2">
                  Personalized for {generatedContent.learner_level} level • {learningStyleInfo[generatedContent.learning_style]?.title}
                </CardDescription>
                <div className="flex items-center justify-center gap-4 mt-4">
                  <Badge variant="outline" className="px-4 py-2">
                    <Target className="h-4 w-4 mr-2" />
                    {generatedContent.learning_objectives?.length} Learning Objectives
                  </Badge>
                  <Badge variant="outline" className="px-4 py-2">
                    <HelpCircle className="h-4 w-4 mr-2" />
                    {generatedContent.quiz?.length} Quiz Questions
                  </Badge>
                  <Badge variant="outline" className="px-4 py-2">
                    <BookOpen className="h-4 w-4 mr-2" />
                    {generatedContent.flashcards?.length} Study Cards
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="p-0">
                <Tabs defaultValue="objectives" className="w-full">
                  <TabsList className="grid grid-cols-4 w-full bg-slate-100 p-1 rounded-none">
                    <TabsTrigger value="objectives" className="flex items-center gap-2 py-3">
                      <Target className="h-4 w-4" />
                      Objectives
                    </TabsTrigger>
                    <TabsTrigger value="video" className="flex items-center gap-2 py-3">
                      <Video className="h-4 w-4" />
                      AI Video
                    </TabsTrigger>
                    <TabsTrigger value="quiz" className="flex items-center gap-2 py-3">
                      <HelpCircle className="h-4 w-4" />
                      Interactive Quiz
                    </TabsTrigger>
                    <TabsTrigger value="flashcards" className="flex items-center gap-2 py-3">
                      <RotateCw className="h-4 w-4" />
                      Study Cards
                    </TabsTrigger>
                  </TabsList>

                  <div className="p-8">
                    {/* Learning Objectives */}
                    <TabsContent value="objectives" className="space-y-6 mt-0">
                      <div className="text-center mb-6">
                        <h3 className="text-2xl font-semibold text-slate-800 mb-2">🎯 Learning Objectives</h3>
                        <p className="text-slate-600">
                          Clear, measurable goals tailored to your {generatedContent.learner_level} level
                        </p>
                      </div>
                      
                      <div className="grid gap-4 max-w-4xl mx-auto">
                        {generatedContent.learning_objectives?.map((objective, index) => (
                          <Card key={index} className="border-l-4 border-l-blue-500 shadow-sm hover:shadow-md transition-shadow">
                            <CardContent className="p-6">
                              <div className="flex items-start gap-4">
                                <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-full flex items-center justify-center text-lg font-bold">
                                  {index + 1}
                                </div>
                                <div className="flex-1">
                                  <p className="text-lg text-slate-700 leading-relaxed">{objective}</p>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        )) || (
                          <Alert>
                            <AlertDescription>
                              Learning objectives are being generated. Please wait...
                            </AlertDescription>
                          </Alert>
                        )}
                      </div>
                    </TabsContent>

                    {/* AI Video Section */}
                    <TabsContent value="video" className="space-y-6 mt-0">
                      <div className="text-center mb-6">
                        <h3 className="text-2xl font-semibold text-slate-800 mb-2">🎬 AI-Generated Educational Video</h3>
                        <p className="text-slate-600">
                          Personalized video content with professional narration and visual aids
                        </p>
                      </div>
                      
                      {/* AI Features Showcase */}
                      <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                        <div className="flex items-center gap-2 mb-4">
                          <Sparkles className="h-5 w-5 text-blue-600" />
                          <h4 className="font-semibold text-blue-800">AI-Powered Video Features</h4>
                        </div>
                        <div className="grid md:grid-cols-2 gap-4 text-sm">
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-blue-700">
                              <CheckCircle2 className="h-4 w-4 text-green-500" />
                              AI-generated visual scenes using advanced LLM
                            </div>
                            <div className="flex items-center gap-2 text-blue-700">
                              <CheckCircle2 className="h-4 w-4 text-green-500" />
                              Professional narration with high-quality TTS
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-blue-700">
                              <CheckCircle2 className="h-4 w-4 text-green-500" />
                              Smooth transitions and animations
                            </div>
                            <div className="flex items-center gap-2 text-blue-700">
                              <CheckCircle2 className="h-4 w-4 text-green-500" />
                              1080p HD quality at 30fps
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Video Player */}
                      {videoUrl ? (
                        <div className="aspect-video bg-slate-900 rounded-xl overflow-hidden shadow-2xl max-w-4xl mx-auto">
                          <video 
                            controls 
                            className="w-full h-full object-cover"
                            poster="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTkyMCIgaGVpZ2h0PSIxMDgwIiB2aWV3Qm94PSIwIDAgMTkyMCAxMDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8ZGVmcz4KPGxpbmVhckdyYWRpZW50IGlkPSJiZyIgeDE9IjAlIiB5MT0iMCUiIHgyPSIwJSIgeTI9IjEwMCUiPgo8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojMGYxNzJhO3N0b3Atb3BhY2l0eToxIiAvPgo8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiMyZDM3NTI7c3RvcC1vcGFjaXR5OjEiIC8+CjwvbGluZWFyR3JhZGllbnQ+CjwvZGVmcz4KPHJlY3Qgd2lkdGg9IjE5MjAiIGhlaWdodD0iMTA4MCIgZmlsbD0idXJsKCNiZykiLz4KPGNpcmNsZSBjeD0iOTYwIiBjeT0iNTQwIiByPSI4MCIgZmlsbD0id2hpdGUiIGZpbGwtb3BhY2l0eT0iMC45Ii8+Cjxwb2x5Z29uIHBvaW50cz0iOTIwLDUwMCAxMDIwLDU0MCA5MjAsNTgwIiBmaWxsPSIjMGYxNzJhIi8+Cjx0ZXh0IHg9Ijk2MCIgeT0iNjYwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSJ3aGl0ZSIgZm9udC1zaXplPSI0OCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iYm9sZCI+RURVRE9SR0UgQUkgVklERU88L3RleHQ+Cjx0ZXh0IHg9Ijk2MCIgeT0iNzIwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjOWNhM2FmIiBmb250LXNpemU9IjMyIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiPkFJLUdlbmVyYXRlZCBFZHVjYXRpb25hbCBDb250ZW50PC90ZXh0Pgo8L3N2Zz4K"
                          >
                            <source src={videoUrl} type="video/mp4" />
                            Your browser does not support the video tag.
                          </video>
                        </div>
                      ) : isGeneratingVideo ? (
                        <div className="aspect-video bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 rounded-xl flex items-center justify-center relative overflow-hidden max-w-4xl mx-auto">
                          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 animate-pulse"></div>
                          <div className="text-center z-10 p-8">
                            <div className="w-20 h-20 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
                            <h4 className="text-2xl font-bold text-white mb-4">Creating Your AI Video</h4>
                            <div className="space-y-2 text-blue-200">
                              <p className="font-medium">🤖 Generating AI visual scenes...</p>
                              <p className="font-medium">🎙️ Creating professional narration...</p>
                              <p className="font-medium">🎬 Adding animations & transitions...</p>
                            </div>
                            <div className="w-80 bg-slate-700 rounded-full h-3 mx-auto mt-6">
                              <div 
                                className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-300" 
                                style={{width: `${videoProgress}%`}}
                              ></div>
                            </div>
                            <p className="text-xs text-slate-300 mt-3">
                              This may take 1-2 minutes for optimal quality ({Math.round(videoProgress)}% complete)
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="aspect-video bg-slate-100 rounded-xl flex items-center justify-center max-w-4xl mx-auto">
                          <div className="text-center p-8">
                            <Video className="h-16 w-16 text-slate-400 mx-auto mb-4" />
                            <p className="text-slate-500 text-lg">Enhanced video generation in progress...</p>
                            <p className="text-slate-400 text-sm mt-2">Your personalized video will appear here</p>
                          </div>
                        </div>
                      )}

                      {/* Video Script Preview */}
                      {generatedContent.video_script && (
                        <div className="mt-8 max-w-4xl mx-auto">
                          <h4 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                            <BookOpen className="h-5 w-5" />
                            📝 Generated Video Script
                          </h4>
                          <Card className="bg-slate-50 border">
                            <CardContent className="p-6">
                              <div className="prose prose-slate max-w-none">
                                <div className="text-slate-700 leading-relaxed whitespace-pre-line font-mono text-sm">
                                  {generatedContent.video_script}
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        </div>
                      )}
                    </TabsContent>

                    {/* Interactive Quiz */}
                    <TabsContent value="quiz" className="space-y-6 mt-0">
                      <div className="text-center mb-6">
                        <h3 className="text-2xl font-semibold text-slate-800 mb-2">🧠 Interactive Knowledge Check</h3>
                        <p className="text-slate-600">
                          Test your understanding with these personalized questions
                        </p>
                        {generatedContent.quiz?.length > 0 && (
                          <div className="flex items-center justify-center gap-4 mt-4">
                            <Badge variant="outline" className="px-3 py-1">
                              <Clock className="h-4 w-4 mr-1" />
                              ~{generatedContent.quiz.length * 2} minutes
                            </Badge>
                            <Badge variant="outline" className="px-3 py-1">
                              <TrendingUp className="h-4 w-4 mr-1" />
                              {generatedContent.learner_level} level
                            </Badge>
                          </div>
                        )}
                      </div>

                      {/* Quiz Progress */}
                      {generatedContent.quiz?.length > 0 && (
                        <div className="mb-6 max-w-2xl mx-auto">
                          <div className="flex items-center justify-between text-sm text-slate-600 mb-2">
                            <span>Progress</span>
                            <span>{Object.keys(quizAnswers).length}/{generatedContent.quiz.length} answered</span>
                          </div>
                          <Progress 
                            value={(Object.keys(quizAnswers).length / generatedContent.quiz.length) * 100} 
                            className="h-2"
                          />
                        </div>
                      )}

                      {/* Quiz Questions */}
                      <div className="space-y-6 max-w-4xl mx-auto">
                        {generatedContent.quiz?.map((question, qIndex) => (
                          <Card key={question.id || qIndex} className="border shadow-sm">
                            <CardHeader className="pb-4">
                              <div className="flex items-start gap-3">
                                <div className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-semibold text-sm">
                                  {qIndex + 1}
                                </div>
                                <CardTitle className="text-lg text-slate-800 leading-relaxed">
                                  {question.question}
                                </CardTitle>
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-3">
                              {question.options?.map((option, oIndex) => (
                                <div key={oIndex}>
                                  <button
                                    onClick={() => !showQuizResults && handleQuizAnswer(question.id || `q_${qIndex}`, oIndex)}
                                    disabled={showQuizResults}
                                    className={`w-full text-left p-4 rounded-lg border transition-all duration-200 ${
                                      showQuizResults
                                        ? oIndex === question.correct_answer
                                          ? 'bg-green-100 border-green-300 text-green-800 shadow-sm'
                                          : quizAnswers[question.id || `q_${qIndex}`] === oIndex && oIndex !== question.correct_answer
                                          ? 'bg-red-100 border-red-300 text-red-800'
                                          : 'bg-slate-50 border-slate-200 text-slate-600'
                                        : quizAnswers[question.id || `q_${qIndex}`] === oIndex
                                        ? 'bg-blue-100 border-blue-300 text-blue-800 shadow-sm'
                                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300'
                                    }`}
                                  >
                                    <div className="flex items-center gap-3">
                                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center text-sm font-semibold ${
                                        showQuizResults && oIndex === question.correct_answer
                                          ? 'bg-green-500 text-white border-green-500'
                                          : showQuizResults && quizAnswers[question.id || `q_${qIndex}`] === oIndex && oIndex !== question.correct_answer
                                          ? 'bg-red-500 text-white border-red-500'
                                          : quizAnswers[question.id || `q_${qIndex}`] === oIndex
                                          ? 'bg-blue-500 text-white border-blue-500'
                                          : 'border-slate-300'
                                      }`}>
                                        {String.fromCharCode(65 + oIndex)}
                                      </div>
                                      <span className="leading-relaxed">{option}</span>
                                    </div>
                                  </button>
                                </div>
                              )) || []}

                              {/* Show hint if not answered yet */}
                              {!showQuizResults && 
                               quizAnswers[question.id || `q_${qIndex}`] === undefined && 
                               question.hint && (
                                <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                                  <div className="flex items-start gap-2">
                                    <Lightbulb className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
                                    <div>
                                      <p className="text-sm font-medium text-blue-800">Hint:</p>
                                      <p className="text-sm text-blue-700">{question.hint}</p>
                                    </div>
                                  </div>
                                </div>
                              )}

                              {/* Show explanation after quiz submission */}
                              {showQuizResults && question.explanation && (
                                <div className="mt-4 p-4 bg-slate-50 rounded-lg border">
                                  <div className="flex items-start gap-2">
                                    <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                                    <div>
                                      <p className="text-sm font-semibold text-slate-800 mb-1">Explanation:</p>
                                      <p className="text-sm text-slate-700 leading-relaxed">{question.explanation}</p>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        )) || (
                          <Alert>
                            <AlertDescription>
                              Interactive quiz questions are being generated based on your learning preferences...
                            </AlertDescription>
                          </Alert>
                        )}

                        {/* Submit Quiz Button */}
                        {!showQuizResults && 
                         generatedContent.quiz?.length > 0 && 
                         Object.keys(quizAnswers).length === generatedContent.quiz.length && (
                          <div className="text-center pt-4">
                            <Button 
                              onClick={submitQuiz} 
                              className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 px-8 py-3 text-lg font-semibold shadow-lg"
                            >
                              <Award className="h-5 w-5 mr-2" />
                              Submit Quiz & Get Results
                            </Button>
                          </div>
                        )}

                        {/* Quiz Results Summary */}
                        {showQuizResults && generatedContent.quiz?.length > 0 && (
                          <Card className="bg-gradient-to-r from-blue-50 to-green-50 border-blue-200">
                            <CardContent className="p-6 text-center">
                              <div className="flex items-center justify-center gap-2 mb-3">
                                <Award className="h-6 w-6 text-blue-600" />
                                <h4 className="text-lg font-semibold text-slate-800">Quiz Complete!</h4>
                              </div>
                              <p className="text-slate-600 mb-4">
                                You've completed the knowledge check. Review the explanations above to reinforce your learning.
                              </p>
                              <div className="flex items-center justify-center gap-4">
                                <Badge variant="outline" className="px-4 py-2">
                                  <Users className="h-4 w-4 mr-1" />
                                  {Object.keys(quizAnswers).length} Questions Answered
                                </Badge>
                                <Badge variant="outline" className="px-4 py-2">
                                  <TrendingUp className="h-4 w-4 mr-1" />
                                  Learning Progress Updated
                                </Badge>
                              </div>
                            </CardContent>
                          </Card>
                        )}
                      </div>
                    </TabsContent>

                    {/* Study Flashcards */}
                    <TabsContent value="flashcards" className="space-y-6 mt-0">
                      <div className="text-center mb-6">
                        <h3 className="text-2xl font-semibold text-slate-800 mb-2">🎴 Interactive Study Cards</h3>
                        <p className="text-slate-600 mb-4">
                          Master key concepts with these personalized flashcards. Click any card to reveal the answer.
                        </p>
                        <Badge variant="outline" className="px-4 py-2">
                          <RotateCw className="h-4 w-4 mr-2" />
                          {generatedContent.flashcards?.length || 0} Study Cards
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
                        {generatedContent.flashcards?.map((card, index) => (
                          <div key={card.id || index} className="relative h-48">
                            <div 
                              onClick={() => toggleFlashcard(card.id || `card_${index}`)}
                              className={`w-full h-full cursor-pointer transition-transform duration-500 transform-style-preserve-3d ${
                                flippedCards.has(card.id || `card_${index}`) ? 'rotate-y-180' : ''
                              }`}
                              style={{ transformStyle: 'preserve-3d' }}
                            >
                              {/* Front of card */}
                              <div className="absolute inset-0 backface-hidden bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-xl p-6 flex items-center justify-center shadow-xl">
                                <div className="text-center">
                                  <div className="text-xs opacity-80 mb-2 font-medium">Card {index + 1}</div>
                                  <div className="font-semibold text-lg leading-relaxed mb-4">{card.front}</div>
                                  <div className="text-xs opacity-70">Click to reveal answer</div>
                                </div>
                              </div>
                              
                              {/* Back of card */}
                              <div 
                                className="absolute inset-0 backface-hidden bg-gradient-to-br from-green-500 to-teal-600 text-white rounded-xl p-6 flex items-center justify-center shadow-xl rotate-y-180"
                                style={{ transform: 'rotateY(180deg)' }}
                              >
                                <div className="text-center">
                                  <div className="text-xs opacity-80 mb-2 font-medium">Answer</div>
                                  <div className="font-medium text-lg leading-relaxed mb-4">{card.back}</div>
                                  <div className="text-xs opacity-70">Click to flip back</div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )) || (
                          <div className="col-span-full">
                            <Alert>
                              <AlertDescription>
                                Personalized flashcards are being created to help you master the key concepts...
                              </AlertDescription>
                            </Alert>
                          </div>
                        )}
                      </div>

                      {/* Flashcard Instructions */}
                      {generatedContent.flashcards?.length > 0 && (
                        <Card className="max-w-2xl mx-auto bg-slate-50 border-slate-200 mt-8">
                          <CardContent className="p-6 text-center">
                            <h4 className="font-semibold text-slate-800 mb-2">💡 Study Tips</h4>
                            <p className="text-sm text-slate-600 leading-relaxed">
                              For effective studying: Read the question, try to answer it mentally, then click to check. 
                              Review cards you got wrong multiple times. Active recall strengthens memory retention!
                            </p>
                          </CardContent>
                        </Card>
                      )}
                    </TabsContent>
                  </div>
                </Tabs>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Floating Chatbot */}
      <ChatBot 
        currentTopic={generatedContent?.topic}
        learningStyle={generatedContent?.learning_style}
        learnerLevel={generatedContent?.learner_level}
      />
    </div>
  );
}

export default App;