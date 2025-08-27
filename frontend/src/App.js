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
  Sparkles,
  Target,
  Clock,
  Users,
  TrendingUp,
  Award,
  Zap,
  Lightbulb,
  X
} from "lucide-react";
import { toast, Toaster } from "sonner";
import ChatBot from "./components/ChatBot";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [formData, setFormData] = useState({
    topic: "",
    learner_level: ""
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
  const [quizScore, setQuizScore] = useState(null);
  const [canRetakeQuiz, setCanRetakeQuiz] = useState(false);

  const steps = ["Content Generation", "Video Creation", "Ready to Learn"];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const generateContent = async () => {
    if (!formData.topic || !formData.learner_level) {
      toast.error("Please fill in all fields to create your learning experience");
      return;
    }

    setIsGenerating(true);
    setCurrentStep(0);
    setVideoProgress(0);
    
    try {
      toast.info("🚀 Generating your personalized learning content...");
      
      const requestData = {
        ...formData,
        learning_style: "comprehensive"  // Default style since we removed selection
      };
      
      const response = await axios.post(`${API}/generate_content`, requestData);
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
      
      toast.success("🎬 Your educational video is ready!");
      
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
    const correctAnswers = generatedContent.quiz.filter(
      (q) => quizAnswers[q.id] === q.correct_answer
    ).length;
    
    const totalQuestions = generatedContent.quiz.length;
    const percentage = Math.round((correctAnswers / totalQuestions) * 100);
    
    setQuizScore({ correct: correctAnswers, total: totalQuestions, percentage });
    setShowQuizResults(true);
    
    if (percentage >= 70) {
      toast.success(`🎉 Excellent! You scored ${correctAnswers}/${totalQuestions} (${percentage}%)`);
      setCanRetakeQuiz(false);
    } else {
      toast.error(`📚 You scored ${correctAnswers}/${totalQuestions} (${percentage}%). Review the explanations and try again!`);
      setCanRetakeQuiz(true);
    }
  };

  const retakeQuiz = () => {
    setQuizAnswers({});
    setShowQuizResults(false);
    setQuizScore(null);
    setCanRetakeQuiz(false);
    toast.info("Quiz reset! Try again with the knowledge you've gained.");
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
    setFormData({ topic: "", learner_level: "" });
    setGeneratedContent(null);
    setCurrentStep(0);
    setQuizAnswers({});
    setShowQuizResults(false);
    setFlippedCards(new Set());
    setVideoUrl(null);
    setIsGeneratingVideo(false);
    setVideoProgress(0);
    setQuizScore(null);
    setCanRetakeQuiz(false);
    
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
    <div className="min-h-screen w-full bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      <Toaster position="top-center" expand={true} richColors />
      
      <div className="w-full px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
        {/* Header */}
        <div className="text-center mb-8 lg:mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="relative">
              <Brain className="h-10 w-10 lg:h-12 lg:w-12 text-blue-600" />
              <Sparkles className="h-4 w-4 lg:h-5 lg:w-5 text-purple-500 absolute -top-1 -right-1" />
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
              EduForge AI
            </h1>
          </div>
          <p className="text-lg lg:text-xl text-slate-600 max-w-4xl mx-auto leading-relaxed mb-6">
            Transform any topic into a complete learning experience with AI-powered content generation, 
            interactive quizzes, personalized videos, and intelligent tutoring.
          </p>
          
          {/* Feature highlights */}
          <div className="flex flex-wrap justify-center gap-2 lg:gap-4 mt-6 lg:mt-8">
            <Badge variant="outline" className="px-3 py-1 lg:px-4 lg:py-2 text-xs lg:text-sm">
              <Zap className="h-3 w-3 lg:h-4 lg:w-4 mr-2 text-yellow-500" />
              AI-Powered Content
            </Badge>
            <Badge variant="outline" className="px-3 py-1 lg:px-4 lg:py-2 text-xs lg:text-sm">
              <Target className="h-3 w-3 lg:h-4 lg:w-4 mr-2 text-green-500" />
              Personalized Learning
            </Badge>
            <Badge variant="outline" className="px-3 py-1 lg:px-4 lg:py-2 text-xs lg:text-sm">
              <Award className="h-3 w-3 lg:h-4 lg:w-4 mr-2 text-purple-500" />
              Interactive Quizzes
            </Badge>
            <Badge variant="outline" className="px-3 py-1 lg:px-4 lg:py-2 text-xs lg:text-sm">
              <Video className="h-3 w-3 lg:h-4 lg:w-4 mr-2 text-blue-500" />
              HD Video Generation
            </Badge>
          </div>
        </div>

        {!generatedContent ? (
          // Content Generation Form
          <Card className="w-full max-w-4xl mx-auto shadow-2xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader className="text-center pb-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-t-lg">
              <CardTitle className="text-2xl lg:text-3xl font-semibold text-slate-800">Create Your Learning Experience</CardTitle>
              <CardDescription className="text-base lg:text-lg text-slate-600 mt-2">
                Tell us what you want to learn. Our AI will create comprehensive educational content just for you.
              </CardDescription>
            </CardHeader>
            
            <CardContent className="p-6 lg:p-8 space-y-6 lg:space-y-8">
              {/* Topic Input */}
              <div className="space-y-3">
                <Label htmlFor="topic" className="text-base font-semibold text-slate-700">
                  What would you like to learn about? 🎯
                </Label>
                <Input
                  id="topic"
                  placeholder="e.g., Machine Learning, Quantum Physics, Spanish Grammar, Photography, Data Science..."
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

              {/* Generate Button */}
              <div className="pt-4">
                <Button 
                  onClick={generateContent} 
                  disabled={isGenerating || !formData.topic || !formData.learner_level}
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
          <div className="w-full space-y-6 lg:space-y-8">
            {/* Progress Indicator */}
            <Card className="w-full shadow-lg border-0 bg-white/95 backdrop-blur-sm">
              <CardContent className="p-4 lg:p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-4">
                  <h3 className="text-lg lg:text-xl font-semibold text-slate-800">Learning Experience Progress</h3>
                  <Button 
                    onClick={resetApp} 
                    variant="outline" 
                    size="sm"
                    className="text-slate-600 hover:text-slate-800 w-full sm:w-auto"
                  >
                    <RotateCw className="h-4 w-4 mr-2" />
                    Create New Experience
                  </Button>
                </div>
                
                {/* Steps Progress */}
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-4 space-y-4 lg:space-y-0">
                  {steps.map((step, index) => (
                    <div key={index} className="flex items-center">
                      <div className={`flex items-center justify-center w-10 h-10 lg:w-12 lg:h-12 rounded-full border-2 transition-colors ${
                        currentStep > index 
                          ? 'bg-green-500 border-green-500 text-white shadow-lg' 
                          : currentStep === index 
                          ? 'bg-blue-500 border-blue-500 text-white animate-pulse shadow-lg' 
                          : 'border-slate-300 text-slate-400 bg-white'
                      }`}>
                        {currentStep > index ? <CheckCircle2 className="h-5 w-5 lg:h-6 lg:w-6" /> : index + 1}
                      </div>
                      <div className="ml-3">
                        <span className={`text-sm lg:text-base font-medium ${
                          currentStep >= index ? 'text-slate-800' : 'text-slate-400'
                        }`}>
                          {step}
                        </span>
                      </div>
                      {index < steps.length - 1 && (
                        <div className={`hidden lg:block w-20 xl:w-24 h-1 mx-6 rounded-full ${
                          currentStep > index ? 'bg-green-500' : 'bg-slate-200'
                        }`} />
                      )}
                    </div>
                  ))}
                </div>
                
                {/* Progress Details */}
                {(isGenerating || isGeneratingVideo) && (
                  <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                    <div className="flex items-start gap-3 mb-3">
                      <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                        <RotateCw className="h-4 w-4 text-white animate-spin" />
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-slate-800">
                          {isGeneratingVideo ? "🎬 Creating Educational Video" : "🤖 Generating Content"}
                        </p>
                        <p className="text-sm text-slate-600">
                          {isGeneratingVideo 
                            ? "Creating personalized educational video with narration..." 
                            : "Analyzing your topic and creating comprehensive learning materials..."
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
                          {videoProgress > 30 ? "✅" : "⏳"} Video scenes created
                        </p>
                        <p className={videoProgress > 60 ? "text-green-600" : ""}>
                          {videoProgress > 60 ? "✅" : "⏳"} Audio narration generated
                        </p>
                        <p className={videoProgress > 80 ? "text-green-600" : ""}>
                          {videoProgress > 80 ? "✅" : "⏳"} HD video compilation complete
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Learning Content */}
            <Card className="w-full shadow-2xl border-0 bg-white/95 backdrop-blur-sm">
              <CardHeader className="text-center pb-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-t-lg">
                <CardTitle className="text-2xl lg:text-3xl font-bold text-slate-800">
                  📚 {generatedContent.topic}
                </CardTitle>
                <CardDescription className="text-base lg:text-lg text-slate-600 mt-2">
                  Personalized for {generatedContent.learner_level} level learners
                </CardDescription>
                <div className="flex flex-wrap items-center justify-center gap-2 lg:gap-4 mt-4">
                  <Badge variant="outline" className="px-3 py-1 lg:px-4 lg:py-2 text-xs lg:text-sm">
                    <Target className="h-3 w-3 lg:h-4 lg:w-4 mr-2" />
                    {generatedContent.learning_objectives?.length} Learning Objectives
                  </Badge>
                  <Badge variant="outline" className="px-3 py-1 lg:px-4 lg:py-2 text-xs lg:text-sm">
                    <HelpCircle className="h-3 w-3 lg:h-4 lg:w-4 mr-2" />
                    {generatedContent.quiz?.length} Quiz Questions
                  </Badge>
                  <Badge variant="outline" className="px-3 py-1 lg:px-4 lg:py-2 text-xs lg:text-sm">
                    <BookOpen className="h-3 w-3 lg:h-4 lg:w-4 mr-2" />
                    {generatedContent.flashcards?.length} Study Cards
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="p-0">
                <Tabs defaultValue="objectives" className="w-full">
                  <TabsList className="grid grid-cols-4 w-full bg-slate-100 p-1 rounded-none">
                    <TabsTrigger value="objectives" className="flex items-center gap-1 lg:gap-2 py-2 lg:py-3 text-xs lg:text-sm">
                      <Target className="h-3 w-3 lg:h-4 lg:w-4" />
                      <span className="hidden sm:inline">Objectives</span>
                    </TabsTrigger>
                    <TabsTrigger value="video" className="flex items-center gap-1 lg:gap-2 py-2 lg:py-3 text-xs lg:text-sm">
                      <Video className="h-3 w-3 lg:h-4 lg:w-4" />
                      <span className="hidden sm:inline">Video</span>
                    </TabsTrigger>
                    <TabsTrigger value="quiz" className="flex items-center gap-1 lg:gap-2 py-2 lg:py-3 text-xs lg:text-sm">
                      <HelpCircle className="h-3 w-3 lg:h-4 lg:w-4" />
                      <span className="hidden sm:inline">Quiz</span>
                    </TabsTrigger>
                    <TabsTrigger value="flashcards" className="flex items-center gap-1 lg:gap-2 py-2 lg:py-3 text-xs lg:text-sm">
                      <RotateCw className="h-3 w-3 lg:h-4 lg:w-4" />
                      <span className="hidden sm:inline">Cards</span>
                    </TabsTrigger>
                  </TabsList>

                  <div className="p-4 lg:p-8">
                    {/* Learning Objectives */}
                    <TabsContent value="objectives" className="space-y-4 lg:space-y-6 mt-0">
                      <div className="text-center mb-4 lg:mb-6">
                        <h3 className="text-xl lg:text-2xl font-semibold text-slate-800 mb-2">🎯 Learning Objectives</h3>
                        <p className="text-sm lg:text-base text-slate-600">
                          Clear, measurable goals tailored to your {generatedContent.learner_level} level
                        </p>
                      </div>
                      
                      <div className="grid gap-3 lg:gap-4 w-full">
                        {generatedContent.learning_objectives?.map((objective, index) => (
                          <Card key={index} className="border-l-4 border-l-blue-500 shadow-sm hover:shadow-md transition-shadow">
                            <CardContent className="p-4 lg:p-6">
                              <div className="flex items-start gap-3 lg:gap-4">
                                <div className="flex-shrink-0 w-8 h-8 lg:w-10 lg:h-10 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-full flex items-center justify-center text-sm lg:text-lg font-bold">
                                  {index + 1}
                                </div>
                                <div className="flex-1">
                                  <p className="text-base lg:text-lg text-slate-700 leading-relaxed">{objective}</p>
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

                    {/* Video Section */}
                    <TabsContent value="video" className="space-y-4 lg:space-y-6 mt-0">
                      <div className="text-center mb-4 lg:mb-6">
                        <h3 className="text-xl lg:text-2xl font-semibold text-slate-800 mb-2">🎬 Educational Video</h3>
                        <p className="text-sm lg:text-base text-slate-600">
                          AI-generated video content with professional narration
                        </p>
                      </div>
                      
                      {/* Video Player */}
                      {videoUrl ? (
                        <div className="aspect-video bg-slate-900 rounded-lg lg:rounded-xl overflow-hidden shadow-2xl w-full">
                          <video 
                            controls 
                            className="w-full h-full object-cover"
                          >
                            <source src={videoUrl} type="video/mp4" />
                            Your browser does not support the video tag.
                          </video>
                        </div>
                      ) : isGeneratingVideo ? (
                        <div className="aspect-video bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 rounded-lg lg:rounded-xl flex items-center justify-center relative overflow-hidden w-full">
                          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 animate-pulse"></div>
                          <div className="text-center z-10 p-4 lg:p-8">
                            <div className="w-16 h-16 lg:w-20 lg:h-20 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-4 lg:mb-6"></div>
                            <h4 className="text-lg lg:text-2xl font-bold text-white mb-2 lg:mb-4">Creating Your Video</h4>
                            <div className="space-y-1 lg:space-y-2 text-blue-200 text-sm lg:text-base">
                              <p>🤖 Generating educational content...</p>
                              <p>🎙️ Creating narration...</p>
                              <p>🎬 Compiling video...</p>
                            </div>
                            <div className="w-48 lg:w-80 bg-slate-700 rounded-full h-2 lg:h-3 mx-auto mt-4 lg:mt-6">
                              <div 
                                className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 lg:h-3 rounded-full transition-all duration-300" 
                                style={{width: `${videoProgress}%`}}
                              ></div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="aspect-video bg-slate-100 rounded-lg lg:rounded-xl flex items-center justify-center w-full">
                          <div className="text-center p-4 lg:p-8">
                            <Video className="h-12 w-12 lg:h-16 lg:w-16 text-slate-400 mx-auto mb-4" />
                            <p className="text-slate-500 text-base lg:text-lg">Video will appear here once generated</p>
                          </div>
                        </div>
                      )}
                    </TabsContent>

                    {/* Interactive Quiz */}
                    <TabsContent value="quiz" className="space-y-4 lg:space-y-6 mt-0">
                      <div className="text-center mb-4 lg:mb-6">
                        <h3 className="text-xl lg:text-2xl font-semibold text-slate-800 mb-2">🧠 Knowledge Check</h3>
                        <p className="text-sm lg:text-base text-slate-600">
                          Test your understanding with these questions about {generatedContent.topic}
                        </p>
                      </div>

                      {/* Quiz Progress */}
                      {generatedContent.quiz?.length > 0 && (
                        <div className="mb-4 lg:mb-6">
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
                      <div className="space-y-4 lg:space-y-6 w-full">
                        {generatedContent.quiz?.map((question, qIndex) => (
                          <Card key={question.id || qIndex} className="border shadow-sm">
                            <CardHeader className="pb-4">
                              <div className="flex items-start gap-3">
                                <div className="flex-shrink-0 w-6 h-6 lg:w-8 lg:h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-semibold text-xs lg:text-sm">
                                  {qIndex + 1}
                                </div>
                                <CardTitle className="text-base lg:text-lg text-slate-800 leading-relaxed">
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
                                    className={`w-full text-left p-3 lg:p-4 rounded-lg border transition-all duration-200 ${
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
                                      <div className={`w-5 h-5 lg:w-6 lg:h-6 rounded-full border-2 flex items-center justify-center text-xs lg:text-sm font-semibold ${
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
                                      <span className="leading-relaxed text-sm lg:text-base">{option}</span>
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
                              Quiz questions are being generated based on the topic...
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
                              className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 px-6 lg:px-8 py-2 lg:py-3 text-base lg:text-lg font-semibold shadow-lg w-full sm:w-auto"
                            >
                              <Award className="h-4 w-4 lg:h-5 lg:w-5 mr-2" />
                              Submit Quiz
                            </Button>
                          </div>
                        )}

                        {/* Quiz Results */}
                        {showQuizResults && quizScore && (
                          <Card className={`${
                            quizScore.percentage >= 70 
                              ? 'bg-gradient-to-r from-green-50 to-blue-50 border-green-200' 
                              : 'bg-gradient-to-r from-red-50 to-orange-50 border-red-200'
                          }`}>
                            <CardContent className="p-4 lg:p-6 text-center">
                              <div className="flex items-center justify-center gap-2 mb-3">
                                <Award className={`h-5 w-5 lg:h-6 lg:w-6 ${
                                  quizScore.percentage >= 70 ? 'text-green-600' : 'text-red-600'
                                }`} />
                                <h4 className="text-lg font-semibold text-slate-800">Quiz Results</h4>
                              </div>
                              <p className="text-2xl lg:text-3xl font-bold mb-2">
                                {quizScore.correct}/{quizScore.total} ({quizScore.percentage}%)
                              </p>
                              <p className={`text-sm lg:text-base mb-4 ${
                                quizScore.percentage >= 70 ? 'text-green-700' : 'text-red-700'
                              }`}>
                                {quizScore.percentage >= 70 
                                  ? "Excellent work! You've mastered this topic." 
                                  : "Keep studying! Review the explanations above."
                                }
                              </p>
                              {canRetakeQuiz && (
                                <Button 
                                  onClick={retakeQuiz}
                                  variant="outline"
                                  className="bg-white hover:bg-slate-50"
                                >
                                  <RotateCw className="h-4 w-4 mr-2" />
                                  Retake Quiz
                                </Button>
                              )}
                            </CardContent>
                          </Card>
                        )}
                      </div>
                    </TabsContent>

                    {/* Study Flashcards */}
                    <TabsContent value="flashcards" className="space-y-4 lg:space-y-6 mt-0">
                      <div className="text-center mb-4 lg:mb-6">
                        <h3 className="text-xl lg:text-2xl font-semibold text-slate-800 mb-2">🎴 Study Cards</h3>
                        <p className="text-sm lg:text-base text-slate-600 mb-4">
                          Master key concepts about {generatedContent.topic}. Click any card to flip it.
                        </p>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 lg:gap-6 w-full">
                        {generatedContent.flashcards?.map((card, index) => (
                          <div key={card.id || index} className="relative h-48 lg:h-56">
                            <div 
                              onClick={() => toggleFlashcard(card.id || `card_${index}`)}
                              className={`w-full h-full cursor-pointer transition-transform duration-500 transform-style-preserve-3d ${
                                flippedCards.has(card.id || `card_${index}`) ? 'rotate-y-180' : ''
                              }`}
                              style={{ transformStyle: 'preserve-3d' }}
                            >
                              {/* Front of card */}
                              <div className="absolute inset-0 backface-hidden bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-xl p-4 lg:p-6 flex items-center justify-center shadow-xl">
                                <div className="text-center">
                                  <div className="text-xs opacity-80 mb-2 font-medium">Card {index + 1}</div>
                                  <div className="font-semibold text-base lg:text-lg leading-relaxed mb-4">{card.front}</div>
                                  <div className="text-xs opacity-70">Click to reveal answer</div>
                                </div>
                              </div>
                              
                              {/* Back of card */}
                              <div 
                                className="absolute inset-0 backface-hidden bg-gradient-to-br from-green-500 to-teal-600 text-white rounded-xl p-4 lg:p-6 flex items-center justify-center shadow-xl rotate-y-180"
                                style={{ transform: 'rotateY(180deg)' }}
                              >
                                <div className="text-center">
                                  <div className="text-xs opacity-80 mb-2 font-medium">Answer</div>
                                  <div className="font-medium text-base lg:text-lg leading-relaxed mb-4">{card.back}</div>
                                  <div className="text-xs opacity-70">Click to flip back</div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )) || (
                          <div className="col-span-full">
                            <Alert>
                              <AlertDescription>
                                Study cards are being created to help you master the concepts...
                              </AlertDescription>
                            </Alert>
                          </div>
                        )}
                      </div>
                    </TabsContent>
                  </div>
                </Tabs>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Enhanced Chatbot with better positioning */}
      <div style={{ position: 'fixed', bottom: '20px', right: '20px', zIndex: 9999 }}>
        <ChatBot 
          currentTopic={generatedContent?.topic}
          learningStyle="comprehensive"
          learnerLevel={generatedContent?.learner_level}
        />
      </div>
    </div>
  );
}

export default App;