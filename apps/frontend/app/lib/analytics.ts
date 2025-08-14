// import ReactGA from 'react-ga4'; // Temporalmente comentado para desarrollo

// Mock ReactGA para desarrollo
const ReactGA = {
  initialize: () => {},
  send: () => {},
  event: () => {},
  set: () => {},
  gtag: () => {}
};

// Analytics events types
export interface AnalyticsEvent {
  category: string;
  action: string;
  label?: string;
  value?: number;
  nonInteraction?: boolean;
}

// User properties for analytics
export interface UserProperties {
  userId?: string;
  userLevel?: number;
  userRank?: string;
  isPremium?: boolean;
  heroClass?: string;
}

class Analytics {
  private static instance: Analytics;
  private initialized = false;
  
  private constructor() {}
  
  static getInstance(): Analytics {
    if (!Analytics.instance) {
      Analytics.instance = new Analytics();
    }
    return Analytics.instance;
  }
  
  initialize(measurementId: string | undefined) {
    if (!measurementId || this.initialized) return;
    
    try {
      ReactGA.initialize(measurementId, {
        gaOptions: {
          anonymizeIp: true,
          cookieFlags: 'SameSite=None;Secure',
        },
        gtagOptions: {
          send_page_view: false,
        },
      });
      
      this.initialized = true;
      console.log('Google Analytics initialized');
    } catch (error) {
      console.error('Failed to initialize Google Analytics:', error);
    }
  }
  
  // Track page views
  trackPageView(path?: string, title?: string) {
    if (!this.initialized) return;
    
    try {
      ReactGA.send({
        hitType: 'pageview',
        page: path || window.location.pathname + window.location.search,
        title: title || document.title,
      });
    } catch (error) {
      console.error('Analytics page view error:', error);
    }
  }
  
  // Track custom events
  trackEvent(event: AnalyticsEvent) {
    if (!this.initialized) return;
    
    try {
      ReactGA.event({
        category: event.category,
        action: event.action,
        label: event.label,
        value: event.value,
        nonInteraction: event.nonInteraction,
      });
    } catch (error) {
      console.error('Analytics event error:', error);
    }
  }
  
  // Set user properties
  setUserProperties(properties: UserProperties) {
    if (!this.initialized) return;
    
    try {
      if (properties.userId) {
        ReactGA.set({ user_id: properties.userId });
      }
      
      // Set custom dimensions
      const customDimensions: any = {};
      
      if (properties.userLevel !== undefined) {
        customDimensions.user_level = properties.userLevel;
      }
      if (properties.userRank) {
        customDimensions.user_rank = properties.userRank;
      }
      if (properties.isPremium !== undefined) {
        customDimensions.is_premium = properties.isPremium;
      }
      if (properties.heroClass) {
        customDimensions.hero_class = properties.heroClass;
      }
      
      ReactGA.gtag('set', 'user_properties', customDimensions);
    } catch (error) {
      console.error('Analytics user properties error:', error);
    }
  }
  
  // Track user timing (performance)
  trackTiming(category: string, variable: string, value: number, label?: string) {
    if (!this.initialized) return;
    
    try {
      ReactGA.gtag('event', 'timing_complete', {
        event_category: category,
        name: variable,
        value: Math.round(value),
        event_label: label,
      });
    } catch (error) {
      console.error('Analytics timing error:', error);
    }
  }
  
  // Track exceptions/errors
  trackException(description: string, fatal = false) {
    if (!this.initialized) return;
    
    try {
      ReactGA.gtag('event', 'exception', {
        description,
        fatal,
      });
    } catch (error) {
      console.error('Analytics exception error:', error);
    }
  }
  
  // E-commerce tracking for premium purchases
  trackPurchase(transactionData: {
    transactionId: string;
    value: number;
    currency: string;
    items: Array<{
      itemId: string;
      itemName: string;
      itemCategory: string;
      price: number;
      quantity: number;
    }>;
  }) {
    if (!this.initialized) return;
    
    try {
      ReactGA.gtag('event', 'purchase', {
        transaction_id: transactionData.transactionId,
        value: transactionData.value,
        currency: transactionData.currency,
        items: transactionData.items.map(item => ({
          item_id: item.itemId,
          item_name: item.itemName,
          item_category: item.itemCategory,
          price: item.price,
          quantity: item.quantity,
        })),
      });
    } catch (error) {
      console.error('Analytics purchase error:', error);
    }
  }
  
  // Game-specific events
  trackGameEvent(eventType: string, data: any) {
    const gameEvents: Record<string, AnalyticsEvent> = {
      // Authentication
      login: { category: 'Authentication', action: 'Login', label: data.method },
      logout: { category: 'Authentication', action: 'Logout' },
      register: { category: 'Authentication', action: 'Register', label: data.method },
      guest_mode: { category: 'Authentication', action: 'Guest Mode' },
      guest_convert: { category: 'Authentication', action: 'Guest Convert', value: data.score },
      
      // Gameplay
      battle_start: { category: 'Gameplay', action: 'Battle Start', label: data.subject },
      battle_complete: { category: 'Gameplay', action: 'Battle Complete', value: data.score },
      quest_complete: { category: 'Gameplay', action: 'Quest Complete', label: data.questId },
      level_up: { category: 'Gameplay', action: 'Level Up', value: data.newLevel },
      achievement_unlock: { category: 'Gameplay', action: 'Achievement Unlock', label: data.achievementId },
      
      // Social
      guild_join: { category: 'Social', action: 'Guild Join', label: data.guildId },
      guild_chat: { category: 'Social', action: 'Guild Chat' },
      raid_participate: { category: 'Social', action: 'Raid Participate' },
      
      // Learning
      video_watch: { category: 'Learning', action: 'Video Watch', label: data.videoId, value: data.duration },
      quiz_complete: { category: 'Learning', action: 'Quiz Complete', value: data.score },
      study_plan_start: { category: 'Learning', action: 'Study Plan Start', label: data.subject },
      
      // Premium
      premium_view: { category: 'Premium', action: 'View Premium' },
      premium_purchase: { category: 'Premium', action: 'Purchase', label: data.plan, value: data.price },
      
      // UI/UX
      tutorial_complete: { category: 'UX', action: 'Tutorial Complete' },
      mode_toggle: { category: 'UX', action: 'Mode Toggle', label: data.mode },
      theme_change: { category: 'UX', action: 'Theme Change', label: data.theme },
    };
    
    const event = gameEvents[eventType];
    if (event) {
      this.trackEvent(event);
    }
  }
}

// Export singleton instance
export const analytics = Analytics.getInstance();

// Helper functions for common events
export const trackPageView = (path?: string, title?: string) => {
  analytics.trackPageView(path, title);
};

export const trackEvent = (category: string, action: string, label?: string, value?: number) => {
  analytics.trackEvent({ category, action, label, value });
};

export const trackGameEvent = (eventType: string, data: any = {}) => {
  analytics.trackGameEvent(eventType, data);
};

export const setUserProperties = (properties: UserProperties) => {
  analytics.setUserProperties(properties);
};