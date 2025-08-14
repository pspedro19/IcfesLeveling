'use client';

import React from 'react';
import { motion } from 'framer-motion';

// Base skeleton component
function Skeleton({ className = '', ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <motion.div
      className={`bg-gray-200 dark:bg-gray-700 rounded animate-pulse ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      {...props}
    />
  );
}

// Unit card skeleton
export function UnitCardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 animate-pulse">
      <div className="flex items-center gap-4">
        <div className="w-16 h-16 bg-gray-300 dark:bg-gray-700 rounded-full" />
        <div className="flex-1">
          <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded w-3/4 mb-2" />
          <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-full" />
        </div>
      </div>
      <div className="mt-4">
        <div className="h-3 bg-gray-300 dark:bg-gray-700 rounded-full" />
      </div>
      <div className="grid grid-cols-3 gap-4 mt-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="text-center">
            <div className="w-8 h-8 bg-gray-300 dark:bg-gray-700 rounded mx-auto mb-1" />
            <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-12 mx-auto" />
            <div className="h-3 bg-gray-300 dark:bg-gray-700 rounded w-16 mx-auto mt-1" />
          </div>
        ))}
      </div>
    </div>
  );
}

// Progress dashboard skeleton
export function ProgressDashboardSkeleton() {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-teal-50 dark:from-gray-900 dark:to-gray-800 rounded-2xl p-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {/* Circular progress skeleton */}
        <div className="col-span-2 md:col-span-1">
          <div className="w-32 h-32 bg-gray-300 dark:bg-gray-700 rounded-full mx-auto" />
        </div>
        
        {/* Stats cards skeleton */}
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-4">
            <div className="w-8 h-8 bg-gray-300 dark:bg-gray-700 rounded mx-auto mb-2" />
            <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded w-16 mx-auto mb-2" />
            <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-20 mx-auto" />
          </div>
        ))}
      </div>
      
      {/* Achievement section skeleton */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4">
        <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded w-32 mb-3" />
        <div className="flex gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="w-8 h-8 bg-gray-300 dark:bg-gray-700 rounded-full" />
          ))}
        </div>
      </div>
    </div>
  );
}

// Learning path skeleton
export function LearningPathSkeleton() {
  return (
    <div className="relative py-12">
      <div className="absolute left-1/2 top-0 bottom-0 w-1 bg-gray-300 dark:bg-gray-600 transform -translate-x-1/2" />
      
      {Array.from({ length: 3 }).map((_, phaseIndex) => (
        <div key={phaseIndex} className={`relative mb-16 ${phaseIndex % 2 === 0 ? 'pr-1/2' : 'pl-1/2 ml-auto'}`}>
          {/* Phase marker skeleton */}
          <div className="absolute left-1/2 top-8 w-12 h-12 bg-gray-300 dark:bg-gray-600 rounded-full transform -translate-x-1/2 -translate-y-1/2" />
          
          {/* Phase card skeleton */}
          <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 ${
            phaseIndex % 2 === 0 ? 'mr-8' : 'ml-8'
          }`}>
            <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded w-3/4 mb-2" />
            <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-full mb-4" />
            
            {/* Units skeleton */}
            <div className="space-y-2">
              {Array.from({ length: 2 }).map((_, unitIndex) => (
                <div key={unitIndex} className="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                  <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-2/3 mb-1" />
                  <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-full" />
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Table skeleton
export function TableSkeleton({ rows = 5, columns = 4 }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg overflow-hidden">
      {/* Header skeleton */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: columns }).map((_, i) => (
            <div key={i} className="h-4 bg-gray-300 dark:bg-gray-700 rounded" />
          ))}
        </div>
      </div>
      
      {/* Rows skeleton */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-4 gap-4">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <div key={colIndex} className="h-4 bg-gray-200 dark:bg-gray-600 rounded" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// Card skeleton
export function CardSkeleton({ className = '' }) {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg p-6 ${className}`}>
      <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded w-3/4 mb-4" />
      <div className="space-y-3">
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-full" />
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-5/6" />
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-4/6" />
      </div>
    </div>
  );
}

// List skeleton
export function ListSkeleton({ items = 3, className = '' }) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="w-10 h-10 bg-gray-300 dark:bg-gray-600 rounded-full" />
          <div className="flex-1">
            <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-1" />
            <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

// Grid skeleton
export function GridSkeleton({ rows = 2, cols = 3, className = '' }) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-${cols} gap-6 ${className}`}>
      {Array.from({ length: rows * cols }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}
