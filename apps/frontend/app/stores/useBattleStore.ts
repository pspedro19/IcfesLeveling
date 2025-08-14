import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface Enemy {
  id: string;
  name: string;
  level: number;
  hp: number;
  maxHp: number;
  difficulty: string;
  imageUrl?: string;
}

interface BattleState {
  // State
  currentEnemy: Enemy | null;
  playerHp: number;
  playerMaxHp: number;
  playerMp: number;
  playerMaxMp: number;
  combo: number;
  isInBattle: boolean;
  battleLog: string[];
  
  // Battle stats
  damageDealt: number;
  damageTaken: number;
  questionsAnswered: number;
  correctAnswers: number;
  
  // Actions
  startBattle: (enemy: Enemy) => void;
  endBattle: (victory: boolean) => void;
  dealDamage: (damage: number, isCritical?: boolean) => void;
  takeDamage: (damage: number) => void;
  healPlayer: (amount: number) => void;
  useMp: (amount: number) => void;
  increaseCombo: () => void;
  resetCombo: () => void;
  addBattleLog: (message: string) => void;
  updateBattleStats: (correct: boolean) => void;
}

export const useBattleStore = create<BattleState>()(
  devtools(
    (set, get) => ({
      // Initial state
      currentEnemy: null,
      playerHp: 100,
      playerMaxHp: 100,
      playerMp: 50,
      playerMaxMp: 50,
      combo: 0,
      isInBattle: false,
      battleLog: [],
      damageDealt: 0,
      damageTaken: 0,
      questionsAnswered: 0,
      correctAnswers: 0,
      
      // Start battle
      startBattle: (enemy: Enemy) => {
        set({
          currentEnemy: enemy,
          isInBattle: true,
          combo: 0,
          battleLog: [`¡${enemy.name} aparece!`],
          damageDealt: 0,
          damageTaken: 0,
          questionsAnswered: 0,
          correctAnswers: 0,
        });
      },
      
      // End battle
      endBattle: (victory: boolean) => {
        const state = get();
        const message = victory 
          ? `¡Victoria! Has derrotado a ${state.currentEnemy?.name}`
          : `Has sido derrotado por ${state.currentEnemy?.name}`;
          
        set({
          isInBattle: false,
          combo: 0,
          battleLog: [...state.battleLog, message],
        });
      },
      
      // Deal damage to enemy
      dealDamage: (damage: number, isCritical = false) => {
        const state = get();
        if (!state.currentEnemy) return;
        
        const newHp = Math.max(0, state.currentEnemy.hp - damage);
        const message = isCritical
          ? `¡GOLPE CRÍTICO! ${damage} de daño`
          : `Infliges ${damage} de daño`;
          
        set({
          currentEnemy: { ...state.currentEnemy, hp: newHp },
          damageDealt: state.damageDealt + damage,
          battleLog: [...state.battleLog, message],
        });
        
        // Check if enemy defeated
        if (newHp === 0) {
          get().endBattle(true);
        }
      },
      
      // Take damage
      takeDamage: (damage: number) => {
        const state = get();
        const newHp = Math.max(0, state.playerHp - damage);
        
        set({
          playerHp: newHp,
          damageTaken: state.damageTaken + damage,
          battleLog: [...state.battleLog, `Recibes ${damage} de daño`],
        });
        
        // Check if player defeated
        if (newHp === 0) {
          get().endBattle(false);
        }
      },
      
      // Heal player
      healPlayer: (amount: number) => {
        const state = get();
        const newHp = Math.min(state.playerMaxHp, state.playerHp + amount);
        
        set({
          playerHp: newHp,
          battleLog: [...state.battleLog, `Te curas ${amount} HP`],
        });
      },
      
      // Use MP
      useMp: (amount: number) => {
        const state = get();
        const newMp = Math.max(0, state.playerMp - amount);
        
        set({ playerMp: newMp });
      },
      
      // Increase combo
      increaseCombo: () => {
        const state = get();
        set({
          combo: state.combo + 1,
          battleLog: [...state.battleLog, `¡Combo x${state.combo + 1}!`],
        });
      },
      
      // Reset combo
      resetCombo: () => {
        const state = get();
        if (state.combo > 0) {
          set({
            combo: 0,
            battleLog: [...state.battleLog, '¡Combo roto!'],
          });
        }
      },
      
      // Add battle log
      addBattleLog: (message: string) => {
        const state = get();
        set({
          battleLog: [...state.battleLog, message],
        });
      },
      
      // Update battle statistics
      updateBattleStats: (correct: boolean) => {
        const state = get();
        set({
          questionsAnswered: state.questionsAnswered + 1,
          correctAnswers: correct ? state.correctAnswers + 1 : state.correctAnswers,
        });
      },
    }),
    {
      name: 'battle-store',
    }
  )
);