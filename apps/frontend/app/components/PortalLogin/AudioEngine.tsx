'use client';

import { useCallback, useEffect, useRef } from 'react';
import { Howl, Howler } from 'howler';

interface SoundOptions {
  volume?: number;
  loop?: boolean;
  rate?: number;
}

interface AudioEngineHook {
  playSound: (soundName: string, options?: SoundOptions) => void;
  stopSound: (soundName: string) => void;
  setMasterVolume: (volume: number) => void;
  toggleMute: () => void;
}

// Sound library configuration
const SOUNDS = {
  portal_hum: '/sounds/portal_hum.mp3',
  typing_pulse: '/sounds/typing_pulse.mp3',
  portal_reject: '/sounds/portal_reject.wav',
  portal_success: '/sounds/portal_success.mp3',
  click: '/sounds/click.mp3',
  hover: '/sounds/hover.mp3',
  level_up: '/sounds/level_up.mp3',
  damage_hit: '/sounds/damage_hit.mp3',
  combo_break: '/sounds/combo_break.mp3',
  ultimate_ready: '/sounds/ultimate_ready.mp3'
};

// Singleton audio manager
class AudioManager {
  private sounds: Map<string, Howl> = new Map();
  private isMuted: boolean = false;

  constructor() {
    // Pre-load critical sounds
    this.preloadSounds(['portal_hum', 'typing_pulse', 'portal_reject', 'portal_success']);
  }

  private preloadSounds(soundNames: string[]) {
    soundNames.forEach(name => {
      if (SOUNDS[name as keyof typeof SOUNDS]) {
        const sound = new Howl({
          src: [SOUNDS[name as keyof typeof SOUNDS]],
          preload: true,
          html5: true // Better for streaming
        });
        this.sounds.set(name, sound);
      }
    });
  }

  play(soundName: string, options?: SoundOptions) {
    if (this.isMuted) return;

    let sound = this.sounds.get(soundName);
    
    if (!sound && SOUNDS[soundName as keyof typeof SOUNDS]) {
      sound = new Howl({
        src: [SOUNDS[soundName as keyof typeof SOUNDS]],
        html5: true
      });
      this.sounds.set(soundName, sound);
    }

    if (sound) {
      sound.volume(options?.volume || 0.5);
      sound.loop(options?.loop || false);
      sound.rate(options?.rate || 1.0);
      sound.play();
    }
  }

  stop(soundName: string) {
    const sound = this.sounds.get(soundName);
    if (sound) {
      sound.stop();
    }
  }

  setMasterVolume(volume: number) {
    Howler.volume(Math.max(0, Math.min(1, volume)));
  }

  toggleMute() {
    this.isMuted = !this.isMuted;
    Howler.mute(this.isMuted);
  }

  dispose() {
    this.sounds.forEach(sound => sound.unload());
    this.sounds.clear();
  }
}

// Create singleton instance
let audioManagerInstance: AudioManager | null = null;

export function useAudioEngine(): AudioEngineHook {
  const managerRef = useRef<AudioManager>();

  useEffect(() => {
    if (!audioManagerInstance) {
      audioManagerInstance = new AudioManager();
    }
    managerRef.current = audioManagerInstance;

    return () => {
      // Don't dispose on component unmount as it's a singleton
    };
  }, []);

  const playSound = useCallback((soundName: string, options?: SoundOptions) => {
    managerRef.current?.play(soundName, options);
  }, []);

  const stopSound = useCallback((soundName: string) => {
    managerRef.current?.stop(soundName);
  }, []);

  const setMasterVolume = useCallback((volume: number) => {
    managerRef.current?.setMasterVolume(volume);
  }, []);

  const toggleMute = useCallback(() => {
    managerRef.current?.toggleMute();
  }, []);

  return {
    playSound,
    stopSound,
    setMasterVolume,
    toggleMute
  };
}

// Context provider for global audio settings
import React, { createContext, useContext, useState } from 'react';

interface AudioContextType {
  isMuted: boolean;
  masterVolume: number;
  toggleMute: () => void;
  setMasterVolume: (volume: number) => void;
}

const AudioContext = createContext<AudioContextType | undefined>(undefined);

interface AudioProviderProps {
  children: React.ReactNode;
}

export function AudioProvider({ children }: AudioProviderProps) {
  const [isMuted, setIsMuted] = useState(false);
  const [masterVolume, setMasterVolume] = useState(0.5);
  const { toggleMute: engineToggleMute, setMasterVolume: engineSetMasterVolume } = useAudioEngine();

  const toggleMute = () => {
    setIsMuted(!isMuted);
    engineToggleMute();
  };

  const handleSetMasterVolume = (volume: number) => {
    setMasterVolume(volume);
    engineSetMasterVolume(volume);
  };

  return (
    <AudioContext.Provider value={{ 
      isMuted, 
      masterVolume, 
      toggleMute, 
      setMasterVolume: handleSetMasterVolume 
    }}>
      {children}
    </AudioContext.Provider>
  );
}

export function useAudioContext() {
  const context = useContext(AudioContext);
  if (!context) {
    throw new Error('useAudioContext must be used within AudioProvider');
  }
  return context;
}

// Convenience hook expected by many components
export function useAudio() {
  const engine = useAudioEngine();
  const { isMuted, masterVolume, toggleMute, setMasterVolume } = useAudioContext();
  return {
    ...engine,
    isMuted,
    masterVolume,
    toggleMute,
    setMasterVolume
  };
}