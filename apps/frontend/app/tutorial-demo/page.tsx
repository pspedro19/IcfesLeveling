'use client';

import React, { useState } from 'react';
import TutorialSystem from '../components/Tutorial/TutorialSystem';
import { 
  Sword, 
  Book, 
  Users, 
  Trophy, 
  Settings,
  RotateCcw,
  CheckCircle
} from 'lucide-react';

export default function TutorialDemoPage() {
  const [tutorialCompleted, setTutorialCompleted] = useState(false);
  const [tutorialKey, setTutorialKey] = useState(0);
  
  const handleComplete = () => {
    setTutorialCompleted(true);
  };
  
  const handleSkip = () => {
    console.log('Tutorial skipped');
  };
  
  const resetTutorial = () => {
    localStorage.removeItem('tutorial-demo');
    setTutorialKey(prev => prev + 1);
    setTutorialCompleted(false);
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-white text-center mb-8 font-cinzel">
          Sistema de Tutorial
        </h1>
        
        {/* Demo UI Elements */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Character Stats */}
          <div className="character-stats bg-gray-900/80 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Estadísticas</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Nivel</span>
                <span className="text-white font-bold">15</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Experiencia</span>
                <span className="text-white font-bold">3,450 / 5,000</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Rango</span>
                <span className="text-purple-400 font-bold">B</span>
              </div>
            </div>
          </div>
          
          {/* Battle Button */}
          <div className="flex items-center justify-center">
            <button className="battle-button bg-gradient-to-r from-red-600 to-red-700 
              hover:from-red-700 hover:to-red-800 text-white font-bold px-8 py-4 
              rounded-lg transform hover:scale-105 transition-all flex items-center gap-3">
              <Sword className="w-6 h-6" />
              Iniciar Batalla
            </button>
          </div>
          
          {/* Quest Tracker */}
          <div className="quest-tracker bg-gray-900/80 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Misiones Diarias</h3>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-gray-300">Completa 5 batallas</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full border-2 border-gray-600" />
                <span className="text-gray-300">Gana 1000 EXP</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex justify-center gap-4 mb-8">
          <button className="guild-button bg-green-600 hover:bg-green-700 text-white 
            font-semibold px-6 py-3 rounded-lg transition-all flex items-center gap-2">
            <Users className="w-5 h-5" />
            Gremios
          </button>
          
          <button className="leaderboard-button bg-yellow-600 hover:bg-yellow-700 
            text-white font-semibold px-6 py-3 rounded-lg transition-all flex 
            items-center gap-2">
            <Trophy className="w-5 h-5" />
            Ranking
          </button>
          
          <button className="settings-button bg-gray-600 hover:bg-gray-700 text-white 
            font-semibold px-6 py-3 rounded-lg transition-all flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Ajustes
          </button>
        </div>
        
        {/* Tutorial Controls */}
        <div className="bg-gray-900/80 rounded-lg p-6 text-center">
          <h3 className="text-xl font-semibold text-white mb-4">
            Controles del Tutorial
          </h3>
          
          {tutorialCompleted && (
            <div className="bg-green-900/30 border border-green-500/50 rounded-lg p-4 mb-4">
              <p className="text-green-400">
                ¡Tutorial completado exitosamente!
              </p>
            </div>
          )}
          
          <button
            onClick={resetTutorial}
            className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 
              hover:to-purple-800 text-white font-bold px-6 py-3 rounded-lg transition-all
              transform hover:scale-105 flex items-center gap-2 mx-auto"
          >
            <RotateCcw className="w-5 h-5" />
            Reiniciar Tutorial
          </button>
          
          <p className="text-gray-400 text-sm mt-4">
            El tutorial se iniciará automáticamente si no se ha completado antes
          </p>
        </div>
      </div>
      
      {/* Tutorial System */}
      <TutorialSystem
        key={tutorialKey}
        onComplete={handleComplete}
        onSkip={handleSkip}
        storageKey="tutorial-demo"
      />
    </div>
  );
}