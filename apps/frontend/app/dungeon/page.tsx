'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Map, 
  Sword, 
  Shield, 
  Heart, 
  Zap, 
  Lock,
  AlertTriangle,
  ChevronRight,
  Star,
  Trophy,
  Users,
  Clock
} from 'lucide-react';
import { useAuthStore } from '@/stores/useAuthStore';
import { useGameModeStore } from '@/stores/useGameModeStore';
import { websocketService } from '../services/websocket.service';
import { cacheService } from '../services/cache.service';
import { useAnalytics } from '../services/analytics.service';
import { ErrorBoundary } from '../components/ErrorBoundary';

// Epic sound effects
const battleStartSound = typeof Audio !== 'undefined' ? new Audio('/sounds/warrior-roar.mp3') : null;
const hoverSound = typeof Audio !== 'undefined' ? new Audio('/sounds/hover.mp3') : null;
const clickSound = typeof Audio !== 'undefined' ? new Audio('/sounds/click.mp3') : null;
const victorySound = typeof Audio !== 'undefined' ? new Audio('/sounds/victory.mp3') : null;
const dungeonMusic = typeof Audio !== 'undefined' ? new Audio('/sounds/menu.mp3') : null;

interface Floor {
  id: number;
  name: string;
  difficulty: number;
  enemies: Enemy[];
  rewards: Reward[];
  isUnlocked: boolean;
  isCompleted: boolean;
}

interface Enemy {
  id: string;
  name: string;
  type: string;
  hp: number;
  attack: number;
  defense: number;
  level: number;
  icon: string;
}

interface Reward {
  type: 'experience' | 'orbs' | 'crystals' | 'items';
  amount: number;
  name?: string;
}

// Mock dungeon data con narrativa épica
const mockDungeon: Floor[] = [
  {
    id: 1,
    name: 'Piso 1: Entrada a las Mazmorras del Conocimiento',
    difficulty: 1,
    enemies: [
      {
        id: 'slime-1',
        name: 'Slime Básico del Saber',
        type: 'slime',
        hp: 50,
        attack: 10,
        defense: 5,
        level: 1,
        icon: '🟢'
      },
      {
        id: 'goblin-1',
        name: 'Goblin Novato de Preguntas',
        type: 'goblin',
        hp: 75,
        attack: 15,
        defense: 8,
        level: 2,
        icon: '🟤'
      }
    ],
    rewards: [
      { type: 'experience', amount: 100 },
      { type: 'orbs', amount: 10 },
      { type: 'crystals', amount: 1 }
    ],
    isUnlocked: true,
    isCompleted: false
  },
  {
    id: 2,
    name: 'Piso 2: Cámaras Intermedias del Conocimiento',
    difficulty: 3,
    enemies: [
      {
        id: 'orc-2',
        name: 'Orc Guerrero del Saber',
        type: 'orc',
        hp: 120,
        attack: 25,
        defense: 15,
        level: 3,
        icon: '⚫'
      },
      {
        id: 'skeleton-2',
        name: 'Esqueleto Arcano de Preguntas',
        type: 'skeleton',
        hp: 90,
        attack: 30,
        defense: 10,
        level: 4,
        icon: '⚪'
      }
    ],
    rewards: [
      { type: 'experience', amount: 200 },
      { type: 'orbs', amount: 20 },
      { type: 'crystals', amount: 2 },
      { type: 'items', amount: 1, name: 'Espada Básica del Hunter' }
    ],
    isUnlocked: false,
    isCompleted: false
  },
  {
    id: 3,
    name: 'Piso 3: Salas Avanzadas de la Sabiduría',
    difficulty: 5,
    enemies: [
      {
        id: 'dragon-3',
        name: 'Dragón Menor del ICFES',
        type: 'dragon',
        hp: 300,
        attack: 50,
        defense: 30,
        level: 5,
        icon: '🔴'
      }
    ],
    rewards: [
      { type: 'experience', amount: 500 },
      { type: 'orbs', amount: 50 },
      { type: 'crystals', amount: 5 },
      { type: 'items', amount: 1, name: 'Bastón Mágico Legendario' }
    ],
    isUnlocked: false,
    isCompleted: false
  }
];

const GUEST_FLOOR_LIMIT = 1;

export default function DungeonPage() {
  // Analytics hook
  const { trackPageView, trackButtonClick, trackBattleStart } = useAnalytics();
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const mode = searchParams.get('mode');
  const floorParam = searchParams.get('floor');
  const isGuestMode = mode === 'guest';
  
  const { user } = useAuthStore();
  const { mode: gameMode } = useGameModeStore();
  
  const [selectedFloor, setSelectedFloor] = useState<Floor | null>(null);
  const [showGuestLimitModal, setShowGuestLimitModal] = useState(false);
  const [showBattleModal, setShowBattleModal] = useState(false);
  const [currentEnemy, setCurrentEnemy] = useState<Enemy | null>(null);
  const [dungeonData, setDungeonData] = useState<Floor[]>(mockDungeon);
  const [isLoadingDungeon, setIsLoadingDungeon] = useState(false);
  const [realGameState, setRealGameState] = useState({
    dungeonLoaded: false,
    statsLoaded: false,
    historyLoaded: false,
    progressSynced: false
  });
  const [battleState, setBattleState] = useState({
    playerHp: 100,
    enemyHp: 0,
    isPlayerTurn: true,
    isComplete: false,
    result: '' as 'victory' | 'defeat' | ''
  });
  const [orbsEarned, setOrbsEarned] = useState(0); // Añadido: Gamificación con orbs

  // Load all dungeon data and check guest limits on mount
  useEffect(() => {
    Promise.all([
      loadDungeonData(),
      loadUserGameStats(),
      loadBattleHistory(),
      syncGameProgress()
    ]).catch(error => {
      console.error('Error loading dungeon data:', error);
    });
    
    if (isGuestMode) {
      const floorNumber = floorParam ? parseInt(floorParam) : 1;
      if (floorNumber > GUEST_FLOOR_LIMIT) {
        setShowGuestLimitModal(true);
        return;
      }
    }
  }, [isGuestMode, floorParam]);

  // Set selected floor when dungeon data changes
  useEffect(() => {
    const floorId = floorParam ? parseInt(floorParam) : 1;
    const floor = dungeonData.find(f => f.id === floorId);
    setSelectedFloor(floor || dungeonData[0]);
  }, [dungeonData, floorParam]);

  const loadDungeonData = async () => {
    try {
      setIsLoadingDungeon(true);
      const response = await fetch('/api/v1/user/dungeon-progress');
      
      if (response.ok) {
        const data = await response.json();
        if (data.floors && data.floors.length > 0) {
          setDungeonData(data.floors);
          setRealGameState(prev => ({ ...prev, dungeonLoaded: true }));
        }
        // Si no hay datos del servidor, mantener mockDungeon como fallback
      }
    } catch (error) {
      console.error('Error loading dungeon data:', error);
      // Usar datos mock como fallback
    } finally {
      setIsLoadingDungeon(false);
    }
  };

  const loadUserGameStats = async () => {
    try {
      const response = await fetch('/api/v1/analytics/personal', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const stats = await response.json();
        setOrbsEarned(stats.totalOrbs || 0);
      }
    } catch (error) {
      console.error('Error loading user game stats:', error);
    }
  };

  const loadBattleHistory = async () => {
    try {
      const response = await fetch('/api/v1/battles/history', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const history = await response.json();
        console.log('Battle history loaded:', history.battles?.length || 0);
      }
    } catch (error) {
      console.error('Error loading battle history:', error);
    }
  };

  const syncGameProgress = async () => {
    try {
      const response = await fetch('/api/v1/user/game-state', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const gameState = await response.json();
        // Sync real progress with local state
        if (gameState.currentFloor) {
          const floor = dungeonData.find(f => f.id === gameState.currentFloor);
          if (floor) setSelectedFloor(floor);
        }
      }
    } catch (error) {
      console.error('Error syncing game progress:', error);
    }
  };

  const handleFloorSelect = (floor: Floor) => {
    if (isGuestMode && floor.id > GUEST_FLOOR_LIMIT) {
      setShowGuestLimitModal(true);
      return;
    }
    clickSound?.play();
    setSelectedFloor(floor);
  };

  const handleEnemySelect = async (enemy: Enemy) => {
    battleStartSound?.play();
    setCurrentEnemy(enemy);
    
    // Start battle via API
    try {
      const response = await fetch('/api/v1/battles/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enemy_id: enemy.id,
          battle_type: 'dungeon',
          floor_id: selectedFloor?.id
        })
      });
      
      if (response.ok) {
        const battleData = await response.json();
        setBattleState({
          battle_id: battleData.battle_id,
          playerHp: 100,
          enemyHp: enemy.hp,
          isPlayerTurn: true,
          isComplete: false,
          result: ''
        });
      }
    } catch (error) {
      console.error('Error starting battle:', error);
      // Fallback to local battle
      setBattleState({
        playerHp: 100,
        enemyHp: enemy.hp,
        isPlayerTurn: true,
        isComplete: false,
        result: ''
      });
    }
    
    setShowBattleModal(true);
  };

  const handleAttack = () => {
    if (!currentEnemy) return;
    
    // Player attacks
    const playerDamage = Math.floor(Math.random() * 20) + 10; // 10-30 damage
    const newEnemyHp = Math.max(0, battleState.enemyHp - playerDamage);
    
    if (newEnemyHp <= 0) {
      // Victory
      setBattleState(prev => ({
        ...prev,
        enemyHp: 0,
        isComplete: true,
        result: 'victory'
      }));
      return;
    }
    
    // Enemy attacks back
    const enemyDamage = Math.floor(Math.random() * currentEnemy.attack) + 5;
    const newPlayerHp = Math.max(0, battleState.playerHp - enemyDamage);
    
    if (newPlayerHp <= 0) {
      // Defeat
      setBattleState(prev => ({
        ...prev,
        playerHp: 0,
        isComplete: true,
        result: 'defeat'
      }));
      return;
    }
    
    setBattleState(prev => ({
      ...prev,
      enemyHp: newEnemyHp,
      playerHp: newPlayerHp,
      isPlayerTurn: !prev.isPlayerTurn
    }));
  };

  const handleDefend = () => {
    if (!currentEnemy) return;
    
    // Player defends (reduces damage)
    const enemyDamage = Math.floor(Math.random() * currentEnemy.attack * 0.5) + 2;
    const newPlayerHp = Math.max(0, battleState.playerHp - enemyDamage);
    
    setBattleState(prev => ({
      ...prev,
      playerHp: newPlayerHp,
      isPlayerTurn: true
    }));
  };

  const handleBattleComplete = () => {
    setShowBattleModal(false);
    setCurrentEnemy(null);
    
    if (battleState.result === 'victory' && selectedFloor) {
      // Mark floor as completed y gamify
      const updatedFloor = { ...selectedFloor, isCompleted: true };
      setSelectedFloor(updatedFloor);
      setOrbsEarned(prev => prev + 20); // Orbs por victoria
    }
  };

  const getDifficultyColor = (difficulty: number) => {
    if (difficulty <= 2) return 'text-green-400';
    if (difficulty <= 4) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getDifficultyIcon = (difficulty: number) => {
    if (difficulty <= 2) return <Star className="w-4 h-4 text-green-400" />;
    if (difficulty <= 4) return <Star className="w-4 h-4 text-yellow-400" />;
    return <Star className="w-4 h-4 text-red-400" />;
  };

  if (showGuestLimitModal) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black to-purple-900 flex items-center justify-center p-4">
        <motion.div
          className="bg-black/30 backdrop-blur-md rounded-lg p-8 max-w-md w-full border-purple-500 shadow-[0_0_10px_#8a2be2]"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
        >
          <div className="text-center">
            <Lock className="w-16 h-16 text-gold-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gold-500 mb-4 font-cinzel">
              Piso Bloqueado por Maldición de Invitado
            </h2>
            <p className="text-gray-300 mb-6">
              En modo Hunter Novato solo puedes acceder al Piso Inicial. 
              Despierta tu poder completo creando una cuenta para conquistar mazmorras legendarias.
            </p>
            
            <div className="space-y-3 mb-6">
              <div className="flex items-center justify-between bg-black/50 rounded-lg p-3">
                <span className="text-gray-300">Pisos Desbloqueados:</span>
                <span className="text-gold-400 font-bold">1/{mockDungeon.length}</span>
              </div>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => router.push('/')}
                className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all shadow-[0_0_5px_#8a2be2]"
              >
                Despertar Poder (Crear Cuenta)
              </button>
              <button
                onClick={() => router.push('/dungeon?mode=guest&floor=1')}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold transition-all shadow-[0_0_5px_#ffd700]"
              >
                Entrar al Piso Inicial
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    );
  }

  if (!selectedFloor) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black to-purple-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gold-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black to-purple-900 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header con lore */}
        <motion.div
          className="bg-black/30 backdrop-blur-md rounded-lg p-6 mb-6 border-purple-500 shadow-[0_0_10px_#8a2be2]"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gold-500 mb-2 font-cinzel">
                Mazmorras del Conocimiento
              </h1>
              <p className="text-gray-300">
                {isGuestMode ? 'Modo Hunter Novato' : 'Modo Conquista Completa'} • {gameMode === 'casual' ? 'Progresión Libre' : 'Progresión Gated'}
              </p>
              <p className="text-sm text-purple-300">Como Hunter, conquista estas mazmorras para alcanzar Rango S+.</p> {/* Lore */}
            </div>
            
            {isGuestMode && (
              <div className="flex items-center gap-2 text-gold-400">
                <AlertTriangle className="w-5 h-5" />
                <span className="text-sm">Solo Piso Inicial disponible</span>
              </div>
            )}
            <p className="text-gold-300">Orbs Ganados: {orbsEarned} 💎</p> {/* Gamificación */}
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Floor Selection */}
          <motion.div
            className="lg:col-span-1"
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            <div className="bg-black/30 backdrop-blur-md rounded-lg p-6 border-purple-500 shadow-[0_0_10px_#8a2be2]">
              <h2 className="text-xl font-bold text-gold-500 mb-4 flex items-center gap-2 font-cinzel">
                <Map className="w-5 h-5" />
                Pisos de las Mazmorras Épicas
              </h2>
              
              <div className="space-y-3">
                {dungeonData.map((floor) => (
                  <motion.button
                    key={floor.id}
                    onClick={() => handleFloorSelect(floor)}
                    disabled={isGuestMode && floor.id > GUEST_FLOOR_LIMIT}
                    className={`
                      w-full p-4 rounded-lg text-left transition-all duration-200
                      ${selectedFloor?.id === floor.id 
                        ? 'bg-purple-900/20 border-purple-500 text-gold-300 shadow-[0_0_5px_#8a2be2]' 
                        : floor.isUnlocked 
                          ? 'bg-gray-800/50 border-gray-600 text-gray-300 hover:bg-gray-700/50 hover:shadow-[0_0_5px_#ffd700]' 
                          : 'bg-gray-800/30 border-gray-700 text-gray-500 cursor-not-allowed'
                      }
                      ${isGuestMode && floor.id > GUEST_FLOOR_LIMIT ? 'opacity-50' : ''}
                      border-2
                    `}
                    whileHover={floor.isUnlocked && !(isGuestMode && floor.id > GUEST_FLOOR_LIMIT) ? { scale: 1.02 } : {}}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-gold-300">{floor.name}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          {getDifficultyIcon(floor.difficulty)}
                          <span className={`text-sm ${getDifficultyColor(floor.difficulty)}`}>
                            Dificultad: {floor.difficulty}/5
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {floor.isCompleted && (
                          <Trophy className="w-5 h-5 text-gold-400" />
                        )}
                        {isGuestMode && floor.id > GUEST_FLOOR_LIMIT && (
                          <Lock className="w-4 h-4 text-gray-500" />
                        )}
                        <ChevronRight className="w-4 h-4" />
                      </div>
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Floor Content */}
          <motion.div
            className="lg:col-span-2"
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <div className="bg-black/30 backdrop-blur-md rounded-lg p-6 border-purple-500 shadow-[0_0_10px_#8a2be2]">
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gold-500 mb-2 font-cinzel">
                  {selectedFloor.name}
                </h2>
                <div className="flex items-center gap-4 text-gray-300">
                  <div className="flex items-center gap-2">
                    {getDifficultyIcon(selectedFloor.difficulty)}
                    <span className={getDifficultyColor(selectedFloor.difficulty)}>
                      Dificultad: {selectedFloor.difficulty}/5
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    <span>{selectedFloor.enemies.length} monstruos del conocimiento</span>
                  </div>
                  {selectedFloor.isCompleted && (
                    <div className="flex items-center gap-2 text-green-400">
                      <Trophy className="w-4 h-4" />
                      <span>Conquistado</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Enemies */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gold-500 mb-4 flex items-center gap-2 font-cinzel">
                  <Sword className="w-5 h-5" />
                  Monstruos en este Piso
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {selectedFloor.enemies.map((enemy) => (
                    <motion.button
                      key={enemy.id}
                      onClick={() => handleEnemySelect(enemy)}
                      disabled={selectedFloor.isCompleted}
                      className="bg-black/50 backdrop-blur-sm rounded-lg p-4 border-gray-600 hover:border-gold-500 transition-all text-left hover:shadow-[0_0_5px_#ffd700]"
                      whileHover={!selectedFloor.isCompleted ? { scale: 1.02 } : {}}
                    >
                      <div className="flex items-center gap-3">
                        <div className="text-2xl">{enemy.icon}</div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-gold-300">{enemy.name}</h4>
                          <p className="text-sm text-gray-300">Nivel {enemy.level}</p>
                          <div className="flex items-center gap-4 mt-2 text-sm">
                            <div className="flex items-center gap-1 text-red-400">
                              <Heart className="w-3 h-3" />
                              <span>{enemy.hp}</span>
                            </div>
                            <div className="flex items-center gap-1 text-orange-400">
                              <Sword className="w-3 h-3" />
                              <span>{enemy.attack}</span>
                            </div>
                            <div className="flex items-center gap-1 text-blue-400">
                              <Shield className="w-3 h-3" />
                              <span>{enemy.defense}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* Rewards */}
              <div>
                <h3 className="text-lg font-semibold text-gold-500 mb-4 flex items-center gap-2 font-cinzel">
                  <Trophy className="w-5 h-5" />
                  Tesoros y Recompensas
                </h3>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {selectedFloor.rewards.map((reward, index) => (
                    <div
                      key={index}
                      className="bg-black/30 backdrop-blur-sm rounded-lg p-3 border-gray-700 shadow-[0_0_3px_#ffd700]"
                    >
                      <div className="text-center">
                        <div className="text-2xl mb-1">
                          {reward.type === 'experience' && '⭐'}
                          {reward.type === 'orbs' && '💎'}
                          {reward.type === 'crystals' && '🔮'}
                          {reward.type === 'items' && '⚔️'}
                        </div>
                        <div className="text-sm text-gold-300 font-semibold">
                          {reward.amount}
                        </div>
                        <div className="text-xs text-gray-300">
                          {reward.type === 'experience' && 'EXP Mística'}
                          {reward.type === 'orbs' && 'Orbs Mágicos'}
                          {reward.type === 'crystals' && 'Cristales Legendarios'}
                          {reward.type === 'items' && reward.name}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Battle Modal */}
      <AnimatePresence>
        {showBattleModal && currentEnemy && (
          <motion.div
            className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="bg-black/50 backdrop-blur-md rounded-lg p-8 max-w-md w-full border-purple-500 shadow-[0_0_10px_#8a2be2]"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
            >
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-gold-500 mb-4 font-cinzel">
                  Batalla Épica contra {currentEnemy.name}
                </h2>
                
                <div className="text-4xl mb-4">{currentEnemy.icon}</div>
                
                {/* HP Bars */}
                <div className="space-y-3 mb-6">
                  <div>
                    <div className="flex justify-between text-sm text-gray-300 mb-1">
                      <span>Esencia Vital del Hunter</span>
                      <span>{battleState.playerHp}/100</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${(battleState.playerHp / 100) * 100}%` }}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm text-gray-300 mb-1">
                      <span>{currentEnemy.name}</span>
                      <span>{battleState.enemyHp}/{currentEnemy.hp}</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-red-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${(battleState.enemyHp / currentEnemy.hp) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
                
                {/* Battle Result */}
                {battleState.isComplete && (
                  <motion.div
                    className="mb-6 p-4 rounded-lg"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    {battleState.result === 'victory' ? (
                      <div className="bg-green-900/20 border border-green-500/30 text-green-300">
                        <h3 className="font-bold text-lg font-cinzel">¡Victoria Legendaria!</h3>
                        <p>Has conquistado a {currentEnemy.name} en nombre del conocimiento.</p>
                      </div>
                    ) : (
                      <div className="bg-red-900/20 border border-red-500/30 text-red-300">
                        <h3 className="font-bold text-lg font-cinzel">Derrota Temporal</h3>
                        <p>El monstruo {currentEnemy.name} te ha superado... ¡Entrena y regresa!</p>
                      </div>
                    )}
                  </motion.div>
                )}
                
                {/* Battle Actions */}
                {!battleState.isComplete && battleState.isPlayerTurn && (
                  <div className="flex gap-3 justify-center">
                    <button
                      onClick={handleAttack}
                      className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-all flex items-center gap-2 shadow-[0_0_5px_#ffd700]"
                    >
                      <Sword className="w-4 h-4" />
                      Ataque Poderoso
                    </button>
                    <button
                      onClick={handleDefend}
                      className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-all flex items-center gap-2 shadow-[0_0_5px_#ffd700]"
                    >
                      <Shield className="w-4 h-4" />
                      Defensa Arcana
                    </button>
                  </div>
                )}
                
                {!battleState.isComplete && !battleState.isPlayerTurn && (
                  <div className="text-gold-400">
                    <Clock className="w-6 h-6 mx-auto mb-2 animate-pulse" />
                    <p>El monstruo prepara su asalto...</p>
                  </div>
                )}
                
                {/* Close Button */}
                {battleState.isComplete && (
                  <button
                    onClick={handleBattleComplete}
                    className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all shadow-[0_0_5px_#ffd700]"
                  >
                    Continuar la Conquista
                  </button>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}