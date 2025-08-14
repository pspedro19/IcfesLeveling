import { useEffect, useRef, useState, useCallback } from 'react';

type WorkerStatus = 'idle' | 'loading' | 'ready' | 'processing' | 'error';

interface UseWorkerOptions {
  onMessage?: (data: any) => void;
  onError?: (error: Error) => void;
  autoTerminate?: boolean;
}

interface UseWorkerReturn<T = any> {
  postMessage: (message: any) => void;
  terminate: () => void;
  status: WorkerStatus;
  error: Error | null;
  result: T | null;
  isProcessing: boolean;
}

export function useWorker<T = any>(
  workerPath: string,
  options: UseWorkerOptions = {}
): UseWorkerReturn<T> {
  const { onMessage, onError, autoTerminate = true } = options;
  
  const workerRef = useRef<Worker | null>(null);
  const [status, setStatus] = useState<WorkerStatus>('idle');
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<T | null>(null);
  
  // Initialize worker
  useEffect(() => {
    setStatus('loading');
    
    try {
      const worker = new Worker(new URL(workerPath, import.meta.url), {
        type: 'module'
      });
      
      worker.onmessage = (event) => {
        setStatus('ready');
        setResult(event.data);
        onMessage?.(event.data);
      };
      
      worker.onerror = (event) => {
        const err = new Error(event.message || 'Worker error');
        setStatus('error');
        setError(err);
        onError?.(err);
      };
      
      workerRef.current = worker;
      setStatus('ready');
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to initialize worker');
      setStatus('error');
      setError(error);
      onError?.(error);
    }
    
    // Cleanup
    return () => {
      if (autoTerminate && workerRef.current) {
        workerRef.current.terminate();
        workerRef.current = null;
      }
    };
  }, [workerPath, onMessage, onError, autoTerminate]);
  
  // Post message to worker
  const postMessage = useCallback((message: any) => {
    if (!workerRef.current) {
      console.error('Worker not initialized');
      return;
    }
    
    setStatus('processing');
    setError(null);
    
    try {
      workerRef.current.postMessage(message);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to post message');
      setStatus('error');
      setError(error);
      onError?.(error);
    }
  }, [onError]);
  
  // Terminate worker manually
  const terminate = useCallback(() => {
    if (workerRef.current) {
      workerRef.current.terminate();
      workerRef.current = null;
      setStatus('idle');
    }
  }, []);
  
  return {
    postMessage,
    terminate,
    status,
    error,
    result,
    isProcessing: status === 'processing'
  };
}

// Specialized hook for stats worker
interface StatsWorkerResult {
  type: string;
  data: any;
}

export function useStatsWorker() {
  const [results, setResults] = useState<Record<string, any>>({});
  
  const { postMessage, status, error, isProcessing } = useWorker<StatsWorkerResult>(
    '../workers/stats.worker.ts',
    {
      onMessage: (message) => {
        if (message.type && message.data) {
          setResults(prev => ({
            ...prev,
            [message.type]: message.data
          }));
        }
      }
    }
  );
  
  const calculateZScore = useCallback((userScore: number, mean: number, stdDev: number) => {
    postMessage({
      type: 'CALCULATE_Z_SCORE',
      data: { userScore, mean, standardDeviation: stdDev }
    });
  }, [postMessage]);
  
  const calculateBatchZScore = useCallback((scores: number[], populationScores: number[]) => {
    postMessage({
      type: 'CALCULATE_BATCH_Z_SCORE',
      data: { scores, populationScores }
    });
  }, [postMessage]);
  
  const calculatePercentile = useCallback((score: number, scores: number[]) => {
    postMessage({
      type: 'CALCULATE_PERCENTILE',
      data: { score, scores }
    });
  }, [postMessage]);
  
  const calculateStatistics = useCallback((values: number[]) => {
    postMessage({
      type: 'CALCULATE_STATISTICS',
      data: { values }
    });
  }, [postMessage]);
  
  const analyzePerformance = useCallback((
    userAnswers: any[],
    populationData: any
  ) => {
    postMessage({
      type: 'ANALYZE_PERFORMANCE',
      data: { userAnswers, populationData }
    });
  }, [postMessage]);
  
  return {
    calculateZScore,
    calculateBatchZScore,
    calculatePercentile,
    calculateStatistics,
    analyzePerformance,
    results,
    isProcessing,
    status,
    error
  };
}

// Specialized hook for analytics worker
interface AnalyticsWorkerResult {
  type: string;
  data: any;
}

export function useAnalyticsWorker() {
  const [results, setResults] = useState<Record<string, any>>({});
  
  const { postMessage, status, error, isProcessing } = useWorker<AnalyticsWorkerResult>(
    '../workers/analytics.worker.ts',
    {
      onMessage: (message) => {
        if (message.type && message.data) {
          setResults(prev => ({
            ...prev,
            [message.type]: message.data
          }));
        }
      }
    }
  );
  
  const processBattleData = useCallback((battles: any[]) => {
    postMessage({
      type: 'PROCESS_BATTLE_DATA',
      data: { battles }
    });
  }, [postMessage]);
  
  const processUserProgress = useCallback((progressHistory: any[]) => {
    postMessage({
      type: 'PROCESS_USER_PROGRESS',
      data: { progressHistory }
    });
  }, [postMessage]);
  
  const generateInsights = useCallback((
    userStats: any,
    compareWithPopulation = false
  ) => {
    postMessage({
      type: 'GENERATE_INSIGHTS',
      data: { userStats, compareWithPopulation }
    });
  }, [postMessage]);
  
  const aggregateMetrics = useCallback((
    events: any[],
    period: 'daily' | 'weekly' | 'monthly' = 'daily'
  ) => {
    postMessage({
      type: 'AGGREGATE_METRICS',
      data: { events, period }
    });
  }, [postMessage]);
  
  return {
    processBattleData,
    processUserProgress,
    generateInsights,
    aggregateMetrics,
    results,
    isProcessing,
    status,
    error
  };
}