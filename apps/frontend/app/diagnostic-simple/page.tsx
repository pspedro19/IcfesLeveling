'use client';

import { useState, useEffect } from 'react';

export default function DiagnosticSimple() {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadSubjects = async () => {
      try {
        console.log('🚀 Loading subjects...');
        const response = await fetch('http://localhost:4001/api/v1/diagnostic-public/subjects');
        
        if (response.ok) {
          const data = await response.json();
          console.log('✅ Subjects loaded:', data);
          setSubjects(data);
        } else {
          setError(`Failed to load: ${response.status}`);
        }
      } catch (err: any) {
        console.error('❌ Error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadSubjects();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl mb-4">🔄 Loading Subjects...</h1>
          <p>Testing diagnostic page functionality</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl mb-4 text-red-400">❌ Error</h1>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black to-purple-900 text-white">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gold-500 mb-4">
            ✅ DIAGNOSTIC TEST - WORKING!
          </h1>
          <p className="text-xl text-purple-300">
            Found {subjects.length} subjects
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {subjects.map((subject: any) => (
            <div 
              key={subject.id}
              className="bg-black/40 backdrop-blur-sm border border-purple-500 rounded-lg p-6 hover:shadow-[0_0_20px_#ffd700] transition-all cursor-pointer transform hover:scale-105"
              onClick={() => alert(`Starting diagnostic for ${subject.name}!`)}
            >
              <div className="text-center">
                <div 
                  className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center text-2xl"
                  style={{ backgroundColor: subject.color }}
                >
                  📚
                </div>
                <h3 className="text-xl font-semibold text-gold-500 mb-2">
                  {subject.name}
                </h3>
                <p className="text-purple-300 mb-4 text-sm">
                  {subject.description}
                </p>
                <div className="space-y-2 text-sm text-gray-400 mb-4">
                  <div className="flex justify-between">
                    <span>⚔️ Questions:</span>
                    <span className="font-medium text-purple-300">
                      {subject.config.total_questions}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>⏱️ Time:</span>
                    <span className="font-medium text-purple-300">
                      {subject.config.time_limit_minutes} min
                    </span>
                  </div>
                </div>
                <button className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-2 px-4 rounded transition-colors">
                  🚀 Start Diagnostic
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 text-center">
          <p className="text-green-400">
            ✅ Diagnostic page is working! You can now start tests.
          </p>
        </div>
      </div>
    </div>
  );
}