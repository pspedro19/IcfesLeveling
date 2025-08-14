import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BattleReport from '../BattleReport';
import { useAuthStore } from '@/stores/useAuthStore';
import { useBattleStore } from '@/stores/useBattleStore';

// Mock stores
jest.mock('@/stores/useAuthStore');
jest.mock('@/stores/useBattleStore');

// Mock audio hook
jest.mock('../../PortalLogin/AudioEngine', () => ({
  useAudio: () => ({
    playSound: jest.fn(),
  }),
}));

// Mock API client
jest.mock('@/lib/axios', () => ({
  apiClient: {
    post: jest.fn().mockResolvedValue({ tip: 'Practica más álgebra para mejorar' }),
  },
}));

describe('BattleReport', () => {
  const mockOnClose = jest.fn();
  const mockOnRankUp = jest.fn();
  
  const defaultStats = {
    accuracy: 75,
    totalQuestions: 20,
    correctAnswers: 15,
    incorrectAnswers: 5,
    avgResponseTime: 12.5,
    byTag: {
      'Álgebra': { correct: 8, total: 10, accuracy: 80 },
      'Geometría': { correct: 3, total: 5, accuracy: 60 },
      'Cálculo': { correct: 2, total: 3, accuracy: 67 },
      'Estadística': { correct: 2, total: 2, accuracy: 100 },
    },
    byDifficulty: {
      1: { correct: 5, total: 5, accuracy: 100 },
      2: { correct: 5, total: 6, accuracy: 83 },
      3: { correct: 3, total: 5, accuracy: 60 },
      4: { correct: 2, total: 3, accuracy: 67 },
      5: { correct: 0, total: 1, accuracy: 0 },
    },
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: { id: 'user-123', name: 'TestUser', level: 25 },
    });
    
    (useBattleStore as unknown as jest.Mock).mockReturnValue({
      currentEnemy: { name: 'Shadow Monster' },
    });
  });

  it('renders battle report with correct stats', () => {
    render(
      <BattleReport 
        stats={defaultStats} 
        onClose={mockOnClose}
      />
    );
    
    expect(screen.getByText('Reporte de Batalla')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument(); // accuracy
    expect(screen.getByText('15')).toBeInTheDocument(); // correct answers
    expect(screen.getByText('5')).toBeInTheDocument(); // incorrect answers
    expect(screen.getByText('12.5s')).toBeInTheDocument(); // avg response time
  });

  it('calculates and displays Z-Score correctly', () => {
    render(
      <BattleReport 
        stats={defaultStats} 
        onClose={mockOnClose}
      />
    );
    
    // Z-Score for 75% accuracy with mean 70 and std 15 = (75-70)/15 = 0.33
    expect(screen.getByText('Z-Score: 0.33')).toBeInTheDocument();
  });

  it('shows performance level based on Z-Score', () => {
    render(
      <BattleReport 
        stats={defaultStats} 
        onClose={mockOnClose}
      />
    );
    
    // Z-Score 0.33 should show "Promedio" performance
    expect(screen.getByText('Promedio')).toBeInTheDocument();
  });

  it('identifies and displays weaknesses', async () => {
    render(
      <BattleReport 
        stats={defaultStats} 
        onClose={mockOnClose}
      />
    );
    
    // Geometría with 60% accuracy should be identified as weakness
    await waitFor(() => {
      expect(screen.getByText('Áreas a Mejorar')).toBeInTheDocument();
      expect(screen.getByText(/Geometría/i)).toBeInTheDocument();
    });
  });

  it('shows rank up button when criteria are met', () => {
    const highPerformanceStats = {
      ...defaultStats,
      accuracy: 85,
      byTag: {
        'Álgebra': { correct: 10, total: 10, accuracy: 100 },
        'Geometría': { correct: 5, total: 5, accuracy: 100 },
        'Cálculo': { correct: 3, total: 3, accuracy: 100 },
        'Estadística': { correct: 2, total: 2, accuracy: 100 },
      },
    };
    
    render(
      <BattleReport 
        stats={highPerformanceStats} 
        onClose={mockOnClose}
        onRankUp={mockOnRankUp}
      />
    );
    
    expect(screen.getByText('Listo para Ascender')).toBeInTheDocument();
    expect(screen.getByText('Subir de Rango')).toBeInTheDocument();
  });

  it('shows blocked rank status when criteria not met', () => {
    render(
      <BattleReport 
        stats={defaultStats} 
        onClose={mockOnClose}
        onRankUp={mockOnRankUp}
      />
    );
    
    expect(screen.getByText('Ascenso Bloqueado')).toBeInTheDocument();
    expect(screen.queryByText('Subir de Rango')).not.toBeInTheDocument();
  });

  it('toggles detailed analysis when clicked', async () => {
    const user = userEvent.setup();
    render(
      <BattleReport 
        stats={defaultStats} 
        onClose={mockOnClose}
      />
    );
    
    const detailsButton = screen.getByText('Análisis Detallado');
    
    // Initially hidden
    expect(screen.queryByText('8/10')).not.toBeInTheDocument();
    
    // Click to show
    await user.click(detailsButton);
    await waitFor(() => {
      expect(screen.getByText('8/10')).toBeInTheDocument(); // Álgebra details
    });
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <BattleReport 
        stats={defaultStats} 
        onClose={mockOnClose}
      />
    );
    
    const closeButton = screen.getByText('Cerrar Reporte');
    await user.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onRankUp when rank up button is clicked', async () => {
    const user = userEvent.setup();
    const highPerformanceStats = {
      ...defaultStats,
      accuracy: 85,
      byTag: {
        'Álgebra': { correct: 10, total: 10, accuracy: 100 },
        'Geometría': { correct: 5, total: 5, accuracy: 100 },
        'Cálculo': { correct: 3, total: 3, accuracy: 100 },
        'Estadística': { correct: 2, total: 2, accuracy: 100 },
      },
    };
    
    render(
      <BattleReport 
        stats={highPerformanceStats} 
        onClose={mockOnClose}
        onRankUp={mockOnRankUp}
      />
    );
    
    const rankUpButton = screen.getByText('Subir de Rango');
    await user.click(rankUpButton);
    
    expect(mockOnRankUp).toHaveBeenCalled();
  });

  it('displays correct performance colors for different accuracy levels', () => {
    render(
      <BattleReport 
        stats={defaultStats} 
        onClose={mockOnClose}
      />
    );
    
    // Check that different accuracy levels have appropriate colors
    const accuracyElements = screen.getAllByText(/\d+%/);
    
    // Find the 100% accuracy element (Estadística)
    const perfectAccuracy = accuracyElements.find(el => el.textContent === '100%');
    expect(perfectAccuracy).toHaveClass('text-green-400');
  });

  it('fetches and displays AI tip for weaknesses', async () => {
    render(
      <BattleReport 
        stats={defaultStats} 
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('Consejo del Sistema IA')).toBeInTheDocument();
      expect(screen.getByText('Practica más álgebra para mejorar')).toBeInTheDocument();
    });
  });
});