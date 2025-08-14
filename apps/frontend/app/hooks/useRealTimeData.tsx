import { useState, useEffect } from 'react';

export const useRealTimeData = (endpoint: string) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/v1/${endpoint}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (response.ok) {
          const result = await response.json();
          setData(result);
          setError(null);
        } else {
          throw new Error(`Error ${response.status}`);
        }
      } catch (err) {
        console.error(`Error loading ${endpoint}:`, err);
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [endpoint]);

  return { data, loading, error, refetch: () => loadData() };
};