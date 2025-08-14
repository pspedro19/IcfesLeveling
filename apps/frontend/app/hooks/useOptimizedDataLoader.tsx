import { useState, useEffect, useCallback } from 'react';

interface LoaderConfig {
  endpoints: string[];
  dependencies?: any[];
  fallbackData?: any;
}

export const useOptimizedDataLoader = (config: LoaderConfig) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<string[]>([]);

  const loadAllData = useCallback(async () => {
    try {
      setLoading(true);
      setErrors([]);

      const promises = config.endpoints.map(async (endpoint) => {
        try {
          const response = await fetch(`/api/v1/${endpoint}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'Content-Type': 'application/json'
            }
          });

          if (response.ok) {
            return await response.json();
          } else {
            throw new Error(`Failed to load ${endpoint}`);
          }
        } catch (error) {
          console.error(`Error loading ${endpoint}:`, error);
          setErrors(prev => [...prev, `Failed to load ${endpoint}`]);
          return config.fallbackData || null;
        }
      });

      const results = await Promise.allSettled(promises);
      const successfulResults = results.map((result, index) => {
        if (result.status === 'fulfilled') {
          return result.value;
        } else {
          return config.fallbackData || null;
        }
      });

      setData(successfulResults);
    } catch (error) {
      console.error('Error in optimized data loader:', error);
      setErrors(['Failed to load data']);
    } finally {
      setLoading(false);
    }
  }, [config.endpoints, config.fallbackData]);

  useEffect(() => {
    loadAllData();
  }, config.dependencies || []);

  return {
    data,
    loading,
    errors,
    refetch: loadAllData,
    hasErrors: errors.length > 0
  };
};