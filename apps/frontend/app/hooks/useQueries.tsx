import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { questionsService } from '@/services/questions.service';
import { battlesService } from '@/services/battles.service';
import { questsService } from '@/services/quests.service';
import { useNotifications } from '@/components/ui/EpicNotification';
import { Trophy, Sword, Star } from 'lucide-react';

// Questions hooks
export function useQuestions(filters = {}) {
  return useQuery({
    queryKey: ['questions', filters],
    queryFn: () => questionsService.getQuestions(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useRandomQuestions(subjectId?: string, count = 5) {
  return useQuery({
    queryKey: ['questions', 'random', subjectId, count],
    queryFn: () => questionsService.getRandomQuestions(subjectId, count),
    enabled: false, // Manual trigger
  });
}

// Battle hooks
export function useCurrentBattle() {
  return useQuery({
    queryKey: ['battle', 'current'],
    queryFn: () => battlesService.getCurrentBattle(),
    refetchInterval: 5000, // Refetch every 5 seconds during battle
  });
}

export function useStartBattle() {
  const queryClient = useQueryClient();
  const { showNotification } = useNotifications();
  
  return useMutation({
    mutationFn: battlesService.startBattle,
    onSuccess: (battle) => {
      queryClient.invalidateQueries({ queryKey: ['battle', 'current'] });
      showNotification({
        type: 'info',
        title: '¡Batalla Iniciada!',
        message: `Te enfrentas a ${battle.enemy_name}`,
        icon: <Sword className="w-6 h-6" />,
        visual: 'shake',
        duration: 3000,
      });
    },
    onError: (error) => {
      showNotification({
        type: 'error',
        title: 'Error',
        message: 'No se pudo iniciar la batalla',
        duration: 3000,
      });
    },
  });
}

export function useSubmitAnswer(battleId: string) {
  const queryClient = useQueryClient();
  const { showNotification } = useNotifications();
  
  return useMutation({
    mutationFn: (answer: any) => battlesService.submitAnswer(battleId, answer),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['battle', 'current'] });
      
      if (result.is_correct) {
        if (result.is_critical) {
          showNotification({
            type: 'success',
            title: '¡GOLPE CRÍTICO!',
            message: `${result.damage_dealt} de daño`,
            visual: 'explosion',
            duration: 2000,
          });
        }
      }
    },
  });
}

// Quest hooks
export function useUserQuests() {
  return useQuery({
    queryKey: ['quests', 'user'],
    queryFn: () => questsService.getUserQuests(),
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useDailyQuests() {
  return useQuery({
    queryKey: ['quests', 'daily'],
    queryFn: () => questsService.getDailyQuests(),
    refetchInterval: 60 * 60 * 1000, // Refetch every hour
  });
}

export function useQuestStreak() {
  return useQuery({
    queryKey: ['quests', 'streak'],
    queryFn: () => questsService.getQuestStreak(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useUpdateQuestProgress() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: questsService.updateQuestProgress,
    onSuccess: (updatedQuest) => {
      queryClient.invalidateQueries({ queryKey: ['quests'] });
      
      if (updatedQuest.is_completed) {
        const { showNotification } = useNotifications();
        showNotification({
          type: 'quest_complete',
          title: '¡Misión Completada!',
          message: updatedQuest.quest.title,
          icon: <Star className="w-6 h-6" />,
          visual: 'sparkle',
          duration: 4000,
          actions: [
            {
              label: 'Reclamar Recompensa',
              onClick: () => {
                // Trigger claim reward
              },
            },
          ],
        });
      }
    },
  });
}

export function useClaimQuestReward() {
  const queryClient = useQueryClient();
  const { showNotification } = useNotifications();
  
  return useMutation({
    mutationFn: questsService.claimQuestReward,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['quests'] });
      queryClient.invalidateQueries({ queryKey: ['user'] });
      
      showNotification({
        type: 'loot',
        title: '¡Recompensa Obtenida!',
        message: `+${result.rewards.experience} XP${result.rewards.orbs ? `, +${result.rewards.orbs} Orbs` : ''}`,
        icon: <Trophy className="w-6 h-6" />,
        visual: 'sparkle',
        duration: 5000,
      });
    },
  });
}