/**
 * Production-safe Logger
 * Removes console.logs in production and provides structured logging
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: Date;
  data?: any;
  context?: string;
}

class Logger {
  private static instance: Logger;
  private logs: LogEntry[] = [];
  private maxLogs = 100;
  private isDevelopment = process.env.NODE_ENV === 'development';
  private isDebugEnabled = process.env.NEXT_PUBLIC_DEBUG === 'true';

  private constructor() {}

  public static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  private shouldLog(level: LogLevel): boolean {
    if (this.isDevelopment) return true;
    if (this.isDebugEnabled && level !== 'debug') return true;
    if (level === 'error') return true;
    return false;
  }

  private addToHistory(entry: LogEntry) {
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }
  }

  private formatMessage(level: LogLevel, message: string, context?: string): string {
    const prefix = context ? `[${context}]` : '';
    return `${prefix} ${message}`;
  }

  public debug(message: string, data?: any, context?: string) {
    const entry: LogEntry = {
      level: 'debug',
      message,
      timestamp: new Date(),
      data,
      context
    };

    this.addToHistory(entry);
    
    if (this.shouldLog('debug')) {
      console.log(this.formatMessage('debug', message, context), data || '');
    }
  }

  public info(message: string, data?: any, context?: string) {
    const entry: LogEntry = {
      level: 'info',
      message,
      timestamp: new Date(),
      data,
      context
    };

    this.addToHistory(entry);
    
    if (this.shouldLog('info')) {
      console.info(this.formatMessage('info', message, context), data || '');
    }
  }

  public warn(message: string, data?: any, context?: string) {
    const entry: LogEntry = {
      level: 'warn',
      message,
      timestamp: new Date(),
      data,
      context
    };

    this.addToHistory(entry);
    
    if (this.shouldLog('warn')) {
      console.warn(this.formatMessage('warn', message, context), data || '');
    }
  }

  public error(message: string, error?: any, context?: string) {
    const entry: LogEntry = {
      level: 'error',
      message,
      timestamp: new Date(),
      data: error,
      context
    };

    this.addToHistory(entry);
    
    if (this.shouldLog('error')) {
      console.error(this.formatMessage('error', message, context), error || '');
    }

    // Always send errors to monitoring in production
    if (!this.isDevelopment && typeof window !== 'undefined') {
      this.sendToMonitoring(entry);
    }
  }

  private async sendToMonitoring(entry: LogEntry) {
    try {
      // Send to Sentry or other monitoring service
      if ((window as any).Sentry) {
        (window as any).Sentry.captureMessage(entry.message, entry.level);
      }
    } catch {
      // Silently fail
    }
  }

  public getHistory(): LogEntry[] {
    return [...this.logs];
  }

  public clearHistory() {
    this.logs = [];
  }

  public table(data: any[], context?: string) {
    if (this.shouldLog('debug')) {
      if (context) console.log(`[${context}]`);
      console.table(data);
    }
  }

  public time(label: string) {
    if (this.shouldLog('debug')) {
      console.time(label);
    }
  }

  public timeEnd(label: string) {
    if (this.shouldLog('debug')) {
      console.timeEnd(label);
    }
  }

  public group(label: string) {
    if (this.shouldLog('debug')) {
      console.group(label);
    }
  }

  public groupEnd() {
    if (this.shouldLog('debug')) {
      console.groupEnd();
    }
  }
}

// Export singleton instance
export const logger = Logger.getInstance();

// Override console in production
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
  window.console.log = () => {};
  window.console.debug = () => {};
  window.console.info = () => {};
  window.console.warn = (...args) => logger.warn(args.join(' '));
  window.console.error = (...args) => logger.error(args.join(' '));
}