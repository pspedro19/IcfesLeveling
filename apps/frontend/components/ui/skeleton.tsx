/**
 * Universal Skeleton Loaders
 * Consistent loading states across the application
 */

import { cn } from '@/lib/utils';
import React from 'react';

// Base Skeleton Component
export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%]",
        className
      )}
      {...props}
    />
  );
}

// Text Skeleton
export function SkeletonText({
  lines = 3,
  className,
  ...props
}: {
  lines?: number;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("space-y-2", className)} {...props}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn("h-4", i === lines - 1 && "w-3/4")}
        />
      ))}
    </div>
  );
}

// Card Skeleton
export function SkeletonCard({
  className,
  showImage = true,
  ...props
}: {
  showImage?: boolean;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-xl border border-gray-200 bg-white p-6 shadow-sm",
        className
      )}
      {...props}
    >
      {showImage && <Skeleton className="h-48 w-full rounded-lg mb-4" />}
      <Skeleton className="h-6 w-3/4 mb-2" />
      <SkeletonText lines={2} className="mb-4" />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-20 rounded-md" />
        <Skeleton className="h-8 w-20 rounded-md" />
      </div>
    </div>
  );
}

// Table Skeleton
export function SkeletonTable({
  rows = 5,
  columns = 4,
  className,
  ...props
}: {
  rows?: number;
  columns?: number;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("w-full", className)} {...props}>
      {/* Header */}
      <div className="border-b border-gray-200 pb-3 mb-3">
        <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-4" />
          ))}
        </div>
      </div>
      
      {/* Rows */}
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div
            key={rowIndex}
            className="grid gap-4"
            style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
          >
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton
                key={colIndex}
                className={cn(
                  "h-4",
                  colIndex === 0 && "w-4/5"
                )}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// Avatar Skeleton
export function SkeletonAvatar({
  size = "md",
  className,
  ...props
}: {
  size?: "sm" | "md" | "lg" | "xl";
} & React.HTMLAttributes<HTMLDivElement>) {
  const sizeClasses = {
    sm: "h-8 w-8",
    md: "h-10 w-10",
    lg: "h-12 w-12",
    xl: "h-16 w-16"
  };

  return (
    <Skeleton
      className={cn("rounded-full", sizeClasses[size], className)}
      {...props}
    />
  );
}

// Button Skeleton
export function SkeletonButton({
  size = "md",
  className,
  ...props
}: {
  size?: "sm" | "md" | "lg";
} & React.HTMLAttributes<HTMLDivElement>) {
  const sizeClasses = {
    sm: "h-8 w-20",
    md: "h-10 w-28",
    lg: "h-12 w-36"
  };

  return (
    <Skeleton
      className={cn("rounded-md", sizeClasses[size], className)}
      {...props}
    />
  );
}

// Question Card Skeleton
export function SkeletonQuestionCard({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-xl border border-gray-200 bg-white p-6 shadow-sm",
        className
      )}
      {...props}
    >
      <div className="flex justify-between items-center mb-4">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-16" />
      </div>
      <Skeleton className="h-6 w-full mb-4" />
      <Skeleton className="h-5 w-4/5 mb-6" />
      
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full rounded-lg" />
        ))}
      </div>
      
      <Skeleton className="h-10 w-full mt-6 rounded-md" />
    </div>
  );
}

// Dashboard Stats Skeleton
export function SkeletonStats({
  cards = 4,
  className,
  ...props
}: {
  cards?: number;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4", className)}
      {...props}
    >
      {Array.from({ length: cards }).map((_, i) => (
        <div key={i} className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <Skeleton className="h-4 w-20" />
            <SkeletonAvatar size="sm" />
          </div>
          <Skeleton className="h-8 w-24 mb-1" />
          <Skeleton className="h-3 w-16" />
        </div>
      ))}
    </div>
  );
}

// List Skeleton
export function SkeletonList({
  items = 5,
  showAvatar = true,
  className,
  ...props
}: {
  items?: number;
  showAvatar?: boolean;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("space-y-4", className)} {...props}>
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center gap-4">
          {showAvatar && <SkeletonAvatar size="md" />}
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-8 w-16 rounded-md" />
        </div>
      ))}
    </div>
  );
}

// Form Skeleton
export function SkeletonForm({
  fields = 4,
  className,
  ...props
}: {
  fields?: number;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("space-y-6", className)} {...props}>
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i}>
          <Skeleton className="h-4 w-24 mb-2" />
          <Skeleton className="h-10 w-full rounded-md" />
        </div>
      ))}
      <div className="flex gap-3 pt-4">
        <Skeleton className="h-10 w-24 rounded-md" />
        <Skeleton className="h-10 w-24 rounded-md" />
      </div>
    </div>
  );
}

// Chart Skeleton
export function SkeletonChart({
  type = "bar",
  className,
  ...props
}: {
  type?: "bar" | "line" | "pie";
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-xl border border-gray-200 bg-white p-6",
        className
      )}
      {...props}
    >
      <div className="mb-4">
        <Skeleton className="h-6 w-1/3 mb-2" />
        <Skeleton className="h-4 w-1/2" />
      </div>
      
      {type === "bar" && (
        <div className="flex items-end gap-2 h-48">
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton
              key={i}
              className="flex-1"
              style={{ height: `${Math.random() * 100 + 20}%` }}
            />
          ))}
        </div>
      )}
      
      {type === "line" && (
        <Skeleton className="h-48 w-full rounded-lg" />
      )}
      
      {type === "pie" && (
        <div className="flex justify-center">
          <Skeleton className="h-48 w-48 rounded-full" />
        </div>
      )}
    </div>
  );
}

// Loading Page Skeleton
export function SkeletonPage({
  showHeader = true,
  showSidebar = false,
  className,
  ...props
}: {
  showHeader?: boolean;
  showSidebar?: boolean;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("min-h-screen bg-gray-50", className)} {...props}>
      {showHeader && (
        <div className="border-b border-gray-200 bg-white px-6 py-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-8 w-32" />
            <div className="flex items-center gap-4">
              <Skeleton className="h-8 w-24" />
              <SkeletonAvatar size="md" />
            </div>
          </div>
        </div>
      )}
      
      <div className="flex">
        {showSidebar && (
          <div className="w-64 border-r border-gray-200 bg-white p-4">
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full rounded-md" />
              ))}
            </div>
          </div>
        )}
        
        <div className="flex-1 p-6">
          <Skeleton className="h-8 w-1/3 mb-6" />
          <SkeletonStats className="mb-6" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SkeletonChart type="bar" />
            <SkeletonChart type="line" />
          </div>
        </div>
      </div>
    </div>
  );
}

// Video Player Skeleton
export function SkeletonVideo({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("relative", className)} {...props}>
      <Skeleton className="aspect-video w-full rounded-lg" />
      <div className="absolute inset-0 flex items-center justify-center">
        <Skeleton className="h-16 w-16 rounded-full" />
      </div>
    </div>
  );
}

// Hook for skeleton loading
export function useSkeleton(isLoading: boolean, delay = 0) {
  const [showSkeleton, setShowSkeleton] = React.useState(isLoading);

  React.useEffect(() => {
    if (isLoading) {
      setShowSkeleton(true);
    } else {
      const timer = setTimeout(() => setShowSkeleton(false), delay);
      return () => clearTimeout(timer);
    }
  }, [isLoading, delay]);

  return showSkeleton;
}