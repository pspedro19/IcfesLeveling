'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { parseImageContent } from '../utils/imageParser';

interface ImageTestResult {
  format: string;
  input: string;
  result: 'success' | 'error' | 'pending';
  imageUrl?: string;
  errorMessage?: string;
  loadTime?: number;
}

export default function TestMultimediaComprehensive() {
  const [testResults, setTestResults] = useState<ImageTestResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [serverStatus, setServerStatus] = useState({
    frontend: 'checking',
    mathimg: 'checking'
  });

  // Comprehensive test cases covering all image format scenarios
  const testCases = [
    {
      format: 'Bracket Format - Basic',
      input: '[Imagen: /mathimg/Math_12_R_A_Doc1.png]'
    },
    {
      format: 'Bracket Format - With Spaces',
      input: '[Imagen:    /mathimg/Math_12_R_B_Doc1.png   ]'
    },
    {
      format: 'Direct Path - mathimg',
      input: '/mathimg/Math_12_R_C_Doc1.png'
    },
    {
      format: 'Windows Path Conversion',
      input: 'C:\\Users\\PEDRO_PEREZ\\Documents\\IcfesLeveling\\mathimg\\Math_12_R_D_Doc1.png'
    },
    {
      format: 'Mixed Content - Text + Image',
      input: 'La respuesta correcta es [Imagen: /mathimg/Math_15_1_Doc1.png] según el gráfico mostrado.'
    },
    {
      format: 'Multiple Images',
      input: 'Opción A: /mathimg/Math_1_1_Doc1.png y Opción B: /mathimg/Math_17_1_Doc1.png'
    },
    {
      format: 'URL Format - HTTPS',
      input: 'https://via.placeholder.com/300x200/0066CC/FFFFFF?text=Test+Image'
    },
    {
      format: 'Markdown Format',
      input: '![Descripción de imagen](/mathimg/Math_12_R_A_Doc1.png)'
    },
    {
      format: 'Non-existent Image',
      input: '[Imagen: /mathimg/NonExistent_Image.png]'
    },
    {
      format: 'Invalid Format',
      input: 'Just plain text without any image'
    }
  ];

  useEffect(() => {
    testImageProcessing();
    checkServerStatus();
  }, []);

  const checkServerStatus = async () => {
    try {
      // Check if mathimg directory is accessible
      const mathimgResponse = await fetch('/mathimg/Math_12_R_A_Doc1.png');
      setServerStatus(prev => ({
        ...prev,
        mathimg: mathimgResponse.ok ? 'online' : 'offline'
      }));
    } catch (error) {
      setServerStatus(prev => ({ ...prev, mathimg: 'offline' }));
    }

    setServerStatus(prev => ({ ...prev, frontend: 'online' }));
  };

  const testImageProcessing = async () => {
    setLoading(true);
    const results: ImageTestResult[] = [];

    for (const testCase of testCases) {
      const startTime = Date.now();
      try {
        const parsed = parseImageContent(testCase.input);
        
        // Test actual image loading if it's an image type
        if (parsed.type === 'image' || parsed.type === 'mixed') {
          const imageUrl = extractImageUrl(testCase.input);
          if (imageUrl) {
            try {
              const imageLoadTest = await testImageLoad(imageUrl);
              results.push({
                format: testCase.format,
                input: testCase.input,
                result: imageLoadTest ? 'success' : 'error',
                imageUrl,
                loadTime: Date.now() - startTime,
                errorMessage: imageLoadTest ? undefined : 'Image failed to load'
              });
            } catch (error) {
              results.push({
                format: testCase.format,
                input: testCase.input,
                result: 'error',
                imageUrl,
                loadTime: Date.now() - startTime,
                errorMessage: error instanceof Error ? error.message : 'Unknown error'
              });
            }
          } else {
            results.push({
              format: testCase.format,
              input: testCase.input,
              result: parsed.type !== 'text' ? 'success' : 'error',
              loadTime: Date.now() - startTime,
              errorMessage: parsed.type === 'text' ? 'No image detected' : undefined
            });
          }
        } else {
          results.push({
            format: testCase.format,
            input: testCase.input,
            result: testCase.format.includes('Invalid') || testCase.format.includes('Non-existent') ? 'success' : 'error',
            loadTime: Date.now() - startTime,
            errorMessage: parsed.type === 'text' ? 'Correctly identified as text-only' : undefined
          });
        }
      } catch (error) {
        results.push({
          format: testCase.format,
          input: testCase.input,
          result: 'error',
          loadTime: Date.now() - startTime,
          errorMessage: error instanceof Error ? error.message : 'Parser error'
        });
      }
    }

    setTestResults(results);
    setLoading(false);
  };

  const extractImageUrl = (input: string): string | null => {
    // Extract URL from different formats
    const bracketMatch = input.match(/\[Imagen:\s*([^\]]+)\]/i);
    if (bracketMatch) return bracketMatch[1].trim();

    const pathMatch = input.match(/(\/mathimg\/[^\s,'"]+\.(png|jpg|jpeg|gif))/i);
    if (pathMatch) return pathMatch[1];

    const windowsMatch = input.match(/([A-Z]:\\[^\s,'"]+\.(png|jpg|jpeg|gif))/i);
    if (windowsMatch) {
      const filename = windowsMatch[1].split(/[\\\/]/).pop();
      return `/mathimg/${filename}`;
    }

    const urlMatch = input.match(/(https?:\/\/[^\s,'"]+\.(png|jpg|jpeg|gif))/i);
    if (urlMatch) return urlMatch[1];

    const markdownMatch = input.match(/!\[[^\]]*\]\(([^)]+)\)/);
    if (markdownMatch) return markdownMatch[1];

    return null;
  };

  const testImageLoad = (imageUrl: string): Promise<boolean> => {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve(true);
      img.onerror = () => resolve(false);
      img.src = imageUrl;
      
      // Timeout after 5 seconds
      setTimeout(() => resolve(false), 5000);
    });
  };

  const renderTestCase = (testCase: any, result: ImageTestResult) => {
    const parsed = parseImageContent(testCase.input);
    
    return (
      <motion.div
        key={testCase.format}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-blue-500"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800">{testCase.format}</h3>
          <div className="flex items-center gap-2">
            {result.result === 'success' && (
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                ✅ Success
              </span>
            )}
            {result.result === 'error' && (
              <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">
                ❌ Error
              </span>
            )}
            {result.result === 'pending' && (
              <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                ⏳ Testing...
              </span>
            )}
            {result.loadTime && (
              <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                {result.loadTime}ms
              </span>
            )}
          </div>
        </div>

        {/* Input Text */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-600 mb-2">Input:</h4>
          <code className="block p-3 bg-gray-100 rounded text-sm font-mono break-all">
            {testCase.input}
          </code>
        </div>

        {/* Parsed Result */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-600 mb-2">
            Parsed Result (Type: {parsed.type}):
          </h4>
          <div className="p-3 bg-gray-50 rounded border">
            {parsed.content}
          </div>
        </div>

        {/* Image URL if detected */}
        {result.imageUrl && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-600 mb-2">Detected Image URL:</h4>
            <code className="block p-2 bg-blue-50 rounded text-sm text-blue-800">
              {result.imageUrl}
            </code>
          </div>
        )}

        {/* Error Message */}
        {result.errorMessage && (
          <div className="p-3 bg-red-50 border border-red-200 rounded">
            <h4 className="text-sm font-medium text-red-800 mb-1">Error:</h4>
            <p className="text-sm text-red-600">{result.errorMessage}</p>
          </div>
        )}
      </motion.div>
    );
  };

  const getTestStats = () => {
    const total = testResults.length;
    const success = testResults.filter(r => r.result === 'success').length;
    const errors = testResults.filter(r => r.result === 'error').length;
    const avgLoadTime = testResults.reduce((sum, r) => sum + (r.loadTime || 0), 0) / total;
    
    return { total, success, errors, avgLoadTime: Math.round(avgLoadTime) };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-500 mx-auto mb-4"></div>
          <p className="text-xl text-gray-700">Testing multimedia content handling...</p>
          <p className="text-gray-500 mt-2">Running comprehensive image tests</p>
        </motion.div>
      </div>
    );
  }

  const stats = getTestStats();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            🖼️ Comprehensive Multimedia Content Testing
          </h1>
          <p className="text-xl text-gray-600">
            Testing image path verification, loading, and rendering across all supported formats
          </p>
        </motion.div>

        {/* Server Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-lg p-6 mb-8"
        >
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">🌐 Server Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Frontend Server:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                serverStatus.frontend === 'online' ? 'bg-green-100 text-green-800' : 
                serverStatus.frontend === 'offline' ? 'bg-red-100 text-red-800' : 
                'bg-yellow-100 text-yellow-800'
              }`}>
                {serverStatus.frontend === 'online' ? '✅ Online' : 
                 serverStatus.frontend === 'offline' ? '❌ Offline' : '🔄 Checking...'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">MathImg Assets:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                serverStatus.mathimg === 'online' ? 'bg-green-100 text-green-800' : 
                serverStatus.mathimg === 'offline' ? 'bg-red-100 text-red-800' : 
                'bg-yellow-100 text-yellow-800'
              }`}>
                {serverStatus.mathimg === 'online' ? '✅ Accessible' : 
                 serverStatus.mathimg === 'offline' ? '❌ Not Accessible' : '🔄 Checking...'}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Test Statistics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-lg p-6 mb-8"
        >
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">📊 Test Results Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">{stats.total}</div>
              <div className="text-gray-600">Total Tests</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{stats.success}</div>
              <div className="text-gray-600">Successful</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">{stats.errors}</div>
              <div className="text-gray-600">Failed</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">{stats.avgLoadTime}ms</div>
              <div className="text-gray-600">Avg Load Time</div>
            </div>
          </div>
          
          {/* Success Rate Bar */}
          <div className="mt-6">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Success Rate</span>
              <span>{Math.round((stats.success / stats.total) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <motion.div
                className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${(stats.success / stats.total) * 100}%` }}
                transition={{ duration: 1, delay: 0.5 }}
              />
            </div>
          </div>
        </motion.div>

        {/* Test Cases */}
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold text-gray-800">🧪 Individual Test Results</h2>
          {testCases.map((testCase, index) => {
            const result = testResults[index] || { 
              format: testCase.format, 
              input: testCase.input, 
              result: 'pending' as const 
            };
            return renderTestCase(testCase, result);
          })}
        </div>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 text-center space-x-4"
        >
          <button
            onClick={testImageProcessing}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            🔄 Re-run Tests
          </button>
          <button
            onClick={checkServerStatus}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
          >
            🌐 Check Server Status
          </button>
        </motion.div>

        {/* Instructions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 bg-amber-50 border border-amber-200 rounded-lg p-6"
        >
          <h3 className="text-lg font-semibold text-amber-800 mb-4">📝 Test Coverage</h3>
          <ul className="space-y-2 text-amber-700">
            <li>✅ Bracket format image parsing: [Imagen: /path/image.png]</li>
            <li>✅ Direct path format: /mathimg/image.png</li>
            <li>✅ Windows path conversion: C:\\path\\image.png → /mathimg/image.png</li>
            <li>✅ Mixed content handling: text + images</li>
            <li>✅ Multiple image detection</li>
            <li>✅ URL format support: https://...</li>
            <li>✅ Markdown format: ![alt](/path/image.png)</li>
            <li>✅ Error handling for missing images</li>
            <li>✅ Loading time measurement</li>
            <li>✅ Server accessibility verification</li>
          </ul>
        </motion.div>
      </div>
    </div>
  );
}