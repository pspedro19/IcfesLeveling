/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { HybridStudyPlanUX } from '@/components/StudyPlan/HybridStudyPlanUX';

// Mock Next.js router
const mockPush = jest.fn();
const mockRouter = {
  push: mockPush,
  query: {},
  pathname: '/study-plan-view',
  asPath: '/study-plan-view',
};

jest.mock('next/router', () => ({
  useRouter: () => mockRouter,
}));

// Mock services
jest.mock('@/services/study-plan.service', () => ({
  StudyPlanService: {
    getUserStudyPlans: jest.fn(),
    getStudyPlanProgress: jest.fn(),
    completeTopicInPlan: jest.fn(),
    updateStudyPlan: jest.fn(),
  },
}));

// Mock stores
const mockAuthStore = {
  user: {
    id: 'user-123',
    username: 'testuser',
    display_name: 'Test User',
    rank: 'B',
    level: 5,
    xp: 1250,
  },
  isAuthenticated: true,
};

jest.mock('@/stores/useAuthStore', () => ({
  useAuthStore: () => mockAuthStore,
}));

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
    h2: ({ children, ...props }: any) => <h2 {...props}>{children}</h2>,
    span: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
  useInView: () => true,
}));

const mockStudyPlan = {
  id: 1,
  title: "Plan de Matemáticas - Nivel Intermedio",
  description: "Plan personalizado basado en tu diagnóstico",
  subject_id: 1,
  difficulty_level: 3,
  estimated_weeks: 8,
  status: "active",
  topics: [
    {
      id: 1,
      name: "Álgebra Básica",
      description: "Fundamentos de álgebra",
      status: "completed",
      estimated_hours: 4,
      order_index: 1,
      progress_percentage: 100,
    },
    {
      id: 2,
      name: "Ecuaciones Lineales",
      description: "Resolución de ecuaciones",
      status: "in_progress",
      estimated_hours: 6,
      order_index: 2,
      progress_percentage: 60,
    },
    {
      id: 3,
      name: "Sistemas de Ecuaciones",
      description: "Métodos de resolución",
      status: "pending",
      estimated_hours: 8,
      order_index: 3,
      progress_percentage: 0,
    }
  ],
  progress: {
    completion_percentage: 53,
    completed_topics: 1,
    total_topics: 3,
    current_topic: "Ecuaciones Lineales",
    estimated_completion_date: "2024-03-15"
  }
};

describe('HybridStudyPlanUX Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock API responses
    const { StudyPlanService } = require('@/services/study-plan.service');
    StudyPlanService.getUserStudyPlans.mockResolvedValue([mockStudyPlan]);
    StudyPlanService.getStudyPlanProgress.mockResolvedValue(mockStudyPlan.progress);
  });

  it('renders study plan title and description', async () => {
    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      expect(screen.getByText('Plan de Matemáticas - Nivel Intermedio')).toBeInTheDocument();
      expect(screen.getByText('Plan personalizado basado en tu diagnóstico')).toBeInTheDocument();
    });
  });

  it('displays progress information', async () => {
    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      expect(screen.getByText(/53%/)).toBeInTheDocument();
      expect(screen.getByText(/1 de 3 temas completados/)).toBeInTheDocument();
    });
  });

  it('shows topic list with different statuses', async () => {
    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      expect(screen.getByText('Álgebra Básica')).toBeInTheDocument();
      expect(screen.getByText('Ecuaciones Lineales')).toBeInTheDocument();
      expect(screen.getByText('Sistemas de Ecuaciones')).toBeInTheDocument();
    });

    // Check status indicators
    const completedTopic = screen.getByText('Álgebra Básica').closest('.topic-card');
    expect(completedTopic).toHaveClass('completed');

    const inProgressTopic = screen.getByText('Ecuaciones Lineales').closest('.topic-card');
    expect(inProgressTopic).toHaveClass('in-progress');

    const pendingTopic = screen.getByText('Sistemas de Ecuaciones').closest('.topic-card');
    expect(pendingTopic).toHaveClass('pending');
  });

  it('handles topic click navigation', async () => {
    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      const inProgressTopic = screen.getByText('Ecuaciones Lineales');
      fireEvent.click(inProgressTopic);
    });

    expect(mockPush).toHaveBeenCalledWith('/topics/2');
  });

  it('shows estimated completion date', async () => {
    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      expect(screen.getByText(/marzo 15, 2024/i)).toBeInTheDocument();
    });
  });

  it('displays difficulty level indicators', async () => {
    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      const difficultyIndicator = screen.getByTestId('difficulty-level');
      expect(difficultyIndicator).toBeInTheDocument();
      expect(difficultyIndicator).toHaveTextContent('3');
    });
  });

  it('shows progress bars for topics', async () => {
    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      const progressBars = screen.getAllByRole('progressbar');
      expect(progressBars).toHaveLength(3);
      
      // Check specific progress values
      expect(progressBars[0]).toHaveAttribute('aria-valuenow', '100');
      expect(progressBars[1]).toHaveAttribute('aria-valuenow', '60');
      expect(progressBars[2]).toHaveAttribute('aria-valuenow', '0');
    });
  });

  it('handles topic completion', async () => {
    const { StudyPlanService } = require('@/services/study-plan.service');
    StudyPlanService.completeTopicInPlan.mockResolvedValue({
      success: true,
      xp_gained: 100,
      new_level: 6,
    });

    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      const completeButton = screen.getByRole('button', { name: /completar tema/i });
      fireEvent.click(completeButton);
    });

    await waitFor(() => {
      expect(StudyPlanService.completeTopicInPlan).toHaveBeenCalledWith(1, 2);
    });
  });

  it('displays loading state', () => {
    const { StudyPlanService } = require('@/services/study-plan.service');
    StudyPlanService.getUserStudyPlans.mockReturnValue(new Promise(() => {})); // Never resolves

    render(<HybridStudyPlanUX />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    const { StudyPlanService } = require('@/services/study-plan.service');
    StudyPlanService.getUserStudyPlans.mockRejectedValue(new Error('API Error'));

    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      expect(screen.getByText(/error al cargar/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no study plans', async () => {
    const { StudyPlanService } = require('@/services/study-plan.service');
    StudyPlanService.getUserStudyPlans.mockResolvedValue([]);

    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      expect(screen.getByText(/no tienes planes de estudio/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /crear plan/i })).toBeInTheDocument();
    });
  });
});

describe('StudyPlan Mobile Responsiveness', () => {
  beforeEach(() => {
    const { StudyPlanService } = require('@/services/study-plan.service');
    StudyPlanService.getUserStudyPlans.mockResolvedValue([mockStudyPlan]);
  });

  it('adapts layout for mobile screens', async () => {
    // Mock window.innerWidth
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      const container = screen.getByTestId('study-plan-container');
      expect(container).toHaveClass('mobile-layout');
    });
  });

  it('shows collapsed topic details on mobile', async () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      const expandButton = screen.getAllByRole('button', { name: /expandir/i });
      expect(expandButton.length).toBeGreaterThan(0);
    });
  });
});

describe('StudyPlan Accessibility', () => {
  beforeEach(() => {
    const { StudyPlanService } = require('@/services/study-plan.service');
    StudyPlanService.getUserStudyPlans.mockResolvedValue([mockStudyPlan]);
  });

  it('provides proper ARIA labels', async () => {
    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      const studyPlan = screen.getByRole('main');
      expect(studyPlan).toHaveAttribute('aria-label', 'Plan de estudio');

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-label');
      expect(progressBar).toHaveAttribute('aria-valuenow');
      expect(progressBar).toHaveAttribute('aria-valuemax');
    });
  });

  it('supports keyboard navigation', async () => {
    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      const firstTopic = screen.getByText('Álgebra Básica');
      firstTopic.focus();
      
      fireEvent.keyDown(firstTopic, { key: 'Tab' });
      
      const secondTopic = screen.getByText('Ecuaciones Lineales');
      expect(document.activeElement).toBe(secondTopic);
    });
  });

  it('provides screen reader friendly content', async () => {
    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      const srOnly = screen.getAllByTestId('sr-only');
      expect(srOnly.length).toBeGreaterThan(0);
      
      srOnly.forEach(element => {
        expect(element).toHaveClass('sr-only');
      });
    });
  });
});

describe('StudyPlan Gamification', () => {
  beforeEach(() => {
    const { StudyPlanService } = require('@/services/study-plan.service');
    StudyPlanService.getUserStudyPlans.mockResolvedValue([mockStudyPlan]);
  });

  it('displays XP and level information', async () => {
    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      expect(screen.getByText('1250 XP')).toBeInTheDocument();
      expect(screen.getByText('Nivel 5')).toBeInTheDocument();
      expect(screen.getByText('Rango B')).toBeInTheDocument();
    });
  });

  it('shows achievement badges', async () => {
    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      const achievements = screen.getAllByTestId('achievement-badge');
      expect(achievements.length).toBeGreaterThan(0);
    });
  });

  it('displays topic completion rewards', async () => {
    const { StudyPlanService } = require('@/services/study-plan.service');
    StudyPlanService.completeTopicInPlan.mockResolvedValue({
      success: true,
      xp_gained: 100,
      achievements_unlocked: ['first_topic_completed'],
    });

    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      const completeButton = screen.getByRole('button', { name: /completar tema/i });
      fireEvent.click(completeButton);
    });

    await waitFor(() => {
      expect(screen.getByText('+100 XP')).toBeInTheDocument();
      expect(screen.getByText('¡Logro desbloqueado!')).toBeInTheDocument();
    });
  });
});

describe('StudyPlan Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('integrates with video player', async () => {
    const studyPlanWithVideos = {
      ...mockStudyPlan,
      topics: [
        ...mockStudyPlan.topics,
        {
          id: 4,
          name: "Videos Explicativos",
          videos: [
            {
              id: 'abc123',
              title: 'Introducción al Álgebra',
              url: 'https://youtube.com/watch?v=abc123',
              duration: 600,
            }
          ]
        }
      ]
    };

    const { StudyPlanService } = require('@/services/study-plan.service');
    StudyPlanService.getUserStudyPlans.mockResolvedValue([studyPlanWithVideos]);

    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      expect(screen.getByText('Videos Explicativos')).toBeInTheDocument();
      const playButton = screen.getByRole('button', { name: /reproducir video/i });
      expect(playButton).toBeInTheDocument();
    });
  });

  it('syncs with progress tracking', async () => {
    const { StudyPlanService } = require('@/services/study-plan.service');
    StudyPlanService.getUserStudyPlans.mockResolvedValue([mockStudyPlan]);

    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      expect(StudyPlanService.getStudyPlanProgress).toHaveBeenCalledWith(1);
    });
  });

  it('handles offline mode gracefully', async () => {
    // Mock offline state
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    render(<HybridStudyPlanUX />);
    
    await waitFor(() => {
      expect(screen.getByText(/modo sin conexión/i)).toBeInTheDocument();
    });
  });
});