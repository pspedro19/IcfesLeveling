'use client';

import React, { useState } from 'react';
import AccessibleContent from '../components/Accessibility/AccessibleContent';
import { TTSProvider, useTextToSpeech } from '../hooks/useTextToSpeech';
import TTSButton from '../components/ui/TTSButton';
import { 
  Accessibility,
  Volume2,
  Eye,
  Type,
  Keyboard,
  MessageSquare,
  Settings
} from 'lucide-react';

function TTSDemo() {
  const { voices, currentVoice, setVoice, speak, isSupported } = useTextToSpeech();
  const [selectedRate, setSelectedRate] = useState(1.0);
  
  const spanishVoices = voices.filter(voice => voice.lang.startsWith('es'));
  
  return (
    <div className="bg-gray-900/80 rounded-lg p-6">
      <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
        <Volume2 className="w-6 h-6" />
        Configuración de Voz
      </h3>
      
      {!isSupported ? (
        <p className="text-yellow-300">
          Text-to-Speech no está soportado en este navegador
        </p>
      ) : (
        <div className="space-y-4">
          {/* Voice Selection */}
          <div>
            <label className="text-gray-300 text-sm">Voz:</label>
            <select
              value={currentVoice?.name || ''}
              onChange={(e) => {
                const voice = voices.find(v => v.name === e.target.value);
                if (voice) setVoice(voice);
              }}
              className="w-full mt-1 bg-gray-800 text-white px-3 py-2 rounded-lg"
            >
              <option value="">Seleccionar voz...</option>
              {spanishVoices.map(voice => (
                <option key={voice.name} value={voice.name}>
                  {voice.name} ({voice.lang})
                </option>
              ))}
            </select>
          </div>
          
          {/* Speed Control */}
          <div>
            <label className="text-gray-300 text-sm">
              Velocidad: {selectedRate.toFixed(1)}x
            </label>
            <input
              type="range"
              min="0.5"
              max="2"
              step="0.1"
              value={selectedRate}
              onChange={(e) => setSelectedRate(parseFloat(e.target.value))}
              className="w-full mt-1"
            />
          </div>
          
          {/* Test Button */}
          <button
            onClick={() => speak('Hola, soy tu asistente de ICFES Leveling. ¿Cómo puedo ayudarte hoy?', { rate: selectedRate })}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 
              rounded-lg transition-all"
          >
            Probar Voz
          </button>
        </div>
      )}
    </div>
  );
}

export default function AccessibilityDemoPage() {
  const [keyboardNav, setKeyboardNav] = useState(false);
  
  return (
    <TTSProvider>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 
        to-gray-900 p-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 
              bg-purple-600 rounded-full mb-4">
              <Accessibility className="w-10 h-10 text-white" />
            </div>
            
            <h1 className="text-4xl font-bold text-white mb-4 font-cinzel">
              Accesibilidad Universal
            </h1>
            
            <p className="text-gray-300 max-w-2xl mx-auto">
              ICFES Leveling está diseñado para ser accesible para todos. 
              Explora nuestras funciones de accesibilidad.
            </p>
          </div>
          
          {/* Accessible Content Demo */}
          <AccessibleContent className="mb-8">
            <div className="bg-gray-900/80 rounded-lg p-6">
              <h2 className="text-2xl font-semibold text-white mb-4">
                Contenido Accesible
              </h2>
              
              <p className="text-gray-300 mb-4">
                Este es un ejemplo de contenido con funciones de accesibilidad integradas. 
                Puedes usar los controles superiores para:
              </p>
              
              <ul className="list-disc list-inside text-gray-300 space-y-2 mb-4">
                <li>Escuchar el contenido en voz alta (Text-to-Speech)</li>
                <li>Ajustar el tamaño de la fuente para mejor legibilidad</li>
                <li>Activar el modo de alto contraste</li>
              </ul>
              
              <p className="text-gray-300">
                Todas estas funciones están diseñadas para hacer que el aprendizaje 
                sea más accesible y cómodo para usuarios con diferentes necesidades.
              </p>
            </div>
          </AccessibleContent>
          
          {/* TTS Configuration */}
          <TTSDemo />
          
          {/* Accessibility Features */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-900/80 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <Keyboard className="w-6 h-6" />
                Navegación por Teclado
              </h3>
              
              <p className="text-gray-300 mb-4">
                Toda la aplicación es navegable usando solo el teclado:
              </p>
              
              <div className="space-y-2 text-sm text-gray-400">
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-gray-700 rounded">Tab</kbd>
                  <span>Navegar entre elementos</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-gray-700 rounded">Enter</kbd>
                  <span>Activar elementos</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-gray-700 rounded">Esc</kbd>
                  <span>Cerrar modales</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-gray-700 rounded">←→</kbd>
                  <span>Navegar en carruseles</span>
                </div>
              </div>
              
              <button
                onClick={() => setKeyboardNav(!keyboardNav)}
                className={`mt-4 px-4 py-2 rounded-lg transition-all ${
                  keyboardNav 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-700 text-gray-300'
                }`}
              >
                {keyboardNav ? 'Navegación Activada' : 'Activar Navegación'}
              </button>
            </div>
            
            <div className="bg-gray-900/80 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <MessageSquare className="w-6 h-6" />
                Screen Readers
              </h3>
              
              <p className="text-gray-300 mb-4">
                Compatible con lectores de pantalla populares:
              </p>
              
              <ul className="space-y-2 text-gray-400">
                <li>✓ NVDA (Windows)</li>
                <li>✓ JAWS (Windows)</li>
                <li>✓ VoiceOver (macOS/iOS)</li>
                <li>✓ TalkBack (Android)</li>
              </ul>
              
              <p className="text-sm text-gray-500 mt-4">
                Todos los elementos interactivos tienen etiquetas ARIA apropiadas
              </p>
            </div>
          </div>
          
          {/* Additional Features */}
          <div className="mt-8 bg-gray-900/80 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Settings className="w-6 h-6" />
              Más Funciones de Accesibilidad
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div>
                  <h4 className="font-semibold text-white">Reducir Movimiento</h4>
                  <p className="text-sm text-gray-400">
                    Respeta la configuración del sistema para reducir animaciones
                  </p>
                </div>
                
                <div>
                  <h4 className="font-semibold text-white">Modo Daltonismo</h4>
                  <p className="text-sm text-gray-400">
                    Paletas de colores adaptadas para diferentes tipos de daltonismo
                  </p>
                </div>
                
                <div>
                  <h4 className="font-semibold text-white">Subtítulos</h4>
                  <p className="text-sm text-gray-400">
                    Todos los videos incluyen subtítulos en español
                  </p>
                </div>
              </div>
              
              <div className="space-y-3">
                <div>
                  <h4 className="font-semibold text-white">Tiempo Extendido</h4>
                  <p className="text-sm text-gray-400">
                    Opción para extender límites de tiempo en evaluaciones
                  </p>
                </div>
                
                <div>
                  <h4 className="font-semibold text-white">Modo Simplificado</h4>
                  <p className="text-sm text-gray-400">
                    UI simplificada para reducir distracciones
                  </p>
                </div>
                
                <div>
                  <h4 className="font-semibold text-white">Ayuda Contextual</h4>
                  <p className="text-sm text-gray-400">
                    Tooltips y ayuda disponible en cada sección
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </TTSProvider>
  );
}