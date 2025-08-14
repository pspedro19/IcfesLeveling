import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { devtools } from 'zustand/middleware';

export interface Quest {
  id: string;
  title: string;
  description: string;
  progress: number;
  total: number;
  type: 'daily' | 'weekly' | 'special';
  xpReward: number;
  orbsReward?: number;
  completed: boolean;
  expiresAt?: Date;
}

interface QuestState {
  // State
  dailyQuests: Quest[];
  weeklyQuests: Quest[];
  specialQuests: Quest[];
  streakDays: number;
  freezeShields: number;
  lastCompletedDate: string | null;
  
  // Actions
  setQuests: (quests: Quest[], type: 'daily' | 'weekly' | 'special') => void;
  updateQuestProgress: (questId: string, progress: number) => void;
  completeQuest: (questId: string) => void;
  updateStreak: (days: number) => void;
  useFreeze: () => boolean;
  checkAndUpdateStreak: () => void;
  resetDailyQuests: () => void;
}

export const useQuestStore = create<QuestState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        dailyQuests: [],
        weeklyQuests: [],
        specialQuests: [],
        streakDays: 0,
        freezeShields: 3,
        lastCompletedDate: null,
        
        // Set quests
        setQuests: (quests: Quest[], type: 'daily' | 'weekly' | 'special') => {
          const update: Partial<QuestState> = {};
          
          switch (type) {
            case 'daily':
              update.dailyQuests = quests;
              break;
            case 'weekly':
              update.weeklyQuests = quests;
              break;
            case 'special':
              update.specialQuests = quests;
              break;
          }
          
          set(update);
        },
        
        // Update quest progress
        updateQuestProgress: (questId: string, progress: number) => {
          const state = get();
          
          // Find and update quest in all categories
          const updateQuestInArray = (quests: Quest[]) => {
            return quests.map(quest => {
              if (quest.id === questId) {
                const newProgress = Math.min(progress, quest.total);
                const completed = newProgress >= quest.total;
                
                // If quest just completed, trigger completion
                if (completed && !quest.completed) {
                  get().completeQuest(questId);
                }
                
                return { ...quest, progress: newProgress, completed };
              }
              return quest;
            });
          };
          
          set({
            dailyQuests: updateQuestInArray(state.dailyQuests),
            weeklyQuests: updateQuestInArray(state.weeklyQuests),
            specialQuests: updateQuestInArray(state.specialQuests),
          });
        },
        
        // Complete quest
        completeQuest: (questId: string) => {
          const state = get();
          const today = new Date().toDateString();
          
          // Update last completed date
          set({ lastCompletedDate: today });
          
          // Check and update streak
          get().checkAndUpdateStreak();
          
          console.log(`Quest ${questId} completed!`);
        },
        
        // Update streak
        updateStreak: (days: number) => {
          set({ streakDays: days });
        },
        
        // Use freeze shield
        useFreeze: () => {
          const state = get();
          
          if (state.freezeShields > 0) {
            set({ freezeShields: state.freezeShields - 1 });
            return true;
          }
          
          return false;
        },
        
        // Check and update streak
        checkAndUpdateStreak: () => {
          const state = get();
          const today = new Date();
          const todayString = today.toDateString();
          
          if (state.lastCompletedDate) {
            const lastDate = new Date(state.lastCompletedDate);
            const daysDiff = Math.floor((today.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24));
            
            if (daysDiff === 0) {
              // Same day, no change
              return;
            } else if (daysDiff === 1) {
              // Consecutive day, increase streak
              set({ streakDays: state.streakDays + 1 });
            } else if (daysDiff > 1) {
              // Streak broken, reset unless freeze shield is used
              if (state.freezeShields > 0) {
                // Auto-use freeze shield
                get().useFreeze();
              } else {
                set({ streakDays: 0 });
              }
            }
          } else {
            // First completion
            set({ streakDays: 1 });
          }
        },
        
        // Reset daily quests
        resetDailyQuests: () => {
          const state = get();
          
          // Reset progress for daily quests
          const resetQuests = state.dailyQuests.map(quest => ({
            ...quest,
            progress: 0,
            completed: false,
          }));
          
          set({ dailyQuests: resetQuests });
        },
      }),
      {
        name: 'quest-storage',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          streakDays: state.streakDays,
          freezeShields: state.freezeShields,
          lastCompletedDate: state.lastCompletedDate,
        }),
      }
    ),
    {
      name: 'quest-store',
    }
  )
);