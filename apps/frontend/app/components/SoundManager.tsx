'use client'

import { useEffect, useRef } from 'react'
import { Howl } from 'howler'

interface SoundManagerProps {
  soundEffect?: string
  isPlaying: boolean
  onSoundEnd?: () => void
}

// Configuración de sonidos por clase épica
const SOUND_EFFECTS = {
  warrior_roar: {
    src: '/sounds/warrior-roar.mp3',
    volume: 0.7,
    rate: 1.0
  },
  spell_cast: {
    src: '/sounds/spell-cast.mp3',
    volume: 0.8,
    rate: 1.0
  },
  bow_release: {
    src: '/sounds/bow-release.mp3',
    volume: 0.6,
    rate: 1.0
  },
  healing_spell: {
    src: '/sounds/healing-spell.mp3',
    volume: 0.7,
    rate: 1.0
  },
  stealth_move: {
    src: '/sounds/stealth-move.mp3',
    volume: 0.5,
    rate: 1.0
  },
  // Sonidos de ambiente
  fire_ambient: {
    src: '/sounds/fire-ambient.mp3',
    volume: 0.4,
    rate: 1.0,
    loop: true
  },
  earth_ambient: {
    src: '/sounds/earth-ambient.mp3',
    volume: 0.4,
    rate: 1.0,
    loop: true
  },
  wind_ambient: {
    src: '/sounds/wind-ambient.mp3',
    volume: 0.4,
    rate: 1.0,
    loop: true
  },
  light_ambient: {
    src: '/sounds/light-ambient.mp3',
    volume: 0.4,
    rate: 1.0,
    loop: true
  },
  shadow_ambient: {
    src: '/sounds/shadow-ambient.mp3',
    volume: 0.4,
    rate: 1.0,
    loop: true
  }
}

// Mapeo de elementos a sonidos de ambiente
const ELEMENT_AMBIENT_SOUNDS = {
  'Fuego': 'fire_ambient',
  'Tierra': 'earth_ambient',
  'Viento': 'wind_ambient',
  'Luz': 'light_ambient',
  'Sombra': 'shadow_ambient'
}

export default function SoundManager({ soundEffect, isPlaying, onSoundEnd }: SoundManagerProps) {
  const soundRef = useRef<Howl | null>(null)
  const ambientRef = useRef<Howl | null>(null)

  useEffect(() => {
    if (!soundEffect || !isPlaying) return

    // Detener sonidos anteriores
    if (soundRef.current) {
      soundRef.current.stop()
    }
    if (ambientRef.current) {
      ambientRef.current.stop()
    }

    // Crear sonido principal
    const soundConfig = SOUND_EFFECTS[soundEffect as keyof typeof SOUND_EFFECTS]
    if (soundConfig) {
      soundRef.current = new Howl({
        src: [soundConfig.src],
        volume: soundConfig.volume,
        rate: soundConfig.rate,
        onend: () => {
          onSoundEnd?.()
        }
      })
      soundRef.current.play()
    }

    // Crear sonido de ambiente basado en el elemento
    const ambientSound = getAmbientSound(soundEffect)
    if (ambientSound) {
      ambientRef.current = new Howl({
        src: [ambientSound.src],
        volume: ambientSound.volume,
        rate: ambientSound.rate,
        loop: (ambientSound as any).loop || false
      })
      ambientRef.current.play()
    }

    return () => {
      if (soundRef.current) {
        soundRef.current.stop()
      }
      if (ambientRef.current) {
        ambientRef.current.stop()
      }
    }
  }, [soundEffect, isPlaying, onSoundEnd])

  const getAmbientSound = (soundEffect: string) => {
    // Mapear sound_effect a elemento
    const elementMap: Record<string, string> = {
      'warrior_roar': 'Tierra',
      'spell_cast': 'Fuego',
      'bow_release': 'Viento',
      'healing_spell': 'Luz',
      'stealth_move': 'Sombra'
    }

    const element = elementMap[soundEffect]
    if (element) {
      const ambientKey = ELEMENT_AMBIENT_SOUNDS[element as keyof typeof ELEMENT_AMBIENT_SOUNDS]
      return SOUND_EFFECTS[ambientKey as keyof typeof SOUND_EFFECTS]
    }
    return null
  }

  return null // Componente invisible
}

// Hook para usar sonidos en componentes
export function useSound() {
  const playSound = (soundEffect: string) => {
    const soundConfig = SOUND_EFFECTS[soundEffect as keyof typeof SOUND_EFFECTS]
    if (soundConfig) {
      const sound = new Howl({
        src: [soundConfig.src],
        volume: soundConfig.volume,
        rate: soundConfig.rate
      })
      sound.play()
      return sound
    }
    return null
  }

  const playAmbientSound = (element: string) => {
    const ambientKey = ELEMENT_AMBIENT_SOUNDS[element as keyof typeof ELEMENT_AMBIENT_SOUNDS]
    if (ambientKey) {
      const soundConfig = SOUND_EFFECTS[ambientKey as keyof typeof SOUND_EFFECTS]
      const sound = new Howl({
        src: [soundConfig.src],
        volume: soundConfig.volume,
        rate: soundConfig.rate,
        loop: (soundConfig as any).loop || false
      })
      sound.play()
      return sound
    }
    return null
  }

  // Funciones específicas para el test diagnóstico
  const playClickSound = () => {
    const sound = new Howl({
      src: ['/sounds/click.mp3'],
      volume: 0.5,
      rate: 1.0
    })
    sound.play()
    return sound
  }

  const playHoverSound = () => {
    const sound = new Howl({
      src: ['/sounds/hover.mp3'],
      volume: 0.3,
      rate: 1.0
    })
    sound.play()
    return sound
  }

  const playSuccessSound = () => {
    const sound = new Howl({
      src: ['/sounds/success.mp3'],
      volume: 0.6,
      rate: 1.0
    })
    sound.play()
    return sound
  }

  const playErrorSound = () => {
    const sound = new Howl({
      src: ['/sounds/error.mp3'],
      volume: 0.5,
      rate: 1.0
    })
    sound.play()
    return sound
  }

  const playLevelUpSound = () => {
    const sound = new Howl({
      src: ['/sounds/levelup.mp3'],
      volume: 0.7,
      rate: 1.0
    })
    sound.play()
    return sound
  }

  const playMagicSound = () => {
    const sound = new Howl({
      src: ['/sounds/magic.mp3'],
      volume: 0.6,
      rate: 1.0
    })
    sound.play()
    return sound
  }

  const playVictorySound = () => {
    const sound = new Howl({
      src: ['/sounds/victory.mp3'],
      volume: 0.8,
      rate: 1.0
    })
    sound.play()
    return sound
  }

  return { 
    playSound, 
    playAmbientSound,
    playClickSound,
    playHoverSound,
    playSuccessSound,
    playErrorSound,
    playLevelUpSound,
    playMagicSound,
    playVictorySound
  }
} 