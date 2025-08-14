'use client'

import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

interface HeroAnimationsProps {
  classType: string
  element: string
  isActive: boolean
  onAnimationComplete?: () => void
}

// Configuración de animaciones por clase
const CLASS_ANIMATIONS = {
  mage: {
    particles: {
      count: 20,
      colors: ['#FF6B6B', '#FF8E8E', '#FFB3B3'],
      size: [2, 4, 6],
      duration: 3
    },
    effects: {
      glow: '#FF6B6B',
      sparkle: true,
      floating: true
    }
  },
  warrior: {
    particles: {
      count: 15,
      colors: ['#96CEB4', '#A8D5BA', '#BAE0C0'],
      size: [3, 5, 7],
      duration: 2.5
    },
    effects: {
      glow: '#96CEB4',
      sparkle: false,
      floating: false,
      groundShake: true
    }
  },
  archer: {
    particles: {
      count: 25,
      colors: ['#4ECDC4', '#6ED4CC', '#8EDCD4'],
      size: [1, 3, 5],
      duration: 2
    },
    effects: {
      glow: '#4ECDC4',
      sparkle: true,
      floating: true,
      windTrail: true
    }
  },
  priest: {
    particles: {
      count: 30,
      colors: ['#FFEAA7', '#FFF2C7', '#FFF8E7'],
      size: [2, 4, 6],
      duration: 3.5
    },
    effects: {
      glow: '#FFEAA7',
      sparkle: true,
      floating: true,
      healing: true
    }
  },
  assassin: {
    particles: {
      count: 10,
      colors: ['#6C5CE7', '#8B7CF7', '#AA9CF7'],
      size: [1, 2, 3],
      duration: 1.5
    },
    effects: {
      glow: '#6C5CE7',
      sparkle: false,
      floating: false,
      stealth: true
    }
  }
}

// Configuración de elementos
const ELEMENT_EFFECTS = {
  'Fuego': {
    background: 'radial-gradient(circle, rgba(255, 107, 107, 0.1) 0%, transparent 70%)',
    particles: ['🔥', '✨', '⚡'],
    animation: 'fireFlicker'
  },
  'Tierra': {
    background: 'radial-gradient(circle, rgba(150, 206, 180, 0.1) 0%, transparent 70%)',
    particles: ['🌱', '💎', '🏔️'],
    animation: 'earthPulse'
  },
  'Viento': {
    background: 'radial-gradient(circle, rgba(78, 205, 196, 0.1) 0%, transparent 70%)',
    particles: ['💨', '🌪️', '🍃'],
    animation: 'windFlow'
  },
  'Luz': {
    background: 'radial-gradient(circle, rgba(255, 234, 167, 0.1) 0%, transparent 70%)',
    particles: ['✨', '🌟', '💫'],
    animation: 'lightShimmer'
  },
  'Sombra': {
    background: 'radial-gradient(circle, rgba(108, 92, 231, 0.1) 0%, transparent 70%)',
    particles: ['🌑', '⚫', '💀'],
    animation: 'shadowFade'
  }
}

export default function HeroAnimations({ classType, element, isActive, onAnimationComplete }: HeroAnimationsProps) {
  const [particles, setParticles] = useState<Array<{id: number, x: number, y: number, size: number, color: string}>>([])
  const [showEffects, setShowEffects] = useState(false)

  const animationConfig = CLASS_ANIMATIONS[classType as keyof typeof CLASS_ANIMATIONS]
  const elementConfig = ELEMENT_EFFECTS[element as keyof typeof ELEMENT_EFFECTS]

  useEffect(() => {
    if (isActive && animationConfig) {
      setShowEffects(true)
      
      // Generar partículas
      const newParticles = Array.from({ length: animationConfig.particles.count }, (_, i) => ({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: animationConfig.particles.size[Math.floor(Math.random() * animationConfig.particles.size.length)],
        color: animationConfig.particles.colors[Math.floor(Math.random() * animationConfig.particles.colors.length)]
      }))
      
      setParticles(newParticles)
      
      // Limpiar después de la animación
      const timer = setTimeout(() => {
        setShowEffects(false)
        onAnimationComplete?.()
      }, animationConfig.particles.duration * 1000)
      
      return () => clearTimeout(timer)
    }
  }, [isActive, animationConfig, onAnimationComplete])

  if (!showEffects || !animationConfig) return null

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {/* Efecto de fondo del elemento */}
      <motion.div
        className="absolute inset-0"
        style={{ background: elementConfig?.background }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      />
      
      {/* Partículas */}
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            width: `${particle.size}px`,
            height: `${particle.size}px`,
            backgroundColor: particle.color,
            borderRadius: '50%',
            boxShadow: `0 0 ${particle.size * 2}px ${particle.color}`
          }}
          initial={{ 
            opacity: 0, 
            scale: 0,
            x: 0,
            y: 0
          }}
          animate={{ 
            opacity: [0, 1, 0],
            scale: [0, 1, 0],
            x: animationConfig.effects.floating ? [0, Math.random() * 100 - 50] : 0,
            y: animationConfig.effects.floating ? [0, Math.random() * -100] : 0
          }}
          transition={{ 
            duration: animationConfig.particles.duration,
            ease: "easeOut"
          }}
        />
      ))}
      
      {/* Efectos específicos por clase */}
      {classType === 'mage' && (
        <MageEffects />
      )}
      
      {classType === 'warrior' && (
        <WarriorEffects />
      )}
      
      {classType === 'archer' && (
        <ArcherEffects />
      )}
      
      {classType === 'priest' && (
        <PriestEffects />
      )}
      
      {classType === 'assassin' && (
        <AssassinEffects />
      )}
    </div>
  )
}

// Efectos específicos por clase
function MageEffects() {
  return (
    <motion.div
      className="absolute inset-0"
      animate={{
        background: [
          'radial-gradient(circle, rgba(255, 107, 107, 0.2) 0%, transparent 50%)',
          'radial-gradient(circle, rgba(255, 107, 107, 0.1) 0%, transparent 50%)',
          'radial-gradient(circle, rgba(255, 107, 107, 0.2) 0%, transparent 50%)'
        ]
      }}
      transition={{ duration: 2, repeat: Infinity }}
    />
  )
}

function WarriorEffects() {
  return (
    <motion.div
      className="absolute inset-0"
      animate={{
        scale: [1, 1.02, 1],
        rotate: [0, 1, -1, 0]
      }}
      transition={{ duration: 0.5, repeat: Infinity }}
    />
  )
}

function ArcherEffects() {
  return (
    <motion.div
      className="absolute inset-0"
      animate={{
        background: [
          'linear-gradient(45deg, transparent 0%, rgba(78, 205, 196, 0.1) 50%, transparent 100%)',
          'linear-gradient(45deg, transparent 0%, rgba(78, 205, 196, 0.2) 50%, transparent 100%)',
          'linear-gradient(45deg, transparent 0%, rgba(78, 205, 196, 0.1) 50%, transparent 100%)'
        ]
      }}
      transition={{ duration: 1, repeat: Infinity }}
    />
  )
}

function PriestEffects() {
  return (
    <motion.div
      className="absolute inset-0"
      animate={{
        background: [
          'radial-gradient(circle, rgba(255, 234, 167, 0.3) 0%, transparent 70%)',
          'radial-gradient(circle, rgba(255, 234, 167, 0.1) 0%, transparent 70%)',
          'radial-gradient(circle, rgba(255, 234, 167, 0.3) 0%, transparent 70%)'
        ]
      }}
      transition={{ duration: 2, repeat: Infinity }}
    />
  )
}

function AssassinEffects() {
  return (
    <motion.div
      className="absolute inset-0"
      animate={{
        opacity: [0.3, 0.7, 0.3],
        background: [
          'radial-gradient(circle, rgba(108, 92, 231, 0.1) 0%, transparent 70%)',
          'radial-gradient(circle, rgba(108, 92, 231, 0.3) 0%, transparent 70%)',
          'radial-gradient(circle, rgba(108, 92, 231, 0.1) 0%, transparent 70%)'
        ]
      }}
      transition={{ duration: 1.5, repeat: Infinity }}
    />
  )
} 