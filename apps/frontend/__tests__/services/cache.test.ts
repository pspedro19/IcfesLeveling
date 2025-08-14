import { cacheService } from '../../app/services/cache.service';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock as any;

describe('CacheService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(Date, 'now').mockReturnValue(1000000); // Fixed timestamp
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('set and get', () => {
    it('should store and retrieve data', () => {
      const testData = { id: 1, name: 'test' };
      
      localStorageMock.setItem.mockImplementation(() => {});
      localStorageMock.getItem.mockReturnValue(JSON.stringify({
        data: testData,
        timestamp: 1000000,
        ttl: 60000
      }));

      cacheService.set('test-key', testData, 1);
      const retrieved = cacheService.get('test-key');

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'icfes_cache_test-key',
        expect.stringContaining('"data":{"id":1,"name":"test"}')
      );
      expect(retrieved).toEqual(testData);
    });

    it('should return null for non-existent keys', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const result = cacheService.get('non-existent');

      expect(result).toBeNull();
    });

    it('should return null for expired data', () => {
      localStorageMock.getItem.mockReturnValue(JSON.stringify({
        data: { test: 'data' },
        timestamp: 1000000 - 120000, // 2 minutes ago
        ttl: 60000 // 1 minute TTL
      }));
      localStorageMock.removeItem.mockImplementation(() => {});

      const result = cacheService.get('expired-key');

      expect(result).toBeNull();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('icfes_cache_expired-key');
    });

    it('should handle JSON parse errors gracefully', () => {
      localStorageMock.getItem.mockReturnValue('invalid-json');

      const result = cacheService.get('invalid-key');

      expect(result).toBeNull();
    });

    it('should handle localStorage errors gracefully', () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage quota exceeded');
      });

      // Should not throw
      expect(() => {
        cacheService.set('test-key', { data: 'test' });
      }).not.toThrow();
    });
  });

  describe('delete', () => {
    it('should remove item from storage', () => {
      localStorageMock.removeItem.mockImplementation(() => {});

      cacheService.delete('test-key');

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('icfes_cache_test-key');
    });

    it('should handle errors gracefully', () => {
      localStorageMock.removeItem.mockImplementation(() => {
        throw new Error('Storage error');
      });

      expect(() => {
        cacheService.delete('test-key');
      }).not.toThrow();
    });
  });

  describe('clear', () => {
    it('should clear all cache entries', () => {
      const mockKeys = [
        'icfes_cache_key1',
        'icfes_cache_key2',
        'other_key',
        'icfes_cache_key3'
      ];

      Object.defineProperty(localStorage, 'keys', {
        value: jest.fn().mockReturnValue(mockKeys),
        configurable: true
      });

      // Mock Object.keys for localStorage
      Object.keys = jest.fn().mockReturnValue(mockKeys);

      localStorageMock.removeItem.mockImplementation(() => {});

      cacheService.clear();

      expect(localStorageMock.removeItem).toHaveBeenCalledTimes(3); // Only cache keys
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('icfes_cache_key1');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('icfes_cache_key2');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('icfes_cache_key3');
    });
  });

  describe('specialized cache methods', () => {
    beforeEach(() => {
      localStorageMock.setItem.mockImplementation(() => {});
      localStorageMock.getItem.mockImplementation(() => null);
    });

    describe('user stats cache', () => {
      it('should cache and retrieve user stats', () => {
        const stats = { score: 85, level: 5 };

        cacheService.cacheUserStats(stats);
        
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'icfes_cache_user_stats',
          expect.stringContaining('"data":{"score":85,"level":5}')
        );
      });

      it('should retrieve cached user stats', () => {
        localStorageMock.getItem.mockReturnValue(JSON.stringify({
          data: { score: 85, level: 5 },
          timestamp: 1000000,
          ttl: 1800000
        }));

        const stats = cacheService.getUserStats();
        
        expect(stats).toEqual({ score: 85, level: 5 });
      });
    });

    describe('leaderboard cache', () => {
      it('should cache leaderboard data', () => {
        const leaderboard = [{ id: 1, name: 'Player1', score: 100 }];

        cacheService.cacheLeaderboard('global', leaderboard);

        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'icfes_cache_leaderboard_global',
          expect.stringContaining('"data":[{"id":1,"name":"Player1","score":100}]')
        );
      });

      it('should retrieve cached leaderboard', () => {
        const leaderboard = [{ id: 1, name: 'Player1', score: 100 }];
        
        localStorageMock.getItem.mockReturnValue(JSON.stringify({
          data: leaderboard,
          timestamp: 1000000,
          ttl: 600000
        }));

        const result = cacheService.getLeaderboard('global');
        
        expect(result).toEqual(leaderboard);
      });
    });

    describe('subjects cache', () => {
      it('should cache subjects data', () => {
        const subjects = [{ id: 1, name: 'Mathematics' }, { id: 2, name: 'Physics' }];

        cacheService.cacheSubjects(subjects);

        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'icfes_cache_subjects',
          expect.stringContaining('"data":[{"id":1,"name":"Mathematics"}')
        );
      });

      it('should retrieve cached subjects', () => {
        const subjects = [{ id: 1, name: 'Mathematics' }];
        
        localStorageMock.getItem.mockReturnValue(JSON.stringify({
          data: subjects,
          timestamp: 1000000,
          ttl: 7200000
        }));

        const result = cacheService.getSubjects();
        
        expect(result).toEqual(subjects);
      });
    });
  });

  describe('TTL handling', () => {
    it('should use default TTL when not specified', () => {
      cacheService.set('test-key', { data: 'test' });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'icfes_cache_test-key',
        expect.stringContaining('"ttl":3600000') // 1 hour in milliseconds
      );
    });

    it('should use custom TTL when specified', () => {
      cacheService.set('test-key', { data: 'test' }, 30); // 30 minutes

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'icfes_cache_test-key',
        expect.stringContaining('"ttl":1800000') // 30 minutes in milliseconds
      );
    });
  });
});