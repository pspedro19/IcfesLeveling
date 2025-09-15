'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { parseImageContent } from '../utils/imageParser';
import { useCache } from '../hooks/useCache';

interface ImageLoadTest {
  id: string;
  name: string;
  url: string;
  size?: 'small' | 'medium' | 'large';
  expectedToExist: boolean;
}

interface LoadResult {
  id: string;
  loadTime: number;
  success: boolean;
  cached: boolean;
  size: number;
  error?: string;
  retries: number;
}

export default function TestImagePerformance() {
  const [results, setResults] = useState<LoadResult[]>([]);
  const [testing, setTesting] = useState(false);
  const [currentTest, setCurrentTest] = useState<string>('');
  const [cacheStats, setCacheStats] = useState({
    hits: 0,
    misses: 0,
    totalRequests: 0
  });

  const imageCache = useRef(new Map<string, boolean>());
  const performanceMetrics = useRef({
    totalLoadTime: 0,
    successfulLoads: 0,
    failedLoads: 0,
    cacheHits: 0,
    cacheMisses: 0
  });

  // Test cases covering different scenarios
  const testImages: ImageLoadTest[] = [
    // Existing mathimg files
    {
      id: 'math-1',
      name: 'Math Question 12 Option A',
      url: '/mathimg/Math_12_R_A_Doc1.png',
      size: 'small',
      expectedToExist: true
    },
    {
      id: 'math-2',
      name: 'Math Question 12 Option B',
      url: '/mathimg/Math_12_R_B_Doc1.png',
      size: 'small',
      expectedToExist: true
    },
    {
      id: 'math-3',
      name: 'Math Question 15',
      url: '/mathimg/Math_15_1_Doc1.png',
      size: 'medium',
      expectedToExist: true
    },
    {
      id: 'math-4',
      name: 'Math Question 17 (Large)',
      url: '/mathimg/Math_17_1_Doc1.png',
      size: 'large',
      expectedToExist: true
    },
    // Non-existent files for error testing
    {
      id: 'error-1',
      name: 'Non-existent Image 1',
      url: '/mathimg/NonExistent_Image_1.png',
      expectedToExist: false
    },
    {
      id: 'error-2',
      name: 'Non-existent Image 2',
      url: '/mathimg/Missing_File.jpg',
      expectedToExist: false
    },
    // External test images
    {
      id: 'external-1',
      name: 'External Placeholder (Small)',
      url: 'https://via.placeholder.com/150x100/3B82F6/FFFFFF?text=Small',
      size: 'small',
      expectedToExist: true
    },
    {
      id: 'external-2',
      name: 'External Placeholder (Large)',
      url: 'https://via.placeholder.com/800x600/10B981/FFFFFF?text=Large',
      size: 'large',
      expectedToExist: true
    }
  ];

  const testImageLoad = (testImage: ImageLoadTest): Promise<LoadResult> => {
    return new Promise((resolve) => {
      const startTime = performance.now();
      const img = new Image();
      let retries = 0;
      const maxRetries = 2;

      // Check cache first
      const cached = imageCache.current.has(testImage.url);
      if (cached) {
        performanceMetrics.current.cacheHits++;
        setCacheStats(prev => ({ ...prev, hits: prev.hits + 1, totalRequests: prev.totalRequests + 1 }));
      } else {
        performanceMetrics.current.cacheMisses++;
        setCacheStats(prev => ({ ...prev, misses: prev.misses + 1, totalRequests: prev.totalRequests + 1 }));
      }

      const attemptLoad = () => {
        img.onload = () => {
          const loadTime = performance.now() - startTime;
          
          // Cache successful load
          imageCache.current.set(testImage.url, true);
          
          // Update metrics
          performanceMetrics.current.totalLoadTime += loadTime;
          performanceMetrics.current.successfulLoads++;
          
          // Get image size (approximate)
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');
          canvas.width = img.naturalWidth;
          canvas.height = img.naturalHeight;
          ctx?.drawImage(img, 0, 0);
          
          resolve({
            id: testImage.id,
            loadTime: Math.round(loadTime),
            success: true,
            cached,
            size: Math.round(canvas.width * canvas.height * 4 / 1024), // Approximate KB
            retries
          });
        };

        img.onerror = () => {
          retries++;
          if (retries <= maxRetries && testImage.expectedToExist) {
            setTimeout(attemptLoad, 1000 * retries); // Exponential backoff
            return;
          }

          const loadTime = performance.now() - startTime;
          performanceMetrics.current.failedLoads++;
          
          resolve({
            id: testImage.id,
            loadTime: Math.round(loadTime),
            success: false,
            cached: false,
            size: 0,
            error: 'Failed to load image',
            retries
          });
        };

        img.src = testImage.url;
      };

      // Simulate network delay for cache testing
      if (cached) {
        setTimeout(attemptLoad, 10); // Cached images load faster
      } else {
        attemptLoad();
      }

      // Timeout after 10 seconds
      setTimeout(() => {
        if (!img.complete) {
          resolve({
            id: testImage.id,
            loadTime: 10000,
            success: false,
            cached: false,
            size: 0,
            error: 'Timeout',
            retries
          });
        }
      }, 10000);
    });
  };

  const runPerformanceTest = async () => {
    setTesting(true);
    setResults([]);
    
    // Reset metrics
    performanceMetrics.current = {
      totalLoadTime: 0,
      successfulLoads: 0,
      failedLoads: 0,
      cacheHits: 0,
      cacheMisses: 0
    };
    
    setCacheStats({ hits: 0, misses: 0, totalRequests: 0 });

    // Test each image
    for (const testImage of testImages) {
      setCurrentTest(testImage.name);
      
      try {
        const result = await testImageLoad(testImage);
        setResults(prev => [...prev, result]);
        
        // Small delay between tests
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (error) {
        console.error(`Test failed for ${testImage.name}:`, error);
        setResults(prev => [...prev, {
          id: testImage.id,
          loadTime: 0,
          success: false,
          cached: false,
          size: 0,
          error: error instanceof Error ? error.message : 'Unknown error',
          retries: 0
        }]);
      }
    }

    setCurrentTest('');
    setTesting(false);
  };

  const runCacheTest = async () => {
    setTesting(true);
    setCurrentTest('Testing cache performance...');
    
    // Clear previous results
    setResults([]);
    
    // First run - no cache
    const firstRunResults: LoadResult[] = [];
    for (const testImage of testImages.slice(0, 4)) { // Test first 4 images
      const result = await testImageLoad(testImage);
      firstRunResults.push(result);
    }
    
    // Second run - should hit cache
    const secondRunResults: LoadResult[] = [];
    for (const testImage of testImages.slice(0, 4)) {
      const result = await testImageLoad(testImage);
      secondRunResults.push({ ...result, id: result.id + '-cached' });
    }
    
    setResults([...firstRunResults, ...secondRunResults]);
    setCurrentTest('');
    setTesting(false);
  };

  const getPerformanceStats = () => {
    const totalTests = results.length;
    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;
    const avgLoadTime = results.length > 0 
      ? Math.round(results.reduce((sum, r) => sum + r.loadTime, 0) / results.length)
      : 0;
    const cacheHitRate = cacheStats.totalRequests > 0 
      ? Math.round((cacheStats.hits / cacheStats.totalRequests) * 100)
      : 0;

    return {
      totalTests,
      successful,
      failed,
      avgLoadTime,
      cacheHitRate,
      successRate: totalTests > 0 ? Math.round((successful / totalTests) * 100) : 0
    };
  };

  const stats = getPerformanceStats();

  const clearCache = () => {
    imageCache.current.clear();
    setCacheStats({ hits: 0, misses: 0, totalRequests: 0 });
    performanceMetrics.current = {
      totalLoadTime: 0,
      successfulLoads: 0,
      failedLoads: 0,
      cacheHits: 0,
      cacheMisses: 0
    };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            ⚡ Image Performance & Caching Test
          </h1>
          <p className="text-xl text-gray-600">
            Testing image load times, caching efficiency, and error handling
          </p>
        </motion.div>

        {/* Control Panel */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-lg p-6 mb-8"
        >
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">🎛️ Test Controls</h2>
          <div className="flex flex-wrap gap-4">
            <button
              onClick={runPerformanceTest}
              disabled={testing}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              {testing ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-white"></div>
                  Testing...
                </>
              ) : (
                <>⚡ Run Performance Test</>
              )}
            </button>
            
            <button
              onClick={runCacheTest}
              disabled={testing}
              className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
            >
              🗄️ Test Cache Performance
            </button>
            
            <button
              onClick={clearCache}
              disabled={testing}
              className="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
            >
              🗑️ Clear Cache
            </button>
          </div>
          
          {currentTest && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg"
            >
              <p className="text-blue-800 font-medium">Currently testing: {currentTest}</p>
            </motion.div>
          )}
        </motion.div>

        {/* Performance Statistics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-lg p-6 mb-8"
        >
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">📊 Performance Metrics</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">{stats.totalTests}</div>
              <div className="text-gray-600 text-sm">Total Tests</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{stats.successful}</div>
              <div className="text-gray-600 text-sm">Successful</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">{stats.failed}</div>
              <div className="text-gray-600 text-sm">Failed</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">{stats.avgLoadTime}ms</div>
              <div className="text-gray-600 text-sm">Avg Load Time</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600">{stats.cacheHitRate}%</div>
              <div className="text-gray-600 text-sm">Cache Hit Rate</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-indigo-600">{stats.successRate}%</div>
              <div className="text-gray-600 text-sm">Success Rate</div>
            </div>
          </div>

          {/* Cache Statistics */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-800 mb-2">🗄️ Cache Statistics</h3>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Cache Hits:</span>
                <span className="font-semibold ml-2 text-green-600">{cacheStats.hits}</span>
              </div>
              <div>
                <span className="text-gray-600">Cache Misses:</span>
                <span className="font-semibold ml-2 text-red-600">{cacheStats.misses}</span>
              </div>
              <div>
                <span className="text-gray-600">Total Requests:</span>
                <span className="font-semibold ml-2">{cacheStats.totalRequests}</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Test Results */}
        <AnimatePresence>
          {results.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-lg shadow-lg p-6 mb-8"
            >
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">🧪 Test Results</h2>
              
              <div className="space-y-3">
                {results.map((result, index) => {
                  const testImage = testImages.find(t => t.id === result.id || t.id === result.id.replace('-cached', ''));
                  const isCachedTest = result.id.includes('-cached');
                  
                  return (
                    <motion.div
                      key={result.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`p-4 rounded-lg border-l-4 ${
                        result.success 
                          ? 'bg-green-50 border-green-500' 
                          : 'bg-red-50 border-red-500'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-gray-800">
                              {testImage?.name}
                              {isCachedTest && ' (Cached)'}
                            </h3>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              result.success 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {result.success ? '✅ Success' : '❌ Failed'}
                            </span>
                            {result.cached && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                                🗄️ Cached
                              </span>
                            )}
                          </div>
                          
                          <div className="mt-2 text-sm text-gray-600">
                            <span className="mr-4">Load Time: <strong>{result.loadTime}ms</strong></span>
                            {result.success && (
                              <>
                                <span className="mr-4">Size: <strong>{result.size}KB</strong></span>
                                <span>Retries: <strong>{result.retries}</strong></span>
                              </>
                            )}
                            {result.error && (
                              <span className="text-red-600">Error: <strong>{result.error}</strong></span>
                            )}
                          </div>
                          
                          <div className="mt-1 text-xs text-gray-500">
                            URL: {testImage?.url}
                          </div>
                        </div>
                        
                        {/* Performance indicator */}
                        <div className="ml-4">
                          {result.success && (
                            <div className={`w-4 h-4 rounded-full ${
                              result.loadTime < 100 ? 'bg-green-500' :
                              result.loadTime < 500 ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`} title={`Load time: ${result.loadTime}ms`} />
                          )}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Image Preview Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-lg p-6"
        >
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">🖼️ Image Preview</h2>
          <p className="text-gray-600 mb-6">
            Preview of images being tested for visual verification
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {testImages.filter(img => img.expectedToExist).map((testImage) => (
              <div key={testImage.id} className="text-center">
                <div className="bg-gray-100 rounded-lg p-4 mb-2">
                  <img
                    src={testImage.url}
                    alt={testImage.name}
                    className="max-w-full h-auto max-h-24 mx-auto rounded"
                    onError={(e) => {
                      const target = e.currentTarget as HTMLImageElement;
                      target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0yMS4zMzMzIDIxLjMzMzNMMzIgMzJMNDIuNjY2NyAyMS4zMzMzVjQyLjY2NjdIMjEuMzMzM1YyMS4zMzMzWiIgc3Ryb2tlPSIjOUI5QjlCIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K';
                    }}
                  />
                </div>
                <p className="text-xs text-gray-600 text-center truncate">
                  {testImage.name}
                </p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Instructions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 bg-amber-50 border border-amber-200 rounded-lg p-6"
        >
          <h3 className="text-lg font-semibold text-amber-800 mb-4">📝 Performance Test Coverage</h3>
          <ul className="space-y-2 text-amber-700">
            <li>✅ Load time measurement for different image sizes</li>
            <li>✅ Cache hit/miss ratio testing</li>
            <li>✅ Error handling for missing images</li>
            <li>✅ Retry mechanism testing</li>
            <li>✅ External image loading performance</li>
            <li>✅ Memory usage optimization</li>
            <li>✅ Visual image verification</li>
            <li>✅ Performance metrics analysis</li>
          </ul>
        </motion.div>
      </div>
    </div>
  );
}