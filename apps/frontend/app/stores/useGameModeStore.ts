import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { devtools } from 'zustand/middleware';

export type GameMode = 'casual' | 'gated';

interface GameModeState {
  // State
  mode: GameMode;
  modeSettings: {
    requireAllUnits: boolean;
    minimumAccuracy: number;
    unlockRequirements: boolean;
    showWeaknessWarnings: boolean;
    allowSkipContent: boolean;
    rankProgressionLocked: boolean;
  };
  
  // Actions
  setMode: (mode: GameMode) => void;
  updateSettings: (settings: Partial<GameModeState['modeSettings']>) => void;
  canAccessContent: (accuracy: number, hasWeaknesses: boolean) => boolean;
  getModeDescription: () => string;
}

const defaultSettings = {
  casual: {
    requireAllUnits: false,
    minimumAccuracy: 60,
    unlockRequirements: false,
    showWeaknessWarnings: true,
    allowSkipContent: true,
    rankProgressionLocked: false
  },
  gated: {
    requireAllUnits: true,
    minimumAccuracy: 80,
    unlockRequirements: true,
    showWeaknessWarnings: true,
    allowSkipContent: false,
    rankProgressionLocked: true
  }
};

export const useGameModeStore = create<GameModeState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        mode: 'gated',
        modeSettings: defaultSettings.gated,
        
        // Set game mode
        setMode: (mode: GameMode) => {
          set({
            mode,
            modeSettings: defaultSettings[mode]
          });
        },
        
        // Update specific settings
        updateSettings: (settings: Partial<GameModeState['modeSettings']>) => {
          const state = get();
          set({
            modeSettings: {
              ...state.modeSettings,
              ...settings
            }
          });
        },
        
        // Check if user can access content based on mode
        canAccessContent: (accuracy: number, hasWeaknesses: boolean) => {
          const { modeSettings } = get();
          
          if (!modeSettings.unlockRequirements) {
            return true; // Casual mode - always allow access
          }
          
          // Gated mode - check requirements
          if (accuracy < modeSettings.minimumAccuracy) {
            return false;
          }
          
          if (hasWeaknesses && modeSettings.requireAllUnits) {
            return false;
          }
          
          return true;
        },
        
        // Get mode description
        getModeDescription: () => {
          const { mode } = get();
          
          if (mode === 'casual') {
            return 'Practica libremente sin restricciones. Ideal para explorar y aprender a tu propio ritmo.';
          }
          
          return 'Progresión estructurada que requiere dominar cada tema antes de avanzar. Diseñado para máximo aprendizaje.';
        }
      }),
      {
        name: 'game-mode-storage',
        storage: createJSONStorage(() => localStorage)
      }
    ),
    {
      name: 'game-mode-store'
    }
  )
);