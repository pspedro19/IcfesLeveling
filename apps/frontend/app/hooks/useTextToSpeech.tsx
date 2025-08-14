import { useState, useCallback, useEffect, useRef } from 'react';

interface TTSOptions {
  lang?: string;
  rate?: number;
  pitch?: number;
  volume?: number;
  voice?: SpeechSynthesisVoice | null;
}

interface UseTTSReturn {
  speak: (text: string, options?: TTSOptions) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  isSpeaking: boolean;
  isPaused: boolean;
  isSupported: boolean;
  voices: SpeechSynthesisVoice[];
  currentVoice: SpeechSynthesisVoice | null;
  setVoice: (voice: SpeechSynthesisVoice) => void;
}

const DEFAULT_OPTIONS: TTSOptions = {
  lang: 'es-ES',
  rate: 1.0,
  pitch: 1.0,
  volume: 1.0,
};

export function useTextToSpeech(): UseTTSReturn {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [currentVoice, setCurrentVoice] = useState<SpeechSynthesisVoice | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  
  const isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;
  
  // Load available voices
  useEffect(() => {
    if (!isSupported) return;
    
    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      setVoices(availableVoices);
      
      // Set default Spanish voice
      const spanishVoice = availableVoices.find(voice => 
        voice.lang.startsWith('es')
      );
      if (spanishVoice && !currentVoice) {
        setCurrentVoice(spanishVoice);
      }
    };
    
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
    
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, [isSupported, currentVoice]);
  
  const speak = useCallback((text: string, options: TTSOptions = {}) => {
    if (!isSupported) return;
    
    // Stop any ongoing speech
    stop();
    
    const utterance = new SpeechSynthesisUtterance(text);
    const opts = { ...DEFAULT_OPTIONS, ...options };
    
    utterance.lang = opts.lang!;
    utterance.rate = opts.rate!;
    utterance.pitch = opts.pitch!;
    utterance.volume = opts.volume!;
    
    if (opts.voice) {
      utterance.voice = opts.voice;
    } else if (currentVoice) {
      utterance.voice = currentVoice;
    }
    
    utterance.onstart = () => {
      setIsSpeaking(true);
      setIsPaused(false);
    };
    
    utterance.onend = () => {
      setIsSpeaking(false);
      setIsPaused(false);
    };
    
    utterance.onpause = () => {
      setIsPaused(true);
    };
    
    utterance.onresume = () => {
      setIsPaused(false);
    };
    
    utterance.onerror = (event) => {
      console.error('TTS Error:', event);
      setIsSpeaking(false);
      setIsPaused(false);
    };
    
    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  }, [isSupported, currentVoice]);
  
  const pause = useCallback(() => {
    if (!isSupported || !isSpeaking) return;
    window.speechSynthesis.pause();
  }, [isSupported, isSpeaking]);
  
  const resume = useCallback(() => {
    if (!isSupported || !isPaused) return;
    window.speechSynthesis.resume();
  }, [isSupported, isPaused]);
  
  const stop = useCallback(() => {
    if (!isSupported) return;
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
  }, [isSupported]);
  
  const setVoice = useCallback((voice: SpeechSynthesisVoice) => {
    setCurrentVoice(voice);
  }, []);
  
  return {
    speak,
    pause,
    resume,
    stop,
    isSpeaking,
    isPaused,
    isSupported,
    voices,
    currentVoice,
    setVoice,
  };
}

// React Context for global TTS
import React, { createContext, useContext } from 'react';

const TTSContext = createContext<UseTTSReturn | null>(null);

export function TTSProvider({ children }: { children: React.ReactNode }) {
  const tts = useTextToSpeech();
  
  return (
    <TTSContext.Provider value={tts}>
      {children}
    </TTSContext.Provider>
  );
}

export function useTTS() {
  const context = useContext(TTSContext);
  if (!context) {
    throw new Error('useTTS must be used within a TTSProvider');
  }
  return context;
}

// HOC for adding TTS to any component
interface WithTTSProps {
  ttsText?: string;
  ttsAutoPlay?: boolean;
  ttsOptions?: TTSOptions;
}

export function withTTS<P extends object>(
  Component: React.ComponentType<P>
) {
  return function WithTTSComponent(props: P & WithTTSProps) {
    const { ttsText, ttsAutoPlay, ttsOptions, ...componentProps } = props;
    const { speak } = useTTS();
    
    useEffect(() => {
      if (ttsAutoPlay && ttsText) {
        speak(ttsText, ttsOptions);
      }
    }, [ttsAutoPlay, ttsText, ttsOptions, speak]);
    
    return <Component {...(componentProps as P)} />;
  };
}