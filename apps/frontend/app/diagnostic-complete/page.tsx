'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import confetti from 'canvas-confetti';
import StudyPlanRouter from '../components/StudyPlan/StudyPlanRouter';
import {
  Trophy, Shield, Sword, Star, Zap, TrendingUp, Award,
  CheckCircle, Lock, Unlock, BookOpen, Target, Flame,
  ChevronRight, BarChart, Activity, Users, Globe
} from 'lucide-react';

interface DiagnosticResult {
  score: number;
  subject: string;
  weakTopics: string[];
  strongTopics: string[];
  totalQuestions: number;
  correctAnswers: number;
  timeSpent: number;
  rank: string;
}

export default function DiagnosticCompletePage() {
  const router = useRouter();
  const [showResults, setShowResults] = useState(true);
  const [showStudyPlan, setShowStudyPlan] = useState(false);
  const [isUnlocking, setIsUnlocking] = useState(false);
  const [diagnosticData, setDiagnosticData] = useState<DiagnosticResult>({
    score: 75,
    subject: 'Mathematics',
    weakTopics: ['Algebra', 'Trigonometry', 'Calculus'],
    strongTopics: ['Geometry', 'Statistics', 'Probability'],
    totalQuestions: 50,
    correctAnswers: 38,
    timeSpent: 2400,
    rank: 'B'
  });

  useEffect(() => {
    // Load diagnostic results from localStorage or API
    const savedResults = localStorage.getItem('diagnostic_results');
    if (savedResults) {
      setDiagnosticData(JSON.parse(savedResults));
    }
    
    // Celebration animation
    setTimeout(() => {
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 }
      });
    }, 500);
  }, []);

  const unlockStudyPlan = () => {
    setIsUnlocking(true);
    
    // Epic unlock animation
    confetti({
      particleCount: 200,
      spread: 100,
      origin: { y: 0.5 },
      colors: ['#a855f7', '#ec4899', '#f59e0b']
    });
    
    setTimeout(() => {
      setShowResults(false);
      setShowStudyPlan(true);
      setIsUnlocking(false);
    }, 2000);
  };

  const getRankColor = (rank: string) => {
    const colors: { [key: string]: string } = {
      'E': 'from-gray-400 to-gray-600',
      'D': 'from-green-400 to-green-600',
      'C': 'from-blue-400 to-blue-600',
      'B': 'from-purple-400 to-purple-600',
      'A': 'from-orange-400 to-orange-600',
      'S': 'from-red-400 to-red-600',
      'SS': 'from-yellow-400 to-yellow-600',
      'SSS': 'from-pink-400 via-purple-500 to-indigo-600'
    };
    return colors[rank] || colors['E'];
  };

  const getScoreMessage = (score: number) => {
    if (score >= 90) return "Legendary Performance! You're destined to be an S-Rank Hunter!";
    if (score >= 80) return "Excellent Work! You show the potential of an A-Rank Hunter!";
    if (score >= 70) return "Great Job! You've proven yourself as a B-Rank Hunter!";
    if (score >= 60) return "Good Effort! You're on your way to becoming stronger!";
    return "Keep Training! Every Hunter starts somewhere!";
  };

  if (showStudyPlan) {
    return (
      <StudyPlanRouter
        userId="user-123"
        subject={diagnosticData.subject}
        diagnosticScore={diagnosticData.score}
        weakTopics={diagnosticData.weakTopics}
        strongTopics={diagnosticData.strongTopics}
        useHybridSystem={true}
        fallbackToCoursera={true}
        onUnitStart={(unitId) => console.log('Unit started:', unitId)}
        onTopicStart={(topicId, unitId) => console.log('Topic started:', topicId, 'Unit:', unitId)}
        onProgressUpdate={(unitId, progress) => console.log('Progress updated:', unitId, progress)}
        onModuleStart={(moduleId) => console.log('Module started (legacy):', moduleId)}
        onVideoComplete={(videoId, xp) => console.log('Video completed (legacy):', videoId, 'XP:', xp)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black text-white overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0">
        <div className="absolute top-20 left-20 w-96 h-96 bg-purple-500 rounded-full filter blur-3xl opacity-20 animate-pulse" />
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-pink-500 rounded-full filter blur-3xl opacity-20 animate-pulse" />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-purple-500 to-pink-500 rounded-full filter blur-3xl opacity-10 animate-spin-slow" />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-16">
        <AnimatePresence mode="wait">
          {showResults && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="max-w-4xl mx-auto"
            >
              {/* Header */}
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="text-center mb-12"
              >
                <h1 className="text-5xl md:text-7xl font-bold mb-4 bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">
                  Diagnostic Complete!
                </h1>
                <p className="text-xl text-gray-300">
                  Your Hunter evaluation has been completed. Let's see your results...
                </p>
              </motion.div>

              {/* Rank Display */}
              <motion.div
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4, type: "spring", stiffness: 200 }}
                className="mb-12"
              >
                <div className="flex justify-center mb-6">
                  <div className={`
                    w-48 h-48 rounded-2xl bg-gradient-to-br ${getRankColor(diagnosticData.rank)}
                    flex items-center justify-center text-8xl font-bold shadow-2xl
                    transform hover:scale-110 transition-transform duration-300
                    relative overflow-hidden
                  `}>
                    <div className="absolute inset-0 bg-white/20 animate-pulse" />
                    <span className="relative z-10">{diagnosticData.rank}</span>
                  </div>
                </div>
                <p className="text-center text-2xl font-semibold text-gray-300">
                  {getScoreMessage(diagnosticData.score)}
                </p>
              </motion.div>

              {/* Score Card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="bg-black/40 backdrop-blur-lg rounded-2xl p-8 border border-purple-500/30 mb-8"
              >
                <div className="grid md:grid-cols-2 gap-8">
                  {/* Left Column - Main Score */}
                  <div>
                    <h3 className="text-2xl font-bold mb-6 flex items-center">
                      <Trophy className="w-8 h-8 mr-3 text-yellow-400" />
                      Performance Overview
                    </h3>
                    
                    <div className="space-y-4">
                      {/* Score Circle */}
                      <div className="flex items-center justify-center">
                        <div className="relative w-48 h-48">
                          <svg className="transform -rotate-90 w-48 h-48">
                            <circle
                              cx="96"
                              cy="96"
                              r="88"
                              stroke="currentColor"
                              strokeWidth="8"
                              fill="none"
                              className="text-gray-700"
                            />
                            <motion.circle
                              cx="96"
                              cy="96"
                              r="88"
                              stroke="url(#gradient)"
                              strokeWidth="8"
                              fill="none"
                              strokeLinecap="round"
                              initial={{ strokeDasharray: "0 552" }}
                              animate={{ strokeDasharray: `${(diagnosticData.score / 100) * 552} 552` }}
                              transition={{ duration: 1.5, delay: 0.8 }}
                            />
                            <defs>
                              <linearGradient id="gradient">
                                <stop offset="0%" stopColor="#a855f7" />
                                <stop offset="100%" stopColor="#ec4899" />
                              </linearGradient>
                            </defs>
                          </svg>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <div className="text-center">
                              <motion.p
                                className="text-5xl font-bold"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 1 }}
                              >
                                {diagnosticData.score}%
                              </motion.p>
                              <p className="text-gray-400">Overall Score</p>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Stats */}
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-purple-500/10 rounded-lg p-4 text-center">
                          <p className="text-3xl font-bold text-purple-400">
                            {diagnosticData.correctAnswers}/{diagnosticData.totalQuestions}
                          </p>
                          <p className="text-sm text-gray-400">Correct Answers</p>
                        </div>
                        <div className="bg-blue-500/10 rounded-lg p-4 text-center">
                          <p className="text-3xl font-bold text-blue-400">
                            {Math.floor(diagnosticData.timeSpent / 60)}m
                          </p>
                          <p className="text-sm text-gray-400">Time Spent</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right Column - Topics Analysis */}
                  <div>
                    <h3 className="text-2xl font-bold mb-6 flex items-center">
                      <BarChart className="w-8 h-8 mr-3 text-purple-400" />
                      Skill Analysis
                    </h3>

                    {/* Weak Topics */}
                    <div className="mb-6">
                      <h4 className="text-lg font-semibold mb-3 text-red-400">Areas to Improve</h4>
                      <div className="space-y-2">
                        {diagnosticData.weakTopics.map((topic, index) => (
                          <motion.div
                            key={topic}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.8 + index * 0.1 }}
                            className="flex items-center space-x-3 bg-red-500/10 rounded-lg p-3"
                          >
                            <Target className="w-5 h-5 text-red-400" />
                            <span>{topic}</span>
                          </motion.div>
                        ))}
                      </div>
                    </div>

                    {/* Strong Topics */}
                    <div>
                      <h4 className="text-lg font-semibold mb-3 text-green-400">Your Strengths</h4>
                      <div className="space-y-2">
                        {diagnosticData.strongTopics.map((topic, index) => (
                          <motion.div
                            key={topic}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 1 + index * 0.1 }}
                            className="flex items-center space-x-3 bg-green-500/10 rounded-lg p-3"
                          >
                            <CheckCircle className="w-5 h-5 text-green-400" />
                            <span>{topic}</span>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Unlock Study Plan CTA */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.2 }}
                className="text-center"
              >
                <div className="mb-6 p-6 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-2xl border border-purple-500/30">
                  <h3 className="text-2xl font-bold mb-3">Ready to Begin Your Journey?</h3>
                  <p className="text-gray-300 mb-6">
                    Based on your diagnostic results, we've prepared a personalized learning path 
                    that will transform you into an S-Rank Hunter!
                  </p>
                  
                  <motion.button
                    onClick={unlockStudyPlan}
                    disabled={isUnlocking}
                    className={`
                      px-12 py-4 rounded-xl font-bold text-xl
                      bg-gradient-to-r from-purple-500 to-pink-500
                      hover:from-purple-600 hover:to-pink-600
                      transform transition-all duration-300
                      ${isUnlocking ? 'scale-110 animate-pulse' : 'hover:scale-105'}
                      shadow-2xl relative overflow-hidden
                    `}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {isUnlocking ? (
                      <span className="flex items-center space-x-3">
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        >
                          <Unlock className="w-6 h-6" />
                        </motion.div>
                        <span>Unlocking Your Path...</span>
                      </span>
                    ) : (
                      <span className="flex items-center space-x-3">
                        <Lock className="w-6 h-6" />
                        <span>Unlock Personalized Study Plan</span>
                        <ChevronRight className="w-6 h-6" />
                      </span>
                    )}
                    
                    {/* Shimmer Effect */}
                    <motion.div
                      className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                      animate={{ x: [-200, 200] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    />
                  </motion.button>
                </div>

                {/* Additional Actions */}
                <div className="flex justify-center space-x-4">
                  <button className="px-6 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors">
                    View Detailed Report
                  </button>
                  <button className="px-6 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors">
                    Compare with Others
                  </button>
                  <button className="px-6 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors">
                    Share Results
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}