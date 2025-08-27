import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Textarea } from "./components/ui/textarea";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Progress } from "./components/ui/progress";
import { CheckCircle2, Brain, BookOpen, Video, HelpCircle, RotateCw, Play, Pause, Volume2 } from "lucide-react";
import { toast } from "sonner";

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

  const steps = ["Content Generation", "Video Creation", "Ready to Learn"];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const generateContent = async () => {
    if (!formData.topic || !formData.learner_level || !formData.learning_style) {
      toast.error("Please fill in all fields");
      return;
    }

    setIsGenerating(true);
    setCurrentStep(0);
    
    try {
      const response = await axios.post(`${API}/generate_content`, formData);
      setGeneratedContent(response.data);
      setCurrentStep(1);
      
      // Generate video
      await generateVideo(response.data.id);
      
    } catch (error) {
      console.error("Error generating content:", error);
      toast.error("Failed to generate content. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  const generateVideo = async (contentId) => {
    setIsGeneratingVideo(true);
    try {
      const response = await axios.post(`${API}/generate_video`, 
        { content_id: contentId },
        { responseType: 'blob' }
      );
      
      const videoBlob = new Blob([response.data], { type: 'video/mp4' });
      const videoUrl = URL.createObjectURL(videoBlob);
      setVideoUrl(videoUrl);
      setCurrentStep(2);
      toast.success("Content and video generated successfully!");
    } catch (error) {
      console.error("Error generating video:", error);
      toast.error("Failed to generate video");
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
      (q, index) => quizAnswers[q.id] === q.correct_answer
    ).length;
    
    toast.success(`Quiz completed! You got ${correctAnswers}/${generatedContent.quiz.length} correct.`);
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
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Brain className="h-10 w-10 text-blue-600" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
              EduForge AI
            </h1>
          </div>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Transform any topic into a complete learning experience with AI-powered content generation, interactive quizzes, and personalized videos.
          </p>
        </div>

        {!generatedContent ? (
          // Content Generation Form
          <Card className="max-w-2xl mx-auto shadow-xl border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader className="text-center pb-6">
              <CardTitle className="text-2xl font-semibold text-slate-800">Create Your Learning Experience</CardTitle>
              <CardDescription className="text-lg text-slate-600">
                Tell us what you want to learn and how you learn best
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="topic" className="text-sm font-medium text-slate-700">Learning Topic</Label>
                <Input
                  id="topic"
                  placeholder="e.g., Photosynthesis, Machine Learning, French Grammar..."
                  value={formData.topic}
                  onChange={(e) => handleInputChange("topic", e.target.value)}
                  className="text-base py-3 border-slate-200 focus:border-blue-500 focus:ring-blue-500/20"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">Learning Level</Label>
                  <Select onValueChange={(value) => handleInputChange("learner_level", value)}>
                    <SelectTrigger className="border-slate-200 focus:border-blue-500">
                      <SelectValue placeholder="Choose your level" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="beginner">🌱 Beginner</SelectItem>
                      <SelectItem value="intermediate">🌿 Intermediate</SelectItem>
                      <SelectItem value="advanced">🌳 Advanced</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">Learning Style</Label>
                  <Select onValueChange={(value) => handleInputChange("learning_style", value)}>
                    <SelectTrigger className="border-slate-200 focus:border-blue-500">
                      <SelectValue placeholder="How do you learn?" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="visual">👁️ Visual</SelectItem>
                      <SelectItem value="auditory">👂 Auditory</SelectItem>
                      <SelectItem value="kinesthetic">✋ Hands-on</SelectItem>
                      <SelectItem value="reading">📚 Reading/Writing</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button 
                onClick={generateContent} 
                disabled={isGenerating || !formData.topic || !formData.learner_level || !formData.learning_style}
                className="w-full py-6 text-lg font-semibold bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg transition-all duration-200 transform hover:scale-[1.02]"
              >
                {isGenerating ? (
                  <div className="flex items-center gap-2">
                    <RotateCw className="h-5 w-5 animate-spin" />
                    Generating Your Learning Experience...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    Generate Learning Experience
                  </div>
                )}
              </Button>
            </CardContent>
          </Card>
        ) : (
          // Generated Content Display
          <div className="space-y-8">
            {/* Progress Indicator */}
            <Card className="max-w-4xl mx-auto shadow-lg border-0 bg-white/90 backdrop-blur-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-slate-800">Generation Progress</h3>
                  <Button 
                    onClick={resetApp} 
                    variant="outline" 
                    size="sm"
                    className="text-slate-600 hover:text-slate-800"
                  >
                    <RotateCw className="h-4 w-4 mr-2" />
                    Start Over
                  </Button>
                </div>
                
                <div className="flex items-center justify-between">
                  {steps.map((step, index) => (
                    <div key={index} className="flex items-center">
                      <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors ${
                        currentStep > index 
                          ? 'bg-green-500 border-green-500 text-white' 
                          : currentStep === index 
                          ? 'bg-blue-500 border-blue-500 text-white animate-pulse' 
                          : 'border-slate-300 text-slate-400'
                      }`}>
                        {currentStep > index ? <CheckCircle2 className="h-5 w-5" /> : index + 1}
                      </div>
                      <span className={`ml-2 text-sm font-medium ${
                        currentStep >= index ? 'text-slate-800' : 'text-slate-400'
                      }`}>
                        {step}
                      </span>
                      {index < steps.length - 1 && (
                        <div className={`w-16 h-0.5 mx-4 ${
                          currentStep > index ? 'bg-green-500' : 'bg-slate-200'
                        }`} />
                      )}
                    </div>
                  ))}
                </div>
                
                {(isGenerating || isGeneratingVideo) && (
                  <div className="mt-4">
                    <Progress value={(currentStep / (steps.length - 1)) * 100} className="h-2" />
                    <p className="text-sm text-slate-600 mt-2 text-center">
                      {isGeneratingVideo ? "Creating your personalized video..." : "Generating educational content..."}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Content Tabs */}
            <Card className="max-w-6xl mx-auto shadow-xl border-0 bg-white/90 backdrop-blur-sm">
              <CardHeader className="text-center pb-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-t-lg">
                <CardTitle className="text-2xl font-bold text-slate-800">
                  Learning Experience: {generatedContent.topic}
                </CardTitle>
                <div className="flex items-center justify-center gap-4 mt-2">
                  <Badge variant="outline" className="px-3 py-1">
                    {generatedContent.learner_level}
                  </Badge>
                  <Badge variant="outline" className="px-3 py-1">
                    {generatedContent.learning_style} learner
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="p-0">
                <Tabs defaultValue="objectives" className="w-full">
                  <TabsList className="grid grid-cols-4 w-full bg-slate-100 p-1 rounded-none">
                    <TabsTrigger value="objectives" className="flex items-center gap-2">
                      <BookOpen className="h-4 w-4" />
                      Objectives
                    </TabsTrigger>
                    <TabsTrigger value="video" className="flex items-center gap-2">
                      <Video className="h-4 w-4" />
                      Video
                    </TabsTrigger>
                    <TabsTrigger value="quiz" className="flex items-center gap-2">
                      <HelpCircle className="h-4 w-4" />
                      Quiz
                    </TabsTrigger>
                    <TabsTrigger value="flashcards" className="flex items-center gap-2">
                      <RotateCw className="h-4 w-4" />
                      Flashcards
                    </TabsTrigger>
                  </TabsList>

                  <div className="p-6">
                    {/* Learning Objectives */}
                    <TabsContent value="objectives" className="space-y-4">
                      <h3 className="text-xl font-semibold text-slate-800 mb-4">Learning Objectives</h3>
                      <div className="grid gap-3">
                        {generatedContent.learning_objectives.map((objective, index) => (
                          <div key={index} className="flex items-start gap-3 p-4 bg-slate-50 rounded-lg">
                            <div className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-semibold mt-0.5">
                              {index + 1}
                            </div>
                            <p className="text-slate-700 leading-relaxed">{objective}</p>
                          </div>
                        ))}
                      </div>
                    </TabsContent>

                    {/* Video */}
                    <TabsContent value="video" className="space-y-4">
                      <h3 className="text-xl font-semibold text-slate-800 mb-4">🎬 AI-Enhanced Educational Video</h3>
                      <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                          <p className="text-sm font-medium text-blue-800">AI-Powered Features</p>
                        </div>
                        <ul className="text-sm text-blue-700 space-y-1">
                          <li>• AI-generated visual scenes using Groq LLM</li>
                          <li>• Professional narration with high-quality TTS</li>
                          <li>• Ken Burns effect with smooth zoom animations</li>
                          <li>• Crossfade transitions between scenes</li>
                          <li>• 1080p HD quality at 30fps</li>
                        </ul>
                      </div>
                      
                      {videoUrl ? (
                        <div className="aspect-video bg-slate-100 rounded-lg overflow-hidden shadow-inner">
                          <video 
                            controls 
                            className="w-full h-full object-cover"
                            poster="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTkyMCIgaGVpZ2h0PSIxMDgwIiB2aWV3Qm94PSIwIDAgMTkyMCAxMDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8ZGVmcz4KPGxpbmVhckdyYWRpZW50IGlkPSJiZyIgeDE9IjAlIiB5MT0iMCUiIHgyPSIwJSIgeTI9IjEwMCUiPgo8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojMGYxNzJhO3N0b3Atb3BhY2l0eToxIiAvPgo8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiMyZDM3NTI7c3RvcC1vcGFjaXR5OjEiIC8+CjwvbGluZWFyR3JhZGllbnQ+CjwvZGVmcz4KPHJlY3Qgd2lkdGg9IjE5MjAiIGhlaWdodD0iMTA4MCIgZmlsbD0idXJsKCNiZykiLz4KPHJlY3QgeD0iMCIgeT0iMCIgd2lkdGg9IjE5MjAiIGhlaWdodD0iOCIgZmlsbD0iIzYzNjZmMSIvPgo8cmVjdCB4PSIwIiB5PSIwIiB3aWR0aD0iMTIiIGhlaWdodD0iMTA4MCIgZmlsbD0iIzYzNjZmMSIvPgo8Y2lyY2xlIGN4PSI5NjAiIGN5PSI1NDAiIHI9IjYwIiBmaWxsPSJ3aGl0ZSIgZmlsbC1vcGFjaXR5PSIwLjkiLz4KPHBhdGggZD0iTTkzNSA1MDBMMTA0MCA1NDBMOTM1IDU4MFY1MDBaIiBmaWxsPSIjMGYxNzJhIi8+Cjx0ZXh0IHg9Ijk2MCIgeT0iNjQwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSJ3aGl0ZSIgZm9udC1zaXplPSI0OCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIj5FRFVGT1JHRSBBASBBSSBWSURFT1M8L3RleHQ+Cjx0ZXh0IHg9Ijk2MCIgeT0iNzAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjOWNhM2FmIiBmb250LXNpemU9IjMyIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiPkFJLUdlbmVyYXRlZCBFZHVjYXRpb25hbCBDb250ZW50PC90ZXh0Pgo8L3N2Zz4K"
                          >
                            <source src={videoUrl} type="video/mp4" />
                            Your browser does not support the video tag.
                          </video>
                        </div>
                      ) : isGeneratingVideo ? (
                        <div className="aspect-video bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 rounded-lg flex items-center justify-center relative overflow-hidden">
                          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10"></div>
                          <div className="text-center z-10">
                            <RotateCw className="h-16 w-16 animate-spin text-blue-400 mx-auto mb-6" />
                            <h4 className="text-2xl font-bold text-white mb-2">Creating Your AI Video</h4>
                            <p className="text-blue-200 font-medium mb-1">🤖 Generating AI visual scenes...</p>
                            <p className="text-blue-200 font-medium mb-1">🎙️ Creating professional narration...</p>
                            <p className="text-blue-200 font-medium mb-4">🎬 Adding animations & transitions...</p>
                            <div className="w-64 bg-slate-700 rounded-full h-2 mx-auto">
                              <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full animate-pulse" style={{width: '75%'}}></div>
                            </div>
                            <p className="text-xs text-slate-300 mt-3">This may take 1-2 minutes for optimal quality</p>
                          </div>
                        </div>
                      ) : (
                        <div className="aspect-video bg-slate-100 rounded-lg flex items-center justify-center">
                          <div className="text-center">
                            <Video className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                            <p className="text-slate-500">Enhanced video generation in progress...</p>
                          </div>
                        </div>
                      )}

                      {/* Video Script */}
                      <div className="mt-6">
                        <h4 className="text-lg font-semibold text-slate-800 mb-3">📝 Generated Video Script</h4>
                        <div className="bg-slate-50 rounded-lg p-4 border">
                          <p className="text-slate-700 leading-relaxed whitespace-pre-line">{generatedContent.video_script}</p>
                        </div>
                      </div>
                    </TabsContent>

                    {/* Quiz */}
                    <TabsContent value="quiz" className="space-y-6">
                      <div className="flex items-center justify-between">
                        <h3 className="text-xl font-semibold text-slate-800">Interactive Quiz</h3>
                        {!showQuizResults && Object.keys(quizAnswers).length === generatedContent.quiz.length && (
                          <Button onClick={submitQuiz} className="bg-green-600 hover:bg-green-700">
                            Submit Quiz
                          </Button>
                        )}
                      </div>

                      <div className="space-y-6">
                        {generatedContent.quiz.map((question, qIndex) => (
                          <Card key={question.id} className="border border-slate-200">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-lg text-slate-800">
                                Question {qIndex + 1}: {question.question}
                              </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                              {question.options.map((option, oIndex) => (
                                <div key={oIndex}>
                                  <button
                                    onClick={() => !showQuizResults && handleQuizAnswer(question.id, oIndex)}
                                    disabled={showQuizResults}
                                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                                      showQuizResults
                                        ? oIndex === question.correct_answer
                                          ? 'bg-green-100 border-green-300 text-green-800'
                                          : quizAnswers[question.id] === oIndex && oIndex !== question.correct_answer
                                          ? 'bg-red-100 border-red-300 text-red-800'
                                          : 'bg-slate-50 border-slate-200 text-slate-600'
                                        : quizAnswers[question.id] === oIndex
                                        ? 'bg-blue-100 border-blue-300 text-blue-800'
                                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                                    }`}
                                  >
                                    <div className="flex items-center gap-3">
                                      <div className="w-6 h-6 rounded-full border-2 flex items-center justify-center text-sm font-semibold">
                                        {String.fromCharCode(65 + oIndex)}
                                      </div>
                                      {option}
                                    </div>
                                  </button>
                                </div>
                              ))}

                              {showQuizResults && (
                                <div className="mt-4 p-4 bg-slate-50 rounded-lg">
                                  <p className="text-sm font-medium text-slate-800 mb-2">Explanation:</p>
                                  <p className="text-slate-700">{question.explanation}</p>
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </TabsContent>

                    {/* Flashcards */}
                    <TabsContent value="flashcards" className="space-y-4">
                      <h3 className="text-xl font-semibold text-slate-800 mb-4">Study Flashcards</h3>
                      <p className="text-slate-600 mb-6">Click on any card to flip it and reveal the answer</p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {generatedContent.flashcards.map((card, index) => (
                          <div key={card.id} className="relative h-48">
                            <div 
                              onClick={() => toggleFlashcard(card.id)}
                              className={`w-full h-full cursor-pointer transition-transform duration-500 transform-style-preserve-3d ${
                                flippedCards.has(card.id) ? 'rotate-y-180' : ''
                              }`}
                              style={{ transformStyle: 'preserve-3d' }}
                            >
                              {/* Front */}
                              <div className="absolute inset-0 backface-hidden bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-lg p-6 flex items-center justify-center shadow-lg">
                                <div className="text-center">
                                  <p className="text-sm opacity-80 mb-2">Card {index + 1}</p>
                                  <p className="font-medium text-lg leading-relaxed">{card.front}</p>
                                  <p className="text-xs opacity-70 mt-4">Click to flip</p>
                                </div>
                              </div>
                              
                              {/* Back */}
                              <div 
                                className="absolute inset-0 backface-hidden bg-gradient-to-br from-green-500 to-teal-600 text-white rounded-lg p-6 flex items-center justify-center shadow-lg rotate-y-180"
                                style={{ transform: 'rotateY(180deg)' }}
                              >
                                <div className="text-center">
                                  <p className="text-sm opacity-80 mb-2">Answer</p>
                                  <p className="font-medium text-lg leading-relaxed">{card.back}</p>
                                  <p className="text-xs opacity-70 mt-4">Click to flip back</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </TabsContent>
                  </div>
                </Tabs>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;