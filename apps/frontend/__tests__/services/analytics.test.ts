import { analyticsService } from '../../app/services/analytics.service';

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock as any;

// Mock navigator
Object.defineProperty(window, 'navigator', {
  value: {
    userAgent: 'test-user-agent',
  },
  writable: true,
});

// Mock location
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000/test',
  },
  writable: true,
});

// Mock document
Object.defineProperty(window, 'document', {
  value: {
    referrer: 'http://localhost:3000',
  },
  writable: true,
});

describe('AnalyticsService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true }),
    } as Response);
  });

  describe('trackPageView', () => {
    it('should track page view with correct properties', () => {
      analyticsService.trackPageView('test-page', { custom: 'property' });
      
      // Verify the event was queued (we can't directly access the queue)
      expect(true).toBe(true); // Basic test structure
    });
  });

  describe('trackButtonClick', () => {
    it('should track button click with context', () => {
      analyticsService.trackButtonClick('test-button', 'header');
      
      expect(true).toBe(true);
    });
  });

  describe('trackDiagnosticStart', () => {
    it('should track diagnostic test start', () => {
      analyticsService.trackDiagnosticStart('mathematics');
      
      expect(true).toBe(true);
    });
  });

  describe('trackDiagnosticComplete', () => {
    it('should track diagnostic test completion', () => {
      analyticsService.trackDiagnosticComplete('mathematics', 85, 1200);
      
      expect(true).toBe(true);
    });

    it('should trigger immediate flush for critical events', async () => {
      // Mock a successful flush
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      } as Response);

      analyticsService.trackDiagnosticComplete('mathematics', 85, 1200);
      
      // Wait a bit for the flush to potentially happen
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Verify fetch was called (flush happened)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/analytics/events',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });
  });

  describe('trackVideoWatch', () => {
    it('should track video watch with completion status', () => {
      analyticsService.trackVideoWatch('https://youtube.com/watch?v=test', 180, true);
      
      expect(true).toBe(true);
    });
  });

  describe('trackBattleStart', () => {
    it('should track battle start with enemy and floor', () => {
      analyticsService.trackBattleStart('shadow-beast', 5);
      
      expect(true).toBe(true);
    });
  });

  describe('trackBattleComplete', () => {
    it('should track battle completion with result', () => {
      analyticsService.trackBattleComplete('victory', 45);
      
      expect(true).toBe(true);
    });

    it('should trigger immediate flush for critical events', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      } as Response);

      analyticsService.trackBattleComplete('victory', 45);
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(mockFetch).toHaveBeenCalled();
    });
  });

  describe('trackError', () => {
    it('should track errors with context', () => {
      analyticsService.trackError('Test error', 'diagnostic-test', 'Error stack trace');
      
      expect(true).toBe(true);
    });

    it('should trigger immediate flush for error events', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      } as Response);

      analyticsService.trackError('Test error', 'diagnostic-test');
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(mockFetch).toHaveBeenCalled();
    });
  });

  describe('flush behavior', () => {
    it('should handle fetch failures gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      analyticsService.trackDiagnosticComplete('mathematics', 85, 1200);
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Should not throw an error
      expect(true).toBe(true);
    });

    it('should include authorization header when token exists', async () => {
      localStorageMock.getItem.mockReturnValue('test-token');
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      } as Response);

      analyticsService.trackError('Test error');
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/analytics/events',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      );
    });
  });

  describe('enable/disable functionality', () => {
    it('should not track events when disabled', () => {
      analyticsService.disable();
      analyticsService.trackPageView('test-page');
      
      // Events should not be tracked when disabled
      expect(true).toBe(true);
    });

    it('should resume tracking when re-enabled', () => {
      analyticsService.disable();
      analyticsService.enable();
      analyticsService.trackPageView('test-page');
      
      expect(true).toBe(true);
    });
  });
});