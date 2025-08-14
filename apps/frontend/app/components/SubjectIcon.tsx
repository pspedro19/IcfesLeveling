'use client';

import React from 'react';
import Image from 'next/image';

interface SubjectIconProps {
  subjectName: string;
  size?: number;
  className?: string;
}

const SUBJECT_ICONS: Record<string, string> = {
  'Matemáticas': '/assets/images/subjects/matematicasicon.png',
  'Ciencias Naturales': '/assets/images/subjects/cienciasnaturalesicon.png',
  'Ciencias': '/assets/images/subjects/cienciasnaturalesicon.png',
  'Lenguaje': '/assets/images/subjects/lecturaicon.png',
  'Lectura Crítica': '/assets/images/subjects/lecturaicon.png',
  'Ciencias Sociales': '/assets/images/subjects/socialesicon.png',
  'Sociales': '/assets/images/subjects/socialesicon.png',
  'Inglés': '/assets/images/subjects/englishicon.png',
  'English': '/assets/images/subjects/englishicon.png'
};

export default function SubjectIcon({ subjectName, size = 64, className = '' }: SubjectIconProps) {
  const iconPath = SUBJECT_ICONS[subjectName] || SUBJECT_ICONS['Matemáticas']; // Default fallback

  return (
    <div className={`relative ${className}`} style={{ width: size, height: size }}>
      <Image
        src={iconPath}
        alt={`Icono de ${subjectName}`}
        width={size}
        height={size}
        className="rounded-full object-cover"
        onError={(e) => {
          // Fallback to emoji if image fails to load
          const target = e.target as HTMLImageElement;
          target.style.display = 'none';
          const parent = target.parentElement;
          if (parent) {
            parent.innerHTML = `<div class="w-full h-full rounded-full flex items-center justify-center text-2xl bg-purple-500 text-white">${subjectName.charAt(0).toUpperCase()}</div>`;
          }
        }}
      />
    </div>
  );
}

export function getSubjectIconPath(subjectName: string): string {
  return SUBJECT_ICONS[subjectName] || SUBJECT_ICONS['Matemáticas'];
} 