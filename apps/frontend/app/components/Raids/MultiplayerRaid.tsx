'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Swords, 
  Heart, 
  Shield, 
  Zap,
  Users,
  Timer,
  Trophy,
  AlertTriangle,
  TrendingUp,
  Sparkles,
  Skull
} from 'lucide-react';
import { useRaidSocket } from '@/hooks/useWebSocket';
import { useAuthStore } from '@/stores/useAuthStore';
import { useAudio } from '../PortalLogin/AudioEngine';
import DamageNumbers from '../BattleSystem/DamageNumbers';

interface RaidParticipant {
  id: string;
  username: string;
  level: number;
  role: 'tank' | 'dps' | 'healer';
  hp: number;
  maxHp: number;
  damage: number;
  isReady: boolean;
  isAlive: boolean;
  combo: number;
}

interface RaidBoss {
  id: string;
  name: string;
  title: string;
  hp: number;
  maxHp: number;
  phase: number;
  mechanics: string[];
  enrageTimer: number;
  difficulty: 'normal' | 'hard' | 'mythic';
}

interface RaidState {
  id: string;
  status: 'waiting' | 'starting' | 'active' | 'victory' | 'defeat';
  boss: RaidBoss;
  participants: RaidParticipant[];
  startTime?: Date;
  endTime?: Date;
  totalDamage: number;
  mechanics: {
    current?: string;
    nextIn?: number;
  };
}

interface MultiplayerRaidProps {
  raidId: string;
  onComplete?: (result: 'victory' | 'defeat') => void;
}

export default function MultiplayerRaid({ raidId, onComplete }: MultiplayerRaidProps) {
  const { user } = useAuthStore();
  const { playSound } = useAudio();
  const { isConnected, raidState, participants, joinRaid, attackBoss, sendMessage } = useRaidSocket();
  
  const [localRaidState, setLocalRaidState] = useState<RaidState | null>(null);
  const [isAttacking, setIsAttacking] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [damageEvents, setDamageEvents] = useState<Array<{
    id: string;
    value: number;
    position: { x: number; y: number };
    isCritical?: boolean;
  }>>([]);
  const [mechanicWarning, setMechanicWarning] = useState<string | null>(null);
  
  const bossRef = useRef<HTMLDivElement>(null);
  const [countdown, setCountdown] = useState<number | null>(null);
  
  // Join raid on mount
  useEffect(() => {
    if (!isConnected || !user) return;
    
    joinRaid(raidId, user.id);
    playSound('portal_hum');
    
    return () => {
      // Leave raid on unmount
      playSound('portal_close');
    };
  }, [isConnected, user, raidId, joinRaid, playSound]);
  
  // Update local raid state
  useEffect(() => {
    if (raidState) {
      setLocalRaidState(raidState);
      
      // Check for phase changes
      if (localRaidState && raidState.boss.phase > localRaidState.boss.phase) {
        playSound('boss_roar');
        setMechanicWarning(`¡FASE ${raidState.boss.phase}!`);
      }
      
      // Check for victory/defeat
      if (raidState.status === 'victory') {
        playSound('level_up');
        onComplete?.('victory');
      } else if (raidState.status === 'defeat') {
        playSound('game_over');
        onComplete?.('defeat');
      }
    }
  }, [raidState, localRaidState, playSound, onComplete]);
  
  // Handle countdown
  useEffect(() => {
    if (localRaidState?.status === 'starting') {
      let count = 5;
      setCountdown(count);
      
      const interval = setInterval(() => {
        count--;
        setCountdown(count);
        
        if (count === 0) {
          clearInterval(interval);
          setCountdown(null);
          playSound('battle_start');
        } else {
          playSound('countdown_tick');
        }
      }, 1000);
      
      return () => clearInterval(interval);
    }
  }, [localRaidState?.status, playSound]);
  
  // Mechanic warnings
  useEffect(() => {
    if (mechanicWarning) {
      const timeout = setTimeout(() => {
        setMechanicWarning(null);
      }, 3000);
      
      return () => clearTimeout(timeout);
    }
  }, [mechanicWarning]);
  
  // Mock question fetching
  const fetchQuestion = () => {
    // In real implementation, this would fetch from API
    const mockQuestion = {
      id: Date.now().toString(),
      text: '¿Cuál es la derivada de x²?',
      options: ['2x', 'x²', '2x²', 'x'],
      correct: '2x',
      difficulty: localRaidState?.boss.phase || 1,
      damageMultiplier: 1 + (localRaidState?.boss.phase || 1) * 0.5
    };
    
    setCurrentQuestion(mockQuestion);
    setSelectedAnswer(null);
  };
  
  const handleAttack = () => {
    if (!currentQuestion || !selectedAnswer || isAttacking) return;
    
    setIsAttacking(true);
    const isCorrect = selectedAnswer === currentQuestion.correct;
    
    if (isCorrect) {
      const baseDamage = 50;
      const damage = Math.floor(baseDamage * currentQuestion.damageMultiplier);
      const isCritical = Math.random() < 0.2;
      const finalDamage = isCritical ? damage * 2 : damage;
      
      // Send damage to server
      attackBoss(raidId, finalDamage);
      
      // Show damage number
      if (bossRef.current) {
        const rect = bossRef.current.getBoundingClientRect();
        const event = {
          id: Date.now().toString(),
          value: finalDamage,
          position: {
            x: rect.left + rect.width / 2 + (Math.random() - 0.5) * 100,
            y: rect.top + rect.height / 2
          },
          isCritical
        };
        
        setDamageEvents(prev => [...prev, event]);
        setTimeout(() => {
          setDamageEvents(prev => prev.filter(e => e.id !== event.id));
        }, 2000);
      }
      
      playSound(isCritical ? 'critical_hit' : 'damage_hit');
    } else {
      playSound('miss');
      // Take damage
      sendMessage(raidId, `${user?.name} falló la pregunta!`);
    }
    
    setTimeout(() => {
      setIsAttacking(false);
      setCurrentQuestion(null);
      setSelectedAnswer(null);
    }, 1000);
  };
  
  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'tank':
        return <Shield className="w-4 h-4 text-blue-400" />;
      case 'healer':
        return <Heart className="w-4 h-4 text-green-400" />;
      default:
        return <Swords className="w-4 h-4 text-red-400" />;
    }
  };
  
  const getBossHealthColor = () => {
    const hpPercent = ((localRaidState?.boss.hp || 0) / (localRaidState?.boss.maxHp || 1)) * 100;
    if (hpPercent > 60) return 'bg-green-500';
    if (hpPercent > 30) return 'bg-yellow-500';
    return 'bg-red-500';
  };
  
  if (!localRaidState) {
    return (
      <div className="flex items-center justify-center min-h-[600px]">
        <div className="text-center">
          <motion.div
            className="w-20 h-20 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
          <p className="text-purple-300">Conectando a la raid...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="relative bg-gradient-to-br from-gray-900 via-red-900 to-gray-900 rounded-lg overflow-hidden">
      {/* Countdown Overlay */}
      <AnimatePresence>
        {countdown !== null && (
          <motion.div
            className="absolute inset-0 bg-black/80 z-50 flex items-center justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="text-9xl font-bold text-white"
              initial={{ scale: 0.5 }}
              animate={{ scale: 1 }}
              exit={{ scale: 1.5, opacity: 0 }}
              transition={{ duration: 0.5 }}
            >
              {countdown || '¡LUCHA!'}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Mechanic Warning */}
      <AnimatePresence>
        {mechanicWarning && (
          <motion.div
            className="absolute top-8 left-1/2 transform -translate-x-1/2 z-40"
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -50, opacity: 0 }}
          >
            <div className="bg-red-600 text-white px-8 py-4 rounded-lg shadow-lg flex items-center gap-3">
              <AlertTriangle className="w-6 h-6" />
              <span className="text-xl font-bold">{mechanicWarning}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Header */}
      <div className="bg-black/50 p-4 border-b border-red-500/50">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white font-cinzel">
              {localRaidState.boss.name}
            </h2>
            <p className="text-red-300">{localRaidState.boss.title}</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-center">
              <Timer className="w-5 h-5 text-yellow-400 mx-auto" />
              <span className="text-sm text-gray-300">
                {Math.floor((Date.now() - (localRaidState.startTime?.getTime() || Date.now())) / 1000)}s
              </span>
            </div>
            
            <div className="text-center">
              <Users className="w-5 h-5 text-blue-400 mx-auto" />
              <span className="text-sm text-gray-300">
                {participants.filter(p => p.isAlive).length}/{participants.length}
              </span>
            </div>
            
            <div className="text-center">
              <Skull className="w-5 h-5 text-purple-400 mx-auto" />
              <span className="text-sm text-gray-300">
                Fase {localRaidState.boss.phase}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Boss Area */}
      <div className="relative h-96 flex items-center justify-center p-8">
        {/* Boss Model */}
        <motion.div
          ref={bossRef}
          className="relative"
          animate={localRaidState.status === 'active' ? {
            y: [0, -10, 0],
            scale: [1, 1.05, 1]
          } : {}}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="w-48 h-48 bg-gradient-to-br from-red-600 to-purple-800 rounded-full 
            shadow-2xl shadow-red-500/50 flex items-center justify-center">
            <Skull className="w-24 h-24 text-white" />
          </div>
          
          {/* Boss HP Bar */}
          <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 w-64">
            <div className="bg-gray-800 rounded-full h-6 overflow-hidden">
              <motion.div
                className={`h-full ${getBossHealthColor()} transition-all duration-500`}
                initial={{ width: '100%' }}
                animate={{ 
                  width: `${((localRaidState.boss.hp / localRaidState.boss.maxHp) * 100)}%` 
                }}
              />
            </div>
            <p className="text-center text-white mt-1">
              {localRaidState.boss.hp.toLocaleString()} / {localRaidState.boss.maxHp.toLocaleString()} HP
            </p>
          </div>
        </motion.div>
        
        {/* Damage Numbers */}
        {damageEvents.map(event => (
          <DamageNumbers
            key={event.id}
            damages={[event]}
          />
        ))}
      </div>
      
      {/* Participants */}
      <div className="bg-black/30 p-4">
        <h3 className="text-lg font-semibold text-white mb-3">Participantes</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {participants.map(participant => (
            <motion.div
              key={participant.id}
              className={`bg-gray-800/50 rounded-lg p-3 border ${
                participant.isAlive ? 'border-gray-600' : 'border-red-600 opacity-50'
              }`}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <div className="flex items-center gap-2 mb-2">
                {getRoleIcon(participant.role)}
                <span className="text-sm text-white truncate">
                  {participant.username}
                  {participant.id === user?.id && ' (Tú)'}
                </span>
              </div>
              
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">HP</span>
                  <span className="text-white">
                    {participant.hp}/{participant.maxHp}
                  </span>
                </div>
                
                <div className="bg-gray-700 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-green-500 transition-all duration-300"
                    style={{ width: `${(participant.hp / participant.maxHp) * 100}%` }}
                  />
                </div>
                
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Daño</span>
                  <span className="text-yellow-400">{participant.damage.toLocaleString()}</span>
                </div>
                
                {participant.combo > 0 && (
                  <div className="text-xs text-purple-400 text-center">
                    Combo x{participant.combo}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
      
      {/* Battle Interface */}
      {localRaidState.status === 'active' && (
        <div className="bg-black/50 p-6">
          {!currentQuestion ? (
            <div className="text-center">
              <motion.button
                onClick={fetchQuestion}
                disabled={isAttacking}
                className="bg-gradient-to-r from-red-600 to-purple-600 hover:from-red-700 
                  hover:to-purple-700 text-white font-bold py-4 px-8 rounded-lg text-lg 
                  disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3 mx-auto"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Zap className="w-6 h-6" />
                ¡Atacar al Jefe!
              </motion.button>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-2xl mx-auto"
            >
              <h4 className="text-xl text-white mb-4 text-center">
                {currentQuestion.text}
              </h4>
              
              <div className="grid grid-cols-2 gap-3 mb-4">
                {currentQuestion.options.map((option: string, index: number) => (
                  <motion.button
                    key={index}
                    onClick={() => setSelectedAnswer(option)}
                    disabled={isAttacking}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      selectedAnswer === option
                        ? 'border-purple-500 bg-purple-900/50'
                        : 'border-gray-600 bg-gray-800/50 hover:border-gray-500'
                    } disabled:opacity-50`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <span className="text-white">{option}</span>
                  </motion.button>
                ))}
              </div>
              
              <motion.button
                onClick={handleAttack}
                disabled={!selectedAnswer || isAttacking}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 
                  hover:from-purple-700 hover:to-pink-700 text-white font-bold py-3 
                  rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                Confirmar Ataque
              </motion.button>
            </motion.div>
          )}
        </div>
      )}
      
      {/* Victory/Defeat Screen */}
      {(localRaidState.status === 'victory' || localRaidState.status === 'defeat') && (
        <motion.div
          className="absolute inset-0 bg-black/90 flex items-center justify-center z-50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <motion.div
            className="text-center"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            {localRaidState.status === 'victory' ? (
              <>
                <Trophy className="w-32 h-32 text-yellow-400 mx-auto mb-4" />
                <h2 className="text-5xl font-bold text-yellow-400 mb-4 font-cinzel">
                  ¡VICTORIA!
                </h2>
                <p className="text-xl text-gray-300 mb-8">
                  {localRaidState.boss.name} ha sido derrotado
                </p>
              </>
            ) : (
              <>
                <Skull className="w-32 h-32 text-red-400 mx-auto mb-4" />
                <h2 className="text-5xl font-bold text-red-400 mb-4 font-cinzel">
                  DERROTA
                </h2>
                <p className="text-xl text-gray-300 mb-8">
                  El equipo ha sido eliminado
                </p>
              </>
            )}
            
            <div className="bg-gray-800 rounded-lg p-6 max-w-md mx-auto">
              <h3 className="text-lg font-semibold text-white mb-4">
                Estadísticas de la Raid
              </h3>
              
              <div className="space-y-3 text-left">
                <div className="flex justify-between">
                  <span className="text-gray-400">Tiempo Total</span>
                  <span className="text-white">
                    {Math.floor(
                      ((localRaidState.endTime?.getTime() || Date.now()) - 
                      (localRaidState.startTime?.getTime() || Date.now())) / 1000
                    )}s
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-400">Daño Total</span>
                  <span className="text-yellow-400">
                    {localRaidState.totalDamage.toLocaleString()}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-400">Supervivientes</span>
                  <span className="text-green-400">
                    {participants.filter(p => p.isAlive).length}/{participants.length}
                  </span>
                </div>
              </div>
              
              <div className="mt-6 pt-6 border-t border-gray-700">
                <h4 className="text-sm font-semibold text-gray-400 mb-3">
                  TOP DAÑO
                </h4>
                <div className="space-y-2">
                  {participants
                    .sort((a, b) => b.damage - a.damage)
                    .slice(0, 3)
                    .map((p, index) => (
                      <div key={p.id} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-yellow-400">#{index + 1}</span>
                          <span className="text-white">{p.username}</span>
                        </div>
                        <span className="text-yellow-400">
                          {p.damage.toLocaleString()}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}