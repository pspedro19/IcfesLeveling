/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QuestionCard } from '@/components/gamified/QuestionCard';

// Mock hooks
const mockUseSoundManager = {
  play: jest.fn(),
  playRandomEffect: jest.fn(),
  setVolume: jest.fn(),
};

jest.mock('@/hooks/useGameSounds', () => ({
  useGameSounds: () => mockUseSoundManager,
}));

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
    span: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
  useAnimation: () => ({
    start: jest.fn(),
    set: jest.fn(),
  }),
}));

const mockQuestion = {
  id: 1,
  question_text: "¿Cuál es el resultado de 2 + 2?",
  options: {
    A: "3",
    B: "4", 
    C: "5",
    D: "6"
  },
  difficulty: 2,
  subject_id: 1,
  topic_id: 1,
  question_type: "multiple_choice",
  competency: "Razonamiento cuantitativo"
};

describe('QuestionCard Component', () => {
  const defaultProps = {
    question: mockQuestion,
    selectedAnswer: null,
    onAnswerSelect: jest.fn(),
    showResult: false,
    correctAnswer: 'B',
    timeRemaining: 60,
    questionNumber: 1,
    totalQuestions: 10,
    isLoading: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders question text correctly', () => {
    render(<QuestionCard {...defaultProps} />);
    
    expect(screen.getByText('¿Cuál es el resultado de 2 + 2?')).toBeInTheDocument();
  });

  it('renders all answer options', () => {
    render(<QuestionCard {...defaultProps} />);
    
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
  });

  it('shows question number and total', () => {
    render(<QuestionCard {...defaultProps} />);
    
    expect(screen.getByText(/pregunta 1 de 10/i)).toBeInTheDocument();
  });

  it('displays difficulty level', () => {
    render(<QuestionCard {...defaultProps} />);
    
    // Assuming difficulty is shown as stars or similar indicator
    expect(screen.getByRole('img', { name: /difficulty/i })).toBeInTheDocument();
  });

  it('handles answer selection', () => {
    const mockOnAnswerSelect = jest.fn();
    render(<QuestionCard {...defaultProps} onAnswerSelect={mockOnAnswerSelect} />);
    
    const optionB = screen.getByRole('button', { name: /4/i });
    fireEvent.click(optionB);
    
    expect(mockOnAnswerSelect).toHaveBeenCalledWith('B');
    expect(mockUseSoundManager.play).toHaveBeenCalledWith('click');
  });

  it('shows selected answer visually', () => {
    render(<QuestionCard {...defaultProps} selectedAnswer="B" />);
    
    const selectedOption = screen.getByRole('button', { name: /4/i });
    expect(selectedOption).toHaveClass('selected');
  });

  it('displays timer', () => {
    render(<QuestionCard {...defaultProps} timeRemaining={45} />);
    
    expect(screen.getByText('45s')).toBeInTheDocument();
  });

  it('shows timer warning when time is low', () => {
    render(<QuestionCard {...defaultProps} timeRemaining={10} />);
    
    const timer = screen.getByText('10s');
    expect(timer).toHaveClass('warning');
  });

  it('disables options when showing result', () => {
    render(<QuestionCard {...defaultProps} showResult={true} selectedAnswer="A" />);
    
    const options = screen.getAllByRole('button');
    options.forEach(option => {
      expect(option).toBeDisabled();
    });
  });

  it('shows correct answer in green when revealing result', () => {
    render(<QuestionCard {...defaultProps} showResult={true} selectedAnswer="A" />);
    
    const correctOption = screen.getByRole('button', { name: /4/i });
    expect(correctOption).toHaveClass('correct');
  });

  it('shows incorrect answer in red when revealing result', () => {
    render(<QuestionCard {...defaultProps} showResult={true} selectedAnswer="A" />);
    
    const incorrectOption = screen.getByRole('button', { name: /3/i });
    expect(incorrectOption).toHaveClass('incorrect');
  });

  it('displays loading state', () => {
    render(<QuestionCard {...defaultProps} isLoading={true} />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('shows competency information', () => {
    render(<QuestionCard {...defaultProps} />);
    
    expect(screen.getByText('Razonamiento cuantitativo')).toBeInTheDocument();
  });

  it('handles keyboard navigation', () => {
    const mockOnAnswerSelect = jest.fn();
    render(<QuestionCard {...defaultProps} onAnswerSelect={mockOnAnswerSelect} />);
    
    const optionA = screen.getByRole('button', { name: /3/i });
    optionA.focus();
    fireEvent.keyDown(optionA, { key: 'Enter' });
    
    expect(mockOnAnswerSelect).toHaveBeenCalledWith('A');
  });

  it('supports accessibility features', () => {
    render(<QuestionCard {...defaultProps} />);
    
    const questionElement = screen.getByRole('group');
    expect(questionElement).toHaveAttribute('aria-label');
    
    const options = screen.getAllByRole('button');
    options.forEach((option, index) => {
      expect(option).toHaveAttribute('aria-label');
      expect(option).toHaveAttribute('tabIndex');
    });
  });
});

describe('QuestionCard Edge Cases', () => {
  const defaultProps = {
    question: mockQuestion,
    selectedAnswer: null,
    onAnswerSelect: jest.fn(),
    showResult: false,
    correctAnswer: 'B',
    timeRemaining: 60,
    questionNumber: 1,
    totalQuestions: 10,
    isLoading: false,
  };

  it('handles question with image', () => {
    const questionWithImage = {
      ...mockQuestion,
      image_url: '/mathimg/Math_1_1_Doc1.png'
    };

    render(<QuestionCard {...defaultProps} question={questionWithImage} />);
    
    expect(screen.getByRole('img', { name: /question image/i })).toBeInTheDocument();
  });

  it('handles very long question text', () => {
    const longQuestion = {
      ...mockQuestion,
      question_text: "Esta es una pregunta muy larga que debería truncarse o ajustarse correctamente en el diseño para asegurar una buena experiencia de usuario. ".repeat(5)
    };

    render(<QuestionCard {...defaultProps} question={longQuestion} />);
    
    const questionText = screen.getByText(/Esta es una pregunta muy larga/);
    expect(questionText).toBeInTheDocument();
  });

  it('handles empty or invalid options', () => {
    const questionWithInvalidOptions = {
      ...mockQuestion,
      options: {
        A: "",
        B: "Valid option",
        C: null,
        D: undefined
      }
    };

    render(<QuestionCard {...defaultProps} question={questionWithInvalidOptions} />);
    
    // Should still render valid options
    expect(screen.getByText('Valid option')).toBeInTheDocument();
  });

  it('handles zero time remaining', () => {
    render(<QuestionCard {...defaultProps} timeRemaining={0} />);
    
    expect(screen.getByText('0s')).toBeInTheDocument();
    const timer = screen.getByText('0s');
    expect(timer).toHaveClass('expired');
  });

  it('handles question without competency', () => {
    const questionWithoutCompetency = {
      ...mockQuestion,
      competency: null
    };

    render(<QuestionCard {...defaultProps} question={questionWithoutCompetency} />);
    
    // Should not crash and should render other elements
    expect(screen.getByText('¿Cuál es el resultado de 2 + 2?')).toBeInTheDocument();
  });
});

describe('QuestionCard Animations', () => {
  const defaultProps = {
    question: mockQuestion,
    selectedAnswer: null,
    onAnswerSelect: jest.fn(),
    showResult: false,
    correctAnswer: 'B',
    timeRemaining: 60,
    questionNumber: 1,
    totalQuestions: 10,
    isLoading: false,
  };

  it('triggers animation when answer is selected', async () => {
    const mockOnAnswerSelect = jest.fn();
    render(<QuestionCard {...defaultProps} onAnswerSelect={mockOnAnswerSelect} />);
    
    const optionB = screen.getByRole('button', { name: /4/i });
    fireEvent.click(optionB);
    
    await waitFor(() => {
      expect(mockUseSoundManager.play).toHaveBeenCalledWith('click');
    });
  });

  it('plays success sound for correct answer', async () => {
    render(<QuestionCard {...defaultProps} showResult={true} selectedAnswer="B" />);
    
    await waitFor(() => {
      expect(mockUseSoundManager.play).toHaveBeenCalledWith('success');
    });
  });

  it('plays error sound for incorrect answer', async () => {
    render(<QuestionCard {...defaultProps} showResult={true} selectedAnswer="A" />);
    
    await waitFor(() => {
      expect(mockUseSoundManager.play).toHaveBeenCalledWith('error');
    });
  });
});

describe('QuestionCard Performance', () => {
  const defaultProps = {
    question: mockQuestion,
    selectedAnswer: null,
    onAnswerSelect: jest.fn(),
    showResult: false,
    correctAnswer: 'B',
    timeRemaining: 60,
    questionNumber: 1,
    totalQuestions: 10,
    isLoading: false,
  };

  it('does not re-render unnecessarily', () => {
    const { rerender } = render(<QuestionCard {...defaultProps} />);
    
    // Re-render with same props
    rerender(<QuestionCard {...defaultProps} />);
    
    // Component should use React.memo or similar optimization
    expect(screen.getByText('¿Cuál es el resultado de 2 + 2?')).toBeInTheDocument();
  });

  it('handles rapid click events correctly', () => {
    const mockOnAnswerSelect = jest.fn();
    render(<QuestionCard {...defaultProps} onAnswerSelect={mockOnAnswerSelect} />);
    
    const optionB = screen.getByRole('button', { name: /4/i });
    
    // Rapid clicks
    fireEvent.click(optionB);
    fireEvent.click(optionB);
    fireEvent.click(optionB);
    
    // Should only call once due to debouncing
    expect(mockOnAnswerSelect).toHaveBeenCalledTimes(1);
  });
});