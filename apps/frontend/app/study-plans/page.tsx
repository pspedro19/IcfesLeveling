'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  BookOpen, 
  Play, 
  CheckCircle, 
  Clock, 
  Target,
  BarChart3,
  Video,
  FileText,
  Activity,
  TrendingUp,
  Calendar,
  Users,
  Award,
  Zap,
  Sparkles,
  Flame,
  Crown,
  Shield,
  Swords
} from 'lucide-react';
import { websocketService } from '../services/websocket.service';
import { cacheService } from '../services/cache.service';
import { useAnalytics } from '../services/analytics.service';
import { ErrorBoundary } from '../components/ErrorBoundary';

// Epic sound effects for study experience
const studyStartSound = typeof Audio !== 'undefined' ? new Audio('/sounds/success.mp3') : null;
const hoverSound = typeof Audio !== 'undefined' ? new Audio('/sounds/hover.mp3') : null;
const clickSound = typeof Audio !== 'undefined' ? new Audio('/sounds/click.mp3') : null;
const levelUpSound = typeof Audio !== 'undefined' ? new Audio('/sounds/level_up.mp3') : null;
const videoPlaySound = typeof Audio !== 'undefined' ? new Audio('/sounds/unlock.mp3') : null;
const completionSound = typeof Audio !== 'undefined' ? new Audio('/sounds/reward.mp3') : null;

interface UnitContent {
  videos: string[];
  exercises: string[];
  resources: string[];
}

interface WeightedProgressComponent {
  completed: number;
  total: number;
  weight: number;
}

interface WeightedProgress {
  videos: WeightedProgressComponent;
  exercises: WeightedProgressComponent;
  readings: WeightedProgressComponent;
}

interface StudyUnit {
  unit_number: number;
  unit_name: string;
  unit_description: string;
  content: UnitContent;
  is_completed: boolean;
  score: number;
  weighted_progress: WeightedProgress;
  estimated_time_minutes: number;
}

interface StudyPlan {
  id: string;
  plan_name: string;
  subject: string;
  units: StudyUnit[];
  total_units: number;
  completed_units: number;
  progress_percentage: number;
  estimated_duration: string;
  difficulty_level: string;
  last_updated: string;
}

interface PlanStatistics {
  plan_id: string;
  total_units: number;
  completed_units: number;
  progress_percentage: number;
  average_score: number;
  time_spent_minutes: number;
  units_by_difficulty: Record<string, number>;
  completion_rate: number;
  estimated_completion_date?: string;
  improvement_trend: Array<{
    unit_number: number;
    score: number;
    completion_date?: string;
    improvement: number;
  }>;
}

interface StudyPlanDashboard {
  plans: StudyPlan[];
  total_plans: number;
  active_plans: number;
  average_progress: number;
  total_completed_units: number;
  estimated_completion_time?: string;
}

export default function StudyPlans() {
  // Analytics hook
  const { trackPageView, trackButtonClick, trackStudyPlanStart } = useAnalytics();
  
  const router = useRouter();
  const [dashboard, setDashboard] = useState<StudyPlanDashboard | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<StudyPlan | null>(null);
  const [planStatistics, setPlanStatistics] = useState<PlanStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [realDataLoaded, setRealDataLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [orbsEarned, setOrbsEarned] = useState(0);
  const [hunterRank, setHunterRank] = useState('E');
  const [particles, setParticles] = useState([]);
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  // Floating particles effect
  useEffect(() => {
    const interval = setInterval(() => {
      setParticles(prev => [...prev.slice(-20), {
        id: Date.now(),
        x: Math.random() * 100,
        y: 100,
        size: Math.random() * 4 + 2,
        color: Math.random() > 0.5 ? '#ffd700' : '#8a2be2'
      }]);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  // Update hunter rank based on progress
  useEffect(() => {
    if (dashboard) {
      const avg = dashboard.average_progress;
      if (avg >= 90) setHunterRank('S');
      else if (avg >= 80) setHunterRank('A');
      else if (avg >= 70) setHunterRank('B');
      else if (avg >= 60) setHunterRank('C');
      else if (avg >= 50) setHunterRank('D');
      else setHunterRank('E');
    }
  }, [dashboard]);

  useEffect(() => {
    // Initialize services
    websocketService.connect();
    trackPageView('study-plans');
    
    // WebSocket subscriptions
    websocketService.subscribe('study_plan_update', (data) => {
      console.log('Study plan update received:', data);
    });
    
    // Cargar todos los datos en paralelo para mejor performance
    Promise.all([
      loadDashboard(),
      loadUserProgress(),
      loadSubjectData(),
      loadTestHistory(),
      loadAchievementData(),
      syncRealTimeProgress()
    ]).catch(error => {
      console.error('Error loading initial data:', error);
    });

    return () => {
      websocketService.disconnect();
    };
  }, [trackPageView]);

  const loadUserProgress = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      if (!token) {
        console.warn('No authentication token found');
        return;
      }

      const response = await fetch(`${API_URL}/api/v1/analytics/personal`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const progressData = await response.json();
        // Update orbs and rank based on real progress
        setOrbsEarned(progressData.totalOrbs || orbsEarned);
      } else {
        console.warn('Failed to load user progress:', response.status);
      }
    } catch (error) {
      console.error('Error loading user progress:', error);
    }
  };

  const loadSubjectData = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const response = await fetch(`${API_URL}/api/v1/diagnostic/subjects`);
      if (response.ok) {
        const subjectsData = await response.json();
        // Cache subjects for better performance
        console.log('Subjects loaded:', subjectsData.length);
      } else {
        console.warn('Failed to load subjects:', response.status);
      }
    } catch (error) {
      console.error('Error loading subjects:', error);
    }
  };

  const loadTestHistory = async () => {
    try {
      const response = await fetch('/api/v1/diagnostic/tests', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (response.ok) {
        const historyData = await response.json();
        console.log('Test history loaded:', historyData.length);
      }
    } catch (error) {
      console.error('Error loading test history:', error);
    }
  };

  const loadAchievementData = async () => {
    try {
      const response = await fetch('/api/v1/achievements/user', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (response.ok) {
        const achievements = await response.json();
        // Update orbs based on real achievements
        const totalOrbs = achievements.reduce((sum: number, ach: any) => sum + (ach.orbs || 0), 0);
        setOrbsEarned(prev => Math.max(prev, totalOrbs));
      }
    } catch (error) {
      console.error('Error loading achievements:', error);
    }
  };

  const syncRealTimeProgress = async () => {
    try {
      const response = await fetch('/api/v1/study-plans/real-time-progress', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (response.ok) {
        const progressData = await response.json();
        // Sync real data with local state
        if (progressData.totalOrbs) setOrbsEarned(progressData.totalOrbs);
        if (progressData.currentRank) setHunterRank(progressData.currentRank);
      }
    } catch (error) {
      console.error('Error syncing real-time progress:', error);
    }
  };

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/study-plans/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Error cargando dashboard');
      }

      const dashboardData = await response.json();
      setDashboard(dashboardData);
      setRealDataLoaded(true);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setError('Error cargando datos del dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadPlanDetails = async (planId: string) => {
    try {
      clickSound?.play();
      const response = await fetch(`/api/v1/study-plans/plans/${planId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Error cargando detalles del plan');
      }

      const planData = await response.json();
      setSelectedPlan(planData);
      studyStartSound?.play();
    } catch (error) {
      console.error('Error loading plan details:', error);
      setError('Error cargando detalles del plan');
    }
  };

  const loadPlanStatistics = async (planId: string) => {
    try {
      const response = await fetch(`/api/v1/study-plans/plans/${planId}/statistics`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Error cargando estadísticas');
      }

      const statsData = await response.json();
      setPlanStatistics(statsData);
    } catch (error) {
      console.error('Error loading statistics:', error);
      setError('Error cargando estadísticas');
    }
  };

  const updateUnitProgress = async (planId: string, unitNumber: number, score: number, isCompleted: boolean) => {
    try {
      const response = await fetch(`/api/v1/study-plans/plans/${planId}/progress`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          unit_number: unitNumber,
          score: score,
          is_completed: isCompleted
        })
      });

      if (!response.ok) {
        throw new Error('Error actualizando progreso');
      }

      // Play completion sound if unit is completed
      if (isCompleted) {
        completionSound?.play();
        setOrbsEarned(prev => prev + 50);
      } else {
        levelUpSound?.play();
        setOrbsEarned(prev => prev + 10);
      }

      // Check for rank up
      if (score > 80 && hunterRank === 'E') setHunterRank('D');
      else if (score > 85 && hunterRank === 'D') setHunterRank('C');
      else if (score > 90 && hunterRank === 'C') setHunterRank('B');
      else if (score > 95 && hunterRank === 'B') setHunterRank('A');

      // Reload data
      await loadDashboard();
      if (selectedPlan) {
        await loadPlanDetails(selectedPlan.id);
      }
    } catch (error) {
      setError('Error actualizando progreso');
      console.error('Error:', error);
    }
  };

  const updateWeightedProgress = async (planId: string, unitNumber: number, componentType: string, completed: number, total: number, isCompleted: boolean = false) => {
    try {
      const response = await fetch(`/api/v1/study-plans/plans/${planId}/weighted-progress`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          unit_number: unitNumber,
          component_type: componentType,
          completed: completed,
          total: total,
          is_completed: isCompleted
        })
      });

      if (!response.ok) {
        throw new Error('Error actualizando progreso ponderado');
      }

      // Gamification rewards
      setOrbsEarned(prev => prev + 5);

      // Reload data
      await loadDashboard();
      if (selectedPlan) {
        await loadPlanDetails(selectedPlan.id);
      }
    } catch (error) {
      setError('Error actualizando progreso ponderado');
      console.error('Error:', error);
    }
  };

  const getSubjectIcon = (subject: string) => {
    const subjectIcons: Record<string, string> = {
      matematicas: '/assets/images/subjects/matematicasicon.png',
      lenguaje: '/assets/images/subjects/lecturaicon.png',
      ciencias: '/assets/images/subjects/cienciasnaturalesicon.png',
      sociales: '/assets/images/subjects/socialesicon.png',
      ingles: '/assets/images/subjects/englishicon.png'
    };
    
    const iconPath = subjectIcons[subject.toLowerCase()];
    if (iconPath) {
      return (
        <motion.div
          whileHover={{ scale: 1.2, rotate: 360 }}
          transition={{ duration: 0.5 }}
        >
          <img 
            src={iconPath} 
            alt={subject} 
            className="h-6 w-6 object-cover rounded shadow-lg"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
              const parent = target.parentElement;
              if (parent) {
                parent.innerHTML = '<BookOpen className="h-6 w-6" />';
              }
            }}
          />
        </motion.div>
      );
    }
    return <BookOpen className="h-6 w-6 text-gold-400" />;
  };

  const getDifficultyColor = (difficulty: string): string => {
    const colors: Record<string, string> = {
      'básico': 'bg-green-600 text-white',
      'intermedio': 'bg-yellow-600 text-white',
      'avanzado': 'bg-red-600 text-white'
    };
    return colors[difficulty] || 'bg-gray-600 text-white';
  };

  if (loading) {
    return (
      <ErrorBoundary>
        <div className="flex items-center justify-center min-h-screen bg-black relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-black to-gold-900/20" />
        {/* Animated loading indicator */}
        <motion.div className="relative">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-24 h-24 border-4 border-gold-500 border-t-transparent rounded-full"
          />
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            className="absolute inset-2 w-20 h-20 border-4 border-purple-500 border-b-transparent rounded-full"
          />
          <BookOpen className="absolute inset-0 m-auto w-8 h-8 text-gold-500" />
        </motion.div>
        <p className="absolute bottom-10 text-purple-300 animate-pulse">Invocando planes de conquista...</p>
      </div>
      </ErrorBoundary>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-black to-red-900/20" />
        <motion.div 
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center relative z-10"
        >
          <motion.div
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Shield className="w-20 h-20 text-red-500 mx-auto mb-4" />
          </motion.div>
          <div className="text-red-500 text-2xl mb-4 font-bold">Maldición Arcana</div>
          <p className="text-gray-300 mb-6">{error}</p>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={loadDashboard}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-800 hover:from-purple-700 hover:to-purple-900 text-white rounded-lg font-semibold shadow-lg transition-all"
            style={{ boxShadow: '0 0 20px rgba(139, 92, 246, 0.5)' }}
          >
            Intentar de Nuevo
          </motion.button>
        </motion.div>
      </div>
    );
  }

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
              y: '-100%', 
              opacity: [0, 1, 0],
              scale: [1, 1.5, 1]
            }}
            transition={{ duration: 8, ease: "linear" }}
            style={{
              width: particle.size,
              height: particle.size,
              backgroundColor: particle.color,
              boxShadow: `0 0 ${particle.size * 2}px ${particle.color}`
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
            className="text-5xl md:text-7xl font-bold mb-4 relative inline-block"
            animate={{ 
              textShadow: [
                "0 0 20px #ffd700",
                "0 0 40px #ffd700",
                "0 0 20px #ffd700"
              ]
            }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <span className="bg-gradient-to-r from-gold-400 via-orange-400 to-purple-400 text-transparent bg-clip-text">
              📚 ACADEMIA DE CONQUISTA ÉPICA
            </span>
          </motion.h1>
          
          <motion.p 
            className="text-xl text-purple-300 mb-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            Planes místicos forjados por IA según tu gloria como Hunter
          </motion.p>
          
          {/* Player Status Bar */}
          <motion.div 
            className="flex items-center justify-center gap-8 mt-6"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.7 }}
          >
            <div className="flex items-center gap-3 bg-black/50 backdrop-blur-md rounded-full px-6 py-3 border border-gold-500/30">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              >
                <Crown className="w-6 h-6 text-gold-400" />
              </motion.div>
              <div className="text-left">
                <div className="text-xs text-purple-400">Rango Actual</div>
                <div className="text-xl font-bold text-gold-400">{hunterRank}</div>
              </div>
            </div>
            
            <div className="flex items-center gap-3 bg-black/50 backdrop-blur-md rounded-full px-6 py-3 border border-purple-500/30">
              <motion.div
                animate={{ 
                  scale: [1, 1.2, 1],
                  rotate: [0, 180, 360]
                }}
                transition={{ duration: 3, repeat: Infinity }}
              >
                <Sparkles className="w-6 h-6 text-purple-400" />
              </motion.div>
              <div className="text-left">
                <div className="text-xs text-purple-400">Orbes de Poder</div>
                <div className="text-xl font-bold text-purple-300">{orbsEarned} 💎</div>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* Epic Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 bg-black/50 backdrop-blur-xl rounded-xl border border-purple-500/30 p-1">
            {[
              { value: 'dashboard', label: 'Dashboard', icon: BarChart3 },
              { value: 'plans', label: 'Planes', icon: BookOpen },
              { value: 'statistics', label: 'Runas', icon: Activity },
              { value: 'progress', label: 'Progreso', icon: TrendingUp }
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

          <TabsContent value="dashboard" className="mt-6">
            <DashboardView 
              dashboard={dashboard} 
              onPlanSelect={loadPlanDetails}
              getSubjectIcon={getSubjectIcon}
              getDifficultyColor={getDifficultyColor}
              hoveredCard={hoveredCard}
              setHoveredCard={setHoveredCard}
            />
          </TabsContent>

          <TabsContent value="plans" className="mt-6">
            <PlansView 
              plans={dashboard?.plans || []} 
              onPlanSelect={loadPlanDetails}
              onUnitProgress={updateUnitProgress}
              onWeightedProgress={updateWeightedProgress}
              getSubjectIcon={getSubjectIcon}
              getDifficultyColor={getDifficultyColor}
            />
          </TabsContent>

          <TabsContent value="statistics" className="mt-6">
            <StatisticsView 
              selectedPlan={selectedPlan}
              statistics={planStatistics}
              onLoadStatistics={loadPlanStatistics}
            />
          </TabsContent>

          <TabsContent value="progress" className="mt-6">
            <ProgressView 
              dashboard={dashboard}
              selectedPlan={selectedPlan}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function DashboardView({ 
  dashboard, 
  onPlanSelect,
  getSubjectIcon,
  getDifficultyColor,
  hoveredCard,
  setHoveredCard
}: { 
  dashboard: StudyPlanDashboard | null, 
  onPlanSelect: (planId: string) => void,
  getSubjectIcon: (subject: string) => React.ReactNode,
  getDifficultyColor: (difficulty: string) => string,
  hoveredCard: string | null,
  setHoveredCard: (id: string | null) => void
}) {
  if (!dashboard) return null;

  const statsCards = [
    { title: 'Planes Totales', value: dashboard.total_plans, icon: BookOpen, color: 'from-purple-600 to-purple-800', glow: '#8a2be2' },
    { title: 'Planes Activos', value: dashboard.active_plans, icon: Zap, color: 'from-gold-600 to-orange-600', glow: '#ffd700' },
    { title: 'Gloria Promedio', value: `${dashboard.average_progress.toFixed(1)}%`, icon: TrendingUp, color: 'from-blue-600 to-cyan-600', glow: '#3b82f6' },
    { title: 'Unidades Conquistadas', value: dashboard.total_completed_units, icon: Award, color: 'from-green-600 to-emerald-600', glow: '#10b981' }
  ];

  return (
    <div className="space-y-6">
      {/* Epic Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {statsCards.map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -5 }}
            onHoverStart={() => {
              setHoveredCard(stat.title);
              hoverSound?.play();
            }}
            onHoverEnd={() => setHoveredCard(null)}
          >
            <Card className="relative overflow-hidden bg-black/40 backdrop-blur-md border-purple-500/30 hover:border-gold-400/50 transition-all duration-300">
              {/* Animated gradient background */}
              <motion.div
                className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-10`}
                animate={hoveredCard === stat.title ? {
                  opacity: [0.1, 0.3, 0.1],
                } : {}}
                transition={{ duration: 2, repeat: Infinity }}
              />
              
              {/* Glow effect */}
              {hoveredCard === stat.title && (
                <motion.div
                  className="absolute inset-0"
                  style={{
                    background: `radial-gradient(circle at center, ${stat.glow}40 0%, transparent 70%)`,
                  }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                />
              )}
              
              <CardHeader className="relative z-10 flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gold-300">{stat.title}</CardTitle>
                <motion.div
                  animate={hoveredCard === stat.title ? { 
                    rotate: [0, 360],
                    scale: [1, 1.2, 1]
                  } : {}}
                  transition={{ duration: 0.5 }}
                >
                  <stat.icon className="h-5 w-5 text-purple-400" />
                </motion.div>
              </CardHeader>
              <CardContent className="relative z-10">
                <div className="text-3xl font-bold text-gold-400">{stat.value}</div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Recent Plans Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <Card className="bg-black/40 backdrop-blur-xl border-purple-500/30">
          <CardHeader>
            <CardTitle className="text-2xl text-gold-400 flex items-center gap-3">
              <Flame className="w-6 h-6" />
              Planes Recientes de Conquista
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {dashboard.plans.slice(0, 6).map((plan, index) => (
                <motion.div
                  key={plan.id}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.6 + index * 0.1 }}
                  whileHover={{ scale: 1.05 }}
                  onHoverStart={() => hoverSound?.play()}
                >
                  <Card 
                    className="cursor-pointer bg-black/60 backdrop-blur-sm border-purple-500/30 hover:border-gold-400/50 transition-all duration-300 overflow-hidden group"
                    onClick={() => {
                      clickSound?.play();
                      onPlanSelect(plan.id);
                    }}
                    style={{
                      boxShadow: hoveredCard === plan.id ? '0 0 30px rgba(255, 215, 0, 0.5)' : 'none'
                    }}
                    onMouseEnter={() => setHoveredCard(plan.id)}
                    onMouseLeave={() => setHoveredCard(null)}
                  >
                    {/* Shimmer effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
                    
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          {getSubjectIcon(plan.subject)}
                          <CardTitle className="text-lg text-gold-300 capitalize">
                            {plan.subject}
                          </CardTitle>
                        </div>
                        <Badge className={`${getDifficultyColor(plan.difficulty_level)} shadow-lg`}>
                          {plan.difficulty_level}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="mb-4">
                        <div className="flex justify-between text-sm mb-2">
                          <span className="text-purple-300">Progreso Místico</span>
                          <span className="text-gold-400 font-bold">{plan.progress_percentage.toFixed(1)}%</span>
                        </div>
                        <div className="relative">
                          <Progress value={plan.progress_percentage} className="h-3 bg-black/50" />
                          <motion.div
                            className="absolute inset-0 h-3 bg-gradient-to-r from-purple-500 to-gold-500 rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${plan.progress_percentage}%` }}
                            transition={{ duration: 1, delay: 0.8 + index * 0.1 }}
                            style={{
                              boxShadow: '0 0 10px rgba(255, 215, 0, 0.8)'
                            }}
                          />
                        </div>
                      </div>
                      <div className="text-sm text-gray-300">
                        {plan.completed_units}/{plan.total_units} unidades conquistadas
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Epic Time Estimation */}
      {dashboard.estimated_completion_time && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1 }}
        >
          <Card className="bg-gradient-to-r from-purple-900/40 to-gold-900/40 backdrop-blur-xl border-gold-500/50">
            <CardHeader>
              <CardTitle className="flex items-center space-x-3 text-2xl text-gold-400">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                >
                  <Clock className="h-6 w-6" />
                </motion.div>
                <span>Tiempo para la Gloria Final</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <motion.div 
                className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-gold-400"
                animate={{ 
                  textShadow: [
                    "0 0 20px #ffd700",
                    "0 0 40px #8a2be2",
                    "0 0 20px #ffd700"
                  ]
                }}
                transition={{ duration: 3, repeat: Infinity }}
              >
                {dashboard.estimated_completion_time}
              </motion.div>
              <p className="text-sm text-purple-300 mt-3">
                Basado en tu ritmo de conquista actual, Hunter
              </p>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}

function PlansView({ 
  plans, 
  onPlanSelect, 
  onUnitProgress,
  onWeightedProgress,
  getSubjectIcon,
  getDifficultyColor
}: {
  plans: StudyPlan[],
  onPlanSelect: (planId: string) => void,
  onUnitProgress: (planId: string, unitNumber: number, score: number, isCompleted: boolean) => void,
  onWeightedProgress: (planId: string, unitNumber: number, componentType: string, completed: number, total: number, isCompleted: boolean) => void,
  getSubjectIcon: (subject: string) => React.ReactNode,
  getDifficultyColor: (difficulty: string) => string
}) {
  const [expandedPlans, setExpandedPlans] = useState<Set<string>>(new Set());
  const [hoveredUnit, setHoveredUnit] = useState<string | null>(null);

  const togglePlanExpansion = (planId: string) => {
    const newExpanded = new Set(expandedPlans);
    if (newExpanded.has(planId)) {
      newExpanded.delete(planId);
    } else {
      newExpanded.add(planId);
      clickSound?.play();
    }
    setExpandedPlans(newExpanded);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {plans.map((plan, index) => (
        <motion.div
          key={plan.id}
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <StudyPlanCard 
            plan={plan} 
            isExpanded={expandedPlans.has(plan.id)}
            onToggleExpansion={() => togglePlanExpansion(plan.id)}
            onPlanSelect={onPlanSelect}
            onUnitProgress={onUnitProgress}
            onWeightedProgress={onWeightedProgress}
            getSubjectIcon={getSubjectIcon}
            getDifficultyColor={getDifficultyColor}
            hoveredUnit={hoveredUnit}
            setHoveredUnit={setHoveredUnit}
          />
        </motion.div>
      ))}
    </div>
  );
}

function StudyPlanCard({ 
  plan, 
  isExpanded, 
  onToggleExpansion, 
  onPlanSelect, 
  onUnitProgress,
  onWeightedProgress,
  getSubjectIcon,
  getDifficultyColor,
  hoveredUnit,
  setHoveredUnit
}: {
  plan: StudyPlan,
  isExpanded: boolean,
  onToggleExpansion: () => void,
  onPlanSelect: (planId: string) => void,
  onUnitProgress: (planId: string, unitNumber: number, score: number, isCompleted: boolean) => void,
  onWeightedProgress: (planId: string, unitNumber: number, componentType: string, completed: number, total: number, isCompleted: boolean) => void,
  getSubjectIcon: (subject: string) => React.ReactNode,
  getDifficultyColor: (difficulty: string) => string,
  hoveredUnit: string | null,
  setHoveredUnit: (id: string | null) => void
}) {
  return (
    <Card className="mb-4 bg-black/40 backdrop-blur-xl border-purple-500/30 hover:border-gold-400/50 transition-all duration-300 overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getSubjectIcon(plan.subject)}
            <div>
              <CardTitle className="text-xl text-gold-400">{plan.plan_name}</CardTitle>
              <p className="text-sm text-purple-300">{plan.subject}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge className={`${getDifficultyColor(plan.difficulty_level)} shadow-lg`}>
              {plan.difficulty_level}
            </Badge>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={onToggleExpansion}
              className="px-3 py-1 bg-purple-600/30 hover:bg-purple-600/50 text-gold-300 rounded-lg text-sm font-medium transition-all"
              onMouseEnter={() => hoverSound?.play()}
            >
              {isExpanded ? 'Ocultar' : 'Ver'} Unidades
            </motion.button>
          </div>
        </div>
        
        <div className="space-y-3 mt-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Progreso Místico General</span>
            <span className="text-sm font-bold text-gold-400">{plan.progress_percentage.toFixed(1)}%</span>
          </div>
          <div className="relative">
            <Progress value={plan.progress_percentage} className="h-3 bg-black/50" />
            <motion.div
              className="absolute inset-0 h-3 bg-gradient-to-r from-purple-500 to-gold-500 rounded-full"
              style={{
                width: `${plan.progress_percentage}%`,
                boxShadow: '0 0 10px rgba(255, 215, 0, 0.8)'
              }}
            />
          </div>
          
          <div className="grid grid-cols-3 gap-4 text-sm mt-4">
            <motion.div 
              className="text-center"
              whileHover={{ scale: 1.05 }}
            >
              <div className="font-bold text-gold-300">{plan.completed_units}/{plan.total_units}</div>
              <div className="text-gray-400 text-xs">Unidades</div>
            </motion.div>
            <motion.div 
              className="text-center"
              whileHover={{ scale: 1.05 }}
            >
              <div className="font-bold text-gold-300">{plan.estimated_duration}</div>
              <div className="text-gray-400 text-xs">Duración</div>
            </motion.div>
            <motion.div 
              className="text-center"
              whileHover={{ scale: 1.05 }}
            >
              <div className="font-bold text-gold-300">{plan.last_updated}</div>
              <div className="text-gray-400 text-xs">Actualizado</div>
            </motion.div>
          </div>
        </div>
      </CardHeader>
      
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <CardContent>
              <div className="space-y-4">
                {plan.units.map((unit, unitIndex) => (
                  <motion.div
                    key={unit.unit_number}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: unitIndex * 0.1 }}
                    className="border border-purple-500/20 rounded-xl p-5 space-y-3 bg-black/30 backdrop-blur-sm hover:border-gold-400/30 transition-all"
                    onMouseEnter={() => {
                      setHoveredUnit(`${plan.id}-${unit.unit_number}`);
                      hoverSound?.play();
                    }}
                    onMouseLeave={() => setHoveredUnit(null)}
                    style={{
                      boxShadow: hoveredUnit === `${plan.id}-${unit.unit_number}` 
                        ? '0 0 20px rgba(255, 215, 0, 0.3)' 
                        : 'none'
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gold-300 flex items-center gap-2">
                          <Swords className="w-4 h-4" />
                          Unidad {unit.unit_number}: {unit.unit_name}
                        </h4>
                        <p className="text-sm text-purple-300 mt-1">{unit.unit_description}</p>
                      </div>
                      <div className="flex items-center space-x-3">
                        <Badge 
                          className={unit.is_completed 
                            ? "bg-green-600 text-white" 
                            : "bg-gray-600 text-white"
                          }
                        >
                          {unit.is_completed ? "Conquistada" : "Pendiente"}
                        </Badge>
                        <span className="text-sm font-bold text-gold-400">{unit.score.toFixed(1)}%</span>
                      </div>
                    </div>
                    
                    {/* Epic Weighted Progress */}
                    <WeightedProgressDisplay 
                      weightedProgress={unit.weighted_progress}
                      planId={plan.id}
                      unitNumber={unit.unit_number}
                      onWeightedProgress={onWeightedProgress}
                    />
                    
                    <div className="flex items-center justify-between text-sm pt-2">
                      <span className="text-gray-400 flex items-center gap-2">
                        <Clock className="w-3 h-3" />
                        {unit.estimated_time_minutes} min estimados
                      </span>
                      <div className="flex space-x-2">
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => onUnitProgress(plan.id, unit.unit_number, unit.score, true)}
                          className="px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-lg text-sm font-medium shadow-lg transition-all"
                          style={{ boxShadow: '0 0 15px rgba(16, 185, 129, 0.5)' }}
                        >
                          Completar
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => {
                            clickSound?.play();
                            onPlanSelect(plan.id);
                          }}
                          className="px-4 py-2 bg-gradient-to-r from-purple-600 to-purple-800 hover:from-purple-700 hover:to-purple-900 text-white rounded-lg text-sm font-medium shadow-lg transition-all"
                          style={{ boxShadow: '0 0 15px rgba(139, 92, 246, 0.5)' }}
                        >
                          Ver Detalles
                        </motion.button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

function StatisticsView({ selectedPlan, statistics, onLoadStatistics }: {
  selectedPlan: StudyPlan | null,
  statistics: PlanStatistics | null,
  onLoadStatistics: (planId: string) => void
}) {
  useEffect(() => {
    if (selectedPlan && !statistics) {
      onLoadStatistics(selectedPlan.id);
    }
  }, [selectedPlan, statistics, onLoadStatistics]);

  if (!selectedPlan) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-16"
      >
        <motion.div
          animate={{ 
            y: [0, -10, 0],
            rotate: [0, 5, -5, 0]
          }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          <BarChart3 className="w-24 h-24 text-purple-400 mx-auto mb-4" />
        </motion.div>
        <p className="text-purple-300 text-xl">Selecciona un plan para invocar sus runas estadísticas</p>
      </motion.div>
    );
  }

  if (!statistics) {
    return (
      <div className="text-center py-16">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 border-4 border-gold-500 border-t-transparent rounded-full mx-auto"
        />
        <p className="mt-4 text-purple-300">Invocando runas ancestrales...</p>
      </div>
    );
  }

  const statCards = [
    { title: 'Gloria Promedio', value: `${statistics.average_score.toFixed(1)}%`, color: 'from-blue-600 to-cyan-600', icon: Trophy },
    { title: 'Tasa de Conquista', value: `${statistics.completion_rate.toFixed(1)}%`, color: 'from-green-600 to-emerald-600', icon: CheckCircle },
    { title: 'Tiempo en Batallas', value: `${statistics.time_spent_minutes} min`, color: 'from-purple-600 to-pink-600', icon: Clock }
  ];

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card className="bg-black/40 backdrop-blur-xl border-purple-500/30">
          <CardHeader>
            <CardTitle className="text-2xl text-gold-400 flex items-center gap-3">
              <Activity className="w-6 h-6" />
              Runas de {selectedPlan.plan_name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {statCards.map((stat, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.05 }}
                  className="relative overflow-hidden rounded-xl p-6 bg-gradient-to-br from-black/60 to-black/30 border border-purple-500/20"
                >
                  <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-10`} />
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                    className="absolute -right-4 -top-4 opacity-10"
                  >
                    <stat.icon className="w-24 h-24" />
                  </motion.div>
                  <div className="relative z-10 text-center">
                    <div className="text-3xl font-bold text-white mb-2">{stat.value}</div>
                    <div className="text-sm text-purple-300">{stat.title}</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {statistics.improvement_trend.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-black/40 backdrop-blur-xl border-purple-500/30">
            <CardHeader>
              <CardTitle className="text-2xl text-gold-400 flex items-center gap-3">
                <TrendingUp className="w-6 h-6" />
                Tendencia de Ascenso Legendario
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {statistics.improvement_trend.map((trend, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + index * 0.1 }}
                    className="flex items-center justify-between p-4 bg-black/30 rounded-lg border border-purple-500/20 hover:border-gold-400/30 transition-all"
                    whileHover={{ x: 5 }}
                  >
                    <span className="text-gold-300 font-medium flex items-center gap-2">
                      <Shield className="w-4 h-4" />
                      Unidad {trend.unit_number}
                    </span>
                    <div className="flex items-center space-x-4">
                      <span className="text-purple-300">{trend.score}%</span>
                      <Badge 
                        className={trend.improvement > 0 
                          ? "bg-green-600 text-white" 
                          : "bg-red-600 text-white"
                        }
                      >
                        {trend.improvement > 0 ? "↑" : "↓"} {Math.abs(trend.improvement).toFixed(1)}%
                      </Badge>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}

function ProgressView({ dashboard, selectedPlan }: {
  dashboard: StudyPlanDashboard | null,
  selectedPlan: StudyPlan | null
}) {
  if (!dashboard) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <Card className="bg-black/40 backdrop-blur-xl border-purple-500/30">
        <CardHeader>
          <CardTitle className="text-2xl text-gold-400 flex items-center gap-3">
            <Crown className="w-6 h-6" />
            Progreso Místico General
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold mb-4 text-gold-300 text-lg">Progreso por Reino (Materia)</h3>
              {dashboard.plans.map((plan, index) => (
                <motion.div 
                  key={plan.id} 
                  className="mb-4"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div className="flex justify-between text-sm mb-2">
                    <span className="capitalize text-purple-300 font-medium">{plan.subject}</span>
                    <span className="text-gold-400 font-bold">{plan.progress_percentage.toFixed(1)}%</span>
                  </div>
                  <div className="relative">
                    <Progress value={plan.progress_percentage} className="h-3 bg-black/50" />
                    <motion.div
                      className="absolute inset-0 h-3 bg-gradient-to-r from-purple-500 to-gold-500 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${plan.progress_percentage}%` }}
                      transition={{ duration: 1, delay: 0.5 + index * 0.1 }}
                      style={{
                        boxShadow: '0 0 10px rgba(255, 215, 0, 0.6)'
                      }}
                    />
                  </div>
                </motion.div>
              ))}
            </div>
            
            <div>
              <h3 className="font-semibold mb-4 text-gold-300 text-lg">Resumen de Conquista</h3>
              <div className="space-y-3 bg-black/30 rounded-xl p-6 border border-purple-500/20">
                {[
                  { label: 'Planes Activos', value: dashboard.active_plans, icon: Zap },
                  { label: 'Gloria Promedio', value: `${dashboard.average_progress.toFixed(1)}%`, icon: TrendingUp },
                  { label: 'Unidades Conquistadas', value: dashboard.total_completed_units, icon: Award },
                  { label: 'Tiempo para Rango S+', value: dashboard.estimated_completion_time || 'Calculando...', icon: Clock }
                ].map((item, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + index * 0.1 }}
                    className="flex justify-between items-center p-3 bg-black/40 rounded-lg hover:bg-black/60 transition-all"
                    whileHover={{ scale: 1.02 }}
                  >
                    <span className="text-purple-300 flex items-center gap-2">
                      <item.icon className="w-4 h-4" />
                      {item.label}:
                    </span>
                    <span className="font-bold text-gold-400">{item.value}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function WeightedProgressDisplay({ 
  weightedProgress,
  planId,
  unitNumber,
  onWeightedProgress
}: { 
  weightedProgress: WeightedProgress,
  planId: string,
  unitNumber: number,
  onWeightedProgress: (planId: string, unitNumber: number, componentType: string, completed: number, total: number, isCompleted: boolean) => void
}) {
  const components = [
    { key: 'videos', label: 'Videos Arcanos', color: 'from-blue-500 to-blue-700', icon: Video, weight: 0.3 },
    { key: 'exercises', label: 'Ejercicios de Combate', color: 'from-green-500 to-green-700', icon: Target, weight: 0.5 },
    { key: 'readings', label: 'Pergaminos Antiguos', color: 'from-purple-500 to-purple-700', icon: FileText, weight: 0.2 }
  ];

  const calculateTotalProgress = () => {
    let totalProgress = 0;
    components.forEach(comp => {
      const data = weightedProgress[comp.key as keyof WeightedProgress];
      if (data.total > 0) {
        totalProgress += (data.completed / data.total) * comp.weight;
      }
    });
    return totalProgress * 100;
  };

  const handleProgressUpdate = (componentKey: string, completed: number, total: number) => {
    onWeightedProgress(planId, unitNumber, componentKey, completed, total, completed === total);
    if (completed === total) {
      completionSound?.play();
    } else {
      clickSound?.play();
    }
  };

  return (
    <div className="space-y-3 bg-black/20 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gold-300 flex items-center gap-2">
          <Sparkles className="w-4 h-4" />
          Progreso Ponderado Místico
        </h4>
        <motion.span 
          className="text-sm font-bold text-gold-400"
          animate={{ 
            textShadow: [
              "0 0 10px #ffd700",
              "0 0 20px #ffd700",
              "0 0 10px #ffd700"
            ]
          }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          {calculateTotalProgress().toFixed(1)}%
        </motion.span>
      </div>
      
      <div className="space-y-3">
        {components.map((comp, index) => {
          const data = weightedProgress[comp.key as keyof WeightedProgress];
          const progress = data.total > 0 ? (data.completed / data.total) * 100 : 0;
          
          return (
            <motion.div 
              key={comp.key} 
              className="space-y-2"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <div className="flex items-center justify-between text-xs">
                <span className="text-purple-300 flex items-center gap-2">
                  <comp.icon className="w-3 h-3" />
                  {comp.label}
                </span>
                <span className="text-gray-400">
                  {data.completed}/{data.total} ({progress.toFixed(1)}%)
                </span>
              </div>
              <div className="relative">
                <div className="w-full bg-black/50 rounded-full h-2.5 overflow-hidden">
                  <motion.div 
                    className={`h-2.5 rounded-full bg-gradient-to-r ${comp.color}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 1, delay: 0.2 + index * 0.1 }}
                    style={{
                      boxShadow: `0 0 10px ${comp.color.includes('blue') ? '#3b82f6' : comp.color.includes('green') ? '#10b981' : '#8a2be2'}`
                    }}
                  />
                </div>
                <div className="flex items-center justify-between mt-1">
                  <div className="text-xs text-gray-500">
                    Peso Arcano: {(comp.weight * 100).toFixed(0)}%
                  </div>
                  {data.completed < data.total && (
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => handleProgressUpdate(comp.key, data.completed + 1, data.total)}
                      className="text-xs px-2 py-0.5 bg-purple-600/30 hover:bg-purple-600/50 text-gold-300 rounded transition-all"
                    >
                      +1
                    </motion.button>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}