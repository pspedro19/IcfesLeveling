'use client';

import React from 'react';
import LoginTester from '../components/login/LoginTester';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function LoginTestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link 
            href="/login"
            className="inline-flex items-center gap-2 text-purple-400 hover:text-purple-300 mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Volver al Login
          </Link>
          
          <h1 className="text-4xl font-bold bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent mb-4">
            🧪 Sistema de Pruebas de Login
          </h1>
          
          <div className="bg-blue-600/20 border border-blue-500/50 rounded-lg p-4 mb-6">
            <h2 className="text-lg font-semibold text-blue-300 mb-2">Información del Sistema</h2>
            <div className="text-sm text-blue-200 space-y-1">
              <p>• <strong>Frontend:</strong> Next.js corriendo en puerto 3000</p>
              <p>• <strong>Backend:</strong> FastAPI corriendo en puerto 4000</p>
              <p>• <strong>Autenticación:</strong> JWT con OAuth2</p>
              <p>• <strong>Base de Datos:</strong> PostgreSQL con usuarios de prueba</p>
            </div>
          </div>

          <div className="bg-green-600/20 border border-green-500/50 rounded-lg p-4 mb-6">
            <h2 className="text-lg font-semibold text-green-300 mb-2">Cuentas de Prueba Disponibles</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="bg-purple-600/20 p-3 rounded">
                <div className="font-bold text-purple-300">👑 Admin</div>
                <div className="text-gray-300">Usuario: admin</div>
                <div className="text-gray-300">Contraseña: secret</div>
                <div className="text-purple-200 text-xs">Nivel 50, Rango S, Premium</div>
              </div>
              <div className="bg-blue-600/20 p-3 rounded">
                <div className="font-bold text-blue-300">🆕 Test</div>
                <div className="text-gray-300">Usuario: test</div>
                <div className="text-gray-300">Contraseña: secret</div>
                <div className="text-blue-200 text-xs">Nivel 1, Rango E, Free</div>
              </div>
              <div className="bg-green-600/20 p-3 rounded">
                <div className="font-bold text-green-300">📚 Student1</div>
                <div className="text-gray-300">Usuario: student1</div>
                <div className="text-gray-300">Contraseña: secret</div>
                <div className="text-green-200 text-xs">Nivel 5, Rango D, Free</div>
              </div>
            </div>
          </div>
        </div>

        {/* Test Component */}
        <LoginTester />

        {/* Additional Test Information */}
        <div className="mt-8 space-y-6">
          <div className="bg-yellow-600/20 border border-yellow-500/50 rounded-lg p-4">
            <h2 className="text-lg font-semibold text-yellow-300 mb-2">Notas de Prueba</h2>
            <div className="text-sm text-yellow-200 space-y-2">
              <p>• Las pruebas validan tanto la autenticación exitosa como el rechazo de credenciales inválidas</p>
              <p>• Se mide el tiempo de respuesta para evaluar el rendimiento del sistema</p>
              <p>• Se verifica que los datos del usuario sean correctos (nivel, rango, plan premium)</p>
              <p>• Los tokens JWT se almacenan en localStorage para sesiones persistentes</p>
            </div>
          </div>

          <div className="bg-red-600/20 border border-red-500/50 rounded-lg p-4">
            <h2 className="text-lg font-semibold text-red-300 mb-2">Solución de Problemas</h2>
            <div className="text-sm text-red-200 space-y-2">
              <p>• Si las pruebas fallan, verifica que el backend esté corriendo en puerto 4000</p>
              <p>• Errores 404: El endpoint auth-simple no existe o la ruta es incorrecta</p>
              <p>• Errores 401: Credenciales incorrectas o usuario no existe en la base de datos</p>
              <p>• Errores de red: Problema de conexión entre frontend y backend</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}