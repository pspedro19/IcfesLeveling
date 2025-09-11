'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  staleTime?: number; // Time until data is considered stale
  refreshOnFocus?: boolean;
  refreshOnReconnect?: boolean;
}

interface CacheState<T> {
  data: T | null;
  isLoading: boolean;
  isStale: boolean;
  error: Error | null;
  lastUpdated: number | null;
}

const DEFAULT_OPTIONS: Required<CacheOptions> = {
  ttl: 5 * 60 * 1000, // 5 minutes
  staleTime: 30 * 1000, // 30 seconds
  refreshOnFocus: true,
  refreshOnReconnect: true
};

class CacheManager {
  private cache = new Map<string, CacheEntry<any>>();
  private subscribers = new Map<string, Set<(data: any) => void>>();
  private pendingRequests = new Map<string, Promise<any>>();

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now > entry.timestamp + entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  set<T>(key: string, data: T, ttl: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });

    // Notify subscribers
    const subs = this.subscribers.get(key);
    if (subs) {
      subs.forEach(callback => callback(data));
    }
  }

  delete(key: string): void {
    this.cache.delete(key);
    this.pendingRequests.delete(key);
  }

  isStale(key: string, staleTime: number): boolean {
    const entry = this.cache.get(key);
    if (!entry) return true;

    const now = Date.now();
    return now > entry.timestamp + staleTime;
  }

  subscribe<T>(key: string, callback: (data: T) => void): () => void {
    if (!this.subscribers.has(key)) {
      this.subscribers.set(key, new Set());
    }
    
    const subs = this.subscribers.get(key)!;
    subs.add(callback);

    // Return unsubscribe function
    return () => {
      subs.delete(callback);
      if (subs.size === 0) {
        this.subscribers.delete(key);
      }
    };
  }

  async fetchWithDeduplication<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number
  ): Promise<T> {
    // Check if there's already a pending request for this key
    const pending = this.pendingRequests.get(key);
    if (pending) {
      return pending;
    }

    // Create new request
    const request = fetcher().then(data => {
      this.set(key, data, ttl);
      this.pendingRequests.delete(key);
      return data;
    }).catch(error => {
      this.pendingRequests.delete(key);
      throw error;
    });

    this.pendingRequests.set(key, request);
    return request;
  }

  clear(): void {
    this.cache.clear();
    this.subscribers.clear();
    this.pendingRequests.clear();
  }

  getStats() {
    return {
      cacheSize: this.cache.size,
      subscribersCount: Array.from(this.subscribers.values()).reduce(
        (total, subs) => total + subs.size, 0
      ),
      pendingRequests: this.pendingRequests.size
    };
  }
}

// Global cache manager instance
const cacheManager = new CacheManager();

export const useCache = <T>(
  key: string,
  fetcher: () => Promise<T>,
  options: CacheOptions = {}
) => {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  const [state, setState] = useState<CacheState<T>>({
    data: null,
    isLoading: false,
    isStale: false,
    error: null,
    lastUpdated: null
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const fetcherRef = useRef(fetcher);
  
  // Update fetcher ref when it changes
  useEffect(() => {
    fetcherRef.current = fetcher;
  }, [fetcher]);

  const fetchData = useCallback(async (force = false) => {
    // Cancel any pending request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Check cache first (unless force refresh)
    if (!force) {
      const cachedData = cacheManager.get<T>(key);
      if (cachedData !== null) {
        setState(prev => ({
          ...prev,
          data: cachedData,
          isLoading: false,
          error: null,
          isStale: cacheManager.isStale(key, opts.staleTime),
          lastUpdated: Date.now()
        }));
        return cachedData;
      }
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      abortControllerRef.current = new AbortController();
      
      const data = await cacheManager.fetchWithDeduplication(
        key,
        fetcherRef.current,
        opts.ttl
      );

      setState(prev => ({
        ...prev,
        data,
        isLoading: false,
        error: null,
        isStale: false,
        lastUpdated: Date.now()
      }));

      return data;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return; // Request was cancelled
      }

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error as Error
      }));
      
      throw error;
    }
  }, [key, opts.ttl, opts.staleTime]);

  const refetch = useCallback(() => fetchData(true), [fetchData]);

  const invalidate = useCallback(() => {
    cacheManager.delete(key);
    setState(prev => ({
      ...prev,
      data: null,
      isStale: true,
      lastUpdated: null
    }));
  }, [key]);

  // Initial fetch and cache subscription
  useEffect(() => {
    // Check cache on mount
    const cachedData = cacheManager.get<T>(key);
    if (cachedData !== null) {
      setState(prev => ({
        ...prev,
        data: cachedData,
        isStale: cacheManager.isStale(key, opts.staleTime),
        lastUpdated: Date.now()
      }));
    } else {
      fetchData();
    }

    // Subscribe to cache updates
    const unsubscribe = cacheManager.subscribe<T>(key, (data) => {
      setState(prev => ({
        ...prev,
        data,
        isStale: false,
        lastUpdated: Date.now()
      }));
    });

    return unsubscribe;
  }, [key, fetchData, opts.staleTime]);

  // Refresh on window focus
  useEffect(() => {
    if (!opts.refreshOnFocus) return;

    const handleFocus = () => {
      if (cacheManager.isStale(key, opts.staleTime)) {
        fetchData();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [key, fetchData, opts.refreshOnFocus, opts.staleTime]);

  // Refresh on network reconnect
  useEffect(() => {
    if (!opts.refreshOnReconnect) return;

    const handleOnline = () => {
      if (cacheManager.isStale(key, opts.staleTime)) {
        fetchData();
      }
    };

    window.addEventListener('online', handleOnline);
    return () => window.removeEventListener('online', handleOnline);
  }, [key, fetchData, opts.refreshOnReconnect, opts.staleTime]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    ...state,
    refetch,
    invalidate,
    fetchData
  };
};

// Hook for managing multiple cache entries
export const useCacheQuery = <T>(
  queries: Array<{
    key: string;
    fetcher: () => Promise<T>;
    options?: CacheOptions;
  }>
) => {
  const results = queries.map(query => 
    useCache(query.key, query.fetcher, query.options)
  );

  const isLoading = results.some(result => result.isLoading);
  const hasError = results.some(result => result.error !== null);
  const isStale = results.some(result => result.isStale);

  const refetchAll = useCallback(() => {
    return Promise.all(results.map(result => result.refetch()));
  }, [results]);

  const invalidateAll = useCallback(() => {
    results.forEach(result => result.invalidate());
  }, [results]);

  return {
    results,
    isLoading,
    hasError,
    isStale,
    refetchAll,
    invalidateAll
  };
};

// Hook for cache statistics
export const useCacheStats = () => {
  const [stats, setStats] = useState(cacheManager.getStats());

  useEffect(() => {
    const interval = setInterval(() => {
      setStats(cacheManager.getStats());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return stats;
};

// Utility functions
export const clearCache = () => cacheManager.clear();

export const invalidateCache = (key: string) => cacheManager.delete(key);

export const getCacheData = <T>(key: string): T | null => cacheManager.get<T>(key);

export const setCacheData = <T>(key: string, data: T, ttl = 5 * 60 * 1000) => 
  cacheManager.set(key, data, ttl);