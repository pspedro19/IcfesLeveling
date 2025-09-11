'use client';

import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  color: string;
  life: number;
  maxLife: number;
}

interface AnimatedBackgroundProps {
  variant?: 'default' | 'success' | 'error' | 'warning';
  intensity?: 'low' | 'medium' | 'high';
  interactive?: boolean;
}

export default function AnimatedBackground({ 
  variant = 'default', 
  intensity = 'medium',
  interactive = true 
}: AnimatedBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const particlesRef = useRef<Particle[]>([]);
  const mouseRef = useRef({ x: 0, y: 0 });

  const colors = {
    default: ['#8B5CF6', '#A855F7', '#9333EA', '#7C3AED'],
    success: ['#10B981', '#059669', '#047857', '#065F46'],
    error: ['#EF4444', '#DC2626', '#B91C1C', '#991B1B'],
    warning: ['#F59E0B', '#D97706', '#B45309', '#92400E']
  };

  const particleCount = {
    low: 30,
    medium: 50,
    high: 80
  };

  const createParticle = (x?: number, y?: number): Particle => {
    const canvas = canvasRef.current;
    if (!canvas) return {} as Particle;

    const colorArray = colors[variant];
    
    return {
      x: x ?? Math.random() * canvas.width,
      y: y ?? Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      size: Math.random() * 3 + 1,
      opacity: Math.random() * 0.8 + 0.2,
      color: colorArray[Math.floor(Math.random() * colorArray.length)],
      life: 0,
      maxLife: Math.random() * 200 + 100
    };
  };

  const initParticles = () => {
    const count = particleCount[intensity];
    particlesRef.current = Array.from({ length: count }, () => createParticle());
  };

  const updateParticles = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    particlesRef.current.forEach((particle, index) => {
      // Update position
      particle.x += particle.vx;
      particle.y += particle.vy;
      particle.life++;

      // Boundary wrapping
      if (particle.x < 0) particle.x = canvas.width;
      if (particle.x > canvas.width) particle.x = 0;
      if (particle.y < 0) particle.y = canvas.height;
      if (particle.y > canvas.height) particle.y = 0;

      // Fade out over lifetime
      particle.opacity = Math.max(0, 1 - (particle.life / particle.maxLife));

      // Mouse interaction
      if (interactive) {
        const dx = mouseRef.current.x - particle.x;
        const dy = mouseRef.current.y - particle.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance < 100) {
          const force = (100 - distance) / 100;
          particle.vx += (dx / distance) * force * 0.01;
          particle.vy += (dy / distance) * force * 0.01;
        }
      }

      // Apply drag
      particle.vx *= 0.99;
      particle.vy *= 0.99;

      // Respawn particle if dead
      if (particle.life >= particle.maxLife) {
        Object.assign(particle, createParticle());
      }
    });
  };

  const drawParticles = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw particles
    particlesRef.current.forEach(particle => {
      ctx.save();
      ctx.globalAlpha = particle.opacity;
      ctx.fillStyle = particle.color;
      ctx.shadowBlur = 10;
      ctx.shadowColor = particle.color;
      
      ctx.beginPath();
      ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
      ctx.fill();
      
      ctx.restore();
    });

    // Draw connections
    if (intensity !== 'low') {
      ctx.strokeStyle = colors[variant][0];
      ctx.lineWidth = 0.5;
      
      for (let i = 0; i < particlesRef.current.length; i++) {
        for (let j = i + 1; j < particlesRef.current.length; j++) {
          const particle1 = particlesRef.current[i];
          const particle2 = particlesRef.current[j];
          
          const dx = particle1.x - particle2.x;
          const dy = particle1.y - particle2.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance < 80) {
            ctx.save();
            ctx.globalAlpha = (80 - distance) / 80 * 0.3;
            ctx.beginPath();
            ctx.moveTo(particle1.x, particle1.y);
            ctx.lineTo(particle2.x, particle2.y);
            ctx.stroke();
            ctx.restore();
          }
        }
      }
    }
  };

  const animate = () => {
    updateParticles();
    drawParticles();
    animationRef.current = requestAnimationFrame(animate);
  };

  const handleMouseMove = (event: MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    mouseRef.current = {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top
    };
  };

  const handleResize = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    initParticles();
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Set canvas size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Initialize particles
    initParticles();

    // Start animation
    animate();

    // Event listeners
    if (interactive) {
      window.addEventListener('mousemove', handleMouseMove);
    }
    window.addEventListener('resize', handleResize);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
    };
  }, [variant, intensity, interactive]);

  return (
    <>
      <canvas
        ref={canvasRef}
        className="fixed inset-0 pointer-events-none z-0"
        style={{ opacity: 0.6 }}
      />
      
      {/* Additional overlay effects */}
      <div className="fixed inset-0 pointer-events-none z-0">
        {/* Gradient overlays */}
        <motion.div
          className="absolute inset-0"
          style={{
            background: `radial-gradient(circle at 20% 80%, ${colors[variant][0]}20 0%, transparent 50%), 
                        radial-gradient(circle at 80% 20%, ${colors[variant][1]}20 0%, transparent 50%), 
                        radial-gradient(circle at 40% 40%, ${colors[variant][2]}10 0%, transparent 50%)`
          }}
          animate={{
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        />

        {/* Floating orbs */}
        {Array.from({ length: 3 }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-32 h-32 rounded-full blur-xl"
            style={{
              background: `radial-gradient(circle, ${colors[variant][i % colors[variant].length]}40, transparent)`
            }}
            animate={{
              x: [0, 100, 0],
              y: [0, -50, 0],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 10 + i * 2,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: i * 2
            }}
            style={{
              left: `${20 + i * 30}%`,
              top: `${10 + i * 20}%`,
            }}
          />
        ))}

        {/* Scanning lines effect */}
        <motion.div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(90deg, transparent 0%, ${colors[variant][0]}20 50%, transparent 100%)`
          }}
          animate={{
            x: ['-100%', '100%'],
          }}
          transition={{
            duration: 6,
            repeat: Infinity,
            ease: 'linear'
          }}
        />
      </div>
    </>
  );
}