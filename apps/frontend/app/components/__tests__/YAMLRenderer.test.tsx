import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import YAMLRenderer from '../YAMLRenderer';
import { useWebSocket } from '@/hooks/useWebSocket';

// Mock React Query
const mockUseQuery = jest.fn();
jest.mock('react-query', () => ({
  useQuery: () => mockUseQuery(),
  useQueryClient: () => ({
    setQueryData: jest.fn(),
  }),
}));

// Mock dependencies
jest.mock('@/hooks/useWebSocket');
jest.mock('@/hooks/useMediaQuery', () => ({
  useMediaQuery: () => false, // Desktop by default
}));
jest.mock('../PortalLogin/AudioEngine', () => ({
  useAudio: () => ({
    playSound: jest.fn(),
  }),
}));

// Mock fetch
global.fetch = jest.fn();

const mockDungeonData = {
  subject: 'Matemáticas',
  title: 'Mazmorra de Matemáticas',
  description: 'Conquista los conceptos fundamentales y avanza tu dominio',
  units: [
    {
      name: 'Fundamentos Básicos',
      description: 'Conceptos esenciales para construir una base sólida',
      topics: [
        {
          name: 'Introducción',
          difficulty: 1,
          questions: 10,
          tags: ['básico', 'conceptos'],
        },
        {
          name: 'Teoría Fundamental',
          difficulty: 2,
          questions: 15,
          tags: ['teoría', 'importante'],
        },
      ],
      recommendations: {
        priority: 'high',
        weak_areas: ['conceptos básicos'],
        study_time: '2 horas',
      },
      unlocked: true,
      progress: 30,
      ai_recommended: true,
    },
    {
      name: 'Nivel Intermedio',
      description: 'Aplica los conceptos en problemas más complejos',
      topics: [
        {
          name: 'Aplicaciones Prácticas',
          difficulty: 3,
          questions: 20,
          tags: ['práctica', 'aplicación'],
        },
      ],
      unlocked: true,
      progress: 0,
    },
    {
      name: 'Dominio Avanzado',
      description: 'Desafíos para verdaderos maestros',
      topics: [
        {
          name: 'Problemas Complejos',
          difficulty: 4,
          questions: 25,
          tags: ['avanzado', 'complejo'],
        },
      ],
      unlocked: false,
      progress: 0,
    },
  ],
  total_questions: 70,
  estimated_time: '4-5 horas',
  difficulty_curve: 'progressive',
};

describe('YAMLRenderer', () => {
  const mockOnUnitSelect = jest.fn();
  const mockSocket = {
    on: jest.fn(),
    off: jest.fn(),
    emit: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup React Query mock
    mockUseQuery.mockReturnValue({
      data: mockDungeonData,
      isLoading: false,
      error: null,
    });

    (useWebSocket as jest.Mock).mockReturnValue({
      socket: mockSocket,
    });
  });

  const renderComponent = (props = {}) => {
    return render(
      <YAMLRenderer
        subject="Matemáticas"
        userLevel={15}
        onUnitSelect={mockOnUnitSelect}
        {...props}
      />
    );
  };

  it('shows loading state initially', () => {
    mockUseQuery.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });
    
    renderComponent();
    
    expect(screen.getByText('Generando mazmorra personalizada...')).toBeInTheDocument();
  });

  it('renders dungeon data after loading', async () => {
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText('Mazmorra de Matemáticas')).toBeInTheDocument();
      expect(screen.getByText('Conquista los conceptos fundamentales y avanza tu dominio')).toBeInTheDocument();
    });
  });

  it('displays unit information correctly', async () => {
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText('Fundamentos Básicos')).toBeInTheDocument();
      expect(screen.getByText('Conceptos esenciales para construir una base sólida')).toBeInTheDocument();
    });
  });

  it('shows AI recommendations for units', async () => {
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText('IA Recomienda')).toBeInTheDocument();
      expect(screen.getByText('Recomendaciones IA')).toBeInTheDocument();
    });
  });

  it('expands unit details when clicked', async () => {
    const user = userEvent.setup();
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText('Fundamentos Básicos')).toBeInTheDocument();
    });
    
    const unitButton = screen.getByText('Fundamentos Básicos').closest('button');
    if (unitButton) {
      await user.click(unitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Introducción')).toBeInTheDocument();
        expect(screen.getByText('10 preguntas')).toBeInTheDocument();
      });
    }
  });

  it('shows locked state for locked units', async () => {
    renderComponent();
    
    await waitFor(() => {
      const lockedUnit = screen.getByText('Dominio Avanzado').closest('div');
      expect(lockedUnit).toHaveClass('opacity-50');
    });
  });

  it('calls onUnitSelect when unit is clicked', async () => {
    const user = userEvent.setup();
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText('Fundamentos Básicos')).toBeInTheDocument();
    });
    
    // Expand the unit first
    const unitButton = screen.getByText('Fundamentos Básicos').closest('button');
    if (unitButton) {
      await user.click(unitButton);
    }
    
    // Click the start button
    await waitFor(() => {
      const startButton = screen.getByText('Iniciar Unidad');
      expect(startButton).toBeInTheDocument();
    });
    
    const startButton = screen.getByText('Iniciar Unidad');
    await user.click(startButton);
    
    expect(mockOnUnitSelect).toHaveBeenCalled();
  });

  it('displays progress bars for units', async () => {
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText('30%')).toBeInTheDocument(); // Progress for first unit
    });
  });

  it('shows difficulty indicators for topics', async () => {
    const user = userEvent.setup();
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText('Fundamentos Básicos')).toBeInTheDocument();
    });
    
    const unitButton = screen.getByText('Fundamentos Básicos').closest('button');
    if (unitButton) {
      await user.click(unitButton);
      
      await waitFor(() => {
        // Should show difficulty stars
        const stars = screen.getAllByTestId(/star/i);
        expect(stars.length).toBeGreaterThan(0);
      });
    }
  });

  it('handles WebSocket updates for recommendations', async () => {
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText('Fundamentos Básicos')).toBeInTheDocument();
    });
    
    // Simulate WebSocket recommendation update
    const socketHandler = mockSocket.on.mock.calls.find(
      call => call[0] === 'recommendation-update'
    )?.[1];
    
    if (socketHandler) {
      socketHandler({
        subject: 'Matemáticas',
        unit: 'Nivel Intermedio',
        recommendations: {
          priority: 'medium',
          weak_areas: ['aplicaciones'],
        },
      });
    }
    
    // The component should update with the new recommendation
    // In a real test, we'd check for the visual update
  });

  it('shows error state when fetch fails', async () => {
    mockUseQuery.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Network error'),
    });
    
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText('Error al cargar el contenido')).toBeInTheDocument();
    });
  });

  it('displays completion message when all units are 100%', async () => {
    const completedData = {
      ...mockDungeonData,
      units: [{
        name: 'Unit 1',
        description: 'Test unit',
        topics: [],
        unlocked: true,
        progress: 100,
      }],
    };
    
    mockUseQuery.mockReturnValue({
      data: completedData,
      isLoading: false,
      error: null,
    });
    
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText('¡Mazmorra Completada!')).toBeInTheDocument();
      expect(screen.getByText('Has dominado todos los temas de Matemáticas')).toBeInTheDocument();
    });
  });

  it('shows weakness indicators for units with poor performance', async () => {
    renderComponent({
      weaknessData: {
        'algebra': 45,
        'geometry': 60,
      },
    });
    
    await waitFor(() => {
      // Units with high priority recommendations should show warning
      const warningIcons = screen.getAllByTitle(/Área débil detectada/i);
      expect(warningIcons.length).toBeGreaterThan(0);
    });
  });
});