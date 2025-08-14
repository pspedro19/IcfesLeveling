// Analytics Worker for background data processing
// Handles heavy analytics computations without blocking the UI

interface ProcessBattleDataMessage {
  type: 'PROCESS_BATTLE_DATA';
  data: {
    battles: {
      id: string;
      userId: string;
      timestamp: number;
      duration: number;
      questionsAnswered: number;
      correctAnswers: number;
      experienceGained: number;
      enemyLevel: number;
      enemyType: string;
    }[];
  };
}

interface ProcessUserProgressMessage {
  type: 'PROCESS_USER_PROGRESS';
  data: {
    progressHistory: {
      date: string;
      level: number;
      experience: number;
      rank: string;
      battlesWon: number;
      questionsAnswered: number;
      accuracy: number;
    }[];
  };
}

interface GenerateInsightsMessage {
  type: 'GENERATE_INSIGHTS';
  data: {
    userStats: {
      totalBattles: number;
      winRate: number;
      avgAccuracy: number;
      favoriteSubject: string;
      weakestTopic: string;
      strongestTopic: string;
      peakHour: number;
      streakDays: number;
    };
    compareWithPopulation: boolean;
  };
}

interface AggregateMetricsMessage {
  type: 'AGGREGATE_METRICS';
  data: {
    events: {
      type: string;
      timestamp: number;
      data: any;
    }[];
    period: 'daily' | 'weekly' | 'monthly';
  };
}

type WorkerMessage = 
  | ProcessBattleDataMessage
  | ProcessUserProgressMessage
  | GenerateInsightsMessage
  | AggregateMetricsMessage;

// Helper functions
function groupByPeriod<T extends { timestamp: number }>(
  items: T[],
  period: 'daily' | 'weekly' | 'monthly'
): Record<string, T[]> {
  const groups: Record<string, T[]> = {};
  
  items.forEach(item => {
    const date = new Date(item.timestamp);
    let key: string;
    
    switch (period) {
      case 'daily':
        key = date.toISOString().split('T')[0];
        break;
      case 'weekly':
        const weekStart = new Date(date);
        weekStart.setDate(date.getDate() - date.getDay());
        key = weekStart.toISOString().split('T')[0];
        break;
      case 'monthly':
        key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        break;
    }
    
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
  });
  
  return groups;
}

function calculateTrend(values: number[]): {
  trend: 'increasing' | 'decreasing' | 'stable';
  percentage: number;
} {
  if (values.length < 2) {
    return { trend: 'stable', percentage: 0 };
  }
  
  const firstHalf = values.slice(0, Math.floor(values.length / 2));
  const secondHalf = values.slice(Math.floor(values.length / 2));
  
  const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
  const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
  
  const change = ((secondAvg - firstAvg) / firstAvg) * 100;
  
  let trend: 'increasing' | 'decreasing' | 'stable';
  if (change > 5) trend = 'increasing';
  else if (change < -5) trend = 'decreasing';
  else trend = 'stable';
  
  return { trend, percentage: Math.abs(change) };
}

function findPeakHour(timestamps: number[]): number {
  const hours = timestamps.map(ts => new Date(ts).getHours());
  const hourCounts: Record<number, number> = {};
  
  hours.forEach(hour => {
    hourCounts[hour] = (hourCounts[hour] || 0) + 1;
  });
  
  let peakHour = 0;
  let maxCount = 0;
  
  Object.entries(hourCounts).forEach(([hour, count]) => {
    if (count > maxCount) {
      maxCount = count;
      peakHour = parseInt(hour);
    }
  });
  
  return peakHour;
}

// Message handler
self.addEventListener('message', (event: MessageEvent<WorkerMessage>) => {
  const { type, data } = event.data;
  
  try {
    switch (type) {
      case 'PROCESS_BATTLE_DATA': {
        const { battles } = data;
        
        // Group battles by different criteria
        const byDay = groupByPeriod(battles, 'daily');
        const byWeek = groupByPeriod(battles, 'weekly');
        const byEnemyType = battles.reduce((acc, battle) => {
          if (!acc[battle.enemyType]) {
            acc[battle.enemyType] = [];
          }
          acc[battle.enemyType].push(battle);
          return acc;
        }, {} as Record<string, typeof battles>);
        
        // Calculate metrics
        const dailyMetrics = Object.entries(byDay).map(([date, dayBattles]) => {
          const totalQuestions = dayBattles.reduce((sum, b) => sum + b.questionsAnswered, 0);
          const totalCorrect = dayBattles.reduce((sum, b) => sum + b.correctAnswers, 0);
          const totalExp = dayBattles.reduce((sum, b) => sum + b.experienceGained, 0);
          const avgDuration = dayBattles.reduce((sum, b) => sum + b.duration, 0) / dayBattles.length;
          
          return {
            date,
            battles: dayBattles.length,
            accuracy: totalQuestions > 0 ? (totalCorrect / totalQuestions) * 100 : 0,
            experienceGained: totalExp,
            avgBattleDuration: avgDuration,
            questionsPerBattle: totalQuestions / dayBattles.length
          };
        });
        
        // Enemy type analysis
        const enemyTypeStats = Object.entries(byEnemyType).map(([type, typeBattles]) => {
          const wins = typeBattles.filter(b => b.correctAnswers >= b.questionsAnswered * 0.6).length;
          const totalQuestions = typeBattles.reduce((sum, b) => sum + b.questionsAnswered, 0);
          const totalCorrect = typeBattles.reduce((sum, b) => sum + b.correctAnswers, 0);
          
          return {
            enemyType: type,
            totalBattles: typeBattles.length,
            winRate: (wins / typeBattles.length) * 100,
            avgAccuracy: totalQuestions > 0 ? (totalCorrect / totalQuestions) * 100 : 0,
            avgLevel: typeBattles.reduce((sum, b) => sum + b.enemyLevel, 0) / typeBattles.length
          };
        });
        
        // Performance trends
        const accuracyTrend = calculateTrend(dailyMetrics.map(m => m.accuracy));
        const activityTrend = calculateTrend(dailyMetrics.map(m => m.battles));
        
        // Time patterns
        const peakHour = findPeakHour(battles.map(b => b.timestamp));
        const weekdayActivity = battles.reduce((acc, battle) => {
          const day = new Date(battle.timestamp).getDay();
          acc[day] = (acc[day] || 0) + 1;
          return acc;
        }, {} as Record<number, number>);
        
        self.postMessage({
          type: 'BATTLE_DATA_PROCESSED',
          data: {
            dailyMetrics,
            enemyTypeStats,
            trends: {
              accuracy: accuracyTrend,
              activity: activityTrend
            },
            patterns: {
              peakHour,
              weekdayActivity,
              mostActiveDays: Object.entries(weekdayActivity)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 3)
                .map(([day]) => parseInt(day))
            },
            summary: {
              totalBattles: battles.length,
              avgAccuracy: dailyMetrics.reduce((sum, m) => sum + m.accuracy, 0) / dailyMetrics.length,
              totalExperience: battles.reduce((sum, b) => sum + b.experienceGained, 0),
              avgBattlesPerDay: battles.length / dailyMetrics.length
            }
          }
        });
        break;
      }
      
      case 'PROCESS_USER_PROGRESS': {
        const { progressHistory } = data;
        
        // Calculate growth metrics
        const levelProgression = progressHistory.map(p => p.level);
        const experienceProgression = progressHistory.map(p => p.experience);
        const accuracyProgression = progressHistory.map(p => p.accuracy);
        
        // Find milestones
        const milestones = progressHistory.filter((p, i) => {
          if (i === 0) return false;
          const prev = progressHistory[i - 1];
          return p.level > prev.level || p.rank !== prev.rank;
        }).map(p => ({
          date: p.date,
          type: p.rank !== progressHistory[progressHistory.indexOf(p) - 1]?.rank ? 'rank_up' : 'level_up',
          from: progressHistory[progressHistory.indexOf(p) - 1]?.level || p.level - 1,
          to: p.level,
          rank: p.rank
        }));
        
        // Calculate improvement rate
        const firstWeek = progressHistory.slice(0, 7);
        const lastWeek = progressHistory.slice(-7);
        
        const improvementMetrics = {
          levelGrowth: lastWeek[lastWeek.length - 1]?.level - firstWeek[0]?.level || 0,
          accuracyImprovement: (lastWeek.reduce((sum, p) => sum + p.accuracy, 0) / lastWeek.length) -
                               (firstWeek.reduce((sum, p) => sum + p.accuracy, 0) / firstWeek.length),
          questionsPerDayGrowth: (lastWeek.reduce((sum, p) => sum + p.questionsAnswered, 0) / lastWeek.length) -
                                 (firstWeek.reduce((sum, p) => sum + p.questionsAnswered, 0) / firstWeek.length)
        };
        
        // Predict next milestone
        const avgDailyExp = experienceProgression.slice(-7).reduce((sum, exp, i) => {
          if (i === 0) return 0;
          return sum + (exp - experienceProgression[experienceProgression.length - 8 + i]);
        }, 0) / 6;
        
        const currentLevel = progressHistory[progressHistory.length - 1]?.level || 1;
        const currentExp = progressHistory[progressHistory.length - 1]?.experience || 0;
        const expForNextLevel = (currentLevel + 1) * 100; // Assuming 100 exp per level
        const daysToNextLevel = avgDailyExp > 0 ? Math.ceil((expForNextLevel - currentExp) / avgDailyExp) : -1;
        
        self.postMessage({
          type: 'USER_PROGRESS_PROCESSED',
          data: {
            progression: {
              levels: levelProgression,
              experience: experienceProgression,
              accuracy: accuracyProgression
            },
            milestones,
            improvementMetrics,
            predictions: {
              daysToNextLevel,
              projectedLevelIn30Days: currentLevel + Math.floor((avgDailyExp * 30) / 100),
              accuracyTrend: calculateTrend(accuracyProgression)
            },
            streakAnalysis: analyzeStreaks(progressHistory)
          }
        });
        break;
      }
      
      case 'GENERATE_INSIGHTS': {
        const { userStats, compareWithPopulation } = data;
        
        const insights: string[] = [];
        
        // Performance insights
        if (userStats.avgAccuracy > 85) {
          insights.push('🌟 ¡Tu precisión es excepcional! Estás en el top 10% de jugadores.');
        } else if (userStats.avgAccuracy < 60) {
          insights.push('💡 Tu precisión puede mejorar. Tómate más tiempo para analizar las preguntas.');
        }
        
        // Win rate insights
        if (userStats.winRate > 80) {
          insights.push('🏆 Tu tasa de victoria es impresionante. ¡Sigue así!');
        }
        
        // Time pattern insights
        const hourLabel = userStats.peakHour < 12 ? 'mañana' : 
                         userStats.peakHour < 18 ? 'tarde' : 'noche';
        insights.push(`🕐 Tu mejor rendimiento es en la ${hourLabel} (${userStats.peakHour}:00)`);
        
        // Streak insights
        if (userStats.streakDays >= 30) {
          insights.push('🔥 ¡Racha legendaria! Has jugado por más de 30 días consecutivos.');
        } else if (userStats.streakDays >= 7) {
          insights.push(`🎯 Racha de ${userStats.streakDays} días. ¡Mantén el ritmo!`);
        }
        
        // Subject insights
        if (userStats.favoriteSubject && userStats.weakestTopic) {
          insights.push(`📚 Dominas ${userStats.favoriteSubject} pero necesitas reforzar ${userStats.weakestTopic}`);
        }
        
        // Personalized recommendations
        const recommendations = generatePersonalizedRecommendations(userStats);
        
        self.postMessage({
          type: 'INSIGHTS_GENERATED',
          data: {
            insights,
            recommendations,
            badges: generateBadges(userStats),
            comparisons: compareWithPopulation ? generateComparisons(userStats) : null
          }
        });
        break;
      }
      
      case 'AGGREGATE_METRICS': {
        const { events, period } = data;
        
        // Group events by type
        const eventsByType = events.reduce((acc, event) => {
          if (!acc[event.type]) {
            acc[event.type] = [];
          }
          acc[event.type].push(event);
          return acc;
        }, {} as Record<string, typeof events>);
        
        // Aggregate by period
        const aggregated = Object.entries(eventsByType).map(([eventType, typeEvents]) => {
          const grouped = groupByPeriod(typeEvents, period);
          
          return {
            eventType,
            metrics: Object.entries(grouped).map(([periodKey, periodEvents]) => ({
              period: periodKey,
              count: periodEvents.length,
              uniqueData: extractUniqueData(periodEvents)
            }))
          };
        });
        
        // Calculate event correlations
        const correlations = findEventCorrelations(events);
        
        self.postMessage({
          type: 'METRICS_AGGREGATED',
          data: {
            aggregated,
            correlations,
            summary: {
              totalEvents: events.length,
              uniqueEventTypes: Object.keys(eventsByType).length,
              avgEventsPerPeriod: events.length / Object.keys(groupByPeriod(events, period)).length
            }
          }
        });
        break;
      }
      
      default:
        throw new Error(`Unknown message type: ${type}`);
    }
  } catch (error) {
    self.postMessage({
      type: 'ERROR',
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    });
  }
});

// Helper functions for insights
function analyzeStreaks(progressHistory: any[]): any {
  let currentStreak = 0;
  let longestStreak = 0;
  let lastDate: Date | null = null;
  
  progressHistory.forEach(p => {
    const date = new Date(p.date);
    if (lastDate) {
      const dayDiff = Math.floor((date.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24));
      if (dayDiff === 1) {
        currentStreak++;
      } else if (dayDiff > 1) {
        currentStreak = 1;
      }
    } else {
      currentStreak = 1;
    }
    
    longestStreak = Math.max(longestStreak, currentStreak);
    lastDate = date;
  });
  
  return { currentStreak, longestStreak };
}

function generatePersonalizedRecommendations(stats: any): string[] {
  const recommendations: string[] = [];
  
  if (stats.avgAccuracy < 70) {
    recommendations.push('Practica con preguntas de menor dificultad para mejorar tu confianza');
  }
  
  if (stats.peakHour >= 22 || stats.peakHour <= 5) {
    recommendations.push('Considera estudiar más temprano para mejor retención');
  }
  
  if (stats.weakestTopic) {
    recommendations.push(`Dedica 15 minutos diarios a practicar ${stats.weakestTopic}`);
  }
  
  return recommendations;
}

function generateBadges(stats: any): string[] {
  const badges: string[] = [];
  
  if (stats.totalBattles >= 100) badges.push('Veterano');
  if (stats.avgAccuracy >= 90) badges.push('Precisión Perfecta');
  if (stats.streakDays >= 30) badges.push('Dedicación Legendaria');
  if (stats.winRate >= 85) badges.push('Invencible');
  
  return badges;
}

function generateComparisons(stats: any): any {
  // Mock population comparisons
  return {
    accuracy: {
      user: stats.avgAccuracy,
      population: 72.5,
      percentile: Math.min(95, Math.max(5, stats.avgAccuracy - 30 + Math.random() * 20))
    },
    battles: {
      user: stats.totalBattles,
      population: 45,
      percentile: Math.min(95, Math.max(5, (stats.totalBattles / 45) * 50))
    }
  };
}

function extractUniqueData(events: any[]): any {
  // Extract unique values from event data
  const uniqueValues = new Set();
  events.forEach(event => {
    if (event.data && typeof event.data === 'object') {
      Object.values(event.data).forEach(value => {
        if (typeof value === 'string' || typeof value === 'number') {
          uniqueValues.add(value);
        }
      });
    }
  });
  return Array.from(uniqueValues);
}

function findEventCorrelations(events: any[]): any[] {
  // Simple correlation finder
  const correlations: any[] = [];
  const eventPairs: Record<string, number> = {};
  
  for (let i = 0; i < events.length - 1; i++) {
    const pair = `${events[i].type}->${events[i + 1].type}`;
    eventPairs[pair] = (eventPairs[pair] || 0) + 1;
  }
  
  Object.entries(eventPairs).forEach(([pair, count]) => {
    if (count > 5) {
      const [from, to] = pair.split('->');
      correlations.push({ from, to, count, strength: count > 20 ? 'strong' : 'moderate' });
    }
  });
  
  return correlations;
}

// Export for TypeScript
export {};