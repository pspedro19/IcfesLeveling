import { useEffect, useRef, useState } from 'react';
import { AssetsManager } from '../utils/assets';

interface SoundOptions {
  volume?: number;
  loop?: boolean;
}

export function useGameSounds() {
  const audioContext = useRef<AudioContext | null>(null);
  const audioBuffers = useRef<{ [key: string]: AudioBuffer }>({});
  const [isMuted, setIsMuted] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('gameSoundsMuted') === 'true';
    }
    return false;
  });
  const [volume, setVolume] = useState<number>(() => {
    if (typeof window !== 'undefined') {
      return parseFloat(localStorage.getItem('gameSoundsVolume') || '0.5');
    }
    return 0.5;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;
    audioContext.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    // Usar únicamente assets existentes del proyecto
    const soundFiles: Record<string, string> = {
      correct: AssetsManager.SOUNDS.SUCCESS,
      incorrect: AssetsManager.SOUNDS.ERROR,
      levelUp: AssetsManager.SOUNDS.LEVEL_UP,
      streak: AssetsManager.SOUNDS.MAGIC,
      click: AssetsManager.SOUNDS.CLICK,
      timerWarning: AssetsManager.SOUNDS.TYPING_PULSE,
    };
    Object.entries(soundFiles).forEach(async ([key, url]) => {
      try {
        const response = await fetch(url);
        const arrayBuffer = await response.arrayBuffer();
        const audioBuffer = await audioContext.current!.decodeAudioData(arrayBuffer);
        audioBuffers.current[key] = audioBuffer;
      } catch (err) {
        console.warn(`Failed to load sound: ${key}`, err);
      }
    });
    return () => {
      audioContext.current?.close();
    };
  }, []);

  const playSound = (type: keyof typeof audioBuffers.current, options: SoundOptions = {}) => {
    if (!audioContext.current || isMuted || !audioBuffers.current[type]) return;
    try {
      const source = audioContext.current.createBufferSource();
      const gainNode = audioContext.current.createGain();
      source.buffer = audioBuffers.current[type];
      source.connect(gainNode);
      gainNode.connect(audioContext.current.destination);
      gainNode.gain.value = (options.volume ?? 1) * volume;
      source.loop = options.loop ?? false;
      source.start(0);
      if ('vibrate' in navigator && type === 'correct') {
        (navigator as any).vibrate?.(200);
      }
      return () => source.stop();
    } catch (error) {
      console.warn('Error playing sound:', error);
    }
  };

  const toggleMute = () => {
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    if (typeof window !== 'undefined') localStorage.setItem('gameSoundsMuted', String(newMuted));
  };

  const changeVolume = (newVolume: number) => {
    const clamped = Math.max(0, Math.min(1, newVolume));
    setVolume(clamped);
    if (typeof window !== 'undefined') localStorage.setItem('gameSoundsVolume', String(clamped));
  };

  const playBackgroundMusic = () => {
    if (!audioContext.current || isMuted) return;
    const oscillator = audioContext.current.createOscillator();
    const gainNode = audioContext.current.createGain();
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.current.destination);
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(110, audioContext.current.currentTime);
    gainNode.gain.setValueAtTime(0.02 * volume, audioContext.current.currentTime);
    oscillator.start();
    return () => oscillator.stop();
  };

  return { playSound, isMuted, toggleMute, volume, changeVolume, playBackgroundMusic };
}


