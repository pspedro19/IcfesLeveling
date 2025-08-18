'use client';

import React, { useState } from 'react';

export default function TestLoginPage() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testLogin = async () => {
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', 'admin');
      formData.append('password', 'secret');

      const response = await fetch('http://localhost:4000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      const data = await response.json();
      setResult({
        status: response.status,
        ok: response.ok,
        data: data
      });

      if (response.ok) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
      }
    } catch (error) {
      setResult({
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-3xl font-bold mb-8">Test Login</h1>
      
      <div className="bg-gray-800 p-6 rounded-lg mb-4">
        <h2 className="text-xl mb-4">Test Credentials:</h2>
        <p>Username: admin</p>
        <p>Password: secret</p>
      </div>

      <button
        onClick={testLogin}
        disabled={loading}
        className="bg-blue-500 hover:bg-blue-600 px-6 py-3 rounded-lg font-bold disabled:opacity-50"
      >
        {loading ? 'Testing...' : 'Test Login'}
      </button>

      {result && (
        <div className="mt-8 bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl mb-4">Result:</h2>
          <pre className="whitespace-pre-wrap overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}