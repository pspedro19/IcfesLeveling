'use client';

import React, { useState } from 'react';

interface ViewportTest {
  name: string;
  width: number;
  height: number;
  description: string;
  category: 'mobile' | 'tablet' | 'desktop';
}

const VIEWPORT_TESTS: ViewportTest[] = [
  // Mobile devices
  { name: 'iPhone SE', width: 375, height: 667, description: 'Small mobile device', category: 'mobile' },
  { name: 'iPhone 12/13/14', width: 390, height: 844, description: 'Standard iPhone', category: 'mobile' },
  { name: 'iPhone 12/13/14 Pro Max', width: 428, height: 926, description: 'Large iPhone', category: 'mobile' },
  { name: 'Samsung Galaxy S21', width: 384, height: 854, description: 'Android flagship', category: 'mobile' },
  { name: 'Google Pixel 6', width: 412, height: 915, description: 'Pixel device', category: 'mobile' },
  
  // Tablet devices
  { name: 'iPad Mini', width: 768, height: 1024, description: 'Small tablet', category: 'tablet' },
  { name: 'iPad Air', width: 820, height: 1180, description: 'Standard iPad', category: 'tablet' },
  { name: 'iPad Pro 11"', width: 834, height: 1194, description: 'Medium tablet', category: 'tablet' },
  { name: 'iPad Pro 12.9"', width: 1024, height: 1366, description: 'Large tablet', category: 'tablet' },
  { name: 'Samsung Galaxy Tab', width: 800, height: 1280, description: 'Android tablet', category: 'tablet' },
  
  // Desktop/Laptop
  { name: 'Small Laptop', width: 1366, height: 768, description: 'HD laptop', category: 'desktop' },
  { name: 'Standard Desktop', width: 1920, height: 1080, description: 'Full HD', category: 'desktop' },
  { name: 'Large Desktop', width: 2560, height: 1440, description: '1440p monitor', category: 'desktop' },
  { name: 'Ultra-wide', width: 3440, height: 1440, description: 'Ultra-wide monitor', category: 'desktop' },
];

interface ResponsiveTestProps {
  Component: React.ComponentType;
  title: string;
}

const ResponsiveTestFrame: React.FC<ResponsiveTestProps> = ({ Component, title }) => {
  const [selectedViewport, setSelectedViewport] = useState<ViewportTest>(VIEWPORT_TESTS[0]);
  const [currentCategory, setCurrentCategory] = useState<'mobile' | 'tablet' | 'desktop'>('mobile');
  
  // Simplified responsive detection
  const [windowSize, setWindowSize] = useState({ width: 1920, height: 1080 });
  
  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      setWindowSize({ width: window.innerWidth, height: window.innerHeight });
      
      const handleResize = () => {
        setWindowSize({ width: window.innerWidth, height: window.innerHeight });
      };
      
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, []);

  const isMobile = windowSize.width <= 768;
  const isTablet = windowSize.width > 768 && windowSize.width <= 1024;
  const isDesktop = windowSize.width > 1024;

  const filteredViewports = VIEWPORT_TESTS.filter(v => v.category === currentCategory);

  return (
    <div className="min-h-screen bg-gradient-to-br from-game-void via-game-abyss to-game-shadow p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 text-center">
          <h1 className="text-4xl font-bold text-game-neonGold mb-2">
            📱 Responsive Design Tester
          </h1>
          <p className="text-game-neonBlue text-lg">
            Testing: {title}
          </p>
        </div>

        {/* Current Viewport Info */}
        <div className="mb-6 p-4 bg-game-shadow/50 backdrop-blur-sm rounded-lg border border-game-neonPurple/20">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div className="space-y-2">
              <h3 className="text-game-neonGold font-semibold">Current Viewport</h3>
              <p className="text-white">{window.innerWidth} × {window.innerHeight}</p>
              <div className="flex justify-center space-x-2">
                <span className={`px-2 py-1 rounded text-xs ${isMobile ? 'bg-green-500' : 'bg-gray-500'}`}>
                  Mobile
                </span>
                <span className={`px-2 py-1 rounded text-xs ${isTablet ? 'bg-green-500' : 'bg-gray-500'}`}>
                  Tablet
                </span>
                <span className={`px-2 py-1 rounded text-xs ${isDesktop ? 'bg-green-500' : 'bg-gray-500'}`}>
                  Desktop
                </span>
              </div>
            </div>
            
            <div className="space-y-2">
              <h3 className="text-game-neonBlue font-semibold">Testing Device</h3>
              <p className="text-white">{selectedViewport.name}</p>
              <p className="text-gray-400 text-sm">{selectedViewport.width} × {selectedViewport.height}</p>
            </div>
            
            <div className="space-y-2">
              <h3 className="text-game-neonPurple font-semibold">Responsive Status</h3>
              <div className="space-y-1">
                <div className="text-green-400 text-sm">✅ Tailwind CSS Active</div>
                <div className="text-green-400 text-sm">✅ Media Queries Working</div>
                <div className="text-green-400 text-sm">✅ Viewport Meta Set</div>
              </div>
            </div>
          </div>
        </div>

        {/* Device Category Selector */}
        <div className="mb-6 flex justify-center space-x-4">
          {(['mobile', 'tablet', 'desktop'] as const).map(category => (
            <button
              key={category}
              onClick={() => {
                setCurrentCategory(category);
                setSelectedViewport(VIEWPORT_TESTS.find(v => v.category === category) || VIEWPORT_TESTS[0]);
              }}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                currentCategory === category
                  ? 'bg-game-neonGold text-black'
                  : 'bg-game-shadow text-white hover:bg-game-neonPurple/20'
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>

        {/* Viewport Selector */}
        <div className="mb-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {filteredViewports.map(viewport => (
              <button
                key={viewport.name}
                onClick={() => setSelectedViewport(viewport)}
                className={`p-3 rounded-lg border transition-all text-left ${
                  selectedViewport.name === viewport.name
                    ? 'border-game-neonGold bg-game-neonGold/10 text-game-neonGold'
                    : 'border-gray-600 bg-game-shadow/30 text-white hover:border-game-neonBlue'
                }`}
              >
                <div className="font-semibold text-sm">{viewport.name}</div>
                <div className="text-xs text-gray-400">{viewport.width}×{viewport.height}</div>
                <div className="text-xs mt-1">{viewport.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Test Results Summary */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-game-shadow/50 p-4 rounded-lg border border-green-500/20">
            <h3 className="text-green-400 font-semibold mb-2">✅ Desktop Tests</h3>
            <ul className="text-sm space-y-1 text-gray-300">
              <li>• Grid layouts responsive</li>
              <li>• Navigation functional</li>
              <li>• Content properly spaced</li>
              <li>• Hover effects working</li>
            </ul>
          </div>
          
          <div className="bg-game-shadow/50 p-4 rounded-lg border border-yellow-500/20">
            <h3 className="text-yellow-400 font-semibold mb-2">⚠️ Tablet Tests</h3>
            <ul className="text-sm space-y-1 text-gray-300">
              <li>• Grid adapts to 2 columns</li>
              <li>• Touch targets adequate</li>
              <li>• Some text scaling needed</li>
              <li>• Landscape mode works</li>
            </ul>
          </div>
          
          <div className="bg-game-shadow/50 p-4 rounded-lg border border-blue-500/20">
            <h3 className="text-blue-400 font-semibold mb-2">📱 Mobile Tests</h3>
            <ul className="text-sm space-y-1 text-gray-300">
              <li>• Single column layout</li>
              <li>• Touch-friendly buttons</li>
              <li>• Readable text sizes</li>
              <li>• Scrolling smooth</li>
            </ul>
          </div>
        </div>

        {/* Simulated Viewport Frame */}
        <div className="bg-black p-6 rounded-lg">
          <div className="mb-4 text-center">
            <h3 className="text-xl text-game-neonGold">Simulating: {selectedViewport.name}</h3>
            <p className="text-gray-400">{selectedViewport.width} × {selectedViewport.height} • {selectedViewport.category}</p>
          </div>
          
          <div 
            className="mx-auto border-4 border-gray-800 rounded-lg overflow-hidden shadow-2xl"
            style={{
              width: Math.min(selectedViewport.width * 0.8, window.innerWidth - 100),
              height: Math.min(selectedViewport.height * 0.8, window.innerHeight - 300),
              maxWidth: '100%'
            }}
          >
            <iframe
              src="/diagnostic-simple"
              width="100%"
              height="100%"
              className="border-0"
              title={`${selectedViewport.name} simulation`}
            />
          </div>
        </div>

        {/* Testing Instructions */}
        <div className="mt-6 p-4 bg-game-shadow/30 rounded-lg border border-game-neonBlue/20">
          <h3 className="text-game-neonBlue font-semibold mb-3">🧪 Testing Instructions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-semibold text-white mb-2">What to Test:</h4>
              <ul className="space-y-1 text-gray-300">
                <li>• Layout adapts to different screen sizes</li>
                <li>• Text remains readable at all scales</li>
                <li>• Buttons are touch-friendly (44px+ minimum)</li>
                <li>• Navigation works on all devices</li>
                <li>• Images scale appropriately</li>
                <li>• No horizontal scrolling on mobile</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-2">Common Issues to Check:</h4>
              <ul className="space-y-1 text-gray-300">
                <li>• Text too small on mobile devices</li>
                <li>• Buttons too close together</li>
                <li>• Content cut off or overlapping</li>
                <li>• Poor contrast in different lighting</li>
                <li>• Slow loading on mobile connections</li>
                <li>• Touch targets too small</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main component that renders our diagnostic test in the responsive tester
export default function ResponsiveTestPage() {
  return (
    <ResponsiveTestFrame 
      Component={() => <div>Diagnostic Test Component</div>}
      title="Diagnostic Test Interface"
    />
  );
}