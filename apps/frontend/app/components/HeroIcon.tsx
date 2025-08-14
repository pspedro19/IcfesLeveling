'use client';

import React from 'react';
import Image from 'next/image';

interface HeroIconProps {
  heroClass: string;
  size?: number;
  className?: string;
}

const HERO_ICONS: Record<string, string> = {
  'warrior': '/assets/images/heroes/warrior-knowledge.png.jpg',
  'mage': '/assets/images/heroes/mage-quantum.png.jpg',
  'archer': '/assets/images/heroes/archer-wisdom.png.jpg',
  'assassin': '/assets/images/heroes/assassin-logic.png.jpg',
  'priest': '/assets/images/heroes/priest-learning.png.jpg',
  'warrior-knowledge': '/assets/images/heroes/warrior-knowledge.png.jpg',
  'mage-quantum': '/assets/images/heroes/mage-quantum.png.jpg',
  'archer-wisdom': '/assets/images/heroes/archer-wisdom.png.jpg',
  'assassin-logic': '/assets/images/heroes/assassin-logic.png.jpg',
  'priest-learning': '/assets/images/heroes/priest-learning.png.jpg'
};

export default function HeroIcon({ heroClass, size = 64, className = '' }: HeroIconProps) {
  const iconPath = HERO_ICONS[heroClass.toLowerCase()] || HERO_ICONS['warrior'];

  return (
    <div className={`relative ${className}`} style={{ width: size, height: size }}>
      <Image
        src={iconPath}
        alt={`Icono de ${heroClass}`}
        width={size}
        height={size}
        className="rounded-full object-cover"
        onError={(e) => {
          // Fallback to emoji if image fails to load
          const target = e.target as HTMLImageElement;
          target.style.display = 'none';
          const parent = target.parentElement;
          if (parent) {
            parent.innerHTML = `<div class="w-full h-full rounded-full flex items-center justify-center text-2xl bg-purple-500 text-white">⚔️</div>`;
          }
        }}
      />
    </div>
  );
}

export function getHeroIconPath(heroClass: string): string {
  return HERO_ICONS[heroClass.toLowerCase()] || HERO_ICONS['warrior'];
} 