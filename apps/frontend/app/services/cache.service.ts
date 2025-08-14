interface CacheItem {
  data: any;
  timestamp: number;
  ttl: number;
}

class CacheService {
  private prefix = 'icfes_cache_';

  set(key: string, data: any, ttlMinutes = 60) {
    const item: CacheItem = {
      data,
      timestamp: Date.now(),
      ttl: ttlMinutes * 60 * 1000
    };
    
    try {
      localStorage.setItem(this.prefix + key, JSON.stringify(item));
    } catch (error) {
      console.warn('Cache storage failed:', error);
    }
  }

  get<T>(key: string): T | null {
    try {
      const stored = localStorage.getItem(this.prefix + key);
      if (!stored) return null;

      const item: CacheItem = JSON.parse(stored);
      
      // Check if expired
      if (Date.now() - item.timestamp > item.ttl) {
        this.delete(key);
        return null;
      }

      return item.data as T;
    } catch (error) {
      console.warn('Cache retrieval failed:', error);
      return null;
    }
  }

  delete(key: string) {
    try {
      localStorage.removeItem(this.prefix + key);
    } catch (error) {
      console.warn('Cache deletion failed:', error);
    }
  }

  clear() {
    try {
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith(this.prefix)) {
          localStorage.removeItem(key);
        }
      });
    } catch (error) {
      console.warn('Cache clear failed:', error);
    }
  }

  // Specialized methods for common data
  cacheUserStats(stats: any) {
    this.set('user_stats', stats, 30); // 30 min TTL
  }

  getUserStats() {
    return this.get('user_stats');
  }

  cacheLeaderboard(type: string, data: any) {
    this.set(`leaderboard_${type}`, data, 10); // 10 min TTL
  }

  getLeaderboard(type: string) {
    return this.get(`leaderboard_${type}`);
  }

  cacheSubjects(subjects: any[]) {
    this.set('subjects', subjects, 120); // 2 hour TTL
  }

  getSubjects() {
    return this.get('subjects');
  }
}

export const cacheService = new CacheService();