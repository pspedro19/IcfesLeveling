'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain,
  Lightbulb,
  TrendingUp,
  AlertCircle,
  Sparkles,
  ChevronRight,
  RefreshCw
} from 'lucide-react';
import { aiTipsService } from '@/services/ai-tips.service';

interface AIBattleTipsProps {
  battleId: string;
  currentTopic: string;
  difficulty: number;
  battleType?: string;
  onTipClick?: (tip: string) => void;
}

export default function AIBattleTips({
  battleId,
  currentTopic,
  difficulty,
  battleType = 'normal',
  onTipClick
}: AIBattleTipsProps) {
  const [tips, setTips] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerated, setIsGenerated] = useState(false);
  const [accuracy, setAccuracy] = useState<number | null>(null);
  const [weakAreas, setWeakAreas] = useState<string[]>([]);
  const [selectedTipIndex, setSelectedTipIndex] = useState(0);
  
  const fetchTips = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await aiTipsService.getBattleTips(
        battleId,
        currentTopic,
        difficulty,
        battleType
      );
      
      setTips(response.tips);
      setIsGenerated(response.generated);
      setAccuracy(response.accuracy || null);
      setWeakAreas(response.weakAreas || []);
    } catch (err) {
      setError('Error al cargar tips');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchTips();
  }, [battleId, currentTopic]);
  
  const handleTipClick = (tip: string, index: number) => {
    setSelectedTipIndex(index);
    onTipClick?.(tip);
  };
  
  if (loading) {
    return (
      <div className="bg-gray-900/80 rounded-lg p-4 border border-purple-500/30">
        <div className="flex items-center gap-3">
          <Brain className="w-6 h-6 text-purple-400 animate-pulse" />
          <p className="text-gray-400">Analizando tu rendimiento...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-900/20 rounded-lg p-4 border border-red-500/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-red-400" />
            <p className="text-red-400">{error}</p>
          </div>
          <button
            onClick={fetchTips}
            className="p-2 hover:bg-red-800/30 rounded-lg transition-all"
          >
            <RefreshCw className="w-4 h-4 text-red-400" />
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <motion.div
      className="bg-gray-900/80 rounded-lg border border-purple-500/30 overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {/* Header */}
      <div className="bg-purple-900/30 px-4 py-3 border-b border-purple-500/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="w-6 h-6 text-purple-400" />
            <h3 className="font-semibold text-white">
              Tips de IA {isGenerated && <span className="text-xs text-purple-400">(Personalizado)</span>}
            </h3>
          </div>
          
          {accuracy !== null && (
            <div className="flex items-center gap-2 text-sm">
              <TrendingUp className="w-4 h-4 text-green-400" />
              <span className="text-gray-300">Precisión: {accuracy.toFixed(1)}%</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Tips Content */}
      <div className="p-4">
        {/* Weak Areas Alert */}
        {weakAreas.length > 0 && (
          <div className="mb-4 bg-orange-900/20 rounded-lg p-3 border border-orange-500/30">
            <p className="text-sm text-orange-400 mb-2">
              Áreas a reforzar:
            </p>
            <div className="flex flex-wrap gap-2">
              {weakAreas.map((area, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-orange-800/30 rounded text-xs text-orange-300"
                >
                  {area}
                </span>
              ))}
            </div>
          </div>
        )}
        
        {/* Tips List */}
        <div className="space-y-3">
          <AnimatePresence mode="wait">
            {tips.map((tip, index) => (
              <motion.div
                key={`tip-${index}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => handleTipClick(tip, index)}
                className={`
                  relative group cursor-pointer rounded-lg p-3 transition-all
                  ${selectedTipIndex === index 
                    ? 'bg-purple-800/30 border border-purple-500/50' 
                    : 'bg-gray-800/50 border border-gray-700/50 hover:border-purple-500/30'
                  }
                `}
              >
                <div className="flex items-start gap-3">
                  <div className={`
                    p-2 rounded-lg transition-all
                    ${selectedTipIndex === index 
                      ? 'bg-purple-600/30' 
                      : 'bg-gray-700/50 group-hover:bg-purple-700/30'
                    }
                  `}>
                    <Lightbulb className="w-4 h-4 text-purple-400" />
                  </div>
                  
                  <div className="flex-1">
                    <p className="text-sm text-gray-300 leading-relaxed">
                      {tip}
                    </p>
                  </div>
                  
                  <ChevronRight className={`
                    w-4 h-4 text-gray-500 transition-all
                    ${selectedTipIndex === index ? 'rotate-90 text-purple-400' : ''}
                  `} />
                </div>
                
                {/* Sparkle effect on selected */}
                {selectedTipIndex === index && (
                  <motion.div
                    className="absolute -top-1 -right-1"
                    initial={{ scale: 0, rotate: 0 }}
                    animate={{ scale: 1, rotate: 360 }}
                    transition={{ duration: 0.5 }}
                  >
                    <Sparkles className="w-5 h-5 text-purple-400" />
                  </motion.div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
        
        {/* AI Status */}
        <div className="mt-4 pt-4 border-t border-gray-700/50">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              {isGenerated ? (
                <>
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-gray-400">IA Activa</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 bg-yellow-400 rounded-full" />
                  <span className="text-gray-400">Tips Estándar</span>
                </>
              )}
            </div>
            
            <button
              onClick={fetchTips}
              className="text-purple-400 hover:text-purple-300 transition-colors"
            >
              Actualizar Tips
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}