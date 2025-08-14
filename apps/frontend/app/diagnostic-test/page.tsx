'use client';

// React and Next.js imports
import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';

// Animation imports
import { motion, AnimatePresence } from 'framer-motion';

// UI Component imports
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

// Icon imports
import { 
  Clock, Sparkles, Shield, Swords, Trophy, Loader2, AlertCircle,
  Unlock, Lock, PlayCircle, CheckCircle, Star, XCircle, Brain,
  Zap, BarChart3, BookOpen, Play, Target
} from 'lucide-react';

// Service imports - FIXED: Import axios here, not dynamically
import api, { apiClient, tokenManager } from '@/lib/axios';  // ✅ FIXED IMPORT
import { websocketService } from '../services/websocket.service';
import { cacheService } from '../services/cache.service';
import { useAnalytics } from '../services/analytics.service';
import { useSound } from '../components/SoundManager';

// Component imports
import { ErrorBoundary } from '../components/ErrorBoundary';
import MultimediaQuestion from '../components/MultimediaQuestion';
import QuestionNavigation from '../components/QuestionNavigation';
import { QuestionCard } from '../components/gamified/QuestionCard';
import { AnswerOption } from '../components/gamified/AnswerOption';
import { GameStats } from '../components/gamified/GameStats';
import { AchievementPopup } from '../components/gamified/AchievementPopup';
import { NavigationPills } from '../components/gamified/NavigationPills';
import { useGameSounds } from '../hooks/useGameSounds';
import SubjectIcon from '../components/SubjectIcon';
import VideoPlayer from '../components/VideoPlayer';

// ============= CONFIGURATION =============
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
const API_BASE = `${BACKEND_URL}/api/v1`;
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:4002';

// Epic sound effects for diagnostic experience
const hoverSound = typeof Audio !== 'undefined' ? new Audio('/sounds/hover.mp3') : null;
const aiRecommendationSound = typeof Audio !== 'undefined' ? new Audio('/sounds/success.mp3') : null;
const videoPlaySound = typeof Audio !== 'undefined' ? new Audio('/sounds/unlock.mp3') : null;

// ============= TYPE DEFINITIONS =============
interface Question {
  id: string;
  question_text: string;
  options: Record<string, string>;
  subject: string;
  topic: string;
  difficulty: number;
  hint?: string;
  image_url?: string;
  options_images?: Record<string, string>;
}

interface TestResult {
  subject: string;
  score: number;
  total_questions: number;
  percentage: number;
  time_spent_minutes: number;
  strengths: string[];
  weaknesses: string[];
  score_by_topic: Record<string, number>;
  recommendations: string[];
}

interface Subject {
  id: string;
  name: string;
  description: string;
  icon_url: string;
  color: string;
  config: {
    total_questions: number;
    time_limit_minutes: number;
    topics: string[];
  };
}

interface StudyPlanTopic {
  name: string;
  difficulty: number;
  questions: number;
  tags: string[];
  video_url?: string;
  completed: boolean;
  video_watched: boolean;
  exercises_completed: number;
  total_exercises: number;
}

interface StudyPlanUnit {
  unit_number: number;
  name: string;
  description: string;
  topics: StudyPlanTopic[];
  video_urls: Record<string, string>;
  reading_materials: Record<string, string>;
  learning_objectives: string[];
  exercise_count: number;
  recommendations: {
    priority: string;
    weak_areas: string[];
    focus_topics: string[];
    study_time: string;
    custom_tips: string[];
  };
  unlocked: boolean;
  progress: number;
  video_progress: Record<string, number>;
  exercise_progress: Record<string, number>;
  ai_recommended: boolean;
  estimated_completion_time: number;
  difficulty_level: number;
  icfes_weight: number;
}

interface AdaptiveStudyPlan {
  subject: string;
  title: string;
  description: string;
  units: StudyPlanUnit[];
  total_questions: number;
  total_videos: number;
  estimated_time: string;
  difficulty_curve: string;
  icfes_weight: number;
  exam_sections: string[];
  personalization: {
    based_on_performance: boolean;
    adaptation_date: string;
    focus_areas: string[];
  };
}

// ... (rest of your interfaces remain the same)

// Helper unificado para obtener token
// ============= HELPER FUNCTIONS =============
const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return tokenManager.getToken();  // Use the tokenManager from axios
};

export default function FusedAdaptiveLearning() {
  // Services
  const { 
    trackPageView, 
    trackDiagnosticStart, 
    trackDiagnosticComplete,
    trackVideoWatch,
    trackButtonClick 
  } = useAnalytics();

  // Sound effects
  const {
    playClickSound,
    playHoverSound,
    playSuccessSound,
    playErrorSound,
    playLevelUpSound,
    playMagicSound,
    playVictorySound
  } = useSound();

  // Navigation states
  const [currentPhase, setCurrentPhase] = useState<'selection' | 'diagnostic' | 'results' | 'studyplan'>('selection');
  
  // Diagnostic test states
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [responseTimes, setResponseTimes] = useState<Record<string, number>>({});
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [testStarted, setTestStarted] = useState(false);
  const [currentTestId, setCurrentTestId] = useState<string | null>(null);
  
  // Study plan states
  const [studyPlan, setStudyPlan] = useState<AdaptiveStudyPlan | null>(null);
  const [selectedUnit, setSelectedUnit] = useState<StudyPlanUnit | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<StudyPlanTopic | null>(null);
  const [showVideoPlayer, setShowVideoPlayer] = useState(false);

  // Gamification lightweight states (visible durante diagnóstico)
  const [streak, setStreak] = useState<number>(0);
  const [hearts, setHearts] = useState<number>(3);
  const [level, setLevel] = useState<number>(1);
  
  // Shared states
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [realDataState, setRealDataState] = useState({
    subjectsLoaded: false,
    profileLoaded: false,
    historyLoaded: false,
    metricsLoaded: false
  });
  
  // Gamification states
  const [userMetrics, setUserMetrics] = useState({
    overall_progress: 0,
    completed_units: 0,
    total_videos_watched: 0,
    total_exercises_completed: 0,
    current_streak: 0,
    average_accuracy: 0,
    diagnostic_score: 0
  });
  const [orbsEarned, setOrbsEarned] = useState(0);
  const [hunterRank, setHunterRank] = useState('F'); // Starts at F after diagnostic

  // Load all data on mount for better performance
  useEffect(() => {
    // Initialize services
    websocketService.connect();
    
    // Track page view once on mount
    trackPageView('diagnostic-test');
    
    // WebSocket subscriptions
    websocketService.subscribe('diagnostic_update', (data) => {
      // Real-time updates for diagnostic progress
      console.log('Diagnostic update received:', data);
    });
    
    websocketService.subscribe('leaderboard_update', (data) => {
      // Real-time leaderboard updates
      console.log('Leaderboard update received:', data);
    });

    Promise.all([
      loadSubjects(),
      loadUserProfile(),
      loadTestHistory(),
      loadProgressMetrics()
    ]).catch(error => {
      console.error('Error loading initial data:', error);
    });

    return () => {
      websocketService.disconnect();
    };
  }, []); // Remove trackPageView from dependencies

  const loadSubjects = async () => {
    try {
      setIsLoading(true);
      
      // Try to get from cache first
      const cachedSubjectsUnknown = cacheService.getSubjects() as unknown;
      const cachedSubjects = Array.isArray(cachedSubjectsUnknown) ? (cachedSubjectsUnknown as Subject[]) : null;
      if (cachedSubjects) {
        setSubjects(cachedSubjects);
        setRealDataState(prev => ({ ...prev, subjectsLoaded: true }));
        return;
      }

      const response = await fetch(`${API_BASE}/diagnostic/subjects`);
      if (response.ok) {
        const subjectsData: Subject[] = await response.json();
        setSubjects(subjectsData as Subject[]);
        // Cache for future use
        cacheService.cacheSubjects(subjectsData);
        setRealDataState(prev => ({ ...prev, subjectsLoaded: true }));
      } else {
        // Fallback to mock data if API fails
        setSubjects(mockSubjects);
      }
    } catch (error) {
      console.error('Error loading subjects:', error);
      // Fallback to mock data
      setSubjects(mockSubjects);
    } finally {
      setIsLoading(false);
    }
  };

  const loadUserProfile = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      // Add token if available, but don't require it in development
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/users/cached/profile/me`, {
        headers
      });
      
      if (response.ok) {
        const profileData = await response.json();
        setUserMetrics(prev => ({
          ...prev,
          current_streak: profileData.streak_days || 0,
          total_videos_watched: profileData.questions_answered || 0
        }));
      } else {
        console.warn('Failed to load user profile:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error loading user profile:', error);
    }
  };

  const loadTestHistory = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      // Add token if available, but don't require it in development
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/diagnostic/tests`, {
        headers
      });
      
      if (response.ok) {
        const historyData = await response.json();
        console.log('Diagnostic history loaded:', historyData.length);
        // Update metrics based on history
        if (historyData.length > 0) {
          const latestTest = historyData[0];
          setUserMetrics(prev => ({
            ...prev,
            diagnostic_score: latestTest.score_percentage || 0
          }));
        }
      } else {
        console.warn('Failed to load test history:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error loading test history:', error);
    }
  };

  const loadProgressMetrics = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      // Add token if available, but don't require it in development
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/analytics/personal`, {
        headers
      });
      
      if (response.ok) {
        const metricsData = await response.json();
        setUserMetrics(prev => ({
          ...prev,
          overall_progress: metricsData.overall_accuracy || 0,
          completed_units: metricsData.total_battles || 0,
          average_accuracy: metricsData.overall_accuracy || 0,
          total_exercises_completed: metricsData.total_questions_answered || 0
        }));
      } else {
        console.warn('Failed to load progress metrics:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error loading progress metrics:', error);
    }
  };

  // Fallback mock subjects (only used if API fails)
  const mockSubjects: Subject[] = [
    { 
      id: '550e8400-e29b-41d4-a716-446655440001', 
      name: 'Matemáticas',
      description: 'Domina el arte de los números y las ecuaciones',
      icon_url: '/assets/images/subjects/matematicasicon.png',
      color: '#8B5CF6',
      config: {
        total_questions: 20,
        time_limit_minutes: 30,
        topics: ['Álgebra', 'Geometría', 'Trigonometría', 'Cálculo']
      }
    },
    { 
      id: '550e8400-e29b-41d4-a716-446655440002', 
      name: 'Lenguaje',
      description: 'Conquista el poder de las palabras',
      icon_url: '/assets/images/subjects/lecturaicon.png',
      color: '#3B82F6',
      config: {
        total_questions: 20,
        time_limit_minutes: 30,
        topics: ['Comprensión', 'Gramática', 'Literatura', 'Redacción']
      }
    },
    { 
      id: '550e8400-e29b-41d4-a716-446655440003', 
      name: 'Ciencias Naturales',
      description: 'Descubre los secretos del universo',
      icon_url: '/assets/images/subjects/cienciasnaturalesicon.png',
      color: '#10B981',
      config: {
        total_questions: 20,
        time_limit_minutes: 30,
        topics: ['Física', 'Química', 'Biología', 'Ecología']
      }
    },
    { 
      id: '550e8400-e29b-41d4-a716-446655440004', 
      name: 'Ciencias Sociales',
      description: 'Explora la historia y la sociedad',
      icon_url: '/assets/images/subjects/socialesicon.png',
      color: '#F59E0B',
      config: {
        total_questions: 20,
        time_limit_minutes: 30,
        topics: ['Historia', 'Geografía', 'Economía', 'Filosofía']
      }
    },
    { 
      id: '550e8400-e29b-41d4-a716-446655440005', 
      name: 'Inglés',
      description: 'Master the global language',
      icon_url: '/assets/images/subjects/englishicon.png',
      color: '#EF4444',
      config: {
        total_questions: 20,
        time_limit_minutes: 25,
        topics: ['Grammar', 'Reading', 'Vocabulary', 'Writing']
      }
    }
  ];

  useEffect(() => {
    if (testStarted && timeRemaining > 0) {
      const timer = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            handleTimeUp();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [testStarted, timeRemaining]);

  // FIXED startDiagnosticTest function
  const startDiagnosticTest = async (subject: Subject) => {
    setIsLoading(true);
    setSelectedSubject(subject);
    
    try {
      console.log('🚀 Starting diagnostic test for:', subject.name);
      
      const token = getAuthToken();
      console.log('🔐 Auth token present:', !!token);
      
      // Create test using the imported api client
      const testResponse = await apiClient.post('/diagnostic/tests', {
        subject_id: subject.id,
        test_type: 'real_icfes'
      });

      console.log('✅ Test created:', testResponse);
      setCurrentTestId(testResponse.id);

      // Load questions
      const questionsData = await apiClient.get(`/diagnostic/tests/${testResponse.id}/questions`);
      
      console.log('✅ Questions loaded:', questionsData.length);
      
      setQuestions(questionsData);
      setTimeRemaining(subject.config.time_limit_minutes * 60);
      setTestStarted(true);
      setCurrentPhase('diagnostic');
      playClickSound();
      
    } catch (error: any) {
      console.error('❌ Error starting diagnostic test:', error);
      
      const errorMessage = error.response?.data?.detail || 
                          error.message || 
                          'Failed to start test';
      
      alert(`Cannot start test: ${errorMessage}\n\nMake sure the backend is running on port ${BACKEND_URL}`);
      
    } finally {
      setIsLoading(false);
    }
  };

  // Fallback mock function (only used if API fails)
  const startMockDiagnosticTest = async (subject: Subject) => {
    const mockQuestions: Question[] = Array.from({ length: subject.config.total_questions }, (_, i) => ({
      id: `mock-q${i + 1}`,
      question_text: `[MOCK] Pregunta ${i + 1} de ${subject.name}: Esta es una pregunta de ejemplo`,
      options: {
        A: 'Primera opción (mock)',
        B: 'Segunda opción (mock)',
        C: 'Tercera opción (mock)',
        D: 'Cuarta opción (mock)'
      },
      subject: subject.name,
      topic: subject.config.topics[i % subject.config.topics.length],
      difficulty: Math.floor(Math.random() * 3) + 1,
      hint: '[MOCK] Piensa en los conceptos fundamentales'
    }));
    
    setQuestions(mockQuestions);
    setTimeRemaining(subject.config.time_limit_minutes * 60);
    setTestStarted(true);
    setCurrentPhase('diagnostic');
  };

  const questionShownAtRef = useRef<Record<string, number>>({});
  useEffect(() => {
    try {
      const q = questions[currentQuestion] as any;
      if (q && q.id) {
        questionShownAtRef.current[q.id] = Date.now();
      }
    } catch {}
  }, [questions, currentQuestion]);

  const handleAnswer = (questionId: string, answer: string) => {
    const now = Date.now();
    setAnswers(prev => ({
      ...prev,
      [questionId]: (answer || '').toLowerCase()
    }));
    setResponseTimes(prev => ({
      ...prev,
      [questionId]: Math.max(0, now - (questionShownAtRef.current[questionId] || now))
    }));
    hoverSound?.play();
  };

  const handleTimeUp = () => {
    setTestStarted(false);
    handleSubmitTest();
  };

  // FIXED handleSubmitTest function - no dynamic import
  const handleSubmitTest = async () => {
    if (!selectedSubject || questions.length === 0) return;
    
    setIsSubmitting(true);
    
    try {
      // 1. Validate token
      const token = getAuthToken();
      if (!token) {
        console.warn('No auth token found, proceeding anyway in dev mode');
      }
      
      // 2. Validate test
      if (!currentTestId) {
        throw new Error('No active test. Please start the diagnostic again.');
      }
      
      // 3. Validate answers
      const unanswered = questions.filter(q => !answers[q.id]);
      if (unanswered.length > 0) {
        throw new Error(`Please answer all questions (${unanswered.length} remaining)`);
      }
      
      // 4. Prepare submission
      const answersArray = Object.entries(answers).map(([questionId, answer]) => ({
        question_id: questionId,
        user_answer: String(answer).trim().toUpperCase(),
        response_time_ms: Math.max(0, Math.min(2147483647, responseTimes[questionId] || 0))
      }));
      
      console.log('📤 Submitting diagnostic test:', {
        testId: currentTestId,
        totalAnswers: answersArray.length,
        endpoint: `/diagnostic/tests/${currentTestId}/submit`
      });
      
      // 5. ✅ FIXED: Use the imported api client directly
      const submitResponse = await api.post(`/diagnostic/tests/${currentTestId}/submit`, {
        answers: answersArray
      });
      
      const result = submitResponse.data;
      console.log('✅ Test submitted successfully:', result);
      
      // 6. Update state with results
      setTestResults([result]);
      setUserMetrics(prev => ({ 
        ...prev, 
        diagnostic_score: result.percentage || 0 
      }));
      
      // 7. Gamification rewards
      const orbsAwarded = Math.floor((result.percentage || 0) / 2);
      setOrbsEarned(prev => prev + orbsAwarded);
      
      if (result.percentage >= 80) setHunterRank('D');
      else if (result.percentage >= 70) setHunterRank('E');
      else setHunterRank('F');
      
      // 8. Transition to results
      playLevelUpSound();
      setCurrentPhase('results');
      
      // 9. Track analytics
      trackDiagnosticComplete(selectedSubject.name, result.percentage);
      
    } catch (error: any) {
      console.error('❌ Error submitting test:', error);
      
      // Show user-friendly error
      const errorMessage = error.response?.data?.detail || 
                          error.message || 
                          'Failed to submit test. Please try again.';
      
      alert(`Error: ${errorMessage}`);
      
    } finally {
      setIsSubmitting(false);
    }
  };

  // ... (rest of your component code remains the same)

  // Fallback mock function (only used if API fails)
  const handleMockSubmitTest = async () => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const score = Math.floor(Math.random() * 30) + 50;
    const result: TestResult = {
      subject: selectedSubject!.name,
      score: score,
      total_questions: questions.length,
      percentage: score,
      time_spent_minutes: Math.floor((selectedSubject!.config.time_limit_minutes * 60 - timeRemaining) / 60),
      strengths: score > 70 ? ['Conceptos básicos'] : ['Memoria'],
      weaknesses: score < 70 ? ['Análisis crítico'] : ['Velocidad'],
      score_by_topic: Object.fromEntries(
        selectedSubject!.config.topics.map(topic => [topic, Math.floor(Math.random() * 40) + 60])
      ),
      recommendations: ['Fallback: Dedica más tiempo a los temas débiles']
    };
    
    setTestResults([result]);
    setUserMetrics(prev => ({ ...prev, diagnostic_score: score }));
    setCurrentPhase('results');
  };

  const generateAdaptiveStudyPlan = async () => {
    setIsLoading(true);
    
    try {
      // Usar servicio real en lugar de mock
      const response = await api.post(`/study-plans/generate-adaptive`, {
        subject_id: selectedSubject!.id,
        use_diagnostic: true
      });
      
      const realPlan = response.data;
      console.log('✅ Plan real generado:', realPlan);
      
      setStudyPlan(realPlan);
      aiRecommendationSound?.play();
      setCurrentPhase('studyplan');
      
      // Track analytics
      trackDiagnosticComplete(selectedSubject!.name, testResults[0]?.percentage || 0);
      
    } catch (error: any) {
      console.error('❌ Error generando plan real:', error);
      
      // Fallback a plan mock si falla el servicio real
      console.log('🔄 Usando plan mock como fallback...');
      await handleMockPlanGeneration();
      
    } finally {
      setIsLoading(false);
    }
  };

  // Función de fallback para plan mock
  const handleMockPlanGeneration = async () => {
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const testResult = testResults[0];
    
    // Crear objeto seguro para evitar errores
    const safeTestResult = {
      ...testResult,
      score_by_topic: testResult?.score_by_topic || {},
      percentage: testResult?.percentage || 0
    };
    
    const weakTopics = Object.entries(safeTestResult.score_by_topic)
      .filter(([_, score]) => score < 70)
      .map(([topic]) => topic);
    
    const mockPlan: AdaptiveStudyPlan = {
      subject: selectedSubject!.name,
      title: `Mazmorra Adaptativa de ${selectedSubject!.name}`,
      description: `Plan personalizado basado en tu diagnóstico (${safeTestResult.percentage}%)`,
      units: [
        {
          unit_number: 1,
          name: 'Refuerzo de Fundamentos',
          description: 'Fortalece las bases identificadas en tu diagnóstico',
          topics: weakTopics.map((topic, idx) => ({
            name: `${topic} - Nivel Básico`,
            difficulty: 1,
            questions: 5,
            tags: [topic.toLowerCase(), 'fundamentos'],
            video_url: 'https://www.youtube.com/watch?v=lGp_8-jAYI4',
            completed: false,
            video_watched: false,
            exercises_completed: 0,
            total_exercises: 5
          })),
          video_urls: Object.fromEntries(
            weakTopics.map(topic => [`${topic} - Nivel Básico`, 'https://www.youtube.com/watch?v=lGp_8-jAYI4'])
          ),
          reading_materials: {
            'Material de apoyo': 'https://es.khanacademy.org/',
            'Ejercicios adicionales': 'https://www.coursera.org/'
          },
          learning_objectives: [
            'Dominar los conceptos fundamentales',
            'Mejorar la velocidad de resolución',
            'Alcanzar 80% de precisión'
          ],
          exercise_count: weakTopics.length * 5,
          recommendations: {
            priority: 'high',
            weak_areas: weakTopics,
            focus_topics: weakTopics,
            study_time: '4-5 horas',
            custom_tips: [`Tu diagnóstico mostró ${safeTestResult.percentage}% - enfócate en los fundamentos`]
          },
          unlocked: true,
          progress: 0,
          video_progress: {},
          exercise_progress: {},
          ai_recommended: true,
          estimated_completion_time: 5,
          difficulty_level: 1,
          icfes_weight: 0.35
        },
        {
          unit_number: 2,
          name: 'Desarrollo Intermedio',
          description: 'Avanza hacia conceptos más complejos',
          topics: selectedSubject!.config.topics.map((topic, idx) => ({
            name: `${topic} - Nivel Intermedio`,
            difficulty: 2,
            questions: 6,
            tags: [topic.toLowerCase(), 'intermedio'],
            video_url: 'https://www.youtube.com/watch?v=AuWaC5ORE3M',
            completed: false,
            video_watched: false,
            exercises_completed: 0,
            total_exercises: 6
          })),
          video_urls: Object.fromEntries(
            selectedSubject!.config.topics.map(topic => [`${topic} - Nivel Intermedio`, 'https://www.youtube.com/watch?v=AuWaC5ORE3M'])
          ),
          reading_materials: {
            'Teoría avanzada': 'https://es.khanacademy.org/',
            'Problemas resueltos': 'https://www.coursera.org/'
          },
          learning_objectives: [
            'Aplicar conceptos en problemas complejos',
            'Desarrollar pensamiento crítico',
            'Preparación específica ICFES'
          ],
          exercise_count: selectedSubject!.config.topics.length * 6,
          recommendations: {
            priority: 'medium',
            weak_areas: [],
            focus_topics: selectedSubject!.config.topics,
            study_time: '6-7 horas',
            custom_tips: []
          },
          unlocked: false,
          progress: 0,
          video_progress: {},
          exercise_progress: {},
          ai_recommended: false,
          estimated_completion_time: 7,
          difficulty_level: 2,
          icfes_weight: 0.30
        }
      ],
      total_questions: weakTopics.length * 5 + selectedSubject!.config.topics.length * 6,
      total_videos: weakTopics.length + selectedSubject!.config.topics.length,
      estimated_time: '10-12 horas',
      difficulty_curve: 'adaptive',
      icfes_weight: 0.65,
      exam_sections: [selectedSubject!.name],
      personalization: {
        based_on_performance: true,
        adaptation_date: new Date().toISOString(),
        focus_areas: weakTopics.map(t => `Reforzar ${t}`)
      }
    };
    
    setStudyPlan(mockPlan);
    setCurrentPhase('studyplan');
  };

  const handleTopicVideoWatch = (topic: StudyPlanTopic) => {
    videoPlaySound?.play();
    setSelectedTopic(topic);
    setShowVideoPlayer(true);
  };

  const handleVideoProgress = (watchedSeconds: number, percentage: number) => {
    if (selectedTopic) {
      console.log(`Video progress: ${percentage}% watched for ${selectedTopic.name}`);
    }
  };

  const handleVideoComplete = () => {
    if (selectedTopic) {
      selectedTopic.video_watched = true;
      playLevelUpSound();
      setUserMetrics(prev => ({
        ...prev,
        total_videos_watched: prev.total_videos_watched + 1
      }));
      setOrbsEarned(prev => prev + 15);
      
      // Rank up logic
      const totalProgress = userMetrics.total_videos_watched + userMetrics.total_exercises_completed;
      if (totalProgress >= 50 && hunterRank === 'F') setHunterRank('E');
      else if (totalProgress >= 100 && hunterRank === 'E') setHunterRank('D');
      else if (totalProgress >= 200 && hunterRank === 'D') setHunterRank('C');
    }
  };

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getDifficultyColor = (difficulty: number) => {
    if (difficulty <= 1) return 'bg-green-100 text-green-800';
    if (difficulty <= 2) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getRankColor = (rank: string) => {
    const colors: Record<string, string> = {
      'F': 'text-gray-400',
      'E': 'text-green-400',
      'D': 'text-blue-400',
      'C': 'text-purple-400',
      'B': 'text-orange-400',
      'A': 'text-red-400',
      'S': 'text-gold-500'
    };
    return colors[rank] || 'text-gray-400';
  };

  // Phase 1: Subject Selection
  if (currentPhase === 'selection') {
    return (
      <ErrorBoundary>
        <div className="min-h-screen bg-gradient-to-br from-black to-purple-900">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gold-500 mb-4 font-cinzel">
              🏰 Academia de Hunters ICFES
            </h1>
            <p className="text-xl text-purple-300 font-orbitron">
              Inicia tu viaje épico hacia la conquista del conocimiento
            </p>
            <div className="mt-4 flex justify-center gap-4">
              <Badge className="bg-purple-900 text-purple-300">
                <Trophy className="w-4 h-4 mr-1" />
                Sistema Adaptativo IA
              </Badge>
              <Badge className="bg-purple-900 text-purple-300">
                <Sparkles className="w-4 h-4 mr-1" />
                Gamificación Épica
              </Badge>
            </div>
          </div>

          <Card className="bg-black/30 backdrop-blur-md border-purple-500 mb-8">
            <CardHeader>
              <CardTitle className="text-2xl text-center text-gold-500 font-cinzel">
                ⚔️ Elige tu Primera Conquista
              </CardTitle>
              <p className="text-center text-purple-300 mt-2">
                Comenzarás con un diagnóstico místico para evaluar tu poder actual
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {subjects.map((subject) => (
                  <Card 
                    key={subject.id} 
                    className="hover:shadow-[0_0_20px_#ffd700] transition-all cursor-pointer bg-black/40 backdrop-blur-sm border-purple-500 transform hover:scale-105"
                    onClick={() => {
                      trackButtonClick('start-diagnostic', subject.name);
                      trackDiagnosticStart(subject.name);
                      startDiagnosticTest(subject);
                    }}
                  >
                    <CardContent className="p-6">
                      <div className="text-center">
                        <div 
                          className="w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center text-3xl shadow-[0_0_15px_rgba(139,92,246,0.5)]"
                          style={{ backgroundColor: subject.color }}
                        >
                          <SubjectIcon subjectName={subject.name} size={48} />
                        </div>
                        <h3 className="text-xl font-semibold text-gold-500 mb-2 font-cinzel">
                          {subject.name}
                        </h3>
                        <p className="text-purple-300 mb-4 text-sm">
                          {subject.description}
                        </p>
                        <div className="space-y-2 text-sm text-gray-400 mb-4">
                          <div className="flex justify-between">
                            <span>⚔️ Combates:</span>
                            <span className="font-medium text-purple-300">{subject.config.total_questions}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>⏱️ Tiempo:</span>
                            <span className="font-medium text-purple-300">{subject.config.time_limit_minutes} min</span>
                          </div>
                        </div>
                        <Button 
                          className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-[0_0_10px_#8a2be2]"
                        >
                          <Swords className="w-4 h-4 mr-2" />
                          Iniciar Diagnóstico
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      </ErrorBoundary>
    );
  }

  // Phase 2: Diagnostic Test
  if (currentPhase === 'diagnostic' && !showVideoPlayer) {
    const currentQ = questions[currentQuestion];
    const progress = questions.length > 0 ? (Object.keys(answers).length / questions.length) * 100 : 0;

    // Transform legacy Question → MultimediaQuestion shape (texto + imagen por opción)
    const toMultimedia = (q: Question | undefined) => {
      if (!q) return undefined as any;
      const rawOpt: any = q.options ?? {};
      const rawImg: any = q.options_images ?? {};

      const normalizeUrl = (u?: string) => {
        if (!u) return undefined;
        const trimmed = u.trim();
        if (trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.startsWith('data:')) return trimmed;
        if (trimmed.startsWith('/')) return trimmed;
        if (trimmed.startsWith('mathimg/')) return `/${trimmed}`;
        return trimmed;
      };

      // Si el texto viene como "[Imagen: /mathimg/...png]" extraer la ruta
      const extractImageFromText = (text?: string) => {
        if (!text) return { text, img: undefined as string | undefined };
        const m = text.match(/\[?\s*Imagen:?\s*([^\]\n]+)\]?/i);
        if (m && m[1]) {
          const url = normalizeUrl(m[1].trim());
          return { text: '', img: url };
        }
        // Soportar formato "[Imagen: mathimg/..]" o "(Imagen: ..)"
        const n = text.match(/mathimg\/[\w\-_.]+\.(png|jpg|jpeg|gif)/i);
        if (n) {
          return { text: '', img: normalizeUrl(n[0]) };
        }
        return { text, img: undefined };
      };

      const mapToABCD = (src: any): Record<string, string | undefined> => {
        const out: Record<string, string | undefined> = { A: undefined, B: undefined, C: undefined, D: undefined };
        if (Array.isArray(src)) {
          // Array → index 0..3
          out.A = src[0]; out.B = src[1]; out.C = src[2]; out.D = src[3];
          return out;
        }
        if (src && typeof src === 'object') {
          const keys = Object.keys(src);
          // Case-insensitive letter keys first
          const get = (k: string) => src[k] ?? src[k.toUpperCase?.()] ?? src[k.toLowerCase?.()];
          if (get('A') || get('B') || get('C') || get('D')) {
            out.A = get('A'); out.B = get('B'); out.C = get('C'); out.D = get('D');
            return out;
          }
          // Numeric keys '0','1','2','3'
          if (keys.some(k => ['0','1','2','3'].includes(k))) {
            out.A = src['0']; out.B = src['1']; out.C = src['2']; out.D = src['3'];
            return out;
          }
          // Fallback: first four entries by insertion order
          const vals = keys.slice(0,4).map(k => src[k]);
          out.A = vals[0]; out.B = vals[1]; out.C = vals[2]; out.D = vals[3];
          return out;
        }
        return out;
      };

      const optRaw = mapToABCD(rawOpt) as Record<string, string | undefined>;
      const optImg = mapToABCD(rawImg) as Record<string, string | undefined>;

      // Elevar imágenes embebidas en texto de opciones
      const opt: Record<string, string | undefined> = { A: undefined, B: undefined, C: undefined, D: undefined };
      (['A','B','C','D'] as const).forEach(k => {
        const { text, img } = extractImageFromText(optRaw[k]);
        opt[k] = text;
        if (!optImg[k] && img) optImg[k] = img;
      });

      // Imagen de la pregunta también puede venir en el texto
      const qImage = normalizeUrl((q as any).pregunta_imagen || q.image_url);
      const { text: qText, img: extractedQImg } = extractImageFromText((q as any).pregunta_texto || q.question_text);
      const preguntaTexto = qText || (q as any).pregunta_texto || q.question_text;
      const preguntaImagen = qImage || extractedQImg;
      return {
        id: q.id,
        // Preferir campos multimedia si existen
        pregunta_texto: preguntaTexto,
        pregunta_imagen: preguntaImagen,
        opcion_a_texto: opt['A'] as string | undefined,
        opcion_a_imagen: optImg['A'] as string | undefined,
        opcion_b_texto: opt['B'] as string | undefined,
        opcion_b_imagen: optImg['B'] as string | undefined,
        opcion_c_texto: opt['C'] as string | undefined,
        opcion_c_imagen: optImg['C'] as string | undefined,
        opcion_d_texto: opt['D'] as string | undefined,
        opcion_d_imagen: optImg['D'] as string | undefined,
        // respuesta_correcta puede no venir en flujo diagnóstico; no mostrar corrección durante test
        respuesta_correcta: 'a',
        difficulty: q.difficulty,
        explanation: undefined,
        hint: q.hint,
      };
    };
    const mmCurrent = toMultimedia(currentQ);

    // Build answered indices for grid
    const answeredIdx = Object.keys(answers).map(id =>
      questions.findIndex(q => q.id === id) + 1
    ).filter(n => n > 0);

    // Prefer 45 grid if la materia lo requiere
    const gridTotal = questions.length > 0 ? questions.length : (selectedSubject?.config?.total_questions || 20);

    return (
      <div className="min-h-screen bg-gradient-to-br from-black to-purple-900">
        <div className="sticky top-0 z-20 p-3 bg-black/40 backdrop-blur-md">
          <GameStats
            streak={streak}
            totalXP={Math.round(progress)}
            hearts={hearts}
            level={level}
            nextLevelXP={100}
          />
        </div>
        <div className="flex h-[calc(100vh-80px)]">
          {/* Navegación lateral gamificada */}
          <div className="w-80 bg-black/40 backdrop-blur-sm border-r border-purple-800 overflow-y-auto">
            <div className="p-3">
              <NavigationPills
                totalQuestions={gridTotal}
                currentQuestion={currentQuestion + 1}
                answeredQuestions={new Set(answeredIdx)}
                skippedQuestions={new Set<number>()}
                onQuestionClick={(idx) => setCurrentQuestion(Math.max(0, Math.min(idx, questions.length - 1)))}
              />
            </div>
          </div>

          {/* Contenido principal */}
          <div className="flex-1 overflow-y-auto">
            <div className="container mx-auto px-4 py-6 max-w-4xl">
              <Card className="bg-black/30 backdrop-blur-md border-purple-500 shadow-[0_0_20px_#8a2be2]">
                <CardHeader>
                  <div className="flex items-center justify-between mb-4">
                    <CardTitle className="text-2xl text-gold-500 font-cinzel">
                      ⚔️ Prueba de Poder - {selectedSubject?.name}
                    </CardTitle>
                    <div className="flex items-center space-x-2">
                      <Clock className="h-5 w-5 text-red-400" />
                      <span className="text-lg font-mono font-bold text-red-400">
                        {formatTime(timeRemaining)}
                      </span>
                    </div>
                  </div>
                  <p className="text-center text-purple-300">
                    Demuestra tu conocimiento actual para forjar tu camino personalizado
                  </p>
                </CardHeader>
                <CardContent>
              {/* Barra de progreso */}
                  <div className="mb-6">
                    <div className="flex justify-between text-sm text-purple-300 mb-2">
                      <span>Progreso de Batalla</span>
                      <span className="text-gold-300">{Math.round(progress)}%</span>
                    </div>
                    <Progress value={progress} className="h-3 bg-purple-900" />
                  </div>

                  {/* Pregunta con soporte multimedia (texto + imagen) y opciones A-D */}
                  {mmCurrent && (
                <>
                  <QuestionCard
                    questionNumber={currentQuestion + 1}
                    totalQuestions={questions.length}
                    questionText={mmCurrent.pregunta_texto || ''}
                    difficulty={mmCurrent.difficulty || 5}
                    timeRemaining={timeRemaining}
                    category={selectedSubject?.name || 'Diagnóstico'}
                    imageUrl={mmCurrent.pregunta_imagen}
                  />

                  <div className="mt-6 space-y-4">
                    {(['a','b','c','d'] as const).map((key, idx) => {
                      const optionText = (mmCurrent as any)[`opcion_${key}_texto`];
                      const optionImg = (mmCurrent as any)[`opcion_${key}_imagen`];
                      const hasContent = optionText || (mmCurrent as any)[`opcion_${key}_imagen`];
                      if (!hasContent) return null;
                      const selected = (answers[currentQ!.id] || '').toLowerCase() === key;
                      return (
                         <AnswerOption
                          key={`${currentQ!.id}-${key}`}
                          label={key.toUpperCase()}
                          text={optionText || ''}
                          imageUrl={optionImg}
                          isSelected={!!selected}
                          onClick={() => handleAnswer(currentQ!.id, key)}
                          disabled={false}
                          delay={idx * 0.05}
                        />
                      );
                    })}
                  </div>
                </>
                  )}

                  {/* Navegación inferior */}
                  <div className="flex justify-between mt-4">
                    <Button
                      variant="outline"
                      onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
                      disabled={currentQuestion === 0}
                      className="shadow-[0_0_5px_#ffd700]"
                    >
                      <Shield className="w-4 h-4 mr-2" />
                      Anterior
                    </Button>

                    {currentQuestion === questions.length - 1 ? (
                      <Button
                        onClick={handleSubmitTest}
                        disabled={isSubmitting || Object.keys(answers).length < questions.length}
                        className="bg-gradient-to-r from-gold-500 to-yellow-600 hover:from-gold-600 hover:to-yellow-700 text-black shadow-[0_0_10px_#ffd700]"
                      >
                        {isSubmitting ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Evaluando Poder...
                          </>
                        ) : (
                          <>
                            <Trophy className="w-4 h-4 mr-2" />
                            Completar Diagnóstico
                          </>
                        )}
                      </Button>
                    ) : (
                      <Button
                        onClick={() => setCurrentQuestion(prev => prev + 1)}
                        disabled={!answers[currentQ?.id]}
                        className="shadow-[0_0_5px_#ffd700]"
                      >
                        Siguiente
                        <Swords className="w-4 h-4 ml-2" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Phase 3: Test Results
  if (currentPhase === 'results') {
    const result = testResults[0];
    
    // Crear objeto seguro con valores por defecto para evitar errores
    const safeResult = {
      ...result,
      score_by_topic: result?.score_by_topic || {},
      strengths: result?.strengths || [],
      weaknesses: result?.weaknesses || [],
      recommendations: result?.recommendations || [],
      percentage: result?.percentage || 0,
      subject: result?.subject || 'Materia'
    };
    
    // Log para debugging
    console.log('🔍 Result object:', result);
    console.log('🛡️ Safe result object:', safeResult);
    console.log('📊 Score by topic:', safeResult.score_by_topic);
    console.log('💪 Strengths:', safeResult.strengths);
    console.log('⚠️ Weaknesses:', safeResult.weaknesses);
    console.log('💡 Recommendations:', safeResult.recommendations);
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-black to-purple-900">
        <div className="container mx-auto px-4 py-8">
          <Card className="bg-black/30 backdrop-blur-md border-purple-500 shadow-[0_0_20px_#8a2be2]">
            <CardHeader>
              <CardTitle className="text-3xl text-center text-gold-500 font-cinzel">
                🏆 Resultados de tu Prueba de Poder
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Score Display */}
              <div className="text-center py-8">
                <div className="text-6xl font-bold text-gold-500 mb-2">
                  {Math.round(safeResult.percentage)}%
                </div>
                <div className="text-xl text-purple-300 mb-4">
                  Poder Demostrado en Matemáticas ICFES
                </div>
                <div className="flex justify-center gap-4">
                  <Badge className={`text-lg px-4 py-2 ${getRankColor(hunterRank)}`}>
                    <Trophy className="w-5 h-5 mr-2" />
                    Rango Hunter: {hunterRank}
                  </Badge>
                  <Badge className="text-lg px-4 py-2 bg-purple-900 text-purple-300">
                    <Sparkles className="w-5 h-5 mr-2" />
                    +{Math.floor(safeResult.percentage / 2)} Orbs
                  </Badge>
                </div>
              </div>

              <Progress 
                value={safeResult.percentage} 
                className="h-6"
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Strengths */}
                <Card className="bg-green-900/20 border-green-500">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-green-400">
                      <CheckCircle className="w-5 h-5" />
                      Fortalezas Descubiertas
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {safeResult.strengths && safeResult.strengths.length > 0 ? (
                        safeResult.strengths.map((strength) => (
                          <div key={strength} className="flex items-center gap-2">
                            <Star className="w-4 h-4 text-green-400" />
                            <span className="text-green-300">{strength}</span>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-2">
                          <div className="text-gray-400 text-sm">
                            🌟 No se han identificado fortalezas específicas
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Weaknesses */}
                <Card className="bg-red-900/20 border-red-500">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-red-400">
                      <XCircle className="w-5 h-5" />
                      Áreas a Conquistar
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {safeResult.weaknesses && safeResult.weaknesses.length > 0 ? (
                        safeResult.weaknesses.map((weakness) => (
                          <div key={weakness} className="flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-red-400" />
                            <span className="text-red-300">{weakness}</span>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-2">
                          <div className="text-gray-400 text-sm">
                            ⚠️ No se han identificado áreas de mejora específicas
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Topic Scores */}
              <Card className="bg-purple-900/20 border-purple-500">
                <CardHeader>
                  <CardTitle className="text-purple-300">
                    Poder por Reino de Conocimiento
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {safeResult.score_by_topic && Object.keys(safeResult.score_by_topic).length > 0 ? (
                      Object.entries(safeResult.score_by_topic).map(([topic, score]) => (
                        <div key={topic}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-300">{topic}</span>
                            <span className={score >= 70 ? 'text-green-400' : 'text-orange-400'}>
                              {score}%
                            </span>
                          </div>
                          <Progress value={score} className="h-2" />
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-4">
                        <div className="text-gray-400 text-sm">
                          📊 No hay datos de puntuación por tema disponibles
                        </div>
                        <div className="text-gray-500 text-xs mt-1">
                          Los resultados se mostrarán aquí después de completar más preguntas
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Recommendations */}
              <Card className="bg-blue-900/20 border-blue-500">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-blue-400">
                    <Brain className="w-5 h-5" />
                    Sabiduría del Oráculo IA
                  </CardTitle>
                </CardHeader>
                                  <CardContent>
                    <div className="space-y-2">
                      {safeResult.recommendations && safeResult.recommendations.length > 0 ? (
                        safeResult.recommendations.map((rec, idx) => (
                          <div key={idx} className="flex items-start gap-2">
                            <Zap className="w-4 h-4 text-blue-400 mt-0.5" />
                            <span className="text-blue-300">{rec}</span>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-2">
                          <div className="text-gray-400 text-sm">
                            💡 No hay recomendaciones específicas disponibles
                          </div>
                          <div className="text-gray-500 text-xs mt-1">
                            Las recomendaciones se generarán basándose en tu rendimiento
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
              </Card>

              {/* Action Button */}
              <div className="text-center pt-6">
                <Button 
                  onClick={generateAdaptiveStudyPlan}
                  disabled={isLoading}
                  className="bg-gradient-to-r from-gold-500 to-yellow-600 hover:from-gold-600 hover:to-yellow-700 text-black text-lg px-8 py-6 shadow-[0_0_20px_#ffd700]"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Forjando tu Camino...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5 mr-2" />
                      Generar Plan de Conquista Personalizado
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Phase 4: Study Plan
  if (currentPhase === 'studyplan' && !showVideoPlayer) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black to-purple-900">
        <div className="container mx-auto px-4 py-8">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-gold-500 mb-2 font-cinzel">
              Plan de Conquista Adaptativo
            </h1>
            <p className="text-purple-300 font-orbitron">
              Forjado especialmente para ti basado en tu diagnóstico
            </p>
            <div className="mt-4 flex justify-center gap-4">
              <Badge className={`text-lg px-4 py-2 ${getRankColor(hunterRank)}`}>
                Rango: {hunterRank}
              </Badge>
              <Badge className="text-lg px-4 py-2 bg-purple-900 text-purple-300">
                💎 {orbsEarned} Orbs
              </Badge>
              <Badge className="text-lg px-4 py-2 bg-gold-900 text-gold-300">
                📊 Diagnóstico: {userMetrics.diagnostic_score}%
              </Badge>
            </div>
          </div>

          {isLoading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gold-500"></div>
            </div>
          ) : studyPlan ? (
            <>
              {/* User Metrics Card */}
              <Card className="bg-black/30 backdrop-blur-md border-purple-500 shadow-[0_0_10px_#8a2be2] mb-6">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-gold-500 font-cinzel">
                    <BarChart3 className="w-5 h-5" />
                    Tu Progreso como Hunter
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-300">
                        {userMetrics.overall_progress}%
                      </div>
                      <div className="text-sm text-gray-300">Progreso Total</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-300">
                        {userMetrics.completed_units}/{studyPlan.units.length}
                      </div>
                      <div className="text-sm text-gray-300">Unidades</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-300">
                        {userMetrics.total_videos_watched}
                      </div>
                      <div className="text-sm text-gray-300">Videos</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-300">
                        {userMetrics.current_streak}
                      </div>
                      <div className="text-sm text-gray-300">Racha</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Personalization Card */}
              {studyPlan.personalization.based_on_performance && (
                <Card className="bg-black/30 backdrop-blur-md border-purple-500 shadow-[0_0_10px_#8a2be2] mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-gold-500 font-cinzel">
                      <Brain className="w-5 h-5" />
                      Plan Personalizado por IA Arcana
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-semibold mb-2 text-gold-300">
                          Basado en tu diagnóstico ({userMetrics.diagnostic_score}%):
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {studyPlan.personalization.focus_areas.map((area, idx) => (
                            <Badge key={idx} variant="outline" className="text-purple-300">
                              {area}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-semibold mb-2 text-gold-300">Plan creado el:</h4>
                        <p className="text-sm text-gray-300">
                          {new Date(studyPlan.personalization.adaptation_date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Study Units */}
              <div className="space-y-6">
                {studyPlan.units.map((unit) => (
                  <Card key={unit.unit_number} className="overflow-hidden bg-black/30 backdrop-blur-md border-purple-500 shadow-[0_0_10px_#8a2be2]">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2">
                            {unit.unlocked ? (
                              <Unlock className="w-5 h-5 text-green-500" />
                            ) : (
                              <Lock className="w-5 h-5 text-gray-400" />
                            )}
                            <CardTitle className="text-gold-500 font-cinzel">
                              Unidad {unit.unit_number}: {unit.name}
                            </CardTitle>
                          </div>
                          {unit.ai_recommended && (
                            <Badge className="bg-purple-900 text-purple-300">
                              <Star className="w-3 h-3 mr-1" />
                              Recomendado por IA
                            </Badge>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <Badge className={getPriorityColor(unit.recommendations.priority)}>
                            Prioridad {unit.recommendations.priority}
                          </Badge>
                          <Badge variant="outline" className="text-gray-300">
                            {unit.estimated_completion_time}h
                          </Badge>
                        </div>
                      </div>
                      
                      <p className="text-purple-300">{unit.description}</p>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-300">Progreso de Unidad</span>
                          <span className="text-gold-300">{unit.progress}%</span>
                        </div>
                        <Progress value={unit.progress} className="h-2" />
                      </div>
                    </CardHeader>
                    
                    <CardContent>
                      {unit.unlocked ? (
                        <Tabs defaultValue="topics" className="w-full">
                          <TabsList className="grid w-full grid-cols-4 bg-black/50 backdrop-blur-sm">
                            <TabsTrigger value="topics">Temas</TabsTrigger>
                            <TabsTrigger value="videos">Videos</TabsTrigger>
                            <TabsTrigger value="objectives">Objetivos</TabsTrigger>
                            <TabsTrigger value="tips">Consejos IA</TabsTrigger>
                          </TabsList>
                          
                          <TabsContent value="topics" className="mt-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {unit.topics.map((topic, topicIdx) => (
                                <div
                                  key={topicIdx}
                                  className="border border-purple-500 rounded-lg p-4 hover:shadow-[0_0_10px_#ffd700] transition-shadow bg-black/40 backdrop-blur-sm"
                                >
                                  <div className="flex items-center justify-between mb-2">
                                    <h4 className="font-semibold text-gold-300">{topic.name}</h4>
                                    <Badge className={getDifficultyColor(topic.difficulty)}>
                                      Nivel {topic.difficulty}
                                    </Badge>
                                  </div>
                                  
                                  <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                      <span className="text-purple-300">Ejercicios</span>
                                      <span className="text-gray-300">
                                        {topic.exercises_completed}/{topic.total_exercises}
                                      </span>
                                    </div>
                                    <Progress 
                                      value={(topic.exercises_completed / topic.total_exercises) * 100} 
                                      className="h-1" 
                                    />
                                  </div>
                                  
                                  <div className="flex gap-2 mt-3">
                                    {topic.video_url && (
                                      <Button
                                        size="sm"
                                        variant={topic.video_watched ? "secondary" : "default"}
                                        onClick={() => handleTopicVideoWatch(topic)}
                                        className="flex-1 shadow-[0_0_5px_#ffd700]"
                                      >
                                        <PlayCircle className="w-4 h-4 mr-1" />
                                        {topic.video_watched ? 'Revisar' : 'Ver Video'}
                                      </Button>
                                    )}
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="flex-1 shadow-[0_0_5px_#ffd700]"
                                      disabled={!topic.video_watched}
                                    >
                                      <BookOpen className="w-4 h-4 mr-1" />
                                      Ejercicios
                                    </Button>
                                  </div>
                                  
                                  {topic.completed && (
                                    <div className="flex items-center gap-1 mt-2 text-green-300">
                                      <CheckCircle className="w-4 h-4" />
                                      <span className="text-sm">Completado</span>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </TabsContent>
                          
                          <TabsContent value="videos" className="mt-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {Object.entries(unit.video_urls).map(([topic, url]) => (
                                <div key={topic} className="border border-purple-500 rounded-lg p-4 bg-black/40 backdrop-blur-sm">
                                  <h4 className="font-semibold mb-2 text-gold-300">{topic}</h4>
                                  <div className="aspect-video bg-gray-900 rounded-lg mb-3 flex items-center justify-center">
                                    <PlayCircle className="w-12 h-12 text-purple-300" />
                                  </div>
                                  <Button
                                    size="sm"
                                    className="w-full bg-purple-600 hover:bg-purple-700 shadow-[0_0_5px_#8a2be2]"
                                    onClick={() => {
                                      const topic_obj = unit.topics.find(t => t.name === topic);
                                      if (topic_obj) handleTopicVideoWatch(topic_obj);
                                    }}
                                  >
                                    <Play className="w-4 h-4 mr-1" />
                                    Ver Video
                                  </Button>
                                </div>
                              ))}
                            </div>
                          </TabsContent>
                          
                          <TabsContent value="objectives" className="mt-4">
                            <div className="space-y-3">
                              {unit.learning_objectives.map((objective, idx) => (
                                <div key={idx} className="flex items-center gap-3 text-purple-300">
                                  <Target className="w-5 h-5 text-blue-300" />
                                  <span>{objective}</span>
                                </div>
                              ))}
                            </div>
                          </TabsContent>
                          
                          <TabsContent value="tips" className="mt-4">
                            <div className="space-y-4">
                              <div>
                                <h4 className="font-semibold mb-2 text-gold-300">
                                  Tiempo Recomendado:
                                </h4>
                                <Badge variant="outline" className="text-purple-300">
                                  {unit.recommendations.study_time}
                                </Badge>
                              </div>
                              
                              {unit.recommendations.custom_tips.length > 0 && (
                                <div>
                                  <h4 className="font-semibold mb-2 text-gold-300">
                                    Consejos Personalizados:
                                  </h4>
                                  <ul className="space-y-2">
                                    {unit.recommendations.custom_tips.map((tip, idx) => (
                                      <li key={idx} className="flex items-center gap-2 text-purple-300">
                                        <Zap className="w-4 h-4 text-gold-300" />
                                        {tip}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              
                              <div>
                                <h4 className="font-semibold mb-2 text-gold-300">
                                  Temas de Enfoque:
                                </h4>
                                <div className="flex flex-wrap gap-2">
                                  {unit.recommendations.focus_topics.map((topic, idx) => (
                                    <Badge key={idx} variant="secondary" className="text-gold-300">
                                      {topic}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </TabsContent>
                        </Tabs>
                      ) : (
                        <div className="text-center py-8 text-gray-300">
                          <Lock className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                          <p>Completa las unidades anteriores para desbloquear</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          ) : null}
        </div>
      </div>
    );
  }

  // Video Player View
  if (showVideoPlayer && selectedTopic) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black to-purple-900">
        <div className="container mx-auto px-4 py-8">
          <div className="mb-6">
            <Button
              variant="outline"
              onClick={() => setShowVideoPlayer(false)}
              className="mb-4 shadow-[0_0_5px_#ffd700]"
            >
              ← Volver al Plan de Conquista
            </Button>
            
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold text-gold-500 font-cinzel">{selectedTopic.name}</h1>
              <div className="flex items-center gap-2">
                <Badge className={getDifficultyColor(selectedTopic.difficulty)}>
                  Nivel {selectedTopic.difficulty}
                </Badge>
                <Badge variant="outline">
                  {selectedTopic.exercises_completed}/{selectedTopic.total_exercises} ejercicios
                </Badge>
              </div>
            </div>
          </div>

          <VideoPlayer
            youtubeUrl={selectedTopic.video_url || ''}
            videoTitle={selectedTopic.name}
            planId="current-plan"
            unitNumber={1}
            onProgressUpdate={handleVideoProgress}
            onVideoComplete={handleVideoComplete}
            completionThreshold={80}
          />

          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-black/30 backdrop-blur-md border-purple-500 shadow-[0_0_10px_#8a2be2]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-gold-500 font-cinzel">
                  <Target className="w-5 h-5" />
                  Objetivos del Video
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  <li className="flex items-center gap-2 text-purple-300">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    Comprender los conceptos fundamentales
                  </li>
                  <li className="flex items-center gap-2 text-purple-300">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    Aplicar el conocimiento en ejercicios
                  </li>
                  <li className="flex items-center gap-2 text-purple-300">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    Prepararte para el ICFES
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-black/30 backdrop-blur-md border-purple-500 shadow-[0_0_10px_#8a2be2]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-gold-500 font-cinzel">
                  <Zap className="w-5 h-5" />
                  Siguiente Paso
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <p className="text-sm text-gray-300">
                    Completa el video para desbloquear los ejercicios prácticos.
                  </p>
                  <Button className="w-full bg-gold-500 hover:bg-gold-600 shadow-[0_0_5px_#ffd700] text-black" disabled>
                    <BookOpen className="w-4 h-4 mr-2" />
                    Ejercicios (Ver video primero)
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-black to-indigo-900 text-white">
        <div className="container mx-auto p-6">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
              🎯 Sistema de Diagnóstico Avanzado
            </h1>
            <p className="text-purple-300 text-lg">
              Completa tu diagnóstico y obtén tu plan personalizado
            </p>
          </div>
          <div className="max-w-4xl mx-auto">
            <p className="text-center text-purple-300">
              Funcionalidad en desarrollo. Por favor, selecciona una materia específica.
            </p>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}