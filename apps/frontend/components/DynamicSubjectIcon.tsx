'use client';

import React, { useEffect, useState } from 'react';
import { BookOpen, Calculator, Globe, Microscope, Users, Languages } from 'lucide-react';

interface SubjectAssets {
  icon_url?: string;
  color_primary?: string;
  color_secondary?: string;
}

interface DynamicSubjectIconProps {
  subjectId?: string;
  subjectName?: string;
  size?: number;
  className?: string;
}

// Fallback icon mapping for when dynamic assets aren't available
const FALLBACK_ICONS: Record<string, any> = {
  'matemáticas': Calculator,
  'mathematics': Calculator,
  'math': Calculator,
  'lectura crítica': BookOpen,
  'lenguaje': BookOpen,
  'language': BookOpen,
  'reading': BookOpen,
  'ciencias naturales': Microscope,
  'natural sciences': Microscope,
  'science': Microscope,
  'ciencias': Microscope,
  'ciencias sociales': Users,
  'social sciences': Users,
  'sociales': Users,
  'history': Users,
  'inglés': Languages,
  'english': Languages,
  'foreign language': Languages,
  'default': Globe
};

export default function DynamicSubjectIcon({ 
  subjectId, 
  subjectName, 
  size = 24, 
  className = '' 
}: DynamicSubjectIconProps) {
  const [assets, setAssets] = useState<SubjectAssets | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (subjectId) {
      loadSubjectAssets(subjectId);
    }
  }, [subjectId]);

  const loadSubjectAssets = async (id: string) => {
    setLoading(true);
    setError(false);
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const response = await fetch(`${API_URL}/api/v1/subjects/${id}/assets`);
      if (response.ok) {
        const assetData = await response.json();
        setAssets(assetData);
      } else {
        setError(true);
      }
    } catch (err) {
      console.warn('Failed to load dynamic subject assets:', err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const getFallbackIcon = () => {
    if (!subjectName) return FALLBACK_ICONS.default || Globe;
    
    const normalizedName = subjectName.toLowerCase().trim();
    
    // Try exact match first
    if (normalizedName in FALLBACK_ICONS && FALLBACK_ICONS[normalizedName]) {
      return FALLBACK_ICONS[normalizedName];
    }
    
    // Try partial matches
    for (const [key, icon] of Object.entries(FALLBACK_ICONS)) {
      if (key !== 'default' && (normalizedName.includes(key) || key.includes(normalizedName))) {
        return icon;
      }
    }
    
    return FALLBACK_ICONS.default || Globe;
  };

  // If we have dynamic assets and an icon URL, use it
  if (assets?.icon_url && !error) {
    return (
      <div 
        className={`flex items-center justify-center ${className}`}
        style={{ 
          width: size, 
          height: size,
          color: assets.color_primary || 'currentColor'
        }}
      >
        <img
          src={assets.icon_url}
          alt={subjectName || 'Subject'}
          width={size}
          height={size}
          className="object-contain"
          onError={() => setError(true)}
        />
      </div>
    );
  }

  // Fallback to Lucide icons
  const FallbackIcon = getFallbackIcon();
  
  return (
    <div 
      className={`flex items-center justify-center ${className}`}
      style={{ 
        width: size, 
        height: size,
        color: assets?.color_primary || 'currentColor'
      }}
    >
      <FallbackIcon size={size * 0.8} />
    </div>
  );
}

// Hook for getting subject assets
export function useSubjectAssets(subjectId?: string) {
  const [assets, setAssets] = useState<SubjectAssets | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (subjectId) {
      loadAssets(subjectId);
    }
  }, [subjectId]);

  const loadAssets = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const response = await fetch(`${API_URL}/api/v1/subjects/${id}/assets`);
      if (response.ok) {
        const data = await response.json();
        setAssets(data);
      } else {
        throw new Error('Failed to load assets');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return { assets, loading, error, refetch: () => subjectId && loadAssets(subjectId) };
}

// Hook for getting all subjects dynamically
export function useDynamicSubjects() {
  const [subjects, setSubjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const response = await fetch(`${API_URL}/api/v1/subjects/dynamic`);
      if (response.ok) {
        const data = await response.json();
        setSubjects(data);
      } else {
        throw new Error('Failed to load subjects');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return { 
    subjects, 
    loading, 
    error, 
    refetch: loadSubjects,
    findSubject: (nameOrId: string) => 
      subjects.find(s => 
        s.id === nameOrId || 
        s.name.toLowerCase() === nameOrId.toLowerCase() ||
        s.aliases.some((alias: string) => alias.toLowerCase() === nameOrId.toLowerCase())
      )
  };
}