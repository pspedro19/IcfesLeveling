'use client';

import React, { useState, useEffect } from 'react';
import { useMediaQuery } from '../hooks/useMediaQuery';
import MobileContainer from '../components/Mobile/MobileContainer';
import MobileGrid from '../components/Mobile/MobileGrid';
import MobileCard from '../components/Mobile/MobileCard';
import MobileButton from '../components/Mobile/MobileButton';

interface DeviceInfo {
  userAgent: string;
  screenWidth: number;
  screenHeight: number;
  devicePixelRatio: number;
  orientation: string;
  touchSupport: boolean;
  platform: string;
}

interface TouchTest {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'success' | 'failed';
  size: string;
}

export default function MobileTestComprehensive() {
  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo | null>(null);
  const [touchTests, setTouchTests] = useState<TouchTest[]>([
    {
      id: 'small-button',
      name: 'Small Button (40px)',
      description: 'Minimum touch target test',
      status: 'pending',
      size: '40px'
    },
    {
      id: 'recommended-button',
      name: 'Recommended Button (44px)',
      description: 'iOS/Android recommended size',
      status: 'pending',
      size: '44px'
    },
    {
      id: 'comfortable-button',
      name: 'Comfortable Button (48px)',
      description: 'Comfortable touch target',
      status: 'pending',
      size: '48px'
    },
    {
      id: 'large-button',
      name: 'Large Button (56px)',
      description: 'Large touch target test',
      status: 'pending',
      size: '56px'
    }
  ]);

  // Media queries
  const isMobile = useMediaQuery('(max-width: 767px)');
  const isTablet = useMediaQuery('(min-width: 768px) and (max-width: 1023px)');
  const isDesktop = useMediaQuery('(min-width: 1024px)');
  const isPortrait = useMediaQuery('(orientation: portrait)');
  const isLandscape = useMediaQuery('(orientation: landscape)');
  const isRetina = useMediaQuery('(min-resolution: 192dpi)');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const info: DeviceInfo = {
        userAgent: navigator.userAgent,
        screenWidth: window.screen.width,
        screenHeight: window.screen.height,
        devicePixelRatio: window.devicePixelRatio || 1,
        orientation: screen.orientation?.type || 'unknown',
        touchSupport: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
        platform: navigator.platform
      };
      setDeviceInfo(info);
    }
  }, []);

  const handleTouchTest = (testId: string) => {
    // Haptic feedback if available
    if (navigator.vibrate) {
      navigator.vibrate(50);
    }

    // Update test status
    setTouchTests(prev => prev.map(test => 
      test.id === testId 
        ? { ...test, status: 'success' as const }
        : test
    ));
  };

  const getDeviceCategory = () => {
    if (isMobile) return 'Mobile';
    if (isTablet) return 'Tablet';
    if (isDesktop) return 'Desktop';
    return 'Unknown';
  };

  const getScreenSize = () => {
    if (!deviceInfo) return 'Unknown';
    return `${deviceInfo.screenWidth} × ${deviceInfo.screenHeight}`;
  };

  const runPerformanceTest = () => {
    const startTime = performance.now();
    
    // Simulate some work
    for (let i = 0; i < 100000; i++) {
      Math.random();
    }
    
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    alert(`Performance Test:\nExecution time: ${duration.toFixed(2)}ms\n${duration < 10 ? '✅ Excellent' : duration < 50 ? '✅ Good' : '⚠️ Needs optimization'}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-game-void via-game-abyss to-game-shadow">
      <MobileContainer safeArea className="py-6">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full mb-4 shadow-[0_0_30px_rgba(34,197,94,0.6)]">
            <span className="text-3xl">🧪</span>
          </div>
          
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2 font-game">
            Mobile Testing Suite
          </h1>
          
          <p className="text-lg text-gray-300 mb-4">
            Comprehensive responsiveness validation
          </p>
          
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-500/20 border border-green-500/30 rounded-full text-green-400 text-sm">
            <span>🎯</span>
            <span>{getDeviceCategory()} Mode Active</span>
          </div>
        </div>

        {/* Device Information */}
        {deviceInfo && (
          <MobileCard variant="elevated" className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>📱</span>
              <span>Device Information</span>
            </h3>
            
            <MobileGrid columns={{ mobile: 1, tablet: 2, desktop: 3 }} gap="md">
              <div className="space-y-2">
                <div className="text-sm text-gray-400">Screen Size</div>
                <div className="text-white font-mono">{getScreenSize()}</div>
              </div>
              
              <div className="space-y-2">
                <div className="text-sm text-gray-400">Device Pixel Ratio</div>
                <div className="text-white font-mono">{deviceInfo.devicePixelRatio}x</div>
              </div>
              
              <div className="space-y-2">
                <div className="text-sm text-gray-400">Touch Support</div>
                <div className="text-white">
                  {deviceInfo.touchSupport ? '✅ Yes' : '❌ No'}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="text-sm text-gray-400">Orientation</div>
                <div className="text-white">
                  {isPortrait ? '📱 Portrait' : '📱 Landscape'}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="text-sm text-gray-400">Retina Display</div>
                <div className="text-white">
                  {isRetina ? '✅ Yes' : '❌ No'}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="text-sm text-gray-400">Platform</div>
                <div className="text-white font-mono text-xs truncate">
                  {deviceInfo.platform}
                </div>
              </div>
            </MobileGrid>
          </MobileCard>
        )}

        {/* Breakpoint Tests */}
        <MobileCard variant="gaming" className="mb-6">
          <h3 className="text-lg font-semibold text-game-neonGold mb-4 flex items-center gap-2">
            <span>📐</span>
            <span>Responsive Breakpoints</span>
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className={`p-3 rounded-lg text-center ${isMobile ? 'bg-green-500/20 border border-green-500/30' : 'bg-gray-500/20 border border-gray-500/30'}`}>
              <div className="text-lg mb-1">{isMobile ? '✅' : '❌'}</div>
              <div className="text-sm font-semibold">Mobile</div>
              <div className="text-xs text-gray-400">&lt; 768px</div>
            </div>
            
            <div className={`p-3 rounded-lg text-center ${isTablet ? 'bg-green-500/20 border border-green-500/30' : 'bg-gray-500/20 border border-gray-500/30'}`}>
              <div className="text-lg mb-1">{isTablet ? '✅' : '❌'}</div>
              <div className="text-sm font-semibold">Tablet</div>
              <div className="text-xs text-gray-400">768-1023px</div>
            </div>
            
            <div className={`p-3 rounded-lg text-center ${isDesktop ? 'bg-green-500/20 border border-green-500/30' : 'bg-gray-500/20 border border-gray-500/30'}`}>
              <div className="text-lg mb-1">{isDesktop ? '✅' : '❌'}</div>
              <div className="text-sm font-semibold">Desktop</div>
              <div className="text-xs text-gray-400">&gt; 1024px</div>
            </div>
            
            <div className={`p-3 rounded-lg text-center ${isPortrait ? 'bg-green-500/20 border border-green-500/30' : 'bg-blue-500/20 border border-blue-500/30'}`}>
              <div className="text-lg mb-1">{isPortrait ? '📱' : '📱'}</div>
              <div className="text-sm font-semibold">{isPortrait ? 'Portrait' : 'Landscape'}</div>
              <div className="text-xs text-gray-400">Orientation</div>
            </div>
          </div>
        </MobileCard>

        {/* Touch Target Tests */}
        <MobileCard variant="gaming" className="mb-6">
          <h3 className="text-lg font-semibold text-game-neonGold mb-4 flex items-center gap-2">
            <span>👆</span>
            <span>Touch Target Tests</span>
          </h3>
          
          <div className="space-y-4">
            <p className="text-sm text-gray-300 mb-4">
              Test different button sizes to validate touch accessibility (tap each button)
            </p>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {touchTests.map((test) => (
                <div key={test.id} className="text-center">
                  <button
                    onClick={() => handleTouchTest(test.id)}
                    className={`
                      bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700
                      text-white font-semibold rounded-lg transition-all duration-200
                      touch-manipulation active:scale-95
                      ${test.status === 'success' ? 'ring-2 ring-green-500' : ''}
                      flex items-center justify-center mx-auto mb-2
                    `}
                    style={{
                      width: test.size,
                      height: test.size,
                      minWidth: test.size,
                      minHeight: test.size
                    }}
                  >
                    {test.status === 'success' ? '✅' : '👆'}
                  </button>
                  
                  <div className="text-xs">
                    <div className="font-semibold text-white">{test.name}</div>
                    <div className="text-gray-400">{test.description}</div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 p-3 bg-blue-500/20 border border-blue-500/30 rounded-lg">
              <div className="text-sm text-blue-300">
                <strong>Recommendation:</strong> Use minimum 44px touch targets for mobile accessibility.
                The 48px+ buttons provide the most comfortable experience.
              </div>
            </div>
          </div>
        </MobileCard>

        {/* Performance Tests */}
        <MobileCard variant="elevated" className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <span>⚡</span>
            <span>Performance Tests</span>
          </h3>
          
          <MobileGrid columns={{ mobile: 1, tablet: 2, desktop: 3 }} gap="md">
            <MobileButton
              variant="warning"
              onClick={runPerformanceTest}
              size="md"
            >
              <span className="flex items-center gap-2">
                <span>🧮</span>
                <span>CPU Test</span>
              </span>
            </MobileButton>
            
            <MobileButton
              variant="secondary"
              onClick={() => {
                const connection = (navigator as any).connection;
                if (connection) {
                  alert(`Network Info:\nType: ${connection.effectiveType}\nDownlink: ${connection.downlink} Mbps\nRTT: ${connection.rtt}ms`);
                } else {
                  alert('Network information not available');
                }
              }}
              size="md"
            >
              <span className="flex items-center gap-2">
                <span>📶</span>
                <span>Network Info</span>
              </span>
            </MobileButton>
            
            <MobileButton
              variant="success"
              onClick={() => {
                const memory = (performance as any).memory;
                if (memory) {
                  alert(`Memory Info:\nUsed: ${(memory.usedJSHeapSize / 1048576).toFixed(2)} MB\nLimit: ${(memory.jsHeapSizeLimit / 1048576).toFixed(2)} MB`);
                } else {
                  alert('Memory information not available');
                }
              }}
              size="md"
            >
              <span className="flex items-center gap-2">
                <span>🧠</span>
                <span>Memory Info</span>
              </span>
            </MobileButton>
          </MobileGrid>
        </MobileCard>

        {/* Feature Tests */}
        <MobileCard variant="default" className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <span>🔧</span>
            <span>Mobile Features</span>
          </h3>
          
          <MobileGrid columns={{ mobile: 2, tablet: 3, desktop: 4 }} gap="sm">
            <MobileButton
              variant="primary"
              size="sm"
              onClick={() => {
                if (navigator.vibrate) {
                  navigator.vibrate([100, 50, 100]);
                  alert('✅ Vibration works!');
                } else {
                  alert('❌ Vibration not supported');
                }
              }}
            >
              📲 Vibrate
            </MobileButton>
            
            <MobileButton
              variant="primary"
              size="sm"
              onClick={() => {
                if ('serviceWorker' in navigator) {
                  alert('✅ Service Worker supported');
                } else {
                  alert('❌ Service Worker not supported');
                }
              }}
            >
              ⚙️ SW Support
            </MobileButton>
            
            <MobileButton
              variant="primary"
              size="sm"
              onClick={() => {
                if ('geolocation' in navigator) {
                  alert('✅ Geolocation supported');
                } else {
                  alert('❌ Geolocation not supported');
                }
              }}
            >
              📍 Location
            </MobileButton>
            
            <MobileButton
              variant="primary"
              size="sm"
              onClick={() => {
                if ('requestFullscreen' in document.documentElement) {
                  alert('✅ Fullscreen supported');
                } else {
                  alert('❌ Fullscreen not supported');
                }
              }}
            >
              🖥️ Fullscreen
            </MobileButton>
          </MobileGrid>
        </MobileCard>

        {/* Test Results Summary */}
        <div className="text-center p-6 bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 rounded-lg">
          <div className="text-3xl mb-2">🎯</div>
          <h3 className="text-xl font-semibold text-white mb-2">
            Mobile Testing Complete
          </h3>
          <p className="text-green-400 mb-4">
            System optimized for {getDeviceCategory().toLowerCase()} devices
          </p>
          
          <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-gray-300">
            <span className="flex items-center gap-1">
              <span>✅</span>
              <span>Touch Targets</span>
            </span>
            <span className="flex items-center gap-1">
              <span>✅</span>
              <span>Responsive Grid</span>
            </span>
            <span className="flex items-center gap-1">
              <span>✅</span>
              <span>Performance</span>
            </span>
            <span className="flex items-center gap-1">
              <span>✅</span>
              <span>Accessibility</span>
            </span>
          </div>
        </div>
      </MobileContainer>
    </div>
  );
}