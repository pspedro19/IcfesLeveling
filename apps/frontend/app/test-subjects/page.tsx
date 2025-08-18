'use client';

import React, { useState, useEffect } from 'react';

export default function TestSubjectsPage() {
  const [subjects, setSubjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSubjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:4000/api/v1/diagnostic/subjects');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSubjects(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSubjects();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-3xl font-bold mb-8">Test Subjects Loading</h1>
      
      <button
        onClick={loadSubjects}
        disabled={loading}
        className="bg-blue-500 hover:bg-blue-600 px-6 py-3 rounded-lg font-bold disabled:opacity-50 mb-8"
      >
        {loading ? 'Loading...' : 'Reload Subjects'}
      </button>

      {error && (
        <div className="bg-red-800 p-4 rounded-lg mb-8">
          <h2 className="text-xl font-bold mb-2">Error:</h2>
          <p>{error}</p>
        </div>
      )}

      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-bold mb-4">Subjects ({subjects.length}):</h2>
        {subjects.length === 0 ? (
          <p>No subjects loaded</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {subjects.map((subject: any) => (
              <div key={subject.id} className="bg-gray-700 p-4 rounded-lg">
                <h3 className="text-lg font-bold" style={{color: subject.color}}>
                  {subject.name}
                </h3>
                <p className="text-sm text-gray-300 mt-2">{subject.description}</p>
                <div className="mt-2 text-xs text-gray-400">
                  <p>Questions: {subject.config?.total_questions}</p>
                  <p>Time: {subject.config?.time_limit_minutes} minutes</p>
                  <p>Topics: {subject.config?.topics?.join(', ') || 'None'}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-8 bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-bold mb-4">Raw JSON:</h2>
        <pre className="whitespace-pre-wrap overflow-auto text-xs">
          {JSON.stringify(subjects, null, 2)}
        </pre>
      </div>
    </div>
  );
}