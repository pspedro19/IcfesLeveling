'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Clock, Target, Zap } from 'lucide-react';

interface PriorityBadgeProps {
  priority: 'high' | 'medium' | 'low' | 'critical';
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  className?: string;
}

const priorityConfig = {
  critical: {
    color: 'bg-red-500 text-white',
    icon: AlertTriangle,
    label: 'Crítica',
    pulse: true
  },
  high: {
    color: 'bg-orange-500 text-white',
    icon: Zap,
    label: 'Alta',
    pulse: false
  },
  medium: {
    color: 'bg-yellow-500 text-white',
    icon: Target,
    label: 'Media',
    pulse: false
  },
  low: {
    color: 'bg-green-500 text-white',
    icon: Clock,
    label: 'Baja',
    pulse: false
  }
};

export function PriorityBadge({ 
  priority, 
  size = 'md', 
  animated = true,
  className = ""
}: PriorityBadgeProps) {
  const config = priorityConfig[priority];
  const Icon = config.icon;
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base'
  };

  return (
    <motion.div
      className={`
        inline-flex items-center gap-2 rounded-full font-medium
        ${config.color} ${sizeClasses[size]} ${className}
        ${config.pulse && animated ? 'animate-pulse' : ''}
      `}
      whileHover={animated ? { scale: 1.05 } : {}}
      whileTap={animated ? { scale: 0.95 } : {}}
      initial={animated ? { opacity: 0, scale: 0.8 } : {}}
      animate={animated ? { opacity: 1, scale: 1 } : {}}
      transition={{ duration: 0.2 }}
    >
      <Icon className={`w-3 h-3 ${size === 'lg' ? 'w-4 h-4' : ''}`} />
      <span>{config.label}</span>
    </motion.div>
  );
}
