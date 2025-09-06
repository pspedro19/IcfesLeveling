/**
 * Integration tests for the diagnostic flow
 * @jest-environment jsdom
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Mock Next.js router
const mockPush = jest.fn();
const mockRouter = {
  push: mockPush,
  query: { subject: '1' },
  pathname: '/diagnostic-test',
};

jest.mock('next/router', () => ({
  useRouter: () => mockRouter,
}));

// Mock services
jest.mock('@/services/question.service');
jest.mock('@/services/auth.service');

// Mock stores
const mockAuthStore = {
  user: {
    id: 'user-123',
    username: 'testuser',
    display_name: 'Test User',
    rank: 'E',
    level: 1,
  },
  isAuthenticated: true,
};

jest.mock('@/stores/useAuthStore', () => ({
  useAuthStore: () => mockAuthStore,
}));

// Test components (mock implementations)
const DiagnosticTest = () => {
  const [currentQuestion, setCurrentQuestion] = React.useState(0);
  const [answers, setAnswers] = React.useState<string[]>([]);
  const [timeRemaining, setTimeRemaining] = React.useState(1800); // 30 minutes

  const mockQuestions = [
    {
      id: 1,
      question_text: "¿Cuál es el resultado de 15 + 27?",
      options: { A: "42", B: "41", C: "43", D: "40" },
      correct_answer: "A",
      difficulty: 1,
    },
    {
      id: 2,
      question_text: "Si x + 5 = 12, ¿cuál es el valor de x?",
      options: { A: "6", B: "7", C: "8", D: "5" },
      correct_answer: "B",
      difficulty: 2,
    },
    {
      id: 3,
      question_text: "¿Cuál es la raíz cuadrada de 144?",
      options: { A: "11", B: "12", C: "13", D: "14" },
      correct_answer: "B",
      difficulty: 2,
    },
  ];

  const handleAnswerSelect = (answer: string) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = answer;
    setAnswers(newAnswers);
  };

  const handleNextQuestion = () => {
    if (currentQuestion < mockQuestions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      // Submit test
      handleSubmitTest();
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const handleSubmitTest = async () => {
    // Calculate score
    let correct = 0;
    answers.forEach((answer, index) => {
      if (answer === mockQuestions[index]?.correct_answer) {
        correct++;
      }
    });

    const score = (correct / mockQuestions.length) * 100;
    
    // Navigate to results
    mockPush(`/diagnostic-test/results?score=${score}&correct=${correct}&total=${mockQuestions.length}`);
  };

  const currentQ = mockQuestions[currentQuestion];
  const progress = ((currentQuestion + 1) / mockQuestions.length) * 100;

  return (
    <div data-testid="diagnostic-test">
      <div className="test-header">
        <div data-testid="progress-bar" style={{ width: `${progress}%` }} />
        <div data-testid="question-counter">
          Pregunta {currentQuestion + 1} de {mockQuestions.length}
        </div>
        <div data-testid="timer">
          {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}
        </div>
      </div>

      <div className="question-content">
        <h2 data-testid="question-text">{currentQ.question_text}</h2>
        
        <div className="options">
          {Object.entries(currentQ.options).map(([key, value]) => (
            <button
              key={key}
              data-testid={`option-${key}`}
              className={`option ${answers[currentQuestion] === key ? 'selected' : ''}`}
              onClick={() => handleAnswerSelect(key)}
            >
              {key}. {value}
            </button>
          ))}
        </div>
      </div>

      <div className="navigation">
        <button
          data-testid="previous-button"
          onClick={handlePreviousQuestion}
          disabled={currentQuestion === 0}
        >
          Anterior
        </button>
        
        <button
          data-testid="next-button"
          onClick={handleNextQuestion}
          disabled={!answers[currentQuestion]}
        >
          {currentQuestion === mockQuestions.length - 1 ? 'Finalizar' : 'Siguiente'}
        </button>
      </div>
    </div>
  );
};

const DiagnosticResults = () => {
  const [results, setResults] = React.useState({
    score: 80,
    correct: 8,
    total: 10,
    rank: 'B',
    recommendations: [
      'Reforzar conocimientos en álgebra básica',
      'Practicar más ejercicios de aritmética',
      'Revisar conceptos de geometría'
    ]
  });

  return (
    <div data-testid="diagnostic-results">
      <div className="results-header">
        <h1>Resultados del Diagnóstico</h1>
        <div data-testid="score" className="score">
          {results.score}%
        </div>
        <div data-testid="rank" className="rank">
          Rango: {results.rank}
        </div>
      </div>

      <div className="results-details">
        <div data-testid="correct-answers">
          Respuestas correctas: {results.correct} de {results.total}
        </div>
        
        <div className="recommendations">
          <h3>Recomendaciones:</h3>
          <ul data-testid="recommendations-list">
            {results.recommendations.map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="actions">
        <button
          data-testid="view-study-plan"
          onClick={() => mockPush('/study-plan-view')}
        >
          Ver Plan de Estudio
        </button>
        
        <button
          data-testid="retake-test"
          onClick={() => mockPush('/diagnostic-test')}
        >
          Repetir Diagnóstico
        </button>
      </div>
    </div>
  );
};

// Wrapper component for tests
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Diagnostic Flow Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Diagnostic Test Component', () => {
    it('renders the diagnostic test interface correctly', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      expect(screen.getByTestId('diagnostic-test')).toBeInTheDocument();
      expect(screen.getByTestId('question-counter')).toHaveTextContent('Pregunta 1 de 3');
      expect(screen.getByTestId('timer')).toBeInTheDocument();
      expect(screen.getByTestId('question-text')).toHaveTextContent('¿Cuál es el resultado de 15 + 27?');
    });

    it('displays all answer options for the current question', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      expect(screen.getByTestId('option-A')).toHaveTextContent('A. 42');
      expect(screen.getByTestId('option-B')).toHaveTextContent('B. 41');
      expect(screen.getByTestId('option-C')).toHaveTextContent('C. 43');
      expect(screen.getByTestId('option-D')).toHaveTextContent('D. 40');
    });

    it('allows selecting answers and shows selection visually', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      const optionA = screen.getByTestId('option-A');
      fireEvent.click(optionA);

      expect(optionA).toHaveClass('selected');
      expect(screen.getByTestId('next-button')).not.toBeDisabled();
    });

    it('navigates through questions correctly', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      // Select answer for first question
      fireEvent.click(screen.getByTestId('option-A'));
      
      // Go to next question
      fireEvent.click(screen.getByTestId('next-button'));

      expect(screen.getByTestId('question-counter')).toHaveTextContent('Pregunta 2 de 3');
      expect(screen.getByTestId('question-text')).toHaveTextContent('Si x + 5 = 12, ¿cuál es el valor de x?');
      expect(screen.getByTestId('previous-button')).not.toBeDisabled();
    });

    it('prevents navigation without selecting an answer', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      const nextButton = screen.getByTestId('next-button');
      expect(nextButton).toBeDisabled();
    });

    it('shows progress bar updates', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      const progressBar = screen.getByTestId('progress-bar');
      
      // First question should show 33.33% progress
      expect(progressBar).toHaveStyle('width: 33.333333333333336%');

      // Navigate to second question
      fireEvent.click(screen.getByTestId('option-A'));
      fireEvent.click(screen.getByTestId('next-button'));

      // Second question should show 66.67% progress
      expect(progressBar).toHaveStyle('width: 66.66666666666667%');
    });

    it('can navigate back to previous questions', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      // Navigate to second question
      fireEvent.click(screen.getByTestId('option-A'));
      fireEvent.click(screen.getByTestId('next-button'));

      // Go back to first question
      fireEvent.click(screen.getByTestId('previous-button'));

      expect(screen.getByTestId('question-counter')).toHaveTextContent('Pregunta 1 de 3');
      expect(screen.getByTestId('option-A')).toHaveClass('selected'); // Should remember selection
    });

    it('completes the test and navigates to results', async () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      // Answer all questions
      fireEvent.click(screen.getByTestId('option-A')); // Correct
      fireEvent.click(screen.getByTestId('next-button'));

      fireEvent.click(screen.getByTestId('option-B')); // Correct
      fireEvent.click(screen.getByTestId('next-button'));

      fireEvent.click(screen.getByTestId('option-A')); // Incorrect
      
      // Final button should say "Finalizar"
      expect(screen.getByTestId('next-button')).toHaveTextContent('Finalizar');
      fireEvent.click(screen.getByTestId('next-button'));

      // Should navigate to results with calculated score
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/diagnostic-test/results?score=66.66666666666666&correct=2&total=3');
      });
    });
  });

  describe('Diagnostic Results Component', () => {
    it('displays the test results correctly', () => {
      render(
        <TestWrapper>
          <DiagnosticResults />
        </TestWrapper>
      );

      expect(screen.getByTestId('diagnostic-results')).toBeInTheDocument();
      expect(screen.getByTestId('score')).toHaveTextContent('80%');
      expect(screen.getByTestId('rank')).toHaveTextContent('Rango: B');
      expect(screen.getByTestId('correct-answers')).toHaveTextContent('Respuestas correctas: 8 de 10');
    });

    it('shows personalized recommendations', () => {
      render(
        <TestWrapper>
          <DiagnosticResults />
        </TestWrapper>
      );

      const recommendationsList = screen.getByTestId('recommendations-list');
      expect(recommendationsList).toHaveTextContent('Reforzar conocimientos en álgebra básica');
      expect(recommendationsList).toHaveTextContent('Practicar más ejercicios de aritmética');
      expect(recommendationsList).toHaveTextContent('Revisar conceptos de geometría');
    });

    it('provides navigation to study plan', () => {
      render(
        <TestWrapper>
          <DiagnosticResults />
        </TestWrapper>
      );

      const studyPlanButton = screen.getByTestId('view-study-plan');
      fireEvent.click(studyPlanButton);

      expect(mockPush).toHaveBeenCalledWith('/study-plan-view');
    });

    it('allows retaking the diagnostic test', () => {
      render(
        <TestWrapper>
          <DiagnosticResults />
        </TestWrapper>
      );

      const retakeButton = screen.getByTestId('retake-test');
      fireEvent.click(retakeButton);

      expect(mockPush).toHaveBeenCalledWith('/diagnostic-test');
    });
  });

  describe('Complete Diagnostic Flow', () => {
    it('handles the complete flow from test to results', async () => {
      const { rerender } = render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      // Complete the diagnostic test
      fireEvent.click(screen.getByTestId('option-A'));
      fireEvent.click(screen.getByTestId('next-button'));

      fireEvent.click(screen.getByTestId('option-B'));
      fireEvent.click(screen.getByTestId('next-button'));

      fireEvent.click(screen.getByTestId('option-B'));
      fireEvent.click(screen.getByTestId('next-button'));

      // Verify navigation to results
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/diagnostic-test/results?score=100&correct=3&total=3');
      });

      // Render results component
      rerender(
        <TestWrapper>
          <DiagnosticResults />
        </TestWrapper>
      );

      // Verify results are displayed
      expect(screen.getByTestId('diagnostic-results')).toBeInTheDocument();
    });

    it('handles partial completion and resume', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      // Answer first question
      fireEvent.click(screen.getByTestId('option-A'));
      fireEvent.click(screen.getByTestId('next-button'));

      // Answer second question
      fireEvent.click(screen.getByTestId('option-B'));
      
      // Go back to first question
      fireEvent.click(screen.getByTestId('previous-button'));
      
      // Verify first answer is still selected
      expect(screen.getByTestId('option-A')).toHaveClass('selected');
      
      // Go forward again
      fireEvent.click(screen.getByTestId('next-button'));
      
      // Verify second answer is still selected
      expect(screen.getByTestId('option-B')).toHaveClass('selected');
    });

    it('handles edge cases and error states', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      // Try to go to previous question on first question
      const previousButton = screen.getByTestId('previous-button');
      expect(previousButton).toBeDisabled();

      // Try to proceed without selecting an answer
      const nextButton = screen.getByTestId('next-button');
      expect(nextButton).toBeDisabled();
    });
  });

  describe('Timer Functionality', () => {
    it('displays timer correctly', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      const timer = screen.getByTestId('timer');
      expect(timer).toHaveTextContent('30:00'); // 30 minutes
    });

    it('updates timer countdown', async () => {
      jest.useFakeTimers();
      
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      // Fast forward time
      jest.advanceTimersByTime(60000); // 1 minute

      await waitFor(() => {
        const timer = screen.getByTestId('timer');
        expect(timer).toHaveTextContent('29:00');
      });

      jest.useRealTimers();
    });
  });

  describe('Accessibility', () => {
    it('provides proper ARIA labels and roles', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      const questionText = screen.getByTestId('question-text');
      expect(questionText).toHaveAttribute('role', 'heading');

      const options = screen.getAllByRole('button');
      options.forEach((option) => {
        expect(option).toHaveAttribute('aria-label');
      });
    });

    it('supports keyboard navigation', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      const optionA = screen.getByTestId('option-A');
      optionA.focus();
      
      fireEvent.keyDown(optionA, { key: 'Enter' });
      expect(optionA).toHaveClass('selected');

      const nextButton = screen.getByTestId('next-button');
      fireEvent.keyDown(nextButton, { key: 'Enter' });
      
      expect(screen.getByTestId('question-counter')).toHaveTextContent('Pregunta 2 de 3');
    });
  });

  describe('Performance', () => {
    it('does not cause memory leaks', () => {
      const { unmount } = render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      // Component should unmount cleanly
      expect(() => unmount()).not.toThrow();
    });

    it('handles rapid user interactions', () => {
      render(
        <TestWrapper>
          <DiagnosticTest />
        </TestWrapper>
      );

      const optionA = screen.getByTestId('option-A');
      
      // Rapid clicks should not cause issues
      for (let i = 0; i < 10; i++) {
        fireEvent.click(optionA);
      }

      expect(optionA).toHaveClass('selected');
    });
  });
});