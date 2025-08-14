interface AnalyticsEvent {
  event: string;
  properties?: Record<string, any>;
  timestamp?: number;
  userId?: string;
}

class AnalyticsService {
  private queue: AnalyticsEvent[] = [];
  private isEnabled = true;
  private flushInterval: NodeJS.Timeout | null = null;
  private readonly API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/api/v1').replace(/\/$/, '');

  constructor() {
    // Start periodic flush
    this.flushInterval = setInterval(() => {
      this.flush();
    }, 5000); // Flush every 5 seconds
  }

  private getUserId(): string | undefined {
    // Try to get user ID from localStorage or session
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    if (token) {
      try {
        // Decode JWT token to get user ID (basic implementation)
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.sub || payload.user_id;
      } catch (error) {
        console.warn('Failed to decode token for analytics:', error);
      }
    }
    return undefined;
  }

  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  // Public tracking methods
  trackPageView(page: string, properties?: Record<string, any>) {
    this.track('page_view', {
      page,
      ...properties
    });
  }

  trackEvent(event: string, properties?: Record<string, any>) {
    this.track(event, properties);
  }

  trackError(error: string, context?: string, stack?: string) {
    this.track('error_occurred', {
      error,
      context,
      stack
    });
  }

  trackBattleComplete(battleData: any) {
    this.track('battle_complete', battleData);
  }

  trackDiagnosticComplete(diagnosticData: any) {
    this.track('diagnostic_complete', diagnosticData);
  }

  // Core tracking method
  private track(event: string, properties?: Record<string, any>) {
    if (!this.isEnabled) return;

    const analyticsEvent: AnalyticsEvent = {
      event,
      properties: {
        ...properties,
        user_agent: navigator.userAgent,
        url: window.location.href,
        referrer: document.referrer
      },
      timestamp: Date.now(),
      userId: this.getUserId()
    };

    this.queue.push(analyticsEvent);

    // Immediate flush for critical events
    const criticalEvents = ['error_occurred', 'diagnostic_complete', 'battle_complete'];
    if (criticalEvents.includes(event)) {
      this.flush();
    }
  }

  private async flush() {
    if (this.queue.length === 0) return;

    const events = [...this.queue];
    this.queue = [];

    try {
      const response = await fetch(`${this.API_BASE}/analytics/events`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ events })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      console.log(`Analytics: ${events.length} events sent successfully`);
    } catch (error) {
      console.warn('Analytics/events failed (ignored):', error);
      // No re-queue events - just drop them to avoid blocking the UI
    }
  }

  destroy() {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
    }
    this.flush(); // Final flush
  }
}

// Export singleton instance
export const analyticsService = new AnalyticsService();

// React hook for easier usage
export const useAnalytics = () => {
  return {
    trackPageView: analyticsService.trackPageView.bind(analyticsService),
    trackEvent: analyticsService.trackEvent.bind(analyticsService),
    trackError: analyticsService.trackError.bind(analyticsService),
    trackBattleComplete: analyticsService.trackBattleComplete.bind(analyticsService),
    trackDiagnosticComplete: analyticsService.trackDiagnosticComplete.bind(analyticsService),
    trackDiagnosticStart: (subject: string) => analyticsService.trackEvent('diagnostic_start', { subject }),
    trackVideoWatch: (videoUrl: string, watchTime: number, completed: boolean) => 
      analyticsService.trackEvent('video_watch', { video_url: videoUrl, watch_time: watchTime, completed }),
    trackButtonClick: (buttonName: string, context?: string) => 
      analyticsService.trackEvent('button_click', { button_name: buttonName, context })
  };
};