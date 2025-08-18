'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useScroll, useTransform } from 'framer-motion';
import confetti from 'canvas-confetti';
import { 
  BookOpen, Play, Lock, Unlock, CheckCircle, Star, Zap, TrendingUp,
  Trophy, Shield, Sword, Target, Eye, Clock, Award, Flame,
  ChevronRight, ChevronDown, Video, FileText, Code, Users,
  Download, Share2, Heart, MessageCircle, ThumbsUp, AlertCircle,
  BarChart, Activity, Cpu, Database, Globe, Layers, Package
} from 'lucide-react';

// Types
interface VideoResource {
  id: string;
  youtube_url: string;
  title: string;
  duration: number;
  thumbnail?: string;
  xp_reward: number;
  completed?: boolean;
  progress?: number;
}

interface Module {
  id: string;
  number: number;
  title: string;
  description: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
  topics: string[];
  videos: VideoResource[];
  exercises: number;
  readings: number;
  estimated_hours: number;
  xp_reward: number;
  locked: boolean;
  progress: number;
  prerequisite?: string[];
  boss_level?: boolean;
  ai_explanation?: string;
}

interface StudyPlanProps {
  userId: string;
  subject: string;
  diagnosticScore: number;
  weakTopics: string[];
  strongTopics: string[];
  onModuleStart?: (moduleId: string) => void;
  onVideoComplete?: (videoId: string, xp: number) => void;
}

// Solo Leveling Rank System
const RANKS = [
  { name: 'E', color: 'from-gray-400 to-gray-600', minXP: 0, title: 'Novice Hunter' },
  { name: 'D', color: 'from-green-400 to-green-600', minXP: 1000, title: 'Apprentice Hunter' },
  { name: 'C', color: 'from-blue-400 to-blue-600', minXP: 3000, title: 'Skilled Hunter' },
  { name: 'B', color: 'from-purple-400 to-purple-600', minXP: 6000, title: 'Expert Hunter' },
  { name: 'A', color: 'from-orange-400 to-orange-600', minXP: 10000, title: 'Master Hunter' },
  { name: 'S', color: 'from-red-400 to-red-600', minXP: 15000, title: 'Elite Hunter' },
  { name: 'SS', color: 'from-yellow-400 to-yellow-600', minXP: 25000, title: 'Legendary Hunter' },
  { name: 'SSS', color: 'from-pink-400 via-purple-500 to-indigo-600', minXP: 50000, title: 'Mythical Hunter' }
];

const CourseraGradeStudyPlan: React.FC<StudyPlanProps> = ({
  userId,
  subject,
  diagnosticScore,
  weakTopics,
  strongTopics,
  onModuleStart,
  onVideoComplete
}) => {
  const [modules, setModules] = useState<Module[]>([]);
  const [selectedModule, setSelectedModule] = useState<Module | null>(null);
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());
  const [userXP, setUserXP] = useState(0);
  const [userRank, setUserRank] = useState(RANKS[0]);
  const [showVideoPlayer, setShowVideoPlayer] = useState(false);
  const [currentVideo, setCurrentVideo] = useState<VideoResource | null>(null);
  const [achievements, setAchievements] = useState<string[]>([]);
  const [studyStreak, setStudyStreak] = useState(0);
  const [loading, setLoading] = useState(true);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });
  
  const progressBarWidth = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);
  const parallaxY = useTransform(scrollYProgress, [0, 1], [0, -50]);

  useEffect(() => {
    generatePersonalizedModules();
    loadUserProgress();
  }, [subject, diagnosticScore]);

  const generatePersonalizedModules = () => {
    // Generate modules based on diagnostic results
    const generatedModules: Module[] = [
      {
        id: 'mod-1',
        number: 1,
        title: '🔥 Foundation Mastery - Awakening',
        description: 'Begin your journey as a Hunter. Master the fundamental concepts that will be your weapons.',
        difficulty: 'Beginner',
        topics: ['Basic Concepts', 'Core Principles', 'Fundamental Theory'],
        videos: [
          {
            id: 'vid-1-1',
            youtube_url: 'https://www.youtube.com/embed/X1E7I7_r3Cw',
            title: 'Core Concepts Explained',
            duration: 900,
            xp_reward: 150,
            completed: false,
            progress: 0
          },
          {
            id: 'vid-1-2',
            youtube_url: 'https://www.youtube.com/embed/IHIHy8jF2R4',
            title: 'Practical Applications',
            duration: 1200,
            xp_reward: 200,
            completed: false,
            progress: 0
          }
        ],
        exercises: 15,
        readings: 3,
        estimated_hours: 4,
        xp_reward: 500,
        locked: false,
        progress: 0,
        ai_explanation: 'Based on your diagnostic, we start with fundamentals to build a solid foundation.'
      },
      {
        id: 'mod-2',
        number: 2,
        title: '⚔️ Combat Training - Skills Development',
        description: 'Learn advanced techniques. Your weak areas will be transformed into strengths.',
        difficulty: 'Intermediate',
        topics: weakTopics.slice(0, 3),
        videos: [
          {
            id: 'vid-2-1',
            youtube_url: 'https://www.youtube.com/embed/CzKoQQpAZ6k',
            title: `Mastering ${weakTopics[0] || 'Advanced Concepts'}`,
            duration: 1080,
            xp_reward: 250,
            completed: false,
            progress: 0
          }
        ],
        exercises: 20,
        readings: 5,
        estimated_hours: 6,
        xp_reward: 750,
        locked: true,
        progress: 0,
        prerequisite: ['mod-1'],
        ai_explanation: 'Focused on your weak areas identified in the diagnostic test.'
      },
      {
        id: 'mod-3',
        number: 3,
        title: '🛡️ Defense Strategies - Problem Solving',
        description: 'Apply your knowledge in real combat scenarios. Face increasingly difficult challenges.',
        difficulty: 'Advanced',
        topics: ['Problem Solving', 'Critical Analysis', 'Application'],
        videos: [
          {
            id: 'vid-3-1',
            youtube_url: 'https://www.youtube.com/embed/b1t41Q3xRM8',
            title: 'Advanced Problem Solving',
            duration: 1500,
            xp_reward: 300,
            completed: false,
            progress: 0
          }
        ],
        exercises: 25,
        readings: 4,
        estimated_hours: 8,
        xp_reward: 1000,
        locked: true,
        progress: 0,
        prerequisite: ['mod-2']
      },
      {
        id: 'mod-4',
        number: 4,
        title: '👹 BOSS RAID - Final Assessment',
        description: 'Face the ultimate challenge. Prove you have become a true Hunter.',
        difficulty: 'Expert',
        topics: ['Comprehensive Review', 'Final Challenge', 'Mastery Test'],
        videos: [
          {
            id: 'vid-4-1',
            youtube_url: 'https://www.youtube.com/embed/9Dj2MQmLOTw',
            title: 'Final Boss Strategy Guide',
            duration: 1800,
            xp_reward: 500,
            completed: false,
            progress: 0
          }
        ],
        exercises: 30,
        readings: 6,
        estimated_hours: 10,
        xp_reward: 2000,
        locked: true,
        progress: 0,
        prerequisite: ['mod-3'],
        boss_level: true,
        ai_explanation: 'The ultimate test of your mastery. Combines all learned concepts.'
      }
    ];

    // Unlock first module if diagnostic is complete
    if (diagnosticScore > 0) {
      generatedModules[0].locked = false;
    }

    setModules(generatedModules);
    setLoading(false);
  };

  const loadUserProgress = () => {
    // Simulate loading user progress
    const savedXP = localStorage.getItem(`user_xp_${userId}`) || '0';
    const xp = parseInt(savedXP);
    setUserXP(xp);
    updateRank(xp);
    
    // Load streak
    const lastStudyDate = localStorage.getItem(`last_study_${userId}`);
    if (lastStudyDate) {
      const daysSince = Math.floor((Date.now() - parseInt(lastStudyDate)) / (1000 * 60 * 60 * 24));
      setStudyStreak(daysSince === 0 ? 7 : daysSince === 1 ? 8 : 0);
    }
  };

  const updateRank = (xp: number) => {
    const newRank = RANKS.slice().reverse().find(rank => xp >= rank.minXP) || RANKS[0];
    setUserRank(newRank);
  };

  const unlockModule = (moduleId: string) => {
    setModules(prev => prev.map(mod => {
      if (mod.id === moduleId) {
        return { ...mod, locked: false };
      }
      return mod;
    }));
    
    // Celebration animation
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    });
    
    // Show achievement
    const achievement = `Module Unlocked: ${modules.find(m => m.id === moduleId)?.title}`;
    setAchievements(prev => [...prev, achievement]);
  };

  const handleModuleClick = (module: Module) => {
    if (module.locked) {
      // Show lock animation
      return;
    }
    
    setSelectedModule(module);
    
    if (expandedModules.has(module.id)) {
      setExpandedModules(prev => {
        const newSet = new Set(prev);
        newSet.delete(module.id);
        return newSet;
      });
    } else {
      setExpandedModules(prev => new Set(prev).add(module.id));
      onModuleStart?.(module.id);
    }
  };

  const handleVideoClick = (video: VideoResource) => {
    setCurrentVideo(video);
    setShowVideoPlayer(true);
  };

  const handleVideoComplete = (video: VideoResource) => {
    // Update video completion
    setModules(prev => prev.map(mod => ({
      ...mod,
      videos: mod.videos.map(v => 
        v.id === video.id ? { ...v, completed: true, progress: 100 } : v
      )
    })));
    
    // Award XP
    const newXP = userXP + video.xp_reward;
    setUserXP(newXP);
    updateRank(newXP);
    localStorage.setItem(`user_xp_${userId}`, newXP.toString());
    
    // Update module progress
    updateModuleProgress(video.id);
    
    // Call parent callback
    onVideoComplete?.(video.id, video.xp_reward);
    
    // Celebration
    confetti({
      particleCount: 50,
      angle: 60,
      spread: 55,
      origin: { x: 0 }
    });
    
    setShowVideoPlayer(false);
  };

  const updateModuleProgress = (videoId: string) => {
    setModules(prev => prev.map(mod => {
      const videoInModule = mod.videos.some(v => v.id === videoId);
      if (videoInModule) {
        const completedVideos = mod.videos.filter(v => v.completed).length;
        const progress = (completedVideos / mod.videos.length) * 100;
        
        // Check if module is complete
        if (progress === 100) {
          // Unlock next module
          const nextModule = modules.find(m => m.prerequisite?.includes(mod.id));
          if (nextModule) {
            setTimeout(() => unlockModule(nextModule.id), 500);
          }
        }
        
        return { ...mod, progress };
      }
      return mod;
    }));
  };

  const getDifficultyColor = (difficulty: Module['difficulty']) => {
    switch (difficulty) {
      case 'Beginner': return 'from-green-400 to-green-600';
      case 'Intermediate': return 'from-blue-400 to-blue-600';
      case 'Advanced': return 'from-purple-400 to-purple-600';
      case 'Expert': return 'from-red-400 to-red-600';
      default: return 'from-gray-400 to-gray-600';
    }
  };

  const getDifficultyIcon = (difficulty: Module['difficulty']) => {
    switch (difficulty) {
      case 'Beginner': return <Shield className="w-5 h-5" />;
      case 'Intermediate': return <Sword className="w-5 h-5" />;
      case 'Advanced': return <Target className="w-5 h-5" />;
      case 'Expert': return <Trophy className="w-5 h-5" />;
      default: return <Star className="w-5 h-5" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div ref={containerRef} className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black text-white">
      {/* Progress Bar */}
      <motion.div 
        className="fixed top-0 left-0 h-1 bg-gradient-to-r from-purple-500 to-pink-500 z-50"
        style={{ width: progressBarWidth }}
      />

      {/* Header Section */}
      <motion.div 
        className="relative overflow-hidden"
        style={{ y: parallaxY }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-purple-900/50 to-transparent" />
        
        {/* Animated Background */}
        <div className="absolute inset-0">
          <div className="absolute top-20 left-20 w-72 h-72 bg-purple-500 rounded-full filter blur-3xl opacity-20 animate-pulse" />
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-pink-500 rounded-full filter blur-3xl opacity-20 animate-pulse" />
        </div>

        <div className="relative z-10 container mx-auto px-4 py-16">
          {/* User Stats Bar */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 bg-black/40 backdrop-blur-lg rounded-2xl p-6 border border-purple-500/30"
          >
            <div className="flex flex-wrap items-center justify-between gap-4">
              {/* Rank Display */}
              <div className="flex items-center space-x-4">
                <div className={`w-16 h-16 rounded-lg bg-gradient-to-br ${userRank.color} flex items-center justify-center`}>
                  <span className="text-2xl font-bold">{userRank.name}</span>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Current Rank</p>
                  <p className="text-xl font-bold">{userRank.title}</p>
                </div>
              </div>

              {/* XP Progress */}
              <div className="flex-1 max-w-md">
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-400">Experience Points</span>
                  <span className="text-sm font-bold">{userXP} XP</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(userXP % 1000) / 10}%` }}
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                  />
                </div>
              </div>

              {/* Study Streak */}
              <div className="flex items-center space-x-2">
                <Flame className="w-8 h-8 text-orange-500" />
                <div>
                  <p className="text-sm text-gray-400">Study Streak</p>
                  <p className="text-xl font-bold">{studyStreak} days</p>
                </div>
              </div>

              {/* Diagnostic Score */}
              <div className="text-center">
                <p className="text-sm text-gray-400">Diagnostic Score</p>
                <p className="text-2xl font-bold text-green-400">{diagnosticScore}%</p>
              </div>
            </div>
          </motion.div>

          {/* Title Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-center mb-12"
          >
            <h1 className="text-5xl md:text-7xl font-bold mb-4 bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">
              Your Learning Dungeon
            </h1>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              {diagnosticScore > 0 
                ? `Based on your diagnostic test, we've created a personalized path to transform you into an S-Rank Hunter in ${subject}.`
                : 'Complete the diagnostic test to unlock your personalized learning path.'}
            </p>
          </motion.div>
        </div>
      </motion.div>

      {/* Modules Section */}
      <div className="container mx-auto px-4 pb-20">
        <div className="space-y-6">
          {modules.map((module, index) => (
            <motion.div
              key={module.id}
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`relative ${module.boss_level ? 'transform scale-105' : ''}`}
            >
              {/* Module Card */}
              <div
                className={`
                  relative overflow-hidden rounded-2xl
                  ${module.locked ? 'opacity-60' : ''}
                  ${module.boss_level ? 'ring-4 ring-red-500 ring-opacity-50' : ''}
                  transition-all duration-300 hover:transform hover:scale-[1.02]
                `}
              >
                {/* Background Gradient */}
                <div className={`absolute inset-0 bg-gradient-to-r ${getDifficultyColor(module.difficulty)} opacity-10`} />
                
                {/* Glass Effect Background */}
                <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
                
                {/* Content */}
                <div className="relative z-10 p-8">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Module Header */}
                      <div className="flex items-center space-x-4 mb-4">
                        <div className={`
                          w-16 h-16 rounded-xl bg-gradient-to-br ${getDifficultyColor(module.difficulty)}
                          flex items-center justify-center text-white font-bold text-2xl
                          ${module.boss_level ? 'animate-pulse' : ''}
                        `}>
                          {module.locked ? <Lock /> : module.number}
                        </div>
                        
                        <div className="flex-1">
                          <h3 className="text-2xl font-bold mb-1">{module.title}</h3>
                          <p className="text-gray-400">{module.description}</p>
                        </div>

                        {/* Difficulty Badge */}
                        <div className={`
                          px-4 py-2 rounded-full bg-gradient-to-r ${getDifficultyColor(module.difficulty)}
                          flex items-center space-x-2
                        `}>
                          {getDifficultyIcon(module.difficulty)}
                          <span className="font-semibold">{module.difficulty}</span>
                        </div>
                      </div>

                      {/* Module Stats */}
                      <div className="flex flex-wrap gap-4 mb-4">
                        <div className="flex items-center space-x-2 text-sm">
                          <Video className="w-4 h-4 text-purple-400" />
                          <span>{module.videos.length} Videos</span>
                        </div>
                        <div className="flex items-center space-x-2 text-sm">
                          <FileText className="w-4 h-4 text-blue-400" />
                          <span>{module.exercises} Exercises</span>
                        </div>
                        <div className="flex items-center space-x-2 text-sm">
                          <BookOpen className="w-4 h-4 text-green-400" />
                          <span>{module.readings} Readings</span>
                        </div>
                        <div className="flex items-center space-x-2 text-sm">
                          <Clock className="w-4 h-4 text-yellow-400" />
                          <span>{module.estimated_hours} hours</span>
                        </div>
                        <div className="flex items-center space-x-2 text-sm">
                          <Zap className="w-4 h-4 text-orange-400" />
                          <span className="font-bold">{module.xp_reward} XP</span>
                        </div>
                      </div>

                      {/* Topics */}
                      <div className="flex flex-wrap gap-2 mb-4">
                        {module.topics.map((topic, i) => (
                          <span key={i} className="px-3 py-1 bg-purple-500/20 rounded-full text-sm">
                            {topic}
                          </span>
                        ))}
                      </div>

                      {/* Progress Bar */}
                      {!module.locked && (
                        <div className="mb-4">
                          <div className="flex justify-between mb-2">
                            <span className="text-sm text-gray-400">Progress</span>
                            <span className="text-sm font-bold">{Math.round(module.progress)}%</span>
                          </div>
                          <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${module.progress}%` }}
                              className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                            />
                          </div>
                        </div>
                      )}

                      {/* AI Explanation (if available) */}
                      {module.ai_explanation && !module.locked && (
                        <div className="p-4 bg-purple-500/10 rounded-lg border border-purple-500/30 mb-4">
                          <div className="flex items-start space-x-2">
                            <Cpu className="w-5 h-5 text-purple-400 mt-1" />
                            <p className="text-sm text-gray-300">{module.ai_explanation}</p>
                          </div>
                        </div>
                      )}

                      {/* Action Button */}
                      <button
                        onClick={() => handleModuleClick(module)}
                        disabled={module.locked}
                        className={`
                          w-full py-3 rounded-lg font-semibold transition-all duration-300
                          ${module.locked 
                            ? 'bg-gray-700 cursor-not-allowed' 
                            : module.boss_level
                              ? 'bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600'
                              : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600'
                          }
                          transform hover:scale-[1.02]
                        `}
                      >
                        {module.locked ? (
                          <span className="flex items-center justify-center space-x-2">
                            <Lock className="w-5 h-5" />
                            <span>Complete Previous Module to Unlock</span>
                          </span>
                        ) : expandedModules.has(module.id) ? (
                          <span className="flex items-center justify-center space-x-2">
                            <ChevronDown className="w-5 h-5" />
                            <span>Hide Content</span>
                          </span>
                        ) : (
                          <span className="flex items-center justify-center space-x-2">
                            <ChevronRight className="w-5 h-5" />
                            <span>{module.boss_level ? 'Enter Boss Raid' : 'Start Learning'}</span>
                          </span>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  <AnimatePresence>
                    {expandedModules.has(module.id) && !module.locked && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                        className="mt-6 pt-6 border-t border-gray-700"
                      >
                        {/* Videos Section */}
                        <div className="space-y-4">
                          <h4 className="text-lg font-semibold flex items-center space-x-2">
                            <Video className="w-5 h-5 text-purple-400" />
                            <span>Video Lessons</span>
                          </h4>
                          
                          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {module.videos.map((video) => (
                              <motion.div
                                key={video.id}
                                whileHover={{ scale: 1.05 }}
                                className="relative overflow-hidden rounded-lg bg-black/60 border border-purple-500/30 cursor-pointer"
                                onClick={() => handleVideoClick(video)}
                              >
                                {/* Video Thumbnail */}
                                <div className="aspect-video bg-gradient-to-br from-purple-900 to-pink-900 relative">
                                  <div className="absolute inset-0 flex items-center justify-center">
                                    <Play className="w-12 h-12 text-white/80" />
                                  </div>
                                  {video.completed && (
                                    <div className="absolute top-2 right-2 bg-green-500 rounded-full p-1">
                                      <CheckCircle className="w-4 h-4 text-white" />
                                    </div>
                                  )}
                                </div>
                                
                                {/* Video Info */}
                                <div className="p-4">
                                  <h5 className="font-semibold mb-2">{video.title}</h5>
                                  <div className="flex items-center justify-between text-sm text-gray-400">
                                    <span>{Math.floor(video.duration / 60)} min</span>
                                    <span className="text-yellow-400 font-bold">+{video.xp_reward} XP</span>
                                  </div>
                                  
                                  {/* Progress Bar */}
                                  {video.progress !== undefined && video.progress > 0 && (
                                    <div className="mt-2">
                                      <div className="w-full bg-gray-800 rounded-full h-1 overflow-hidden">
                                        <div 
                                          className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                                          style={{ width: `${video.progress}%` }}
                                        />
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </motion.div>
                            ))}
                          </div>
                        </div>

                        {/* Additional Resources */}
                        <div className="mt-6 grid md:grid-cols-2 gap-4">
                          <div className="p-4 bg-blue-500/10 rounded-lg border border-blue-500/30">
                            <div className="flex items-center space-x-3">
                              <FileText className="w-8 h-8 text-blue-400" />
                              <div>
                                <p className="font-semibold">{module.exercises} Practice Exercises</p>
                                <p className="text-sm text-gray-400">Test your knowledge</p>
                              </div>
                            </div>
                          </div>
                          
                          <div className="p-4 bg-green-500/10 rounded-lg border border-green-500/30">
                            <div className="flex items-center space-x-3">
                              <BookOpen className="w-8 h-8 text-green-400" />
                              <div>
                                <p className="font-semibold">{module.readings} Reading Materials</p>
                                <p className="text-sm text-gray-400">Deepen your understanding</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Video Player Modal */}
      <AnimatePresence>
        {showVideoPlayer && currentVideo && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90"
            onClick={() => setShowVideoPlayer(false)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="relative w-full max-w-4xl bg-gray-900 rounded-2xl overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Video Header */}
              <div className="p-6 bg-gradient-to-r from-purple-900 to-pink-900">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-2xl font-bold mb-2">{currentVideo.title}</h3>
                    <div className="flex items-center space-x-4 text-sm">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-4 h-4" />
                        <span>{Math.floor(currentVideo.duration / 60)} minutes</span>
                      </span>
                      <span className="flex items-center space-x-1 text-yellow-400">
                        <Zap className="w-4 h-4" />
                        <span className="font-bold">+{currentVideo.xp_reward} XP</span>
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowVideoPlayer(false)}
                    className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>
              </div>

              {/* Video Player */}
              <div className="aspect-video bg-black">
                <iframe
                  src={currentVideo.youtube_url}
                  title={currentVideo.title}
                  className="w-full h-full"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>

              {/* Video Controls */}
              <div className="p-6 bg-gray-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <button className="flex items-center space-x-2 px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors">
                      <ThumbsUp className="w-4 h-4" />
                      <span>Like</span>
                    </button>
                    <button className="flex items-center space-x-2 px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors">
                      <Share2 className="w-4 h-4" />
                      <span>Share</span>
                    </button>
                    <button className="flex items-center space-x-2 px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors">
                      <Download className="w-4 h-4" />
                      <span>Download</span>
                    </button>
                  </div>
                  
                  <button
                    onClick={() => handleVideoComplete(currentVideo)}
                    className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg font-semibold hover:from-green-600 hover:to-emerald-600 transition-all transform hover:scale-105"
                  >
                    Mark as Complete
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Achievement Notifications */}
      <AnimatePresence>
        {achievements.map((achievement, index) => (
          <motion.div
            key={`${achievement}-${index}`}
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 100 }}
            className="fixed bottom-4 right-4 bg-gradient-to-r from-yellow-500 to-orange-500 text-white px-6 py-4 rounded-lg shadow-2xl z-50"
            onAnimationComplete={() => {
              setTimeout(() => {
                setAchievements(prev => prev.filter((_, i) => i !== index));
              }, 3000);
            }}
          >
            <div className="flex items-center space-x-3">
              <Trophy className="w-6 h-6" />
              <div>
                <p className="font-bold">Achievement Unlocked!</p>
                <p className="text-sm">{achievement}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

// Missing import
const X = () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>;

export default CourseraGradeStudyPlan;