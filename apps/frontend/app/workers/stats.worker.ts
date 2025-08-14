// Statistics Worker for complex calculations
// This worker handles heavy statistical computations off the main thread

interface CalculateZScoreMessage {
  type: 'CALCULATE_Z_SCORE';
  data: {
    userScore: number;
    mean: number;
    standardDeviation: number;
  };
}

interface CalculateBatchZScoreMessage {
  type: 'CALCULATE_BATCH_Z_SCORE';
  data: {
    scores: number[];
    populationScores: number[];
  };
}

interface CalculatePercentileMessage {
  type: 'CALCULATE_PERCENTILE';
  data: {
    score: number;
    scores: number[];
  };
}

interface CalculateStatisticsMessage {
  type: 'CALCULATE_STATISTICS';
  data: {
    values: number[];
  };
}

interface AnalyzePerformanceMessage {
  type: 'ANALYZE_PERFORMANCE';
  data: {
    userAnswers: {
      questionId: string;
      isCorrect: boolean;
      responseTime: number;
      difficulty: number;
      topic: string;
    }[];
    populationData: {
      averageByTopic: Record<string, number>;
      averageByDifficulty: Record<number, number>;
    };
  };
}

type WorkerMessage = 
  | CalculateZScoreMessage
  | CalculateBatchZScoreMessage
  | CalculatePercentileMessage
  | CalculateStatisticsMessage
  | AnalyzePerformanceMessage;

// Helper functions
function calculateMean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, val) => sum + val, 0) / values.length;
}

function calculateStandardDeviation(values: number[], mean?: number): number {
  if (values.length === 0) return 0;
  const avg = mean ?? calculateMean(values);
  const squaredDiffs = values.map(val => Math.pow(val - avg, 2));
  const variance = calculateMean(squaredDiffs);
  return Math.sqrt(variance);
}

function calculateMedian(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 
    ? (sorted[mid - 1] + sorted[mid]) / 2 
    : sorted[mid];
}

function calculateQuartiles(values: number[]): { q1: number; q2: number; q3: number } {
  if (values.length === 0) return { q1: 0, q2: 0, q3: 0 };
  const sorted = [...values].sort((a, b) => a - b);
  const n = sorted.length;
  
  return {
    q1: sorted[Math.floor(n * 0.25)],
    q2: calculateMedian(sorted),
    q3: sorted[Math.floor(n * 0.75)]
  };
}

function calculateZScore(value: number, mean: number, stdDev: number): number {
  if (stdDev === 0) return 0;
  return (value - mean) / stdDev;
}

function calculatePercentile(value: number, values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const below = sorted.filter(v => v < value).length;
  return (below / sorted.length) * 100;
}

// Message handler
self.addEventListener('message', (event: MessageEvent<WorkerMessage>) => {
  const { type, data } = event.data;
  
  try {
    switch (type) {
      case 'CALCULATE_Z_SCORE': {
        const zScore = calculateZScore(
          data.userScore,
          data.mean,
          data.standardDeviation
        );
        
        self.postMessage({
          type: 'Z_SCORE_RESULT',
          data: { zScore }
        });
        break;
      }
      
      case 'CALCULATE_BATCH_Z_SCORE': {
        const { scores, populationScores } = data;
        const mean = calculateMean(populationScores);
        const stdDev = calculateStandardDeviation(populationScores, mean);
        
        const zScores = scores.map(score => ({
          score,
          zScore: calculateZScore(score, mean, stdDev),
          percentile: calculatePercentile(score, populationScores)
        }));
        
        self.postMessage({
          type: 'BATCH_Z_SCORE_RESULT',
          data: { zScores, mean, stdDev }
        });
        break;
      }
      
      case 'CALCULATE_PERCENTILE': {
        const percentile = calculatePercentile(data.score, data.scores);
        
        self.postMessage({
          type: 'PERCENTILE_RESULT',
          data: { percentile }
        });
        break;
      }
      
      case 'CALCULATE_STATISTICS': {
        const { values } = data;
        const mean = calculateMean(values);
        const stdDev = calculateStandardDeviation(values, mean);
        const median = calculateMedian(values);
        const quartiles = calculateQuartiles(values);
        const min = Math.min(...values);
        const max = Math.max(...values);
        
        self.postMessage({
          type: 'STATISTICS_RESULT',
          data: {
            mean,
            standardDeviation: stdDev,
            median,
            quartiles,
            min,
            max,
            count: values.length
          }
        });
        break;
      }
      
      case 'ANALYZE_PERFORMANCE': {
        const { userAnswers, populationData } = data;
        
        // Analyze by topic
        const topicAnalysis: Record<string, {
          accuracy: number;
          avgResponseTime: number;
          zScore: number;
          strength: 'weak' | 'average' | 'strong';
        }> = {};
        
        const topicGroups = userAnswers.reduce((acc, answer) => {
          if (!acc[answer.topic]) {
            acc[answer.topic] = [];
          }
          acc[answer.topic].push(answer);
          return acc;
        }, {} as Record<string, typeof userAnswers>);
        
        Object.entries(topicGroups).forEach(([topic, answers]) => {
          const correct = answers.filter(a => a.isCorrect).length;
          const accuracy = (correct / answers.length) * 100;
          const avgResponseTime = calculateMean(answers.map(a => a.responseTime));
          
          const populationAvg = populationData.averageByTopic[topic] || 70;
          const assumedStdDev = 15; // Assumed standard deviation
          const zScore = calculateZScore(accuracy, populationAvg, assumedStdDev);
          
          let strength: 'weak' | 'average' | 'strong';
          if (zScore < -1) strength = 'weak';
          else if (zScore > 1) strength = 'strong';
          else strength = 'average';
          
          topicAnalysis[topic] = {
            accuracy,
            avgResponseTime,
            zScore,
            strength
          };
        });
        
        // Analyze by difficulty
        const difficultyAnalysis: Record<number, {
          accuracy: number;
          totalQuestions: number;
        }> = {};
        
        const difficultyGroups = userAnswers.reduce((acc, answer) => {
          if (!acc[answer.difficulty]) {
            acc[answer.difficulty] = [];
          }
          acc[answer.difficulty].push(answer);
          return acc;
        }, {} as Record<number, typeof userAnswers>);
        
        Object.entries(difficultyGroups).forEach(([difficulty, answers]) => {
          const correct = answers.filter(a => a.isCorrect).length;
          const accuracy = (correct / answers.length) * 100;
          
          difficultyAnalysis[parseInt(difficulty)] = {
            accuracy,
            totalQuestions: answers.length
          };
        });
        
        // Overall performance
        const totalCorrect = userAnswers.filter(a => a.isCorrect).length;
        const overallAccuracy = (totalCorrect / userAnswers.length) * 100;
        const avgResponseTime = calculateMean(userAnswers.map(a => a.responseTime));
        
        // Time analysis
        const timeAnalysis = {
          fastest: Math.min(...userAnswers.map(a => a.responseTime)),
          slowest: Math.max(...userAnswers.map(a => a.responseTime)),
          average: avgResponseTime,
          belowAverage: userAnswers.filter(a => a.responseTime < avgResponseTime).length
        };
        
        self.postMessage({
          type: 'PERFORMANCE_ANALYSIS_RESULT',
          data: {
            topicAnalysis,
            difficultyAnalysis,
            overall: {
              accuracy: overallAccuracy,
              totalQuestions: userAnswers.length,
              correctAnswers: totalCorrect,
              avgResponseTime
            },
            timeAnalysis,
            recommendations: generateRecommendations(topicAnalysis, difficultyAnalysis)
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

// Generate recommendations based on analysis
function generateRecommendations(
  topicAnalysis: Record<string, any>,
  difficultyAnalysis: Record<number, any>
): string[] {
  const recommendations: string[] = [];
  
  // Topic-based recommendations
  Object.entries(topicAnalysis).forEach(([topic, analysis]) => {
    if (analysis.strength === 'weak') {
      recommendations.push(`Refuerza tus conocimientos en ${topic} (precisión: ${analysis.accuracy.toFixed(1)}%)`);
    } else if (analysis.strength === 'strong') {
      recommendations.push(`¡Excelente dominio en ${topic}! Continúa así.`);
    }
    
    if (analysis.avgResponseTime > 15000) {
      recommendations.push(`Practica más ejercicios de ${topic} para mejorar tu velocidad`);
    }
  });
  
  // Difficulty-based recommendations
  const difficulties = Object.entries(difficultyAnalysis);
  const hardQuestions = difficulties.filter(([diff]) => parseInt(diff) >= 4);
  
  if (hardQuestions.length > 0) {
    const avgHardAccuracy = calculateMean(hardQuestions.map(([, data]) => data.accuracy));
    if (avgHardAccuracy < 50) {
      recommendations.push('Dedica más tiempo a problemas de alta dificultad');
    }
  }
  
  return recommendations;
}

// Export for TypeScript
export {};