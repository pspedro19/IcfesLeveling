'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronDown, 
  Lock, 
  Video, 
  Clock, 
  Star, 
  Sparkles,
  BookOpen,
  Target,
  Lightbulb
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { PriorityBadge } from './ui/PriorityBadge';

interface UnitVideo {
  id: string;
  title: string;
  duration: string;
  youtube_id: string;
  watched: boolean;
}

interface UnitObjective {
  id: string;
  description: string;
  completed: boolean;
}

interface AITip {
  id: string;
  tip: string;
  category: 'strategy' | 'motivation' | 'technique';
}

interface Unit {
  id: string;
  number: number;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low' | 'critical';
  isUnlocked: boolean;
  progress: number;
  videoCount: number;
  estimatedHours: number;
  xpReward: number;
  aiRecommended: boolean;
  videos: UnitVideo[];
  objectives: UnitObjective[];
  aiTips: AITip[];
}

interface UnitCardProps {
  unit: Unit;
  className?: string;
}

function QuickStat({ icon, value, label }: { icon: React.ReactNode; value: string | number; label: string }) {
  return (
    <div className="text-center">
      <div className="flex justify-center mb-1 text-gray-600 dark:text-gray-400">
        {icon}
      </div>
      <div className="text-lg font-bold text-gray-900 dark:text-white">{value}</div>
      <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
    </div>
  );
}

function TabButton({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium transition-colors ${
        active
          ? 'text-teal-600 border-b-2 border-teal-600'
          : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
      }`}
    >
      {label === 'overview' && 'Resumen'}
      {label === 'videos' && 'Videos'}
      {label === 'objectives' && 'Objetivos'}
      {label === 'ai-tips' && 'Tips IA'}
    </button>
  );
}

function VideoList({ videos }: { videos: UnitVideo[] }) {
  return (
    <div className="space-y-3">
      {videos.map((video) => (
        <div key={video.id} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className={`w-3 h-3 rounded-full ${video.watched ? 'bg-green-500' : 'bg-gray-300'}`} />
          <div className="flex-1">
            <h4 className="font-medium text-gray-900 dark:text-white">{video.title}</h4>
            <p className="text-sm text-gray-500 dark:text-gray-400">{video.duration}</p>
          </div>
          <Badge variant={video.watched ? 'default' : 'secondary'}>
            {video.watched ? 'Visto' : 'Pendiente'}
          </Badge>
        </div>
      ))}
    </div>
  );
}

function ObjectivesList({ objectives }: { objectives: UnitObjective[] }) {
  return (
    <div className="space-y-3">
      {objectives.map((objective) => (
        <div key={objective.id} className="flex items-center gap-3">
          <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
            objective.completed 
              ? 'border-green-500 bg-green-500 text-white' 
              : 'border-gray-300 dark:border-gray-600'
          }`}>
            {objective.completed && <Star className="w-3 h-3" />}
          </div>
          <span className={`text-sm ${objective.completed ? 'line-through text-gray-500' : 'text-gray-700 dark:text-gray-300'}`}>
            {objective.description}
          </span>
        </div>
      ))}
    </div>
  );
}

function AITips({ tips }: { tips: AITip[] }) {
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'strategy': return <Target className="w-4 h-4" />;
      case 'motivation': return <Lightbulb className="w-4 h-4" />;
      case 'technique': return <BookOpen className="w-4 h-4" />;
      default: return <Sparkles className="w-4 h-4" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'strategy': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300';
      case 'motivation': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'technique': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
      default: return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300';
    }
  };

  return (
    <div className="space-y-3">
      {tips.map((tip) => (
        <div key={tip.id} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Badge className={getCategoryColor(tip.category)}>
              {getCategoryIcon(tip.category)}
              {tip.category === 'strategy' && 'Estrategia'}
              {tip.category === 'motivation' && 'Motivación'}
              {tip.category === 'technique' && 'Técnica'}
            </Badge>
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300 font-caveat text-lg">
            {tip.tip}
          </p>
        </div>
      ))}
    </div>
  );
}

export function UnitCard({ unit, className = '' }: UnitCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`
        relative overflow-hidden rounded-2xl 
        ${unit.isUnlocked 
          ? 'bg-white dark:bg-gray-800 shadow-lg hover:shadow-xl' 
          : 'bg-gray-100 dark:bg-gray-900 opacity-75'
        }
        border-2 transition-all duration-300
        ${unit.isUnlocked 
          ? 'border-teal-500 dark:border-teal-600' 
          : 'border-gray-300 dark:border-gray-700'
        }
        ${className}
      `}
    >
      {/* Priority Badge */}
      <div className="absolute top-4 right-4">
        <PriorityBadge priority={unit.priority} />
      </div>

      {/* Unit Header */}
      <div className="p-6">
        <div className="flex items-center gap-4">
          {/* Unit Icon/Number */}
          <div className={`
            w-16 h-16 rounded-full flex items-center justify-center
            ${unit.isUnlocked 
              ? 'bg-gradient-to-br from-teal-500 to-blue-500' 
              : 'bg-gray-400'
            }
          `}>
            {unit.isUnlocked ? (
              <span className="text-2xl font-bold text-white">{unit.number}</span>
            ) : (
              <Lock className="w-6 h-6 text-white" />
            )}
          </div>

          {/* Unit Info */}
          <div className="flex-1">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              {unit.title}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {unit.description}
            </p>
            
            {/* AI Recommendation Badge */}
            {unit.aiRecommended && (
              <div className="inline-flex items-center gap-1 mt-2 px-3 py-1 
                            bg-purple-100 dark:bg-purple-900/30 rounded-full">
                <Sparkles className="w-4 h-4 text-purple-600" />
                <span className="text-xs font-medium text-purple-700 dark:text-purple-300">
                  Recomendado por IA
                </span>
              </div>
            )}
          </div>

          {/* Expand Button */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <ChevronDown className={`
              w-5 h-5 transition-transform
              ${isExpanded ? 'rotate-180' : ''}
            `} />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-600 dark:text-gray-400">Progreso</span>
            <span className="font-bold text-teal-600">{unit.progress}%</span>
          </div>
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${unit.progress}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="h-full bg-gradient-to-r from-teal-500 to-blue-500"
            />
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <QuickStat icon={<Video />} value={unit.videoCount} label="Videos" />
          <QuickStat icon={<Clock />} value={`${unit.estimatedHours}h`} label="Tiempo" />
          <QuickStat icon={<Star />} value={unit.xpReward} label="XP" />
        </div>
      </div>

      {/* Expandable Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            className="border-t border-gray-200 dark:border-gray-700"
          >
            {/* Tab Navigation */}
            <div className="flex border-b border-gray-200 dark:border-gray-700">
              {['overview', 'videos', 'objectives', 'ai-tips'].map((tab) => (
                <TabButton
                  key={tab}
                  active={activeTab === tab}
                  onClick={() => setActiveTab(tab)}
                  label={tab}
                />
              ))}
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {activeTab === 'videos' && <VideoList videos={unit.videos} />}
              {activeTab === 'objectives' && <ObjectivesList objectives={unit.objectives} />}
              {activeTab === 'ai-tips' && <AITips tips={unit.aiTips} />}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
