import { useState, useEffect } from 'react';

export const useProgressSync = () => {
  const [progress, setProgress] = useState(null);
  const [orbs, setOrbs] = useState(0);
  const [rank, setRank] = useState('F');
  const [loading, setLoading] = useState(true);

  const syncProgress = async () => {
    try {
      setLoading(true);
      
      // Cargar progreso personal
      const progressResponse = await fetch('/api/v1/analytics/personal', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (progressResponse.ok) {
        const progressData = await progressResponse.json();
        setProgress(progressData);
        setOrbs(progressData.totalOrbs || orbs);
        
        // Calcular rango basado en progreso real
        const avgProgress = progressData.averageProgress || 0;
        if (avgProgress >= 90) setRank('S');
        else if (avgProgress >= 80) setRank('A');
        else if (avgProgress >= 70) setRank('B');
        else if (avgProgress >= 60) setRank('C');
        else if (avgProgress >= 50) setRank('D');
        else setRank('E');
      }
    } catch (error) {
      console.error('Error syncing progress:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    syncProgress();
  }, []);

  return { 
    progress, 
    orbs, 
    rank, 
    loading, 
    syncProgress 
  };
};