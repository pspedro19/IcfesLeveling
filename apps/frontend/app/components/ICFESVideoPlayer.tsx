"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, 
  Pause, 
  SkipForward, 
  SkipBack, 
  Volume2, 
  VolumeX,
  Settings,
  Maximize,
  RotateCcw,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';

// =====================================================
// TIPOS Y INTERFACES
// =====================================================

interface ICFESVideoPlayerProps {
  videoId: string;
  codigoTema: string;
  userId: string;
  planId: string;
  unitNumber: number;
  onComplete: (data: VideoProgress) => void;
  onProgress?: (progress: number) => void;
  onError?: (error: string) => void;
  className?: string;
}

interface VideoProgress {
  userId: string;
  planId: string;
  unitNumber: number;
  videoId: string;
  codigoTema: string;
  watchedSeconds: number;
  watchedPercentage: number;
  isCompleted: boolean;
  replayCount: number;
  speedPreference: string;
}

interface SecurityAlert {
  type: 'TAB_SWITCH' | 'TIME_JUMP' | 'MULTIPLE_ATTEMPTS';
  message: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  timestamp: Date;
}

interface Milestone {
  percentage: number;
  xp: number;
  message: string;
  achieved: boolean;
}

// =====================================================
// COMPONENTE PRINCIPAL
// =====================================================

export const ICFESVideoPlayer: React.FC<ICFESVideoPlayerProps> = ({
  videoId,
  codigoTema,
  userId,
  planId,
  unitNumber,
  onComplete,
  onProgress,
  onError,
  className = ""
}) => {
  // =====================================================
  // ESTADOS
  // =====================================================
  
  const [player, setPlayer] = useState<YT.Player | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(50);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  
  // Estados de seguridad
  const [isWatching, setIsWatching] = useState(true);
  const [cheatAttempts, setCheatAttempts] = useState(0);
  const [securityAlerts, setSecurityAlerts] = useState<SecurityAlert[]>([]);
  const [showSecurityWarning, setShowSecurityWarning] = useState(false);
  
  // Estados de progreso
  const [progress, setProgress] = useState(0);
  const [replayCount, setReplayCount] = useState(0);
  const [milestones, setMilestones] = useState<Milestone[]>([
    { percentage: 25, xp: 25, message: "¡Primer cuarto completado!", achieved: false },
    { percentage: 50, xp: 50, message: "¡Mitad del camino!", achieved: false },
    { percentage: 75, xp: 75, message: "¡Casi terminando!", achieved: false },
    { percentage: 90, xp: 100, message: "¡Video completado!", achieved: false }
  ]);
  
  // Estados de engagement
  const [focusTime, setFocusTime] = useState(0);
  const [tabSwitches, setTabSwitches] = useState(0);
  const [engagementScore, setEngagementScore] = useState(100);
  
  // Referencias
  const playerRef = useRef<HTMLDivElement>(null);
  const heartbeatRef = useRef<NodeJS.Timeout>();
  const controlsTimeoutRef = useRef<NodeJS.Timeout>();
  const focusTimerRef = useRef<NodeJS.Timeout>();
  
  // =====================================================
  // EFECTOS
  // =====================================================
  
  // Inicializar YouTube Player
  useEffect(() => {
    if (!window.YT) {
      loadYouTubeAPI();
    } else {
      initializePlayer();
    }
    
    return () => {
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current);
      if (focusTimerRef.current) clearTimeout(focusTimerRef.current);
    };
  }, [videoId]);
  
  // Sistema anti-trampa
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && player && isPlaying) {
        handleTabSwitch();
      }
    };
    
    const handleFocus = () => {
      setIsWatching(true);
      setShowSecurityWarning(false);
    };
    
    const handleBlur = () => {
      if (isPlaying) {
        handleTabSwitch();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);
    window.addEventListener('blur', handleBlur);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('blur', handleBlur);
    };
  }, [player, isPlaying]);
  
  // Heartbeat de progreso
  useEffect(() => {
    if (player && isPlaying && isWatching) {
      heartbeatRef.current = setInterval(() => {
        updateProgress();
        updateEngagement();
      }, 5000); // Cada 5 segundos
    }
    
    return () => {
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
    };
  }, [player, isPlaying, isWatching]);
  
  // Timer de enfoque
  useEffect(() => {
    if (isWatching && isPlaying) {
      focusTimerRef.current = setInterval(() => {
        setFocusTime(prev => prev + 1);
      }, 1000);
    }
    
    return () => {
      if (focusTimerRef.current) clearInterval(focusTimerRef.current);
    };
  }, [isWatching, isPlaying]);
  
  // =====================================================
  // FUNCIONES DE INICIALIZACIÓN
  // =====================================================
  
  const loadYouTubeAPI = () => {
    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    const firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode?.insertBefore(tag, firstScriptTag);
    
    window.onYouTubeIframeAPIReady = initializePlayer;
  };
  
  const initializePlayer = () => {
    if (!playerRef.current) return;
    
    const newPlayer = new window.YT.Player(playerRef.current, {
      height: '100%',
      width: '100%',
      videoId: videoId,
      playerVars: {
        autoplay: 0,
        controls: 0,
        modestbranding: 1,
        rel: 0,
        showinfo: 0,
        iv_load_policy: 3,
        cc_load_policy: 1,
        playsinline: 1,
        enablejsapi: 1,
        origin: window.location.origin
      },
      events: {
        onReady: onPlayerReady,
        onStateChange: onPlayerStateChange,
        onError: onPlayerError
      }
    });
    
    setPlayer(newPlayer);
  };
  
  // =====================================================
  // MANEJADORES DE EVENTOS DEL PLAYER
  // =====================================================
  
  const onPlayerReady = (event: YT.PlayerEvent) => {
    setIsReady(true);
    setDuration(event.target.getDuration());
    logger.info(`✅ Player listo para video ${videoId}`);
  };
  
  const onPlayerStateChange = (event: YT.OnStateChangeEvent) => {
    const state = event.data;
    
    switch (state) {
      case window.YT.PlayerState.PLAYING:
        setIsPlaying(true);
        setIsWatching(true);
        startProgressTracking();
        break;
      case window.YT.PlayerState.PAUSED:
        setIsPlaying(false);
        pauseProgressTracking();
        break;
      case window.YT.PlayerState.ENDED:
        handleVideoComplete();
        break;
      case window.YT.PlayerState.BUFFERING:
        // El video está cargando
        break;
    }
  };
  
  const onPlayerError = (event: YT.OnErrorEvent) => {
    const errorMessage = getYouTubeErrorMessage(event.data);
    logger.error(`❌ Error en player: ${errorMessage}`);
    onError?.(errorMessage);
  };
  
  // =====================================================
  // FUNCIONES DE CONTROL
  // =====================================================
  
  const togglePlay = () => {
    if (!player) return;
    
    if (isPlaying) {
      player.pauseVideo();
    } else {
      player.playVideo();
    }
  };
  
  const seekTo = (time: number) => {
    if (!player) return;
    
    const newTime = Math.max(0, Math.min(time, duration));
    player.seekTo(newTime, true);
    setCurrentTime(newTime);
    
    // Verificar si el salto es sospechoso
    const timeDiff = Math.abs(newTime - currentTime);
    if (timeDiff > 30) {
      handleSuspiciousJump(timeDiff);
    }
  };
  
  const changePlaybackRate = (rate: number) => {
    if (!player) return;
    
    const validRates = [0.5, 0.75, 1, 1.25, 1.5, 2];
    if (validRates.includes(rate)) {
      player.setPlaybackRate(rate);
      setPlaybackRate(rate);
    }
  };
  
  const toggleMute = () => {
    if (!player) return;
    
    if (isMuted) {
      player.unMute();
      setIsMuted(false);
    } else {
      player.mute();
      setIsMuted(true);
    }
  };
  
  const toggleFullscreen = () => {
    if (!playerRef.current) return;
    
    if (!isFullscreen) {
      if (playerRef.current.requestFullscreen) {
        playerRef.current.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
    
    setIsFullscreen(!isFullscreen);
  };
  
  // =====================================================
  // FUNCIONES DE SEGURIDAD
  // =====================================================
  
  const handleTabSwitch = () => {
    if (!player) return;
    
    player.pauseVideo();
    setIsWatching(false);
    setCheatAttempts(prev => prev + 1);
    
    const alert: SecurityAlert = {
      type: 'TAB_SWITCH',
      message: 'Video pausado por cambio de pestaña',
      severity: cheatAttempts >= 2 ? 'HIGH' : 'MEDIUM',
      timestamp: new Date()
    };
    
    setSecurityAlerts(prev => [...prev, alert]);
    setShowSecurityWarning(true);
    
    // Después de 3 intentos, marcar como sospechoso
    if (cheatAttempts >= 2) {
      sendSecurityAlert({
        userId,
        videoId,
        alertType: 'MULTIPLE_TAB_SWITCHES',
        timestamp: Date.now()
      });
    }
    
    logger.warning(`⚠️ Tab switch detectado. Intentos: ${cheatAttempts + 1}`);
  };
  
  const handleSuspiciousJump = (timeDiff: number) => {
    const alert: SecurityAlert = {
      type: 'TIME_JUMP',
      message: `Salto de tiempo sospechoso: ${Math.round(timeDiff)}s`,
      severity: timeDiff > 60 ? 'HIGH' : 'MEDIUM',
      timestamp: new Date()
    };
    
    setSecurityAlerts(prev => [...prev, alert]);
    
    if (timeDiff > 60) {
      sendSecurityAlert({
        userId,
        videoId,
        alertType: 'SUSPICIOUS_JUMP',
        timestamp: Date.now()
      });
    }
    
    logger.warning(`⚠️ Salto de tiempo sospechoso: ${timeDiff}s`);
  };
  
  const sendSecurityAlert = async (data: any) => {
    try {
      // Aquí enviarías la alerta al backend
      console.log('🚨 Alerta de seguridad enviada:', data);
    } catch (error) {
      logger.error('Error enviando alerta de seguridad:', error);
    }
  };
  
  // =====================================================
  // FUNCIONES DE PROGRESO
  // =====================================================
  
  const updateProgress = () => {
    if (!player) return;
    
    const time = player.getCurrentTime();
    const newProgress = (time / duration) * 100;
    
    setCurrentTime(time);
    setProgress(newProgress);
    
    // Verificar milestones
    checkMilestones(newProgress);
    
    // Callback de progreso
    onProgress?.(newProgress);
  };
  
  const checkMilestones = (currentProgress: number) => {
    setMilestones(prev => prev.map(milestone => {
      if (!milestone.achieved && currentProgress >= milestone.percentage) {
        // Logro alcanzado
        showMilestoneNotification(milestone);
        return { ...milestone, achieved: true };
      }
      return milestone;
    }));
  };
  
  const showMilestoneNotification = (milestone: Milestone) => {
    // Aquí podrías mostrar una notificación visual
    logger.info(`🎉 Milestone alcanzado: ${milestone.message} (+${milestone.xp} XP)`);
  };
  
  const startProgressTracking = () => {
    // Iniciar tracking de progreso
    logger.info('🚀 Iniciando tracking de progreso');
  };
  
  const pauseProgressTracking = () => {
    // Pausar tracking de progreso
    logger.info('⏸️ Pausando tracking de progreso');
  };
  
  const handleVideoComplete = () => {
    const videoProgress: VideoProgress = {
      userId,
      planId,
      unitNumber,
      videoId,
      codigoTema,
      watchedSeconds: duration,
      watchedPercentage: 100,
      isCompleted: true,
      replayCount,
      speedPreference: playbackRate.toString()
    };
    
    onComplete(videoProgress);
    logger.info('✅ Video completado');
  };
  
  // =====================================================
  // FUNCIONES DE ENGAGEMENT
  // =====================================================
  
  const updateEngagement = () => {
    if (!isWatching) return;
    
    // Calcular score de engagement
    const focusRatio = focusTime / Math.max(currentTime, 1);
    const tabSwitchPenalty = tabSwitches * 0.1;
    const newScore = Math.max(0, Math.min(100, (focusRatio * 100) * (1 - tabSwitchPenalty)));
    
    setEngagementScore(newScore);
    
    // Enviar métricas al backend
    sendEngagementMetrics(newScore);
  };
  
  const sendEngagementMetrics = async (score: number) => {
    try {
      // Aquí enviarías las métricas al backend
      console.log('📊 Métricas de engagement:', { score, focusTime, tabSwitches });
    } catch (error) {
      logger.error('Error enviando métricas de engagement:', error);
    }
  };
  
  // =====================================================
  // FUNCIONES DE UTILIDAD
  // =====================================================
  
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  const getYouTubeErrorMessage = (errorCode: number): string => {
    const errorMessages: { [key: number]: string } = {
      2: 'Parámetro inválido',
      5: 'HTML5 player error',
      100: 'Video no encontrado',
      101: 'Embedding no permitido',
      150: 'Embedding no permitido'
    };
    
    return errorMessages[errorCode] || 'Error desconocido';
  };
  
  const logger = {
    info: (message: string) => console.log(`[ICFES Video Player] ${message}`),
    warning: (message: string) => console.warn(`[ICFES Video Player] ⚠️ ${message}`),
    error: (message: string, error?: any) => console.error(`[ICFES Video Player] ❌ ${message}`, error)
  };
  
  // =====================================================
  // RENDERIZADO
  // =====================================================
  
  return (
    <div className={`relative bg-gray-900 rounded-lg overflow-hidden ${className}`}>
      {/* Advertencia de Seguridad */}
      <AnimatePresence>
        {showSecurityWarning && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 bg-red-900/95 flex items-center justify-center"
          >
            <div className="text-white text-center p-8">
              <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-red-300" />
              <h3 className="text-2xl mb-4 font-bold">⚠️ Video Pausado</h3>
              <p className="text-lg mb-2">Por favor, mantén el foco en el video para continuar</p>
              <p className="text-sm text-red-300">Intentos: {cheatAttempts}/3</p>
              <button
                onClick={() => setShowSecurityWarning(false)}
                className="mt-4 px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
              >
                Entendido
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Player Container */}
      <div 
        ref={playerRef} 
        className="aspect-video relative"
        onMouseMove={() => {
          setShowControls(true);
          if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current);
          controlsTimeoutRef.current = setTimeout(() => setShowControls(false), 3000);
        }}
      />
      
      {/* Controles del Player */}
      <AnimatePresence>
        {showControls && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4"
          >
            {/* Barra de Progreso */}
            <div className="mb-4">
              <div className="relative">
                <input
                  type="range"
                  min="0"
                  max={duration}
                  value={currentTime}
                  onChange={(e) => seekTo(Number(e.target.value))}
                  className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-white text-sm mt-1">
                  <span>{formatTime(currentTime)}</span>
                  <span>{formatTime(duration)}</span>
                </div>
              </div>
            </div>
            
            {/* Controles Principales */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button
                  onClick={togglePlay}
                  className="text-white hover:text-blue-400 transition-colors"
                >
                  {isPlaying ? <Pause size={24} /> : <Play size={24} />}
                </button>
                
                <button
                  onClick={() => seekTo(currentTime - 10)}
                  className="text-white hover:text-blue-400 transition-colors"
                >
                  <SkipBack size={20} />
                </button>
                
                <button
                  onClick={() => seekTo(currentTime + 10)}
                  className="text-white hover:text-blue-400 transition-colors"
                >
                  <SkipForward size={20} />
                </button>
                
                <button
                  onClick={toggleMute}
                  className="text-white hover:text-blue-400 transition-colors"
                >
                  {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
                </button>
                
                <div className="flex items-center space-x-2">
                  <span className="text-white text-sm">Velocidad:</span>
                  <select
                    value={playbackRate}
                    onChange={(e) => changePlaybackRate(Number(e.target.value))}
                    className="bg-gray-700 text-white text-sm rounded px-2 py-1"
                  >
                    <option value={0.5}>0.5x</option>
                    <option value={0.75}>0.75x</option>
                    <option value={1}>1x</option>
                    <option value={1.25}>1.25x</option>
                    <option value={1.5}>1.5x</option>
                    <option value={2}>2x</option>
                  </select>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="text-white hover:text-blue-400 transition-colors"
                >
                  <Settings size={20} />
                </button>
                
                <button
                  onClick={toggleFullscreen}
                  className="text-white hover:text-blue-400 transition-colors"
                >
                  <Maximize size={20} />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Panel de Configuración */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="absolute top-4 right-4 bg-gray-800 rounded-lg p-4 text-white"
          >
            <h4 className="font-semibold mb-3">Configuración</h4>
            <div className="space-y-3">
              <div>
                <label className="block text-sm mb-1">Volumen</label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={volume}
                  onChange={(e) => {
                    const newVolume = Number(e.target.value);
                    setVolume(newVolume);
                    if (player) player.setVolume(newVolume);
                  }}
                  className="w-full"
                />
              </div>
              
              <div>
                <label className="block text-sm mb-1">Calidad</label>
                <select className="w-full bg-gray-700 rounded px-2 py-1 text-sm">
                  <option value="auto">Automático</option>
                  <option value="1080p">1080p</option>
                  <option value="720p">720p</option>
                  <option value="480p">480p</option>
                </select>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Indicadores de Estado */}
      <div className="absolute top-4 left-4 flex space-x-2">
        {!isReady && (
          <div className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm">
            Cargando...
          </div>
        )}
        
        {isPlaying && (
          <div className="bg-green-600 text-white px-3 py-1 rounded-full text-sm flex items-center space-x-1">
            <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
            Reproduciendo
          </div>
        )}
        
        {!isWatching && (
          <div className="bg-red-600 text-white px-3 py-1 rounded-full text-sm">
            Pausado
          </div>
        )}
      </div>
      
      {/* Métricas de Engagement */}
      <div className="absolute top-4 right-4 text-white text-sm">
        <div className="bg-black/50 rounded-lg p-2">
          <div>Focus: {Math.round(focusTime)}s</div>
          <div>Engagement: {Math.round(engagementScore)}%</div>
          <div>Replays: {replayCount}</div>
        </div>
      </div>
      
      {/* Milestones */}
      <div className="absolute bottom-20 left-4 right-4">
        <div className="flex justify-between">
          {milestones.map((milestone, index) => (
            <div
              key={index}
              className={`flex flex-col items-center ${
                milestone.achieved ? 'text-green-400' : 'text-gray-400'
              }`}
            >
              <div className="w-8 h-8 rounded-full border-2 border-current flex items-center justify-center text-xs">
                {milestone.achieved ? (
                  <CheckCircle size={16} />
                ) : (
                  <span>{milestone.percentage}%</span>
                )}
              </div>
              <div className="text-xs mt-1 text-center">
                +{milestone.xp} XP
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Alertas de Seguridad */}
      <div className="absolute top-20 left-4 right-4">
        <AnimatePresence>
          {securityAlerts.slice(-3).map((alert, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 100 }}
              className={`mb-2 p-3 rounded-lg text-white text-sm ${
                alert.severity === 'HIGH' ? 'bg-red-600' :
                alert.severity === 'MEDIUM' ? 'bg-yellow-600' : 'bg-blue-600'
              }`}
            >
              <div className="flex items-center justify-between">
                <span>{alert.message}</span>
                <button
                  onClick={() => setSecurityAlerts(prev => prev.filter((_, i) => i !== index))}
                  className="ml-2 hover:opacity-70"
                >
                  <XCircle size={16} />
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

// =====================================================
// ESTILOS CSS
// =====================================================

const styles = `
  .slider::-webkit-slider-thumb {
    appearance: none;
    height: 16px;
    width: 16px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
  }
  
  .slider::-moz-range-thumb {
    height: 16px;
    width: 16px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: none;
  }
`;

// Agregar estilos al head
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = styles;
  document.head.appendChild(styleElement);
}

export default ICFESVideoPlayer;


