'use client';

import React from 'react';
import Image from 'next/image';

interface AchievementIconProps {
  achievementType: string;
  size?: number;
  className?: string;
}

const ACHIEVEMENT_ICONS: Record<string, string> = {
  // Logros de días
  '7-days': '/assets/images/achievements/7-days.png.jpg',
  '30-days': '/assets/images/achievements/30-days.png.jpg',
  '100-days': '/assets/images/achievements/100-days.png.jpg',
  
  // Logros de puntos
  '10-points': '/assets/images/achievements/10-points.png.jpg',
  '25-points': '/assets/images/achievements/25-points.png.jpg',
  
  // Logros de unidades
  '5-units': '/assets/images/achievements/5-units.png.jpg',
  '10-units': '/assets/images/achievements/10-units.png.jpg',
  '20-units': '/assets/images/achievements/20-units.png.jpg',
  'first-unit': '/assets/images/achievements/first-unit.png.jpg',
  
  // Logros sociales
  'first-friend': '/assets/images/achievements/first-friend.png.jpg',
  
  // Logros de progreso
  'consistency': '/assets/images/achievements/consistency.png.jpg',
  'improvement': '/assets/images/achievements/improvement.png.jpg',
  'subject-master': '/assets/images/achievements/subject-master.png.jpg',
  
  // Logros generales
  'achievement': '/assets/images/achievements/ACHIEVEMENT.PNG.jpg',
  'battle': '/assets/images/achievements/BATTLE.PNG.jpg',
  'guild': '/assets/images/achievements/GUILD.PNG.jpg',
  'quest': '/assets/images/achievements/QUEST.PNG.jpg'
};

export default function AchievementIcon({ achievementType, size = 64, className = '' }: AchievementIconProps) {
  const iconPath = ACHIEVEMENT_ICONS[achievementType.toLowerCase()] || ACHIEVEMENT_ICONS['achievement'];

  return (
    <div className={`relative ${className}`} style={{ width: size, height: size }}>
      <Image
        src={iconPath}
        alt={`Logro ${achievementType}`}
        width={size}
        height={size}
        className="rounded-lg object-cover"
        onError={(e) => {
          // Fallback to emoji if image fails to load
          const target = e.target as HTMLImageElement;
          target.style.display = 'none';
          const parent = target.parentElement;
          if (parent) {
            parent.innerHTML = `<div class="w-full h-full rounded-lg flex items-center justify-center text-2xl bg-yellow-500 text-white">🏆</div>`;
          }
        }}
      />
    </div>
  );
}

export function getAchievementIconPath(achievementType: string): string {
  return ACHIEVEMENT_ICONS[achievementType.toLowerCase()] || ACHIEVEMENT_ICONS['achievement'];
} 