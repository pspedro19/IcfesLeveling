'use client';

import { useState, useEffect } from 'react';
import { useMediaQuery } from '../hooks/useMediaQuery';
import MobileContainer from '../components/Mobile/MobileContainer';
import MobileGrid from '../components/Mobile/MobileGrid';
import MobileCard from '../components/Mobile/MobileCard';
import MobileButton from '../components/Mobile/MobileButton';

export default function MobileDiagnostic() {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Media queries for responsive behavior
  const isMobile = useMediaQuery('(max-width: 767px)');
  const isTablet = useMediaQuery('(min-width: 768px) and (max-width: 1023px)');
  
  useEffect(() => {
    const loadSubjects = async () => {
      try {
        console.log('🚀 Loading subjects for mobile diagnostic...');
        const response = await fetch('http://localhost:4001/api/v1/diagnostic-public/subjects');
        
        if (response.ok) {
          const data = await response.json();
          console.log('✅ Subjects loaded for mobile:', data);
          setSubjects(data);
        } else {
          setError(`Failed to load: ${response.status}`);
        }
      } catch (err: any) {
        console.error('❌ Mobile diagnostic error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadSubjects();
  }, []);

  const handleSubjectClick = (subject: any) => {
    // Enhanced mobile feedback
    if (navigator.vibrate) {
      navigator.vibrate(50); // Haptic feedback
    }
    alert(`🎮 Starting ${subject.name} diagnostic!\n📱 Mobile-optimized interface`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-game-void via-game-abyss to-game-shadow flex items-center justify-center">
        <MobileContainer className="text-center">
          <div className="animate-spin w-16 h-16 border-4 border-game-neonGold border-t-transparent rounded-full mx-auto mb-4"></div>
          <h1 className="text-xl md:text-2xl text-white mb-2">📱 Loading Mobile Diagnostic...</h1>
          <p className="text-game-neonBlue">Optimizing for your device</p>
        </MobileContainer>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-game-void via-game-abyss to-game-shadow flex items-center justify-center">
        <MobileContainer className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-xl md:text-2xl text-red-400 mb-2">Connection Error</h1>
          <p className="text-white mb-4">{error}</p>
          <MobileButton 
            variant="danger" 
            onClick={() => window.location.reload()}
          >
            🔄 Retry
          </MobileButton>
        </MobileContainer>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-game-void via-game-abyss to-game-shadow">
      <MobileContainer safeArea className="py-6">
        {/* Header Section */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-game-neonGold to-yellow-500 rounded-full mb-4 shadow-[0_0_30px_rgba(255,215,0,0.6)]">
            <span className="text-3xl">🎯</span>
          </div>
          
          <h1 className="text-3xl md:text-4xl font-bold text-game-neonGold mb-2 font-game">
            📱 Mobile Diagnostic
          </h1>
          
          <p className="text-lg text-game-neonBlue mb-2">
            Found {subjects.length} subjects
          </p>
          
          <div className="flex items-center justify-center gap-2 text-sm text-gray-400">
            <span>📱</span>
            <span>{isMobile ? 'Mobile' : isTablet ? 'Tablet' : 'Desktop'} Mode</span>
            <span>•</span>
            <span>Touch Optimized</span>
          </div>
        </div>

        {/* Subjects Grid */}
        <MobileGrid
          columns={{ mobile: 1, tablet: 2, desktop: 3 }}
          gap={isMobile ? 'md' : 'lg'}
          className="mb-8"
        >
          {subjects.map((subject: any) => (
            <MobileCard
              key={subject.id}
              title={subject.name}
              subtitle={subject.description}
              variant="gaming"
              size={isMobile ? 'default' : 'large'}
              interactive
              onClick={() => handleSubjectClick(subject)}
              icon={<span>📚</span>}
            >
              {/* Subject Details */}
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-game-neonGold">⚔️</span>
                    <div>
                      <div className="text-gray-400">Questions</div>
                      <div className="text-white font-semibold">
                        {subject.config.total_questions}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-game-neonBlue">⏱️</span>
                    <div>
                      <div className="text-gray-400">Time</div>
                      <div className="text-white font-semibold">
                        {subject.config.time_limit_minutes}m
                      </div>
                    </div>
                  </div>
                </div>
                
                <MobileButton 
                  fullWidth 
                  size={isMobile ? 'md' : 'lg'}
                  onClick={() => handleSubjectClick(subject)}
                >
                  <span className="flex items-center gap-2">
                    <span>🚀</span>
                    <span>Start Diagnostic</span>
                  </span>
                </MobileButton>
              </div>
            </MobileCard>
          ))}
        </MobileGrid>

        {/* Mobile-specific features section */}
        <MobileCard variant="elevated" className="mb-6">
          <h3 className="text-lg font-semibold text-game-neonGold mb-4 flex items-center gap-2">
            <span>📱</span>
            <span>Mobile Features</span>
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex items-start gap-3">
              <span className="text-2xl">👆</span>
              <div>
                <div className="font-semibold text-white">Touch Optimized</div>
                <div className="text-gray-400">Large buttons (44px+ minimum)</div>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-2xl">📲</span>
              <div>
                <div className="font-semibold text-white">Haptic Feedback</div>
                <div className="text-gray-400">Vibration on interactions</div>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-2xl">🔄</span>
              <div>
                <div className="font-semibold text-white">Auto-Rotate</div>
                <div className="text-gray-400">Portrait & landscape support</div>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-2xl">⚡</span>
              <div>
                <div className="font-semibold text-white">Fast Performance</div>
                <div className="text-gray-400">Optimized for mobile networks</div>
              </div>
            </div>
          </div>
        </MobileCard>

        {/* Success Status */}
        <div className="text-center p-4 bg-green-500/20 border border-green-500/30 rounded-lg">
          <div className="text-2xl mb-2">✅</div>
          <p className="text-green-400 font-semibold">
            Mobile Diagnostic System Active
          </p>
          <p className="text-sm text-gray-400 mt-1">
            Touch targets optimized • Responsive design • Cross-platform compatible
          </p>
        </div>
      </MobileContainer>
    </div>
  );
}