'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  Crown, 
  Star, 
  Trophy,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Target,
  BookOpen,
  Video,
  Award,
  Zap,
  Brain,
  Shield,
  Sword,
  Eye,
  Calendar,
  TrendingUp,
  Sparkles,
  Flame,
  Scroll,
  Swords,
  Gem
} from 'lucide-react';

// Epic sound effects for rank reevaluation
const examStartSound = typeof Audio !== 'undefined' ? new Audio('/sounds/warrior-roar.mp3') : null;
const correctAnswerSound = typeof Audio !== 'undefined' ? new Audio('/sounds/success.mp3') : null;
const wrongAnswerSound = typeof Audio !== 'undefined' ? new Audio('/sounds/error.mp3') : null;
const rankUpSound = typeof Audio !== 'undefined' ? new Audio('/sounds/victory.mp3') : null;
const hoverSound = typeof Audio !== 'undefined' ? new Audio('/sounds/hover.mp3') : null;
const clickSound = typeof Audio !== 'undefined' ? new Audio('/sounds/click.mp3') : null;
const epicSound = typeof Audio !== 'undefined' ? new Audio('/sounds/epic.mp3') : null;

import SubjectIcon from '@/components/SubjectIcon';

interface ReevaluationEligibility {
  eligible: boolean;
  subject_id?: string;
  subject_name?: string;
  requirements_met: boolean;
  plan_completion: {
    percentage: number;
    completed_units: number;
    total_units: number;
  };
  video_completion: {
    percentage: number;
    completed_videos: number;
    total_videos: number;
  };
  exercise_completion: {
    percentage: number;
    completed_exercises: number;
    total_exercises: number;
  };
  reason: string;
  next_exam_info: {
    questions_count: number;
    estimated_duration: string;
    passing_score: number;
  };
}

interface ReevaluationDashboard {
  user_info: {
    current_level: number;
    current_rank: string;
    experience: number;
    next_rank_requirements: {
      next_rank: string;
      is_max_rank: boolean;
      requirements?: string;
    };
  };
  eligibility: {
    eligible: boolean;
    eligible_subjects: string[];
    subjects_status: Record<string, ReevaluationEligibility>;
    total_subjects: number;
    eligible_count: number;
    reason: string;
  };
  reevaluation_history: Array<{
    id: string;
    subject_name: string;
    score: number;
    passed: boolean;
    date: string;
    questions_answered: number;
    status: string;
  }>;
  exam_config: {
    questions_per_subject: number;
    min_accuracy_for_rank_up: number;
    cooldown_days: number;
  };
}

interface ExamQuestion {
  id: string;
  question_number: number;
  question_text: string;
  options: string[];
  difficulty: number;
  topic: string;
  subject: string;
}

interface ExamState {
  exam_id: string | null;
  questions: ExamQuestion[];
  current_question: number;
  answers: Record<string, string>;
  time_remaining: number;
  exam_started: boolean;
  exam_completed: boolean;
}

export default function RankReevaluationPage() {
  const [dashboard, setDashboard] = useState<ReevaluationDashboard | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<string>('');
  const [examState, setExamState] = useState<ExamState>({
    exam_id: null,
    questions: [],
    current_question: 0,
    answers: {},
    time_remaining: 3600,
    exam_started: false,
    exam_completed: false
  });
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [orbsEarned, setOrbsEarned] = useState(0);
  const [hunterRank, setHunterRank] = useState('E');
  const [particles, setParticles] = useState([]);
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  // Floating particles effect
  useEffect(() => {
    const interval = setInterval(() => {
      setParticles(prev => [...prev.slice(-30), {
        id: Date.now(),
        x: Math.random() * 100,
        y: 100,
        size: Math.random() * 6 + 2,
        color: Math.random() > 0.5 ? '#ffd700' : '#8a2be2',
        speed: Math.random() * 5 + 3
      }]);
    }, 300);
    return () => clearInterval(interval);
  }, []);

  // Timer effect
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (examState.exam_started && !examState.exam_completed && examState.time_remaining > 0) {
      timer = setInterval(() => {
        setExamState(prev => ({
          ...prev,
          time_remaining: prev.time_remaining - 1
        }));
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [examState.exam_started, examState.exam_completed, examState.time_remaining]);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    epicSound?.play();
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const mockDashboard: ReevaluationDashboard = {
        user_info: {
          current_level: 45,
          current_rank: "C",
          experience: 12500,
          next_rank_requirements: {
            next_rank: "B",
            is_max_rank: false,
            requirements: "Aprobar la Prueba Arcana con 75% de maestría"
          }
        },
        eligibility: {
          eligible: true,
          eligible_subjects: ["Matemáticas", "Lenguaje"],
          subjects_status: {
            "math": {
              eligible: true,
              subject_id: "550e8400-e29b-41d4-a716-446655440001",
              subject_name: "Matemáticas",
              requirements_met: true,
              plan_completion: { percentage: 92, completed_units: 4, total_units: 4 },
              video_completion: { percentage: 85, completed_videos: 8, total_videos: 10 },
              exercise_completion: { percentage: 88, completed_exercises: 44, total_exercises: 50 },
              reason: "¡Eres digno de enfrentar la Prueba Arcana de las Matemáticas!",
              next_exam_info: { questions_count: 45, estimated_duration: "45-60 minutos épicos", passing_score: 75 }
            },
            "language": {
              eligible: true,
              subject_id: "550e8400-e29b-41d4-a716-446655440002",
              subject_name: "Lenguaje",
              requirements_met: true,
              plan_completion: { percentage: 89, completed_units: 4, total_units: 4 },
              video_completion: { percentage: 78, completed_videos: 7, total_videos: 9 },
              exercise_completion: { percentage: 82, completed_exercises: 41, total_exercises: 50 },
              reason: "¡Tu poder en las Artes del Lenguaje te hace digno!",
              next_exam_info: { questions_count: 45, estimated_duration: "45-60 minutos legendarios", passing_score: 75 }
            },
            "science": {
              eligible: false,
              subject_id: "550e8400-e29b-41d4-a716-446655440003",
              subject_name: "Ciencias Naturales",
              requirements_met: false,
              plan_completion: { percentage: 65, completed_units: 2, total_units: 4 },
              video_completion: { percentage: 60, completed_videos: 5, total_videos: 10 },
              exercise_completion: { percentage: 58, completed_exercises: 29, total_exercises: 50 },
              reason: "Necesitas más poder: Completa 20% más del plan místico; Conquista 1 unidad más; Descifra 10% más pergaminos",
              next_exam_info: { questions_count: 45, estimated_duration: "45-60 minutos", passing_score: 75 }
            }
          },
          total_subjects: 3,
          eligible_count: 2,
          reason: "Reinos disponibles para ascenso: Matemáticas, Lenguaje"
        },
        reevaluation_history: [
          {
            id: "1",
            subject_name: "Matemáticas",
            score: 78,
            passed: true,
            date: "2024-01-15T10:00:00Z",
            questions_answered: 45,
            status: "completed"
          },
          {
            id: "2",
            subject_name: "Ciencias Naturales",
            score: 72,
            passed: false,
            date: "2024-01-01T14:00:00Z",
            questions_answered: 45,
            status: "completed"
          }
        ],
        exam_config: {
          questions_per_subject: 45,
          min_accuracy_for_rank_up: 75,
          cooldown_days: 30
        }
      };
      
      setDashboard(mockDashboard);
      setHunterRank(mockDashboard.user_info.current_rank);
    } catch (error) {
      console.error('⚔️ Error invocando datos ancestrales:', error);
    }
    setLoading(false);
  };

  const startExam = async (subjectId: string) => {
    examStartSound?.play();
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const mockQuestions: ExamQuestion[] = Array.from({ length: 45 }, (_, i) => ({
        id: `q${i + 1}`,
        question_number: i + 1,
        question_text: `Enigma Arcano ${i + 1}: Esta prueba desafiará tu dominio y conocimiento ancestral en las artes místicas.`,
        options: [
          `Solución Alfa del enigma ${i + 1}`,
          `Solución Beta del enigma ${i + 1}`,
          `Solución Gamma del enigma ${i + 1}`,
          `Solución Delta del enigma ${i + 1}`
        ],
        difficulty: Math.floor(Math.random() * 3) + 1,
        topic: `Reino del Conocimiento ${Math.floor(i / 5) + 1}`,
        subject: dashboard?.eligibility.subjects_status[Object.keys(dashboard.eligibility.subjects_status).find(key => 
          dashboard.eligibility.subjects_status[key].subject_id === subjectId
        ) || '']?.subject_name || 'Desconocido'
      }));

      setExamState({
        exam_id: `exam_arcano_${Date.now()}`,
        questions: mockQuestions,
        current_question: 0,
        answers: {},
        time_remaining: 3600,
        exam_started: true,
        exam_completed: false
      });
      
      setActiveTab('exam');
    } catch (error) {
      console.error('⚔️ Error iniciando la Prueba Arcana:', error);
    }
    setLoading(false);
  };

  const selectAnswer = (questionId: string, answer: string) => {
    clickSound?.play();
    setSelectedOption(answer);
    setExamState(prev => ({
      ...prev,
      answers: {
        ...prev.answers,
        [questionId]: answer
      }
    }));
  };

  const nextQuestion = () => {
    if (examState.current_question < examState.questions.length - 1) {
      setSelectedOption(null);
      setExamState(prev => ({
        ...prev,
        current_question: prev.current_question + 1
      }));
    }
  };

  const previousQuestion = () => {
    if (examState.current_question > 0) {
      setSelectedOption(null);
      setExamState(prev => ({
        ...prev,
        current_question: prev.current_question - 1
      }));
    }
  };

  const submitExam = async () => {
    setLoading(true);
    epicSound?.play();
    try {
      await new Promise(resolve => setTimeout(resolve, 2500));
      
      setExamState(prev => ({
        ...prev,
        exam_completed: true
      }));
      
      // Simulate passing
      rankUpSound?.play();
      
      // Gamification rewards
      setOrbsEarned(prev => prev + 200);
      setHunterRank('B');
      
      await loadDashboard();
      setActiveTab('results');
    } catch (error) {
      console.error('⚔️ Error enviando Prueba Arcana:', error);
    }
    setLoading(false);
  };

  const getRankIcon = (rank: string) => {
    const rankIcons = {
      'E': { icon: <Shield className="w-8 h-8" />, color: 'text-gray-500', glow: '#6b7280' },
      'D': { icon: <Sword className="w-8 h-8" />, color: 'text-bronze-500', glow: '#92400e' },
      'C': { icon: <Eye className="w-8 h-8" />, color: 'text-blue-500', glow: '#3b82f6' },
      'B': { icon: <Brain className="w-8 h-8" />, color: 'text-purple-500', glow: '#8b5cf6' },
      'A': { icon: <Star className="w-8 h-8" />, color: 'text-yellow-500', glow: '#eab308' },
      'S': { icon: <Crown className="w-8 h-8" />, color: 'text-orange-500', glow: '#f97316' },
      'SS': { icon: <Trophy className="w-8 h-8" />, color: 'text-red-500', glow: '#ef4444' },
      'SSS': { icon: <Zap className="w-8 h-8" />, color: 'text-pink-500', glow: '#ec4899' }
    };
    const rankData = rankIcons[rank as keyof typeof rankIcons] || rankIcons['E'];
    return (
      <motion.div 
        className={`relative ${rankData.color}`}
        animate={{ 
          rotate: [0, 5, -5, 0],
          scale: [1, 1.1, 1]
        }}
        transition={{ duration: 3, repeat: Infinity }}
      >
        {rankData.icon}
        <motion.div
          className="absolute inset-0 blur-xl opacity-50"
          style={{ backgroundColor: rankData.glow }}
          animate={{ scale: [1, 1.3, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
      </motion.div>
    );
  };

  const formatTimeRemaining = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading && !dashboard) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-black to-gold-900/20" />
        <motion.div className="relative">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-32 h-32 border-4 border-gold-500 border-t-transparent rounded-full"
          />
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            className="absolute inset-4 w-24 h-24 border-4 border-purple-500 border-b-transparent rounded-full"
          />
          <Crown className="absolute inset-0 m-auto w-10 h-10 text-gold-500" />
        </motion.div>
      </div>
    );
  }

  // Exam View
  if (examState.exam_started && !examState.exam_completed) {
    const currentQuestion = examState.questions[examState.current_question];
    const progress = ((examState.current_question + 1) / examState.questions.length) * 100;

    return (
      <div className="min-h-screen bg-black relative overflow-hidden">
        {/* Epic background */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-900/30 via-black to-gold-900/30" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent" />
        </div>

        <div className="relative z-10 container mx-auto px-4 py-8">
          {/* Exam Header */}
          <motion.div 
            className="mb-8"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center justify-between mb-6">
              <motion.h1 
                className="text-3xl font-bold text-gold-400"
                animate={{ 
                  textShadow: [
                    "0 0 20px #ffd700",
                    "0 0 40px #ffd700",
                    "0 0 20px #ffd700"
                  ]
                }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                Prueba Arcana de Ascensión
              </motion.h1>
              <div className="flex items-center gap-4">
                <Badge className="bg-black/50 backdrop-blur-md border-purple-500/30 text-purple-300 px-4 py-2 flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  {formatTimeRemaining(examState.time_remaining)}
                </Badge>
                <Badge className="bg-black/50 backdrop-blur-md border-gold-500/30 text-gold-300 px-4 py-2">
                  Enigma {examState.current_question + 1} de {examState.questions.length}
                </Badge>
              </div>
            </div>
            
            <div className="relative h-3 bg-black/50 rounded-full overflow-hidden">
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-purple-600 to-gold-600"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5 }}
                style={{
                  boxShadow: '0 0 20px rgba(255, 215, 0, 0.8)'
                }}
              />
            </div>
          </motion.div>

          {/* Current Question */}
          {currentQuestion && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              key={currentQuestion.id}
            >
              <Card className="mb-8 bg-black/40 backdrop-blur-xl border-purple-500/30 overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-600/5 to-gold-600/5" />
                <CardHeader className="relative z-10">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-3 text-gold-400 text-2xl">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                      >
                        <Target className="w-7 h-7" />
                      </motion.div>
                      Enigma {currentQuestion.question_number}
                    </CardTitle>
                    <div className="flex items-center gap-3">
                      <Badge className={`
                        ${currentQuestion.difficulty === 1 ? 'bg-gradient-to-r from-green-600 to-emerald-600' : ''}
                        ${currentQuestion.difficulty === 2 ? 'bg-gradient-to-r from-yellow-600 to-orange-600' : ''}
                        ${currentQuestion.difficulty === 3 ? 'bg-gradient-to-r from-red-600 to-rose-600' : ''}
                        text-white shadow-lg
                      `}>
                        {currentQuestion.difficulty === 1 && '⚔️'}
                        {currentQuestion.difficulty === 2 && '🛡️'}
                        {currentQuestion.difficulty === 3 && '👑'}
                        Nivel {currentQuestion.difficulty}
                      </Badge>
                      <Badge className="bg-black/50 backdrop-blur-md border-purple-500/30 text-purple-300">
                        {currentQuestion.topic}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="relative z-10">
                  <motion.p 
                    className="text-xl mb-8 text-purple-200"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                  >
                    {currentQuestion.question_text}
                  </motion.p>
                  
                  <div className="space-y-4">
                    {currentQuestion.options.map((option, index) => {
                      const optionLetter = String.fromCharCode(65 + index);
                      const isSelected = examState.answers[currentQuestion.id] === optionLetter;
                      
                      return (
                        <motion.button
                          key={index}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.3 + index * 0.1 }}
                          whileHover={{ scale: 1.02, x: 10 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => selectAnswer(currentQuestion.id, optionLetter)}
                          onMouseEnter={() => hoverSound?.play()}
                          className={`w-full p-5 text-left border-2 rounded-xl transition-all ${
                            isSelected 
                              ? 'border-gold-500 bg-gradient-to-r from-gold-900/30 to-orange-900/30' 
                              : 'border-purple-500/30 hover:border-gold-400/50 bg-black/30 hover:bg-purple-900/20'
                          }`}
                          style={{
                            boxShadow: isSelected 
                              ? '0 0 30px rgba(255, 215, 0, 0.3)' 
                              : '0 0 10px rgba(139, 92, 246, 0.2)'
                          }}
                        >
                          <div className="flex items-start gap-4">
                            <motion.div 
                              className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-sm font-bold transition-all ${
                                isSelected 
                                  ? 'border-gold-500 bg-gradient-to-r from-gold-500 to-orange-500 text-black' 
                                  : 'border-purple-400 text-purple-300'
                              }`}
                              animate={isSelected ? { 
                                rotate: [0, 360],
                                scale: [1, 1.2, 1]
                              } : {}}
                              transition={{ duration: 0.5 }}
                            >
                              {optionLetter}
                            </motion.div>
                            <span className="text-purple-200 text-lg">{option}</span>
                          </div>
                        </motion.button>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Navigation */}
          <motion.div 
            className="flex items-center justify-between"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={previousQuestion}
              disabled={examState.current_question === 0}
              className="px-6 py-3 bg-black/50 backdrop-blur-md border border-purple-500/30 text-purple-300 rounded-lg hover:bg-purple-900/20 hover:border-purple-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg flex items-center gap-2"
              onMouseEnter={() => hoverSound?.play()}
            >
              <Swords className="w-5 h-5" />
              Enigma Anterior
            </motion.button>
            
            <div className="flex items-center gap-3 text-purple-300">
              <Sparkles className="w-5 h-5 text-gold-400" />
              <span className="text-sm font-medium">
                {Object.keys(examState.answers).length} de {examState.questions.length} enigmas resueltos
              </span>
            </div>
            
            {examState.current_question === examState.questions.length - 1 ? (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={submitExam}
                disabled={Object.keys(examState.answers).length < examState.questions.length}
                className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg flex items-center gap-2"
                style={{ boxShadow: '0 0 30px rgba(16, 185, 129, 0.5)' }}
              >
                <Trophy className="w-5 h-5" />
                Finalizar Prueba Arcana
              </motion.button>
            ) : (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={nextQuestion}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-gold-600 hover:from-purple-700 hover:to-gold-700 text-white rounded-lg font-bold transition-all shadow-lg flex items-center gap-2"
                style={{ boxShadow: '0 0 30px rgba(139, 92, 246, 0.5)' }}
                onMouseEnter={() => hoverSound?.play()}
              >
                Siguiente Enigma
                <Swords className="w-5 h-5" />
              </motion.button>
            )}
          </motion.div>
        </div>
      </div>
    );
  }

  // Main Dashboard View
  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      {/* Epic animated background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/30 via-black to-gold-900/30" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gold-900/20 via-transparent to-transparent" />
        
        {/* Floating particles */}
        {particles.map(particle => (
          <motion.div
            key={particle.id}
            className="absolute rounded-full blur-sm"
            initial={{ x: `${particle.x}%`, y: `${particle.y}%`, opacity: 0 }}
            animate={{ 
              y: '-120%', 
              opacity: [0, 1, 0],
              scale: [1, 1.5, 1]
            }}
            transition={{ duration: particle.speed, ease: "linear" }}
            style={{
              width: particle.size,
              height: particle.size,
              backgroundColor: particle.color,
              boxShadow: `0 0 ${particle.size * 3}px ${particle.color}`
            }}
          />
        ))}
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Epic Header */}
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, type: "spring" }}
          className="mb-8 text-center"
        >
          <motion.h1 
            className="text-5xl md:text-6xl font-bold mb-4 relative inline-block"
            animate={{ 
              textShadow: [
                "0 0 30px #ffd700",
                "0 0 60px #8a2be2",
                "0 0 30px #ffd700"
              ]
            }}
            transition={{ duration: 3, repeat: Infinity }}
          >
            <span className="bg-gradient-to-r from-gold-400 via-orange-400 to-purple-400 text-transparent bg-clip-text">
              REEVALUACIÓN ÉPICA DE RANGO HUNTER
            </span>
          </motion.h1>
          
          <motion.p 
            className="text-xl text-purple-300 mb-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            Demuestra tu poder en pruebas arcanas y asciende entre las leyendas
          </motion.p>
          
          {/* Player Status */}
          <motion.div 
            className="flex items-center justify-center gap-6 mt-6"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.7 }}
          >
            <div className="flex items-center gap-3 bg-black/50 backdrop-blur-md rounded-full px-6 py-3 border border-gold-500/30">
              <Crown className="w-6 h-6 text-gold-400" />
              <div className="text-left">
                <div className="text-xs text-purple-400">Rango Actual</div>
                <div className="text-xl font-bold text-gold-400">{hunterRank}</div>
              </div>
            </div>
            
            <div className="flex items-center gap-3 bg-black/50 backdrop-blur-md rounded-full px-6 py-3 border border-purple-500/30">
              <Gem className="w-6 h-6 text-purple-400" />
              <div className="text-left">
                <div className="text-xs text-purple-400">Orbes de Poder</div>
                <div className="text-xl font-bold text-purple-300">{orbsEarned} 💎</div>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {dashboard && (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-4 bg-black/50 backdrop-blur-xl rounded-xl border border-purple-500/30 p-1">
              {[
                { value: 'overview', label: 'Resumen de Gloria', icon: Crown },
                { value: 'eligibility', label: 'Dignidad', icon: Shield },
                { value: 'history', label: 'Crónicas', icon: Scroll },
                { value: 'results', label: 'Conquistas', icon: Trophy }
              ].map((tab) => (
                <TabsTrigger 
                  key={tab.value}
                  value={tab.value}
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-600 data-[state=active]:to-gold-600 data-[state=active]:text-white transition-all"
                  onMouseEnter={() => hoverSound?.play()}
                >
                  <tab.icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              {/* Current Status Card */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
              >
                <Card className="bg-black/40 backdrop-blur-xl border-purple-500/30 overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-600/5 to-gold-600/5" />
                  <CardHeader className="relative z-10">
                    <CardTitle className="flex items-center gap-3 text-gold-400 text-2xl">
                      <motion.div
                        animate={{ 
                          rotate: [0, 360],
                          scale: [1, 1.2, 1]
                        }}
                        transition={{ duration: 3, repeat: Infinity }}
                      >
                        <Crown className="w-7 h-7" />
                      </motion.div>
                      Tu Gloria Actual como Hunter
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="relative z-10">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                      {[
                        { 
                          label: 'Rango Actual', 
                          value: dashboard.user_info.current_rank,
                          icon: getRankIcon(dashboard.user_info.current_rank)
                        },
                        { 
                          label: 'Nivel Arcano', 
                          value: dashboard.user_info.current_level,
                          icon: <motion.div
                            className="text-blue-400"
                            animate={{ y: [0, -5, 0] }}
                            transition={{ duration: 2, repeat: Infinity }}
                          >
                            <Sparkles className="w-8 h-8" />
                          </motion.div>
                        },
                        { 
                          label: 'Esencia Acumulada', 
                          value: dashboard.user_info.experience.toLocaleString(),
                          icon: <motion.div
                            className="text-purple-400"
                            animate={{ 
                              scale: [1, 1.2, 1],
                              rotate: [0, 180, 360]
                            }}
                            transition={{ duration: 3, repeat: Infinity }}
                          >
                            <Gem className="w-8 h-8" />
                          </motion.div>
                        }
                      ].map((stat, index) => (
                        <motion.div
                          key={index}
                          className="text-center"
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.2 + index * 0.1 }}
                          whileHover={{ scale: 1.05 }}
                        >
                          <div className="mb-3">{stat.icon}</div>
                          <div className="text-3xl font-bold text-gold-300">{stat.value}</div>
                          <div className="text-sm text-purple-300 mt-1">{stat.label}</div>
                        </motion.div>
                      ))}
                    </div>
                    
                    {!dashboard.user_info.next_rank_requirements.is_max_rank && (
                      <motion.div 
                        className="p-6 bg-gradient-to-r from-purple-900/30 to-gold-900/30 rounded-xl border border-gold-500/30"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.5 }}
                        style={{ boxShadow: '0 0 30px rgba(255, 215, 0, 0.2)' }}
                      >
                        <div className="flex items-center gap-3 mb-3">
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                          >
                            <TrendingUp className="w-6 h-6 text-gold-400" />
                          </motion.div>
                          <span className="font-bold text-gold-300 text-lg">
                            Próximo Rango: {dashboard.user_info.next_rank_requirements.next_rank}
                          </span>
                        </div>
                        <p className="text-purple-200">
                          {dashboard.user_info.next_rank_requirements.requirements}
                        </p>
                      </motion.div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>

              {/* Eligibility Status */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
              >
                <Card className="bg-black/40 backdrop-blur-xl border-purple-500/30 overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-green-600/5 to-red-600/5" />
                  <CardHeader className="relative z-10">
                    <CardTitle className="flex items-center gap-3 text-gold-400 text-2xl">
                      <Award className="w-7 h-7" />
                      Estado de Dignidad para la Prueba
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="relative z-10">
                    {dashboard.eligibility.eligible ? (
                      <Alert className="bg-green-900/20 border-green-500/30 mb-6">
                        <CheckCircle className="h-5 w-5 text-green-400" />
                        <AlertTitle className="text-green-300 text-lg">¡Eres Digno de la Prueba Legendaria!</AlertTitle>
                        <AlertDescription className="text-purple-200 mt-2">
                          {dashboard.eligibility.reason}
                        </AlertDescription>
                      </Alert>
                    ) : (
                      <Alert className="bg-red-900/20 border-red-500/30 mb-6">
                        <XCircle className="h-5 w-5 text-red-400" />
                        <AlertTitle className="text-red-300 text-lg">Aún No Eres Digno</AlertTitle>
                        <AlertDescription className="text-purple-200 mt-2">
                          {dashboard.eligibility.reason}
                        </AlertDescription>
                      </Alert>
                    )}
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {[
                        { 
                          value: dashboard.eligibility.eligible_count, 
                          label: 'Reinos Conquistados',
                          color: 'from-green-600 to-emerald-600',
                          icon: CheckCircle
                        },
                        { 
                          value: dashboard.eligibility.total_subjects, 
                          label: 'Reinos Totales',
                          color: 'from-blue-600 to-cyan-600',
                          icon: BookOpen
                        },
                        { 
                          value: dashboard.exam_config.questions_per_subject, 
                          label: 'Enigmas por Prueba',
                          color: 'from-purple-600 to-pink-600',
                          icon: Target
                        }
                      ].map((metric, index) => (
                        <motion.div
                          key={index}
                          className="relative overflow-hidden rounded-xl p-6 bg-gradient-to-br from-black/60 to-black/30 border border-purple-500/20"
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: 0.4 + index * 0.1 }}
                          whileHover={{ scale: 1.05 }}
                        >
                          <div className={`absolute inset-0 bg-gradient-to-br ${metric.color} opacity-10`} />
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                            className="absolute -right-4 -top-4 opacity-10"
                          >
                            <metric.icon className="w-24 h-24" />
                          </motion.div>
                          <div className="relative z-10 text-center">
                            <div className="text-3xl font-bold text-white mb-2">{metric.value}</div>
                            <div className="text-sm text-purple-300">{metric.label}</div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            <TabsContent value="eligibility" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {Object.entries(dashboard.eligibility.subjects_status).map(([key, status], index) => (
                  <motion.div
                    key={key}
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    whileHover={{ y: -5 }}
                    onHoverStart={() => {
                      setHoveredCard(key);
                      hoverSound?.play();
                    }}
                    onHoverEnd={() => setHoveredCard(null)}
                  >
                    <Card className={`relative overflow-hidden bg-black/40 backdrop-blur-xl transition-all duration-300 ${
                      status.eligible 
                        ? 'border-green-500/30 hover:border-gold-400/50' 
                        : 'border-gray-500/30 hover:border-purple-400/30'
                    }`}
                    style={{
                      boxShadow: hoveredCard === key 
                        ? `0 0 30px ${status.eligible ? 'rgba(255, 215, 0, 0.3)' : 'rgba(139, 92, 246, 0.2)'}` 
                        : 'none'
                    }}
                    >
                      {/* Shimmer effect */}
                      <motion.div
                        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"
                        animate={{
                          x: hoveredCard === key ? ['-200%', '200%'] : '-200%',
                        }}
                        transition={{
                          duration: 1.5,
                          ease: "linear"
                        }}
                      />
                      
                      <CardHeader className="relative z-10">
                        <div className="flex items-center justify-between">
                          <CardTitle className="flex items-center gap-3 text-gold-400 text-xl">
                            <motion.div
                              animate={hoveredCard === key ? { 
                                rotate: [0, 10, -10, 0],
                                scale: [1, 1.1, 1]
                              } : {}}
                              transition={{ duration: 0.5 }}
                            >
                              <SubjectIcon subjectName={status.subject_name || 'Unknown'} size={28} />
                            </motion.div>
                            {status.subject_name}
                          </CardTitle>
                          {status.eligible ? (
                            <motion.div
                              animate={{ scale: [1, 1.1, 1] }}
                              transition={{ duration: 2, repeat: Infinity }}
                            >
                              <Badge className="bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg">
                                <CheckCircle className="w-4 h-4 mr-1" />
                                Digno
                              </Badge>
                            </motion.div>
                          ) : (
                            <Badge className="bg-gray-900/80 text-gray-400 border-gray-700">
                              <XCircle className="w-4 h-4 mr-1" />
                              No Digno
                            </Badge>
                          )}
                        </div>
                      </CardHeader>
                      
                      <CardContent className="relative z-10 space-y-4">
                        {/* Progress bars */}
                        {[
                          { 
                            icon: BookOpen, 
                            label: 'Plan de Conquista', 
                            data: status.plan_completion,
                            color: 'from-blue-500 to-cyan-500'
                          },
                          { 
                            icon: Video, 
                            label: 'Pergaminos Visuales', 
                            data: status.video_completion,
                            color: 'from-purple-500 to-pink-500'
                          },
                          { 
                            icon: Target, 
                            label: 'Combates Prácticos', 
                            data: status.exercise_completion,
                            color: 'from-orange-500 to-red-500'
                          }
                        ].map((item, idx) => (
                          <motion.div
                            key={idx}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.2 + idx * 0.1 }}
                          >
                            <div className="flex justify-between text-sm mb-2">
                              <span className="flex items-center gap-2 text-purple-300">
                                <item.icon className="w-4 h-4" />
                                {item.label}
                              </span>
                              <span className="text-gold-300 font-bold">{item.data.percentage}%</span>
                            </div>
                            <div className="relative h-3 bg-black/50 rounded-full overflow-hidden">
                              <motion.div
                                className={`absolute inset-0 bg-gradient-to-r ${item.color}`}
                                initial={{ width: 0 }}
                                animate={{ width: `${item.data.percentage}%` }}
                                transition={{ duration: 1, delay: 0.3 + idx * 0.1 }}
                                style={{
                                  boxShadow: `0 0 10px ${item.color.includes('blue') ? '#3b82f6' : item.color.includes('purple') ? '#8b5cf6' : '#f97316'}`
                                }}
                              />
                            </div>
                            <p className="text-xs text-gray-400 mt-1">
                              {item.data.completed}/{item.data.total} completados
                            </p>
                          </motion.div>
                        ))}

                        <div className="pt-4 border-t border-purple-500/20">
                          <p className="text-sm text-purple-200 mb-4">{status.reason}</p>
                          
                          {status.eligible ? (
                            <motion.button
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                              onClick={() => startExam(status.subject_id || '')}
                              disabled={loading}
                              className="w-full py-3 px-6 bg-gradient-to-r from-gold-600 to-orange-600 hover:from-gold-700 hover:to-orange-700 text-white rounded-lg font-bold transition-all shadow-lg flex items-center justify-center gap-2"
                              style={{ boxShadow: '0 0 30px rgba(255, 215, 0, 0.5)' }}
                            >
                              <Trophy className="w-5 h-5" />
                              Iniciar Prueba ({status.next_exam_info.questions_count} enigmas)
                            </motion.button>
                          ) : (
                            <Button 
                              variant="outline" 
                              className="w-full opacity-50 cursor-not-allowed" 
                              disabled
                            >
                              <AlertTriangle className="w-5 h-5 mr-2" />
                              Cumple los Requisitos Arcanos
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="history" className="space-y-6">
              {dashboard.reevaluation_history.length > 0 ? (
                <div className="space-y-4">
                  {dashboard.reevaluation_history.map((attempt, index) => (
                    <motion.div
                      key={attempt.id}
                      initial={{ opacity: 0, x: -50 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      whileHover={{ x: 10 }}
                    >
                      <Card className="bg-black/40 backdrop-blur-xl border-purple-500/30 hover:border-gold-400/30 transition-all">
                        <CardContent className="p-6">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <motion.div
                                animate={{ 
                                  rotate: [0, 360],
                                  scale: [1, 1.1, 1]
                                }}
                                transition={{ 
                                  duration: 3,
                                  delay: index * 0.2,
                                  repeat: Infinity 
                                }}
                              >
                                <SubjectIcon subjectName={attempt.subject_name} size={40} />
                              </motion.div>
                              <div>
                                <h4 className="font-bold text-lg text-gold-400">{attempt.subject_name}</h4>
                                <p className="text-sm text-purple-300">
                                  {new Date(attempt.date).toLocaleDateString('es-ES', {
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric'
                                  })}
                                </p>
                              </div>
                            </div>
                            
                            <div className="text-right">
                              <div className="flex items-center gap-3 mb-2">
                                <span className="text-3xl font-bold text-gold-300">{attempt.score}%</span>
                                {attempt.passed ? (
                                  <Badge className="bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg">
                                    <CheckCircle className="w-4 h-4 mr-1" />
                                    Victoria Épica
                                  </Badge>
                                ) : (
                                  <Badge className="bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-lg">
                                    <XCircle className="w-4 h-4 mr-1" />
                                    Derrota Honorable
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-purple-300">
                                {attempt.questions_answered} enigmas enfrentados
                              </p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <Card className="bg-black/40 backdrop-blur-xl border-purple-500/30">
                    <CardContent className="text-center py-16">
                      <motion.div
                        animate={{ 
                          y: [0, -10, 0],
                          rotate: [0, 5, -5, 0]
                        }}
                        transition={{ duration: 3, repeat: Infinity }}
                      >
                        <Calendar className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                      </motion.div>
                      <h3 className="text-xl font-bold text-gold-400 mb-2">Sin Crónicas Ancestrales</h3>
                      <p className="text-purple-300">Las páginas de tu historia épica esperan ser escritas</p>
                    </CardContent>
                  </Card>
                </motion.div>
              )}
            </TabsContent>

            <TabsContent value="results" className="space-y-6">
              {examState.exam_completed ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ type: "spring" }}
                >
                  <Card className="bg-black/40 backdrop-blur-xl border-gold-500/30 overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-gold-600/10 to-purple-600/10" />
                    <CardHeader className="relative z-10">
                      <CardTitle className="flex items-center gap-3 text-gold-400 text-2xl justify-center">
                        <motion.div
                          animate={{ 
                            rotate: [0, 360],
                            scale: [1, 1.3, 1]
                          }}
                          transition={{ duration: 2 }}
                        >
                          <Trophy className="w-8 h-8" />
                        </motion.div>
                        Resultado de la Prueba Arcana
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="relative z-10">
                      <div className="text-center py-8">
                        <motion.div
                          className="text-7xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400 mb-6"
                          animate={{ 
                            scale: [1, 1.1, 1],
                            textShadow: [
                              "0 0 30px #10b981",
                              "0 0 60px #10b981",
                              "0 0 30px #10b981"
                            ]
                          }}
                          transition={{ duration: 2, repeat: Infinity }}
                        >
                          85%
                        </motion.div>
                        
                        <motion.div 
                          className="text-2xl font-bold text-gold-400 mb-3"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.5 }}
                        >
                          ¡GLORIA ETERNA ALCANZADA!
                        </motion.div>
                        
                        <p className="text-purple-200 mb-8 text-lg">
                          Has demostrado tu valía y ascendido entre las leyendas
                        </p>
                        
                        {/* Rank transition */}
                        <div className="flex items-center justify-center gap-8 mb-8">
                          <motion.div 
                            className="text-center"
                            initial={{ opacity: 0, x: -50 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.7 }}
                          >
                            <div className="text-sm text-purple-300 mb-2">Rango Anterior</div>
                            <div className="flex items-center justify-center gap-2">
                              {getRankIcon("C")}
                              <span className="text-2xl font-bold text-purple-300">C</span>
                            </div>
                          </motion.div>
                          
                          <motion.div
                            animate={{ x: [0, 10, 0] }}
                            transition={{ duration: 1, repeat: Infinity }}
                            className="text-3xl text-gold-400"
                          >
                            →
                          </motion.div>
                          
                          <motion.div 
                            className="text-center"
                            initial={{ opacity: 0, x: 50 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.9 }}
                          >
                            <div className="text-sm text-purple-300 mb-2">Nuevo Rango</div>
                            <div className="flex items-center justify-center gap-2">
                              {getRankIcon("B")}
                              <span className="text-2xl font-bold text-gold-400">B</span>
                            </div>
                          </motion.div>
                        </div>
                        
                        {/* Rewards */}
                        <motion.div 
                          className="grid grid-cols-3 gap-6 max-w-2xl mx-auto"
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 1.1 }}
                        >
                          {[
                            { value: '+1000', label: 'Esencia (EXP)', color: 'from-purple-600 to-pink-600', icon: Sparkles },
                            { value: '+200', label: 'Orbes Mágicos', color: 'from-blue-600 to-cyan-600', icon: Gem },
                            { value: '+50', label: 'Cristales Legendarios', color: 'from-gold-600 to-orange-600', icon: Star }
                          ].map((reward, index) => (
                            <motion.div
                              key={index}
                              className="relative overflow-hidden rounded-xl p-6 bg-gradient-to-br from-black/60 to-black/30 border border-purple-500/20"
                              whileHover={{ scale: 1.05 }}
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: 1.3 + index * 0.1 }}
                            >
                              <div className={`absolute inset-0 bg-gradient-to-br ${reward.color} opacity-20`} />
                              <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                                className="absolute -right-4 -top-4 opacity-20"
                              >
                                <reward.icon className="w-24 h-24" />
                              </motion.div>
                              <div className="relative z-10 text-center">
                                <div className="text-2xl font-bold text-white mb-1">{reward.value}</div>
                                <div className="text-xs text-purple-300">{reward.label}</div>
                              </div>
                            </motion.div>
                          ))}
                        </motion.div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <Card className="bg-black/40 backdrop-blur-xl border-purple-500/30">
                    <CardContent className="text-center py-16">
                      <motion.div
                        animate={{ 
                          y: [0, -10, 0],
                          scale: [1, 1.1, 1]
                        }}
                        transition={{ duration: 3, repeat: Infinity }}
                      >
                        <Trophy className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                      </motion.div>
                      <h3 className="text-xl font-bold text-gold-400 mb-2">Sin Conquistas Aún</h3>
                      <p className="text-purple-300">Completa una Prueba Arcana para revelar tus glorias</p>
                    </CardContent>
                  </Card>
                </motion.div>
              )}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
}