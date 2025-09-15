'use client';

import React, { useState } from 'react';
import { authService } from '../../services/auth.service';
import { Play, CheckCircle, XCircle, Clock, User, AlertTriangle } from 'lucide-react';

interface TestResult {
  username: string;
  success: boolean;
  error?: string;
  responseTime?: number;
  userInfo?: any;
}

interface TestAccount {
  username: string;
  password: string;
  description: string;
  expectedLevel: number;
  expectedRank: string;
}

export default function LoginTester() {
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [testing, setTesting] = useState(false);
  const [currentTest, setCurrentTest] = useState<string>('');

  const testAccounts: TestAccount[] = [
    { username: 'admin', password: 'secret', description: 'Administrador', expectedLevel: 50, expectedRank: 'S' },
    { username: 'test', password: 'secret', description: 'Usuario de Prueba', expectedLevel: 1, expectedRank: 'E' },
    { username: 'student1', password: 'secret', description: 'Estudiante Activo', expectedLevel: 5, expectedRank: 'D' },
  ];

  const testSingleAccount = async (account: TestAccount): Promise<TestResult> => {
    const startTime = Date.now();
    
    try {
      const response = await authService.login({
        username: account.username,
        password: account.password
      });
      
      const responseTime = Date.now() - startTime;
      
      // Validate response structure
      if (!response.access_token || !response.user) {
        throw new Error('Respuesta incompleta del servidor');
      }
      
      // Validate user data
      const user = response.user;
      if (!user.username || !user.level || !user.rank) {
        throw new Error('Datos de usuario incompletos');
      }
      
      // Check expected values
      if (user.level !== account.expectedLevel) {
        console.warn(`Nivel esperado: ${account.expectedLevel}, recibido: ${user.level}`);
      }
      
      if (user.rank !== account.expectedRank) {
        console.warn(`Rango esperado: ${account.expectedRank}, recibido: ${user.rank}`);
      }
      
      return {
        username: account.username,
        success: true,
        responseTime,
        userInfo: user
      };
      
    } catch (error: any) {
      const responseTime = Date.now() - startTime;
      return {
        username: account.username,
        success: false,
        error: error.message || 'Error desconocido',
        responseTime
      };
    }
  };

  const runAllTests = async () => {
    setTesting(true);
    setTestResults([]);
    
    for (const account of testAccounts) {
      setCurrentTest(account.username);
      
      const result = await testSingleAccount(account);
      
      setTestResults(prev => [...prev, result]);
      
      // Small delay between tests
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    setTesting(false);
    setCurrentTest('');
  };

  const testInvalidCredentials = async () => {
    setTesting(true);
    setCurrentTest('invalid_user');
    
    try {
      await authService.login({ username: 'invalid_user', password: 'wrong_password' });
      // If this succeeds, it's actually an error
      setTestResults(prev => [...prev, {
        username: 'invalid_user',
        success: false,
        error: 'Login con credenciales inválidas fue exitoso (error del sistema)'
      }]);
    } catch (error: any) {
      // This should happen - invalid credentials should fail
      setTestResults(prev => [...prev, {
        username: 'invalid_user',
        success: true,
        error: `Correctamente rechazado: ${error.message}`
      }]);
    }
    
    setTesting(false);
    setCurrentTest('');
  };

  const clearResults = () => {
    setTestResults([]);
  };

  const getResultIcon = (result: TestResult) => {
    if (result.username === 'invalid_user') {
      return result.success ? <CheckCircle className="w-5 h-5 text-green-400" /> : <XCircle className="w-5 h-5 text-red-400" />;
    }
    return result.success ? <CheckCircle className="w-5 h-5 text-green-400" /> : <XCircle className="w-5 h-5 text-red-400" />;
  };

  const getResultColor = (result: TestResult) => {
    if (result.username === 'invalid_user') {
      return result.success ? 'border-green-500/50 bg-green-500/10' : 'border-red-500/50 bg-red-500/10';
    }
    return result.success ? 'border-green-500/50 bg-green-500/10' : 'border-red-500/50 bg-red-500/10';
  };

  const successRate = testResults.length > 0 ? 
    (testResults.filter(r => r.username === 'invalid_user' ? r.success : r.success).length / testResults.length * 100).toFixed(1) : 0;

  return (
    <div className="p-6 bg-gray-900 rounded-lg border border-gray-700">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
          <User className="w-6 h-6 text-purple-400" />
          Login System Tester
        </h2>
        <p className="text-gray-400">
          Prueba automática de todos los usuarios: admin/secret, test/secret, student1/secret
        </p>
      </div>

      {/* Control Buttons */}
      <div className="flex flex-wrap gap-3 mb-6">
        <button
          onClick={runAllTests}
          disabled={testing}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
        >
          {testing ? <Clock className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {testing ? 'Probando...' : 'Probar Todas las Cuentas'}
        </button>
        
        <button
          onClick={testInvalidCredentials}
          disabled={testing}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
        >
          <AlertTriangle className="w-4 h-4" />
          Probar Credenciales Inválidas
        </button>
        
        <button
          onClick={clearResults}
          disabled={testing}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
        >
          Limpiar Resultados
        </button>
      </div>

      {/* Current Test Display */}
      {testing && currentTest && (
        <div className="mb-4 p-3 bg-blue-600/20 border border-blue-500/50 rounded-lg">
          <div className="flex items-center gap-2 text-blue-300">
            <Clock className="w-4 h-4 animate-spin" />
            Probando: <span className="font-mono">{currentTest}</span>
          </div>
        </div>
      )}

      {/* Test Results Summary */}
      {testResults.length > 0 && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-purple-600/20 border border-purple-500/50 rounded-lg">
            <div className="text-purple-300 text-sm">Tests Ejecutados</div>
            <div className="text-2xl font-bold text-white">{testResults.length}</div>
          </div>
          <div className="p-4 bg-green-600/20 border border-green-500/50 rounded-lg">
            <div className="text-green-300 text-sm">Tasa de Éxito</div>
            <div className="text-2xl font-bold text-white">{successRate}%</div>
          </div>
          <div className="p-4 bg-blue-600/20 border border-blue-500/50 rounded-lg">
            <div className="text-blue-300 text-sm">Tiempo Promedio</div>
            <div className="text-2xl font-bold text-white">
              {testResults.length > 0 && testResults.some(r => r.responseTime) ? 
                Math.round(testResults.filter(r => r.responseTime).reduce((acc, r) => acc + (r.responseTime || 0), 0) / testResults.filter(r => r.responseTime).length) : 0}ms
            </div>
          </div>
        </div>
      )}

      {/* Detailed Results */}
      {testResults.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-white">Resultados Detallados</h3>
          {testResults.map((result, index) => (
            <div
              key={index}
              className={`p-4 border rounded-lg ${getResultColor(result)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {getResultIcon(result)}
                  <div>
                    <div className="font-semibold text-white">
                      {result.username === 'invalid_user' ? 'Test de Credenciales Inválidas' : `Usuario: ${result.username}`}
                    </div>
                    {result.userInfo && (
                      <div className="text-sm text-gray-300 mt-1">
                        Nivel: {result.userInfo.level} | Rango: {result.userInfo.rank} | 
                        {result.userInfo.premium_plan && ` Plan: ${result.userInfo.premium_plan}`}
                      </div>
                    )}
                    {result.error && (
                      <div className="text-sm text-gray-300 mt-1">
                        {result.username === 'invalid_user' ? 'Resultado: ' : 'Error: '}{result.error}
                      </div>
                    )}
                  </div>
                </div>
                {result.responseTime && (
                  <div className="text-sm text-gray-400">
                    {result.responseTime}ms
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}