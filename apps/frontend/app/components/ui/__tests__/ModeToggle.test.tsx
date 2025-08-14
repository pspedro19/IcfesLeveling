import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ModeToggle from '../ModeToggle';
import { useGameModeStore } from '@/stores/useGameModeStore';

// Mock the store
jest.mock('@/stores/useGameModeStore');

// Mock the audio hook
jest.mock('../../PortalLogin/AudioEngine', () => ({
  useAudio: () => ({
    playSound: jest.fn(),
  }),
}));

describe('ModeToggle', () => {
  const mockSetMode = jest.fn();
  const mockGetModeDescription = jest.fn();
  
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Setup default mock implementation
    (useGameModeStore as jest.Mock).mockReturnValue({
      mode: 'gated',
      modeSettings: {
        requireAllUnits: true,
        minimumAccuracy: 80,
        unlockRequirements: true,
        showWeaknessWarnings: true,
        allowSkipContent: false,
        rankProgressionLocked: true,
      },
      setMode: mockSetMode,
      getModeDescription: mockGetModeDescription.mockReturnValue(
        'Progresión estructurada que requiere dominar cada tema antes de avanzar. Diseñado para máximo aprendizaje.'
      ),
    });
  });

  it('renders both mode buttons', () => {
    render(<ModeToggle />);
    
    expect(screen.getByText('Modo Casual')).toBeInTheDocument();
    expect(screen.getByText('Modo Progresión')).toBeInTheDocument();
  });

  it('shows the current mode as active', () => {
    render(<ModeToggle />);
    
    const progressionButton = screen.getByRole('button', { name: /Modo Progresión/i });
    expect(progressionButton).toHaveClass('bg-purple-600');
  });

  it('switches to casual mode when clicked', async () => {
    const user = userEvent.setup();
    render(<ModeToggle />);
    
    const casualButton = screen.getByRole('button', { name: /Modo Casual/i });
    await user.click(casualButton);
    
    expect(mockSetMode).toHaveBeenCalledWith('casual');
  });

  it('shows mode description when showDetails is true', () => {
    render(<ModeToggle showDetails={true} />);
    
    expect(screen.getByText(/Progresión estructurada/i)).toBeInTheDocument();
  });

  it('hides mode description when showDetails is false', () => {
    render(<ModeToggle showDetails={false} />);
    
    expect(screen.queryByText(/Progresión estructurada/i)).not.toBeInTheDocument();
  });

  it('shows info modal when info button is clicked', async () => {
    const user = userEvent.setup();
    render(<ModeToggle />);
    
    const infoButton = screen.getByRole('button', { name: '' }); // Info icon button
    await user.click(infoButton);
    
    await waitFor(() => {
      expect(screen.getByText('Modos de Juego')).toBeInTheDocument();
      expect(screen.getByText('Exploración Libre')).toBeInTheDocument();
      expect(screen.getByText('Aprendizaje Estructurado')).toBeInTheDocument();
    });
  });

  it('closes info modal when background is clicked', async () => {
    const user = userEvent.setup();
    render(<ModeToggle />);
    
    // Open modal
    const infoButton = screen.getByRole('button', { name: '' });
    await user.click(infoButton);
    
    // Click background
    const modal = screen.getByText('Modos de Juego');
    const background = modal.closest('div')?.previousSibling;
    
    if (background) {
      fireEvent.click(background);
      await waitFor(() => {
        expect(screen.queryByText('Modos de Juego')).not.toBeInTheDocument();
      });
    }
  });

  it('calls onModeChange callback when mode is changed', async () => {
    const mockOnModeChange = jest.fn();
    const user = userEvent.setup();
    
    render(<ModeToggle onModeChange={mockOnModeChange} />);
    
    const casualButton = screen.getByRole('button', { name: /Modo Casual/i });
    await user.click(casualButton);
    
    expect(mockOnModeChange).toHaveBeenCalledWith('casual');
  });

  it('displays current mode settings in info modal', async () => {
    const user = userEvent.setup();
    render(<ModeToggle />);
    
    const infoButton = screen.getByRole('button', { name: '' });
    await user.click(infoButton);
    
    await waitFor(() => {
      expect(screen.getByText('80%')).toBeInTheDocument(); // minimumAccuracy
      expect(screen.getByText('Requeridos')).toBeInTheDocument(); // unlockRequirements
      expect(screen.getByText('No permitido')).toBeInTheDocument(); // allowSkipContent
      expect(screen.getByText('Bloqueada')).toBeInTheDocument(); // rankProgressionLocked
    });
  });

  it('does not call setMode when clicking the already active mode', async () => {
    const user = userEvent.setup();
    render(<ModeToggle />);
    
    const progressionButton = screen.getByRole('button', { name: /Modo Progresión/i });
    await user.click(progressionButton);
    
    expect(mockSetMode).not.toHaveBeenCalled();
  });
});